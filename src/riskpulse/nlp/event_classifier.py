from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from riskpulse.config import load_yaml
from riskpulse.domain.signals import EventLabel, EventResult


class RuleEventClassifier:
    backend = "taxonomy_rules_v1"

    def __init__(self, taxonomy_path: Path) -> None:
        payload = load_yaml(taxonomy_path)
        self.labels: dict[str, dict[str, Any]] = payload["labels"]

    def classify(self, text: str) -> EventResult:
        lowered = text.casefold()
        scores: dict[str, float] = {}
        terms_by_label: dict[str, list[str]] = {}
        for label, definition in self.labels.items():
            if label == "other":
                continue
            matches = [
                term
                for term in definition.get("keywords", [])
                if re.search(rf"(?<!\w){re.escape(str(term).casefold())}(?!\w)", lowered)
            ]
            terms_by_label[label] = matches
            if matches:
                longest_bonus = min(max(map(len, matches)) / 30, 0.35)
                scores[label] = len(matches) + longest_bonus
        if not scores:
            return EventResult(
                label=EventLabel.OTHER,
                confidence=0.45,
                matched_terms=[],
                backend=self.backend,
            )
        ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        best_label, best_score = ranked[0]
        total = sum(scores.values())
        dominance = best_score / total
        confidence = min(0.96, 0.60 + 0.12 * len(terms_by_label[best_label]) + 0.18 * dominance)
        secondary = [
            EventLabel(label) for label, _ in ranked[1:3] if scores[label] >= best_score * 0.65
        ]
        return EventResult(
            label=EventLabel(best_label),
            confidence=round(confidence, 4),
            secondary_labels=secondary,
            matched_terms=terms_by_label[best_label],
            backend=self.backend,
        )
