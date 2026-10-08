from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from riskpulse.domain.portfolio import PortfolioPosition

OPTIONAL_FLOATS = {
    "duration_years",
    "convexity",
    "probability_of_default",
    "loss_given_default",
    "equity_delta",
    "dv01",
    "fx_delta",
}


def load_portfolio(path: Path) -> list[PortfolioPosition]:
    positions: list[PortfolioPosition] = []
    with path.open("r", encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            payload: dict[str, object] = dict(row)
            for field in {"notional", "market_value", *OPTIONAL_FLOATS}:
                value = row.get(field, "")
                payload[field] = None if value in {None, ""} else float(value)
            positions.append(PortfolioPosition.model_validate(payload))
    if not positions:
        raise ValueError(f"Portfolio is empty: {path}")
    return positions


def portfolio_version(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]
