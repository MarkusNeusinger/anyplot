"""Tests for agents/anyplot/code/normalise.py: header, guard, savefig target and canvas rewrites."""

import ast
from pathlib import Path

import pytest

from agents.anyplot.code.normalise import (
    LANDSCAPE,
    SQUARE,
    TOLERANCE,
    effective_dpi,
    figure_size,
    measure_canvas,
    normalise,
    normalise_report,
    plan_dpi,
)
from agents.anyplot.code.regions import find_regions

from .conftest import CATALOGUE, CATALOGUE_FILES, CATALOGUE_NORMALISED, source


THEME_BLOCK = 'import os\n\nimport matplotlib.pyplot as plt\n\nTHEME = os.getenv("ANYPLOT_THEME", "light")\n'


def norm(code: str, library: str = "matplotlib") -> str:
    result = normalise(code, library=library)
    assert normalise(result, library=library) == result, "normalise must be idempotent"
    ast.parse(result)
    return result


def test_catalogue_file_in_miniature() -> None:
    report = normalise_report(CATALOGUE, library="matplotlib")

    assert report.code == CATALOGUE_NORMALISED
    assert report.notes == ()
    assert any("header" in change for change in report.changes)
    assert any("sys.path guard" in change for change in report.changes)
    assert any("bbox_inches" in change for change in report.changes)
    assert measure_canvas(report.code).pixels == LANDSCAPE


@pytest.mark.parametrize("library", ["plotly", "ggplot2", ""])
def test_unsupported_library_raises(library: str) -> None:
    with pytest.raises(ValueError, match="no normaliser"):
        normalise(CATALOGUE, library=library)


def test_syntax_error_is_left_alone_with_a_note() -> None:
    report = normalise_report("def broken(:\n", library="seaborn")

    assert report.code == "def broken(:\n"
    assert report.notes and report.notes[0].startswith("syntax:")


# --- header ------------------------------------------------------------------------------


def test_only_the_catalogue_docstring_goes() -> None:
    other = '"""My own module docstring."""\n\n' + THEME_BLOCK
    assert norm(other) == other


# --- sys.path guard and file paths -------------------------------------------------------


@pytest.mark.parametrize(
    "guard",
    [
        # plain, with a helper and a comment
        """
        import sys

        # Strip this directory from sys.path.
        _here = os.path.dirname(os.path.abspath(__file__))
        sys.path = [p for p in sys.path if os.path.abspath(p) != _here]
        """,
        # pop and slice assignment
        """
        import sys

        sys.path.pop(0)
        sys.path[:] = [p for p in sys.path if p]
        """,
        # aliased sys and os, with del
        """
        import os as _os
        import sys as _sys

        _here = _os.path.dirname(_os.path.abspath(__file__))
        _sys.path = [p for p in _sys.path if _os.path.abspath(p) != _here]
        del _sys, _here
        """,
        # try/except with pathlib
        """
        import pathlib as _pathlib
        import sys as _sys

        try:
            _here = str(_pathlib.Path(__file__).resolve().parent)
            _sys.path = [p for p in _sys.path if p not in ("", _here)]
        except NameError:
            pass
        del _sys, _pathlib
        """,
        # loops and an if
        """
        import sys

        _d = os.path.dirname(os.path.abspath(__file__))
        while _d in sys.path:
            sys.path.remove(_d)
        for path in list(sys.path):
            if "implementations" in path:
                sys.path.remove(path)
        if sys.path and sys.path[0] == "":
            sys.path.pop(0)
        """,
        # a helper bound in a try, sys.modules and os.chdir
        """
        import sys

        try:
            _here = os.path.realpath(os.path.dirname(__file__))
        except NameError:
            _here = os.path.realpath(os.getcwd())
        sys.path = [p for p in sys.path if p and os.path.realpath(p) != _here]
        sys.modules.pop("matplotlib", None)
        os.chdir(_here)
        """,
    ],
)
def test_guard_variants_go_completely(guard: str) -> None:
    code = "import os\n" + source(guard) + "\n" + THEME_BLOCK.removeprefix("import os\n")
    result = norm(code)

    tree = ast.parse(result)
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    imported = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    assert "__file__" not in names
    assert not imported & {"sys", "pathlib"}
    assert "sys.path" not in result and "chdir" not in result
    assert 'THEME = os.getenv("ANYPLOT_THEME", "light")' in result


def test_helper_used_elsewhere_stays() -> None:
    code = source("""
        import os
        import sys

        _here = os.path.dirname(os.path.abspath(__file__))
        sys.path = [p for p in sys.path if p != _here]
        THEME = os.getenv("ANYPLOT_THEME", "light")
        print(_here)
    """)
    result = norm(code)

    assert "sys" not in result.replace("os.path.abspath", "")
    assert "_here = os.path.dirname" in result and "print(_here)" in result


def test_importlib_imports_become_plain_imports() -> None:
    code = source("""
        import importlib
        import os

        plt = importlib.import_module("matplotlib.pyplot")
        np = importlib.import_module("numpy")
        THEME = os.getenv("ANYPLOT_THEME", "light")
    """)
    result = norm(code)

    assert "importlib" not in result
    assert "import matplotlib.pyplot as plt\nimport numpy\n" not in result
    assert "import matplotlib.pyplot as plt\n" in result and "import numpy as np\n" in result


def test_blank_lines_shrink_to_two_where_lines_went() -> None:
    code = "import os\nimport sys\n\n\n# guard\nsys.path.pop(0)\n\n\nimport numpy as np\n"
    assert norm(code) == "import os\n\n\nimport numpy as np\n"


def test_unrelated_sys_use_keeps_the_import() -> None:
    code = "import sys\n\nsys.path.pop(0)\nprint(sys.version)\n"
    result = norm(code)

    assert result == "import sys\n\nprint(sys.version)\n"


@pytest.mark.parametrize(
    ("setup", "target"),
    [
        ("script_dir = os.path.dirname(os.path.abspath(__file__))", 'os.path.join(script_dir, f"plot-{THEME}.png")'),
        ("OUT = pathlib.Path(__file__).parent", 'OUT / f"plot-{THEME}.png"'),
        ("OUT = Path(__file__).parent", 'str(OUT / f"plot-{THEME}.png")'),
        ('output_path = os.path.join(os.path.dirname(__file__), f"plot-{THEME}.png")', "output_path"),
    ],
)
def test_theme_path_targets_become_the_literal(setup: str, target: str) -> None:
    code = source(f"""
        import os
        import pathlib
        from pathlib import Path

        THEME = os.getenv("ANYPLOT_THEME", "light")
        {setup}
        fig.savefig({target}, dpi=400)
    """)
    result = norm(code)

    assert 'fig.savefig(f"plot-{THEME}.png", dpi=400)' in result
    assert "__file__" not in result and "pathlib" not in result and "os.path" not in result
    assert find_regions(result).savefig_calls[0].standard_target


def test_fname_keyword_target_is_rewritten() -> None:
    code = THEME_BLOCK + 'plt.savefig(fname=os.path.join(d, f"plot-{THEME}.png"))\n'
    assert 'plt.savefig(fname=f"plot-{THEME}.png"' in norm(code)


def test_single_theme_target_stays() -> None:
    code = THEME_BLOCK + 'fig, ax = plt.subplots(figsize=(8, 4.5))\nplt.savefig("plot.png", dpi=400)\n'
    assert 'plt.savefig("plot.png", dpi=400)' in norm(code)


def test_path_used_for_something_else_is_not_a_target_rewrite() -> None:
    code = THEME_BLOCK + 'out = os.path.join(d, "other.png")\nplt.savefig(out)\n'
    assert "plt.savefig(out" in norm(code)


# --- canvas ------------------------------------------------------------------------------


def canvas_code(figure: str, save: str) -> str:
    return THEME_BLOCK + f"{figure}\n{save}\n"


@pytest.mark.parametrize(
    ("figure", "save", "expected"),
    [
        (
            "fig, ax = plt.subplots(figsize=(16, 9))",
            'plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight")',
            'plt.savefig(f"plot-{THEME}.png", dpi=200)',
        ),
        (
            "fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)",
            'plt.savefig(f"plot-{THEME}.png", bbox_inches="tight", pad_inches=0.1, facecolor=BG)',
            'plt.savefig(f"plot-{THEME}.png", facecolor=BG, dpi=400)',
        ),
        (
            "fig, ax = plt.subplots(figsize=(12, 12), dpi=100)",
            'plt.savefig(f"plot-{THEME}.png", dpi=300)',
            'plt.savefig(f"plot-{THEME}.png", dpi=200)',
        ),
        (
            "fig = plt.figure(figsize=(16, 16))",
            'plt.savefig(f"plot-{THEME}.png")',
            'plt.savefig(f"plot-{THEME}.png", dpi=150)',
        ),
        (
            "fig = plt.figure(figsize=(7, 7))",
            'plt.savefig(f"plot-{THEME}.png", dpi=300)',
            'plt.savefig(f"plot-{THEME}.png", dpi=342.9)',
        ),
    ],
)
def test_dpi_rescale_hits_the_target(figure: str, save: str, expected: str) -> None:
    result = norm(canvas_code(figure, save))

    assert expected in result
    canvas = measure_canvas(result)
    assert canvas.on_target, canvas.note
    assert canvas.pixels in (LANDSCAPE, SQUARE)


def test_figure_dpi_follows_the_savefig_dpi() -> None:
    result = norm(
        canvas_code("fig, ax = plt.subplots(figsize=(16, 9), dpi=400)", 'plt.savefig(f"plot-{THEME}.png", dpi=300)')
    )
    assert "plt.subplots(figsize=(16, 9), dpi=200)" in result


def test_exact_dpi_literal_is_kept_as_written() -> None:
    code = canvas_code("fig, ax = plt.subplots(figsize=(8, 4.5))", 'plt.savefig(f"plot-{THEME}.png", dpi=400.0)')
    assert norm(code) == code


def test_seaborn_grid_size_and_dpi_setters() -> None:
    code = source("""
        g = sns.relplot(data=df, x="a", y="b", height=4.5, aspect=16 / 9)
        g.figure.set_dpi(300)
        g.figure.set_size_inches(16, 9)
        g.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight")
    """)
    result = norm(THEME_BLOCK + code, library="seaborn")

    assert "g.figure.set_dpi(200)" in result
    assert 'g.savefig(f"plot-{THEME}.png", dpi=200)' in result
    assert measure_canvas(result).on_target


def test_multiline_savefig_keyword_lines_are_cut() -> None:
    code = THEME_BLOCK + source("""
        fig, ax = plt.subplots(figsize=(8, 4.5))
        plt.savefig(
            f"plot-{THEME}.png",
            dpi=400,
            bbox_inches="tight",
            pad_inches=0.05)
    """)
    result = norm(code)

    assert result.endswith('plt.savefig(\n    f"plot-{THEME}.png",\n    dpi=400,\n)\n')


@pytest.mark.parametrize(
    ("figure", "reason"),
    [
        ("fig, ax = plt.subplots(figsize=(16, 12))", "aspect 1.333"),
        ("fig, ax = plt.subplots(figsize=(16, 10))", "aspect 1.600"),
        ("fig, ax = plt.subplots()", "no figsize="),
        ("fig, ax = plt.subplots(figsize=SIZE)", "not a pair of numeric literals"),
        ("fig = plt.figure(figsize=(8, 4.5))\nfig2 = plt.figure(figsize=(6, 6))", "2 different figsize="),
    ],
)
def test_canvas_left_alone_with_a_note(figure: str, reason: str) -> None:
    code = canvas_code(figure, 'plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight")')
    report = normalise_report(code, library="matplotlib")

    assert report.code == code
    assert any(note.startswith("canvas:") and reason in note for note in report.notes), report.notes
    assert not measure_canvas(report.code).on_target


def test_savefig_with_kwargs_is_left_alone() -> None:
    code = canvas_code("fig, ax = plt.subplots(figsize=(16, 9))", 'plt.savefig(f"plot-{THEME}.png", **SAVE)')
    report = normalise_report(code, library="matplotlib")

    assert report.code == code and any("**kwargs" in note for note in report.notes)


# --- dpi planning and measurement ---------------------------------------------------------


@pytest.mark.parametrize(
    ("size", "target", "literal"),
    [
        ((8, 4.5), LANDSCAPE, "400"),
        ((16, 9), LANDSCAPE, "200"),
        ((6.4, 3.6), LANDSCAPE, "500"),
        ((6, 6), SQUARE, "400"),
        ((7, 7), SQUARE, "342.9"),
        ((3, 3), SQUARE, "800"),
        ((16, 9.05), LANDSCAPE, "200"),  # within tolerance: 3200 x 1810
    ],
)
def test_plan_dpi(size: tuple[float, float], target: tuple[int, int], literal: str) -> None:
    plan = plan_dpi(size)

    assert plan == (target, literal)
    width, height = int(size[0] * float(literal)), int(size[1] * float(literal))
    assert abs(width - target[0]) <= TOLERANCE and abs(height - target[1]) <= TOLERANCE


@pytest.mark.parametrize("size", [(16, 12), (16, 10), (4, 8), (0, 9), (-8, 4.5)])
def test_plan_dpi_refuses_unreachable_sizes(size: tuple[float, float]) -> None:
    assert isinstance(plan_dpi(size), str)


def test_measure_canvas_and_effective_dpi() -> None:
    code = canvas_code("fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)", 'plt.savefig(f"plot-{THEME}.png")')
    regions = find_regions(code)
    assert regions.savefig is not None

    assert figure_size(regions)[0] == (8, 4.5)
    assert effective_dpi(regions, regions.savefig) == (400, "figure dpi=")
    assert measure_canvas(code).on_target
    no_dpi = canvas_code("fig, ax = plt.subplots(figsize=(8, 4.5))", 'plt.savefig(f"plot-{THEME}.png")')
    assert measure_canvas(no_dpi).pixels == (800, 450)
    tight = canvas_code(
        "fig, ax = plt.subplots(figsize=(8, 4.5))", 'plt.savefig(f"plot-{THEME}.png", dpi=400, bbox_inches="tight")'
    )
    assert "crops" in (measure_canvas(tight).note or "")


# --- catalogue sweep ------------------------------------------------------------------------


@pytest.mark.skipif(not CATALOGUE_FILES, reason="plots/ is not checked out")
@pytest.mark.parametrize("path", CATALOGUE_FILES, ids=lambda p: f"{p.parts[-4]}-{p.stem}")
def test_catalogue_sweep(path: Path) -> None:
    original = path.read_text(encoding="utf-8")
    result = normalise(original, library=path.stem)

    assert normalise(result, library=path.stem) == result
    regions = find_regions(original)
    size, _ = figure_size(regions)
    call = regions.savefig or (regions.savefig_calls[-1] if regions.savefig_calls else None)
    dpi = effective_dpi(regions, call)[0] if call is not None else None
    if size is not None and dpi is not None and not isinstance(plan_dpi(size), str):
        canvas = measure_canvas(result)
        assert canvas.pixels in (LANDSCAPE, SQUARE), canvas.note
        assert canvas.on_target, canvas.note
