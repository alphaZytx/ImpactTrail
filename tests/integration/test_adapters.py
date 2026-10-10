from __future__ import annotations

import asyncio

import httpx

from impacttrail.ingestion.bluesky import BlueskyAdapter
from impacttrail.ingestion.gdelt import GdeltAdapter


async def collect(adapter: object, query: str) -> list[object]:
    return [item async for item in adapter.fetch(query)]  # type: ignore[attr-defined]


def test_gdelt_adapter_maps_provider_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["query"] == "Nova Bank"
        return httpx.Response(
            200,
            json={
                "articles": [
                    {
                        "url": "https://example.org/a",
                        "title": "Nova Bank reports growth",
                        "seendate": "20261008T080000Z",
                        "domain": "example.org",
                        "language": "English",
                        "sourcecountry": "US",
                    }
                ]
            },
        )

    records = asyncio.run(
        collect(GdeltAdapter(transport=httpx.MockTransport(handler)), "Nova Bank")
    )
    assert len(records) == 1
    assert records[0].source == "gdelt"  # type: ignore[attr-defined]


def test_bluesky_adapter_maps_provider_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["q"] == "$NOVA"
        return httpx.Response(
            200,
            json={
                "posts": [
                    {
                        "uri": "at://did:plc:demo/app.bsky.feed.post/1",
                        "author": {"handle": "demo.example"},
                        "record": {"text": "$NOVA upgraded", "createdAt": "2026-10-08T08:00:00Z"},
                        "likeCount": 4,
                    }
                ]
            },
        )

    records = asyncio.run(collect(BlueskyAdapter(transport=httpx.MockTransport(handler)), "$NOVA"))
    assert len(records) == 1
    assert records[0].source_type.value == "social"  # type: ignore[attr-defined]


def test_gdelt_adapter_retries_rate_limit() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, headers={"retry-after": "0"})
        return httpx.Response(200, json={"articles": []})

    records = asyncio.run(collect(GdeltAdapter(transport=httpx.MockTransport(handler)), "markets"))
    assert records == []
    assert calls == 2
