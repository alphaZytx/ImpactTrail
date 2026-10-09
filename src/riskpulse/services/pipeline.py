from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from riskpulse.config import Settings
from riskpulse.domain.documents import NormalizedDocument, RawDocument
from riskpulse.domain.signals import (
    EntityMatch,
    EventLabel,
    EventResult,
    Explanation,
    RiskSignal,
    SourceReference,
)
from riskpulse.ingestion.base import SourceAdapter
from riskpulse.nlp.event_classifier import RuleEventClassifier
from riskpulse.nlp.impact import ImpactScorer
from riskpulse.nlp.sentiment import SentimentAnalyzer, build_sentiment_analyzer
from riskpulse.processing.entity_linker import EntityLinker
from riskpulse.processing.normalize import normalize_document
from riskpulse.storage.repositories import Repository
from riskpulse.stress_testing.service import StressTestingService

logger = logging.getLogger(__name__)

SYSTEMIC_EVENT_LABELS = {
    EventLabel.GEOPOLITICAL,
    EventLabel.MACROECONOMIC,
    EventLabel.CLIMATE_NATURAL_HAZARD,
}
EVENT_CLUSTER_WINDOW = timedelta(hours=6)
EVENT_TERM_SIMILARITY_MIN = 0.20


@dataclass
class ProcessingSummary:
    fetched: int = 0
    processed: int = 0
    duplicates: int = 0
    signals: int = 0
    stress_runs: int = 0
    failed: int = 0

    def as_dict(self) -> dict[str, int]:
        return self.__dict__.copy()


class RiskPipeline:
    def __init__(
        self,
        settings: Settings,
        repository: Repository,
        sentiment_analyzer: SentimentAnalyzer | None = None,
    ) -> None:
        self.settings = settings
        self.repository = repository
        self.repository.init_schema()
        self.entity_linker = EntityLinker.from_csv(settings.companies_path)
        self.sentiment_analyzer = sentiment_analyzer or build_sentiment_analyzer(
            settings.model_backend, settings.allow_model_downloads
        )
        self.event_classifier = RuleEventClassifier(settings.taxonomy_path)
        self.impact_scorer = ImpactScorer(settings.taxonomy_path)
        self.stress_service = StressTestingService(
            settings.scenarios_path,
            settings.portfolio_path,
            settings.stress_trigger_threshold,
        )

    async def process_adapter(self, adapter: SourceAdapter, query: str = "") -> ProcessingSummary:
        summary = ProcessingSummary()
        try:
            async for raw in adapter.fetch(query):
                summary.fetched += 1
                try:
                    result = self.process_raw(raw)
                    if result["duplicate"]:
                        summary.duplicates += 1
                    else:
                        summary.processed += 1
                        summary.signals += len(result["signals"])
                        summary.stress_runs += len(result["stress_runs"])
                except Exception as exc:
                    summary.failed += 1
                    self.repository.save_dead_letter(
                        raw.source, str(exc), raw.model_dump(mode="json")
                    )
                    logger.exception("Failed to process document %s", raw.source_record_id)
        except Exception as exc:
            summary.failed += 1
            self.repository.save_dead_letter(adapter.name, str(exc), {"query": query})
            logger.exception("Source adapter failed: %s", adapter.name)
        for failure in adapter.drain_failures():
            summary.failed += 1
            self.repository.save_dead_letter(adapter.name, failure.reason, failure.payload)
            logger.warning("Skipped invalid %s record: %s", adapter.name, failure.reason)
        return summary

    def process_raw(self, raw: RawDocument) -> dict[str, Any]:
        document = normalize_document(raw, max_length=self.settings.max_text_length)
        sentiment = self.sentiment_analyzer.analyze(document.text)
        event = self.event_classifier.classify(document.text)
        entities = self.entity_linker.resolve(document.text)
        if not entities:
            fallback = (
                self.entity_linker.market_wide()
                if event.label in SYSTEMIC_EVENT_LABELS
                else self.entity_linker.unresolved()
            )
            entities = [fallback]

        if not self.repository.save_document(document):
            return {"duplicate": True, "signals": [], "stress_runs": []}

        signals: list[RiskSignal] = []
        stress_runs: list[Any] = []
        for entity in entities:
            cluster_id = self._event_cluster_id(document, entity, event)
            corroborating_sources = len(
                self.repository.cluster_sources(str(cluster_id)) | {document.source}
            )
            impact = self.impact_scorer.score(
                document,
                entity,
                sentiment,
                event,
                corroborating_sources=corroborating_sources,
            )
            actionable = (
                entity.entity_id != "unresolved"
                and event.label.value != "other"
                and event.confidence >= self.settings.event_confidence_threshold
                and impact.confidence >= self.settings.impact_confidence_threshold
            )
            signal_key = f"{document.document_id}:{entity.entity_id}:risk-engine-1.0.0"
            warnings: list[str] = []
            if entity.entity_id == "market-wide":
                warnings.append("Systemic event has no issuer; signal treated as market-wide.")
            elif entity.entity_id == "unresolved":
                warnings.append(
                    "No supported issuer resolved; signal is inspectable but cannot trigger action."
                )
            if not self.stress_service.direction_is_supported(event):
                warnings.append(
                    "Narrative direction is incompatible with the configured adverse rate-rise "
                    "scenario; automatic stress is suppressed."
                )
            if not actionable:
                warnings.append("Signal is below the automatic-action confidence gate.")
            reason_codes = [
                event.label.value.upper(),
                f"SOURCE_{document.source.upper()}",
                *[term.upper().replace(" ", "_") for term in event.matched_terms[:3]],
            ]
            signal = RiskSignal(
                signal_id=uuid5(NAMESPACE_URL, signal_key),
                event_cluster_id=cluster_id,
                document_id=document.document_id,
                source=SourceReference(
                    name=document.source,
                    type=document.source_type.value,
                    url=document.canonical_url,
                ),
                entity=entity,
                sentiment=sentiment,
                event=event,
                impact=impact,
                explanation=Explanation(
                    evidence_excerpt=document.text[:280],
                    reason_codes=list(dict.fromkeys(reason_codes)),
                    warnings=warnings,
                ),
                published_at=document.published_at,
                created_at=datetime.now(UTC),
                actionable=actionable,
                metadata={
                    "is_replay": document.is_replay,
                    "language": document.language,
                    "corroborating_sources": corroborating_sources,
                },
            )
            if self.repository.save_signal(signal):
                signals.append(signal)
                stress_run = self.stress_service.run(signal)
                if stress_run and self.repository.save_stress_run(
                    stress_run, self.stress_service.portfolio_version
                ):
                    stress_runs.append(stress_run)
        return {"duplicate": False, "signals": signals, "stress_runs": stress_runs}

    def _event_cluster_id(
        self, document: NormalizedDocument, entity: EntityMatch, event: EventResult
    ) -> UUID:
        """Reuse a nearby cluster only when event evidence has meaningful term overlap."""
        event_terms = {term.casefold() for term in event.matched_terms}
        candidates, _ = self.repository.list_signals(limit=500, event_label=event.label.value)
        for candidate in candidates:
            if candidate.entity.entity_id != entity.entity_id:
                continue
            if abs(document.published_at - candidate.published_at) > EVENT_CLUSTER_WINDOW:
                continue
            candidate_terms = {term.casefold() for term in candidate.event.matched_terms}
            union = event_terms | candidate_terms
            similarity = len(event_terms & candidate_terms) / len(union) if union else 0.0
            if similarity >= EVENT_TERM_SIMILARITY_MIN:
                return candidate.event_cluster_id
        cluster_key = f"{entity.entity_id}:{event.label.value}:{document.document_id}"
        return uuid5(NAMESPACE_URL, cluster_key)
