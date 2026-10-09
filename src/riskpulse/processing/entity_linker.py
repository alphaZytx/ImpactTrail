from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from riskpulse.domain.signals import EntityMatch


@dataclass(frozen=True)
class EntityDefinition:
    entity_id: str
    name: str
    ticker: str
    aliases: tuple[str, ...]
    sector: str
    country: str


class EntityLinker:
    def __init__(self, entities: list[EntityDefinition]) -> None:
        self.entities = entities

    @classmethod
    def from_csv(cls, path: Path) -> EntityLinker:
        entities: list[EntityDefinition] = []
        with path.open("r", encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream):
                aliases = tuple(
                    alias.strip() for alias in row.get("aliases", "").split("|") if alias.strip()
                )
                entities.append(
                    EntityDefinition(
                        entity_id=row["entity_id"],
                        name=row["name"],
                        ticker=row["ticker"],
                        aliases=aliases,
                        sector=row["sector"],
                        country=row["country"],
                    )
                )
        return cls(entities)

    def resolve(self, text: str) -> list[EntityMatch]:
        lowered = text.casefold()
        matches: list[EntityMatch] = []
        for entity in self.entities:
            ticker_pattern = rf"(?<!\w)\$?{re.escape(entity.ticker)}(?!\w)"
            if re.search(ticker_pattern, text, flags=re.IGNORECASE):
                matches.append(
                    EntityMatch(
                        entity_id=entity.entity_id,
                        name=entity.name,
                        ticker=entity.ticker,
                        sector=entity.sector,
                        country=entity.country,
                        match_confidence=0.99,
                        match_method="ticker",
                    )
                )
                continue
            candidates = (entity.name, *entity.aliases)
            matched_alias = next(
                (
                    alias
                    for alias in sorted(candidates, key=len, reverse=True)
                    if re.search(rf"(?<!\w){re.escape(alias.casefold())}(?!\w)", lowered)
                ),
                None,
            )
            if matched_alias:
                matches.append(
                    EntityMatch(
                        entity_id=entity.entity_id,
                        name=entity.name,
                        ticker=entity.ticker,
                        sector=entity.sector,
                        country=entity.country,
                        match_confidence=0.96 if matched_alias == entity.name else 0.90,
                        match_method="canonical_name" if matched_alias == entity.name else "alias",
                    )
                )
        return matches

    @staticmethod
    def market_wide() -> EntityMatch:
        return EntityMatch(
            entity_id="market-wide",
            name="Market-wide",
            ticker=None,
            sector=None,
            country=None,
            match_confidence=0.85,
            match_method="market_event",
        )

    @staticmethod
    def unresolved() -> EntityMatch:
        return EntityMatch(
            entity_id="unresolved",
            name="Unresolved entity",
            ticker=None,
            sector=None,
            country=None,
            match_confidence=0.0,
            match_method="unresolved",
        )
