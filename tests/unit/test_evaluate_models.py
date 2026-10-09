from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load_evaluation_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "riskpulse_evaluate_models", ROOT / "scripts/evaluate_models.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load scripts/evaluate_models.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


evaluation = load_evaluation_module()
evaluate = evaluation.evaluate
mean_absolute_error = evaluation.mean_absolute_error
pearson_correlation = evaluation.pearson_correlation
per_label_mean_absolute_error = evaluation.per_label_mean_absolute_error


def test_numeric_metric_helpers() -> None:
    actual = [1.0, 2.0, 3.0]

    assert mean_absolute_error(actual, [1.0, 1.0, 5.0]) == pytest.approx(1.0)
    assert pearson_correlation(actual, [2.0, 4.0, 6.0]) == pytest.approx(1.0)
    assert pearson_correlation(actual, [6.0, 4.0, 2.0]) == pytest.approx(-1.0)
    assert pearson_correlation(actual, [4.0, 4.0, 4.0]) is None
    assert pearson_correlation([4.0, 4.0, 4.0], actual) is None


def test_metric_helpers_reject_invalid_shapes() -> None:
    with pytest.raises(ValueError, match="same number"):
        mean_absolute_error([1.0], [1.0, 2.0])
    with pytest.raises(ValueError, match="at least one"):
        pearson_correlation([], [])
    with pytest.raises(ValueError, match="labels and values"):
        per_label_mean_absolute_error([1.0], [1.0], [])


def test_per_label_mean_absolute_error() -> None:
    result = per_label_mean_absolute_error(
        [2.0, 4.0, 8.0],
        [1.0, 7.0, 6.0],
        ["credit", "credit", "macro"],
    )

    assert result == {"credit": 2.0, "macro": 2.0}


def test_evaluate_reports_impact_metrics_and_protocol() -> None:
    result = evaluate()
    impact = result["impact"]

    assert isinstance(impact, dict)
    assert "not measure production generalization" in result["evaluation_notice"]
    assert impact["samples"] == 20
    assert impact["mae"] == pytest.approx(1.15)
    assert -1.0 <= impact["pearson_correlation"] <= 1.0
    assert set(impact["per_event_label_mae"]) == {
        "climate_natural_hazard",
        "credit_event",
        "earnings_guidance",
        "geopolitical",
        "macroeconomic",
        "merger_acquisition",
        "operational_cyber",
        "other",
        "product_launch",
        "regulatory_legal",
    }
    assert impact["assumptions"] == {
        "document_shape": "synthetic GDELT-shaped English news record",
        "source": "gdelt",
        "fixed_timestamp_utc": "2026-10-08T00:00:00+00:00",
        "entity": "fixed synthetic evaluation entity",
        "entity_relevance": 1.0,
        "corroborating_sources": 1,
        "novelty": 1.0,
        "sentiment_input": "financial_lexicon_v1",
        "event_input": "taxonomy_rules_v1",
        "target": "human-specified synthetic severity rubric, not observed market movement",
        "pearson_zero_variance_policy": (
            "null if gold or predicted impact scores have zero variance"
        ),
    }
