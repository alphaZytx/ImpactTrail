from __future__ import annotations

from functools import lru_cache

from riskpulse.config import Settings, get_settings
from riskpulse.services.pipeline import RiskPipeline
from riskpulse.storage.repositories import Repository


@lru_cache(maxsize=1)
def get_repository() -> Repository:
    settings = get_settings()
    repository = Repository(settings.database_url)
    repository.init_schema()
    return repository


@lru_cache(maxsize=1)
def get_pipeline() -> RiskPipeline:
    return RiskPipeline(get_settings(), get_repository())


def build_pipeline(settings: Settings) -> RiskPipeline:
    repository = Repository(settings.database_url)
    return RiskPipeline(settings, repository)
