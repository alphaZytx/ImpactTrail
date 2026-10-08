from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SentimentLabel(StrEnum):
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"


class EventLabel(StrEnum):
    GEOPOLITICAL = "geopolitical"
    MACROECONOMIC = "macroeconomic"
    CREDIT_EVENT = "credit_event"
    MERGER_ACQUISITION = "merger_acquisition"
    PRODUCT_LAUNCH = "product_launch"
    REGULATORY_LEGAL = "regulatory_legal"
    OPERATIONAL_CYBER = "operational_cyber"
    EARNINGS_GUIDANCE = "earnings_guidance"
    CLIMATE_NATURAL_HAZARD = "climate_natural_hazard"
    OTHER = "other"


class EntityMatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_id: str
    name: str
    ticker: str | None = None
    sector: str | None = None
    country: str | None = None
    match_confidence: float = Field(ge=0, le=1)
    match_method: str


class SourceReference(BaseModel):
    name: str
    type: str
    url: str | None = None


class SentimentResult(BaseModel):
    score: float = Field(ge=-1, le=1)
    label: SentimentLabel
    confidence: float = Field(ge=0, le=1)
    probabilities: dict[str, float]
    backend: str


class EventResult(BaseModel):
    label: EventLabel
    confidence: float = Field(ge=0, le=1)
    secondary_labels: list[EventLabel] = Field(default_factory=list)
    matched_terms: list[str] = Field(default_factory=list)
    backend: str


class ImpactResult(BaseModel):
    score: float = Field(ge=1, le=10)
    confidence: float = Field(ge=0, le=1)
    horizon: str = "short_term"
    components: dict[str, float]


class Explanation(BaseModel):
    evidence_excerpt: str
    reason_codes: list[str]
    warnings: list[str] = Field(default_factory=list)


class RiskSignal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    signal_id: UUID
    event_cluster_id: UUID
    document_id: str
    source: SourceReference
    entity: EntityMatch
    sentiment: SentimentResult
    event: EventResult
    impact: ImpactResult
    explanation: Explanation
    published_at: datetime
    created_at: datetime
    model_version: str = "risk-engine-1.0.0"
    actionable: bool
    metadata: dict[str, Any] = Field(default_factory=dict)


class SignalList(BaseModel):
    items: list[RiskSignal]
    total: int
    limit: int
    offset: int
