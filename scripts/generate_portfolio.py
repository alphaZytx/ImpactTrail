from __future__ import annotations

import csv
import random
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/synthetic/wholesale_portfolio.csv"
SEED = 20261008

ENTITIES = [
    ("Nova Bank", "Financials", "United States", "BBB"),
    ("Aeon Technologies", "Technology", "United States", "A"),
    ("Helios Energy", "Energy", "United Kingdom", "BBB"),
    ("Meridian Retail", "Consumer", "India", "BB"),
    ("Atlas Motors", "Industrials", "Germany", "BBB"),
    ("Orion Pharma", "Healthcare", "Switzerland", "A"),
    ("Vertex Telecom", "Telecommunications", "Singapore", "BBB"),
    ("Lumen Aerospace", "Industrials", "France", "BB"),
    ("Cedar Logistics", "Logistics", "Canada", "BBB"),
    ("Terra Mining", "Materials", "Australia", "BB"),
]

FIELDS = [
    "asset_id",
    "asset_type",
    "derivative_type",
    "fictional_counterparty",
    "sector",
    "country",
    "currency",
    "notional",
    "market_value",
    "rating",
    "maturity_date",
    "duration_years",
    "convexity",
    "probability_of_default",
    "loss_given_default",
    "equity_delta",
    "dv01",
    "fx_delta",
]

PD_BY_RATING = {"A": 0.008, "BBB": 0.018, "BB": 0.045}


def build_rows() -> list[dict[str, object]]:
    rng = random.Random(SEED)
    rows: list[dict[str, object]] = []
    asset_types = ["loan"] * 32 + ["bond"] * 24 + ["derivative"] * 16
    rng.shuffle(asset_types)
    for index, asset_type in enumerate(asset_types, start=1):
        counterparty, sector, country, rating = ENTITIES[(index - 1) % len(ENTITIES)]
        notional = round(rng.uniform(2_000_000, 15_000_000), 2)
        maturity = date(2028 + index % 8, 1 + index % 12, 1 + index % 27).isoformat()
        row: dict[str, object] = {
            "asset_id": f"AST-{index:03d}",
            "asset_type": asset_type,
            "derivative_type": "",
            "fictional_counterparty": counterparty,
            "sector": sector,
            "country": country,
            "currency": "USD",
            "notional": f"{notional:.2f}",
            "market_value": f"{notional:.2f}",
            "rating": rating,
            "maturity_date": maturity,
            "duration_years": "",
            "convexity": "",
            "probability_of_default": "",
            "loss_given_default": "",
            "equity_delta": "",
            "dv01": "",
            "fx_delta": "",
        }
        if asset_type == "loan":
            row["market_value"] = f"{notional * rng.uniform(0.96, 1.0):.2f}"
            row["probability_of_default"] = f"{PD_BY_RATING[rating]:.4f}"
            row["loss_given_default"] = f"{rng.uniform(0.35, 0.55):.4f}"
        elif asset_type == "bond":
            row["market_value"] = f"{notional * rng.uniform(0.90, 1.04):.2f}"
            row["duration_years"] = f"{rng.uniform(1.5, 7.5):.4f}"
            row["convexity"] = f"{rng.uniform(2.0, 22.0):.4f}"
        else:
            derivative_type = ("equity", "rates", "fx")[(index - 1) % 3]
            row["derivative_type"] = derivative_type
            row["market_value"] = f"{notional * rng.uniform(0.02, 0.09):.2f}"
            if derivative_type == "equity":
                row["equity_delta"] = f"{notional * rng.uniform(0.35, 0.8):.2f}"
            elif derivative_type == "rates":
                row["dv01"] = f"{notional * rng.uniform(0.0002, 0.001):.2f}"
            else:
                row["fx_delta"] = f"{notional * rng.uniform(0.25, 0.75):.2f}"
        rows.append(row)
    return rows


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(build_rows())
    print(f"Generated {OUTPUT}")


if __name__ == "__main__":
    main()
