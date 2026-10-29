"""Tests for agents/anyplot/code/profiles/julia/normalise.py: Makie catalogue code to the exact canvas."""

import re
from collections import Counter

import pytest

from agents.anyplot.code.profiles.julia.normalise import measure_canvas, normalise, normalise_report, pixels, plan_scale
from agents.anyplot.code.treesitter import Source, syntax_problems

from .conftest import JULIA_CATALOGUE, JULIA_CATALOGUE_FILES, JULIA_CATALOGUE_NORMALISED, source


THEME = 'const THEME = get(ENV, "ANYPLOT_THEME", "light")\n'


def test_the_catalogue_file_in_miniature() -> None:
    report = normalise_report(JULIA_CATALOGUE)

    assert report.code == JULIA_CATALOGUE_NORMALISED
    assert report.changes == (
        "removed the catalogue header at lines 1-4",
        "emptied the catalogue title at line 26",
        "renamed the Figure's deprecated resolution keyword to size at line 25",
    )
    assert report.notes == ()


def test_normalising_twice_changes_nothing() -> None:
    assert normalise(JULIA_CATALOGUE_NORMALISED) == JULIA_CATALOGUE_NORMALISED


def test_only_header_lines_go() -> None:
    code = "# anyplot.ai\n# demo-spec: Demo\n# a comment of the file\nx = 1\n"

    assert normalise(code) == "# a comment of the file\nx = 1\n"
    assert normalise("# a first comment\nx = 1\n") == "# a first comment\nx = 1\n"


def test_a_save_next_to_the_script_saves_in_the_working_directory() -> None:
    code = THEME + 'fig = Figure()\nsave(joinpath(@__DIR__, "plot-$(THEME).png"), fig; px_per_unit = 2)\n'

    assert normalise(code).endswith('\nsave("plot-$(THEME).png", fig; px_per_unit = 2)\n')


@pytest.mark.parametrize(
    "target",
    [
        'joinpath(@__DIR__, "plot.png")',
        'joinpath(dir, "plot-$(THEME).png")',
        'joinpath(@__DIR__, "x", "plot-$(THEME).png")',
    ],
)
def test_other_joined_targets_stay(target: str) -> None:
    code = THEME + f"fig = Figure()\nsave({target}, fig; px_per_unit = 2)\n"

    assert normalise(code) == code


@pytest.mark.parametrize(
    ("title", "blank"),
    [
        ('"scatter-basic · julia · makie · anyplot.ai"', True),
        ('"Height vs weight · scatter-basic · julia · makie · anyplot.ai"', True),
        ('"NovaTech — box \\$2.00 · point-and-figure-basic · julia · makie · anyplot.ai"', True),
        ('"$(name) · scatter-basic · julia · makie · anyplot.ai"', False),
        ('"Height vs weight"', False),
    ],
)
def test_catalogue_titles_become_empty(title: str, blank: bool) -> None:
    code = f"ax = Axis(fig[1, 1]; title = {title})\n"

    assert (normalise(code) == 'ax = Axis(fig[1, 1]; title = "")\n') is blank


def test_resolution_and_size_together_stay_with_a_note() -> None:
    code = "fig = Figure(size = (1600, 900), resolution = (1600, 900))\n"
    report = normalise_report(code)

    assert report.code == code
    assert any("passes size and resolution" in note for note in report.notes)


def test_the_resolution_shorthand_passes_the_same_value_as_size() -> None:
    """`Figure(; resolution)` passes the variable `resolution` (review of 2026-10-29: the rename raised IndexError)."""
    code = f'{THEME}resolution = (1600, 900)\nfig = Figure(; resolution)\nsave("plot-$(THEME).png", fig; px_per_unit = 2)\n'
    report = normalise_report(code)

    assert "fig = Figure(; size = resolution)\n" in report.code
    assert report.changes == ("renamed the Figure's deprecated resolution keyword to size at line 3",)
    assert normalise(report.code) == report.code
    assert measure_canvas(report.code).note == "the Figure's size (resolution) is not a tuple of two number literals"


@pytest.mark.parametrize(
    "body",
    [
        "fig = Figure(; resolution)",
        "fig = Figure(resolution...)",
        "fig = Figure(; kw...)",
        "fig = Figure(; resolution = r, size)",
        "fig = Figure(size = (0.4, 0.3))",
        "fig = Figure(size = (1e400, 900))",
        "fig = Figure(size = (1e300, 1e300))",
        "fig = Figure(size = (-1600, 900))",
        "fig = Figure(size = (1600, 900)); fig2 = Figure(; resolution)",
        "fig = Figure(size = (1600, 900))\nsave(joinpath(@__DIR__), fig)",
        'fig = Figure(size = (1600, 900))\nsave(joinpath(@__DIR__(), "plot-$(THEME).png"), fig)',
        "fig = Figure(size = (1600, 900))\ns = save",
        "fig = Figure(Figure()...)",
        'ax = Axis(fig[1, 1]; title = """scatter-basic · julia · makie · anyplot.ai""")',
        # integer literals past a double, past Python's 4,300 digits, BigInt strings, hex and underscores
        f"fig = Figure(size = ({'9' * 400}, 900))",
        f"fig = Figure(size = (1600, {'1' * 5000}))",
        "fig = Figure(size = (1e308, 1e308))",
        "fig = Figure(size = (0x1p1100, 900))",
        'fig = Figure(size = (big"1600", 900))',
        "fig = Figure(size = (0x640, 0x384))",
        "fig = Figure(size = (1_600, 9_00))",
        "fig = Figure(size = (0b11001000000, 900))",
    ],
)
@pytest.mark.parametrize(
    "save",
    [
        'save("plot-$(THEME).png", fig; px_per_unit = 2)',
        'save("plot-$(THEME).png", fig; px_per_unit)',
        'save("plot-$(THEME).png", fig; px_per_unit = 1e400)',
        'save("plot-$(THEME).png", fig; px_per_unit = 0)',
        'save("plot-$(THEME).png", fig; px_per_unit = -2)',
        f'save("plot-$(THEME).png", fig; px_per_unit = {"7" * 400})',
        'save("plot-$(THEME).png", fig; px_per_unit = 1e300)',
        'save("plot-$(THEME).png", fig; px_per_unit = big"2")',
        'save("plot-$(THEME).png", fig; px_per_unit = 0x2)',
        'save("plot-$(THEME).png"; px_per_unit = 2)',
        "save()",
    ],
)
def test_the_normaliser_never_raises_on_valid_julia(body: str, save: str) -> None:
    """A normaliser must never raise on code that parses: odd but valid shapes leave notes, never exceptions."""
    code = f"{THEME}{body}\n{save}\n"
    assert syntax_problems(Source(code, "julia").tree) == []
    report = normalise_report(code)

    assert normalise(report.code) == report.code
    measure_canvas(report.code)


def test_hex_and_underscored_sizes_read_as_their_value() -> None:
    """`0x640` and `1_600` are 1600 to Julia, so the canvas measures 3200x1800; a literal past a double is no number."""
    for size in ("(0x640, 0x384)", "(1_600, 9_00)"):
        code = f'{THEME}fig = Figure(size = {size})\nsave("plot-$(THEME).png", fig; px_per_unit = 2)\n'
        assert measure_canvas(code).pixels == (3200, 1800)
    huge = f'{THEME}fig = Figure(size = ({"9" * 400}, 900))\nsave("plot-$(THEME).png", fig; px_per_unit = 2)\n'
    assert measure_canvas(huge).note is not None and len(measure_canvas(huge).note or "") < 200


@pytest.mark.parametrize(
    ("size", "target", "scale", "exact"),
    [
        ((1600, 900), (3200, 1800), "2", True),
        ((800, 450), (3200, 1800), "4", True),
        ((1200, 1200), (2400, 2400), "2", True),
        ((1000, 562.5), (3200, 1800), "3.2", False),
        ((1067, 600), (3200, 1800), "2.9992", True),
        ((900, 900), (2400, 2400), "2.667", True),
    ],
)
def test_plan_scale_hits_the_target_as_cairomakie_rounds(
    size: tuple[float, float], target: tuple[int, int], scale: str, exact: bool
) -> None:
    plan = plan_scale(size)

    assert plan == (target, scale, exact)
    assert exact is (pixels(size, float(scale)) == target)


def test_the_measured_rounding() -> None:
    """CairoMakie 0.15.16 in the J1 image, 2026-10-29: the size rounds to whole units, then size * px_per_unit to
    whole pixels."""
    assert pixels((1600, 900), 1.9999) == (3200, 1800)
    assert pixels((1600, 900), 2.0004) == (3201, 1800)
    assert pixels((1066.6667, 600), 3) == (3201, 1800)
    assert pixels((1000, 562.5), 3.2) == (3200, 1798)
    assert pixels((1600.75, 900), 2) == (3202, 1800)
    assert pixels((1600.25, 900), 2) == (3200, 1800)


def test_plan_scale_gives_up_on_an_aspect_no_scale_reaches() -> None:
    assert plan_scale((1600, 1100)) is None


@pytest.mark.parametrize(
    ("figure", "save", "expected"),
    [
        ("Figure(size = (800, 450))", 'save("plot-$(THEME).png", fig; px_per_unit = 2)', "px_per_unit = 4)"),
        ("Figure(size = (800, 450))", 'save("plot-$(THEME).png", fig)', "fig; px_per_unit = 4)"),
        ("Figure(resolution = (1600, 900))", 'save("plot-$(THEME).png", fig; px_per_unit = 3)', "px_per_unit = 2)"),
    ],
)
def test_only_px_per_unit_changes(figure: str, save: str, expected: str) -> None:
    code = f"{THEME}fig = {figure}\n{save}\n"
    normalised = normalise(code)

    assert normalised.endswith(expected + "\n")
    assert "(800, 450)" in normalised or "(1600, 900)" in normalised
    assert measure_canvas(normalised).note is None


@pytest.mark.parametrize(
    ("body", "note"),
    [
        ("fig = Figure(size = (w, h))", "is not a tuple of two number literals"),
        ("fig = Figure(size = (1600, 900))\nresize_to_layout!(fig)", "resize_to_layout! can size the figure"),
        ("fig = Figure(size = (1600, 900))\nother = Figure()", "creates 2 figures"),
        ("set_theme!(size = (800, 600))\nfig = Figure()", "set_theme! can size the figure"),
        ("fig = Figure(size = (1600, 1100))", "no px_per_unit renders"),
    ],
)
def test_a_canvas_the_normaliser_cannot_set_gets_a_note(body: str, note: str) -> None:
    code = f'{THEME}{body}\nsave("plot-$(THEME).png", fig; px_per_unit = 2)\n'
    report = normalise_report(code)

    assert report.code == code
    assert any(note in text for text in report.notes), report.notes


def test_a_figure_without_size_takes_makies_default() -> None:
    """`Figure()` is 600x450 in Makie 0.24 (measured: 1200x900 at px_per_unit 2): 4:3, which no scale brings on a
    target, so the save stays with a note."""
    code = f'{THEME}fig = Figure()\nsave("plot-$(THEME).png", fig; px_per_unit = 2)\n'
    report = normalise_report(code)

    assert measure_canvas(code).pixels == (1200, 900)
    assert report.code == code
    assert any("no px_per_unit renders" in note for note in report.notes)


def test_measure_canvas_reports_a_canvas_over_the_cap() -> None:
    code = f'{THEME}fig = Figure(size = (1600, 900))\nsave("plot-$(THEME).png", fig; px_per_unit = 4)\n'
    canvas = measure_canvas(code)

    assert canvas.pixels == (6400, 3600)
    assert canvas.note == "the save renders 6400x3600 (over R2's pixel cap), not 3200x1800"


def test_measure_canvas_without_a_protected_save() -> None:
    assert measure_canvas("x = 1\n").note == "no protected save, so the canvas is unknown"


def test_code_with_syntax_problems_is_left_alone() -> None:
    code = "# anyplot.ai\nx = (1 +\n"
    report = normalise_report(code)

    assert report.code == code
    assert report.notes[0].startswith("syntax: ")


def test_catalogue_corpus() -> None:
    """All 325 files: idempotent, parse after normalising, one title each, and the canvas as J1's sweep rendered it."""
    changes: Counter[str] = Counter()
    canvases: Counter[tuple[int, int] | None] = Counter()
    notes: Counter[str] = Counter()
    for path in JULIA_CATALOGUE_FILES:
        report = normalise_report(path.read_text(encoding="utf-8"))
        assert normalise(report.code) == report.code, path
        assert syntax_problems(Source(report.code, "julia").tree) == [], path
        changes.update(re.sub(r"\d+", "N", change) for change in report.changes)
        notes.update(
            note.split(":", 1)[0] + ": " + note.rsplit(";", 1)[0].split(": ", 1)[-1][:20] for note in report.notes
        )
        canvases[measure_canvas(report.code).pixels] += 1

    assert changes == {
        "removed the catalogue header at lines N-N": 325,
        "emptied the catalogue title at line N": 325,
        "renamed the Figure's deprecated resolution keyword to size at line N": 122,
        'saved "plot-$(THEME).png" in the working directory instead of next to the script at line N': 4,
    }
    assert canvases == {(3200, 1800): 250, (2400, 2400): 69, None: 6}
    assert sum(notes.values()) == 6


def test_the_normalised_title_is_the_only_title() -> None:
    code = source("""
        ax = Axis(fig[1, 1]; title = "scatter-basic · julia · makie · anyplot.ai", xlabel = "x · y")
    """)

    assert normalise(code) == 'ax = Axis(fig[1, 1]; title = "", xlabel = "x · y")\n'
