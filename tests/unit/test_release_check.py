from __future__ import annotations

import runpy
from pathlib import Path

submission_issues = runpy.run_path(
    str(Path(__file__).resolve().parents[2] / "scripts/release_check.py")
)["submission_issues"]


def test_submission_issues_reject_placeholders() -> None:
    readme = """
**Candidate Name:** `[REPLACE WITH FULL NAME]`
**College Email ID:** `[REPLACE WITH COLLEGE EMAIL]`
**College / Campus:** `[REPLACE WITH COLLEGE NAME]`
**Demo Video Link:** `[ADD UNLISTED YOUTUBE LINK]`

```bash
git clone <your-public-repository-url>
```
"""
    issues = submission_issues(readme, "code-to-connect", "College name to be added")
    assert len(issues) == 6


def test_submission_issues_accept_final_metadata() -> None:
    readme = """
**Candidate Name:** Alok Chandra<br>
**College Email ID:** alok@example.edu<br>
**College / Campus:** Example Institute<br>
**Demo Video Link:** https://youtu.be/example-id<br>

```bash
git clone https://github.com/alok/example-alok-chandra-hackathon.git
```
"""
    assert submission_issues(readme, "example-alok-chandra-hackathon", "Final deck") == []
