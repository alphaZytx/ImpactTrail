from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class RawDocumentRecord(Base):
    __tablename__ = "raw_documents"
    __table_args__ = (
        UniqueConstraint("source", "source_record_id", name="uq_source_record"),
        Index("ix_raw_content_hash", "content_hash"),
    )

    document_id: Mapped[str] = mapped_column(String(700), primary_key=True)
    source_record_id: Mapped[str] = mapped_column(String(500))
    source: Mapped[str] = mapped_column(String(100), index=True)
    source_type: Mapped[str] = mapped_column(String(30))
    text: Mapped[str] = mapped_column(Text)
    canonical_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    content_hash: Mapped[str] = mapped_column(String(64))
    language: Mapped[str] = mapped_column(String(20), default="en")
    is_replay: Mapped[bool] = mapped_column(Boolean, default=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)


class RiskSignalRecord(Base):
    __tablename__ = "risk_signals"
    __table_args__ = (
        UniqueConstraint(
            "document_id", "entity_id", "model_version", name="uq_document_entity_model"
        ),
        Index("ix_signal_event_impact", "event_label", "impact_score"),
    )

    signal_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_cluster_id: Mapped[str] = mapped_column(String(36), index=True)
    document_id: Mapped[str] = mapped_column(String(700), index=True)
    entity_id: Mapped[str] = mapped_column(String(200), index=True)
    event_label: Mapped[str] = mapped_column(String(100), index=True)
    sentiment_score: Mapped[float] = mapped_column(Float)
    impact_score: Mapped[float] = mapped_column(Float, index=True)
    actionable: Mapped[bool] = mapped_column(Boolean, index=True)
    source: Mapped[str] = mapped_column(String(100), index=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    model_version: Mapped[str] = mapped_column(String(100))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)


class StressRunRecord(Base):
    __tablename__ = "stress_runs"
    __table_args__ = (
        UniqueConstraint(
            "event_cluster_id", "scenario_version", "portfolio_version", name="uq_stress_run"
        ),
    )

    stress_run_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    signal_id: Mapped[str] = mapped_column(String(36), index=True)
    event_cluster_id: Mapped[str] = mapped_column(String(36), index=True)
    scenario_version: Mapped[str] = mapped_column(String(50))
    portfolio_version: Mapped[str] = mapped_column(String(80))
    pnl: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)


class DeadLetterRecord(Base):
    __tablename__ = "dead_letters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(100), index=True)
    reason: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
