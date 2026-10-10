from __future__ import annotations

import asyncio
from typing import Any

import httpx


async def get_json_with_retry(
    client: httpx.AsyncClient,
    url: str,
    params: dict[str, str | int],
    attempts: int = 3,
) -> dict[str, Any]:
    """Fetch a JSON object with bounded retries for transient provider failures."""
    if attempts < 1:
        raise ValueError("attempts must be at least 1")

    for attempt in range(attempts):
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("Expected a JSON object from source provider")
            return payload
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            status = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
            retryable = status is None or status == 429 or status >= 500
            if not retryable or attempt == attempts - 1:
                raise
            retry_after = (
                exc.response.headers.get("retry-after")
                if isinstance(exc, httpx.HTTPStatusError)
                else None
            )
            delay = (
                float(retry_after) if retry_after and retry_after.isdigit() else 0.2 * 2**attempt
            )
            await asyncio.sleep(min(delay, 2.0))

    raise RuntimeError("Unreachable retry state")
