"""
Data loading and validation utilities for the Ethiopia Financial Inclusion dataset.

Centralizes the load/validate logic used across notebooks so it isn't duplicated
in every notebook cell, and adds basic error handling around file I/O.
"""

import os
import pandas as pd


DATE_COLUMNS = ["observation_date", "period_start", "period_end", "collection_date"]


def load_dataset(data_dir: str, use_enriched: bool = True) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load the main dataset, impact_links, and reference_codes.

    Parameters
    ----------
    data_dir : str
        Path to the project's `data` directory (containing `raw/` and `processed/`).
    use_enriched : bool
        If True, load the enriched files from data/processed/. If False (or if the
        enriched files don't exist yet), fall back to the raw files.

    Returns
    -------
    (df_main, df_impact, df_ref) : tuple of DataFrames

    Raises
    ------
    FileNotFoundError
        If neither the enriched nor raw files can be found, with a clear message
        about which path was checked.
    """
    raw_dir = os.path.join(data_dir, "raw")
    processed_dir = os.path.join(data_dir, "processed")

    main_path = os.path.join(processed_dir, "ethiopia_fi_unified_data_enriched.csv")
    impact_path = os.path.join(processed_dir, "impact_links_enriched.csv")

    if not use_enriched or not os.path.exists(main_path):
        main_path = os.path.join(raw_dir, "ethiopia_fi_unified_data.csv")
        impact_path = os.path.join(raw_dir, "impact_links.csv")

    ref_path = os.path.join(raw_dir, "reference_codes.csv")

    try:
        df_main = pd.read_csv(main_path, parse_dates=DATE_COLUMNS, date_format="mixed")
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Could not find main dataset at '{main_path}'. "
            f"Check that data/raw/ (and data/processed/ if use_enriched=True) exist "
            f"and contain the expected CSV files."
        ) from e
    except pd.errors.EmptyDataError as e:
        raise ValueError(f"Main dataset at '{main_path}' is empty or unreadable.") from e

    try:
        df_impact = pd.read_csv(impact_path, parse_dates=DATE_COLUMNS, date_format="mixed")
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Could not find impact links file at '{impact_path}'.") from e

    try:
        df_ref = pd.read_csv(ref_path)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Could not find reference codes file at '{ref_path}'.") from e

    return df_main, df_impact, df_ref


def validate_schema(df_main: pd.DataFrame, df_ref: pd.DataFrame) -> dict:
    """
    Run schema integrity checks against the loaded dataset.

    Checks:
      - no duplicate record_id values
      - events never have a pillar set (schema design rule)
      - observations/targets never have a category set
      - all categorical values appear in reference_codes

    Returns
    -------
    dict with keys: 'passed' (bool), 'issues' (list of str)
    """
    issues = []

    dupes = df_main["record_id"].duplicated().sum()
    if dupes > 0:
        dup_ids = df_main.loc[df_main["record_id"].duplicated(keep=False), "record_id"].unique().tolist()
        issues.append(f"{dupes} duplicate record_id(s) found: {dup_ids}")

    events = df_main[df_main["record_type"] == "event"]
    if events["pillar"].notna().any():
        bad = events.loc[events["pillar"].notna(), "record_id"].tolist()
        issues.append(f"Event(s) with a pillar set (should be empty per schema): {bad}")

    non_events = df_main[df_main["record_type"].isin(["observation", "target"])]
    if non_events["category"].notna().any():
        bad = non_events.loc[non_events["category"].notna(), "record_id"].tolist()
        issues.append(f"Observation/target(s) with a category set (should be empty per schema): {bad}")

    for field, column in [("record_type", "record_type"), ("pillar", "pillar"), ("confidence", "confidence")]:
        if field not in df_ref["field"].values:
            continue
        valid = set(df_ref.loc[df_ref["field"] == field, "code"])
        seen = set(df_main[column].dropna().unique())
        invalid = seen - valid
        if invalid:
            issues.append(f"Invalid '{column}' values not in reference_codes: {invalid}")

    return {"passed": len(issues) == 0, "issues": issues}


def event_impact_coverage(df_main: pd.DataFrame, df_impact: pd.DataFrame) -> pd.DataFrame:
    """
    Return a table of every event with its impact_link count, so gaps
    (events with zero links) are easy to spot.
    """
    events = df_main[df_main["record_type"] == "event"][["record_id", "indicator"]]
    link_counts = df_impact.groupby("parent_id").size().rename("n_impact_links")
    coverage = events.merge(link_counts, left_on="record_id", right_index=True, how="left")
    coverage["n_impact_links"] = coverage["n_impact_links"].fillna(0).astype(int)
    return coverage.sort_values("n_impact_links")