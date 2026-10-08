from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from riskpulse.config import Settings
from riskpulse.domain.documents import RawDocument
from riskpulse.domain.signals import Explanation, RiskSignal, SourceReference
from riskpulse.ingestion.base import SourceAdapter
from riskpulse.nlp.event_classifier import RuleEventClassifier
from riskpulse.nlp.impact import ImpactScorer
from riskpulse.nlp.sentiment import SentimentAnalyzer, build_sentiment_analyzer
from riskpulse.processing.entity_linker import EntityLinker
from riskpulse.processing.normalize import normalize_document
from riskpulse.storage.repositories import Repository
from riskpulse.stress_testing.service import StressTestingService

logger = logging.getLogger(__name__)


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
        return summary

    def process_raw(self, raw: RawDocument) -> dict[str, Any]:
        document = normalize_document(raw, max_length=self.settings.max_text_length)
        if not self.repository.save_document(document):
            return {"duplicate": True, "signals": [], "stress_runs": []}

        sentiment = self.sentiment_analyzer.analyze(document.text)
        event = self.event_classifier.classify(document.text)
        entities = self.entity_linker.resolve(document.text)
        if not entities:
            entities = [self.entity_linker.market_wide()]

        signals: list[RiskSignal] = []
        stress_runs: list[Any] = []
        for entity in entities:
            cluster_key = (
                f"{entity.entity_id}:{event.label.value}:{document.published_at.date().isoformat()}"
            )
            cluster_id = uuid5(NAMESPACE_URL, cluster_key)
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
                event.label.value != "other"
                and event.confidence >= self.settings.event_confidence_threshold
                and impact.confidence >= self.settings.impact_confidence_threshold
            )
            signal_key = f"{document.document_id}:{entity.entity_id}:risk-engine-1.0.0"
            warnings: list[str] = []
            if entity.entity_id == "market-wide":
                warnings.append("No specific issuer resolved; signal treated as market-wide.")
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
