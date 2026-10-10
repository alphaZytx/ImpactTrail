from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from impacttrail.config import load_yaml
from impacttrail.domain.signals import EventLabel, EventResult

_KEYWORD_VARIANTS = {
    "launch": ("launch", "launches", "launched", "launching"),
}


def _matched_keyword(text: str, keyword: str) -> str | None:
    variants = _KEYWORD_VARIANTS.get(keyword, (keyword,))
    pattern = "|".join(re.escape(variant) for variant in variants)
    match = re.search(rf"(?<!\w)(?:{pattern})(?!\w)", text)
    return match.group(0) if match else None


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
            matches: list[str] = []
            matched_surfaces: list[str] = []
            for term in definition.get("keywords", []):
                keyword = str(term).casefold()
                matched_surface = _matched_keyword(lowered, keyword)
                if matched_surface:
                    matches.append(keyword)
                    matched_surfaces.append(matched_surface)
            terms_by_label[label] = matches
            if matches:
                longest_bonus = min(max(map(len, matched_surfaces)) / 30, 0.35)
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
