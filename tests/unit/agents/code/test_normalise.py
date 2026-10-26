"""Tests for agents/anyplot/code/normalise.py: header, guards, save target, pygal and lets-plot rewrites, canvas."""

import ast
from pathlib import Path

import pytest

from agents.anyplot.code.normalise import (
    LANDSCAPE,
    MAX_IMAGE_PIXELS,
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
    assert "emptied the catalogue title at line 21" in report.changes
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


# --- the other Python libraries ----------------------------------------------------------


PLOTNINE_CATALOGUE = source('''
    """ anyplot.ai
    scatter-demo: Demo Scatter
    Library: plotnine 0.15.7 | Python 3.13.13
    Quality: 90/100 | Updated: 2026-10-01
    """

    import os
    import sys

    import pandas as pd
    from plotnine import aes, geom_point, ggplot, labs

    # This file is named plotnine.py; drop its directory from sys.path.
    _here = os.path.dirname(os.path.abspath(__file__))
    sys.path = [p for p in sys.path if os.path.abspath(p) != _here]

    THEME = os.getenv("ANYPLOT_THEME", "light")
    PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
    df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
    title = "scatter-demo · python · plotnine · anyplot.ai"
    plot = ggplot(df, aes(x="x", y="y")) + geom_point(color=PAGE_BG) + labs(title=title)
    plot.save(os.path.join(_here, f"plot-{THEME}.png"), dpi=400, width=8, height=4.5, units="in", verbose=False)
''')


def test_plotnine_file_is_normalised_without_a_canvas_rewrite() -> None:
    report = normalise_report(PLOTNINE_CATALOGUE, library="plotnine")

    assert report.code.startswith("import os\n")
    assert 'plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)' in report.code
    assert 'title = ""' in report.code and "sys.path" not in report.code and "_here" not in report.code
    assert any(change.startswith("save target os.path.join(_here, ") for change in report.changes)
    assert report.notes == (
        "canvas: plotnine sizes its canvas on the save, not through a matplotlib figure; nothing to rewrite",
    )
    assert norm(PLOTNINE_CATALOGUE, "plotnine") == report.code
    canvas = measure_canvas(report.code, library="plotnine")
    assert canvas.pixels is None and not canvas.on_target
    assert canvas.note == "plotnine sizes its canvas on the save, not through a matplotlib figure"


def test_altair_rewrites_the_png_and_the_html_target() -> None:
    code = source("""
        import os

        import altair as alt

        THEME = os.getenv("ANYPLOT_THEME", "light")
        out = os.path.dirname(os.path.abspath(__file__))
        chart = alt.Chart().mark_point()
        chart.save(os.path.join(out, f"plot-{THEME}.png"), scale_factor=4.0)
        chart.save(os.path.join(out, f"plot-{THEME}.html"))
    """)

    report = normalise_report(code, library="altair")

    assert 'chart.save(f"plot-{THEME}.png", scale_factor=4.0)\nchart.save(f"plot-{THEME}.html")\n' in report.code
    assert "os.path.dirname" not in report.code  # `out` only served the targets, so the guard step dropped it
    assert [change.split(" at ")[0] for change in report.changes if change.startswith("save target")] == [
        'save target os.path.join(out, f"plot-{THEME}.png") -> f"plot-{THEME}.png"',
        'save target os.path.join(out, f"plot-{THEME}.html") -> f"plot-{THEME}.html"',
    ]
    # Read with matplotlib's rule the `.save` calls are no save calls: the targets stay as they are.
    assert "os.path.join(out," in normalise(code, library="matplotlib")


# --- header ------------------------------------------------------------------------------


def test_only_the_catalogue_docstring_goes() -> None:
    other = '"""My own module docstring."""\n\n' + THEME_BLOCK
    assert norm(other) == other


def test_a_second_catalogue_header_goes_too() -> None:
    """lets-plot's indicator-bollinger, parliament-basic and probability-weibull open with two headers."""
    header = '""" anyplot.ai\nscatter-demo: Demo Scatter\nLibrary: letsplot 4.9.0\nQuality: 92/100\n"""\n'
    code = header + "# ruff: noqa: F405\n" + header.replace(" anyplot.ai", "anyplot.ai") + "\n" + THEME_BLOCK
    report = normalise_report(code, library="matplotlib")

    assert report.code == "# ruff: noqa: F405\n\n" + THEME_BLOCK
    assert report.changes[:2] == (
        "removed the catalogue header at lines 1-5",
        "removed the catalogue header at lines 7-11",
    )
    assert norm(code) == report.code


# --- title ---------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "line",
    [
        'ax.set_title("scatter-basic · python · matplotlib · anyplot.ai", fontsize=24)',
        'ax.set_title("Website Traffic · area-basic · python · matplotlib · anyplot.ai")',
        'ax.set_title("density-rug · Python · seaborn · anyplot.ai")',
        'ax.set_title("candlestick-volume · matplotlib · anyplot.ai", pad=15)',
        'ax.set_title("line-markers · matplotlib · pyplots.ai")',
        'ax.set_title("Remote Work Survey  ·  dot-matrix-proportional  ·  matplotlib  ·  anyplot.ai")',
        'ax.set_title("Sediment Composition\\nternary-density · python · matplotlib · anyplot.ai")',
        'title = "bar-basic · python · matplotlib · anyplot.ai"',
        'fig.suptitle(\n    "donut-nested · python · matplotlib · anyplot.ai",\n    y=0.965,\n)',
    ],
)
def test_catalogue_title_becomes_empty(line: str) -> None:
    result = norm(THEME_BLOCK + line + "\n")

    assert "anyplot.ai" not in result and "pyplots.ai" not in result
    assert '""' in result


@pytest.mark.parametrize(
    "line",
    [
        'ax.set_title("Monthly revenue by region")',
        'ax.set_title(f"{SPEC} · python · matplotlib · anyplot.ai")',
        'ax.set_title("Survey results\\nsource: anyplot.ai")',
        'headers = {"User-Agent": "anyplot.ai/1.0"}',
    ],
)
def test_other_titles_and_strings_stay(line: str) -> None:
    code = THEME_BLOCK + line + "\n"
    assert norm(code) == code


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


@pytest.mark.parametrize(
    ("setup", "save", "expected"),
    [
        # lets-plot's shap-summary
        (
            "_plot_dir = os.path.dirname(os.path.abspath(__file__))",
            'ggsave(plot, f"{_plot_dir}/plot-{THEME}.png", scale=3)',
            'ggsave(plot, f"plot-{THEME}.png", scale=3)',
        ),
        # plotnine's candlestick-volume
        (
            'script_dir = __file__[: __file__.rfind("/")]',
            'ggsave(plot, f"{script_dir}/plot-{THEME}.png", dpi=300)',
            'ggsave(plot, f"plot-{THEME}.png", dpi=300)',
        ),
    ],
)
def test_a_formatted_directory_in_front_of_the_theme_file_is_a_target_rewrite(
    setup: str, save: str, expected: str
) -> None:
    code = source(f"""
        import os

        from plotnine import ggsave

        THEME = os.getenv("ANYPLOT_THEME", "light")
        {setup}
        {save}
    """)
    result = norm(code, "plotnine")

    assert expected in result and "__file__" not in result
    # Only a formatted directory: a literal one stays, as does a file name other than the theme's.
    for other in ('f"out/plot-{THEME}.png"', 'f"{d}/plot-{THEME}-raw.png"'):
        kept = THEME_BLOCK + f"plt.savefig({other})\n"
        assert other in norm(kept)


# --- guards of every library --------------------------------------------------------------


def test_find_spec_guard_becomes_its_imports() -> None:
    """pygal's waveform-audio and nine more files; the rule applies to every library."""
    code = source("""
        import importlib.util
        import os
        import sys

        import numpy as np


        # Prevent this file (pygal.py) from shadowing the installed pygal package
        _pygal_spec = importlib.util.find_spec("pygal")
        if _pygal_spec and _pygal_spec.origin != __file__:
            import pygal
            from pygal.style import Style
        else:
            _cwd = sys.path.pop(0)
            import pygal
            from pygal.style import Style

            sys.path.insert(0, _cwd)

        THEME = os.getenv("ANYPLOT_THEME", "light")
    """)
    expected = source("""
        import os

        import numpy as np


        import pygal
        from pygal.style import Style

        THEME = os.getenv("ANYPLOT_THEME", "light")
    """)

    for library in ("pygal", "matplotlib"):
        report = normalise_report(code, library=library)
        assert report.code == expected, library
        assert report.changes[:2] == (
            "replaced the find_spec guard at lines 10-18 with its imports",
            "removed the unused find_spec result _pygal_spec at line 9",
        )


@pytest.mark.parametrize(
    ("guard", "note"),
    [
        # altair's indicator-macd: the branch loads the module by hand, and the test is another one
        (
            """
            spec = importlib.util.find_spec("altair")
            if spec and spec.origin and "site-packages" in spec.origin:
                alt = importlib.util.module_from_spec(spec)
            else:
                import altair as alt
            """,
            None,
        ),
        (
            """
            spec = importlib.util.find_spec("pygal")
            if spec and spec.origin != __file__:
                import pygal
                print(pygal)
            """,
            "find_spec guard: the if at lines 5-7 holds more than imports; left in place",
        ),
    ],
)
def test_other_find_spec_shapes_stay(guard: str, note: str | None) -> None:
    code = "import importlib.util\nimport os\n\n" + source(guard) + '\nTHEME = os.getenv("ANYPLOT_THEME", "light")\n'
    report = normalise_report(code, library="pygal")

    assert "find_spec" in report.code and "if spec" in report.code
    assert (note in report.notes) if note else not any(n.startswith("find_spec") for n in report.notes)


def test_try_finally_guard_becomes_its_imports() -> None:
    """altair's voronoi-basic: the snapshot, the filter and the try/finally all serve the guard."""
    code = source("""
        import os
        import sys


        # Remove current directory from path to avoid shadowing altair library
        _current_dir = os.path.dirname(os.path.abspath(__file__))
        _sys_path_backup = sys.path.copy()
        sys.path = [p for p in sys.path if os.path.abspath(p) != _current_dir]

        try:
            import altair as alt
        finally:
            sys.path = _sys_path_backup

        THEME = os.getenv("ANYPLOT_THEME", "light")
    """)
    report = normalise_report(code, library="altair")

    assert report.code == 'import os\n\n\nimport altair as alt\n\nTHEME = os.getenv("ANYPLOT_THEME", "light")\n'
    assert report.changes[0] == "replaced the try/finally sys.path guard at lines 10-13 with its imports"
    assert "removed an unused sys.path snapshot at line 7" in report.changes
    # A try with an `except`, or a finally that does more, is no guard.
    other = code.replace("finally:\n    sys.path = _sys_path_backup", "except ImportError:\n    alt = None")
    assert "try:" in normalise(other, library="altair")


def test_sys_modules_deletion_and_bytecode_flag_are_guard_statements() -> None:
    """pygal's indicator-rsi: `del sys.modules[...]` in an if, then a try/finally guard."""
    code = source("""
        import os
        import sys

        import numpy as np


        # Clear the local module from sys.modules if it was somehow loaded
        if "pygal" in sys.modules and "implementations" in sys.modules["pygal"].__file__:
            del sys.modules["pygal"]

        # Remove current directory from path to prevent local file from being imported
        _original_path = sys.path[:]
        sys.path = [p for p in sys.path if p not in ("", ".", os.getcwd())]
        sys.dont_write_bytecode = True

        try:
            import pygal
            from pygal.style import Style
        finally:
            # Restore path
            sys.path = _original_path

        # Theme tokens
        THEME = os.getenv("ANYPLOT_THEME", "light")
    """)
    expected = source("""
        import os

        import numpy as np


        import pygal
        from pygal.style import Style

        # Theme tokens
        THEME = os.getenv("ANYPLOT_THEME", "light")
    """)

    assert norm(code, "pygal") == expected


def test_unused_sys_path_snapshot_goes_and_a_used_one_stays() -> None:
    """pygal's ohlc-bar keeps `_cwd = sys.path[0] if ...` that nothing reads."""
    snapshot = '_cwd = sys.path[0] if sys.path and sys.path[0] == "" or sys.path[0] == "." else None\n'
    code = "import os\nimport sys\n\n" + snapshot + "sys.path.pop(0)\n\n" + THEME_BLOCK.removeprefix("import os\n")
    result = norm(code)

    assert "sys" not in result.replace("os.getenv", "")
    used = code + "print(_cwd)\n"
    assert snapshot in norm(used)


@pytest.mark.parametrize(
    ("line", "statement"),
    [
        ('Style = importlib.import_module("pygal.style").Style', "from pygal.style import Style"),
        ('_Style = importlib.import_module("pygal.style").Style', "from pygal.style import Style as _Style"),
        ('pygal = importlib.import_module("pygal")', "import pygal"),
        ('mpatches = importlib.import_module("matplotlib.patches")', "import matplotlib.patches as mpatches"),
    ],
)
def test_import_module_attribute_becomes_a_from_import(line: str, statement: str) -> None:
    code = f"import importlib\nimport os\n\n{line}\n\n" + THEME_BLOCK.removeprefix("import os\n")
    report = normalise_report(code, library="pygal")

    assert f"\n{statement}\n" in report.code and "importlib" not in report.code
    assert any(change.endswith(f"-> {statement} at line 4") for change in report.changes)


def test_import_module_imported_from_importlib() -> None:
    """plotnine's bar-horizontal: `from importlib import import_module`, then `pn = import_module("plotnine")`."""
    code = source("""
        import os
        import sys
        from importlib import import_module


        remove_paths = {os.path.dirname(os.path.abspath(__file__)), os.getcwd()}
        sys.path[:] = [p for p in sys.path if os.path.abspath(p) not in remove_paths]

        import pandas as pd


        pn = import_module("plotnine")
        Style = import_module("pygal.style").Style
        aes = pn.aes

        THEME = os.getenv("ANYPLOT_THEME", "light")
    """)
    result = norm(code, "plotnine")

    assert "import plotnine as pn\nfrom pygal.style import Style\naes = pn.aes\n" in result
    assert "import_module" not in result and "sys" not in result


# --- pygal -----------------------------------------------------------------------------------


PYGAL_HEAD = source("""
    import os

    import numpy as np
    import pygal
    from pygal.style import Style

    THEME = os.getenv("ANYPLOT_THEME", "light")
    PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
""")


def pygal_code(body: str) -> str:
    return PYGAL_HEAD + source(body)


@pytest.mark.parametrize(
    "write",
    [
        'with open(f"plot-{THEME}.html", "wb") as f:\n    f.write(chart.render())',
        'with open(f"plot-{THEME}.html", "w") as f:\n    f.write(chart.render(is_unicode=True))',
        'with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:\n    f.write(chart.render().decode())',
        'with open(os.path.join(out, f"plot-{THEME}.html"), "wb") as f:\n    f.write(chart.render())',
    ],
)
def test_pygal_html_write_becomes_render_to_file(write: str) -> None:
    """158 catalogue files write `chart.render()` through `open()`; `render_to_file` writes the same bytes."""
    body = "out = os.path.dirname(os.path.abspath(__file__))\nchart = pygal.XY(width=3200, height=1800)\n"
    code = PYGAL_HEAD + body + 'chart.render_to_png(f"plot-{THEME}.png")\n' + write + "\n"
    report = normalise_report(code, library="pygal")

    assert report.code.endswith(
        'chart.render_to_png(f"plot-{THEME}.png")\nchart.render_to_file(f"plot-{THEME}.html")\n'
    )
    assert "open(" not in report.code and "__file__" not in report.code
    assert report.changes[0].startswith("the HTML write through open() at lines 12-13 -> chart.render_to_file(")
    assert norm(code, "pygal") == report.code


def test_pygal_other_html_and_svg_writes_go_with_what_fed_them() -> None:
    """contour-filled: an SVG file and a hand-built HTML page around the post-processed SVG."""
    code = pygal_code('''
        chart = pygal.XY(width=3200, height=1800)
        base_svg = chart.render(is_unicode=True)

        # Insert custom contour SVG before the closing </svg> tag
        output_svg = base_svg.replace("</svg>", "<g/>\\n</svg>")

        with open(f"plot-{THEME}.svg", "w", encoding="utf-8") as f:
            f.write(output_svg)

        # Convert to PNG using cairosvg
        cairosvg.svg2png(bytestring=output_svg.encode("utf-8"), write_to=f"plot-{THEME}.png")

        # Save HTML
        html_content = f"""<!DOCTYPE html>
        <html><body>{output_svg}</body></html>"""

        with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
            f.write(html_content)
    ''')
    report = normalise_report(code, library="pygal")

    assert report.code.endswith(
        '\n\n# Convert to PNG using cairosvg\ncairosvg.svg2png(bytestring=output_svg.encode("utf-8"), '
        'write_to=f"plot-{THEME}.png")\n'
    )
    assert "open(" not in report.code and "html_content" not in report.code and '.svg"' not in report.code
    assert "output_svg = base_svg.replace(" in report.code  # it also feeds the PNG
    assert report.changes[:3] == (
        "removed the SVG write through open() at lines 15-16",
        "removed the HTML write through open() at lines 25-26",
        "removed html_content, which only fed a removed write, at lines 22-23",
    )


def test_pygal_svg_save_goes() -> None:
    """network-basic and nine more files also save the theme SVG, which the plot sandbox refuses."""
    code = pygal_code("""
        chart = pygal.XY(width=3200, height=1800)
        chart.render_to_png(f"plot-{THEME}.png")
        # The SVG for the web
        chart.render_to_file(f"plot-{THEME}.svg")
    """)
    report = normalise_report(code, library="pygal")

    assert report.code.endswith('chart.render_to_png(f"plot-{THEME}.png")\n')
    assert report.changes == ("removed the SVG save at line 12",)


def test_pygal_write_whose_target_is_read_again_stays() -> None:
    """network-hierarchical renders the SVG file and converts it with `svg2png(url=...)`."""
    code = pygal_code("""
        chart = pygal.XY(width=3200, height=1800)
        chart.render_to_file(f"plot-{THEME}.svg")
        with open(f"plot-{THEME}.svg", "w") as f:
            f.write(chart.render(is_unicode=True))
        cairosvg.svg2png(url=f"plot-{THEME}.svg", write_to=f"plot-{THEME}.png")
    """)
    report = normalise_report(code, library="pygal")

    assert report.code == code
    assert "html: the SVG save at line 10 is read again elsewhere; left in place" in report.notes
    assert "html: the SVG write through open() at lines 11-12 is read again elsewhere; left in place" in report.notes


def test_pygal_feeder_with_a_save_call_stays() -> None:
    code = pygal_code("""
        chart = pygal.XY(width=3200, height=1800)
        png = chart.render_to_png()
        with open(f"plot-{THEME}.html", "w") as f:
            f.write(f"<img src='{png}'>")
        chart.render_to_png(f"plot-{THEME}.png")
    """)
    result = norm(code, "pygal")

    assert "png = chart.render_to_png()" in result and "open(" not in result


def test_pygal_html_page_that_assigns_inside_its_block_goes() -> None:
    """heatmap-basic renders the chart into a name inside the `with` and writes a page around it."""
    code = pygal_code("""
        chart = pygal.XY(width=3200, height=1800)
        chart.render_to_png(f"plot-{THEME}.png")
        with open(f"plot-{THEME}.html", "w", encoding="utf-8") as fout:
            pygal_svg = chart.render(is_unicode=True)
            fout.write(f"<html><body>{pygal_svg}</body></html>")
    """)
    report = normalise_report(code, library="pygal")

    assert report.code.endswith('chart.render_to_png(f"plot-{THEME}.png")\n')
    assert report.changes == ("removed the HTML write through open() at lines 11-13",)
    assert norm(code, "pygal") == report.code


@pytest.mark.parametrize(
    "block",
    [
        # the name is read after the block
        'with open(f"plot-{THEME}.html", "w") as f:\n    page = "<html/>"\n    f.write(page)\nprint(page)',
        # the assignment holds a save call
        'with open(f"plot-{THEME}.html", "w") as f:\n    png = chart.render_to_png()\n    f.write(str(png))',
        # a tuple target, and a statement that is neither a write nor an assignment
        'with open(f"plot-{THEME}.html", "w") as f:\n    a, b = "<", ">"\n    f.write(a + b)',
        'with open(f"plot-{THEME}.html", "w") as f:\n    print("page")\n    f.write("<html/>")',
        # nothing written
        'with open(f"plot-{THEME}.html", "w") as f:\n    page = "<html/>"',
    ],
)
def test_pygal_html_block_that_does_more_stays(block: str) -> None:
    code = pygal_code('chart = pygal.XY(width=3200, height=1800)\nchart.render_to_png(f"plot-{THEME}.png")\n') + (
        block + "\n"
    )
    assert norm(code, "pygal") == code


def test_pygal_html_step_repeats_once_a_removed_feeder_frees_a_target() -> None:
    """A hand-built page's target is named again in a feeder of the SVG write; once that goes, the page goes too."""
    code = pygal_code("""
        chart = pygal.XY(width=3200, height=1800)
        chart.render_to_png(f"plot-{THEME}.png")
        link = f"plot-{THEME}.html"
        with open(f"plot-{THEME}.svg", "w") as f:
            f.write(link)
        with open(f"plot-{THEME}.html", "w") as f:
            f.write("<html/>")
    """)
    report = normalise_report(code, library="pygal")

    assert report.code.endswith('chart.render_to_png(f"plot-{THEME}.png")\n')
    assert report.changes == (
        "removed the SVG write through open() at lines 12-13",
        "removed link, which only fed a removed write, at line 11",
        "removed the HTML write through open() at lines 11-12",
    )
    assert report.notes == ()  # the first pass's "named again" note is gone with the name


def test_html_writes_stay_for_the_other_libraries() -> None:
    code = THEME_BLOCK + 'with open(f"plot-{THEME}.html", "w") as f:\n    f.write(chart.render(is_unicode=True))\n'
    assert norm(code) == code


def test_pygal_html_open_writes_the_same_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The rewrite's claim, for the three write forms: pygal's `render_to_file` writes what `open()` wrote."""
    pytest.importorskip("pygal")
    import pygal.graph.base

    monkeypatch.setattr(pygal.graph.base, "uuid4", lambda: "00000000-0000-0000-0000-000000000000")
    monkeypatch.setenv("ANYPLOT_THEME", "light")
    chart = "chart = pygal.Bar(width=320, height=180, js=[])\nchart.add('a', [1, 3, 2])\n"
    for number, write in enumerate(
        [
            'with open(f"plot-{THEME}.html", "wb") as f:\n    f.write(chart.render())',
            'with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:\n    f.write(chart.render(is_unicode=True))',
            'with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:\n    f.write(chart.render().decode("utf-8"))',
        ]
    ):
        original = 'import os\n\nimport pygal\n\nTHEME = os.getenv("ANYPLOT_THEME", "light")\n' + chart + write + "\n"
        normalised = normalise(original, library="pygal")
        assert "render_to_file" in normalised
        written = []
        for form, code in (("original", original), ("normalised", normalised)):
            directory = tmp_path / f"{number}-{form}"
            directory.mkdir()
            monkeypatch.chdir(directory)
            exec(compile(code, "plot.py", "exec"), {"__name__": "__main__"})
            written.append((directory / "plot-light.html").read_bytes())
        assert written[0] == written[1], write


@pytest.mark.parametrize(
    ("chart", "size", "target"),
    [
        ("pygal.StackedLine(width=4800, height=2700, js=[])", "4800x2700", LANDSCAPE),
        ("pygal.Pie(width=3600, height=3600)", "3600x3600", SQUARE),
    ],
)
def test_pygal_large_chart_renders_the_canvas_through_svg2png(chart: str, size: str, target: tuple[int, int]) -> None:
    """98 catalogue charts are 4800x2700 and 4 are 3600x3600; the layout stays, the PNG gets the canvas size."""
    code = pygal_code(f"""
        chart = {chart}
        chart.add("a", [1, 2, 3])
        chart.render_to_png(f"plot-{{THEME}}.png")
    """)
    report = normalise_report(code, library="pygal")

    width, height = target
    assert report.code.startswith("import os\n\nimport cairosvg\nimport numpy as np\nimport pygal\n")
    assert report.code.endswith(
        f'cairosvg.svg2png(bytestring=chart.render(), write_to=f"plot-{{THEME}}.png", output_width={width}, '
        f"output_height={height})\n"
    )
    assert f"chart = {chart}" in report.code
    assert report.changes == (
        "added import cairosvg at line 3",
        f"canvas: pygal chart {size} (the saved chart at line 9) renders {size}; the save renders {width}x{height} "
        f"through cairosvg.svg2png(output_width={width}, output_height={height}) in place of render_to_png",
    )
    canvas = measure_canvas(report.code, library="pygal")
    assert canvas.on_target and canvas.pixels == target
    assert not measure_canvas(code, library="pygal").on_target
    assert norm(code, "pygal") == report.code


def test_pygal_svg2png_save_gets_the_output_size() -> None:
    """Traced through `render`, `replace`, `encode` and names; an existing `import cairosvg as _cairosvg` is used."""
    code = pygal_code("""
        import cairosvg as _cairosvg

        chart = pygal.XY(width=3600, height=3600)
        svg = chart.render(is_unicode=True)
        marked = svg.replace("</svg>", "<g/></svg>")
        _cairosvg.svg2png(bytestring=marked.encode("utf-8"), write_to=f"plot-{THEME}.png", output_width=4800)
    """)
    report = normalise_report(code, library="pygal")

    assert report.code.endswith(
        '_cairosvg.svg2png(bytestring=marked.encode("utf-8"), write_to=f"plot-{THEME}.png", output_width=2400, '
        "output_height=2400)\n"
    )
    assert report.changes[-1].startswith("canvas: pygal chart 3600x3600 (the saved chart at line 11) renders 4800x4800")
    assert measure_canvas(report.code, library="pygal").pixels == SQUARE


def test_pygal_from_import_of_svg2png_is_used() -> None:
    code = pygal_code("""
        from cairosvg import svg2png

        chart = pygal.XY(width=4800, height=2700)
        chart.render_to_png(filename=f"plot-{THEME}.png", dpi=96)
    """)
    result = norm(code, "pygal")

    assert result.endswith(
        'svg2png(bytestring=chart.render(), write_to=f"plot-{THEME}.png", dpi=96, output_width=3200, '
        "output_height=1800)\n"
    )
    assert "import cairosvg" not in result


@pytest.mark.parametrize(
    ("body", "note", "pixels"),
    [
        (
            'chart = pygal.XY(width=size * 2, height=size)\nchart.render_to_png(f"plot-{THEME}.png")',
            "canvas: the chart's width= at line 10 is not a positive number or a module-level name bound once to "
            "one; the PNG size is left as it is",
            None,
        ),
        (
            'chart = pygal.XY(width=4800, height=3600)\nchart.render_to_png(f"plot-{THEME}.png")',
            "canvas: pygal chart 4800x3600 (the saved chart at line 10) has another aspect than 16:9 or 1:1; the PNG "
            "size is left as it is",
            (4800, 3600),
        ),
        (
            'chart = pygal.XY()\nchart.render_to_png(f"plot-{THEME}.png")',
            "canvas: pygal chart 800x600 (the saved chart at line 10) has another aspect than 16:9 or 1:1; the PNG "
            "size is left as it is",
            (800, 600),
        ),
        (
            "a = pygal.XY(width=4800, height=2700)\nb = pygal.Bar(width=4800, height=2700)\n"
            'cairosvg.svg2png(bytestring=merge(a, b), write_to=f"plot-{THEME}.png")',
            "canvas: no pygal chart traced from the save at line 12 (the file has 2); the PNG size is left as it is",
            None,
        ),
        (
            'cairosvg.svg2png(bytestring=build(size).encode(), write_to=f"plot-{THEME}.png")',
            "canvas: no pygal chart traced from the save at line 10; the PNG size is left as it is",
            None,
        ),
        # sizes pygal reads at render, after the constructor: never its 800x600 then
        (
            'chart = pygal.Bar()\nchart.width = 4800\nchart.height = 2700\nchart.render_to_png(f"plot-{THEME}.png")',
            "canvas: chart.width at line 11 sets the chart's size after its constructor; the PNG size is left as it is",
            None,
        ),
        (
            'chart = pygal.Bar()\nc = chart\nc.config.height = 2700\nchart.render_to_png(f"plot-{THEME}.png")',
            "canvas: c.config.height at line 12 sets the chart's size after its constructor; the PNG size is left as "
            "it is",
            None,
        ),
        (
            'chart = pygal.Bar()\nchart.config(width=4800, height=2700)\nchart.render_to_png(f"plot-{THEME}.png")',
            "canvas: chart.config(...) at line 11 may set the chart's size after its constructor; the PNG size is "
            "left as it is",
            None,
        ),
        (
            'cfg = pygal.Config()\nchart = pygal.Bar(config=cfg)\nchart.render_to_png(f"plot-{THEME}.png")',
            "canvas: the chart at line 11 takes a pygal.Config, which may set its size; the PNG size is left as it is",
            None,
        ),
        (
            'chart = pygal.Bar(pygal.Config)\nchart.render_to_png(f"plot-{THEME}.png")',
            "canvas: the chart at line 10 takes positional arguments (a pygal.Config) or **kwargs; the PNG size is "
            "left as it is",
            None,
        ),
        (
            "chart = pygal.Bar()\n"
            'cairosvg.svg2png(bytestring=chart.render(width=size, height=2700), write_to=f"plot-{THEME}.png")',
            "canvas: the render at line 11 takes keywords that may set the chart's size; the PNG size is left as it is",
            None,
        ),
        # a save that writes no PNG: the readiness scan blocks it, the canvas step leaves it alone
        (
            'chart = pygal.Bar(width=4800, height=2700)\nchart.render_to_file(f"plot-{THEME}.png")',
            "canvas: the render_to_file at line 11 writes no PNG; nothing to normalise",
            None,
        ),
    ],
)
def test_pygal_canvas_left_alone_with_a_note(body: str, note: str, pixels: tuple[int, int] | None) -> None:
    code = PYGAL_HEAD + "size = 4800\n" + body + "\n"
    report = normalise_report(code, library="pygal")

    assert report.code == code
    assert note in report.notes, report.notes
    canvas = measure_canvas(code, library="pygal")
    assert not canvas.on_target and canvas.pixels == pixels


def test_pygal_canvas_already_on_target_is_kept() -> None:
    code = pygal_code('chart = pygal.XY(width=3200, height=1800)\nchart.render_to_png(f"plot-{THEME}.png")\n')
    assert norm(code, "pygal") == code
    assert measure_canvas(code, library="pygal").pixels == LANDSCAPE


@pytest.mark.parametrize(
    ("build", "size", "line", "target"),
    [
        # dendrogram-radial: implicitly joined f-strings and the module constants they interpolate
        (
            """
            W, H = 4800, 2700
            svg = (
                '<?xml version="1.0" encoding="utf-8"?>\\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">\\n'
                f'<rect width="{W}" height="{H}" fill="{PAGE_BG}"/>\\n' + "\\n".join(elems) + "</svg>"
            )
            """,
            "4800x2700",
            14,
            LANDSCAPE,
        ),
        # histogram-2d: the root tag in a list the file appends to and joins
        (
            """
            svg_parts = []
            svg_parts.append('<svg width="4800" height="2700" viewBox="0 0 4800 2700">')
            for elem in elems:
                svg_parts.append(f'<g width="{elem}"/>')
            svg_parts.append("</svg>")
            svg = "\\n".join(svg_parts)
            """,
            "4800x2700",
            13,
            LANDSCAPE,
        ),
        # ternary-density: one triple-quoted f-string, px units and another name for the size
        (
            '''
            chart_width = 3600
            chart_height = 3600
            title_svg = f'<text x="{chart_width / 2}">t</text>'
            svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{chart_width}px" height="{chart_height}px">
            {title_svg}
            </svg>"""
            ''',
            "3600x3600",
            15,
            SQUARE,
        ),
    ],
)
def test_pygal_hand_built_svg_renders_the_canvas(build: str, size: str, line: int, target: tuple[int, int]) -> None:
    """Four catalogue files draw their own SVG at 4800x2700 or 3600x3600 and convert it with svg2png."""
    code = pygal_code(
        "import cairosvg\n\nelems = []\n"
        + source(build)
        + 'cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=f"plot-{THEME}.png")\n'
    )
    report = normalise_report(code, library="pygal")

    width, height = target
    assert report.code.endswith(
        f'cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=f"plot-{{THEME}}.png", output_width={width}, '
        f"output_height={height})\n"
    )
    assert report.changes == (
        f"canvas: hand-built SVG {size} (the <svg> root at line {line}) renders {size}; the save renders "
        f"{width}x{height} through cairosvg.svg2png(output_width={width}, output_height={height})",
    )
    before = measure_canvas(code, library="pygal")
    assert before.pixels == tuple(int(side) for side in size.split("x"))
    assert (before.note or "").startswith(f"pygal renders {size} (the <svg> root at line {line}), target ")
    assert measure_canvas(report.code, library="pygal").pixels == target
    assert norm(code, "pygal") == report.code


@pytest.mark.parametrize(
    ("build", "note"),
    [
        (
            'svg = f\'<svg width="{W * 2}" height="2700"></svg>\'',
            "the <svg> root at line 12 has no width= of a number or a module-level name bound once to one",
        ),
        (
            'W = 3200\nsvg = f\'<svg width="{W}" height="1800"></svg>\'',  # W is bound twice
            "the <svg> root at line 13 has no width= of a number or a module-level name bound once to one",
        ),
        (
            'svg = \'<svg width="4800" height="100%"></svg>\'',
            "the <svg> root at line 12 has no height= of a number or a module-level name bound once to one",
        ),
        (
            'inner = \'<svg width="800" height="600"/>\'\nsvg = \'<svg width="4800" height="2700">\' + inner',
            "no pygal chart traced from the save at line 14, and 2 <svg> tags at line 12, 13",
        ),
    ],
)
def test_pygal_hand_built_svg_of_unknown_size_is_left_alone(build: str, note: str) -> None:
    code = pygal_code("import cairosvg\n\nW = 4800\n" + build + "\n") + (
        'cairosvg.svg2png(bytestring=svg.encode(), write_to=f"plot-{THEME}.png")\n'
    )
    report = normalise_report(code, library="pygal")

    assert report.code == code
    assert f"canvas: {note}; the PNG size is left as it is" in report.notes, report.notes
    canvas = measure_canvas(code, library="pygal")
    assert canvas.pixels is None and canvas.note == f"pygal canvas unknown: {note}"


def test_pygal_output_size_names_are_read() -> None:
    """chord-basic and ecg-twelve-lead size the PNG through module constants; `W = H = 2400` binds both once."""
    code = pygal_code("""
        import cairosvg

        W = H = 2400
        chart = pygal.XY(width=W, height=H)
        cairosvg.svg2png(bytestring=chart.render(), write_to=f"plot-{THEME}.png", output_width=W, output_height=H)
    """)
    assert measure_canvas(code, library="pygal").pixels == SQUARE
    assert norm(code, "pygal") == code


def test_pygal_import_below_the_save_is_not_used() -> None:
    """An `import cairosvg` after the save would come too late for the rewritten save; one goes into the imports."""
    code = pygal_code("""
        chart = pygal.Bar(width=4800, height=2700)
        chart.render_to_png(f"plot-{THEME}.png")
        import cairosvg
    """)
    result = norm(code, "pygal")
    lines = result.splitlines()

    assert lines.index("import cairosvg") < next(i for i, line in enumerate(lines) if "cairosvg.svg2png(" in line)
    assert result.endswith(
        'cairosvg.svg2png(bytestring=chart.render(), write_to=f"plot-{THEME}.png", output_width=3200, '
        "output_height=1800)\nimport cairosvg\n"
    )


# --- lets-plot -----------------------------------------------------------------------------


LETSPLOT_HEAD = source("""
    import os

    import pandas as pd
    from lets_plot import LetsPlot, aes, geom_point, ggplot, ggsave, ggsize

    LetsPlot.setup_html()
    THEME = os.getenv("ANYPLOT_THEME", "light")
    df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
""")


def test_letsplot_catalogue_shape_in_miniature() -> None:
    """A star import, the `export_ggsave` alias, saves without `path=` and the lets-plot-images epilogue."""
    code = source("""
        import os
        import shutil

        import pandas as pd
        from lets_plot import *  # noqa: F403
        from lets_plot.export import ggsave as export_ggsave

        LetsPlot.setup_html()
        THEME = os.getenv("ANYPLOT_THEME", "light")
        df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
        plot = ggplot(df, aes(x="x", y="y")) + geom_point() + ggsize(1600, 900)

        export_ggsave(plot, f"plot-{THEME}.png", scale=3)
        export_ggsave(plot, filename=f"plot-{THEME}.html")

        # Move files from lets-plot-images to current directory
        if os.path.exists("lets-plot-images"):
            for f in [f"plot-{THEME}.png", f"plot-{THEME}.html"]:
                src = os.path.join("lets-plot-images", f)
                if os.path.exists(src):
                    shutil.move(src, f)
            if not os.listdir("lets-plot-images"):
                shutil.rmtree("lets-plot-images")
    """)
    expected = source("""
        import os

        import pandas as pd
        from lets_plot import (
            LetsPlot,
            aes,
            geom_point,
            ggplot,
            ggsize,
        )
        from lets_plot.export import ggsave

        LetsPlot.setup_html()
        THEME = os.getenv("ANYPLOT_THEME", "light")
        df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
        plot = ggplot(df, aes(x="x", y="y")) + geom_point() + ggsize(1600, 900)

        ggsave(plot, f"plot-{THEME}.png", path=".", scale=2)
        ggsave(plot, filename=f"plot-{THEME}.html", path=".")
    """)
    report = normalise_report(code, library="letsplot")

    assert report.code == expected
    assert report.notes == ()
    assert report.changes == (
        "import ggsave as export_ggsave -> import ggsave at line 6",
        "export_ggsave -> ggsave at line 13, 14",
        "from lets_plot import * -> 5 names at line 5",
        'added path="." to ggsave at line 19',
        'added path="." to ggsave at line 20',
        "removed the unused `import shutil` at line 2",
        "removed the lets-plot-images epilogue at lines 23-29",
        "canvas: 1600x900 (ggsize at line 16) at scale 3 renders 4800x2700; scale=2 renders 3200x1800",
    )
    assert norm(code, "letsplot") == expected
    assert measure_canvas(expected, library="letsplot").pixels == LANDSCAPE


@pytest.mark.parametrize(
    "clash", ["ggsave = None", "def save(export_ggsave):\n    return export_ggsave", "from plotnine import ggsave"]
)
def test_letsplot_save_alias_stays_when_a_name_is_bound_again(clash: str) -> None:
    code = LETSPLOT_HEAD.replace(", ggsave,", ",") + "from lets_plot.export import ggsave as export_ggsave\n\n"
    code += clash + '\nexport_ggsave(ggplot(), f"plot-{THEME}.png", path=".", scale=2)\n'
    report = normalise_report(code, library="letsplot")

    assert "import ggsave as export_ggsave" in report.code
    assert any(
        note.startswith("save alias: ") and note.endswith("export_ggsave left unchanged") for note in report.notes
    )


def test_letsplot_star_import_lists_the_names_the_module_reads() -> None:
    """renko-basic, with an explicit import kept, a name the file assigns (column-stratigraphic's `margin`) and a
    name read only inside a function."""
    code = source("""
        import os

        from lets_plot import *
        from lets_plot import element_blank, theme

        THEME = os.getenv("ANYPLOT_THEME", "light")
        margin = 16
        LetsPlot.setup_html()


        def styled(plot):
            return plot + theme_minimal() + theme(panel_grid=element_blank())


        plot = styled(ggplot() + geom_tile(aes(x="x"), size=margin) + scale_fill_manual(values=["#009E73"]))
        plot += ggsize(1600, 900) + labs(title="")
        ggsave(plot, f"plot-{THEME}.png", path=".", scale=2)
    """)
    result = norm(code, "letsplot")

    assert result.startswith(
        "import os\n\nfrom lets_plot import (\n    LetsPlot,\n    aes,\n    geom_tile,\n    ggplot,\n    ggsave,\n"
        "    ggsize,\n    labs,\n    scale_fill_manual,\n    theme_minimal,\n)\n"
        "from lets_plot import element_blank, theme\n"
    )


@pytest.mark.parametrize(
    ("code", "note"),
    [
        (
            "from lets_plot import *\nfrom math import *\nplot = ggplot() + geom_point(size=pi)\n",
            "star import: the file has 2 star imports; the star import at line 1 stays",
        ),
        (
            "from lets_plot import *\n\n\ndef keep():\n    global plot\n    plot = ggplot()\n",
            "star import: a global statement at line 5; the star import at line 1 stays",
        ),
        (
            "from lets_plot import *\nplot = ggplot() + theme(legend_position='top')\ntheme = None\n",
            "star import: theme may be read before the file binds it; the star import at line 1 stays",
        ),
        # the statement reads the name before it binds it
        (
            "from lets_plot import *\nlabs = labs(title='t')\nplot = ggplot() + labs\n",
            "star import: labs may be read before the file binds it; the star import at line 1 stays",
        ),
        # bound only when the condition holds: without the star import the read would raise NameError
        (
            "import os\nfrom lets_plot import *\nif os.getenv('X'):\n    labs = None\nplot = labs(title='t')\n",
            "star import: labs may be read before the file binds it; the star import at line 2 stays",
        ),
        (
            "try:\n    from lets_plot import *\nexcept ImportError:\n    pass\n",
            "star import: it is not a module-level statement; the star import at line 2 stays",
        ),
        (
            "from lets_plot import *; plot = ggplot()\n",
            "star import: it shares its line with other code; the star import at line 1 stays",
        ),
    ],
)
def test_letsplot_star_import_refusals_keep_it_with_a_note(code: str, note: str) -> None:
    report = normalise_report(code, library="letsplot")

    assert "from lets_plot import *" in report.code
    assert note in report.notes, report.notes


def test_letsplot_star_import_names_bound_where_they_are_read() -> None:
    """column-stratigraphic binds `margin` (a lets-plot name) in a loop and reads it there; a `with` body always
    runs."""
    code = source("""
        import os

        from lets_plot import *

        THEME = os.getenv("ANYPLOT_THEME", "light")
        for row in range(2):
            margin = 0.03
            print(row + margin)
        with open(os.devnull) as handle:
            labs = handle.name
        plot = ggplot() + geom_point(size=len(labs)) + scale_x_log10() + scale_x_log2()
        plot += GGBunch() + LetsPlot.setup_html()
    """)
    result = norm(code, "letsplot")

    assert result.startswith(
        "import os\n\nfrom lets_plot import (\n    GGBunch,\n    LetsPlot,\n    geom_point,\n    ggplot,\n"
        "    scale_x_log2,\n    scale_x_log10,\n)\n"
    )  # ruff's order-by-type: classes first, then natural order


def test_letsplot_unused_star_import_goes() -> None:
    code = 'import os\nfrom lets_plot import *\n\nTHEME = os.getenv("ANYPLOT_THEME", "light")\n'
    report = normalise_report(code, library="letsplot")

    assert report.code == 'import os\n\nTHEME = os.getenv("ANYPLOT_THEME", "light")\n'
    assert report.changes[0] == "removed the unused `from lets_plot import *` at line 2"


@pytest.mark.parametrize(
    ("saves", "expected"),
    [
        # hive-basic: no path=, so lets-plot writes into ./lets-plot-images (the sandbox refuses the os.mkdir)
        (
            'ggsave(plot, f"plot-{THEME}.png", scale=3)\nggsave(plot, filename=f"plot-{THEME}.html")',
            'ggsave(plot, f"plot-{THEME}.png", path=".", scale=2)\nggsave(plot, filename=f"plot-{THEME}.html", path=".")',
        ),
        # scatter-annotated: a computed directory, and lets-plot's default spelled out
        (
            "_script_dir = Path(__file__).parent\n"
            'ggsave(plot, f"plot-{THEME}.png", path=str(_script_dir), scale=3)\n'
            'ggsave(plot, f"plot-{THEME}.html", path=None)',
            'ggsave(plot, f"plot-{THEME}.png", path=".", scale=2)\nggsave(plot, f"plot-{THEME}.html", path=".")',
        ),
        # gain-curve: the shared target rewrite first, then the directory
        (
            "output_dir = os.getcwd()\n"
            'ggsave(plot, os.path.join(output_dir, f"plot-{THEME}.png"), scale=3)\n'
            'ggsave(plot, os.path.join(output_dir, f"plot-{THEME}.html"))',
            'ggsave(plot, f"plot-{THEME}.png", path=".", scale=2)\nggsave(plot, f"plot-{THEME}.html", path=".")',
        ),
    ],
)
def test_letsplot_saves_get_the_directory(saves: str, expected: str) -> None:
    code = "from pathlib import Path\n\n" + LETSPLOT_HEAD + "plot = ggplot(df) + geom_point() + ggsize(1600, 900)\n"
    result = norm(code + saves + "\n", "letsplot")

    assert result.endswith(expected + "\n")
    assert "Path" not in result.replace("LetsPlot", "") and "output_dir" not in result


def test_letsplot_other_literal_directory_stays_with_a_note() -> None:
    code = (
        LETSPLOT_HEAD + 'plot = ggplot() + ggsize(1600, 900)\nggsave(plot, f"plot-{THEME}.png", path="out", scale=2)\n'
    )
    report = normalise_report(code, library="letsplot")

    assert 'path="out"' in report.code
    assert "save directory: the ggsave at line 10 saves into path='out'; left unchanged" in report.notes


@pytest.mark.parametrize(
    "epilogue",
    [
        # chessboard-pieces: one guarded move per file, then the directory
        """
        # Move files from lets-plot-images to current directory
        if os.path.exists(f"lets-plot-images/plot-{THEME}.png"):
            shutil.move(f"lets-plot-images/plot-{THEME}.png", f"plot-{THEME}.png")
        if os.path.exists("lets-plot-images"):
            shutil.rmtree("lets-plot-images")
        """,
        # histogram-overlapping: a listing loop
        """
        if os.path.exists("lets-plot-images"):
            for file in os.listdir("lets-plot-images"):
                src = os.path.join("lets-plot-images", file)
                if os.path.isfile(src):
                    shutil.move(src, file)
            shutil.rmtree("lets-plot-images")
        """,
        # line-3d-trajectory: pathlib names and a copy
        """
        lpi_dir = pathlib.Path("lets-plot-images")
        if lpi_dir.exists():
            for ext in ["png", "html"]:
                src = lpi_dir / f"plot-{THEME}.{ext}"
                dst = pathlib.Path(f"plot-{THEME}.{ext}")
                if src.exists() and not dst.exists():
                    shutil.copy(src, dst)
        """,
        # line-loss-training: a glob over the directory
        """
        images_dir = Path("lets-plot-images")
        if images_dir.exists():
            for file in images_dir.glob(f"plot-{THEME}.*"):
                shutil.move(str(file), str(file.name))
        """,
        # spectrum-basic: a cleanup that swallows OSError
        """
        try:
            if not os.listdir("lets-plot-images"):
                os.rmdir("lets-plot-images")
        except OSError:
            pass
        """,
        # swimmer-clinical-timeline: a dead cleanup with its own import
        """
        if os.path.exists("lets-plot-images"):
            import shutil

            shutil.rmtree("lets-plot-images")
        """,
    ],
)
def test_letsplot_images_epilogue_goes(epilogue: str) -> None:
    saves = source("""
        plot = ggplot(df) + geom_point() + ggsize(1600, 900)
        ggsave(plot, f"plot-{THEME}.png", path=".", scale=2)
        ggsave(plot, f"plot-{THEME}.html", path=".")
    """)
    code = "import pathlib\nimport shutil\nfrom pathlib import Path\n" + LETSPLOT_HEAD + saves + "\n" + source(epilogue)
    report = normalise_report(code, library="letsplot")

    assert report.code == LETSPLOT_HEAD + saves
    assert any(change.startswith("removed the lets-plot-images epilogue") for change in report.changes)
    assert report.notes == ()


def test_letsplot_returned_path_becomes_the_save() -> None:
    """line-confidence moves the path ggsave returns; the save then sizes in pixels, so only the scale changes."""
    code = (
        "import shutil\n"
        + LETSPLOT_HEAD
        + source("""
        plot = ggplot(df) + geom_point() + ggsize(1600, 900)

        # Save as PNG (4800 x 2700 px)
        png_path = ggsave(plot, f"plot-{THEME}.png", w=4800, h=2700, unit="px", dpi=100)
        shutil.move(png_path, f"plot-{THEME}.png")

        # Save as HTML
        html_path = ggsave(plot, f"plot-{THEME}.html")
        shutil.move(html_path, f"plot-{THEME}.html")
    """)
    )
    report = normalise_report(code, library="letsplot")

    assert report.code.endswith(
        "# Save as PNG (4800 x 2700 px)\n"
        'ggsave(plot, f"plot-{THEME}.png", path=".", w=4800, h=2700, unit="px", dpi=100, scale=0.6667)\n\n'
        '# Save as HTML\nggsave(plot, f"plot-{THEME}.html", path=".")\n'
    )
    assert "png_path = ggsave(...) -> ggsave(...) at line 13" in report.changes
    assert measure_canvas(report.code, library="letsplot").pixels == LANDSCAPE


def test_letsplot_every_returned_path_of_a_name_becomes_the_save() -> None:
    """A name bound to two ggsave returns: one pass unwraps both, so a second pass changes nothing."""
    saves = 'png_path = ggsave(plot, f"plot-{THEME}.png", path=".", scale=2)\nshutil.move(png_path, "out.png")\n'
    code = "import shutil\n" + LETSPLOT_HEAD + "plot = ggplot(df) + geom_point() + ggsize(1600, 900)\n" + saves * 2
    result = norm(code, "letsplot")

    assert "png_path" not in result and "shutil" not in result
    assert result.count('ggsave(plot, f"plot-{THEME}.png", path=".", scale=2)\n') == 2


def test_letsplot_statement_that_does_more_than_move_stays_with_a_note() -> None:
    code = LETSPLOT_HEAD + source("""
        lp_dir = "lets-plot-images"
        plot = ggplot(df) + ggsize(1600, 900)
        ggsave(plot, f"plot-{THEME}.png", path=".", scale=2)
        print(os.listdir(lp_dir))
        if os.path.exists(lp_dir):
            os.rmdir(lp_dir)
    """)
    report = normalise_report(code, library="letsplot")

    assert 'lp_dir = "lets-plot-images"' in report.code and "print(os.listdir(lp_dir))" in report.code
    assert "os.rmdir" not in report.code
    assert "save epilogue: the statement at line 12 uses lets-plot-images in other ways; left in place" in report.notes


@pytest.mark.parametrize(
    ("plot", "save", "scale", "pixels"),
    [
        ("ggsize(1600, 900)", "scale=3", "scale=2", LANDSCAPE),  # 106 catalogue files rendered 4800x2700
        ("ggsize(1200, 1200)", "scale=3", "scale=2", SQUARE),
        ("ggsize(900, 900)", "scale=3", "scale=2.667", SQUARE),
        ("ggsize(800, 450)", "", ", scale=4", LANDSCAPE),  # lets-plot's default scale is 2
        ("ggsize(800, 450)", "dpi=150", "dpi=150, scale=2.56", LANDSCAPE),  # dpi= scales by dpi / 96
        # w= and h= in px; in a physical unit lets-plot can render one pixel short of the model
        ("ggsize(1600, 900)", "w=1600, h=900, unit='px'", "unit='px', scale=2", LANDSCAPE),
        # tier 2: inside the canvas, under R2's cap; the exact fit is as short as the decimal below it
        ("ggsize(1600, 960)", "scale=3", "scale=1.875", (3000, 1800)),
        ("ggsize(1600, 970)", "scale=3", "scale=1.855", (2968, 1799)),  # the fit 1.85567... is longer
    ],
)
def test_letsplot_canvas_changes_only_the_scale(plot: str, save: str, scale: str, pixels: tuple[int, int]) -> None:
    keywords = f", {save}" if save else ""
    code = (
        LETSPLOT_HEAD
        + f'plot = ggplot(df) + geom_point() + {plot}\nggsave(plot, f"plot-{{THEME}}.png", path="."{keywords})\n'
    )
    report = normalise_report(code, library="letsplot")

    assert plot in report.code and scale in report.code.splitlines()[-1]
    assert measure_canvas(report.code, library="letsplot").pixels == pixels
    assert norm(code, "letsplot") == report.code


@pytest.mark.parametrize(
    ("plot", "note"),
    [
        # candlestick-volume: a grid sizes itself from its panels
        (
            "top = ggplot() + ggsize(1600, 630)\nbottom = ggplot() + ggsize(1600, 270)\nplot = gggrid([top, bottom])",
            "canvas: gggrid at line 11 has no ggsize of its own; the render relies on the R3 canvas gate",
        ),
        # an aspect no scale reaches, under R2's cap
        (
            "plot = ggplot() + ggsize(800, 853)",
            "canvas: 800x853 (ggsize at line 9) at scale 3 renders 2400x2559; no scale renders 3200x1800 or "
            "2400x2400, so the render relies on the R3 gate",
        ),
    ],
)
def test_letsplot_canvas_left_alone_with_a_note(plot: str, note: str) -> None:
    code = LETSPLOT_HEAD.replace("ggsave, ggsize", "ggsave, gggrid, ggsize") + plot + "\n"
    code += 'ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)\n'
    report = normalise_report(code, library="letsplot")

    assert report.code == code
    assert note in report.notes, report.notes
    assert not measure_canvas(code, library="letsplot").on_target


def test_letsplot_plot_size_falls_back_to_the_file_and_the_default() -> None:
    added = (
        LETSPLOT_HEAD
        + 'plot = ggplot(df) + geom_point()\nplot += ggsize(1600, 900)\nggsave(plot, f"plot-{THEME}.png", path=".", scale=3)\n'
    )
    assert measure_canvas(added, library="letsplot").note == (
        "lets-plot renders 4800x2700 from 1600x900 (the file's only ggsize) at scale 3, target 3200x1800"
    )
    default = LETSPLOT_HEAD + 'plot = ggplot(df) + geom_point()\nggsave(plot, f"plot-{THEME}.png", path=".")\n'
    assert measure_canvas(default, library="letsplot").pixels == (1200, 800)  # 600x400 at the default scale 2


def test_max_image_pixels_is_r2s_cap() -> None:
    from agents.anyplot.render.png import MAX_IMAGE_PIXELS as R2_CAP

    assert MAX_IMAGE_PIXELS == R2_CAP


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


def test_near_aspect_change_names_the_offset() -> None:
    code = canvas_code("fig, ax = plt.subplots(figsize=(16, 9.05))", 'plt.savefig(f"plot-{THEME}.png", dpi=300)')
    report = normalise_report(code, library="matplotlib")

    assert "canvas: figsize (16, 9.05) at dpi 200 renders 3200x1810, within 16 px of 3200x1800" in report.changes
    canvas = measure_canvas(report.code)
    assert canvas.pixels == (3200, 1810) and not canvas.on_target


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
    report = normalise_report(original, library=path.stem)
    result = report.code

    assert normalise(result, library=path.stem) == result
    if any(change.startswith("canvas:") for change in report.changes) and path.stem in ("pygal", "letsplot"):
        rendered = measure_canvas(result, library=path.stem)
        assert rendered.pixels is not None and rendered.target is not None, rendered.note
        assert all(side <= limit + TOLERANCE for side, limit in zip(rendered.pixels, rendered.target, strict=True))
        assert rendered.pixels[0] * rendered.pixels[1] <= MAX_IMAGE_PIXELS
    regions = find_regions(original, library=path.stem)
    size, _ = figure_size(regions)
    call = regions.savefig or (regions.savefig_calls[-1] if regions.savefig_calls else None)
    dpi = effective_dpi(regions, call)[0] if call is not None else None
    canvas = measure_canvas(result, library=path.stem)  # figsize is None where the library sizes its own canvas
    if canvas.figsize is not None and size is not None and dpi is not None and not isinstance(plan_dpi(size), str):
        assert canvas.pixels in (LANDSCAPE, SQUARE), canvas.note
        assert canvas.on_target, canvas.note
