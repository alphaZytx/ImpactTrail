from __future__ import annotations

import asyncio

from riskpulse.config import Settings
from riskpulse.ingestion.replay import ReplayAdapter
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
