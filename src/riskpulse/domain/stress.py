from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ShockSet(BaseModel):
    equity_pct: float = 0
    rates_bps: float = 0
    credit_spread_bps: float = 0
    pd_multiplier: float = Field(default=1, ge=0)
    fx_pct: float = 0


class StressPositionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: str
    asset_type: str
    sector: str
    country: str
    pre_stress_value: float
    post_stress_value: float
    pnl: float
    pnl_percent: float
    exposure_match: float = Field(ge=0, le=1)
    applied_shocks: dict[str, float]
    calculation_method: str


class StressRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stress_run_id: UUID
    signal_id: UUID
    event_cluster_id: UUID
    scenario_version: str
    scenario_name: str
    scenario_description: str
    trigger_impact: float = Field(ge=1, le=10)
    severity_multiplier: float = Field(ge=0, le=1)
    base_shocks: ShockSet
    created_at: datetime
    pre_stress_value: float
    post_stress_value: float
    pnl: float
    pnl_percent: float
    reconciliation_error: float
    position_results: list[StressPositionResult]
    assumptions: list[str]
