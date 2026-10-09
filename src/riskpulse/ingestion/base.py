from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from riskpulse.domain.documents import RawDocument


@dataclass(frozen=True)
class AdapterFailure:
    reason: str
    payload: dict[str, Any]


class SourceAdapter(ABC):
    name: str

    @abstractmethod
    async def fetch(self, query: str) -> AsyncIterator[RawDocument]:
        """Yield validated raw documents for a query."""
        if False:  # pragma: no cover - makes the abstract async generator type explicit
            yield RawDocument.model_construct()

    def drain_failures(self) -> list[AdapterFailure]:
        """Return recoverable record-level failures collected during the latest fetch."""
        return []
