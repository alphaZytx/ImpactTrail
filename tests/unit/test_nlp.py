from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from riskpulse.domain.documents import NormalizedDocument, SourceType
from riskpulse.domain.signals import EntityMatch, EventLabel, SentimentLabel
from riskpulse.nlp.event_classifier import RuleEventClassifier
from riskpulse.nlp.impact import ImpactScorer
from riskpulse.nlp.sentiment import LexiconSentimentAnalyzer, build_sentiment_analyzer

ROOT = Path(__file__).resolve().parents[2]


def test_sentiment_direction_and_ranges() -> None:
    analyzer = LexiconSentimentAnalyzer()
    positive = analyzer.analyze("record profit growth and raised guidance")
    negative = analyzer.analyze("default after missed payment and liquidity crisis")
    neutral = analyzer.analyze("company holds annual meeting")
    assert positive.label == SentimentLabel.POSITIVE and positive.score > 0
    assert negative.label == SentimentLabel.NEGATIVE and negative.score < 0
    assert neutral.label == SentimentLabel.NEUTRAL and neutral.score == 0
    assert all(0 <= item.confidence <= 1 for item in (positive, negative, neutral))


def test_auto_backend_falls_back_without_transformers() -> None:
    analyzer = build_sentiment_analyzer("lexicon")
    assert isinstance(analyzer, LexiconSentimentAnalyzer)


def test_event_classifier_core_categories_and_abstention() -> None:
    classifier = RuleEventClassifier(ROOT / "configs/event_taxonomy.yaml")
    assert classifier.classify("sanctions follow border conflict").label == EventLabel.GEOPOLITICAL
    assert classifier.classify("issuer default and bankruptcy").label == EventLabel.CREDIT_EVENT
    assert classifier.classify("routine community meeting").label == EventLabel.OTHER


def test_product_launch_inflections_are_boundary_safe() -> None:
    classifier = RuleEventClassifier(ROOT / "configs/event_taxonomy.yaml")
    assert (
        classifier.classify(
            "Aeon Technologies launches an approved cloud security product "
            "after strong revenue growth"
        ).label
        == EventLabel.PRODUCT_LAUNCH
    )
    assert classifier.classify("Company expands its launchpad facility").label == EventLabel.OTHER


def test_impact_is_explainable_and_bounded() -> None:
    classifier = RuleEventClassifier(ROOT / "configs/event_taxonomy.yaml")
    sentiment = LexiconSentimentAnalyzer().analyze("downgrade after default and missed payment")
    event = classifier.classify("downgrade after default and missed payment")
    document = NormalizedDocument(
        document_id="gdelt:1",
        source_record_id="1",
        source="gdelt",
        source_type=SourceType.NEWS,
        text="downgrade after default and missed payment",
        published_at=datetime(2026, 1, 1, tzinfo=UTC),
        ingested_at=datetime(2026, 1, 1, tzinfo=UTC),
        content_hash="a" * 64,
    )
    entity = EntityMatch(
        entity_id="nova-bank",
        name="Nova Bank",
        ticker="NOVA",
        sector="Financials",
        country="United States",
        match_confidence=0.99,
        match_method="ticker",
    )
    result = ImpactScorer(ROOT / "configs/event_taxonomy.yaml").score(
        document, entity, sentiment, event, corroborating_sources=2
    )
    assert 7 < result.score <= 10
    assert result.confidence >= 0.6
    assert set(result.components) == {
        "event_severity",
        "entity_relevance",
        "sentiment_intensity",
        "model_confidence",
        "corroboration",
        "novelty",
        "source_quality",
    }
