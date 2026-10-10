from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from impacttrail.domain.documents import RawDocument
from impacttrail.processing.entity_linker import EntityLinker
from impacttrail.stress_testing.portfolio import load_portfolio

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    replay_path = ROOT / "data/demo/mixed_source_events.jsonl"
    with replay_path.open("r", encoding="utf-8") as stream:
        replay_records = [
            RawDocument.model_validate(json.loads(line)) for line in stream if line.strip()
        ]
    assert {item.source_type.value for item in replay_records} == {"news", "social"}
    assert len(replay_records) >= 8

    linker = EntityLinker.from_csv(ROOT / "data/reference/companies.csv")
    assert len(linker.entities) >= 10

    positions = load_portfolio(ROOT / "data/synthetic/wholesale_portfolio.csv")
    assert {position.asset_type.value for position in positions} == {"loan", "bond", "derivative"}
    assert len(positions) >= 60

    with (ROOT / "data/evaluation/sentiment_gold.csv").open(
        "r", encoding="utf-8", newline=""
    ) as stream:
        sentiment_rows = list(csv.DictReader(stream))
    sentiment_support = Counter(row["label"] for row in sentiment_rows)
    assert sentiment_support == {"positive": 30, "neutral": 30, "negative": 30}
    assert len({row["example_id"] for row in sentiment_rows}) == len(sentiment_rows)
    assert len({row["text"] for row in sentiment_rows}) == len(sentiment_rows)

    with (ROOT / "data/evaluation/events_gold.csv").open(
        "r", encoding="utf-8", newline=""
    ) as stream:
        event_rows = list(csv.DictReader(stream))
    event_support = Counter(row["label"] for row in event_rows)
    assert len(event_support) == 10
    assert set(event_support.values()) == {10}
    assert len({row["example_id"] for row in event_rows}) == len(event_rows)
    assert len({row["text"] for row in event_rows}) == len(event_rows)
    assert all(1 <= float(row["impact_score"]) <= 10 for row in event_rows)

    manifest_path = ROOT / "data/manifests/data_manifest.csv"
    with manifest_path.open("r", encoding="utf-8", newline="") as stream:
        manifest = list(csv.DictReader(stream))
    for row in manifest:
        path = ROOT / "data" / row["path"]
        assert path.exists(), path
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == row["sha256"], f"Hash mismatch: {path}"
    print(
        f"Validated {len(replay_records)} replay records, {len(linker.entities)} entities, "
        f"{len(positions)} positions, {len(sentiment_rows)} sentiment examples, "
        f"{len(event_rows)} event examples, and {len(manifest)} manifest entries."
    )


if __name__ == "__main__":
    main()
