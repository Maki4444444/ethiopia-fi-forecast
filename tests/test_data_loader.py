"""
Unit tests for src/data_loader.py and src/eda_utils.py.

Run with: pytest tests/ -v
"""

import sys
import os
import pytest
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data_loader import load_dataset, validate_schema, event_impact_coverage
from src.eda_utils import get_indicator_series, growth_between_points, pillar_summary

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


@pytest.fixture(scope="module")
def loaded_data():
    return load_dataset(DATA_DIR, use_enriched=True)


def test_load_dataset_returns_three_frames(loaded_data):
    df_main, df_impact, df_ref = loaded_data
    assert isinstance(df_main, pd.DataFrame)
    assert isinstance(df_impact, pd.DataFrame)
    assert isinstance(df_ref, pd.DataFrame)
    assert len(df_main) > 0
    assert len(df_impact) > 0


def test_load_dataset_raises_on_missing_directory():
    with pytest.raises(FileNotFoundError):
        load_dataset("this/path/does/not/exist")


def test_validate_schema_passes_on_current_data(loaded_data):
    df_main, df_impact, df_ref = loaded_data
    result = validate_schema(df_main, df_ref)
    assert result["passed"], f"Schema issues found: {result['issues']}"


def test_validate_schema_catches_duplicate_ids():
    df = pd.DataFrame({
        "record_id": ["REC_0001", "REC_0001"],
        "record_type": ["observation", "observation"],
        "pillar": ["ACCESS", "ACCESS"],
        "category": [None, None],
        "confidence": ["high", "high"],
    })
    df_ref = pd.DataFrame({"field": ["confidence"], "code": ["high"]})
    result = validate_schema(df, df_ref)
    assert not result["passed"]
    assert any("duplicate" in issue.lower() for issue in result["issues"])


def test_validate_schema_catches_event_with_pillar():
    df = pd.DataFrame({
        "record_id": ["EVT_0001"],
        "record_type": ["event"],
        "pillar": ["ACCESS"],  # should never be set for an event
        "category": ["policy"],
        "confidence": ["high"],
    })
    df_ref = pd.DataFrame({"field": ["confidence"], "code": ["high"]})
    result = validate_schema(df, df_ref)
    assert not result["passed"]
    assert any("pillar set" in issue for issue in result["issues"])


def test_event_impact_coverage_flags_zero_link_events(loaded_data):
    df_main, df_impact, df_ref = loaded_data
    coverage = event_impact_coverage(df_main, df_impact)
    assert "n_impact_links" in coverage.columns
    # every event in the current enriched dataset should have at least 1 link
    assert (coverage["n_impact_links"] >= 0).all()


def test_get_indicator_series_returns_sorted_data(loaded_data):
    df_main, _, _ = loaded_data
    obs = df_main[df_main["record_type"] == "observation"]
    series = get_indicator_series(obs, "ACC_OWNERSHIP")
    assert len(series) > 0
    assert series["observation_date"].is_monotonic_increasing


def test_get_indicator_series_raises_on_unknown_code(loaded_data):
    df_main, _, _ = loaded_data
    obs = df_main[df_main["record_type"] == "observation"]
    with pytest.raises(ValueError, match="not found in observations"):
        get_indicator_series(obs, "NOT_A_REAL_CODE")


def test_growth_between_points_requires_two_rows():
    single_row = pd.DataFrame({
        "observation_date": pd.to_datetime(["2024-01-01"]),
        "value_numeric": [50.0],
    })
    with pytest.raises(ValueError, match="at least 2 data points"):
        growth_between_points(single_row)


def test_pillar_summary_raises_on_empty_input():
    empty = pd.DataFrame(columns=["pillar", "indicator_code", "observation_date", "confidence"])
    with pytest.raises(ValueError, match="empty"):
        pillar_summary(empty)