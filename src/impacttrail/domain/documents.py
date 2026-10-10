from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


class SourceType(StrEnum):
    NEWS = "news"
    SOCIAL = "social"


class RawDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_record_id: str = Field(min_length=1, max_length=500)
    source: str = Field(min_length=1, max_length=100)
    source_type: SourceType
    text: str = Field(min_length=1, max_length=100_000)
    url: HttpUrl | None = None
    published_at: datetime
    ingested_at: datetime = Field(default_factory=utc_now)
    author: str | None = Field(default=None, max_length=300)
    raw_metadata: dict[str, Any] = Field(default_factory=dict)
    is_replay: bool = False

    @field_validator("published_at", "ingested_at")
    @classmethod
    def timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


class NormalizedDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    source_record_id: str
    source: str
    source_type: SourceType
    text: str
    canonical_url: str | None = None
    published_at: datetime
    ingested_at: datetime
    author: str | None = None
    language: str = "en"
    content_hash: str
    raw_metadata: dict[str, Any] = Field(default_factory=dict)
    is_replay: bool = False
