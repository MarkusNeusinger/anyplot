"""Tests for `agentic.workflows.modules.regen.plan`."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentic.workflows.modules.regen import PlanSpec
from agentic.workflows.modules.regen.plan import (
    archive,
    change_request_for,
    list_libraries,
    mark_done,
    mark_failed,
    next_unchecked,
    parse_plan,
    spec_title,
    write_plan,
)


def _make_synthetic_plots(root: Path, spec: str = "scatter-basic", libs: list[str] | None = None) -> None:
    libs = libs or ["altair", "matplotlib", "plotly"]
    impl_dir = root / spec / "implementations" / "python"
    impl_dir.mkdir(parents=True)
    for lib in libs:
        (impl_dir / f"{lib}.py").write_text("# stub\n", encoding="utf-8")
    (impl_dir / "__init__.py").write_text("", encoding="utf-8")  # should be excluded
    (root / spec / "specification.md").write_text(f"# {spec}: Basic Scatter Plot\n\nDescription...\n", encoding="utf-8")


def test_list_libraries_excludes_init(tmp_path):
    _make_synthetic_plots(tmp_path)
    libs = list_libraries("scatter-basic", plots_root=tmp_path)
    assert libs == ["altair", "matplotlib", "plotly"]


def test_list_libraries_missing_dir(tmp_path):
    libs = list_libraries("nonexistent", plots_root=tmp_path)
    assert libs == []


def test_spec_title_strips_id_prefix(tmp_path):
    _make_synthetic_plots(tmp_path)
    title = spec_title("scatter-basic", plots_root=tmp_path)
    assert title == "Basic Scatter Plot"


def test_write_and_parse_plan_round_trip(tmp_path):
    plan_path = tmp_path / "plan.md"
    spec = PlanSpec(
        spec_id="scatter-basic",
        title="Basic Scatter Plot",
        latest_update="2026-01-01T00:00:00Z",
        libraries=["altair", "matplotlib"],
    )
    write_plan(spec, plan_path=plan_path)
    text = plan_path.read_text(encoding="utf-8")
    assert "# Regen plan: scatter-basic" in text
    assert "- [ ] altair" in text
    assert "- [ ] matplotlib" in text
    # Empty change_requests means the section heading is omitted entirely.
    assert "## Change Requests" not in text

    spec_id, title, lines, change_requests = parse_plan(plan_path=plan_path)
    assert spec_id == "scatter-basic"
    assert title == "Basic Scatter Plot"
    assert [line.library for line in lines] == ["altair", "matplotlib"]
    assert all(line.state == " " for line in lines)
    assert change_requests == {}


def test_write_and_parse_plan_round_trip_with_change_requests(tmp_path):
    plan_path = tmp_path / "plan.md"
    spec = PlanSpec(
        spec_id="sparkline-basic",
        title="Basic Sparkline",
        latest_update="2026-01-01T00:00:00Z",
        libraries=["altair", "bokeh", "highcharts"],
        change_requests={
            "altair": "Pick a different data domain — current matches bokeh exactly.",
            "bokeh": "Use Bokeh's interactive glyph features to differentiate.",
        },
    )
    write_plan(spec, plan_path=plan_path)
    text = plan_path.read_text(encoding="utf-8")
    assert "## Change Requests" in text
    assert "- altair: Pick a different data domain — current matches bokeh exactly." in text
    assert "- bokeh: Use Bokeh's interactive glyph features to differentiate." in text
    # highcharts has no change_request — must NOT appear in the section
    assert "- highcharts:" not in text
    # Section ordering: Libraries → Change Requests → Log
    assert text.index("## Libraries") < text.index("## Change Requests") < text.index("## Log")

    spec_id, title, lines, change_requests = parse_plan(plan_path=plan_path)
    assert spec_id == "sparkline-basic"
    assert [line.library for line in lines] == ["altair", "bokeh", "highcharts"]
    assert change_requests == {
        "altair": "Pick a different data domain — current matches bokeh exactly.",
        "bokeh": "Use Bokeh's interactive glyph features to differentiate.",
    }


def test_change_request_for_returns_empty_when_missing(tmp_path):
    plan_path = tmp_path / "plan.md"
    write_plan(
        PlanSpec(
            spec_id="s",
            title="t",
            latest_update="x",
            libraries=["altair", "bokeh"],
            change_requests={"altair": "Switch domain"},
        ),
        plan_path=plan_path,
    )
    assert change_request_for("altair", plan_path=plan_path) == "Switch domain"
    assert change_request_for("bokeh", plan_path=plan_path) == ""
    assert change_request_for("nonexistent", plan_path=plan_path) == ""


def test_write_plan_drops_change_request_keys_not_in_libraries(tmp_path):
    plan_path = tmp_path / "plan.md"
    write_plan(
        PlanSpec(
            spec_id="s",
            title="t",
            latest_update="x",
            libraries=["altair"],
            # 'plotly' is not a library in this plan — must be silently dropped
            change_requests={"altair": "Real one", "plotly": "Stray key"},
        ),
        plan_path=plan_path,
    )
    text = plan_path.read_text(encoding="utf-8")
    assert "- altair: Real one" in text
    assert "- plotly:" not in text


def test_parse_plan_does_not_pick_up_log_lines_as_change_requests(tmp_path):
    """Log section bullets share the `- {lib}: ...` shape — they must NOT leak into change_requests."""
    plan_path = tmp_path / "plan.md"
    write_plan(PlanSpec(spec_id="s", title="t", latest_update="x", libraries=["altair"]), plan_path=plan_path)
    mark_done("altair", "https://github.com/x/y/pull/1", 87, "APPROVED", plan_path=plan_path)
    _spec_id, _title, _lines, change_requests = parse_plan(plan_path=plan_path)
    assert change_requests == {}


def test_next_unchecked_returns_first_unchecked(tmp_path):
    plan_path = tmp_path / "plan.md"
    write_plan(PlanSpec(spec_id="s", title="t", latest_update="x", libraries=["a", "b", "c"]), plan_path=plan_path)
    assert next_unchecked(plan_path=plan_path) == ("s", "t", "a", "")


def test_next_unchecked_includes_change_request(tmp_path):
    plan_path = tmp_path / "plan.md"
    write_plan(
        PlanSpec(
            spec_id="s",
            title="t",
            latest_update="x",
            libraries=["altair", "bokeh"],
            change_requests={"altair": "Switch to fitness data"},
        ),
        plan_path=plan_path,
    )
    assert next_unchecked(plan_path=plan_path) == ("s", "t", "altair", "Switch to fitness data")
    mark_done("altair", "url", 80, "APPROVED", plan_path=plan_path)
    # bokeh has no change_request → empty 4th field
    assert next_unchecked(plan_path=plan_path) == ("s", "t", "bokeh", "")


def test_next_unchecked_returns_none_when_all_done(tmp_path):
    plan_path = tmp_path / "plan.md"
    write_plan(PlanSpec(spec_id="s", title="t", latest_update="x", libraries=["a"]), plan_path=plan_path)
    mark_done("a", "https://github.com/x/y/pull/1", 87, "APPROVED", plan_path=plan_path)
    assert next_unchecked(plan_path=plan_path) is None


def test_mark_done_ticks_box_and_appends_log(tmp_path):
    plan_path = tmp_path / "plan.md"
    write_plan(
        PlanSpec(spec_id="s", title="t", latest_update="x", libraries=["altair", "matplotlib"]), plan_path=plan_path
    )
    mark_done("altair", "https://github.com/x/y/pull/42", 90, "APPROVED", plan_path=plan_path)
    text = plan_path.read_text(encoding="utf-8")
    assert "- [x] altair" in text
    assert "- [ ] matplotlib" in text
    assert "altair: PR https://github.com/x/y/pull/42, score 90, label ai-approved, verdict APPROVED" in text


def test_mark_failed_uses_bang(tmp_path):
    plan_path = tmp_path / "plan.md"
    write_plan(PlanSpec(spec_id="s", title="t", latest_update="x", libraries=["pygal"]), plan_path=plan_path)
    mark_failed("pygal", "gsutil unauthenticated", plan_path=plan_path)
    text = plan_path.read_text(encoding="utf-8")
    assert "- [!] pygal" in text
    assert "FAILED — gsutil unauthenticated" in text


def test_mark_done_unknown_library_raises(tmp_path):
    plan_path = tmp_path / "plan.md"
    write_plan(PlanSpec(spec_id="s", title="t", latest_update="x", libraries=["altair"]), plan_path=plan_path)
    with pytest.raises(ValueError):
        mark_done("matplotlib", "url", 80, "APPROVED", plan_path=plan_path)


def test_archive_moves_plan_to_history(tmp_path):
    plan_path = tmp_path / "plan.md"
    history = tmp_path / "history"
    write_plan(PlanSpec(spec_id="scatter-basic", title="t", latest_update="x", libraries=["a"]), plan_path=plan_path)
    dest = archive(plan_path=plan_path, history_dir=history)
    assert not plan_path.exists()
    assert dest.exists()
    assert dest.parent == history
    assert dest.name.startswith("scatter-basic-")
    assert dest.name.endswith(".md")
