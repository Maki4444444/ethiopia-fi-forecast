"""
Event impact modeling utilities for Task 3.

Translates categorical impact_link records (direction, magnitude, lag, duration) into a
time-varying numeric effect, and combines effects from multiple events on the same indicator.
Kept separate from notebook cells so the same functions are testable and reusable in Task 4's
forecasting notebook.
"""

import numpy as np
import pandas as pd


def logistic_ramp(months_since_start: float, ramp_period: float = 12, steepness: float = 0.5) -> float:
    """
    Fraction (0 to 1) of an event's full effect that has materialized `months_since_start`
    months after its lag period ended. Reaches ~95% of full effect by `ramp_period` months.

    Returns 0.0 for any non-positive `months_since_start` (effect hasn't started yet).
    """
    if months_since_start <= 0:
        return 0.0
    if ramp_period <= 0:
        # a zero-duration link (e.g. a definitional/structural event) has its full effect
        # instantly once the lag has passed, rather than raising an error
        return 1.0
    midpoint = ramp_period / 2
    return 1 / (1 + np.exp(-steepness * (months_since_start - midpoint)))


def months_between(target_date: pd.Timestamp, start_date: pd.Timestamp) -> int:
    """Whole months elapsed from start_date to target_date (can be negative)."""
    return (target_date.year - start_date.year) * 12 + (target_date.month - start_date.month)


def event_effect_at(target_date: pd.Timestamp, event_date: pd.Timestamp, lag_months: float,
                     full_magnitude: float, duration_months: float = 12) -> float:
    """
    Effect of a single event on an indicator at target_date, in the indicator's native units.

    Raises
    ------
    ValueError if lag_months or duration_months is negative, since a negative delay or
    ramp period is not a meaningful input and likely indicates a data error upstream.
    """
    if lag_months < 0:
        raise ValueError(f"lag_months must be >= 0, got {lag_months}")
    if duration_months < 0:
        raise ValueError(f"duration_months must be >= 0, got {duration_months}")

    months_elapsed = months_between(target_date, event_date)
    months_since_lag_ended = months_elapsed - lag_months
    ramp_fraction = logistic_ramp(months_since_lag_ended, duration_months)
    return full_magnitude * ramp_fraction


def combined_effect_at(target_date: pd.Timestamp, event_rows: pd.DataFrame) -> float:
    """
    Sum of all individual event effects (from event_rows -- a slice of impact_full with
    columns event_date, lag_months, duration_months, impact_direction, impact_estimate) on a
    single indicator at target_date. Additive combination across events; see the impact
    modeling notebook / methodology doc for the documented limitation of this assumption.

    Rows with a missing impact_estimate are skipped (not treated as zero), since a missing
    estimate means "no numeric claim available", not "no effect".
    """
    required_cols = {'event_date', 'lag_months', 'duration_months', 'impact_direction', 'impact_estimate'}
    missing = required_cols - set(event_rows.columns)
    if missing:
        raise ValueError(f"event_rows is missing required columns: {missing}")

    total = 0.0
    for _, row in event_rows.iterrows():
        if pd.isna(row['impact_estimate']):
            continue
        sign = -1 if row['impact_direction'] == 'decrease' else 1
        total += event_effect_at(
            target_date, row['event_date'], row['lag_months'],
            sign * abs(row['impact_estimate']), duration_months=row['duration_months']
        )
    return total


def simulate_indicator(indicator_code: str, target_date: pd.Timestamp, baseline_value: float,
                        impact_full: pd.DataFrame, discount: float = 1.0) -> tuple[float, pd.DataFrame]:
    """
    Predict an indicator's value at target_date as baseline_value plus the combined,
    discounted effect of every event linked to it.

    Parameters
    ----------
    discount : float
        Multiplier applied to the combined raw effect before adding to baseline. Use 1.0 for
        the raw (unrefined) model, or an empirically-derived activation discount (see Section 6
        of the impact modeling notebook) for the refined model.

    Raises
    ------
    ValueError if indicator_code has no impact_links at all, since predicting from zero
    events is likely a typo'd code rather than a genuine "no events affect this" case.
    """
    relevant = impact_full[impact_full['related_indicator'] == indicator_code]
    if relevant.empty:
        raise ValueError(f"No impact_links found for indicator_code '{indicator_code}'")
    raw_effect = combined_effect_at(target_date, relevant)
    return baseline_value + (raw_effect * discount), relevant


def build_association_matrix(impact_full: pd.DataFrame, key_indicators: list[str] = None) -> pd.DataFrame:
    """
    Pivot impact_full into an event x indicator matrix of impact_estimate values.
    Rows = event names, columns = related_indicator codes.
    """
    if impact_full.empty:
        raise ValueError("impact_full is empty -- cannot build an association matrix")

    matrix = impact_full.pivot_table(
        index='event_name', columns='related_indicator', values='impact_estimate', aggfunc='sum'
    )
    if key_indicators:
        cols = [c for c in key_indicators if c in matrix.columns]
        matrix = matrix.reindex(columns=cols)
    return matrix


def fit_activation_discount(actual_final: float, actual_baseline: float,
                             predicted_final_raw: float, baseline_value: float) -> float:
    """
    Solve for the discount factor that makes the raw model's prediction match observed data,
    rather than picking a round number. Returns the implied discount (typically 0 < d <= 1,
    but not clipped, so an out-of-range result is visible rather than silently masked).

    Raises
    ------
    ValueError if predicted_final_raw == baseline_value (zero raw effect), since the discount
    is undefined (division by zero) in that case.
    """
    required_total_effect = actual_final - actual_baseline
    raw_predicted_effect = predicted_final_raw - baseline_value
    if raw_predicted_effect == 0:
        raise ValueError("Raw predicted effect is zero -- cannot fit a discount factor (division by zero).")
    return required_total_effect / raw_predicted_effect