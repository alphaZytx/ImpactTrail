from __future__ import annotations

from pathlib import Path

import pytest

from riskpulse.config import Settings
from riskpulse.nlp.sentiment import LexiconSentimentAnalyzer
from riskpulse.services.pipeline import RiskPipeline
from riskpulse.storage.repositories import Repository


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        env="test",
        database_url=f"sqlite:///{tmp_path / 'riskpulse-test.db'}",
        model_backend="lexicon",
    )


@pytest.fixture
def repository(settings: Settings) -> Repository:
    repository = Repository(settings.database_url)
    repository.init_schema()
    return repository


@pytest.fixture
def pipeline(settings: Settings, repository: Repository) -> RiskPipeline:
    return RiskPipeline(settings, repository, LexiconSentimentAnalyzer())
