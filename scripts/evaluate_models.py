from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from impacttrail.config import get_settings
from impacttrail.domain.documents import NormalizedDocument, RawDocument, SourceType
from impacttrail.domain.signals import EntityMatch
from impacttrail.nlp.event_classifier import RuleEventClassifier
from impacttrail.nlp.impact import ImpactScorer
from impacttrail.nlp.sentiment import LexiconSentimentAnalyzer
from impacttrail.processing.normalize import normalize_document

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/results/model_metrics.json"
IMPACT_EVALUATION_TIMESTAMP = datetime(2026, 10, 8, tzinfo=UTC)
IMPACT_EVALUATION_ENTITY = EntityMatch(
    entity_id="evaluation-entity",
    name="Evaluation Entity",
    ticker="EVAL",
    sector="Diversified",
    country="Global",
    match_confidence=1.0,
    match_method="fixed_evaluation_fixture",
)


def macro_f1(actual: list[str], predicted: list[str]) -> float:
    labels = sorted(set(actual) | set(predicted))
    f1_values = []
    for label in labels:
        true_positive = sum(
            a == label and p == label for a, p in zip(actual, predicted, strict=True)
        )
        false_positive = sum(
            a != label and p == label for a, p in zip(actual, predicted, strict=True)
        )
        false_negative = sum(
            a == label and p != label for a, p in zip(actual, predicted, strict=True)
        )
        precision = (
            true_positive / (true_positive + false_positive)
            if true_positive + false_positive
            else 0
        )
        recall = (
            true_positive / (true_positive + false_negative)
            if true_positive + false_negative
            else 0
        )
        f1_values.append(2 * precision * recall / (precision + recall) if precision + recall else 0)
    return sum(f1_values) / len(f1_values) if f1_values else 0


def _validate_numeric_pairs(actual: Sequence[float], predicted: Sequence[float]) -> None:
    if len(actual) != len(predicted):
        raise ValueError("actual and predicted must contain the same number of values")
    if not actual:
        raise ValueError("metrics require at least one value")


def mean_absolute_error(actual: Sequence[float], predicted: Sequence[float]) -> float:
    _validate_numeric_pairs(actual, predicted)
    absolute_error = math.fsum(
        abs(observed - estimate) for observed, estimate in zip(actual, predicted, strict=True)
    )
    return absolute_error / len(actual)


def pearson_correlation(actual: Sequence[float], predicted: Sequence[float]) -> float | None:
    """Return Pearson's r, or None when either input has zero variance."""
    _validate_numeric_pairs(actual, predicted)
    actual_mean = math.fsum(actual) / len(actual)
    predicted_mean = math.fsum(predicted) / len(predicted)
    actual_centered = [value - actual_mean for value in actual]
    predicted_centered = [value - predicted_mean for value in predicted]
    denominator = math.sqrt(
        math.fsum(value**2 for value in actual_centered)
        * math.fsum(value**2 for value in predicted_centered)
    )
    if denominator == 0:
        return None
    return (
        math.fsum(
            observed * estimate
            for observed, estimate in zip(actual_centered, predicted_centered, strict=True)
        )
        / denominator
    )


def per_label_mean_absolute_error(
    actual: Sequence[float], predicted: Sequence[float], labels: Sequence[str]
) -> dict[str, float]:
    _validate_numeric_pairs(actual, predicted)
    if len(labels) != len(actual):
        raise ValueError("labels and values must contain the same number of items")
    grouped_errors: dict[str, list[float]] = {}
    for observed, estimate, label in zip(actual, predicted, labels, strict=True):
        grouped_errors.setdefault(label, []).append(abs(observed - estimate))
    return {
        label: math.fsum(errors) / len(errors) for label, errors in sorted(grouped_errors.items())
    }


def impact_evaluation_document(text: str, row_number: int) -> NormalizedDocument:
    """Build the standardized synthetic GDELT-shaped document used for impact evaluation."""
    source_record_id = f"impact-evaluation-{row_number:03d}"
    raw = RawDocument(
        source_record_id=source_record_id,
        source="gdelt",
        source_type=SourceType.NEWS,
        text=text,
        url=f"https://example.org/evaluation/{source_record_id}",
        published_at=IMPACT_EVALUATION_TIMESTAMP,
        ingested_at=IMPACT_EVALUATION_TIMESTAMP,
        raw_metadata={
            "language": "en",
            "license": "synthetic",
            "evaluation_fixture_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        },
        is_replay=True,
    )
    return normalize_document(raw)


def evaluate() -> dict[str, object]:
    settings = get_settings()
    sentiment = LexiconSentimentAnalyzer()
    event = RuleEventClassifier(settings.taxonomy_path)
    impact = ImpactScorer(settings.taxonomy_path)

    with (ROOT / "data/evaluation/sentiment_gold.csv").open(
        "r", encoding="utf-8", newline=""
    ) as stream:
        sentiment_rows = list(csv.DictReader(stream))
    sentiment_actual = [row["label"] for row in sentiment_rows]
    sentiment_predicted = [sentiment.analyze(row["text"]).label.value for row in sentiment_rows]

    with (ROOT / "data/evaluation/events_gold.csv").open(
        "r", encoding="utf-8", newline=""
    ) as stream:
        event_rows = list(csv.DictReader(stream))
    event_actual = [row["label"] for row in event_rows]
    event_predicted = [event.classify(row["text"]).label.value for row in event_rows]
    impact_actual = [float(row["impact_score"]) for row in event_rows]
    impact_predicted = []
    for row_number, row in enumerate(event_rows, start=1):
        document = impact_evaluation_document(row["text"], row_number)
        sentiment_result = sentiment.analyze(document.text)
        event_result = event.classify(document.text)
        impact_predicted.append(
            impact.score(
                document,
                IMPACT_EVALUATION_ENTITY,
                sentiment_result,
                event_result,
                corroborating_sources=1,
                novelty=1.0,
            ).score
        )
    impact_pearson = pearson_correlation(impact_actual, impact_predicted)

    return {
        "evaluation_notice": (
            "Metrics use compact synthetic gold sets designed for contract verification; they do "
            "not measure production generalization, calibration, or realized market impact."
        ),
        "sentiment": {
            "backend": sentiment.backend,
            "samples": len(sentiment_rows),
            "macro_f1": round(macro_f1(sentiment_actual, sentiment_predicted), 4),
            "accuracy": round(
                sum(a == p for a, p in zip(sentiment_actual, sentiment_predicted, strict=True))
                / len(sentiment_actual),
                4,
            ),
            "support": Counter(sentiment_actual),
        },
        "event": {
            "backend": event.backend,
            "samples": len(event_rows),
            "macro_f1": round(macro_f1(event_actual, event_predicted), 4),
            "accuracy": round(
                sum(a == p for a, p in zip(event_actual, event_predicted, strict=True))
                / len(event_actual),
                4,
            ),
            "support": Counter(event_actual),
        },
        "impact": {
            "backend": "explainable_seven_factor_v1",
            "samples": len(event_rows),
            "mae": round(mean_absolute_error(impact_actual, impact_predicted), 4),
            "pearson_correlation": (
                round(impact_pearson, 4) if impact_pearson is not None else None
            ),
            "per_event_label_mae": {
                label: round(value, 4)
                for label, value in per_label_mean_absolute_error(
                    impact_actual, impact_predicted, event_actual
                ).items()
            },
            "assumptions": {
                "document_shape": "synthetic GDELT-shaped English news record",
                "source": "gdelt",
                "fixed_timestamp_utc": IMPACT_EVALUATION_TIMESTAMP.isoformat(),
                "entity": "fixed synthetic evaluation entity",
                "entity_relevance": 1.0,
                "corroborating_sources": 1,
                "novelty": 1.0,
                "sentiment_input": sentiment.backend,
                "event_input": event.backend,
                "target": "human-specified synthetic severity rubric, not observed market movement",
                "pearson_zero_variance_policy": (
                    "null if gold or predicted impact scores have zero variance"
                ),
            },
        },
    }


def main() -> None:
    metrics = evaluate()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
