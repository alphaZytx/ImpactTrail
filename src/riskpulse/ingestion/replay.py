from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path

from riskpulse.domain.documents import RawDocument
from riskpulse.ingestion.base import SourceAdapter


class ReplayAdapter(SourceAdapter):
    name = "replay"

    def __init__(self, fixture_path: Path) -> None:
        self.fixture_path = fixture_path

    async def fetch(self, query: str = "") -> AsyncIterator[RawDocument]:
        del query
        with self.fixture_path.open("r", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                payload = json.loads(line)
                payload["is_replay"] = True
                try:
                    yield RawDocument.model_validate(payload)
                except Exception as exc:
                    raise ValueError(
                        f"Invalid replay record at {self.fixture_path}:{line_number}: {exc}"
                    ) from exc
