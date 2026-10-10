from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "README.md",
    "LICENSE",
    "requirements.txt",
    "src/impacttrail/api/app.py",
    "data/README.md",
    "data/demo/mixed_source_events.jsonl",
    "data/synthetic/wholesale_portfolio.csv",
    "docs/architecture.png",
    "docs/presentation.pdf",
    "docs/as_built.md",
    "docs/model_card.md",
    "docs/data_card.md",
    "docs/demo_script.md",
    "docs/jury_qa.md",
]

PLACEHOLDER_MARKERS = (
    "[replace",
    "[add",
    "<your-",
    "to be added",
    "placeholder",
)


def _readme_field(readme: str, label: str) -> str:
    match = re.search(rf"^\*\*{re.escape(label)}:\*\*\s*(.+?)\s*$", readme, flags=re.MULTILINE)
    if not match:
        return ""
    return re.sub(r"<br\s*/?>$", "", match.group(1).strip(), flags=re.IGNORECASE).strip()


def _is_placeholder(value: str) -> bool:
    lowered = value.casefold()
    return not value or any(marker in lowered for marker in PLACEHOLDER_MARKERS)


def submission_issues(readme: str, repository_directory: str, deck_text: str = "") -> list[str]:
    """Return actionable blockers that would make the final package unsafe to submit."""
    issues: list[str] = []
    required_fields = {
        "candidate name": _readme_field(readme, "Candidate Name"),
        "college email": _readme_field(readme, "College Email ID"),
        "college / campus": _readme_field(readme, "College / Campus"),
        "demo video": _readme_field(readme, "Demo Video Link"),
    }
    for label, value in required_fields.items():
        if _is_placeholder(value):
            issues.append(f"README {label} is missing or still a placeholder")

    email = required_fields["college email"].strip("`[] ")
    if not _is_placeholder(required_fields["college email"]) and not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+", email
    ):
        issues.append("README college email is not a valid email address")

    video = required_fields["demo video"].strip("`[] ")
    if not _is_placeholder(required_fields["demo video"]) and not re.search(
        r"https://(?:www\.)?(?:youtube\.com|youtu\.be)/", video, flags=re.IGNORECASE
    ):
        issues.append("README demo video must be a public YouTube URL")

    clone_match = re.search(r"git clone\s+(\S+)", readme)
    clone_url = clone_match.group(1).strip("`<>") if clone_match else ""
    clone_is_valid = not _is_placeholder(clone_url) and bool(
        re.fullmatch(r"https://github\.com/[^/\s]+/[^/\s]+(?:\.git)?", clone_url)
    )
    if not clone_is_valid:
        issues.append("README Quickstart needs the final public GitHub clone URL")

    if deck_text and any(marker in deck_text.casefold() for marker in PLACEHOLDER_MARKERS):
        issues.append("presentation cover still contains placeholder text")
    return issues


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ci", action="store_true")
    parser.add_argument(
        "--submission",
        action="store_true",
        help="Fail on candidate, public repository, video, or deck placeholders",
    )
    args = parser.parse_args()
    missing = [relative for relative in REQUIRED if not (ROOT / relative).exists()]
    checks = {"required_files": not missing, "missing": missing}
    presentation = ROOT / "docs/presentation.pdf"
    deck_text = ""
    if presentation.exists():
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(presentation))
            page_count = len(reader.pages)
            checks["presentation_pages"] = page_count
            checks["presentation_page_count_valid"] = 5 <= page_count <= 7
            deck_text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            checks["presentation_pages"] = "not checked (pypdf unavailable)"
    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
    issues = submission_issues(readme, ROOT.name, deck_text)
    checks["submission_ready"] = not issues
    checks["submission_issues"] = issues
    checks["strict_submission_mode"] = args.submission
    print(json.dumps(checks, indent=2))
    if (
        missing
        or checks.get("presentation_page_count_valid") is False
        or (args.submission and issues)
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
