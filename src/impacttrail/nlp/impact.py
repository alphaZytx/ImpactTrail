from __future__ import annotations

from pathlib import Path
from typing import Any

from impacttrail.config import load_yaml
from impacttrail.domain.documents import NormalizedDocument
from impacttrail.domain.signals import EntityMatch, EventResult, ImpactResult, SentimentResult

SOURCE_QUALITY = {"gdelt": 0.78, "bluesky": 0.55, "manual": 0.65}


class ImpactScorer:
    def __init__(self, taxonomy_path: Path) -> None:
        payload = load_yaml(taxonomy_path)
        self.labels: dict[str, dict[str, Any]] = payload["labels"]

    def score(
        self,
        document: NormalizedDocument,
        entity: EntityMatch,
        sentiment: SentimentResult,
        event: EventResult,
        corroborating_sources: int = 1,
        novelty: float = 1.0,
    ) -> ImpactResult:
        severity = float(self.labels[event.label.value]["severity_prior"])
        relevance = entity.match_confidence
        intensity = abs(sentiment.score)
        model_confidence = (sentiment.confidence + event.confidence) / 2
        corroboration = min(1.0, 0.35 + 0.25 * corroborating_sources)
        source_quality = SOURCE_QUALITY.get(document.source, 0.60)
        components = {
            "event_severity": severity,
            "entity_relevance": relevance,
            "sentiment_intensity": intensity,
            "model_confidence": model_confidence,
            "corroboration": corroboration,
            "novelty": max(0.0, min(1.0, novelty)),
            "source_quality": source_quality,
        }
        weighted = (
            0.30 * severity
            + 0.15 * relevance
            + 0.10 * intensity
            + 0.10 * model_confidence
            + 0.15 * corroboration
            + 0.10 * components["novelty"]
            + 0.10 * source_quality
        )
        impact_score = round(max(1.0, min(10.0, 1 + 9 * weighted)), 1)
        confidence = round(
            max(
                0.0,
                min(
                    1.0,
                    0.45 * event.confidence + 0.30 * entity.match_confidence + 0.25 * corroboration,
                ),
            ),
            4,
        )
        return ImpactResult(
            score=impact_score,
            confidence=confidence,
            components={key: round(value, 4) for key, value in components.items()},
        )
