"""
Task 5: smoke + interaction tests for dashboard/app.py.

Uses Streamlit's official AppTest harness to actually execute the script
(catching import errors, KeyErrors on missing columns, etc.) rather than
just checking that the file parses. This is what caught a missing-plotly
dependency during development -- a plain py_compile would have missed it.
"""
import os

import pandas as pd
import pytest

streamlit_testing = pytest.importorskip("streamlit.testing.v1")
AppTest = streamlit_testing.AppTest

APP_PATH = os.path.join(os.path.dirname(__file__), "..", "dashboard", "app.py")

PAGES = ["Overview", "Trends", "Forecasts", "Inclusion Projections"]


def _navigate(page):
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    assert not at.exception, f"App failed to initialize: {at.exception}"
    at.sidebar.radio[0].set_value(page).run(timeout=30)
    return at


@pytest.mark.parametrize("page", PAGES)
def test_page_renders_without_exception(page):
    at = _navigate(page)
    assert not at.exception, f"[{page}] raised: {at.exception}"


def test_overview_shows_four_metric_cards():
    at = _navigate("Overview")
    assert len(at.metric) == 4


def test_at_least_four_interactive_charts_across_app():
    total_charts = 0
    for page in PAGES:
        at = _navigate(page)
        total_charts += len(at.get("plotly_chart"))
    assert total_charts >= 4


def test_trends_multiselect_and_event_toggle_do_not_crash():
    at = _navigate("Trends")
    assert at.multiselect, "Trends page should expose an indicator multiselect"
    at.multiselect[0].select("ACC_MM_ACCOUNT").run(timeout=30)
    assert not at.exception
    if at.checkbox:
        at.checkbox[0].set_value(False).run(timeout=30)
        assert not at.exception


def test_forecasts_indicator_and_view_switch_do_not_crash():
    at = _navigate("Forecasts")
    assert at.selectbox, "Forecasts page should expose an indicator selector"
    # NOTE: at.selectbox[0].options returns the *formatted display labels*
    # (post format_func), not the raw indicator_code values the widget's
    # set_value() actually expects. Read the raw codes straight from the
    # data instead of round-tripping through the formatted display strings.
    forecasts_path = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "forecasts.csv")
    codes = pd.read_csv(forecasts_path)["indicator_code"].unique()
    assert len(codes) >= 1
    at.selectbox[0].set_value(codes[-1]).run(timeout=30)
    assert not at.exception
    if at.radio:
        at.radio[0].set_value(at.radio[0].options[-1]).run(timeout=30)
        assert not at.exception


def test_projections_scenario_selector_does_not_crash():
    at = _navigate("Inclusion Projections")
    assert at.select_slider, "Projections page should expose a scenario selector"
    for scenario in ["Pessimistic", "Base", "Optimistic"]:
        at.select_slider[0].set_value(scenario).run(timeout=30)
        assert not at.exception, f"scenario={scenario} raised: {at.exception}"
