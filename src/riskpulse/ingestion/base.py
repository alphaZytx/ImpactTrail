from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from riskpulse.domain.documents import RawDocument


class SourceAdapter(ABC):
    name: str

    @abstractmethod
    async def fetch(self, query: str) -> AsyncIterator[RawDocument]:
        """Yield validated raw documents for a query."""
        if False:  # pragma: no cover - makes the abstract async generator type explicit
            yield RawDocument.model_construct()
