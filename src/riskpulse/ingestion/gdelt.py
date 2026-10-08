from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime

import httpx

from riskpulse.domain.documents import RawDocument, SourceType
from riskpulse.ingestion.base import SourceAdapter
from riskpulse.ingestion.http import get_json_with_retry


def _parse_gdelt_date(value: str | None) -> datetime:
    if not value:
        return datetime.now(UTC)
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%d%H%M%S"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


class GdeltAdapter(SourceAdapter):
    name = "gdelt"

    def __init__(
        self,
        base_url: str = "https://api.gdeltproject.org/api/v2/doc/doc",
        max_records: int = 25,
        timeout_seconds: float = 10,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url
        self.max_records = max_records
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    async def fetch(self, query: str) -> AsyncIterator[RawDocument]:
        params: dict[str, str | int] = {
            "query": query,
            "mode": "artlist",
            "format": "json",
            "sort": "datedesc",
            "maxrecords": self.max_records,
        }
        timeout = httpx.Timeout(self.timeout_seconds)
        async with httpx.AsyncClient(
            timeout=timeout, transport=self.transport, follow_redirects=True
        ) as client:
            payload = await get_json_with_retry(client, self.base_url, params)
        for article in payload.get("articles", []):
            url = article.get("url")
            title = str(article.get("title") or "").strip()
            if not title or not url:
                continue
            yield RawDocument(
                source_record_id=str(url),
                source="gdelt",
                source_type=SourceType.NEWS,
                text=title,
                url=url,
                published_at=_parse_gdelt_date(article.get("seendate")),
                raw_metadata={
                    "domain": article.get("domain"),
                    "language": article.get("language"),
                    "sourcecountry": article.get("sourcecountry"),
                },
            )
