from __future__ import annotations

import math
import re
from typing import Protocol

from impacttrail.domain.signals import SentimentLabel, SentimentResult


class SentimentAnalyzer(Protocol):
    def analyze(self, text: str) -> SentimentResult: ...


POSITIVE_TERMS = {
    "beat": 1.0,
    "beats": 1.0,
    "growth": 0.8,
    "profit": 0.8,
    "record": 0.6,
    "upgrade": 1.0,
    "upgraded": 1.0,
    "surge": 0.9,
    "strong": 0.7,
    "approval": 0.8,
    "approved": 0.8,
    "launch": 0.5,
    "gain": 0.7,
    "raised guidance": 1.2,
    "acquisition": 0.3,
    "resilient": 0.6,
}

NEGATIVE_TERMS = {
    "default": 1.4,
    "downgrade": 1.2,
    "downgraded": 1.2,
    "bankruptcy": 1.5,
    "loss": 0.8,
    "miss": 0.7,
    "missed": 0.8,
    "decline": 0.7,
    "plunge": 1.0,
    "sanction": 1.0,
    "sanctions": 1.0,
    "war": 1.2,
    "breach": 1.1,
    "ransomware": 1.3,
    "fine": 0.8,
    "investigation": 0.7,
    "recession": 1.0,
    "inflation": 0.5,
    "profit warning": 1.2,
    "recall": 0.9,
    "outage": 0.8,
    "liquidity crisis": 1.5,
    "missed payment": 1.5,
}

FINBERT_MODEL = "ProsusAI/finbert"
FINBERT_REVISION = "4556d13015211d73dccd3fdd39d39232506f3e43"


class LexiconSentimentAnalyzer:
    backend = "financial_lexicon_v1"

    def analyze(self, text: str) -> SentimentResult:
        lowered = text.casefold()
        positive = self._score_terms(lowered, POSITIVE_TERMS)
        negative = self._score_terms(lowered, NEGATIVE_TERMS)
        total = positive + negative
        if total == 0:
            score = 0.0
            probabilities = {"positive": 0.12, "neutral": 0.76, "negative": 0.12}
        else:
            raw = (positive - negative) / max(total, 1.0)
            score = math.tanh(raw * 1.35)
            neutral = max(0.05, 0.42 - min(abs(score), 0.37))
            directional = 1.0 - neutral
            positive_probability = directional * ((score + 1) / 2)
            negative_probability = directional - positive_probability
            probabilities = {
                "positive": round(positive_probability, 4),
                "neutral": round(neutral, 4),
                "negative": round(negative_probability, 4),
            }
        label = (
            SentimentLabel.POSITIVE
            if score > 0.15
            else SentimentLabel.NEGATIVE
            if score < -0.15
            else SentimentLabel.NEUTRAL
        )
        return SentimentResult(
            score=round(max(-1.0, min(1.0, score)), 4),
            label=label,
            confidence=max(probabilities.values()),
            probabilities=probabilities,
            backend=self.backend,
        )

    @staticmethod
    def _score_terms(text: str, terms: dict[str, float]) -> float:
        total = 0.0
        for term, weight in terms.items():
            occurrences = len(re.findall(rf"(?<!\w){re.escape(term)}(?!\w)", text))
            total += occurrences * weight
        return total


class FinBertSentimentAnalyzer:
    backend = f"{FINBERT_MODEL}@{FINBERT_REVISION[:12]}"

    def __init__(self, allow_downloads: bool = False) -> None:
        try:
            from transformers import pipeline
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("transformers is not installed; use requirements-ml.txt") from exc
        self._pipeline = pipeline(
            "text-classification",
            model=FINBERT_MODEL,
            revision=FINBERT_REVISION,
            top_k=None,
            local_files_only=not allow_downloads,
        )

    def analyze(self, text: str) -> SentimentResult:  # pragma: no cover - optional model
        raw = self._pipeline(text[:4000])[0]
        probabilities = {item["label"].lower(): float(item["score"]) for item in raw}
        score = probabilities.get("positive", 0.0) - probabilities.get("negative", 0.0)
        label = SentimentLabel(max(probabilities, key=lambda key: probabilities[key]))
        return SentimentResult(
            score=round(score, 4),
            label=label,
            confidence=max(probabilities.values()),
            probabilities={key: round(value, 4) for key, value in probabilities.items()},
            backend=self.backend,
        )


def build_sentiment_analyzer(
    backend: str = "auto", allow_downloads: bool = False
) -> SentimentAnalyzer:
    if backend == "lexicon":
        return LexiconSentimentAnalyzer()
    if backend in {"auto", "finbert"}:
        try:
            return FinBertSentimentAnalyzer(allow_downloads=allow_downloads)
        except Exception:
            if backend == "finbert":
                raise
    return LexiconSentimentAnalyzer()
