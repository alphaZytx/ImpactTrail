from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from riskpulse.config import Settings
from riskpulse.domain.documents import RawDocument, SourceType
from riskpulse.domain.signals import SentimentResult
from riskpulse.ingestion.replay import ReplayAdapter
from riskpulse.nlp.sentiment import LexiconSentimentAnalyzer
from riskpulse.services.pipeline import RiskPipeline
from riskpulse.storage.repositories import Repository


def test_complete_replay_is_idempotent(
    settings: Settings, repository: Repository, pipeline: RiskPipeline
) -> None:
    fixture = settings.project_root / "data/demo/mixed_source_events.jsonl"
    first = asyncio.run(pipeline.process_adapter(ReplayAdapter(fixture)))
    assert first.fetched == 9
    assert first.duplicates == 1
    assert first.failed == 0
    assert first.signals >= 8
    assert first.stress_runs >= 1

    second = asyncio.run(pipeline.process_adapter(ReplayAdapter(fixture)))
    assert second.duplicates == 9
    assert second.signals == 0
    assert second.stress_runs == 0
    metrics = repository.metrics()
    assert metrics["documents"] == 8
    assert metrics["stress_runs"] == first.stress_runs
    signals, _ = repository.list_signals(limit=100)
    nova_credit_signals = [
        signal
        for signal in signals
        if signal.entity.ticker == "NOVA" and signal.event.label.value == "credit_event"
    ]
    assert len(nova_credit_signals) == 2
    assert max(signal.metadata["corroborating_sources"] for signal in nova_credit_signals) == 2


def make_manual_document(
    source_record_id: str,
    text: str,
    published_at: datetime | None = None,
) -> RawDocument:
    return RawDocument(
        source_record_id=source_record_id,
        source="manual",
        source_type=SourceType.NEWS,
        text=text,
        published_at=published_at or datetime(2026, 10, 9, tzinfo=UTC),
    )


def test_unknown_issuer_is_inspectable_but_never_actionable(pipeline: RiskPipeline) -> None:
    result = pipeline.process_raw(
        make_manual_document(
            "unknown-credit",
            "Unknown Holdings downgraded after a default and missed payment "
            "amid a liquidity crisis",
        )
    )

    signal = result["signals"][0]
    assert signal.entity.entity_id == "unresolved"
    assert signal.entity.match_confidence == 0
    assert signal.entity.match_method == "unresolved"
    assert signal.actionable is False
    assert result["stress_runs"] == []


def test_systemic_macro_event_remains_market_wide_and_can_trigger(pipeline: RiskPipeline) -> None:
    result = pipeline.process_raw(
        make_manual_document(
            "systemic-macro",
            "Central bank signals a rate hike as inflation and recession risks increase",
        )
    )

    signal = result["signals"][0]
    assert signal.entity.entity_id == "market-wide"
    assert signal.actionable is True
    assert signal.impact.score > pipeline.settings.stress_trigger_threshold
    assert len(result["stress_runs"]) == 1


def test_rate_cut_does_not_trigger_opposite_rate_rise_scenario(pipeline: RiskPipeline) -> None:
    result = pipeline.process_raw(
        make_manual_document(
            "systemic-rate-cut",
            "Central bank announces a rate cut as growth remains strong",
        )
    )

    signal = result["signals"][0]
    assert signal.event.label.value == "macroeconomic"
    assert "rate cut" in signal.event.matched_terms
    assert result["stress_runs"] == []
    assert any("direction" in warning.casefold() for warning in signal.explanation.warnings)


def test_separate_same_day_events_do_not_share_a_cluster(pipeline: RiskPipeline) -> None:
    first = pipeline.process_raw(
        make_manual_document(
            "nova-morning-default",
            "Nova Bank downgraded after a default and missed payment",
            datetime(2026, 10, 9, 1, tzinfo=UTC),
        )
    )
    second = pipeline.process_raw(
        make_manual_document(
            "nova-evening-insolvency",
            "Nova Bank faces insolvency after a separate covenant breach",
            datetime(2026, 10, 9, 20, tzinfo=UTC),
        )
    )

    assert first["signals"][0].event_cluster_id != second["signals"][0].event_cluster_id
    assert len(first["stress_runs"]) == 1
    assert len(second["stress_runs"]) == 1


def test_inference_failure_does_not_strand_document(
    pipeline: RiskPipeline, repository: Repository
) -> None:
    class FailingSentimentAnalyzer:
        def analyze(self, text: str) -> SentimentResult:
            del text
            raise RuntimeError("temporary inference failure")

    document = make_manual_document(
        "retry-after-inference-failure",
        "Nova Bank downgraded after a default and missed payment",
    )
    pipeline.sentiment_analyzer = FailingSentimentAnalyzer()

    with pytest.raises(RuntimeError, match="temporary inference failure"):
        pipeline.process_raw(document)
    assert repository.metrics()["documents"] == 0

    pipeline.sentiment_analyzer = LexiconSentimentAnalyzer()
    retry = pipeline.process_raw(document)
    assert retry["duplicate"] is False
    assert len(retry["signals"]) == 1


def test_replay_skips_bad_records_and_continues(
    tmp_path: Path, pipeline: RiskPipeline, repository: Repository
) -> None:
    valid = make_manual_document(
        "valid-after-bad-records",
        "Nova Bank downgraded after a default and missed payment",
    ).model_dump(mode="json")
    fixture = tmp_path / "mixed-quality.jsonl"
    fixture.write_text(
        "not-json\n"
        + json.dumps({"source_record_id": "missing-required-fields"})
        + "\n"
        + json.dumps(valid)
        + "\n",
        encoding="utf-8",
    )

    summary = asyncio.run(pipeline.process_adapter(ReplayAdapter(fixture)))

    assert summary.fetched == 1
    assert summary.processed == 1
    assert summary.failed == 2
    assert summary.signals == 1
    assert repository.metrics()["dead_letters"] == 2
