"""
Unit tests for src/impact_model.py.

Run with: pytest tests/ -v
"""

import sys
import os
import pytest
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.impact_model import (
    logistic_ramp, months_between, event_effect_at, combined_effect_at,
    simulate_indicator, build_association_matrix, fit_activation_discount
)


def test_logistic_ramp_zero_before_start():
    assert logistic_ramp(0) == 0.0
    assert logistic_ramp(-5) == 0.0


def test_logistic_ramp_approaches_one_over_time():
    early = logistic_ramp(1, ramp_period=12)
    late = logistic_ramp(24, ramp_period=12)
    assert 0 < early < late < 1.001
    assert late > 0.9


def test_logistic_ramp_zero_duration_is_instant():
    assert logistic_ramp(1, ramp_period=0) == 1.0


def test_months_between():
    d1 = pd.Timestamp("2021-05-01")
    d2 = pd.Timestamp("2022-05-01")
    assert months_between(d2, d1) == 12
    assert months_between(d1, d2) == -12


def test_event_effect_at_zero_before_lag_ends():
    event_date = pd.Timestamp("2021-05-17")
    target = event_date + pd.DateOffset(months=1)
    effect = event_effect_at(target, event_date, lag_months=12, full_magnitude=15, duration_months=12)
    assert effect == 0.0


def test_event_effect_at_approaches_full_magnitude():
    event_date = pd.Timestamp("2021-05-17")
    target = event_date + pd.DateOffset(months=48)
    effect = event_effect_at(target, event_date, lag_months=12, full_magnitude=15, duration_months=12)
    assert effect > 14.0  # should be close to full magnitude by 4 years out


def test_event_effect_at_rejects_negative_lag():
    with pytest.raises(ValueError, match="lag_months must be >= 0"):
        event_effect_at(pd.Timestamp("2022-01-01"), pd.Timestamp("2021-01-01"), -5, 10)


def test_event_effect_at_rejects_negative_duration():
    with pytest.raises(ValueError, match="duration_months must be >= 0"):
        event_effect_at(pd.Timestamp("2022-01-01"), pd.Timestamp("2021-01-01"), 5, 10, duration_months=-3)


def test_combined_effect_at_sums_multiple_events():
    rows = pd.DataFrame({
        "event_date": [pd.Timestamp("2020-01-01"), pd.Timestamp("2020-01-01")],
        "lag_months": [0, 0],
        "duration_months": [0, 0],
        "impact_direction": ["increase", "increase"],
        "impact_estimate": [10.0, 5.0],
    })
    target = pd.Timestamp("2021-01-01")
    total = combined_effect_at(target, rows)
    assert total == pytest.approx(15.0)


def test_combined_effect_at_handles_decrease_direction():
    rows = pd.DataFrame({
        "event_date": [pd.Timestamp("2020-01-01")],
        "lag_months": [0],
        "duration_months": [0],
        "impact_direction": ["decrease"],
        "impact_estimate": [10.0],
    })
    target = pd.Timestamp("2021-01-01")
    total = combined_effect_at(target, rows)
    assert total == pytest.approx(-10.0)


def test_combined_effect_at_skips_missing_estimates():
    rows = pd.DataFrame({
        "event_date": [pd.Timestamp("2020-01-01"), pd.Timestamp("2020-01-01")],
        "lag_months": [0, 0],
        "duration_months": [0, 0],
        "impact_direction": ["increase", "increase"],
        "impact_estimate": [10.0, np.nan],
    })
    target = pd.Timestamp("2021-01-01")
    total = combined_effect_at(target, rows)
    assert total == pytest.approx(10.0)


def test_combined_effect_at_rejects_missing_columns():
    rows = pd.DataFrame({"event_date": [pd.Timestamp("2020-01-01")]})
    with pytest.raises(ValueError, match="missing required columns"):
        combined_effect_at(pd.Timestamp("2021-01-01"), rows)


def test_simulate_indicator_raises_on_unknown_code():
    impact_full = pd.DataFrame({
        "related_indicator": ["ACC_OWNERSHIP"],
        "event_date": [pd.Timestamp("2020-01-01")],
        "lag_months": [0], "duration_months": [0],
        "impact_direction": ["increase"], "impact_estimate": [10.0],
    })
    with pytest.raises(ValueError, match="No impact_links found"):
        simulate_indicator("NOT_A_CODE", pd.Timestamp("2021-01-01"), 50, impact_full)


def test_simulate_indicator_applies_discount():
    impact_full = pd.DataFrame({
        "related_indicator": ["ACC_OWNERSHIP"],
        "event_date": [pd.Timestamp("2020-01-01")],
        "lag_months": [0], "duration_months": [0],
        "impact_direction": ["increase"], "impact_estimate": [10.0],
    })
    target = pd.Timestamp("2021-01-01")
    full, _ = simulate_indicator("ACC_OWNERSHIP", target, 50, impact_full, discount=1.0)
    halved, _ = simulate_indicator("ACC_OWNERSHIP", target, 50, impact_full, discount=0.5)
    assert full > halved > 50


def test_build_association_matrix_shape():
    impact_full = pd.DataFrame({
        "event_name": ["Event A", "Event A", "Event B"],
        "related_indicator": ["ACC_OWNERSHIP", "USG_P2P_COUNT", "ACC_OWNERSHIP"],
        "impact_estimate": [10.0, 20.0, 5.0],
    })
    matrix = build_association_matrix(impact_full)
    assert matrix.shape == (2, 2)  # 2 events x 2 indicators, NOT 3 rows (one per link)
    assert matrix.loc["Event A", "ACC_OWNERSHIP"] == 10.0


def test_build_association_matrix_rejects_empty_input():
    with pytest.raises(ValueError, match="empty"):
        build_association_matrix(pd.DataFrame())


def test_fit_activation_discount_basic():
    # actual grew from 40 to 45 (+5), raw model predicted 40 to 60 (+20) -> discount should be 0.25
    discount = fit_activation_discount(actual_final=45, actual_baseline=40,
                                        predicted_final_raw=60, baseline_value=40)
    assert discount == pytest.approx(0.25)


def test_fit_activation_discount_rejects_zero_raw_effect():
    with pytest.raises(ValueError, match="cannot fit a discount factor"):
        fit_activation_discount(actual_final=45, actual_baseline=40,
                                 predicted_final_raw=40, baseline_value=40)