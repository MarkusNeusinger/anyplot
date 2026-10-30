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


@pytest.mark.parametrize("model", sorted(PRICES))
@pytest.mark.parametrize("spelling", ["{}", "{}@20261001", "{}-20261001", "models/{}", " {} "])
def test_every_spelling_of_a_priced_model_finds_its_row(model: str, spelling: str) -> None:
    """The ids a provider reports (version suffixes, a `models/` prefix, case) reach the price row's key."""
    from agents.anyplot.telemetry import model_id

    assert model_id(spelling.format(model)) == model
    assert model_id(spelling.format(model).upper()) == model
    assert model in price_rows()


def test_a_turn_prices_each_step_at_its_model() -> None:
    """Every step of a turn carries a priced model: the judges' too (they book none of their own), and two models
    in one step stay two entries, each at its own price."""
    from agents.anyplot.plugins.ledger import StepUsage
    from agents.anyplot.telemetry import step_tokens

    usage = {
        "anyplot": StepUsage(calls=2, input=1000, output=100, model="claude-haiku-5-5@20261001"),
        "adapter_matplotlib": StepUsage(calls=1, input=500, output=50, model="claude-haiku-5-5"),
        "adapter_seaborn": StepUsage(calls=1, input=500, output=50, model="claude-sonnet-5-5"),
        "reviewer": StepUsage(calls=1, input=300, output=30, model="gemini-3.8-flash"),
        "judge": StepUsage(calls=3, input=90, output=9),
    }
    steps = step_tokens(usage, steps=("root", "adapter", "reviewer", "judge"), judge_model="gemini-3.5-flash-lite")
    assert [(step["step"], step["model"]) for step in steps] == [
        ("root", "claude-haiku-5-5"),
        ("adapter", "claude-haiku-5-5"),
        ("adapter", "claude-sonnet-5-5"),
        ("reviewer", "gemini-3.8-flash"),
        ("judge", "gemini-3.5-flash-lite"),
    ]
    assert all(step["model"] in price_rows() for step in steps)


def test_the_settings_models_are_priced() -> None:
    from agents.anyplot.settings import AgentSettings

    fields = AgentSettings.model_fields
    for name in ("model", "judge_model"):
        assert fields[name].default in price_rows(), name


def test_the_score_view_leaves_out_active_sessions() -> None:
    """Review of #12477: the view's contract says a version shows up once its session ended; its own join says so."""
    text = (VIEWS / "06_score_outcomes.sql").read_text()
    body = text.split("CREATE OR REPLACE VIEW", 1)[1]
    assert body.rstrip().endswith("WHERE sessions.state != 'active';")
    assert "LEFT JOIN `anyplot.agent_telemetry.sessions`" not in body


def test_the_views_name_one_project_and_dataset() -> None:
    """The views are created as written (`docs/reference/agent-telemetry.md`): one project, two datasets."""
    names = set()
    for path in sorted(VIEWS.glob("*.sql")):
        names |= set(re.findall(r"`(anyplot\.[a-z_]+)\.[A-Za-z_]+`", path.read_text()))
    assert names == {"anyplot.agent_telemetry", "anyplot.agent_telemetry_logs"}
