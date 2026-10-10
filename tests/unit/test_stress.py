from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from impacttrail.domain.signals import (
    EntityMatch,
    EventLabel,
    EventResult,
    Explanation,
    ImpactResult,
    RiskSignal,
    SentimentLabel,
    SentimentResult,
    SourceReference,
)
from impacttrail.stress_testing.service import StressTestingService

ROOT = Path(__file__).resolve().parents[2]


def make_signal(impact: float = 9.0, label: EventLabel = EventLabel.CREDIT_EVENT) -> RiskSignal:
    now = datetime.now(UTC)
    return RiskSignal(
        signal_id=uuid4(),
        event_cluster_id=uuid4(),
        document_id="gdelt:credit",
        source=SourceReference(name="gdelt", type="news"),
        entity=EntityMatch(
            entity_id="nova-bank",
            name="Nova Bank",
            ticker="NOVA",
            sector="Financials",
            country="United States",
            match_confidence=0.99,
            match_method="ticker",
        ),
        sentiment=SentimentResult(
            score=-0.8,
            label=SentimentLabel.NEGATIVE,
            confidence=0.9,
            probabilities={"negative": 0.9, "neutral": 0.08, "positive": 0.02},
            backend="test",
        ),
        event=EventResult(label=label, confidence=0.9, backend="test"),
        impact=ImpactResult(score=impact, confidence=0.85, components={}),
        explanation=Explanation(evidence_excerpt="credit event", reason_codes=["CREDIT_EVENT"]),
        published_at=now,
        created_at=now,
        actionable=True,
    )


def service() -> StressTestingService:
    return StressTestingService(
        ROOT / "configs/stress_scenarios.yaml",
        ROOT / "data/synthetic/wholesale_portfolio.csv",
        7.0,
    )


def test_strict_trigger_boundary() -> None:
    assert service().run(make_signal(7.0)) is None
    assert service().run(make_signal(7.1)) is not None


def test_unknown_scenario_does_not_run() -> None:
    assert service().run(make_signal(9.0, EventLabel.PRODUCT_LAUNCH)) is None


def test_rate_cut_does_not_select_adverse_rate_rise_scenario() -> None:
    signal = make_signal(9.0, EventLabel.MACROECONOMIC)
    signal.event.matched_terms = ["central bank", "rate cut"]
    assert service().run(signal) is None

    signal.event.matched_terms = ["central bank", "rate hike"]
    assert service().run(signal) is not None


def test_stress_run_reconciles_and_covers_asset_classes() -> None:
    run = service().run(make_signal())
    assert run is not None
    assert abs(run.reconciliation_error) <= 0.01
    assert round(run.post_stress_value - run.pre_stress_value, 2) == round(run.pnl, 2)
    assert {result.asset_type for result in run.position_results} == {
        "loan",
        "bond",
        "derivative",
    }
    assert run.pnl < 0
