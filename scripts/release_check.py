from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "README.md",
    "LICENSE",
    "requirements.txt",
    "src/riskpulse/api/app.py",
    "data/README.md",
    "data/demo/mixed_source_events.jsonl",
    "data/synthetic/wholesale_portfolio.csv",
    "docs/architecture.png",
    "docs/presentation.pdf",
    "docs/model_card.md",
    "docs/data_card.md",
    "docs/demo_script.md",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ci", action="store_true")
    parser.parse_args()
    missing = [relative for relative in REQUIRED if not (ROOT / relative).exists()]
    checks = {"required_files": not missing, "missing": missing}
    presentation = ROOT / "docs/presentation.pdf"
    if presentation.exists():
        try:
            from pypdf import PdfReader

            page_count = len(PdfReader(str(presentation)).pages)
            checks["presentation_pages"] = page_count
            checks["presentation_page_count_valid"] = 5 <= page_count <= 7
        except ImportError:
            checks["presentation_pages"] = "not checked (pypdf unavailable)"
    print(json.dumps(checks, indent=2))
    if missing or checks.get("presentation_page_count_valid") is False:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
