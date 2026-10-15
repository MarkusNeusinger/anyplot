"""G11 (per-mark labels and decorations past what the marks leave room for) and G12 (the plot language's decimal mark).

The fixtures generalise two findings of the live tests of 2026-10-14/15 (block H):

- Q3: bar-grouped on 26 cantons times two series kept the catalogue's per-bar value labels,
  dots on the bar tops and drop shadows, styled for its 12 example bars, on all 52 bars;
- Q4: German sessions showed "6.0 M" on an axis (the user asked for "6,5 Mio.") and seaborn
  bar labels "5.30" instead of "5,30".

The density report runs in-process on real matplotlib figures (the harness's own code); the
label lists stand for the probe's `labels` field (`{"kind", "text"}` per drawn text).
"""

import json
from typing import Any

import matplotlib.patheffects as patheffects
import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from agents.anyplot.language import NUMBER_FORMATS, number_format, number_format_table
from agents.anyplot.policy import adapter_instruction, adapter_rubric
from agents.anyplot.render import harness
from agents.anyplot.render.backends.fake import fixture_png
from agents.anyplot.render.contract import RenderResult, ThemeOutput
from agents.anyplot.render.gates import (
    MAX_VALUE_LABELS,
    _density_lines,
    _number_format_lines,
    evaluate,
    foreign_decimal,
)
from core.defects import DEFECT_RE


GERMAN = NUMBER_FORMATS["de"]
ENGLISH = NUMBER_FORMATS["en"]


def gate_lines(probe: dict[str, Any], plot_language: str | None = None) -> list[str]:
    output = ThemeOutput("light", 0, png=fixture_png("light", (3200, 1800)), probe=probe)
    report = evaluate(
        RenderResult("p", {"light": output}),
        themes=("light",),
        library="matplotlib",
        rows=100,
        plot_language=plot_language,
    )
    return report.advisory


def grouped_bars(categories: int, *, labels: bool = True, dots: bool = True, shadows: bool = True) -> plt.Figure:
    """The catalogue's bar-grouped style (value labels, dots on the bar tops, shadows) on `categories` x 2 bars."""
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
    x = np.arange(categories)
    values = np.random.default_rng(7).integers(500, 90_000, size=(2, categories))
    for offset, series in zip((-0.2, 0.2), values, strict=True):
        container = ax.bar(x + offset, series, 0.4)
        for rect in container:
            if shadows:
                rect.set_path_effects([patheffects.withSimplePatchShadow(offset=(4, -4))])
            top = rect.get_height()
            centre = rect.get_x() + rect.get_width() / 2
            if dots:
                ax.scatter(centre, top, s=34)
            if labels:
                ax.annotate(f"{int(top)}", xy=(centre, top), xytext=(0, 6), textcoords="offset points", ha="center")
    ax.set_xticks(x, [f"Region {index}" for index in range(categories)], rotation=90)
    return fig


@pytest.fixture(autouse=True)
def _close_figures() -> Any:
    yield
    plt.close("all")


class TestDensityReport:
    def test_the_live_case_52_bars_with_labels_dots_and_shadows(self) -> None:
        fig = grouped_bars(26)
        fig.canvas.draw()

        [axes] = harness.density_report(fig, 400)

        assert axes["bars"] == 52 and axes["labelled"] == 52
        assert axes["decorated"] == 104  # 52 dots on the bar tops and 52 shadowed bars
        assert axes["marks"] == 52  # the dots are decorations, not data marks
        assert axes["label_px"] > axes["slot_px"]
        [line] = _density_lines({"density": [axes]})
        assert line[0] == "G11"

    def test_the_catalogue_scale_is_clean(self) -> None:
        """The catalogue's own 4 categories x 3 series with 3-digit labels: what the style was made for."""
        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
        x = np.arange(4)
        for index, series in enumerate(([245, 312, 287, 425], [178, 195, 285, 310], [125, 210, 195, 165])):
            container = ax.bar(x + (index - 1) * 0.25, series, 0.25)
            ax.bar_label(container, fmt="%d", fontsize=9)
        fig.canvas.draw()

        [axes] = harness.density_report(fig, 400)

        assert axes["bars"] == 12 and axes["labelled"] == 12 and axes["decorated"] == 0
        assert _density_lines({"density": [axes]}) == []

    def test_heatmap_cell_annotations_are_no_value_labels(self) -> None:
        """Cell text sits on no bar or point: the rubric allows it (quality-criteria, cell annotations)."""
        fig, ax = plt.subplots(figsize=(6, 6), dpi=400)
        ax.imshow(np.ones((20, 20)))
        for row in range(20):
            for column in range(20):
                ax.text(column, row, "1", ha="center", va="center")
        fig.canvas.draw()

        assert harness.density_report(fig, 400) == []

    def test_a_label_on_every_point_of_a_long_line(self) -> None:
        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
        values = np.arange(60) ** 1.1
        ax.plot(np.arange(60), values, marker="o")
        for index, value in enumerate(values):
            ax.text(index, value + 1, f"{value:.0f}", ha="center")
        fig.canvas.draw()

        [axes] = harness.density_report(fig, 400)

        assert axes["bars"] == 0 and axes["labelled"] == 60
        [(gate, line)] = _density_lines({"density": [axes]})
        assert "60 marks carry 60 value labels" in line

    def test_one_callout_in_axes_coordinates_is_no_value_label(self) -> None:
        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
        ax.bar(range(40), range(1, 41))
        ax.annotate("Peak", xy=(0.5, 0.9), xycoords="axes fraction")
        fig.canvas.draw()

        [axes] = harness.density_report(fig, 400)

        assert axes["labelled"] == 0 and _density_lines({"density": [axes]}) == []

    def test_named_points_are_no_value_labels_review_d02(self) -> None:
        """Fable g11/d02 and perf/p04: 30 and 40 named scatter points (scatter-annotated asks for 10 to 50)."""
        for count in (30, 40):
            fig, ax = plt.subplots(figsize=(16, 9), dpi=100)
            rng = np.random.default_rng(9)
            x, y = rng.random(count) * 100, rng.random(count) * 100
            ax.scatter(x, y, s=80)
            for index, (xi, yi) in enumerate(zip(x, y, strict=True)):
                ax.text(xi + 1, yi + 1, f"Firm {index}", fontsize=9)
            fig.canvas.draw()

            [axes] = harness.density_report(fig, 200)

            assert axes["labelled"] == count and axes["numeric_labels"] == 0
            assert _density_lines({"density": [axes]}) == []

    def test_offset_shadow_bars_leave_the_space_per_label_review_d01(self) -> None:
        """Fable g11/d01: 12 labelled bars over 12 offset shadow bars once measured 8 px per bar."""
        fig, ax = plt.subplots(figsize=(16, 9), dpi=100)
        x = np.arange(12)
        y = np.random.default_rng(1).integers(50, 500, 12)
        ax.bar(x + 0.04, y - 4, color="#00000033", zorder=1)
        container = ax.bar(x, y, zorder=2)
        ax.bar_label(container, fmt="%d")
        fig.canvas.draw()

        [axes] = harness.density_report(fig, 200)

        assert axes["labelled"] == 12 and axes["slot_px"] > 150
        assert _density_lines({"density": [axes]}) == []

    def test_labelling_only_the_extremes_of_52_bars_is_clean(self) -> None:
        """Gemini on #12184: the fix G11 asks for must pass it."""
        fig = grouped_bars(26, labels=False, dots=False, shadows=False)
        ax = fig.axes[0]
        rects = [rect for container in ax.containers for rect in container]
        for rect in (max(rects, key=lambda r: r.get_height()), min(rects, key=lambda r: r.get_height())):
            ax.annotate(f"{int(rect.get_height())}", xy=(rect.get_x() + rect.get_width() / 2, rect.get_height()))
        fig.canvas.draw()

        [axes] = harness.density_report(fig, 400)

        assert axes["labelled"] == 2 and _density_lines({"density": [axes]}) == []

    def test_stacked_centre_labels_count_once_per_bar_review_p05(self) -> None:
        """Fable perf/p05 and g11/a05: `bar_label(label_type="center")` labels were not counted at all."""
        for positions, fires in ((8, False), (40, True)):
            fig, ax = plt.subplots(figsize=(16, 9), dpi=100)
            x = np.arange(positions)
            rng = np.random.default_rng(2)
            bottom = np.zeros(positions)
            for _ in range(4):
                values = rng.integers(20, 100, positions)
                container = ax.bar(x, values, bottom=bottom)
                ax.bar_label(container, label_type="center", fmt="%d", fontsize=6)
                bottom += values
            fig.canvas.draw()

            [axes] = harness.density_report(fig, 200)

            assert axes["labelled"] == 4 * positions and axes["labelled_bars"] == positions
            assert bool(_density_lines({"density": [axes]})) is fires

    def test_an_inverted_value_axis_keeps_the_bar_ends(self) -> None:
        """Gemini on #12184: the end of a bar on an inverted axis is its lower edge on the canvas."""
        fig = grouped_bars(26, labels=True, dots=True, shadows=False)
        fig.axes[0].invert_yaxis()
        fig.canvas.draw()

        [axes] = harness.density_report(fig, 400)

        assert axes["labelled"] == 52 and axes["decorated"] == 52

    def test_dots_drawn_with_plot_markers_are_decorations(self) -> None:
        """Gemini on #12184: `ax.plot(x, top, "o")` per bar, a Line2D of one vertex."""
        fig = grouped_bars(26, labels=False, dots=False, shadows=False)
        ax = fig.axes[0]
        for rect in [rect for container in ax.containers for rect in container]:
            ax.plot(rect.get_x() + rect.get_width() / 2, rect.get_height(), "o")
        fig.canvas.draw()

        [axes] = harness.density_report(fig, 400)

        assert axes["decorated"] == 52 and axes["marks"] == 52

    def test_a_clipped_text_outside_a_zoomed_view_is_not_counted(self) -> None:
        """Gemini on #12184: `ax.text(..., clip_on=True)` outside the view is never drawn."""
        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
        ax.bar(range(50), range(1, 51))
        for index in range(50):
            ax.text(index, index + 1.5, str(index + 1), ha="center", clip_on=True)
        ax.set_xlim(-0.5, 4.5)
        fig.canvas.draw()

        [axes] = harness.density_report(fig, 400)

        assert axes["labelled"] == 5

    def test_a_missing_bar_value_keeps_the_report_valid_json(self) -> None:
        """Copilot on #12184: a NaN bar (a group missing after a pivot) would void the probe's JSON."""
        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
        container = ax.bar(range(4), [3.0, float("nan"), 2.0, 1.0])
        ax.bar_label(container)
        fig.canvas.draw()

        [axes] = harness.density_report(fig, 400)

        assert axes["bars"] == 3
        json.dumps(axes, allow_nan=False)

    def test_bars_and_labels_outside_a_zoomed_view_are_not_counted(self) -> None:
        """Copilot on #12184: 50 labelled bars zoomed to five draw five labels."""
        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
        container = ax.bar(range(50), range(1, 51))
        ax.bar_label(container)
        ax.set_xlim(-0.5, 4.5)
        fig.canvas.draw()

        [axes] = harness.density_report(fig, 400)

        assert axes["bars"] == 5 and axes["labelled"] == 5

    def test_bars_zoomed_on_their_value_axis_still_count(self) -> None:
        """Copilot round 2 on #12184: 30 bars ending at 1000 under `ylim(900, 1100)` still draw their ends."""
        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
        container = ax.bar(range(30), [1000] * 30)
        ax.bar_label(container)
        ax.set_ylim(900, 1100)
        fig.canvas.draw()

        [axes] = harness.density_report(fig, 400)

        assert axes["bars"] == 30 and axes["labelled"] == 30
        assert _density_lines({"density": [axes]})

    def test_many_scatter_marks_are_matched_in_bounded_chunks(self) -> None:
        """Copilot on #12184: the pairwise arrays stay bounded however many marks the plot draws."""
        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
        container = ax.bar(range(30), range(1, 31))
        rng = np.random.default_rng(3)
        ax.scatter(rng.uniform(0, 29, 9_000), rng.uniform(0, 30, 9_000), s=1)
        ax.scatter([rect.get_x() + rect.get_width() / 2 for rect in container], range(1, 31), s=30)
        fig.canvas.draw()

        [axes] = harness.density_report(fig, 400)

        assert axes["decorated"] >= 30 and axes["marks"] < 9_030

    def test_the_probe_writes_the_density_field(self, tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Figure, "savefig", Figure.savefig)  # restored after the test
        harness.install_probe("light")
        fig = grouped_bars(26)
        fig.savefig("plot-light.png", dpi=100)

        probe = json.loads((tmp_path / "probe-light.json").read_text())
        assert probe["density"][0]["bars"] == 52
        assert probe["tick_axes"] == [{"x": "fixed", "y": "number"}]


class TestDensityGate:
    def test_the_line_is_a_measured_vq03_defect_line(self) -> None:
        probe = {
            "density": [{"bars": 52, "marks": 52, "labelled": 52, "decorated": 104, "slot_px": 35.0, "label_px": 160.0}]
        }

        [line] = gate_lines(probe)

        assert DEFECT_RE.match(line), line
        assert line.startswith("VQ-03 (light): 52 bars carry 52 value labels (160 px wide on 35 px per bar)")
        assert "104 dots or shadows" in line and f"at most {MAX_VALUE_LABELS} labels" in line
        assert "Likely cause:" in line

    @pytest.mark.parametrize(
        "entry",
        [
            {"bars": "52", "marks": 52, "labelled": 52},
            {"bars": True, "marks": 52, "labelled": 99},
            {"bars": 52, "marks": 52, "labelled": 10, "slot_px": float("nan"), "label_px": 1e9},
            "not an entry",
        ],
    )
    def test_a_tampered_entry_yields_no_line(self, entry: Any) -> None:
        assert gate_lines({"density": [entry]}) == []

    def test_a_malformed_density_never_hides_another_gate(self) -> None:
        lines = gate_lines({"density": "broken", "tick_overlaps": 3})

        assert any(line.startswith("VQ-02") for line in lines)

    def test_a_few_cramped_labels_are_callouts(self) -> None:
        entry = {"bars": 4, "marks": 4, "labelled": 3, "decorated": 0, "slot_px": 20.0, "label_px": 120.0}

        assert _density_lines({"density": [entry]}) == []


class TestForeignDecimal:
    @pytest.mark.parametrize(
        "text",
        [
            "5.30",
            "6.0 M",
            "0.25",
            "−1.5",
            "1,234.5",
            "12.5 %",
            "$ 3.75",
            "1,234,567",
            "5.30 €",  # review: a trailing currency, the German order
            "-$5.30",
            "0.125",  # review: a leading 0 is never a thousands group
            "−0.125",
        ],
    )
    def test_english_numbers_in_a_german_plot(self, text: str) -> None:
        assert foreign_decimal(text, GERMAN)

    def test_a_zero_padded_day_and_month_is_a_date(self) -> None:
        """Review of #12184: `14.10` in an annotation is a `%d.%m` date; `12.50` stays a decimal."""
        assert not foreign_decimal("14.10", GERMAN)
        assert foreign_decimal("12.50", GERMAN)
        assert not foreign_decimal("5,30 €", GERMAN)

    @pytest.mark.parametrize(
        "text",
        [
            "5,30",
            "6,5 Mio.",
            "1.234",  # a thousands mark
            "7.184.003",
            "1.234,5",
            "2024",
            "14.10.",  # a date, never a number
            "2024-10-14",
            "Q3",
            "3.11.1 Version",
            "1e6",
            "",
        ],
    )
    def test_german_numbers_and_non_numbers_pass(self, text: str) -> None:
        assert not foreign_decimal(text, GERMAN)

    @pytest.mark.parametrize("text", ["5,30", "6,5 M", "1.234,5"])
    def test_german_numbers_in_an_english_plot(self, text: str) -> None:
        assert foreign_decimal(text, ENGLISH)

    @pytest.mark.parametrize("text", ["5.30", "6.5 M", "1,234", "1,234,567", "1,234.5", "7.184.003", "2024"])
    def test_english_numbers_pass_in_english(self, text: str) -> None:
        assert not foreign_decimal(text, ENGLISH)


def probe_of(fig: plt.Figure, extra: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """The probe's `labels` (as `harness.drawn_labels` writes them, axes index included) and `tick_axes`."""
    fig.canvas.draw()
    labels: list[dict[str, Any]] = []
    for index, ax in enumerate(fig.get_axes()):
        labels += [{"kind": "annotation", "text": text.get_text()} for text in ax.texts]
        for name in ("x", "y"):
            ticks = getattr(ax, f"get_{name}ticklabels")()
            labels += [
                {"kind": f"{name} tick label", "text": t.get_text(), "axes": index} for t in ticks if t.get_text()
            ]
    return {"labels": labels + (extra or []), "tick_axes": harness.tick_axes(fig)}


def seaborn_style_bar_labels(fmt_label: Any, language: str) -> dict[str, Any]:
    """The live seaborn case: bar labels and y tick labels, and a title that names a version."""
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
    container = ax.bar(["A", "B", "C", "D"], [5.3, 4.25, 3.1, 2.05])
    ax.bar_label(container, labels=[fmt_label(value) for value in container.datavalues])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: fmt_label(value)))
    return probe_of(fig, [{"kind": "title", "text": f"Version 2.5 ({language})"}])


class TestNumberFormatGate:
    def test_the_live_german_case_is_a_vq06_line(self) -> None:
        probe = seaborn_style_bar_labels(lambda value: f"{value:.2f}", "de")

        [line] = gate_lines(probe, plot_language="de")

        assert DEFECT_RE.match(line), line
        assert line.startswith("VQ-06 (light): ")
        assert "use a decimal point; German writes a decimal comma" in line
        assert "Mio." in line and "annotations and tick labels" in line
        assert "5.30" not in line  # no label text reaches the line

    def test_the_fixed_german_case_is_clean(self) -> None:
        german = str.maketrans(",.", ".,")
        probe = seaborn_style_bar_labels(lambda value: f"{value:,.2f}".translate(german), "de")

        assert gate_lines(probe, plot_language="Deutsch") == []

    def test_the_english_control_is_clean_and_german_marks_in_english_are_named(self) -> None:
        english = seaborn_style_bar_labels(lambda value: f"{value:.2f}", "en")
        german = seaborn_style_bar_labels(lambda value: f"{value:.2f}".replace(".", ","), "en")

        assert gate_lines(english, plot_language="en") == []
        [line] = gate_lines(german, plot_language="en")
        assert "English writes a decimal point" in line

    def test_date_ticks_and_category_ticks_are_never_checked(self) -> None:
        """Copilot on #12184: a German `%d.%m` date (`14.10`) and a category the data names (`3.11`)."""
        import matplotlib.dates as mdates
        import pandas as pd

        fig, (dates, categories) = plt.subplots(1, 2, figsize=(8, 4.5), dpi=400)
        days = pd.date_range("2026-10-01", periods=20, freq="D")
        dates.plot(days, range(20))
        dates.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
        dates.set_yticks([0, 10, 20])
        categories.bar(["3.11", "3.12", "3.13"], [1, 2, 3])
        categories.set_yticks([0, 1, 2, 3])
        probe = probe_of(fig)

        assert {"date", "category"} <= {entry["x"] for entry in probe["tick_axes"]}
        assert any(label["text"] == "3.11" for label in probe["labels"])
        assert gate_lines(probe, plot_language="de") == []

    @pytest.mark.parametrize(("fmt", "fires"), [("{:.2f}", True), ("{:,.2f}", False)])
    def test_the_real_probe_end_to_end(
        self, fmt: str, fires: bool, tmp_path: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The harness's own probe file (block F's `labels`, this gate's `tick_axes`) through `evaluate`."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(Figure, "savefig", Figure.savefig)  # restored after the test
        harness.install_probe("light")
        german = str.maketrans(",.", ".,")

        def label(value: float) -> str:
            text = fmt.format(value)
            return text if fires else text.translate(german)

        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
        container = ax.bar(["Altbrunn", "Seefeld", "Hochmatt"], [5.3, 4.85, 6.12])
        ax.bar_label(container, labels=[label(value) for value in container.datavalues])
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: label(value)))
        fig.savefig("plot-light.png", dpi=100)
        probe = json.loads((tmp_path / "probe-light.json").read_text())

        lines = [line for line in gate_lines(probe, plot_language="de") if line.startswith("VQ-06")]

        assert probe["labels"] and probe["tick_axes"] == [{"x": "category", "y": "number"}]
        assert bool(lines) is fires

    def test_preconverted_date_coordinates_are_dates(self) -> None:
        """Copilot round 2 on #12184: `date2num` coordinates under a DateFormatter leave the converter unset."""
        import datetime

        import matplotlib.dates as mdates

        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
        start = datetime.datetime(2026, 10, 1)
        days = [mdates.date2num(start + datetime.timedelta(days=offset)) for offset in range(20)]
        ax.plot(days, range(20))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
        ax.set_yticks([0, 10, 20])
        probe = probe_of(fig)

        assert probe["tick_axes"] == [{"x": "date", "y": "number"}]
        assert gate_lines(probe, plot_language="de") == []

    def test_mathtext_reads_as_drawn(self) -> None:
        """Copilot on #12184: `$\\mathdefault{5.30}$` shows a decimal point like `5.30`."""
        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
        ax.plot([0, 1, 2], [0, 1, 2])
        ax.set_xticks([0, 1, 2])
        ax.set_yticks([0.25, 1.5], [r"$\mathdefault{0.25}$", r"$1.50$"])
        ax.text(1, 1, r"$5{,}30$")
        probe = probe_of(fig)
        assert probe["tick_axes"] == [{"x": "number", "y": "fixed"}]
        probe["tick_axes"][0]["y"] = "number"  # as a ScalarFormatter with mathtext would write them

        [line] = gate_lines(probe, plot_language="de")

        # x: 0, 1, 2 (no marks); y: the two mathtext labels; the annotation `$5{,}30$` reads 5,30.
        assert line.startswith("VQ-06 (light): 2 of 6 numeric tick labels use a decimal point")

    def test_without_tick_axes_only_annotations_count(self) -> None:
        labels = [{"kind": "y tick label", "text": "5.30", "axes": 0}, {"kind": "annotation", "text": "4.85"}]

        [line] = gate_lines({"labels": labels}, plot_language="de")

        assert line.startswith("VQ-06 (light): 1 of 1 numeric annotations use a decimal point")

    def test_a_language_without_a_number_format_and_no_language_have_no_gate(self) -> None:
        probe = {"labels": [{"kind": "annotation", "text": "5.30"}]}

        assert _number_format_lines(probe, number_format("Swedish"), "Swedish") == []
        assert gate_lines(probe) == []

    def test_titles_and_legend_entries_are_never_checked(self) -> None:
        labels = [{"kind": "title", "text": "2.5"}, {"kind": "legend text", "text": "1.5"}]

        assert gate_lines({"labels": labels, "tick_axes": []}, plot_language="de") == []

    def test_colorbar_and_3d_tick_labels_count(self) -> None:
        labels = [
            {"kind": "colorbar tick label", "text": "0.25", "axes": 1},
            {"kind": "z tick label", "text": "1.5", "axes": 0},
        ]
        ticks = [{"x": "number", "y": "number", "z": "number"}, {"x": "none", "y": "number"}]

        [line] = gate_lines({"labels": labels, "tick_axes": ticks}, plot_language="de")

        assert line.startswith("VQ-06 (light): 2 of 2 numeric tick labels use a decimal point")

    @pytest.mark.parametrize(
        "probe",
        [
            {"labels": "broken"},
            {"labels": [None, {"kind": "annotation", "text": 5.3}]},
            {"labels": [{"text": "5.30"}]},
            {"labels": [{"kind": "x tick label", "text": "5.30", "axes": True}], "tick_axes": [{"x": "number"}]},
            {"labels": [{"kind": "x tick label", "text": "5.30", "axes": 3}], "tick_axes": [{"x": "number"}]},
            {"labels": [{"kind": "x tick label", "text": "5.30", "axes": 0}], "tick_axes": "broken"},
        ],
    )
    def test_a_tampered_labels_field_yields_no_line(self, probe: Any) -> None:
        assert gate_lines(probe, plot_language="de") == []


class TestNumberFormatTable:
    def test_every_named_language_has_marks_and_words(self) -> None:
        for code, spec in NUMBER_FORMATS.items():
            assert spec.decimal in ".," and spec.decimal != spec.thousands, code
            assert spec.suffixes and all(word for _, word in spec.suffixes), code

    def test_names_and_codes_share_a_format(self) -> None:
        assert number_format("German") is number_format("de") is number_format("Deutsch") is GERMAN
        assert number_format("Klingon") is None

    def test_the_adapter_reads_the_table_and_the_rules(self) -> None:
        instruction = adapter_instruction("matplotlib")

        assert number_format_table() in instruction
        assert "| `de` (German) | `,` | `.` | 10^3: Tsd., 10^6: Mio., 10^9: Mrd. |" in instruction
        assert "**Numbers.**" in instruction and "**Per-mark labels and decorations.**" in instruction

    def test_the_adapter_pattern_writes_every_table_language_and_passes_g12(self) -> None:
        """Gemini on #12184: the old hint (`maketrans(",.", ".,")`, then the thousands mark for "the first `.`") was
        ambiguous for space-grouped languages; the placeholder pattern is exact for every row."""
        assert '.replace(",", "_").replace(".", DECIMAL).replace("_", THOUSANDS)' in adapter_instruction("matplotlib")
        for code, spec in NUMBER_FORMATS.items():
            text = f"{1234567.25:,.2f}".replace(",", "_").replace(".", spec.decimal).replace("_", spec.thousands)

            assert text == f"1{spec.thousands}234{spec.thousands}567{spec.decimal}25", code
            assert not foreign_decimal(f"{0.5:,.2f}".replace(".", spec.decimal), spec), code

    def test_the_adapter_reads_the_narrowed_house_style_rule(self) -> None:
        assert "not those drawn once per bar or point" in adapter_rubric()
