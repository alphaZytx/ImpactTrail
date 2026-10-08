from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AssetType(StrEnum):
    LOAN = "loan"
    BOND = "bond"
    DERIVATIVE = "derivative"


class PortfolioPosition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: str
    asset_type: AssetType
    derivative_type: str | None = None
    fictional_counterparty: str
    sector: str
    country: str
    currency: str = Field(min_length=3, max_length=3)
    notional: float = Field(gt=0)
    market_value: float
    rating: str
    maturity_date: date
    duration_years: float | None = Field(default=None, ge=0)
    convexity: float | None = Field(default=None, ge=0)
    probability_of_default: float | None = Field(default=None, ge=0, le=1)
    loss_given_default: float | None = Field(default=None, ge=0, le=1)
    equity_delta: float | None = None
    dv01: float | None = None
    fx_delta: float | None = None

    @model_validator(mode="after")
    def validate_asset_specific_fields(self) -> PortfolioPosition:
        if self.asset_type == AssetType.LOAN and (
            self.probability_of_default is None or self.loss_given_default is None
        ):
            raise ValueError("Loans require probability_of_default and loss_given_default")
        if self.asset_type == AssetType.BOND and self.duration_years is None:
            raise ValueError("Bonds require duration_years")
        if self.asset_type == AssetType.DERIVATIVE and not self.derivative_type:
            raise ValueError("Derivatives require derivative_type")
        return self
