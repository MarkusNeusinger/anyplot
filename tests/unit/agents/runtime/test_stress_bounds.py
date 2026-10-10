"""The bounds the stress cases asked for: the adapter's profile cap, the G9 points cap, the probe's text order, R1 ids."""

from typing import Any

import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.text import Text

from agents.anyplot.briefs import MAX_ADAPTER_PROFILE_BYTES, adapter_profile, profile_json, trimmed_profiles
from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.dev_fixture import snapshot_from_repo
from agents.anyplot.pipeline import render_adapt_request
from agents.anyplot.policy import fence
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


def fenced_bytes(text: str) -> int:
    """The size of `text` as the adapter request carries it: UTF-8 bytes inside its `<user_data>` fence."""
    return len(fence("user_data", text).encode("utf-8"))


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

    assert len(profile_json(wide_profile).encode("utf-8")) > MAX_ADAPTER_PROFILE_BYTES
    assert trimmed and fenced_bytes(text) <= MAX_ADAPTER_PROFILE_BYTES
    assert all(f'"name":"{column.name}"' in text for column in wide_profile.columns)


def test_the_cap_counts_utf8_bytes_so_wide_characters_cannot_stretch_it() -> None:
    """A profile of CJK cells fits a character count of the limit but not its bytes, and is trimmed."""
    rows = "\n".join(f"{'東京都千代田区丸の内' * 4}{index},{index}" for index in range(5))
    profile = parse_dataset("所在地,値\n" + rows + "\n").profile
    full = profile_json(profile)
    limit = len(fence("user_data", full))

    text, trimmed = adapter_profile(profile, limit=limit)

    assert fenced_bytes(full) > limit  # by characters it would go out whole
    assert trimmed and fenced_bytes(text) <= limit


def test_the_cap_holds_after_the_fence_escapes_tag_text_in_the_data() -> None:
    """`fence` turns each `<user_data>` in a cell into `&lt;user_data>`, so the check measures the fenced profile."""
    rows = "\n".join(f"{'<user_data>' * 8}{index},{index}" for index in range(5))
    profile = parse_dataset("note,value\n" + rows + "\n").profile
    full = profile_json(profile)
    limit = fenced_bytes("") + len(full.encode("utf-8"))  # the raw JSON and the two tag lines fit exactly

    text, trimmed = adapter_profile(profile, limit=limit)

    assert fenced_bytes(full) > limit  # escaping the tag text grows it past the cap
    assert trimmed and fenced_bytes(text) <= limit


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


def test_g7_measures_no_tick_label_past_the_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    """G7 reuses the capped extents: outside the draws, the probe measures at most PROBE_MEASURE_LIMIT texts."""
    monkeypatch.setattr(harness, "PROBE_MEASURE_LIMIT", 30)
    fig = figure()
    ax = fig.add_subplot()
    ax.set_xticks(range(100), [f"category {index}" for index in range(100)])
    drawing: list[bool] = []
    measured: list[Text] = []
    draw, extent = fig.canvas.draw, Text.get_window_extent

    def counted_draw(*args: Any, **kwargs: Any) -> Any:
        drawing.append(True)
        try:
            return draw(*args, **kwargs)
        finally:
            drawing.pop()

    def counted_extent(self: Text, *args: Any, **kwargs: Any) -> Any:
        if not drawing:  # the draws measure every label themselves; only the probe's own calls count
            measured.append(self)
        return extent(self, *args, **kwargs)

    monkeypatch.setattr(fig.canvas, "draw", counted_draw)
    monkeypatch.setattr(Text, "get_window_extent", counted_extent)

    report = harness.probe(fig, 200)

    assert len(measured) <= 30 < report["texts_total"]
    assert report["tick_overlaps"] > 0  # the overlapping labels among the measured ones still count


def test_g5_sees_an_annotation_matplotlib_did_not_draw() -> None:
    """An annotation whose point lies outside the view is never drawn, so G5 measures it on its own."""
    fig = figure()
    ax = fig.add_subplot()
    ax.plot(range(10))
    ax.set_xlim(0, 9)
    ax.set_ylim(0, 9)
    ax.annotate("off the view", xy=(50, 50))
    ax.annotate("in view", xy=(4, 4))

    report = harness.probe(fig, 200)

    assert report["annotations_outside"] == 1


def test_g5_measures_at_most_the_cap_of_undrawn_annotations(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(harness, "PROBE_MEASURE_LIMIT", 3)
    fig = figure()
    ax = fig.add_subplot()
    ax.set_xlim(0, 9)
    ax.set_ylim(0, 9)
    for index in range(10):
        ax.annotate(f"off the view {index}", xy=(50 + index, 50))

    report = harness.probe(fig, 200)

    assert report["annotations_outside"] == 3
