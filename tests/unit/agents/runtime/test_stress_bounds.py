"""The bounds the stress cases asked for: the adapter's profile cap, the G9 points cap, the probe's text order, R1 ids."""

import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from agents.anyplot.briefs import MAX_ADAPTER_PROFILE_CHARS, adapter_profile, profile_json, trimmed_profiles
from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.dev_fixture import snapshot_from_repo
from agents.anyplot.pipeline import render_adapt_request
from agents.anyplot.render import harness
from agents.anyplot.render.backends.fake import fixture_png
from agents.anyplot.render.contract import RenderResult, ThemeOutput
from agents.anyplot.render.gates import MAX_PLOTTED_POINTS, evaluate
from agents.anyplot.schemas import AdaptRequest, Binding
from agents.anyplot.session_state import SessionView

from .conftest import CASES


def gates(probe: dict, rows: int = 61) -> tuple[list[str], list[str]]:
    output = ThemeOutput("light", 0, png=fixture_png("light"), probe=probe)
    report = evaluate(RenderResult("p", {"light": output}), themes=("light",), library="matplotlib", rows=rows)
    return report.failed_gates, report.advisory


def figure() -> Figure:
    fig = Figure(figsize=(16, 9))
    FigureCanvasAgg(fig)
    return fig


# --- The adapter's profile ---------------------------------------------------------------------


@pytest.fixture(scope="module")
def wide_profile():
    return parse_dataset((CASES / "stress-cap-profile" / "data.csv").read_text(encoding="utf-8")).profile


def test_a_small_profile_goes_to_the_adapter_whole() -> None:
    profile = parse_dataset("a,b\n1,2\n3,4\n").profile
    assert adapter_profile(profile) == (profile_json(profile), False)


def test_a_wide_profile_is_trimmed_to_the_cap_and_keeps_every_column(wide_profile) -> None:
    text, trimmed = adapter_profile(wide_profile)

    assert len(profile_json(wide_profile)) > MAX_ADAPTER_PROFILE_CHARS
    assert trimmed and len(text) <= MAX_ADAPTER_PROFILE_CHARS
    assert all(f'"name":"{column.name}"' in text for column in wide_profile.columns)


def test_below_the_smallest_version_the_last_version_still_goes_out(wide_profile) -> None:
    *_, last = trimmed_profiles(wide_profile)
    assert adapter_profile(wide_profile, limit=10) == last


def test_the_adapter_request_carries_the_trimmed_profile_under_its_own_heading(wide_profile) -> None:
    snapshot = snapshot_from_repo("scatter-basic", "matplotlib")
    view = SessionView("scatter-basic", "matplotlib", "en", snapshot, snapshot.code, [], None)
    columns = [column.name for column in wide_profile.columns]
    request = AdaptRequest(
        code=snapshot.code,
        profile=wide_profile,
        bindings=[Binding(role="x", column=columns[0]), Binding(role="y", column=columns[1])],
        loader_columns=columns,
    )

    text = render_adapt_request(request, view)

    assert "Dataset profile (shortened: fewer sample rows or top values):" in text
    assert adapter_profile(wide_profile)[0] in text and profile_json(wide_profile) not in text


# --- G9 and the R1 limit ids -------------------------------------------------------------------


def test_g9_reports_more_plotted_points_than_any_dataset_holds() -> None:
    failed, advisory = gates({"points": 10, "line_points": MAX_PLOTTED_POINTS})
    assert "G9" in failed and advisory[-1].startswith("DQ-03 (code): the plot draws 200010 points")
    assert gates({"points": 0, "line_points": MAX_PLOTTED_POINTS})[0] == []
    assert gates({"line_points": 10_000_000}, rows=61)[0] == ["G9"]


@pytest.mark.parametrize("value", [True, -5, "many", 1.5e9, None])
def test_g9_ignores_a_count_that_is_not_a_plain_number(value: object) -> None:
    assert "G9" not in gates({"points": 0, "line_points": value})[0]


def test_a_renderer_limit_is_recorded_as_its_r1_id() -> None:
    output = ThemeOutput("light", None, reason="memory", measured=400, limit=512)
    report = evaluate(RenderResult("m", {"light": output}), themes=("light",), library="matplotlib", rows=10)

    assert not report.passed_host_gates and report.failed_gates == ["R1-memory"]
    assert "below its 512 MiB floor" in report.blocking[0]


# --- The probe ---------------------------------------------------------------------------------


def test_the_probe_counts_the_vertices_of_visible_lines() -> None:
    fig = figure()
    ax = fig.add_subplot()
    ax.plot(range(1_000))
    ax.plot(range(10), marker="o")
    hidden = ax.plot(range(500))[0]
    hidden.set_visible(False)
    ax.scatter(range(7), range(7))

    report = harness.probe(fig, 200)

    assert (report["line_points"], report["points"]) == (1_010, 7)


def test_the_probe_keeps_clipped_texts_when_it_drops_some() -> None:
    fig = figure()
    ax = fig.add_subplot()
    for index in range(harness.PROBE_LIMIT + 50):
        ax.text(0.5, 0.5, f"label {index}", transform=ax.transAxes)
    fig.text(1.05, 0.5, "drawn last, past the right edge")

    report = harness.probe(fig, 200)

    assert len(report["texts"]) == harness.PROBE_LIMIT < report["texts_total"]
    assert report["texts"][0]["box"][2] > report["canvas"][0]
    assert "G3" in gates(report)[0]


def test_the_probe_measures_only_the_first_texts_it_drew(monkeypatch: pytest.MonkeyPatch) -> None:
    """Each extent costs CPU under the sandbox's limit, so the probe stops measuring after PROBE_MEASURE_LIMIT."""
    monkeypatch.setattr(harness, "PROBE_MEASURE_LIMIT", 30)
    monkeypatch.setattr(harness, "PROBE_LIMIT", 20)
    fig = figure()
    ax = fig.add_subplot()
    for index in range(60):
        ax.text(0.5, 0.5, f"label {index}", transform=ax.transAxes)
    fig.text(1.05, 0.5, "drawn last, past the right edge")

    report = harness.probe(fig, 200)

    assert len(report["texts"]) == 20 and report["texts_total"] > 60
    # The clipped text was drawn after the first 30, so it was never measured and G3 misses it.
    assert all(text["box"][2] <= report["canvas"][0] for text in report["texts"])
