"""
Task 5: Interactive dashboard for Ethiopia's financial inclusion data, event
catalog, and Access/Usage forecasts.

Run locally with:
    streamlit run dashboard/app.py

Reads data/processed/ethiopia_fi_unified_data_enriched.csv,
data/processed/impact_links_enriched.csv, and data/processed/forecasts.csv
(the last one produced by notebooks/04_forecasting.ipynb -- run that notebook
first if forecasts.csv is missing).
"""

import os
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

st.set_page_config(page_title="Ethiopia Financial Inclusion", layout="wide", page_icon="\U0001F4CA")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


# ----------------------------------------------------------------------------
# Data loading (cached so page navigation doesn't re-read CSVs every rerun)
# ----------------------------------------------------------------------------

@st.cache_data
def load_data():
    main_path = os.path.join(DATA_DIR, "processed", "ethiopia_fi_unified_data_enriched.csv")
    impact_path = os.path.join(DATA_DIR, "processed", "impact_links_enriched.csv")
    df = pd.read_csv(main_path, parse_dates=["observation_date"])
    impact = pd.read_csv(impact_path, parse_dates=["observation_date"])
    return df, impact


@st.cache_data
def load_forecasts():
    forecast_path = os.path.join(DATA_DIR, "processed", "forecasts.csv")
    if not os.path.exists(forecast_path):
        return None
    return pd.read_csv(forecast_path)


try:
    df, impact = load_data()
except FileNotFoundError as e:
    st.error(
        "Could not find the enriched dataset. Make sure you're running this from the "
        "repo root (`streamlit run dashboard/app.py`) and that "
        "`data/processed/ethiopia_fi_unified_data_enriched.csv` exists.\n\n"
        f"Details: {e}"
    )
    st.stop()

forecasts = load_forecasts()

obs = df[df["record_type"] == "observation"].copy()
events = df[df["record_type"] == "event"].copy()
targets = df[df["record_type"] == "target"].copy()

INDICATOR_LABELS = (
    obs[["indicator_code", "indicator"]].drop_duplicates().set_index("indicator_code")["indicator"].to_dict()
)


def indicator_series(code, gender="all"):
    sub = obs[(obs["indicator_code"] == code)]
    if "gender" in sub.columns and gender != "all_genders":
        sub = sub[(sub["gender"] == gender) | (sub["gender"].isna())]
    return sub.sort_values("observation_date")


# ----------------------------------------------------------------------------
# Sidebar navigation
# ----------------------------------------------------------------------------

st.sidebar.title("\U0001F4CA Ethiopia Financial Inclusion")
page = st.sidebar.radio(
    "Section",
    ["Overview", "Trends", "Forecasts", "Inclusion Projections"],
)
st.sidebar.markdown("---")
st.sidebar.caption(
    "Data: World Bank Global Findex, National Bank of Ethiopia, EthSwitch, "
    "Safaricom/Ethio Telecom results, GSMA. See `data_enrichment_log.md` for full sourcing."
)


# ----------------------------------------------------------------------------
# Overview page
# ----------------------------------------------------------------------------

def render_overview():
    st.title("Overview")
    st.caption("Snapshot of Ethiopia's financial inclusion progress, latest values and trend direction.")

    acc = indicator_series("ACC_OWNERSHIP")
    mm = indicator_series("ACC_MM_ACCOUNT")
    usg = indicator_series("USG_DIGITAL_PAYMENT")
    crossover = indicator_series("USG_CROSSOVER")

    col1, col2, col3, col4 = st.columns(4)

    def metric_card(col, label, series, suffix="%"):
        if series.empty:
            col.metric(label, "n/a")
            return
        latest = series.iloc[-1]
        delta = None
        if len(series) > 1:
            prev = series.iloc[-2]
            delta = f"{latest['value_numeric'] - prev['value_numeric']:+.1f}{suffix} vs {prev['observation_date'].year}"
        col.metric(
            f"{label} ({latest['observation_date'].year})",
            f"{latest['value_numeric']:.1f}{suffix}",
            delta,
        )

    metric_card(col1, "Account Ownership (Access)", acc)
    metric_card(col2, "Mobile Money Accounts", mm)
    metric_card(col3, "Digital Payment Usage", usg)
    metric_card(col4, "P2P / ATM Crossover Ratio", crossover, suffix="x")

    st.markdown("---")
    left, right = st.columns([2, 1])

    with left:
        st.subheader("Growth rate highlights")
        rate_rows = []
        for code, label in [("ACC_OWNERSHIP", "Account Ownership"), ("USG_DIGITAL_PAYMENT", "Digital Payment Usage")]:
            s = indicator_series(code)
            if len(s) >= 2:
                first, last = s.iloc[0], s.iloc[-1]
                years = (last["observation_date"] - first["observation_date"]).days / 365.25
                pp_per_year = (last["value_numeric"] - first["value_numeric"]) / years if years > 0 else float("nan")
                rate_rows.append({
                    "Indicator": label,
                    f"{first['observation_date'].year}": f"{first['value_numeric']:.1f}%",
                    f"{last['observation_date'].year}": f"{last['value_numeric']:.1f}%",
                    "pp / year": f"{pp_per_year:+.2f}",
                })
        st.dataframe(pd.DataFrame(rate_rows), use_container_width=True, hide_index=True)

    with right:
        st.subheader("P2P / ATM crossover")
        if not crossover.empty:
            val = crossover.iloc[-1]["value_numeric"]
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=val,
                title={"text": "P2P transactions per ATM withdrawal"},
                gauge={"axis": {"range": [0, max(2, val * 1.3)]},
                       "threshold": {"line": {"color": "red", "width": 3}, "value": 1.0}},
            ))
            fig.update_layout(height=250, margin=dict(t=40, b=10, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Ratio > 1 means P2P digital transfers have overtaken ATM cash withdrawals.")


# ----------------------------------------------------------------------------
# Trends page
# ----------------------------------------------------------------------------

def render_trends():
    st.title("Trends")
    st.caption("Interactive time series across indicators, with events overlaid.")

    indicator_options = sorted(obs["indicator_code"].dropna().unique())
    default = [c for c in ["ACC_OWNERSHIP", "USG_DIGITAL_PAYMENT", "ACC_MM_ACCOUNT"] if c in indicator_options]

    selected = st.multiselect(
        "Channels / indicators to compare",
        indicator_options,
        default=default or indicator_options[:2],
        format_func=lambda c: f"{c} \u2014 {INDICATOR_LABELS.get(c, '')}",
    )

    min_date, max_date = obs["observation_date"].min(), obs["observation_date"].max()
    date_range = st.slider(
        "Date range",
        min_value=min_date.to_pydatetime(),
        max_value=max_date.to_pydatetime(),
        value=(min_date.to_pydatetime(), max_date.to_pydatetime()),
    )
    show_events = st.checkbox("Overlay cataloged events", value=True)

    if not selected:
        st.info("Select at least one indicator above.")
        return

    fig = go.Figure()
    for code in selected:
        s = indicator_series(code)
        s = s[(s["observation_date"] >= date_range[0]) & (s["observation_date"] <= date_range[1])]
        if s.empty:
            continue
        fig.add_trace(go.Scatter(
            x=s["observation_date"], y=s["value_numeric"], mode="lines+markers",
            name=f"{code}", hovertemplate="%{x|%Y-%m-%d}: %{y:.1f}<extra>" + code + "</extra>",
        ))

    if show_events:
        ev = events[(events["observation_date"] >= date_range[0]) & (events["observation_date"] <= date_range[1])]
        for _, row in ev.iterrows():
            fig.add_vline(x=row["observation_date"], line_dash="dot", line_color="gray", opacity=0.6)
        if not ev.empty:
            fig.add_trace(go.Scatter(
                x=ev["observation_date"], y=[None] * len(ev), mode="markers",
                marker=dict(symbol="line-ns", color="gray"), name="Event", showlegend=True,
            ))

    fig.update_layout(
        xaxis_title="Date", yaxis_title="Value (native unit \u2014 see indicator definitions)",
        height=500, hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    if show_events:
        with st.expander("Cataloged events in this range"):
            ev = events[(events["observation_date"] >= date_range[0]) & (events["observation_date"] <= date_range[1])]
            st.dataframe(
                ev[["observation_date", "indicator", "category"]].rename(
                    columns={"indicator": "event", "observation_date": "date"}
                ).sort_values("date"),
                use_container_width=True, hide_index=True,
            )

    st.markdown("---")
    st.subheader("Underlying data")
    display_cols = ["indicator_code", "observation_date", "value_numeric", "gender", "location", "source_name", "confidence"]
    table = obs[obs["indicator_code"].isin(selected)][display_cols].sort_values(["indicator_code", "observation_date"])
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.download_button(
        "Download this data as CSV", table.to_csv(index=False).encode(),
        file_name="ethiopia_fi_trends_export.csv", mime="text/csv",
    )


# ----------------------------------------------------------------------------
# Forecasts page
# ----------------------------------------------------------------------------

def render_forecasts():
    st.title("Forecasts")
    st.caption("Access and Usage forecasts for 2025-2027 (from notebooks/04_forecasting.ipynb).")

    if forecasts is None:
        st.warning(
            "`data/processed/forecasts.csv` not found. Run "
            "`jupyter nbconvert --to notebook --execute --inplace notebooks/04_forecasting.ipynb` "
            "first, then reload this page."
        )
        return

    indicator = st.selectbox(
        "Indicator",
        forecasts["indicator_code"].unique(),
        format_func=lambda c: forecasts.loc[forecasts.indicator_code == c, "indicator_label"].iloc[0],
    )
    model_view = st.radio(
        "Uncertainty view", ["Trend + confidence interval", "Scenario range (optimistic/base/pessimistic)"],
        horizontal=True,
    )

    sub = forecasts[forecasts["indicator_code"] == indicator].sort_values("year")
    hist = indicator_series(indicator)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist["observation_date"].dt.year, y=hist["value_numeric"],
                              mode="markers", marker=dict(size=10, color="black"), name="Observed"))
    fig.add_trace(go.Scatter(x=sub["year"], y=sub["trend_base"], mode="lines+markers",
                              line=dict(color="royalblue"), name="Trend forecast (base)"))

    if model_view.startswith("Trend") and sub["trend_ci_lower"].notna().any():
        fig.add_trace(go.Scatter(
            x=list(sub["year"]) + list(sub["year"][::-1]),
            y=list(sub["trend_ci_upper"]) + list(sub["trend_ci_lower"][::-1]),
            fill="toself", fillcolor="rgba(65,105,225,0.2)", line=dict(color="rgba(255,255,255,0)"),
            name="95% CI", hoverinfo="skip",
        ))
    elif model_view.startswith("Trend"):
        st.info(
            "No confidence interval available for this indicator (fit to only 2 historical "
            "points -> 0 residual degrees of freedom). Showing scenario range instead."
        )
        model_view = "Scenario range (optimistic/base/pessimistic)"

    if model_view.startswith("Scenario"):
        fig.add_trace(go.Scatter(
            x=list(sub["year"]) + list(sub["year"][::-1]),
            y=list(sub["scenario_optimistic"]) + list(sub["scenario_pessimistic"][::-1]),
            fill="toself", fillcolor="rgba(128,128,128,0.15)", line=dict(color="rgba(255,255,255,0)"),
            name="Scenario range", hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(x=sub["year"], y=sub["scenario_optimistic"], mode="lines",
                                  line=dict(color="green", dash="dash"), name="Optimistic"))
        fig.add_trace(go.Scatter(x=sub["year"], y=sub["scenario_pessimistic"], mode="lines",
                                  line=dict(color="firebrick", dash="dash"), name="Pessimistic"))

    if "event_augmented" in sub.columns and sub["event_augmented"].notna().any():
        fig.add_trace(go.Scatter(x=sub["year"], y=sub["event_augmented"], mode="lines+markers",
                                  line=dict(color="purple"), marker=dict(symbol="diamond"),
                                  name="Event-augmented"))

    fig.update_layout(xaxis_title="Year", yaxis_title="% of adults", height=500, yaxis_range=[0, 100])
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Forecast table")
    st.dataframe(sub.round(1), use_container_width=True, hide_index=True)
    st.download_button(
        "Download forecasts as CSV", forecasts.to_csv(index=False).encode(),
        file_name="ethiopia_fi_forecasts.csv", mime="text/csv",
    )

    st.subheader("Key projected milestones")
    last_row = sub.iloc[-1]
    st.markdown(
        f"- By **{int(last_row['year'])}**, the base trend projects **{last_row['trend_base']:.1f}%**, "
        f"with a scenario range of **{last_row['scenario_pessimistic']:.1f}% - {last_row['scenario_optimistic']:.1f}%**."
    )
    if "event_augmented" in sub.columns and sub["event_augmented"].notna().any():
        st.markdown(f"- The event-augmented model (cataloged policies/launches) projects **{last_row['event_augmented']:.1f}%** by {int(last_row['year'])}.")


# ----------------------------------------------------------------------------
# Inclusion Projections page
# ----------------------------------------------------------------------------

def render_projections():
    st.title("Inclusion Projections")
    st.caption("Progress toward official targets, and a scenario selector for the projection horizon.")

    if forecasts is None:
        st.warning("`data/processed/forecasts.csv` not found \u2014 run the Task 4 notebook first.")
        return

    scenario = st.select_slider(
        "Scenario", options=["Pessimistic", "Base", "Optimistic"], value="Base",
    )
    scenario_col = {"Pessimistic": "scenario_pessimistic", "Base": "trend_base", "Optimistic": "scenario_optimistic"}[scenario]

    acc_target = targets[targets["indicator_code"] == "ACC_OWNERSHIP"]
    target_value = acc_target["value_numeric"].iloc[0] if not acc_target.empty else None
    target_year = acc_target["observation_date"].dt.year.iloc[0] if not acc_target.empty else None

    acc_fc = forecasts[forecasts["indicator_code"] == "ACC_OWNERSHIP"].sort_values("year")
    hist = indicator_series("ACC_OWNERSHIP")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist["observation_date"].dt.year, y=hist["value_numeric"],
                              mode="lines+markers", marker=dict(size=9, color="black"), name="Observed"))
    fig.add_trace(go.Scatter(x=acc_fc["year"], y=acc_fc[scenario_col], mode="lines+markers",
                              line=dict(color="royalblue"), name=f"{scenario} projection"))
    if target_value is not None:
        fig.add_hline(y=target_value, line_dash="dash", line_color="red",
                       annotation_text=f"NFIS-II target: {target_value:.0f}% by {target_year}")
    fig.update_layout(title="Account Ownership: progress toward the NFIS-II target",
                       xaxis_title="Year", yaxis_title="% of adults", height=480, yaxis_range=[0, 100])
    st.plotly_chart(fig, use_container_width=True)

    if target_value is not None:
        last_projection = acc_fc[scenario_col].iloc[-1]
        gap = target_value - last_projection
        st.metric(
            f"Projected gap to {target_year} target ({scenario} scenario)",
            f"{gap:+.1f} pp" if gap > 0 else "Target reached",
        )

    st.markdown("---")
    st.subheader("Access vs. Usage, side by side")
    both = forecasts.copy()
    fig2 = px.line(both, x="year", y=scenario_col, color="indicator_label", markers=True,
                    labels={scenario_col: "% of adults", "indicator_label": "Indicator"})
    fig2.update_layout(height=420, yaxis_range=[0, 100])
    st.plotly_chart(fig2, use_container_width=True)

    st.download_button(
        "Download projections as CSV", forecasts.to_csv(index=False).encode(),
        file_name="ethiopia_fi_projections.csv", mime="text/csv",
    )


# ----------------------------------------------------------------------------

if page == "Overview":
    render_overview()
elif page == "Trends":
    render_trends()
elif page == "Forecasts":
    render_forecasts()
elif page == "Inclusion Projections":
    render_projections()
