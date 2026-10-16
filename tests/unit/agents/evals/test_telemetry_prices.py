"""The BigQuery price table of the usage telemetry (`agents/telemetry/views/05_prices_cost.sql`) is `pricing.py`'s."""

import re
from pathlib import Path

import pytest

from agents.evals.pricing import CACHE_READ_FACTOR, CACHE_WRITE_FACTOR, PRICES, surcharge


VIEWS = Path(__file__).resolve().parents[4] / "agents" / "telemetry" / "views"
ROW = re.compile(
    r"STRUCT\('(?P<model>[a-z0-9.-]+)' AS model, (?P<input>[0-9.]+) AS input_usd_per_m, "
    r"(?P<output>[0-9.]+) AS output_usd_per_m\)"
)


def price_rows() -> dict[str, tuple[float, float]]:
    text = (VIEWS / "05_prices_cost.sql").read_text()
    return {m["model"]: (float(m["input"]), float(m["output"])) for m in ROW.finditer(text)}


def test_every_listed_model_has_its_eu_price() -> None:
    rows = price_rows()
    assert set(rows) == set(PRICES)
    for model, price in PRICES.items():
        assert rows[model] == (
            pytest.approx(price.input * surcharge("eu")),
            pytest.approx(price.output * surcharge("eu")),
        ), model


def test_the_cost_view_uses_the_cache_factors() -> None:
    text = (VIEWS / "05_prices_cost.sql").read_text()
    assert f"input_usd_per_m * {CACHE_READ_FACTOR}" in text
    assert f"input_usd_per_m * {CACHE_WRITE_FACTOR}" in text


def test_the_settings_models_are_priced() -> None:
    from agents.anyplot.settings import AgentSettings

    fields = AgentSettings.model_fields
    for name in ("model", "judge_model"):
        assert fields[name].default in price_rows(), name


def test_the_views_name_one_project_and_dataset() -> None:
    """The views are created as written (`docs/reference/agent-telemetry.md`): one project, two datasets."""
    names = set()
    for path in sorted(VIEWS.glob("*.sql")):
        names |= set(re.findall(r"`(anyplot\.[a-z_]+)\.[A-Za-z_]+`", path.read_text()))
    assert names == {"anyplot.agent_telemetry", "anyplot.agent_telemetry_logs"}
