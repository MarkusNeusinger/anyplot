"""Tests for the free direction of a polar plot's radial tick labels: the harness's `polar` probe and `rlabel_hint`.

The owner's case of 2026-10-12 (seaborn `polar-scatter`, `y = sin(x)` for x from -pi to pi, the
radius from -1) is generalised here into synthetic figures: the repair had moved the radial labels
to 67.5°, onto the data, because it had to guess an angle.
"""

from typing import Any

import matplotlib
import numpy as np
import pytest
from matplotlib.figure import Figure

from agents.anyplot import pipeline
from agents.anyplot.render import harness
from agents.anyplot.render.backends.fake import fixture_png
from agents.anyplot.render.contract import RenderResult, ThemeOutput
from agents.anyplot.render.gates import evaluate
from agents.anyplot.render.polar import ANGLE_BINS, RINGS, rlabel_hint
from agents.anyplot.schemas import MAX_NOTE_CHARS, MAX_NOTES


matplotlib.use("Agg")


def polar_figure(theta: np.ndarray, radius: np.ndarray, *, rlabel: float | None = None, **setup: Any) -> Figure:
    figure = Figure()
    axes = figure.add_subplot(projection="polar")
    axes.scatter(theta, radius)
    if "rlim" in setup:
        axes.set_rlim(*setup["rlim"])
    if "zero" in setup:
        axes.set_theta_zero_location(setup["zero"])
    if "direction" in setup:
        axes.set_theta_direction(setup["direction"])
    if "span" in setup:
        axes.set_thetamin(setup["span"][0])
        axes.set_thetamax(setup["span"][1])
    if rlabel is not None:
        axes.set_rlabel_position(rlabel)
    return figure


def sine(rlabel: float | None = None, **setup: Any) -> Figure:
    """The owner's data: 200 points of y = sin(x) on a polar scatter, theta = x, radius = y from -1."""
    x = np.linspace(-np.pi, np.pi, 200)
    return polar_figure(x, np.sin(x), rlabel=rlabel, **{"rlim": (-1, 1), **setup})


def half(rlabel: float = 22.5) -> Figure:
    """Points only in the upper half, angles 0° to 170°, at the outer half of the radius."""
    rng = np.random.default_rng(7)
    theta = np.radians(rng.uniform(0, 170, 300))
    return polar_figure(theta, rng.uniform(0.5, 1.0, 300), rlabel=rlabel, rlim=(0, 1))


class TestProbe:
    def test_the_probe_describes_each_polar_axes(self) -> None:
        (entry,) = harness.polar_report(sine(rlabel=67.5))

        assert entry["rlabel"] == pytest.approx(67.5)
        assert (entry["thetamin"], entry["thetamax"]) == (0.0, 360.0)
        assert len(entry["bins"]) == ANGLE_BINS and {len(rings) for rings in entry["bins"]} == {RINGS}
        assert sum(map(sum, entry["bins"])) == 200

    def test_a_figure_without_polar_axes_has_no_entry(self) -> None:
        figure = Figure()
        figure.add_subplot().scatter([1, 2], [3, 4])

        assert harness.polar_report(figure) == []

    def test_points_outside_the_visible_radius_are_left_out(self) -> None:
        """With the radius from 0, the negative half of sin(x) is outside the view."""
        (entry,) = harness.polar_report(sine(rlim=(0, 1)))

        assert sum(map(sum, entry["bins"])) == 100

    def test_degrees_converted_by_the_code_and_radians_give_the_same_bins(self) -> None:
        degrees = np.linspace(0, 180, 50)
        radius = np.linspace(0.2, 1.0, 50)
        converted = harness.polar_report(polar_figure(np.deg2rad(degrees), radius, rlim=(0, 1)))
        radians = harness.polar_report(polar_figure(degrees * np.pi / 180, radius, rlim=(0, 1)))

        assert converted[0]["bins"] == radians[0]["bins"]

    def test_the_probe_json_carries_the_polar_field(self, tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        original = Figure.savefig
        try:
            harness.install_probe("light")
            sine(rlabel=67.5).savefig(tmp_path / "plot-light.png")
        finally:
            Figure.savefig = original
        probe = (tmp_path / "probe-light.json").read_text(encoding="utf-8")

        assert '"polar": [{"rlabel": 67.5' in probe


class TestHint:
    def test_the_owners_case_moves_the_labels_off_the_data(self) -> None:
        """At 67.5° the labels sat on the outer arc; at 270° the curve runs through the centre."""
        hint = rlabel_hint(harness.polar_report(sine(rlabel=67.5)))

        assert hint is not None
        assert hint.startswith("polar radial tick labels: at 67.5° they sit on ")
        assert "ax.set_rlabel_position(270)" in hint and "0 points there" in hint
        assert "Likely cause:" in hint

    def test_the_default_angle_is_measured_too(self) -> None:
        hint = rlabel_hint(harness.polar_report(sine()))

        assert hint is not None and "at 22.5°" in hint and "set_rlabel_position(270)" in hint

    def test_data_in_one_half_sends_the_labels_to_the_empty_half_nearest_the_current_angle(self) -> None:
        hint = rlabel_hint(harness.polar_report(half(rlabel=22.5)))

        assert hint is not None and "ax.set_rlabel_position(337.5)" in hint

    def test_evenly_spread_data_gives_no_hint(self) -> None:
        rng = np.random.default_rng(1)
        figure = polar_figure(rng.uniform(0, 2 * np.pi, 600), rng.uniform(0, 1, 600), rlim=(0, 1))

        assert rlabel_hint(harness.polar_report(figure)) is None

    def test_labels_on_a_free_ray_get_no_hint(self) -> None:
        assert rlabel_hint(harness.polar_report(half(rlabel=270))) is None

    def test_the_angle_is_in_the_axes_own_coordinates_whatever_the_offset_and_direction(self) -> None:
        """`set_rlabel_position` takes the data's theta, so the same data gives the same target."""
        plain = rlabel_hint(harness.polar_report(sine(rlabel=67.5)))
        turned = rlabel_hint(harness.polar_report(sine(rlabel=67.5, zero="N", direction=-1)))

        assert plain == turned

    def test_a_partial_span_offers_only_rays_inside_it(self) -> None:
        """On a quarter from 0° to 90° with data up to 40°, the free ray is 67.5°, never one beyond 90°."""
        theta = np.radians(np.linspace(0, 40, 80))
        figure = polar_figure(theta, np.linspace(0.3, 1.0, 80), rlabel=20, rlim=(0, 1), span=(0, 90))
        hint = rlabel_hint(harness.polar_report(figure))

        assert hint is not None and "set_rlabel_position(67.5)" in hint
        whole = polar_figure(theta, np.linspace(0.3, 1.0, 80), rlabel=20, rlim=(0, 1))
        assert "set_rlabel_position(337.5)" in (rlabel_hint(harness.polar_report(whole)) or "")

    def test_the_hint_fits_a_note(self) -> None:
        hint = rlabel_hint(harness.polar_report(sine(rlabel=67.5)))

        assert hint is not None and len(hint) <= MAX_NOTE_CHARS

    @pytest.mark.parametrize(
        "polar",
        [
            None,
            "x",
            [None],
            [{"rlabel": 67.5, "thetamin": 0, "thetamax": 360}],
            [{"rlabel": float("nan"), "thetamin": 0, "thetamax": 360, "bins": [[0] * RINGS] * ANGLE_BINS}],
            [{"rlabel": True, "thetamin": 0, "thetamax": 360, "bins": [[0] * RINGS] * ANGLE_BINS}],
            [{"rlabel": 0, "thetamin": 0, "thetamax": 360, "bins": [[1] * RINGS] * (ANGLE_BINS - 1)}],
            [{"rlabel": 0, "thetamin": 0, "thetamax": 360, "bins": [[True] * RINGS] * ANGLE_BINS}],
            [{"rlabel": 0, "thetamin": 0, "thetamax": 360, "bins": [[-1] * RINGS] * ANGLE_BINS}],
        ],
    )
    def test_a_malformed_probe_gives_no_hint(self, polar: Any) -> None:
        assert rlabel_hint(polar) is None


class TestGateReport:
    def test_the_hint_is_a_repair_hint_never_a_defect(self) -> None:
        probe = {"canvas": [3200, 1800], "texts": [], "polar": harness.polar_report(sine(rlabel=67.5))}
        outputs = {theme: ThemeOutput(theme, 0, png=fixture_png(theme), probe=probe) for theme in ("light", "dark")}

        report = evaluate(RenderResult("abc123", outputs), themes=("light", "dark"), library="seaborn", rows=200)

        assert report.defects == [] and report.failed_gates == []
        assert len(report.repair_hints) == 1 and "set_rlabel_position(270)" in report.repair_hints[0]


class TestRepairHints:
    def test_measured_targets_come_first_without_duplicates_within_the_cap(self) -> None:
        run = pipeline.Run.__new__(pipeline.Run)
        run.repair_hints = ["polar target", "base 1"]
        base = [f"base {index}" for index in range(1, MAX_NOTES + 1)]

        hints = pipeline._repair_hints(base, run)

        assert hints[0] == "polar target" and hints.count("base 1") == 1
        assert len(hints) == MAX_NOTES
