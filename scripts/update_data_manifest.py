from __future__ import annotations

import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUT = DATA / "manifests/data_manifest.csv"

SOURCES = {
    "demo/mixed_source_events.jsonl": (
        "synthetic",
        "MIT project data",
        "Deterministic demo replay",
    ),
    "evaluation/sentiment_gold.csv": (
        "synthetic",
        "MIT project data",
        "Balanced sentiment challenge evaluation",
    ),
    "evaluation/events_gold.csv": (
        "synthetic",
        "MIT project data",
        "Balanced event and impact challenge evaluation",
    ),
    "reference/companies.csv": ("synthetic", "MIT project data", "Entity registry"),
    "synthetic/wholesale_portfolio.csv": ("synthetic", "MIT project data", "Stress-test portfolio"),
}


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for relative, (source, license_name, purpose) in SOURCES.items():
        path = DATA / relative
        rows.append(
            {
                "path": relative,
                "source": source,
                "license": license_name,
                "purpose": purpose,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "generated_or_reviewed_on": "2026-10-11",
                "redistribution": "allowed",
            }
        )
    with OUTPUT.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Updated {OUTPUT}")


if __name__ == "__main__":
    main()
