"""The switch eval's code checks (`agents/evals/carry.py`): each intent of the owner's examples, in each target's API."""

import pytest

from agents.anyplot.schemas import RememberItem
from agents.evals.carry import CHECKS, DATA, LABEL, OWNER_EXAMPLES, Outcome, check_code


PLOTLY = """
fig.add_trace(go.Scatter(x=df["Zeit"], y=df["Messwert"], mode="markers"))
fig.add_trace(go.Scatter(x=out["Zeit"], y=out["Messwert"], mode="markers",
    marker=dict(color="#B71D27", size=14, symbol="star")))
fig.add_hline(y=7, line_dash="dash")
fig.add_annotation(x=0.02, y=0.98, xref="paper", yref="paper", text="y = ax<sup>2</sup> + b", showarrow=False)
fig.update_layout(xaxis=dict(title="Zeit (h)", range=[0, 100]))
"""
GGPLOT2 = """
p <- ggplot(df, aes(x = Zeit, y = Messwert)) +
  geom_point() +
  geom_point(data = outliers, colour = "#B71D27", shape = 8, size = 4) +
  geom_hline(yintercept = 7, linetype = "dashed") +
  annotate("text", x = 2, y = 11, label = "y == a * x^2 + b", parse = TRUE, hjust = 0) +
  scale_x_continuous(limits = c(0, 100)) +
  labs(x = "Zeit (h)")
"""


@pytest.mark.parametrize(("library", "code"), [("plotly", PLOTLY), ("ggplot2", GGPLOT2)])
def test_every_intent_is_found_in_the_libraries_own_api(library: str, code: str) -> None:
    found = check_code(library, code)

    assert list(found) == [check.name for check in CHECKS[library]] and all(found.values()), found


@pytest.mark.parametrize("library", sorted(CHECKS))
def test_the_catalogue_plot_alone_carries_none_of_them(library: str) -> None:
    from agents.anyplot.dev_fixture import snapshot_from_repo

    found = check_code(library, snapshot_from_repo("scatter-basic", library).code)

    assert not any(found.values()), found


PLOTLY_DICTS = """
fig.add_trace(go.Scatter(x=[0, 100], y=[7, 7], mode="lines", line={"color": INK, "width": 1.5}))
fig.add_trace(go.Scatter(x=out["Zeit"], y=out["Messwert"], mode="markers", marker={"symbol": "star", "size": 16}))
fig.update_layout(
    xaxis={"title": {"text": "Zeit (h)"}, "range": [0, 100]},
    annotations=[{"text": "y = ax<sup>2</sup> + b", "x": 0.02, "y": 0.98, "xref": "paper", "yref": "paper"}],
)
"""
"""What the live run of 2026-11-02 shipped in plotly (a line trace at y = 7, dict-style keys): the same intents."""


def test_dict_style_plotly_carries_the_same_intents() -> None:
    assert all(check_code("plotly", PLOTLY_DICTS).values()), check_code("plotly", PLOTLY_DICTS)


def test_a_raw_latex_string_is_no_formula_in_plotly() -> None:
    """The renderer's browser loads no MathJax: the first live run drew `$y = ax^2 + b$` as typed."""
    raw = PLOTLY_DICTS.replace("y = ax<sup>2</sup> + b", "$y = ax^2 + b$")

    assert check_code("plotly", raw)["latex_annotation"] is False


def test_other_values_are_no_match() -> None:
    wrong = PLOTLY.replace("y=7", "y=8").replace('symbol="star"', 'symbol="circle"').replace("[0, 100]", "[0, 50]")
    found = check_code("plotly", wrong)

    assert (found["reference_line"], found["star_markers"], found["x_limits"]) == (False, False, False)
    assert found["label_text"] and found["latex_annotation"]


def test_the_examples_are_valid_memory_items_and_the_data_parses() -> None:
    from agents.anyplot.data.parse import parse_dataset

    assert [RememberItem.model_validate(item).kind for item in OWNER_EXAMPLES] == [
        "reference_line",
        "annotation",
        "marker",
        "axis_label",
        "limits",
    ]
    assert parse_dataset(DATA).profile.rows == 25


def test_a_target_passes_only_with_every_check_and_the_label_found() -> None:
    passing = Outcome("plotly", status="needs_attention", checks={"a": True})
    assert passing.passed
    assert not Outcome("plotly", status="ok", checks={"a": True}, requested_not_found=[LABEL]).passed
    assert not Outcome("plotly", status="ok", checks={"a": False}).passed
    assert not Outcome("plotly", status="failed", checks={"a": True}).passed
