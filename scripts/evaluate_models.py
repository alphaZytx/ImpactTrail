from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

from riskpulse.config import get_settings
from riskpulse.nlp.event_classifier import RuleEventClassifier
from riskpulse.nlp.sentiment import LexiconSentimentAnalyzer

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/results/model_metrics.json"


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


def evaluate() -> dict[str, object]:
    settings = get_settings()
    sentiment = LexiconSentimentAnalyzer()
    event = RuleEventClassifier(settings.taxonomy_path)

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

    return {
        "evaluation_notice": (
            "Metrics use compact synthetic gold sets and are not production claims."
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
    }


def main() -> None:
    metrics = evaluate()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
