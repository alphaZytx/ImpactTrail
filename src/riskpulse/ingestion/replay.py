from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from riskpulse.domain.documents import RawDocument
from riskpulse.ingestion.base import AdapterFailure, SourceAdapter


class ReplayAdapter(SourceAdapter):
    name = "replay"

    def __init__(self, fixture_path: Path) -> None:
        self.fixture_path = fixture_path
        self._failures: list[AdapterFailure] = []

    async def fetch(self, query: str = "") -> AsyncIterator[RawDocument]:
        del query
        self._failures.clear()
        with self.fixture_path.open("r", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                try:
                    decoded = json.loads(line)
                    if not isinstance(decoded, dict):
                        raise ValueError("record must be a JSON object")
                    payload: dict[str, Any] = decoded
                    payload["is_replay"] = True
                    yield RawDocument.model_validate(payload)
                except Exception as exc:
                    self._failures.append(
                        AdapterFailure(
                            reason=(
                                f"Invalid replay record at {self.fixture_path}:{line_number}: {exc}"
                            ),
                            payload={"line_number": line_number, "raw_record": line.rstrip()},
                        )
                    )

    def drain_failures(self) -> list[AdapterFailure]:
        failures = self._failures.copy()
        self._failures.clear()
        return failures
