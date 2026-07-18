"""
Reusable analysis helpers for the Task 2 EDA notebook.

Keeps repeated aggregation/plotting logic out of notebook cells so the
notebook stays readable and the logic is testable/reusable independently.
"""

import pandas as pd


def get_indicator_series(obs: pd.DataFrame, indicator_code: str, gender: str = "all") -> pd.DataFrame:
    """
    Return a clean, date-sorted time series for a single indicator_code.

    Raises
    ------
    ValueError if the indicator_code doesn't exist in the data at all, so
    a typo'd code fails loudly instead of silently returning an empty frame.
    """
    if indicator_code not in obs["indicator_code"].unique():
        raise ValueError(
            f"indicator_code '{indicator_code}' not found in observations. "
            f"Available codes: {sorted(obs['indicator_code'].dropna().unique())}"
        )
    sub = obs[(obs["indicator_code"] == indicator_code) & (obs["gender"] == gender)]
    return sub.sort_values("observation_date").reset_index(drop=True)


def growth_between_points(series: pd.DataFrame, value_col: str = "value_numeric",
                           date_col: str = "observation_date") -> pd.DataFrame:
    """
    Compute period-over-period change and annualized rate for a time series.
    Expects a DataFrame already sorted by date (see get_indicator_series).
    """
    if len(series) < 2:
        raise ValueError("Need at least 2 data points to compute growth between them.")
    out = series.copy()
    out["years_elapsed"] = out[date_col].dt.year.diff()
    out["pp_change"] = out[value_col].diff()
    out["pp_per_year"] = out["pp_change"] / out["years_elapsed"]
    return out


def indicator_coverage_table(obs: pd.DataFrame, min_points: int = 1) -> pd.Series:
    """Count observations per indicator_code, optionally filtered to a minimum count."""
    counts = obs["indicator_code"].value_counts()
    return counts[counts >= min_points]


def pillar_summary(obs: pd.DataFrame) -> pd.DataFrame:
    """Summarize observation count, date range, and confidence mix per pillar."""
    if obs.empty:
        raise ValueError("Observations DataFrame is empty — nothing to summarize.")

    def _summarize(g):
        return pd.Series({
            "n_observations": len(g),
            "n_indicators": g["indicator_code"].nunique(),
            "earliest": g["observation_date"].min(),
            "latest": g["observation_date"].max(),
            "pct_high_confidence": (g["confidence"] == "high").mean(),
        })

    return obs.groupby("pillar").apply(_summarize, include_groups=False)