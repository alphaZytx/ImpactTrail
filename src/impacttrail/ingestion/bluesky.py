from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime

import httpx
from pydantic import HttpUrl

from impacttrail.domain.documents import RawDocument, SourceType
from impacttrail.ingestion.base import SourceAdapter
from impacttrail.ingestion.http import get_json_with_retry


class BlueskyAdapter(SourceAdapter):
    name = "bluesky"

    def __init__(
        self,
        base_url: str = "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts",
        limit: int = 25,
        timeout_seconds: float = 10,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url
        self.limit = limit
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    async def fetch(self, query: str) -> AsyncIterator[RawDocument]:
        timeout = httpx.Timeout(self.timeout_seconds)
        async with httpx.AsyncClient(
            timeout=timeout, transport=self.transport, follow_redirects=True
        ) as client:
            payload = await get_json_with_retry(
                client,
                self.base_url,
                {"q": query, "limit": self.limit, "sort": "latest"},
            )
        for post in payload.get("posts", []):
            record = post.get("record") or {}
            text = str(record.get("text") or "").strip()
            uri = str(post.get("uri") or "")
            if not text or not uri:
                continue
            author = post.get("author") or {}
            handle = author.get("handle")
            rkey = uri.rsplit("/", maxsplit=1)[-1]
            url = f"https://bsky.app/profile/{handle}/post/{rkey}" if handle else None
            created = record.get("createdAt")
            published_at = (
                datetime.fromisoformat(str(created).replace("Z", "+00:00")).astimezone(UTC)
                if created
                else datetime.now(UTC)
            )
            yield RawDocument(
                source_record_id=uri,
                source="bluesky",
                source_type=SourceType.SOCIAL,
                text=text,
                url=HttpUrl(url) if url else None,
                published_at=published_at,
                author=str(handle) if handle else None,
                raw_metadata={
                    "like_count": post.get("likeCount", 0),
                    "repost_count": post.get("repostCount", 0),
                    "reply_count": post.get("replyCount", 0),
                },
            )
