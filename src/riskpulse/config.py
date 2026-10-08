from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml  # type: ignore[import-untyped]
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application settings loaded from environment variables and safe defaults."""

    model_config = SettingsConfigDict(
        env_prefix="RISKPULSE_", env_file=".env", extra="ignore", case_sensitive=False
    )

    env: Literal["development", "test", "production"] = "development"
    database_url: str = f"sqlite:///{PROJECT_ROOT / 'data/runtime/riskpulse.db'}"
    model_backend: Literal["auto", "lexicon", "finbert"] = "auto"
    event_backend: Literal["rules", "zero_shot"] = "rules"
    allow_model_downloads: bool = False
    log_level: str = "INFO"
    event_confidence_threshold: float = Field(default=0.65, ge=0, le=1)
    impact_confidence_threshold: float = Field(default=0.60, ge=0, le=1)
    stress_trigger_threshold: float = Field(default=7.0, ge=1, le=10)
    gdelt_enabled: bool = False
    bluesky_enabled: bool = False
    poll_interval_seconds: int = Field(default=300, ge=15, le=3600)
    max_text_length: int = Field(default=8000, ge=100, le=100_000)
    project_root: Path = PROJECT_ROOT
    taxonomy_path: Path = PROJECT_ROOT / "configs/event_taxonomy.yaml"
    scenarios_path: Path = PROJECT_ROOT / "configs/stress_scenarios.yaml"
    companies_path: Path = PROJECT_ROOT / "data/reference/companies.csv"
    portfolio_path: Path = PROJECT_ROOT / "data/synthetic/wholesale_portfolio.csv"

    def ensure_runtime_directories(self) -> None:
        (self.project_root / "data/runtime").mkdir(parents=True, exist_ok=True)
        (self.project_root / "data/processed").mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_runtime_directories()
    return settings


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        payload = yaml.safe_load(stream)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected mapping in configuration file: {path}")
    return payload
