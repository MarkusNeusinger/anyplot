"""Tests for agents/anyplot/code/profiles/r/normalise.py: header, save target, title and canvas."""

import math
import re
from collections import Counter
from fractions import Fraction

import pytest

from agents.anyplot.code.profiles.r.normalise import measure_canvas, normalise, normalise_report, plan_dpi
from agents.anyplot.code.profiles.r.regions import find_regions

from .conftest import R_CATALOGUE, R_CATALOGUE_FILES, R_CATALOGUE_NORMALISED, source


def save(dpi: str = "300", width: str = "16", height: str = "9", units: str = '"in"', extra: str = "") -> str:
    return source(f"""
        THEME <- Sys.getenv("ANYPLOT_THEME", "light")
        ggsave(
          filename = sprintf("plot-%s.png", THEME),
          plot     = p,
          device   = ragg::agg_png,
          width    = {width},
          height   = {height},
          units    = {units},
          dpi      = {dpi}{extra}
        )
    """)


def test_the_catalogue_file_in_miniature() -> None:
    report = normalise_report(R_CATALOGUE)

    assert report.code == R_CATALOGUE_NORMALISED
    assert report.changes == (
        "removed the catalogue header at lines 1-4",
        "emptied the catalogue title at line 23",  # lines count in the code each step reads
        "set the save's dpi from 300 to 200: 16 x 9 in renders 3200x1800",
    )
    assert report.notes == ()


def test_normalising_twice_changes_nothing() -> None:
    assert normalise(R_CATALOGUE_NORMALISED) == R_CATALOGUE_NORMALISED


def test_a_file_without_the_header_keeps_its_first_lines() -> None:
    code = "#' A roxygen comment of the user's\nlibrary(ggplot2)\n"

    assert normalise(code) == code


def test_the_bound_once_save_target_is_inlined() -> None:
    code = source("""
        THEME <- Sys.getenv("ANYPLOT_THEME", "light")
        output_file <- sprintf("plot-%s.png", THEME)
        ggsave(
          filename = output_file,
          plot     = p,
          device   = ragg::agg_png,
          width    = 8,
          height   = 4.5,
          units    = "in",
          dpi      = 400
        )
    """)
    report = normalise_report(code)

    assert "output_file" not in report.code
    assert 'filename = sprintf("plot-%s.png", THEME),' in report.code
    assert report.changes == ("inlined output_file as the save target at line 4 and removed its binding at line 2",)
    regions = find_regions(report.code)
    assert regions.save is not None and regions.save.standard_target


@pytest.mark.parametrize(
    "extra",
    [
        "print(output_file)\n",  # read elsewhere
        'output_file <- "other.png"\n',  # bound twice
        "f <- function(output_file) 1\n",  # a parameter of that name
    ],
)
def test_a_save_target_name_used_otherwise_stays(extra: str) -> None:
    code = (
        'THEME <- Sys.getenv("ANYPLOT_THEME", "light")\n'
        'output_file <- sprintf("plot-%s.png", THEME)\n'
        f"{extra}"
        "ggsave(filename = output_file, plot = p, device = ragg::agg_png, width = 8, height = 4.5, dpi = 400)\n"
    )

    assert "filename = output_file" in normalise(code)


def test_a_binding_that_shares_its_line_stays() -> None:
    code = (
        'THEME <- Sys.getenv("ANYPLOT_THEME", "light")\n'
        'x <- 1; output_file <- sprintf("plot-%s.png", THEME)\n'
        "ggsave(filename = output_file, plot = p, device = ragg::agg_png, width = 8, height = 4.5, dpi = 400)\n"
    )

    assert "filename = output_file" in normalise(code)


@pytest.mark.parametrize(
    ("title", "blank"),
    [
        ('"scatter-basic · r · ggplot2 · anyplot.ai"', True),
        ('"Revenue by Region · bar-grouped · r · ggplot2 · anyplot.ai"', True),
        ("'scatter-basic · r · ggplot2 · anyplot.ai'", True),
        ('r"(scatter-basic · r · ggplot2 · anyplot.ai)"', True),
        ('"Revenue by Region"', False),
        ('"anyplot.ai"', False),
    ],
)
def test_catalogue_titles_become_empty(title: str, blank: bool) -> None:
    code = f"p <- p + labs(title = {title})\n"

    assert normalise(code) == ('p <- p + labs(title = "")\n' if blank else code)


def test_a_split_title_and_a_format_title_get_notes() -> None:
    code = source("""
        a <- paste0("Monthly Trends · line-cycle-seasonal · ", "r · ggplot2 · anyplot.ai")
        b <- sprintf("%d-Day Average · line-rolling · r · ggplot2 · anyplot.ai", 7)
        c <- paste0("Winds · windbarb-basic · r · ggplot2 · anyplot.ai")
    """)
    report = normalise_report(code)

    assert report.code.splitlines() == [
        'a <- paste0("Monthly Trends · line-cycle-seasonal · ", "")',
        'b <- sprintf("", 7)',
        'c <- paste0("")',
    ]
    titles = [note for note in report.notes if note.startswith("title:")]
    assert len(titles) == 2
    assert "split over paste0()" in titles[0]
    assert "sprintf format" in titles[1]


@pytest.mark.parametrize(
    ("size", "target", "literal"),
    [
        ((16, 9), (3200, 1800), "200"),
        ((8, 4.5), (3200, 1800), "400"),
        ((6, 6), (2400, 2400), "400"),
        ((9, 9), (2400, 2400), "266.7"),
        ((12, 12), (2400, 2400), "200"),
        ((7, 7), (2400, 2400), "342.9"),
    ],
)
def test_plan_dpi_hits_the_target_as_ragg_truncates(
    size: tuple[float, float], target: tuple[int, int], literal: str
) -> None:
    """ragg renders floor(inches * dpi) per side (measured in the toolchain image on 2026-10-29)."""
    plan = plan_dpi(size)

    assert plan is not None and plan[:2] == (target, literal) and plan[2]
    for side, pixels in zip(size, target, strict=True):
        assert math.floor(side * float(literal)) == pixels
        assert Fraction(pixels) <= Fraction(side) * Fraction(literal) < pixels + 1


def test_the_measured_truncation() -> None:
    """13.333 in at 240 dpi rendered 3199 px in the toolchain image: the model says so too."""
    canvas = measure_canvas(save(width="13.333", height="7.5", dpi="240"))

    assert canvas.pixels == (3199, 1800) and not canvas.on_target


def test_plan_dpi_lands_within_the_tolerance_for_a_hair_off_aspect() -> None:
    plan = plan_dpi((16.0, 9.05))

    assert plan is not None and plan[0] == (3200, 1800) and not plan[2]


def test_plan_dpi_gives_up_on_an_aspect_no_dpi_reaches() -> None:
    assert plan_dpi((10.0, 4.0)) is None


@pytest.mark.parametrize(
    ("arguments", "dpi"),
    [
        ({"dpi": "300"}, "200"),
        ({"dpi": "200"}, "200"),
        ({"dpi": '"print"'}, "200"),
        ({"width": "40.64", "height": "22.86", "units": '"cm"', "dpi": "300"}, "200"),
    ],
)
def test_only_the_dpi_changes(arguments: dict[str, str], dpi: str) -> None:
    code = save(**arguments)
    result = normalise(code)

    assert result == re.sub(r"dpi      = .*", f"dpi      = {dpi}", code)
    assert measure_canvas(result).on_target


def test_a_save_without_dpi_gets_one() -> None:
    code = (
        'THEME <- Sys.getenv("ANYPLOT_THEME", "light")\n'
        'ggsave(filename = sprintf("plot-%s.png", THEME), plot = p, device = ragg::agg_png, width = 16, height = 9)\n'
    )
    result = normalise(code)

    assert result.endswith("width = 16, height = 9, dpi = 200)\n")
    assert measure_canvas(result).pixels == (3200, 1800)


@pytest.mark.parametrize(
    ("arguments", "note"),
    [
        ({"width": "w"}, "not number literals"),
        ({"units": '"px"', "width": "3200", "height": "1800"}, "in px"),
        ({"width": "10", "height": "4"}, "aspect 2.500"),
        ({"dpi": "my_dpi"}, "dpi (my_dpi) is not a number literal"),
    ],
)
def test_a_canvas_the_normaliser_cannot_set_gets_a_note(arguments: dict[str, str], note: str) -> None:
    code = save(**arguments)
    report = normalise_report(code)

    assert report.code == code
    assert any(note in line for line in report.notes)


def test_measure_canvas_reports_a_canvas_over_the_cap() -> None:
    canvas = measure_canvas(save(width="16", height="9", dpi="400"))

    assert canvas.pixels == (6400, 3600) and canvas.target == (3200, 1800)
    assert canvas.note is not None and "over R2's pixel cap" in canvas.note


def test_measure_canvas_without_a_protected_save() -> None:
    assert measure_canvas("x <- 1\n").note == "no protected ggsave, so the canvas is unknown"


def test_code_with_syntax_problems_is_left_alone() -> None:
    code = "#' anyplot.ai\nx <- (\n"
    report = normalise_report(code)

    assert report.code == code and report.notes[0].startswith("syntax: ")


def test_catalogue_corpus() -> None:
    """All 325 files normalise idempotently onto 3200x1800 (251) or 2400x2400 (74), with these changes (2026-10-29):
    325 headers and 325 titles removed, 34 dpi rewrites, 1 inlined target; 6 title notes (5 split over `paste0`,
    one of them a map spec, and 1 `sprintf` format). For every rewritten save the test computes the PNG itself from
    the save's literals as ragg does, floor(inches * dpi) per side, independent of the normaliser's model."""
    changes: Counter[str] = Counter()
    notes: Counter[str] = Counter()
    canvases: Counter[tuple[int, int] | None] = Counter()
    for path in R_CATALOGUE_FILES:
        report = normalise_report(path.read_text(encoding="utf-8"))
        assert normalise(report.code) == report.code, path
        changes.update(re.sub(r" at .*|: .*| from .*", "", change) for change in report.changes)
        notes.update(note.split(":")[0] for note in report.notes)
        canvas = measure_canvas(report.code)
        assert canvas.on_target, (path, canvas.note)
        canvases[canvas.pixels] += 1
        if any("dpi" in change for change in report.changes):
            saved = find_regions(report.code).save
            assert saved is not None
            width, height, dpi, units = (saved.argument(name) for name in ("width", "height", "dpi", "units"))
            assert width and height and dpi and units and units.text == '"in"', path
            pixels = (math.floor(float(width.text) * float(dpi.text)), math.floor(float(height.text) * float(dpi.text)))
            assert pixels == canvas.target, (path, pixels)

    assert changes == Counter(
        {
            "removed the catalogue header": 325,
            "emptied the catalogue title": 325,
            "set the save's dpi": 34,
            "inlined output_file as the save target": 1,
        }
    )
    assert notes == Counter({"title": 6})
    assert canvases == Counter({(3200, 1800): 251, (2400, 2400): 74})
