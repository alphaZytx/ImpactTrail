from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from riskpulse.config import load_yaml
from riskpulse.domain.portfolio import AssetType, PortfolioPosition
from riskpulse.domain.signals import EventLabel, EventResult, RiskSignal
from riskpulse.domain.stress import ShockSet, StressPositionResult, StressRun
from riskpulse.stress_testing.portfolio import load_portfolio, portfolio_version


class StressTestingService:
    def __init__(
        self, scenarios_path: Path, portfolio_path: Path, trigger_threshold: float
    ) -> None:
        config = load_yaml(scenarios_path)
        self.scenario_version = str(config["version"])
        self.scenarios: dict[str, dict[str, Any]] = config["scenarios"]
        self.trigger_threshold = trigger_threshold
        self.portfolio_path = portfolio_path
        self.positions = load_portfolio(portfolio_path)
        self.portfolio_version = portfolio_version(portfolio_path)

    def is_eligible(self, signal: RiskSignal) -> bool:
        return (
            signal.actionable
            and signal.impact.score > self.trigger_threshold
            and signal.event.label.value in self.scenarios
            and self.direction_is_supported(signal.event)
        )

    @staticmethod
    def direction_is_supported(event: EventResult) -> bool:
        """Prevent a rate-cut narrative from selecting the adverse rate-rise scenario."""
        matched_terms = {term.casefold() for term in event.matched_terms}
        return not (
            event.label == EventLabel.MACROECONOMIC
            and "rate cut" in matched_terms
            and "rate hike" not in matched_terms
        )

    def run(self, signal: RiskSignal) -> StressRun | None:
        if not self.is_eligible(signal):
            return None
        scenario = self.scenarios[signal.event.label.value]
        base_shocks = ShockSet.model_validate(scenario["shocks"])
        severity_multiplier = signal.impact.score / 10
        results = [
            self._value_position(position, signal, base_shocks, severity_multiplier)
            for position in self.positions
        ]
        pre_value = round(sum(item.pre_stress_value for item in results), 2)
        post_value = round(sum(item.post_stress_value for item in results), 2)
        pnl = round(sum(item.pnl for item in results), 2)
        reconciliation_error = round((post_value - pre_value) - pnl, 6)
        run_key = f"{signal.event_cluster_id}:{self.scenario_version}:{self.portfolio_version}"
        return StressRun(
            stress_run_id=uuid5(NAMESPACE_URL, run_key),
            signal_id=signal.signal_id,
            event_cluster_id=signal.event_cluster_id,
            scenario_version=self.scenario_version,
            scenario_name=str(scenario["name"]),
            scenario_description=str(scenario["description"]),
            trigger_impact=signal.impact.score,
            severity_multiplier=severity_multiplier,
            base_shocks=base_shocks,
            created_at=datetime.now(UTC),
            pre_stress_value=pre_value,
            post_stress_value=post_value,
            pnl=pnl,
            pnl_percent=round(pnl / pre_value if pre_value else 0, 6),
            reconciliation_error=reconciliation_error,
            position_results=results,
            assumptions=[
                "Illustrative scenario, not regulatory stress testing.",
                "Loan loss uses the change in expected loss (EAD x PD x LGD).",
                "Bond loss uses duration/convexity plus credit-spread approximation.",
                "Derivative loss uses first-order delta/DV01 sensitivities.",
                "All positions are fictional and values are expressed in USD-equivalent units.",
            ],
        )

    def _value_position(
        self,
        position: PortfolioPosition,
        signal: RiskSignal,
        shocks: ShockSet,
        severity: float,
    ) -> StressPositionResult:
        match = self._exposure_match(position, signal)
        factor = severity * match
        applied = {
            "equity_pct": shocks.equity_pct * factor,
            "rates_bps": shocks.rates_bps * factor,
            "credit_spread_bps": shocks.credit_spread_bps * factor,
            "pd_multiplier": 1 + (shocks.pd_multiplier - 1) * factor,
            "fx_pct": shocks.fx_pct * factor,
        }
        if position.asset_type == AssetType.LOAN:
            pd = float(position.probability_of_default or 0)
            lgd = float(position.loss_given_default or 0)
            stressed_pd = min(1.0, pd * applied["pd_multiplier"])
            pnl = -(position.notional * stressed_pd * lgd - position.notional * pd * lgd)
            method = "change_in_expected_loss"
        elif position.asset_type == AssetType.BOND:
            duration = float(position.duration_years or 0)
            convexity = float(position.convexity or 0)
            yield_change = (applied["rates_bps"] + applied["credit_spread_bps"]) / 10_000
            return_change = -duration * yield_change + 0.5 * convexity * yield_change**2
            pnl = position.market_value * return_change
            method = "duration_convexity_and_spread"
        else:
            derivative_type = (position.derivative_type or "").casefold()
            if derivative_type == "equity":
                pnl = float(position.equity_delta or 0) * applied["equity_pct"]
                method = "equity_delta"
            elif derivative_type == "rates":
                pnl = -float(position.dv01 or 0) * applied["rates_bps"]
                method = "signed_dv01"
            else:
                pnl = float(position.fx_delta or 0) * applied["fx_pct"]
                method = "fx_delta"
        pnl = round(pnl, 2)
        post_value = round(position.market_value + pnl, 2)
        return StressPositionResult(
            asset_id=position.asset_id,
            asset_type=position.asset_type.value,
            sector=position.sector,
            country=position.country,
            pre_stress_value=round(position.market_value, 2),
            post_stress_value=post_value,
            pnl=pnl,
            pnl_percent=round(pnl / position.market_value if position.market_value else 0, 6),
            exposure_match=match,
            applied_shocks={key: round(value, 6) for key, value in applied.items()},
            calculation_method=method,
        )

    @staticmethod
    def _exposure_match(position: PortfolioPosition, signal: RiskSignal) -> float:
        entity = signal.entity
        if entity.entity_id == "market-wide":
            return 1.0
        if position.fictional_counterparty.casefold() == entity.name.casefold():
            return 1.0
        if entity.sector and position.sector.casefold() == entity.sector.casefold():
            return 0.60
        if entity.country and position.country.casefold() == entity.country.casefold():
            return 0.40
        return 0.15
