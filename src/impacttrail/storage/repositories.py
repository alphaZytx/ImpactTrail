from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import and_, create_engine, delete, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from impacttrail.domain.documents import NormalizedDocument
from impacttrail.domain.signals import RiskSignal
from impacttrail.domain.stress import StressRun
from impacttrail.storage.models import (
    Base,
    DeadLetterRecord,
    RawDocumentRecord,
    RiskSignalRecord,
    StressRunRecord,
)


class Repository:
    def __init__(self, database_url: str) -> None:
        if database_url.startswith("sqlite:///"):
            database_path = Path(database_url.removeprefix("sqlite:///"))
            database_path.parent.mkdir(parents=True, exist_ok=True)
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        self.engine: Engine = create_engine(database_url, connect_args=connect_args)
        self._sessions = sessionmaker(bind=self.engine, expire_on_commit=False)

    def init_schema(self) -> None:
        Base.metadata.create_all(self.engine)

    @contextmanager
    def session(self) -> Iterator[Session]:
        session = self._sessions()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def clear_runtime(self) -> None:
        self.init_schema()
        with self.session() as session:
            for model in (StressRunRecord, RiskSignalRecord, RawDocumentRecord, DeadLetterRecord):
                session.execute(delete(model))

    def save_document(self, document: NormalizedDocument) -> bool:
        self.init_schema()
        near_duplicate_start = document.published_at - timedelta(hours=24)
        near_duplicate_end = document.published_at + timedelta(hours=24)
        with self.session() as session:
            duplicate = session.scalar(
                select(RawDocumentRecord.document_id).where(
                    (RawDocumentRecord.document_id == document.document_id)
                    | and_(
                        RawDocumentRecord.content_hash == document.content_hash,
                        RawDocumentRecord.published_at >= near_duplicate_start,
                        RawDocumentRecord.published_at <= near_duplicate_end,
                    )
                )
            )
            if duplicate:
                return False
            session.add(
                RawDocumentRecord(
                    document_id=document.document_id,
                    source_record_id=document.source_record_id,
                    source=document.source,
                    source_type=document.source_type.value,
                    text=document.text,
                    canonical_url=document.canonical_url,
                    published_at=document.published_at,
                    ingested_at=document.ingested_at,
                    content_hash=document.content_hash,
                    language=document.language,
                    is_replay=document.is_replay,
                    payload=document.model_dump(mode="json"),
                )
            )
        return True

    def save_signal(self, signal: RiskSignal) -> bool:
        with self.session() as session:
            duplicate = session.scalar(
                select(RiskSignalRecord.signal_id).where(
                    RiskSignalRecord.signal_id == str(signal.signal_id)
                )
            )
            if duplicate:
                return False
            session.add(
                RiskSignalRecord(
                    signal_id=str(signal.signal_id),
                    event_cluster_id=str(signal.event_cluster_id),
                    document_id=signal.document_id,
                    entity_id=signal.entity.entity_id,
                    event_label=signal.event.label.value,
                    sentiment_score=signal.sentiment.score,
                    impact_score=signal.impact.score,
                    actionable=signal.actionable,
                    source=signal.source.name,
                    published_at=signal.published_at,
                    created_at=signal.created_at,
                    model_version=signal.model_version,
                    payload=signal.model_dump(mode="json"),
                )
            )
        return True

    def cluster_sources(self, event_cluster_id: str) -> set[str]:
        """Return providers already observed for a bounded evidence-similarity cluster."""
        with self.session() as session:
            sources = session.scalars(
                select(RiskSignalRecord.source).where(
                    RiskSignalRecord.event_cluster_id == event_cluster_id
                )
            ).all()
        return set(sources)

    def get_signal(self, signal_id: str) -> RiskSignal | None:
        with self.session() as session:
            record = session.get(RiskSignalRecord, signal_id)
            return RiskSignal.model_validate(record.payload) if record else None

    def list_signals(
        self,
        limit: int = 100,
        offset: int = 0,
        event_label: str | None = None,
        source: str | None = None,
        min_impact: float | None = None,
        actionable: bool | None = None,
    ) -> tuple[list[RiskSignal], int]:
        conditions: list[Any] = []
        if event_label:
            conditions.append(RiskSignalRecord.event_label == event_label)
        if source:
            conditions.append(RiskSignalRecord.source == source)
        if min_impact is not None:
            conditions.append(RiskSignalRecord.impact_score >= min_impact)
        if actionable is not None:
            conditions.append(RiskSignalRecord.actionable == actionable)
        with self.session() as session:
            total = int(
                session.scalar(
                    select(func.count()).select_from(RiskSignalRecord).where(*conditions)
                )
                or 0
            )
            records = session.scalars(
                select(RiskSignalRecord)
                .where(*conditions)
                .order_by(RiskSignalRecord.published_at.desc(), RiskSignalRecord.signal_id)
                .offset(offset)
                .limit(limit)
            ).all()
            return [RiskSignal.model_validate(record.payload) for record in records], total

    def save_stress_run(self, run: StressRun, portfolio_version: str) -> bool:
        with self.session() as session:
            duplicate = session.scalar(
                select(StressRunRecord.stress_run_id).where(
                    StressRunRecord.event_cluster_id == str(run.event_cluster_id),
                    StressRunRecord.scenario_version == run.scenario_version,
                    StressRunRecord.portfolio_version == portfolio_version,
                )
            )
            if duplicate:
                return False
            session.add(
                StressRunRecord(
                    stress_run_id=str(run.stress_run_id),
                    signal_id=str(run.signal_id),
                    event_cluster_id=str(run.event_cluster_id),
                    scenario_version=run.scenario_version,
                    portfolio_version=portfolio_version,
                    pnl=run.pnl,
                    created_at=run.created_at,
                    payload=run.model_dump(mode="json"),
                )
            )
        return True

    def get_stress_run(self, stress_run_id: str) -> StressRun | None:
        with self.session() as session:
            record = session.get(StressRunRecord, stress_run_id)
            return StressRun.model_validate(record.payload) if record else None

    def get_stress_run_for_signal(self, signal: RiskSignal) -> StressRun | None:
        with self.session() as session:
            record = session.scalar(
                select(StressRunRecord)
                .where(StressRunRecord.event_cluster_id == str(signal.event_cluster_id))
                .order_by(StressRunRecord.created_at.desc())
            )
            return StressRun.model_validate(record.payload) if record else None

    def list_stress_runs(self, limit: int = 100) -> list[StressRun]:
        with self.session() as session:
            records = session.scalars(
                select(StressRunRecord).order_by(StressRunRecord.created_at.desc()).limit(limit)
            ).all()
            return [StressRun.model_validate(record.payload) for record in records]

    def save_dead_letter(self, source: str, reason: str, payload: dict[str, Any]) -> None:
        self.init_schema()
        with self.session() as session:
            session.add(DeadLetterRecord(source=source, reason=reason, payload=payload))

    def metrics(self) -> dict[str, Any]:
        self.init_schema()
        with self.session() as session:
            document_count = int(
                session.scalar(select(func.count()).select_from(RawDocumentRecord)) or 0
            )
            signal_count = int(
                session.scalar(select(func.count()).select_from(RiskSignalRecord)) or 0
            )
            actionable_count = int(
                session.scalar(
                    select(func.count())
                    .select_from(RiskSignalRecord)
                    .where(RiskSignalRecord.actionable.is_(True))
                )
                or 0
            )
            stress_count = int(
                session.scalar(select(func.count()).select_from(StressRunRecord)) or 0
            )
            dead_letter_count = int(
                session.scalar(select(func.count()).select_from(DeadLetterRecord)) or 0
            )
            source_rows = session.execute(
                select(RawDocumentRecord.source, func.count()).group_by(RawDocumentRecord.source)
            ).all()
        return {
            "documents": document_count,
            "signals": signal_count,
            "actionable_signals": actionable_count,
            "stress_runs": stress_count,
            "dead_letters": dead_letter_count,
            "documents_by_source": {source: count for source, count in source_rows},
        }
