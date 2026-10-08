from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from riskpulse.domain.documents import RawDocument
from riskpulse.processing.entity_linker import EntityLinker
from riskpulse.stress_testing.portfolio import load_portfolio

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
        f"{len(positions)} positions, and {len(manifest)} manifest entries."
    )


if __name__ == "__main__":
    main()
