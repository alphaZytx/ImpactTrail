from __future__ import annotations

from pathlib import Path

from riskpulse.processing.entity_linker import EntityLinker


def test_ticker_match_has_high_confidence() -> None:
    path = Path(__file__).resolve().parents[2] / "data/reference/companies.csv"
    matches = EntityLinker.from_csv(path).resolve("Investors discuss $NOVA after the downgrade")
    assert matches[0].name == "Nova Bank"
    assert matches[0].match_method == "ticker"
    assert matches[0].match_confidence == 0.99


def test_alias_and_multiple_entities() -> None:
    path = Path(__file__).resolve().parents[2] / "data/reference/companies.csv"
    matches = EntityLinker.from_csv(path).resolve(
        "Atlas Auto agrees to acquire Cedar Freight in an all-cash offer"
    )
    assert {match.entity_id for match in matches} == {"atlas-motors", "cedar-logistics"}


def test_unknown_entity_returns_no_match() -> None:
    path = Path(__file__).resolve().parents[2] / "data/reference/companies.csv"
    assert EntityLinker.from_csv(path).resolve("Central bank changes policy") == []
