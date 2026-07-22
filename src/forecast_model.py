"""
Forecasting utilities for Task 4 (Access and Usage, 2025-2027).

Implements the three approaches recommended for short, sparse time series
(see the "Forecasting Approaches for Limited Data" reference deck):
  1. Trend regression (linear or log-linear in "years since base"), with
     statsmodels prediction intervals for statistical uncertainty.
  2. Scenario-based forecasting (optimistic / base / pessimistic), built by
     adjusting the fitted trend's slope rather than picking arbitrary numbers.
  3. Event-augmented forecasting, which reuses Task 3's `impact_model.py` to
     add the combined, discounted effect of cataloged events on top of the
     trend baseline.

Kept separate from notebook cells so the same functions are testable and
reusable from the Streamlit dashboard (Task 5).
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm


def prepare_trend_frame(series: pd.DataFrame, base_year: int,
                         date_col: str = "observation_date",
                         value_col: str = "value_numeric") -> pd.DataFrame:
    """
    Add `years_since_base` and `log_years` columns to a date-sorted indicator series.

    Raises
    ------
    ValueError if any observation predates `base_year` (log undefined for <= 0).
    """
    out = series.copy().sort_values(date_col).reset_index(drop=True)
    out["years_since_base"] = out[date_col].dt.year - base_year + \
        (out[date_col].dt.dayofyear / 365.25)
    if (out["years_since_base"] <= 0).any():
        raise ValueError(
            f"base_year={base_year} is not strictly before all observations; "
            f"choose an earlier base_year."
        )
    out["log_years"] = np.log(out["years_since_base"])
    return out


def fit_trend_regression(trend_frame: pd.DataFrame, value_col: str = "value_numeric",
                          predictor: str = "log_years"):
    """
    Fit an OLS trend model (statsmodels), returning the fitted results object.

    Parameters
    ----------
    predictor : "log_years" (recommended for rates that decelerate near a ceiling,
        e.g. Access) or "years_since_base" (plain linear, e.g. when a series is
        still accelerating and a ceiling isn't yet visible in the data).

    Raises
    ------
    ValueError if trend_frame has fewer than 2 rows (can't fit a line) or the
    predictor column is missing.
    """
    if len(trend_frame) < 2:
        raise ValueError(f"Need at least 2 observations to fit a trend, got {len(trend_frame)}.")
    if predictor not in trend_frame.columns:
        raise ValueError(f"predictor '{predictor}' not found; call prepare_trend_frame first.")

    X = sm.add_constant(trend_frame[predictor])
    y = trend_frame[value_col]
    return sm.OLS(y, X).fit()


def predict_with_interval(model, x_values: np.ndarray, predictor: str,
                           alpha: float = 0.05, clip_0_100: bool = True) -> pd.DataFrame:
    """
    Predict mean + confidence interval for arbitrary x values from a fitted OLS model.

    Parameters
    ----------
    clip_0_100 : if True, clip mean/lower/upper to [0, 100] -- appropriate for
        percentage-point indicators, since an unclipped linear-in-log trend can
        still (rarely) drift outside a valid rate's bounds far from the data.
    """
    X_new = sm.add_constant(pd.DataFrame({predictor: x_values}), has_constant="add")
    pred = model.get_prediction(X_new)
    summary = pred.summary_frame(alpha=alpha)
    out = pd.DataFrame({
        "mean": summary["mean"].values,
        "ci_lower": summary["mean_ci_lower"].values,
        "ci_upper": summary["mean_ci_upper"].values,
    })
    if clip_0_100:
        out = out.clip(lower=0, upper=100)
    return out


def scenario_slopes(base_slope: float, optimistic_mult: float = 1.25,
                     pessimistic_mult: float = 0.70) -> dict:
    """Return {'Optimistic', 'Base case', 'Pessimistic'} slope multipliers applied to base_slope."""
    return {
        "Optimistic": base_slope * optimistic_mult,
        "Base case": base_slope,
        "Pessimistic": base_slope * pessimistic_mult,
    }


def scenario_forecast(trend_frame: pd.DataFrame, model, x_values: np.ndarray,
                       predictor: str = "log_years", value_col: str = "value_numeric",
                       optimistic_mult: float = 1.25, pessimistic_mult: float = 0.70,
                       clip_0_100: bool = True) -> pd.DataFrame:
    """
    Build optimistic/base/pessimistic scenario lines by adjusting the fitted
    trend's slope, each anchored to pass through the last observed value
    (so all three scenarios agree with history and diverge only going forward).

    Returns a DataFrame indexed like x_values with one column per scenario.
    """
    base_slope = model.params[predictor]
    slopes = scenario_slopes(base_slope, optimistic_mult, pessimistic_mult)

    last_row = trend_frame.iloc[-1]
    last_x = last_row[predictor]
    last_y = last_row[value_col]

    out = {}
    for name, slope in slopes.items():
        intercept = last_y - slope * last_x
        values = intercept + slope * np.asarray(x_values)
        if clip_0_100:
            values = np.clip(values, 0, 100)
        out[name] = values
    return pd.DataFrame(out, index=x_values)


def event_augmented_forecast(indicator_code: str, target_dates: list, baseline_date: pd.Timestamp,
                              baseline_value: float, impact_full: pd.DataFrame,
                              discount: float = 1.0, clip_0_100: bool = True) -> pd.DataFrame:
    """
    Forecast an indicator at each target_date as baseline_value plus the combined,
    discounted effect of every cataloged event linked to it (reuses Task 3's
    `impact_model.simulate_indicator`, imported by the caller to avoid a circular
    import here).

    This is a thin batch wrapper -- see `src/impact_model.py` for the underlying
    per-date logic and its documented limitations (additive combination, etc).
    """
    try:
        from src.impact_model import simulate_indicator
    except ImportError:
        from impact_model import simulate_indicator  # when src/ itself is on sys.path

    rows = []
    for target_date in target_dates:
        value, relevant = simulate_indicator(
            indicator_code, target_date, baseline_value, impact_full, discount=discount
        )
        if clip_0_100:
            value = float(np.clip(value, 0, 100))
        rows.append({"date": target_date, "value": value, "n_events_applied": len(relevant)})
    return pd.DataFrame(rows)


def summarize_forecast_table(indicator_code: str, indicator_label: str,
                              years: list, base: pd.DataFrame, optimistic: np.ndarray,
                              pessimistic: np.ndarray, event_augmented: np.ndarray = None) -> pd.DataFrame:
    """
    Assemble a single tidy forecast table (one row per year) combining the trend
    baseline + CI, scenario range, and (optionally) the event-augmented estimate.
    Intended as the canonical output written to data/processed/forecasts.csv and
    read by the Task 5 dashboard.
    """
    table = pd.DataFrame({
        "indicator_code": indicator_code,
        "indicator_label": indicator_label,
        "year": years,
        "trend_base": base["mean"].values,
        "trend_ci_lower": base["ci_lower"].values,
        "trend_ci_upper": base["ci_upper"].values,
        "scenario_optimistic": optimistic,
        "scenario_pessimistic": pessimistic,
    })
    if event_augmented is not None:
        table["event_augmented"] = event_augmented
    return table
