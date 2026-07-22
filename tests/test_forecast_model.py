"""
Unit tests for src/forecast_model.py.

Run with: pytest tests/ -v
"""

import sys
import os
import pytest
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.forecast_model import (
    prepare_trend_frame, fit_trend_regression, predict_with_interval,
    scenario_slopes, scenario_forecast, event_augmented_forecast,
    summarize_forecast_table,
)


@pytest.fixture
def toy_series():
    return pd.DataFrame({
        "observation_date": pd.to_datetime(["2014-12-31", "2017-12-31", "2021-12-31", "2024-11-29"]),
        "value_numeric": [22.0, 35.0, 46.0, 49.0],
    })


def test_prepare_trend_frame_adds_columns(toy_series):
    out = prepare_trend_frame(toy_series, base_year=2013)
    assert "years_since_base" in out.columns
    assert "log_years" in out.columns
    assert (out["years_since_base"] > 0).all()


def test_prepare_trend_frame_rejects_late_base_year(toy_series):
    with pytest.raises(ValueError):
        prepare_trend_frame(toy_series, base_year=2020)


def test_fit_trend_regression_requires_two_points():
    tiny = pd.DataFrame({"value_numeric": [10.0], "log_years": [1.0]})
    with pytest.raises(ValueError):
        fit_trend_regression(tiny, predictor="log_years")


def test_fit_trend_regression_fits_and_predicts(toy_series):
    frame = prepare_trend_frame(toy_series, base_year=2013)
    model = fit_trend_regression(frame, predictor="log_years")
    assert model.params["log_years"] > 0  # account ownership rising over time

    preds = predict_with_interval(model, frame["log_years"].values, predictor="log_years")
    assert len(preds) == len(frame)
    assert (preds["ci_lower"] <= preds["mean"]).all()
    assert (preds["mean"] <= preds["ci_upper"]).all()


def test_predict_with_interval_clips_to_0_100(toy_series):
    frame = prepare_trend_frame(toy_series, base_year=2013)
    model = fit_trend_regression(frame, predictor="log_years")
    # Extrapolate far into the future -- should clip rather than exceed 100
    far_future = np.log(np.array([200.0]))
    preds = predict_with_interval(model, far_future, predictor="log_years", clip_0_100=True)
    assert (preds["mean"] <= 100).all()
    assert (preds["ci_upper"] <= 100).all()


def test_scenario_slopes_ordering():
    slopes = scenario_slopes(base_slope=2.0, optimistic_mult=1.25, pessimistic_mult=0.7)
    assert slopes["Pessimistic"] < slopes["Base case"] < slopes["Optimistic"]


def test_scenario_forecast_agrees_with_history_at_last_point(toy_series):
    frame = prepare_trend_frame(toy_series, base_year=2013)
    model = fit_trend_regression(frame, predictor="log_years")
    last_x = frame["log_years"].iloc[-1]
    scenarios = scenario_forecast(frame, model, np.array([last_x]), predictor="log_years")
    last_y = frame["value_numeric"].iloc[-1]
    # All three scenarios are anchored to the last observed value
    for col in scenarios.columns:
        assert scenarios[col].iloc[0] == pytest.approx(last_y, abs=1e-6)


def test_scenario_forecast_diverges_going_forward(toy_series):
    frame = prepare_trend_frame(toy_series, base_year=2013)
    model = fit_trend_regression(frame, predictor="log_years")
    future_x = np.log(np.array([15.0]))  # well past the last observation
    scenarios = scenario_forecast(frame, model, future_x, predictor="log_years")
    assert scenarios["Pessimistic"].iloc[0] <= scenarios["Base case"].iloc[0] <= scenarios["Optimistic"].iloc[0]


def test_event_augmented_forecast_matches_impact_model(toy_series):
    impact_full = pd.DataFrame({
        "event_date": [pd.Timestamp("2021-05-01")],
        "lag_months": [3],
        "duration_months": [12],
        "impact_direction": ["increase"],
        "impact_estimate": [5.0],
        "related_indicator": ["ACC_MM_ACCOUNT"],
    })
    out = event_augmented_forecast(
        "ACC_MM_ACCOUNT", [pd.Timestamp("2024-12-31")], pd.Timestamp("2021-01-01"),
        baseline_value=4.7, impact_full=impact_full, discount=1.0,
    )
    assert len(out) == 1
    assert out["value"].iloc[0] > 4.7  # some positive event effect should have accrued by 2024
    assert out["n_events_applied"].iloc[0] == 1


def test_summarize_forecast_table_shape():
    base = pd.DataFrame({"mean": [50.0, 52.0], "ci_lower": [45.0, 46.0], "ci_upper": [55.0, 58.0]})
    table = summarize_forecast_table(
        "ACC_OWNERSHIP", "Account Ownership", [2025, 2026], base,
        optimistic=np.array([53.0, 56.0]), pessimistic=np.array([48.0, 49.0]),
    )
    assert list(table["year"]) == [2025, 2026]
    assert "scenario_optimistic" in table.columns
    assert "event_augmented" not in table.columns
