"""The normaliser: catalogue code in, code that renders the exact canvas out.

`normalise(code, library=...)` serves every library with a save rule
(`regions.SAVE_RULES`: matplotlib, seaborn, plotnine, altair, pygal, letsplot) and makes
these rewrites, in the order `_steps` runs them, each only when it applies:

1. **Catalogue header and title.** The four-line module docstring that opens every
   catalogue file (lines `anyplot.ai`, `<spec-id>: <title>`, `Library: ...`,
   `Quality: ...`) and the blank lines after it go first, also a second one right after
   it (3 lets-plot files carry two, 2026-10-26). Every string literal in the
   catalogue title form, `[<descriptive> · ]<spec-id> · [<language> · ]<library> ·
   anyplot.ai` (also with the legacy `pyplots.ai`, or with the descriptive part ended by
   a newline), becomes `""` after the guards: it names the catalogue's spec and demo
   data, and the catalogue title rule does not apply to user plots. The call that shows
   it stays, so code that positions the title keeps working. A title the adapter wrote
   in its own words does not have that form and stays, and so does a title built by an
   f-string.
2. **lets-plot's imports** (letsplot only). `from lets_plot.export import ggsave as
   export_ggsave` (17 catalogue files) becomes `... import ggsave` and every
   `export_ggsave` becomes `ggsave`, so the save rule sees the save; when the file binds
   either name another way, the alias stays with a note. `from lets_plot import *` (151
   files) becomes one parenthesised `from lets_plot import (...)` of exactly the names the
   module looks up as globals and does not bind itself (`symtable`), taken from
   `letsplot_names.LETS_PLOT_NAMES` without importing lets_plot, in ruff's
   order-by-type. A second star import, a `global` statement or a lets-plot name read
   before the file binds it leaves the star import in place with a note (0 catalogue
   files, 2026-10-26).
3. **Save target.** A target that is a path whose file name is the theme f-string,
   such as `os.path.join(script_dir, f"plot-{THEME}.png")`, `OUT / f"plot-{THEME}.png"`,
   `f"{script_dir}/plot-{THEME}.png"`, or a module-level name assigned one of those
   (`output_path`), becomes the literal `f"plot-{THEME}.png"` in every save call of the
   library's rule (`savefig`, plotnine's `save` and `ggsave`, altair's `save`, pygal's
   `render_to_png`, `render_to_file` and `svg2png`, lets-plot's `ggsave`, also for
   `f"plot-{THEME}.html"` where the rule admits it), so the file lands next to the run
   form. A single-theme target such as `"plot.png"` stays (the readiness scan blocks it).
4. **Save directory** (letsplot only). lets-plot's `ggsave` writes into
   `./lets-plot-images` without `path=`, and the plot sandbox refuses the `os.mkdir`, so
   every `ggsave` of a theme target gets `path="."` (31 PNG saves lack it) and a computed
   `path=` (`str(_script_dir)`) or `path=None` becomes `"."`; another literal directory
   stays with a note. The 25 catalogue files that then move, copy or delete what
   lets-plot wrote there lose that epilogue: a module-level statement
   without a save that mentions `"lets-plot-images"` (or a name bound to it or to a
   `ggsave` return value), is made only of `if`, `for`, `try` (each `except` only
   `pass`), expressions, assignments and `import shutil` or `pathlib`, and calls only
   `EPILOGUE_CALLS` and `EPILOGUE_METHODS` goes, with the names bound to the directory and
   an `import shutil` that nothing kept uses; `png_path = ggsave(...)` whose name only fed
   the epilogue becomes the bare save. Any other statement that mentions the directory
   stays with a note, and the SECURITY validator blocks the file.
5. **HTML and SVG writes** (pygal only). A module-level `with open(<f"plot-{THEME}.html"
   or a path to it>, "wb" | "w") as f:` whose one statement writes `X.render()` (mode
   `"wb"`), `X.render(is_unicode=True)` or `X.render().decode()` (mode `"w"`, UTF-8)
   becomes `X.render_to_file(f"plot-{THEME}.html")`, which writes the same bytes (158
   catalogue files; the HTML and the PNG were byte-identical on all 156 that run,
   2026-10-25). Every other module-level `open()` write of the theme `.html` or `.svg`
   file (a hand-built page, a post-processed SVG) and every `X.render_to_file(<theme
   .svg>)` goes, unless the same target is named again elsewhere in the file, and so do
   the module-level assignments that only fed a removed write, repeated until none is
   left (never one that holds a save call). The SECURITY validator has no pinnable form
   for an `open()` write, and the plot sandbox refuses `.svg` files.
6. **Guards.** A file named `matplotlib.py`, `seaborn.py` or `pygal.py` shadows the
   installed package when run from its own directory, so many catalogue files strip
   their directory from `sys.path` first. The run form is `plot.py`, so the guard goes,
   in three steps. `X = importlib.util.find_spec("pkg")` followed by
   `if X and X.origin != __file__:` whose branch holds only imports becomes those imports
   (the branch the run form takes), and `X` goes once unused. A module-level `try:` of
   imports only, with no `except` or `else`, whose `finally:` only changes `sys.path`,
   becomes its imports. Then every module-level statement that only changes `sys.path`
   or `sys.modules` (an assignment to `sys.path`, `sys.dont_write_bytecode = ...`, a
   `sys.path.*()` or `sys.modules.*()` call, `del sys.modules[...]`, or an `if`, `for`,
   `while` or `try` holding only such statements, private helper assignments and
   `pass`), whatever `sys` is imported as, goes. Then every module-level assignment that
   is no longer used and only served the guard, read `sys.path` (`_saved = sys.path[:]`)
   or computed a file location (from `__file__`, `os.path.*`, `pathlib` or
   `os.getcwd()`, or from another such name) goes, repeated until none is left, with the
   `del` of those names, the comment lines directly above every removed statement, and
   each import (`sys`, `os as _os`, `pathlib`, ...) that only they used. Files that load
   their modules through `NAME = importlib.import_module("dotted.name")[.ATTR]`, also
   after `from importlib import import_module`, get `import dotted.name as NAME` or
   `from dotted.name import ATTR as NAME`, and the importlib import goes once unused.
7. **Canvas** (`SaveRule.canvas`), last:
   * matplotlib and seaborn (`figure`): every `savefig` loses `bbox_inches=` and
     `pad_inches=` (`"tight"` crops the canvas by 30 to 50 px, the documented cause of
     the drift that the `impl-review.yml` canvas gate catches), and the dpi is rescaled
     so that `figsize * dpi` renders exactly 3200x1800 (16:9) or 2400x2400 (1:1). The
     figure size stays; the target is the one the figure's aspect reaches, so
     `(8, 4.5)` and `(16, 9)` map to 3200x1800 at dpi 400 and 200, `(6, 6)`, `(12, 12)`
     and `(16, 16)` to 2400x2400 at dpi 400, 200 and 150. The new dpi is written on
     `savefig` (added when missing) and on every literal `dpi=` of a figure creation call
     and `set_dpi(...)`, so code that measures in pixels before saving sees the same
     dpi. An integer dpi is used when one hits the target exactly; otherwise the
     shortest decimal that does (matplotlib truncates `figsize * dpi` to whole pixels,
     so `(7, 7)` gets dpi 342.9). When no dpi hits it exactly, because the aspect is a
     hair off (`(16, 9.05)`), the dpi renders one side exactly and the other within the
     16 px of the canvas gate (3200x1810); the change line names the pixels and the
     offset, and `measure_canvas` and the readiness scan report it as a `canvas:` note.
     The figure size comes from the last literal `set_size_inches(w, h)` (seaborn
     grids), else from the single literal `figsize=`. The rewrite is all or nothing:
     when the figure size is missing or not a literal, when its aspect reaches neither
     target within 16 px, or when a savefig takes `**kwargs`, `bbox_inches` and the dpi
     stay as they are and a note says why.
   * pygal (`pygal`): the PNG is the chart's `width` x `height` (pygal's 800x600 when
     neither is set), or the output size of a `cairosvg.svg2png` save. 98 catalogue
     charts are 4800x2700 and 4 are 3600x3600 (files from May 2026), over R2's pixel cap.
     A chart whose literal size has exactly the 16:9 or 1:1 aspect keeps its size, so the
     layout stays, and its protected save renders the target instead:
     `X.render_to_png(f"plot-{THEME}.png")` becomes `cairosvg.svg2png(bytestring=
     X.render(), write_to=f"plot-{THEME}.png", output_width=3200, output_height=1800)`
     (with `import cairosvg` added where the file lacks it), and an `svg2png` save gets
     the two keywords. The chart is the one the save renders (traced through `render`,
     `encode`, `decode`, `replace` and module-level names bound to them), else the
     file's only chart; a computed size, another aspect or several charts leave the save
     alone with a note.
   * lets-plot (`letsplot`): only `scale=` on the protected PNG save changes, never
     `ggsize` or `w`/`h`, so text and ticks keep their size relative to the plot. The
     size is the literal `ggsize` in the saved plot's `+` chain, else the file's only
     literal `ggsize` (when no grid is drawn), else lets-plot's 600x400; `gggrid` and
     `ggbunch` without a `ggsize` of their own size themselves from their panels and are
     left alone with a note. lets-plot renders `floor(size * scale)` (scale 2 by default,
     1 with `w`/`h` or `dpi=`; `w`/`h` in px, or in `unit` at `dpi`, 300 by default).
     The scale is the shortest decimal that renders the target exactly, else one within
     16 px; when none does and the render is over R2's pixel cap, the shortest decimal
     that fits it inside the nearer target (R3 pads the rest).
   * plotnine and altair (None): plotnine sizes the canvas on its save (`width=`,
     `height=`, `units=`, `dpi=`, 3200x1800 in most catalogue files) and altair through
     its chart's `width` and `height` times `scale_factor`, padded by its PIL block, so
     for those two the step only notes that the render relies on the R3 canvas gate.

Each step is checked with `ast.parse` and dropped with a note if it would not parse.
The result is idempotent: `normalise(normalise(x)) == normalise(x)`.
"""

import ast
import math
import re
import symtable
import textwrap
from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction
from functools import partial

from .letsplot_names import LETS_PLOT_NAMES
from .regions import (
    HTML_SUFFIX,
    HTML_TARGET,
    PNG_SUFFIX,
    SAVE_RULES,
    STANDARD_TARGET,
    THEME_NAME,
    Number,
    Regions,
    SavefigCall,
    SourceIndex,
    Span,
    as_number,
    dotted_name,
    find_regions,
    is_theme_target,
    save_rule,
    save_target,
)


SUPPORTED_LIBRARIES = frozenset(SAVE_RULES)
"""The libraries the normaliser serves: every library with a save rule (`regions.SAVE_RULES`)."""
# Modules whose import goes whenever nothing kept uses it: the guard family, all banned
# by the SECURITY validator.
GUARD_MODULES = frozenset({"sys", "importlib", "pathlib"})
LANDSCAPE = (3200, 1800)
SQUARE = (2400, 2400)
TARGETS = (LANDSCAPE, SQUARE)
TOLERANCE = 16  # px per axis, the impl-review.yml canvas gate
MAX_IMAGE_PIXELS = 3200 * 1800 * 2
"""R2's pixel cap (`render.png.MAX_IMAGE_PIXELS`, pinned by a test): a larger PNG is refused outright."""
DEFAULT_DPI = 100  # matplotlib's figure.dpi; savefig.dpi defaults to the figure's
DROPPED_SAVEFIG_KEYWORDS = ("bbox_inches", "pad_inches")
HEADER_FIRST_LINE = "anyplot.ai"
MAX_DPI_DECIMALS = 6
SVG_SUFFIX = ".svg"

PYGAL_DEFAULT_SIZE = (800, 600)  # pygal's Config width and height
PYGAL_PASSTHROUGH = frozenset({"render", "encode", "decode", "replace"})
"""Calls that hand on the chart's SVG unchanged in size, from `X.render()` to the bytes `svg2png` reads; no
catalogue file's `replace` on the SVG text touches its `viewBox` or a size (2026-10-26)."""
PYGAL_NOT_CHARTS = frozenset({"Config"})
"""Capitalised names of the pygal module that are no chart class (`pygal.Config` carries settings)."""
CAIROSVG = "cairosvg"

LETSPLOT_SAVE = "ggsave"
LETSPLOT_MODULES = frozenset({"lets_plot", "lets_plot.export"})
LETSPLOT_IMAGES = "lets-plot-images"
LETSPLOT_GRIDS = frozenset({"gggrid", "ggbunch", "GGBunch"})
LETSPLOT_DEFAULT_SIZE = (600, 400)  # lets-plot's plot size without ggsize (probed 2026-10-26)
LETSPLOT_DEFAULT_DPI = 300  # ggsave's dpi for `w`/`h` in a physical unit
LETSPLOT_PER_INCH = {"in": Fraction(1), "cm": Fraction(100, 254), "mm": Fraction(10, 254)}
EPILOGUE_CALLS = frozenset(
    {
        "shutil.move",
        "shutil.copy",
        "shutil.copy2",
        "shutil.copyfile",
        "shutil.rmtree",
        "os.rename",
        "os.replace",
        "os.remove",
        "os.unlink",
        "os.rmdir",
        "os.listdir",
        "os.path.exists",
        "os.path.isfile",
        "os.path.isdir",
        "os.path.join",
        "str",
        "pathlib.Path",
    }
)
"""The calls (resolved through the file's imports) a lets-plot-images epilogue may make: file moves, copies,
deletions, listings, existence tests and path joins (the 25 catalogue epilogues, 2026-10-26)."""
EPILOGUE_METHODS = frozenset({"exists", "glob", "iterdir", "is_file", "rename", "replace", "unlink", "rmdir"})
"""The `pathlib.Path` methods an epilogue may call on any receiver."""
EPILOGUE_MODULES = frozenset({"shutil", "pathlib"})
"""The modules an epilogue may import inside itself; `import shutil` goes once nothing kept uses it."""

_MODULE_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*")
_COMMA_GAP = re.compile(r"\s*,\s*")
_LINE_TAIL = re.compile(r"\s*,?\s*(?:#.*)?")
_WHITESPACE = re.compile(r"\s+")
# `[<descriptive> · ]<spec-id> · [<language> · ]<library> · anyplot.ai`, also with the
# legacy `pyplots.ai`, or with the descriptive part ended by a newline instead of ` · `.
_CATALOGUE_TITLE = re.compile(
    r"(?s)\s*(?:.*?[·\n]\s*)?"
    r"[a-z0-9]+(?:-[a-z0-9]+)*\s*·\s*(?:[A-Za-z]+\s*·\s*)?[a-z][a-z0-9]*\s*·\s*(?:anyplot|pyplots)\.ai\s*"
)

TextEdit = tuple[int, int, str]  # replace code[start:end] with the text
StepResult = tuple[str, list[str], list[str]]  # the code, the changes made, the notes on what was left alone
Step = Callable[[str], StepResult]


@dataclass(frozen=True, slots=True)
class Normalised:
    """The normalised code, what changed, and what was left alone and why."""

    code: str
    changes: tuple[str, ...]
    notes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Canvas:
    """The canvas a source renders, as far as its literals tell.

    `pixels` is what the library writes: for matplotlib `figsize` at `dpi`, each side
    truncated to whole pixels as `RendererAgg` does; for pygal the chart's size or the
    `svg2png` output size, rounded as cairosvg does; for lets-plot the plot size times
    the scale, floored. `figsize` and `dpi` are matplotlib's only. `target` is the nearer
    of the two canvases (the impl-review.yml rule). `note` is None exactly when
    `pixels == target`.
    """

    figsize: tuple[Number, Number] | None
    dpi: Number | None
    pixels: tuple[int, int] | None
    target: tuple[int, int] | None
    note: str | None

    @property
    def on_target(self) -> bool:
        """Whether the source renders exactly 3200x1800 or 2400x2400."""
        return self.note is None


def normalise(code: str, *, library: str) -> str:
    """The normalised code; see the module docstring. Raises `ValueError` for an unsupported library."""
    return normalise_report(code, library=library).code


def normalise_report(code: str, *, library: str) -> Normalised:
    """`normalise` with the list of changes made and the notes on what was left alone."""
    if library not in SUPPORTED_LIBRARIES:
        raise ValueError(f"no normaliser for library {library!r}; supported: {sorted(SUPPORTED_LIBRARIES)}")
    try:
        ast.parse(code)
    except SyntaxError as exc:
        return Normalised(code, (), (f"syntax: line {exc.lineno} does not parse; nothing was normalised",))
    changes: list[str] = []
    notes: list[str] = []
    for name, step in _steps(library):
        new_code, step_changes, step_notes = step(code)
        if new_code != code:
            try:
                ast.parse(new_code)
            except SyntaxError:
                notes.append(f"{name}: the rewrite would not parse; left unchanged")
                continue
        code = new_code
        changes.extend(step_changes)
        notes.extend(step_notes)
    return Normalised(code, tuple(changes), tuple(notes))


def _steps(library: str) -> list[tuple[str, Step]]:
    """The rewrites of the module docstring in the order they run; each library-specific one for its library only.

    lets-plot's alias rename runs before the save-target step, which matches calls by
    the save name; its save directory runs after it, on the literal targets, and before
    the guard, which then removes the file-location helpers that `path=` and the
    epilogue used. pygal's HTML step also runs before the guard, which removes the
    output-directory helpers of the writes it rewrote or dropped.
    """
    steps: list[tuple[str, Step]] = [("header", _strip_header)]
    if library == "letsplot":
        steps += [("save alias", _rename_save_alias), ("star import", _expand_star_import)]
    steps.append(("savefig target", partial(_rewrite_savefig_targets, library=library)))
    if library == "letsplot":
        steps += [("save directory", _letsplot_save_paths), ("save epilogue", _strip_letsplot_epilogue)]
    if library == "pygal":
        steps.append(("html", _pygal_html_writes))
    steps += [
        ("find_spec guard", _strip_find_spec_guard),
        ("try guard", _hoist_try_guard),
        ("sys.path guard", _strip_path_guard),
        ("title", _strip_title),
        ("canvas", partial(_normalise_canvas, library=library)),
    ]
    return steps


# --- canvas ------------------------------------------------------------------------------


def figure_size(regions: Regions) -> tuple[tuple[Number, Number] | None, str]:
    """The figure size in inches and where it came from, or None and why not."""
    sizes = [call for call in regions.size_calls if call.method == "set_size_inches"]
    if sizes:
        last = sizes[-1]
        if not isinstance(last.value, tuple):
            return None, f"set_size_inches at {last.span.lines()} is not a pair of numeric literals"
        return last.value, f"set_size_inches at {last.span.lines()}"
    keywords = [call.figsize for call in regions.figure_calls if call.figsize is not None]
    if not keywords:
        return None, "no figsize= on a figure creation call and no set_size_inches"
    values: set[tuple[Number, Number]] = set()
    for keyword in keywords:
        size = _size_value(keyword.value) if keyword.literal else None
        if size is None:
            return None, f"figsize= at {keyword.span.lines()} is not a pair of numeric literals"
        values.add(size)
    if len(values) > 1:
        return None, f"{len(values)} different figsize= values"
    return values.pop(), f"figsize= at {keywords[0].span.lines()}"


def effective_dpi(regions: Regions, call: SavefigCall) -> tuple[Number | None, str]:
    """The dpi `call` saves at: its own `dpi=`, else the figure's (`set_dpi`, creation `dpi=`, 100)."""
    if call.dpi is not None:
        value = as_number(call.dpi.value) if call.dpi.literal else None
        if value is None:
            return None, f"savefig dpi= at {call.dpi.span.lines()} is not a numeric literal"
        return value, "savefig dpi="
    set_dpi = [c for c in regions.size_calls if c.method == "set_dpi" and c.span.start < call.span.start]
    if set_dpi:
        value = as_number(set_dpi[-1].value)
        return value, "set_dpi" if value is not None else "set_dpi is not a numeric literal"
    created = [c.dpi for c in regions.figure_calls if c.dpi is not None]
    if created:
        value = as_number(created[-1].value) if created[-1].literal else None
        return value, "figure dpi=" if value is not None else "figure dpi= is not a numeric literal"
    return DEFAULT_DPI, "matplotlib default"


def measure_canvas(code: str, *, library: str = "matplotlib") -> Canvas:
    """The canvas `code` renders, judged from its literals; raises `SyntaxError` if it does not parse.

    matplotlib's figure size times dpi, pygal's chart or `svg2png` output size and
    lets-plot's plot size times the save's scale can be read (`SaveRule.canvas`); for
    plotnine and altair the canvas is a note that the render relies on the R3 gate.
    """
    kind = save_rule(library).canvas
    if kind == "pygal":
        return _measure_pygal(code)
    if kind == "letsplot":
        return _measure_letsplot(code)
    if kind != "figure":
        return Canvas(
            None, None, None, None, f"{library} sizes its canvas on the save, not through a matplotlib figure"
        )
    regions = find_regions(code, library=library)
    size, size_source = figure_size(regions)
    call = regions.savefig or (regions.savefig_calls[-1] if regions.savefig_calls else None)
    if call is None:
        return Canvas(size, None, None, None, "no savefig call")
    dpi, dpi_source = effective_dpi(regions, call)
    if size is None:
        return Canvas(None, dpi, None, None, size_source)
    if dpi is None:
        return Canvas(size, None, None, None, dpi_source)
    pixels = _pixels(size, dpi)
    target = _nearest_target(pixels)
    for keyword in call.keywords:
        if keyword.name == "bbox_inches" and not (keyword.literal and keyword.value is None):
            note = f"savefig bbox_inches= at {keyword.span.lines()} crops the {pixels[0]}x{pixels[1]} canvas"
            return Canvas(size, dpi, pixels, target, note)
        if keyword.name == "**":
            return Canvas(size, dpi, pixels, target, "savefig takes **kwargs, which may override the canvas")
    if pixels != target:
        note = f"figsize {_fmt_size(size)} at dpi {dpi} renders {pixels[0]}x{pixels[1]}, target {target[0]}x{target[1]}"
        return Canvas(size, dpi, pixels, target, note)
    return Canvas(size, dpi, pixels, target, None)


def plan_dpi(size: tuple[Number, Number]) -> tuple[tuple[int, int], str] | str:
    """The target and dpi literal that render `size` on a canvas, or a note why none does.

    An exact hit is preferred (an integer dpi before a decimal); failing that, a dpi
    that renders one side exactly and the other within `TOLERANCE`.
    """
    width, height = float(size[0]), float(size[1])
    if not (width > 0 and height > 0 and math.isfinite(width) and math.isfinite(height)):
        return f"figsize {_fmt_size(size)} is not a positive size"
    plan = _plan_factor(size)
    if plan is not None:
        return plan[0], plan[1]
    return (
        f"figsize {_fmt_size(size)} has aspect {width / height:.3f}; no dpi renders 3200x1800 (16:9) "
        f"or 2400x2400 (1:1) within {TOLERANCE} px without changing the figure size"
    )


def _plan_factor(size: tuple[Number, Number]) -> tuple[tuple[int, int], str, bool] | None:
    """The target, the factor literal that renders the positive `size` on it when truncated, and whether exactly.

    matplotlib's dpi and lets-plot's scale are such a factor. An exact hit is preferred
    (an integer before a decimal); failing that, a factor that renders one side exactly
    and the other within `TOLERANCE`. None when neither target is reached.
    """
    width, height = float(size[0]), float(size[1])
    ordered = sorted(TARGETS, key=lambda t: abs(math.log((width / height) / (t[0] / t[1]))))

    for target in ordered:
        tw, th = target

        def exact(d: float, t: tuple[int, int] = target) -> bool:
            return _pixels((width, height), d) == t

        low = max(Fraction(tw) / Fraction(width), Fraction(th) / Fraction(height))
        high = min(Fraction(tw + 1) / Fraction(width), Fraction(th + 1) / Fraction(height))
        literal = _nicest(low, high, exact)
        if literal is not None:
            return target, literal, True

    for target in ordered:
        tw, th = target

        def near(d: float, t: tuple[int, int] = target) -> bool:
            pw, ph = _pixels((width, height), d)
            return abs(pw - t[0]) <= TOLERANCE and abs(ph - t[1]) <= TOLERANCE

        for side, pixels in ((width, tw), (height, th)):
            literal = _nicest(Fraction(pixels) / Fraction(side), Fraction(pixels + 1) / Fraction(side), near)
            if literal is not None:
                return target, literal, False
    return None


def _pixels(size: tuple[Number, Number], dpi: float) -> tuple[int, int]:
    return int(float(size[0]) * dpi), int(float(size[1]) * dpi)


def _nearest_target(pixels: tuple[int, int]) -> tuple[int, int]:
    return min(TARGETS, key=lambda t: abs(pixels[0] - t[0]) + abs(pixels[1] - t[1]))


def _nicest(low: Fraction, high: Fraction, accept: Callable[[float], bool]) -> str | None:
    """The shortest decimal literal in `[low, high)` that `accept`s, an integer first."""
    if low >= high:
        return None
    for decimals in range(MAX_DPI_DECIMALS + 1):
        scale = 10**decimals
        numerator = math.ceil(low * scale)
        if Fraction(numerator, scale) >= high:
            continue
        literal = str(numerator) if decimals == 0 else f"{numerator // scale}.{numerator % scale:0{decimals}d}"
        if decimals and literal.endswith("0"):
            continue  # the same value was tried with fewer decimals
        if accept(float(literal)):
            return literal
    return None


def _size_value(value: object) -> tuple[Number, Number] | None:
    if not isinstance(value, tuple | list) or len(value) != 2:
        return None
    width, height = as_number(value[0]), as_number(value[1])
    return (width, height) if width is not None and height is not None else None


def _fmt_size(size: tuple[Number, Number]) -> str:
    return f"({size[0]:g}, {size[1]:g})"


def _same_dpi(value: object, literal: str, size: tuple[Number, Number], target: tuple[int, int]) -> bool:
    """Whether an existing dpi literal already renders `size` exactly on `target`."""
    number = as_number(value)
    return number is not None and (number == float(literal) or _pixels(size, number) == target)


def _normalise_canvas(code: str, *, library: str) -> StepResult:
    kind = save_rule(library).canvas
    if kind == "pygal":
        return _pygal_canvas(code)
    if kind == "letsplot":
        return _letsplot_canvas(code)
    if kind != "figure":
        note = f"canvas: {library} sizes its canvas on the save, not through a matplotlib figure; nothing to rewrite"
        return code, [], [note]
    regions = find_regions(code, library=library)
    index = SourceIndex(code)
    if not regions.savefig_calls:
        return code, [], ["canvas: no savefig call; nothing to normalise"]
    size, source = figure_size(regions)
    if size is None:
        return code, [], [f"canvas: {source}; bbox_inches and dpi left unchanged"]
    plan = plan_dpi(size)
    if isinstance(plan, str):
        return code, [], [f"canvas: {plan}; bbox_inches and dpi left unchanged"]
    target, literal = plan
    if any(call.has_splat for call in regions.savefig_calls):
        return code, [], ["canvas: savefig takes *args or **kwargs; bbox_inches and dpi left unchanged"]

    edits: list[TextEdit] = []
    changes: list[str] = []
    for call in regions.savefig_calls:
        dropped = [kw for kw in call.keywords if kw.name in DROPPED_SAVEFIG_KEYWORDS]
        for keyword in dropped:
            cut = _cut_item(code, index, call.items, keyword.span)
            if cut is None:
                note = f"canvas: cannot cut {keyword.name}= at {keyword.span.lines()} cleanly; left unchanged"
                return code, [], [note]
            edits.append(cut)
            value = code[keyword.value_span.start : keyword.value_span.end]
            changes.append(f"dropped {keyword.name}={value} from savefig at {keyword.span.lines()}")
        if call.dpi is None:
            kept = [item for item in call.items if all(item != kw.span for kw in dropped)]
            at = kept[-1].end if kept else call.span.end - 1
            edits.append((at, at, f", dpi={literal}" if kept else f"dpi={literal}"))
            changes.append(f"added dpi={literal} to savefig at {call.span.lines()}")
        elif not (call.dpi.literal and _same_dpi(call.dpi.value, literal, size, target)):
            edits.append((call.dpi.value_span.start, call.dpi.value_span.end, literal))
            old = code[call.dpi.value_span.start : call.dpi.value_span.end]
            changes.append(f"savefig dpi {old} -> {literal} at {call.dpi.span.lines()}")
    for figure in regions.figure_calls:
        if figure.dpi is not None and figure.dpi.literal and not _same_dpi(figure.dpi.value, literal, size, target):
            edits.append((figure.dpi.value_span.start, figure.dpi.value_span.end, literal))
            changes.append(f"{figure.func} dpi -> {literal} at {figure.dpi.span.lines()}")
    for setter in regions.size_calls:
        if setter.method == "set_dpi" and setter.value is not None and setter.value_span is not None:
            if not _same_dpi(setter.value, literal, size, target):
                edits.append((setter.value_span.start, setter.value_span.end, literal))
                changes.append(f"{setter.func} -> {literal} at {setter.span.lines()}")
    if not edits:
        return code, [], []
    try:
        new_code = _apply(code, edits)
    except ValueError:
        return code, [], ["canvas: the savefig rewrites overlap; bbox_inches and dpi left unchanged"]
    pixels = _pixels(size, float(literal))
    rendered = f"{pixels[0]}x{pixels[1]}"
    if pixels != target:
        rendered += f", within {TOLERANCE} px of {target[0]}x{target[1]}"
    changes.append(f"canvas: figsize {_fmt_size(size)} at dpi {literal} renders {rendered}")
    return new_code, changes, []


def _cut_item(code: str, index: SourceIndex, items: tuple[Span, ...], item: Span) -> TextEdit | None:
    """The deletion that removes one call argument with its separating comma, or None if unsafe."""
    position = items.index(item)
    head = code[index.line_start(item.first_line) : item.start]
    tail = code[item.end : index.line_end(item.last_line)].rstrip("\r\n")
    if not head.strip() and _LINE_TAIL.fullmatch(tail):
        return index.line_start(item.first_line), index.line_end(item.last_line), ""  # alone on its lines
    if position > 0:
        previous = items[position - 1]
        if _COMMA_GAP.fullmatch(code[previous.end : item.start]):
            return previous.end, item.end, ""
        return None
    if position + 1 < len(items):
        following = items[position + 1]
        if _COMMA_GAP.fullmatch(code[item.end : following.start]):
            return item.start, following.start, ""
        return None
    trailing = re.match(r"\s*,?", code[item.end :])
    return item.start, item.end + (trailing.end() if trailing else 0), ""


def _apply(code: str, edits: list[TextEdit]) -> str:
    """Apply character edits; overlapping deletions merge, everything else must be disjoint."""
    deletions = sorted((start, end) for start, end, text in edits if not text)
    merged: list[list[int]] = []
    for start, end in deletions:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    others = [(start, end, text) for start, end, text in edits if text]
    for start, end, _ in others:
        for d_start, d_end in merged:
            if start < d_end and d_start < end:  # for an insertion (start == end): strictly inside
                raise ValueError("overlapping edits")
    ordered = [(start, end, "") for start, end in merged] + others
    for start, end, text in sorted(ordered, key=lambda edit: (edit[0], edit[1]), reverse=True):
        code = code[:start] + text + code[end:]
    return code


def _save_call(tree: ast.Module, index: SourceIndex, save: SavefigCall) -> ast.Call | None:
    """The `ast.Call` of a save call `find_regions` reported."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and node.lineno == save.span.first_line:
            span = index.node_span(node)
            if (span.start, span.end) == (save.span.start, save.span.end):
                return node
    return None


def _keyword_literal(keyword: ast.keyword) -> tuple[object, bool]:
    try:
        return ast.literal_eval(keyword.value), True
    except ValueError, TypeError, SyntaxError, MemoryError, RecursionError:
        return None, False


def _append_keywords(code: str, index: SourceIndex, call: ast.Call, text: str) -> TextEdit:
    """The insertion of `, <text>` after the last argument of `call` (or `<text>` into an empty call)."""
    items: list[ast.expr | ast.keyword] = [*call.args, *call.keywords]
    if not items:
        end = index.node_span(call).end - 1
        return end, end, text
    last = max((index.node_span(item) for item in items), key=lambda span: span.end)
    return last.end, last.end, f", {text}"


# --- pygal canvas ------------------------------------------------------------------------


def _pygal_aliases(tree: ast.Module) -> set[str]:
    return {
        alias.asname or alias.name
        for stmt in tree.body
        if isinstance(stmt, ast.Import)
        for alias in stmt.names
        if alias.name == "pygal"
    }


def _is_pygal_chart(node: ast.AST, aliases: set[str]) -> bool:
    """`pygal.<Chart>(...)`: a call of a capitalised attribute of the pygal module other than `Config`."""
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
        return False
    owner, name = node.func.value, node.func.attr
    return isinstance(owner, ast.Name) and owner.id in aliases and name[:1].isupper() and name not in PYGAL_NOT_CHARTS


def _last_assignment(body: list[ast.stmt], name: str, before: int) -> ast.expr | None:
    """The value of the last module-level `name = ...` above line `before`."""
    values = [
        stmt.value
        for stmt in body
        if isinstance(stmt, ast.Assign)
        and len(stmt.targets) == 1
        and isinstance(stmt.targets[0], ast.Name)
        and stmt.targets[0].id == name
        and stmt.lineno < before
    ]
    return values[-1] if values else None


def _pygal_size(tree: ast.Module, call: ast.Call, name: str) -> tuple[tuple[Number, Number] | None, str]:
    """The size of the chart the PNG save renders and where it came from, or None and why not."""
    aliases = _pygal_aliases(tree)
    node: ast.expr | None = None
    if name == "render_to_png" and isinstance(call.func, ast.Attribute):
        node = call.func.value
    elif name == "svg2png":
        node = next((kw.value for kw in call.keywords if kw.arg == "bytestring"), None)
    seen: set[str] = set()
    chart: ast.Call | None = None
    while node is not None:
        if _is_pygal_chart(node, aliases) and isinstance(node, ast.Call):
            chart = node
            break
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in PYGAL_PASSTHROUGH:
            node = node.func.value
        elif isinstance(node, ast.Name) and node.id not in seen:
            seen.add(node.id)
            node = _last_assignment(tree.body, node.id, call.lineno)
        else:
            node = None
    source = "the saved chart"
    if chart is None:
        charts = [node for node in ast.walk(tree) if _is_pygal_chart(node, aliases) and isinstance(node, ast.Call)]
        if len(charts) != 1:
            return None, f"{len(charts)} pygal charts in the file, none traced from the save at line {call.lineno}"
        chart, source = charts[0], "the file's only chart"
    if chart.args or any(kw.arg is None for kw in chart.keywords):
        return None, f"the chart at line {chart.lineno} takes positional arguments or **kwargs"
    sides: list[Number] = []
    for side, default in zip(("width", "height"), PYGAL_DEFAULT_SIZE, strict=True):
        keyword = next((kw for kw in chart.keywords if kw.arg == side), None)
        value = as_number(_keyword_literal(keyword)[0]) if keyword is not None else default
        if value is None or value <= 0:
            return None, f"the chart's {side}= at line {chart.lineno} is not a positive numeric literal"
        sides.append(value)
    return (sides[0], sides[1]), f"{source} at line {chart.lineno}"


def _pygal_pixels(call: ast.Call, name: str, size: tuple[Number, Number]) -> tuple[int, int] | str:
    """The PNG size the save writes for a chart of `size` (cairosvg's `int(round(...))`), or why it is not known."""
    width, height = float(size[0]), float(size[1])
    if name != "svg2png":
        return round(width), round(height)
    values: dict[str, Number] = {}
    for keyword in call.keywords:
        if keyword.arg in ("output_width", "output_height", "scale"):
            value = as_number(_keyword_literal(keyword)[0])
            if value is None:
                return f"svg2png {keyword.arg}= at line {keyword.lineno} is not a numeric literal"
            values[keyword.arg] = value
    out_width, out_height = values.get("output_width"), values.get("output_height")
    if out_width and out_height:
        return round(out_width), round(out_height)
    if out_width:
        return round(out_width), round(height * out_width / width)
    if out_height:
        return round(width * out_height / height), round(out_height)
    scale = values.get("scale", 1)
    return round(width * scale), round(height * scale)


def _exact_target(size: tuple[Number, Number]) -> tuple[int, int] | None:
    """The target whose aspect `size` has exactly: 16:9 or 1:1."""
    aspect = Fraction(size[0]) / Fraction(size[1])
    return next((target for target in TARGETS if aspect == Fraction(*target)), None)


def _measure_pygal(code: str) -> Canvas:
    tree = ast.parse(code)
    index = SourceIndex(code)
    regions = find_regions(code, tree, library="pygal")
    save = regions.savefig
    call = _save_call(tree, index, save) if save is not None and save.standard_target else None
    if save is None or call is None:
        return Canvas(None, None, None, None, 'no module-level save of f"plot-{THEME}.png"')
    size, source = _pygal_size(tree, call, save.name)
    if size is None:
        return Canvas(None, None, None, None, f"pygal canvas unknown: {source}")
    pixels = _pygal_pixels(call, save.name, size)
    if isinstance(pixels, str):
        return Canvas(None, None, None, None, f"pygal canvas unknown: {pixels}")
    target = _nearest_target(pixels)
    if pixels == target:
        return Canvas(None, None, pixels, target, None)
    note = f"pygal renders {pixels[0]}x{pixels[1]} ({source}), target {target[0]}x{target[1]}"
    return Canvas(None, None, pixels, target, note)


def _svg2png_callee(tree: ast.Module) -> str | None:
    """How the file names cairosvg's `svg2png` (`cairosvg.svg2png`, `_cairosvg.svg2png`, `svg2png`), if it does."""
    for stmt in tree.body:
        if isinstance(stmt, ast.Import):
            for alias in stmt.names:
                if alias.name == CAIROSVG:
                    return f"{alias.asname or alias.name}.svg2png"
        elif isinstance(stmt, ast.ImportFrom) and stmt.module == CAIROSVG and stmt.level == 0:
            for alias in stmt.names:
                if alias.name == "svg2png":
                    return alias.asname or alias.name
    return None


def _import_insertion(tree: ast.Module, index: SourceIndex, module: str) -> tuple[int, int]:
    """Where `import <module>` goes, as `(offset, line)`: in isort order within the block that imports pygal.

    The block is the run of module-level imports on consecutive lines around the first
    pygal import; the new line goes before the first straight import of a module that
    sorts after it, else before the block's first from-import, else after the block.
    """
    body = tree.body
    imports = [stmt for stmt in body if isinstance(stmt, ast.Import | ast.ImportFrom)]
    if not imports:
        docstring = (
            body[0] if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) else None
        )
        line = (docstring.end_lineno or docstring.lineno) + 1 if docstring is not None else 1
        return index.line_start(min(line, index.line_count)), line

    def top(stmt: ast.Import | ast.ImportFrom) -> str:
        name = stmt.names[0].name if isinstance(stmt, ast.Import) else stmt.module or ""
        return name.split(".")[0].lower()

    anchor = next((stmt for stmt in imports if top(stmt) == "pygal"), imports[-1])
    position = body.index(anchor)
    first = last = position
    while first > 0 and isinstance(body[first - 1], ast.Import | ast.ImportFrom):
        if (body[first - 1].end_lineno or 0) + 1 != body[first].lineno:
            break
        first -= 1
    while last + 1 < len(body) and isinstance(body[last + 1], ast.Import | ast.ImportFrom):
        if (body[last].end_lineno or 0) + 1 != body[last + 1].lineno:
            break
        last += 1
    block = [stmt for stmt in body[first : last + 1] if isinstance(stmt, ast.Import | ast.ImportFrom)]
    before: ast.Import | ast.ImportFrom | None = next(
        (stmt for stmt in block if isinstance(stmt, ast.Import) and top(stmt) > module), None
    )
    before = before or next((stmt for stmt in block if isinstance(stmt, ast.ImportFrom)), None)
    if before is not None:
        return index.line_start(before.lineno), before.lineno
    end = block[-1].end_lineno or block[-1].lineno
    return index.line_end(end), end + 1


def _pygal_canvas(code: str) -> StepResult:
    tree = ast.parse(code)
    index = SourceIndex(code)
    regions = find_regions(code, tree, library="pygal")
    save = regions.savefig
    call = _save_call(tree, index, save) if save is not None and save.standard_target else None
    if save is None or call is None:
        return code, [], ['canvas: no module-level save of f"plot-{THEME}.png"; nothing to normalise']
    size, source = _pygal_size(tree, call, save.name)
    if size is None:
        return code, [], [f"canvas: {source}; the PNG size is left as it is"]
    pixels = _pygal_pixels(call, save.name, size)
    if isinstance(pixels, str):
        return code, [], [f"canvas: {pixels}; the PNG size is left as it is"]
    if pixels in TARGETS:
        return code, [], []
    chart = f"pygal chart {size[0]:g}x{size[1]:g} ({source})"
    target = _exact_target(size)
    if target is None:
        return code, [], [f"canvas: {chart} has another aspect than 16:9 or 1:1; the PNG size is left as it is"]
    tw, th = target
    if save.has_splat:
        return code, [], [f"canvas: the save at {save.span.lines()} takes *args or **kwargs; left unchanged"]
    edits: list[TextEdit] = []
    changes: list[str] = []
    callee = _svg2png_callee(tree)
    if save.name == "svg2png":
        sizes = {"output_width": tw, "output_height": th}
        for keyword in call.keywords:
            if keyword.arg in sizes:
                span = index.node_span(keyword.value)
                edits.append((span.start, span.end, str(sizes.pop(keyword.arg))))
        added = [f"{name}={value}" for name, value in sizes.items()]
        if added:
            edits.append(_append_keywords(code, index, call, ", ".join(added)))
        how = f"{save.func}(output_width={tw}, output_height={th})"
    else:
        receiver = call.func.value if isinstance(call.func, ast.Attribute) else None
        extra = [kw for kw in call.keywords if kw.arg not in ("filename", "dpi")]
        if receiver is None or dotted_name(receiver) is None or extra or len(call.args) > 1:
            return code, [], [f"canvas: the {save.name} at {save.span.lines()} has another form; left unchanged"]
        if callee is None:
            callee = f"{CAIROSVG}.svg2png"
            offset, line = _import_insertion(tree, index, CAIROSVG)
            edits.append((offset, offset, f"import {CAIROSVG}{_newline(index, save.span.last_line) or '\n'}"))
            changes.append(f"added import {CAIROSVG} at line {line}")
        dpi = next((kw for kw in call.keywords if kw.arg == "dpi"), None)
        dpi_text = "" if dpi is None else ", " + code[index.node_span(dpi).start : index.node_span(dpi).end]
        receiver_text = code[index.node_span(receiver).start : index.node_span(receiver).end]
        new_call = (
            f"{callee}(bytestring={receiver_text}.render(), write_to={STANDARD_TARGET}{dpi_text}, "
            f"output_width={tw}, output_height={th})"
        )
        span = index.node_span(call)
        edits.append((span.start, span.end, new_call))
        how = f"{callee}(output_width={tw}, output_height={th}) in place of {save.name}"
    changes.append(f"canvas: {chart} renders {pixels[0]}x{pixels[1]}; the save renders {tw}x{th} through {how}")
    return _apply(code, edits), changes, []


# --- lets-plot canvas --------------------------------------------------------------------


def _is_ggsize(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    return (isinstance(func, ast.Name) and func.id == "ggsize") or (
        isinstance(func, ast.Attribute) and func.attr == "ggsize"
    )


def _ggsize_value(call: ast.Call) -> tuple[Number, Number] | None:
    if len(call.args) != 2 or call.keywords:
        return None
    values = [as_number(_literal_value(arg)) for arg in call.args]
    if values[0] is None or values[1] is None or values[0] <= 0 or values[1] <= 0:
        return None
    return values[0], values[1]


def _literal_value(node: ast.expr) -> object:
    try:
        return ast.literal_eval(node)
    except ValueError, TypeError, SyntaxError, MemoryError, RecursionError:
        return None


def _callee_name(func: ast.expr) -> str | None:
    """The last dotted component of a callee: `ggsave` for `ggsave(...)` and `lp.ggsave(...)`."""
    if isinstance(func, ast.Attribute):
        return func.attr
    return func.id if isinstance(func, ast.Name) else None


def _letsplot_plot_size(tree: ast.Module, call: ast.Call) -> tuple[tuple[Number, Number] | None, str]:
    """The `ggsize` of the plot `call` saves and where it came from, or None and why not."""
    subject = call.args[0] if call.args else next((kw.value for kw in call.keywords if kw.arg == "plot"), None)
    seen: set[str] = set()
    value = subject
    while value is not None:
        if isinstance(value, ast.Name):
            if value.id in seen:
                break
            seen.add(value.id)
            value = _last_assignment(tree.body, value.id, call.lineno)
            continue
        sizes: list[ast.Call] = []
        root: ast.expr = value
        while isinstance(root, ast.BinOp) and isinstance(root.op, ast.Add):
            if _is_ggsize(root.right) and isinstance(root.right, ast.Call):
                sizes.append(root.right)  # the rightmost ggsize first: the last one added wins
            root = root.left
        if _is_ggsize(root) and isinstance(root, ast.Call):
            sizes.append(root)
        if sizes:
            size = _ggsize_value(sizes[0])
            where = f"line {sizes[0].lineno}"
            return (size, f"ggsize at {where}") if size else (None, f"ggsize at {where} is not two numeric literals")
        if isinstance(root, ast.Call) and _callee_name(root.func) in LETSPLOT_GRIDS:
            return None, f"{_callee_name(root.func)} at line {root.lineno} has no ggsize of its own"
        value = root if isinstance(root, ast.Name) else None
    literals = {_ggsize_value(node) for node in ast.walk(tree) if isinstance(node, ast.Call) and _is_ggsize(node)}
    grids = any(isinstance(node, ast.Call) and _callee_name(node.func) in LETSPLOT_GRIDS for node in ast.walk(tree))
    if len(literals) == 1 and None not in literals:
        size = literals.pop()
        if size is not None:
            return size, "the file's only ggsize"
    if not literals and not grids:
        return LETSPLOT_DEFAULT_SIZE, "lets-plot's default size"
    sizes_text = f"{len(literals)} distinct ggsize value{'s' if len(literals) != 1 else ''}"
    return None, f"no ggsize on the saved plot; the file has {sizes_text}{' and a grid' if grids else ''}"


def _letsplot_raster(tree: ast.Module, call: ast.Call) -> tuple[tuple[Fraction, Fraction], Number, str] | str:
    """The raster size before `scale=`, the scale in effect and where the size came from; or why it is not known."""
    values: dict[str, object] = {}
    for keyword in call.keywords:
        if keyword.arg in ("scale", "w", "h", "unit", "dpi"):
            value, literal = _keyword_literal(keyword)
            if keyword.arg == "unit":
                valid = isinstance(value, str) and (value in LETSPLOT_PER_INCH or value == "px")
            else:
                number = as_number(value)
                valid = number is not None and number > 0
            if not literal or not valid:
                return f"ggsave {keyword.arg}= at line {keyword.lineno} is not a literal lets-plot takes"
            values[keyword.arg] = value
    scale, dpi = as_number(values.get("scale")), as_number(values.get("dpi"))
    width, height = as_number(values.get("w")), as_number(values.get("h"))
    if (width is None) != (height is None):
        return f"ggsave at line {call.lineno} sets only one of w= and h="
    if width is not None and height is not None:
        unit = str(values.get("unit", "in"))
        source = f"w={width:g}, h={height:g}, unit={unit}"
        if unit == "px":
            return (Fraction(width), Fraction(height)), scale or 1, source
        resolution = dpi or LETSPLOT_DEFAULT_DPI
        per_pixel = LETSPLOT_PER_INCH[unit] * Fraction(resolution)
        size = (Fraction(width) * per_pixel, Fraction(height) * per_pixel)
        return size, scale or 1, f"{source} at dpi {resolution:g}"
    base, source = _letsplot_plot_size(tree, call)
    if base is None:
        return source
    size = (Fraction(base[0]), Fraction(base[1]))
    if dpi is not None:
        factor = Fraction(dpi) / 96
        return (size[0] * factor, size[1] * factor), scale or 1, f"{base[0]:g}x{base[1]:g} ({source}) at dpi {dpi:g}"
    return size, 2 if scale is None else scale, f"{base[0]:g}x{base[1]:g} ({source})"


def _letsplot_pixels(size: tuple[Fraction, Fraction], scale: float) -> tuple[int, int]:
    """lets-plot's raster: each side times the scale, floored (formula probes of 2026-10-26)."""
    return math.floor(float(size[0]) * scale), math.floor(float(size[1]) * scale)


def _letsplot_save(code: str) -> tuple[ast.Module, SourceIndex, SavefigCall, ast.Call] | str:
    tree = ast.parse(code)
    index = SourceIndex(code)
    save = find_regions(code, tree, library="letsplot").savefig
    call = _save_call(tree, index, save) if save is not None and save.standard_target else None
    if save is None or call is None:
        return 'no module-level ggsave of f"plot-{THEME}.png"'
    return tree, index, save, call


def _measure_letsplot(code: str) -> Canvas:
    found = _letsplot_save(code)
    if isinstance(found, str):
        return Canvas(None, None, None, None, found)
    tree, _, _, call = found
    raster = _letsplot_raster(tree, call)
    if isinstance(raster, str):
        return Canvas(None, None, None, None, f"lets-plot canvas unknown: {raster}")
    size, scale, source = raster
    pixels = _letsplot_pixels(size, float(scale))
    target = _nearest_target(pixels)
    if pixels == target:
        return Canvas(None, None, pixels, target, None)
    note = f"lets-plot renders {pixels[0]}x{pixels[1]} from {source} at scale {scale:g}, target {target[0]}x{target[1]}"
    return Canvas(None, None, pixels, target, note)


def _letsplot_canvas(code: str) -> StepResult:
    found = _letsplot_save(code)
    if isinstance(found, str):
        return code, [], [f"canvas: {found}; nothing to normalise"]
    tree, index, save, call = found
    if save.has_splat:
        return code, [], [f"canvas: the ggsave at {save.span.lines()} takes *args or **kwargs; left unchanged"]
    raster = _letsplot_raster(tree, call)
    if isinstance(raster, str):
        return code, [], [f"canvas: {raster}; the render relies on the R3 canvas gate"]
    size, scale, source = raster
    pixels = _letsplot_pixels(size, float(scale))
    if pixels in TARGETS:
        return code, [], []
    rendered = f"{source} at scale {scale:g} renders {pixels[0]}x{pixels[1]}"
    plan = _plan_factor((float(size[0]), float(size[1])))
    if plan is not None:
        target, literal, exact = plan
        how = "" if exact else f", within {TOLERANCE} px of {target[0]}x{target[1]}"
    else:
        target = _nearest_target(pixels)
        if pixels[0] * pixels[1] <= MAX_IMAGE_PIXELS:
            note = f"canvas: {rendered}; no scale renders 3200x1800 or 2400x2400, so the render relies on the R3 gate"
            return code, [], [note]
        fit = min(Fraction(target[0]) / size[0], Fraction(target[1]) / size[1])
        literal = _nicest(fit * Fraction(999, 1000), fit, lambda _: True) or str(float(fit))
        how = f", inside {target[0]}x{target[1]} under R2's pixel cap"
    keyword = next((kw for kw in call.keywords if kw.arg == "scale"), None)
    if keyword is not None:
        span = index.node_span(keyword.value)
        edit: TextEdit = (span.start, span.end, literal)
    else:
        edit = _append_keywords(code, index, call, f"scale={literal}")
    after = _letsplot_pixels(size, float(literal))
    change = f"canvas: {rendered}; scale={literal} renders {after[0]}x{after[1]}{how}"
    return _apply(code, [edit]), [change], []


# --- header and title --------------------------------------------------------------------


def _is_header(stmt: ast.stmt) -> bool:
    if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str)):
        return False
    text = stmt.value.value.strip()
    return bool(text) and text.splitlines()[0].strip() == HEADER_FIRST_LINE


def _strip_header(code: str) -> StepResult:
    """Every catalogue header that opens the file: 3 lets-plot files carry a second one (2026-10-26)."""
    tree = ast.parse(code)
    headers: list[ast.stmt] = []
    for stmt in tree.body:
        if not _is_header(stmt):
            break
        headers.append(stmt)
    if not headers:
        return code, [], []
    index = SourceIndex(code)
    spans = [index.lines_span(stmt) for stmt in headers]
    lines = {line for span in spans for line in range(span.first_line, span.last_line + 1)}
    return _rewrite_lines(code, lines, {}), [f"removed the catalogue header at {span.lines()}" for span in spans], []


def _strip_title(code: str) -> StepResult:
    tree = ast.parse(code)
    in_fstrings = {id(part) for node in ast.walk(tree) if isinstance(node, ast.JoinedStr) for part in node.values}
    index = SourceIndex(code)
    spans = sorted(
        (
            index.node_span(node)
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in in_fstrings
            and _CATALOGUE_TITLE.fullmatch(node.value)
        ),
        key=lambda span: span.start,
    )
    if not spans:
        return code, [], []
    changes = [f"emptied the catalogue title at {span.lines()}" for span in spans]
    return _apply(code, [(span.start, span.end, '""') for span in spans]), changes, []


# --- lets-plot imports -------------------------------------------------------------------


def _alias_span(index: SourceIndex, alias: ast.alias) -> tuple[int, int]:
    end_line, end_col = alias.end_lineno or alias.lineno, alias.end_col_offset or alias.col_offset
    return index.offset(alias.lineno, alias.col_offset), index.offset(end_line, end_col)


def _binding_sites(tree: ast.Module) -> list[tuple[str, int, ast.AST]]:
    """Every place the file binds a name, in any scope: `(name, line, node)`."""
    sites: list[tuple[str, int, ast.AST]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Load):
            sites.append((node.id, node.lineno, node))
        elif isinstance(node, ast.arg):
            sites.append((node.arg, node.lineno, node))
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            sites.append((node.name, node.lineno, node))
        elif isinstance(node, ast.alias) and node.name != "*":
            sites.append(((node.asname or node.name).split(".")[0], node.lineno, node))
        elif isinstance(node, ast.ExceptHandler | ast.MatchAs | ast.MatchStar) and node.name:
            sites.append((node.name, node.lineno, node))
        elif isinstance(node, ast.MatchMapping) and node.rest:
            sites.append((node.rest, node.lineno, node))
        elif isinstance(node, ast.Global | ast.Nonlocal):
            sites.extend((name, node.lineno, node) for name in node.names)
    return sites


def _rename_save_alias(code: str) -> StepResult:
    """`from lets_plot.export import ggsave as export_ggsave` -> `... import ggsave`, every `export_ggsave` too."""
    tree = ast.parse(code)
    saves = [
        alias
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module in LETSPLOT_MODULES
        for alias in node.names
        if alias.name == LETSPLOT_SAVE
    ]
    renamed = [alias for alias in saves if alias.asname not in (None, LETSPLOT_SAVE)]
    if not renamed:
        return code, [], []
    names = {alias.asname for alias in renamed if alias.asname is not None}
    clashes = sorted(
        {
            (name, line)
            for name, line, node in _binding_sites(tree)
            if name in names | {LETSPLOT_SAVE} and not any(node is alias for alias in saves)
        }
    )
    if clashes:
        name, line = clashes[0]
        note = f"save alias: {name} is also bound at line {line}; {', '.join(sorted(names))} left unchanged"
        return code, [], [note]
    index = SourceIndex(code)
    edits: list[TextEdit] = [(*_alias_span(index, alias), LETSPLOT_SAVE) for alias in renamed]
    uses = [node for node in ast.walk(tree) if isinstance(node, ast.Name) and node.id in names]
    edits += [(index.node_span(node).start, index.node_span(node).end, LETSPLOT_SAVE) for node in uses]
    changes = [
        f"import {LETSPLOT_SAVE} as {alias.asname} -> import {LETSPLOT_SAVE} at line {alias.lineno}"
        for alias in renamed
    ]
    if uses:
        changes.append(
            f"{', '.join(sorted(names))} -> {LETSPLOT_SAVE} at line {', '.join(str(n.lineno) for n in uses)}"
        )
    return _apply(code, edits), changes, []


def _global_lookups(code: str) -> tuple[set[str], set[str]]:
    """The names the module looks up as globals and the names its own scope binds, from `symtable`."""
    top = symtable.symtable(code, "plot.py", "exec")
    bound = {s.get_name() for s in top.get_symbols() if s.is_assigned() or s.is_imported() or s.is_namespace()}
    looked_up = {s.get_name() for s in top.get_symbols() if s.is_referenced()}
    tables = list(top.get_children())
    while tables:
        table = tables.pop()
        tables.extend(table.get_children())
        looked_up |= {s.get_name() for s in table.get_symbols() if s.is_referenced() and s.is_global()}
    return looked_up, bound


def _module_bindings(tree: ast.Module) -> dict[str, int]:
    """The first line on which the module scope binds each name (nested function, class and lambda bodies aside)."""
    first: dict[str, int] = {}

    def bind(name: str, line: int) -> None:
        first[name] = min(first.get(name, line), line)

    nodes: list[ast.AST] = list(tree.body)
    while nodes:
        node = nodes.pop()
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            bind(node.name, node.lineno)
            nodes.extend(node.decorator_list)
            if isinstance(node, ast.ClassDef):
                nodes.extend([*node.bases, *node.keywords])
            else:
                nodes.extend([*node.args.defaults, *(d for d in node.args.kw_defaults if d is not None)])
            continue
        if isinstance(node, ast.Lambda):
            nodes.extend([*node.args.defaults, *(d for d in node.args.kw_defaults if d is not None)])
            continue
        if isinstance(node, ast.ListComp | ast.SetComp | ast.DictComp | ast.GeneratorExp):
            nodes.extend(n.target for n in ast.walk(node) if isinstance(n, ast.NamedExpr))  # `:=` binds outside
            nodes.append(node.generators[0].iter)
            continue
        if isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Load):
            bind(node.id, node.lineno)
        elif isinstance(node, ast.alias) and node.name != "*":
            bind((node.asname or node.name).split(".")[0], node.lineno)
        elif isinstance(node, ast.ExceptHandler | ast.MatchAs | ast.MatchStar) and node.name:
            bind(node.name, node.lineno)
        elif isinstance(node, ast.MatchMapping) and node.rest:
            bind(node.rest, node.lineno)
        nodes.extend(ast.iter_child_nodes(node))
    return first


def _import_order(name: str) -> tuple[int, str, str]:
    """ruff's isort order-by-type: CONSTANT_CASE, then CamelCase, then the rest, case-insensitive within each."""
    group = 0 if name.isupper() and len(name) > 1 else 1 if name[:1].isupper() else 2
    return group, name.lower(), name


def _expand_star_import(code: str) -> StepResult:
    """`from lets_plot import *` -> `from lets_plot import (...)` of the names the module takes from it."""
    tree = ast.parse(code)
    stars = [
        node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and any(a.name == "*" for a in node.names)
    ]
    lets_plot = [star for star in stars if star.module == "lets_plot" and star.level == 0]
    if not lets_plot:
        return code, [], []
    star = lets_plot[0]
    where = f"the star import at line {star.lineno} stays"
    if len(stars) > 1:
        return code, [], [f"star import: the file has {len(stars)} star imports; {where}"]
    if not any(star is stmt for stmt in tree.body):
        return code, [], [f"star import: it is not a module-level statement; {where}"]
    globals_ = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Global)]
    if globals_:
        return code, [], [f"star import: a global statement at line {globals_[0]}; {where}"]
    try:
        looked_up, bound = _global_lookups(code)
    except SyntaxError as exc:
        return code, [], [f"star import: symtable refuses line {exc.lineno}; {where}"]
    first = _module_bindings(tree)
    early = sorted(
        {
            node.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and node.id in LETS_PLOT_NAMES
            and node.id in bound
            and node.lineno < first.get(node.id, math.inf)
        }
    )
    if early:
        return code, [], [f"star import: {', '.join(early)} is read before the file binds it; {where}"]
    index = SourceIndex(code)
    span = index.lines_span(star)
    statement = index.node_span(star)
    rest = code[statement.end : span.end].strip()
    if code[span.start : statement.start].strip() or (rest and not rest.startswith("#")):
        return code, [], [f"star import: it shares its line with other code; {where}"]
    names = sorted((looked_up - bound) & LETS_PLOT_NAMES, key=_import_order)
    if not names:
        lines = set(range(span.first_line, span.last_line + 1))
        return _rewrite_lines(code, lines, {}), [f"removed the unused `from lets_plot import *` at {span.lines()}"], []
    newline = _newline(index, span.last_line) or "\n"
    text = f"from lets_plot import ({newline}" + "".join(f"    {name},{newline}" for name in names) + f"){newline}"
    change = f"from lets_plot import * -> {len(names)} names at {span.lines()}"
    return _rewrite_lines(code, set(), {span.first_line: (span.last_line, text)}), [change], []


# --- lets-plot save directory ------------------------------------------------------------


def _letsplot_save_paths(code: str) -> StepResult:
    """`path="."` on every `ggsave` of a theme target; a computed `path=` becomes `"."`."""
    rule = save_rule("letsplot")
    directory = f'"{rule.directory}"'
    tree = ast.parse(code)
    index = SourceIndex(code)
    edits: list[TextEdit] = []
    changes: list[str] = []
    notes: list[str] = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and _callee_name(node.func) in rule.names):
            continue
        name = _callee_name(node.func) or LETSPLOT_SAVE
        target = save_target(node, rule, name)
        if target is None or not (is_theme_target(target, PNG_SUFFIX) or is_theme_target(target, HTML_SUFFIX)):
            continue
        line = f"line {node.lineno}"
        if any(kw.arg is None for kw in node.keywords):
            notes.append(f"save directory: the {name} at {line} takes **kwargs; left unchanged")
            continue
        path = next((kw for kw in node.keywords if kw.arg == "path"), None)
        if path is None:
            anchor = next((kw for kw in node.keywords if kw.value is target), None)
            end = index.node_span(anchor if anchor is not None else target).end
            edits.append((end, end, f", path={directory}"))
            changes.append(f"added path={directory} to {name} at {line}")
        elif not isinstance(path.value, ast.Constant) or path.value.value is None:  # None is lets-plot's default
            span = index.node_span(path.value)
            edits.append((span.start, span.end, directory))
            changes.append(f"{name} path={_WHITESPACE.sub(' ', code[span.start : span.end])} -> {directory} at {line}")
        elif path.value.value != rule.directory:
            notes.append(f"save directory: the {name} at {line} saves into path={path.value.value!r}; left unchanged")
    if not edits:
        return code, [], notes
    return _apply(code, edits), changes, notes


def _import_targets(body: list[ast.stmt]) -> dict[str, str]:
    """Local name -> the dotted module or object a module-level import binds it to."""
    targets: dict[str, str] = {}
    for stmt in body:
        if isinstance(stmt, ast.Import):
            for alias in stmt.names:
                if alias.asname:
                    targets[alias.asname] = alias.name
                else:
                    targets[alias.name.split(".")[0]] = alias.name.split(".")[0]
        elif isinstance(stmt, ast.ImportFrom) and stmt.module and stmt.level == 0:
            for alias in stmt.names:
                targets[alias.asname or alias.name] = f"{stmt.module}.{alias.name}"
    return targets


def _resolved(func: ast.expr, imports: dict[str, str]) -> str | None:
    name = dotted_name(func)
    if name is None:
        return None
    head, _, rest = name.partition(".")
    base = imports.get(head, head)
    return f"{base}.{rest}" if rest else base


def _strip_letsplot_epilogue(code: str) -> StepResult:
    """Remove what moves, copies or deletes the files lets-plot wrote into `./lets-plot-images`."""
    rule = save_rule("letsplot")
    tree = ast.parse(code)
    body = tree.body
    imports = _import_targets(body)

    def has_save(node: ast.AST) -> bool:
        return any(isinstance(n, ast.Call) and _callee_name(n.func) in rule.names for n in ast.walk(node))

    def mentions(node: ast.AST, names: set[str]) -> bool:
        return any(
            (isinstance(n, ast.Constant) and isinstance(n.value, str) and LETSPLOT_IMAGES in n.value)
            or (isinstance(n, ast.Name) and n.id in names)
            for n in ast.walk(node)
        )

    def only_moves(stmt: ast.stmt) -> bool:
        for node in ast.walk(stmt):
            if isinstance(node, ast.Call):
                method = node.func.attr if isinstance(node.func, ast.Attribute) else None
                if _resolved(node.func, imports) not in EPILOGUE_CALLS and method not in EPILOGUE_METHODS:
                    return False
            elif isinstance(node, ast.Import):
                if not all(alias.name in EPILOGUE_MODULES for alias in node.names):
                    return False
            elif isinstance(node, ast.ExceptHandler):
                if not all(isinstance(inner, ast.Pass) for inner in node.body):
                    return False
            elif isinstance(node, ast.stmt) and not isinstance(
                node, ast.If | ast.For | ast.Try | ast.Expr | ast.Assign | ast.Pass
            ):
                return False
        return True

    images: set[str] = set()  # names bound to the directory or to a path inside it
    returned: dict[str, ast.Assign] = {}  # `png_path = ggsave(...)`
    for stmt in body:
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            name = stmt.targets[0].id
            if isinstance(stmt.value, ast.Call) and _callee_name(stmt.value.func) in rule.names:
                returned[name] = stmt
            elif mentions(stmt.value, images) and only_moves(stmt):
                images.add(name)
    removed: set[int] = set()
    epilogue: list[ast.stmt] = []
    for stmt in body:
        if has_save(stmt) or _assigned(stmt) & images:
            continue
        if mentions(stmt, images | set(returned)) and only_moves(stmt):
            removed.add(id(stmt))
            epilogue.append(stmt)
    loads = {id(stmt): _loads(stmt) for stmt in body}

    def kept_loads(skip: ast.stmt | None = None) -> set[str]:
        return set().union(*(loads[id(s)] for s in body if s is not skip and id(s) not in removed))

    names_gone: list[ast.stmt] = []
    grown = True
    while grown:  # the directory names, once nothing kept reads them
        grown = False
        for stmt in body:
            if id(stmt) in removed or not (_assigned(stmt) and _assigned(stmt) <= images):
                continue
            if not _assigned(stmt) & kept_loads(stmt):
                removed.add(id(stmt))
                names_gone.append(stmt)
                grown = True
    unwrapped = [stmt for name, stmt in returned.items() if name not in kept_loads(stmt)]
    imports_gone = [
        stmt
        for stmt in body
        if isinstance(stmt, ast.Import)
        and all(alias.name == "shutil" for alias in stmt.names)
        and not _import_bindings(stmt)[0] & kept_loads()
    ]
    removed.update(id(stmt) for stmt in imports_gone)
    notes = [
        f"save epilogue: the statement at line {stmt.lineno} uses {LETSPLOT_IMAGES} in other ways; left in place"
        for stmt in body
        if id(stmt) not in removed and not has_save(stmt) and mentions(stmt, images)
    ]
    if not removed and not unwrapped:
        return code, [], notes

    index = SourceIndex(code)
    remove: set[int] = set()
    changes: list[str] = []
    for stmt in body:
        if id(stmt) not in removed:
            continue
        span = index.lines_span(stmt)
        remove |= _with_comments(index, span)
        if stmt in epilogue:
            label = "the lets-plot-images epilogue"
        elif stmt in imports_gone:
            label = f"the unused `{ast.unparse(stmt)}`"
        else:
            label = f"the unused lets-plot-images name {', '.join(sorted(_assigned(stmt)))}"
        changes.append(f"removed {label} at {span.lines()}")
    replace: dict[int, tuple[int, str]] = {}
    for stmt in unwrapped:
        span = index.lines_span(stmt)
        value = index.node_span(stmt.value)
        replace[span.first_line] = (span.last_line, code[value.start : span.end])
        changes.append(
            f"{ast.unparse(stmt.targets[0])} = {LETSPLOT_SAVE}(...) -> {LETSPLOT_SAVE}(...) at {span.lines()}"
        )
    return _rewrite_lines(code, remove, replace), changes, notes


# --- pygal HTML and SVG writes -----------------------------------------------------------


def _open_mode(call: ast.Call) -> str | None:
    """The literal mode of an `open(...)` call, "r" when it has none, None when it is not a literal."""
    mode = call.args[1] if len(call.args) > 1 else next((kw.value for kw in call.keywords if kw.arg == "mode"), None)
    if mode is None:
        return "r"
    return mode.value if isinstance(mode, ast.Constant) and isinstance(mode.value, str) else None


def _theme_path(node: ast.expr, suffix: str) -> bool:
    return is_theme_target(node, suffix) or _theme_file_path(node, suffix)


def _is_call(node: ast.AST, attribute: str) -> bool:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == attribute


def _render_receiver(value: ast.expr, mode: str) -> ast.expr | None:
    """`X` when `value` is what `X.render_to_file` writes in `mode`: `X.render()` for "wb", `X.render(is_unicode=True)`
    or `X.render().decode(["utf-8"])` for "w"; `X` must be a name or a dotted name."""
    receiver: ast.expr | None = None
    if mode == "wb" and _is_call(value, "render") and isinstance(value, ast.Call):
        if not value.args and not value.keywords and isinstance(value.func, ast.Attribute):
            receiver = value.func.value
    elif mode == "w" and isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute):
        if value.func.attr == "render" and not value.args and len(value.keywords) == 1:
            keyword = value.keywords[0]
            if keyword.arg == "is_unicode" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                receiver = value.func.value
        elif value.func.attr == "decode" and not value.keywords and len(value.args) <= 1:
            utf8 = not value.args or (
                isinstance(value.args[0], ast.Constant) and str(value.args[0].value).lower() in ("utf-8", "utf8")
            )
            inner = value.func.value
            if utf8 and _is_call(inner, "render") and isinstance(inner, ast.Call):
                if not inner.args and not inner.keywords and isinstance(inner.func, ast.Attribute):
                    receiver = inner.func.value
    return receiver if receiver is not None and dotted_name(receiver) is not None else None


def _pygal_html_writes(code: str) -> StepResult:
    """`_pygal_html_once` until it changes nothing: a removed feeder can free a target that was named again."""
    changes: list[str] = []
    while True:
        new_code, step_changes, notes = _pygal_html_once(code)
        if new_code == code:
            return code, changes, notes
        try:
            ast.parse(new_code)
        except SyntaxError:
            return code, changes, [*notes, "html: the rewrite would not parse; left unchanged"]
        code = new_code
        changes.extend(step_changes)


def _pygal_html_once(code: str) -> StepResult:
    rule = save_rule("pygal")
    tree = ast.parse(code)
    index = SourceIndex(code)
    remove: set[int] = set()
    replace: dict[int, tuple[int, str]] = {}
    changes: list[str] = []
    notes: list[str] = []
    dropped: list[ast.stmt] = []

    def named_again(target: ast.expr, stmt: ast.stmt) -> bool:
        text = ast.dump(target)
        return any(
            ast.dump(node) == text
            for other in tree.body
            if other is not stmt
            for node in ast.walk(other)
            if isinstance(node, ast.expr)
        )

    for stmt in tree.body:
        span = index.lines_span(stmt)
        if isinstance(stmt, ast.Expr) and _is_call(stmt.value, "render_to_file") and isinstance(stmt.value, ast.Call):
            target = save_target(stmt.value, rule, "render_to_file")
            if target is None or not _theme_path(target, SVG_SUFFIX):
                continue
            if named_again(target, stmt):
                notes.append(f"html: the SVG save at {span.lines()} is read again elsewhere; left in place")
            else:
                remove |= _with_comments(index, span)
                changes.append(f"removed the SVG save at {span.lines()}")
            continue
        write = _theme_write(stmt)
        if write is None:
            continue
        target, suffix, mode, utf8, values = write
        receiver = _render_receiver(values[0], mode) if suffix == HTML_SUFFIX and len(values) == 1 and utf8 else None
        kind = suffix.removeprefix(".").upper()
        if receiver is not None:
            name = code[index.node_span(receiver).start : index.node_span(receiver).end]
            indent = index.line_text(span.first_line)[: stmt.col_offset]
            text = f"{indent}{name}.render_to_file({HTML_TARGET}){_newline(index, span.last_line)}"
            replace[span.first_line] = (span.last_line, text)
            changes.append(f"the HTML write through open() at {span.lines()} -> {name}.render_to_file({HTML_TARGET})")
        elif not named_again(target, stmt):
            remove |= _with_comments(index, span)
            dropped.append(stmt)
            changes.append(f"removed the {kind} write through open() at {span.lines()}")
        else:
            notes.append(
                f"html: the {kind} write through open() at {span.lines()} is read again elsewhere; left in place"
            )

    # The module-level assignments that only fed a removed write (the page around the SVG), until none is left.
    gone = {id(stmt) for stmt in dropped}
    candidates = set().union(*(_loads(stmt) for stmt in dropped))
    grown = bool(dropped)
    while grown:
        grown = False
        for stmt in tree.body:
            if id(stmt) in gone or not isinstance(stmt, ast.Assign | ast.AugAssign):
                continue
            targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
            if not all(isinstance(target, ast.Name) for target in targets):
                continue
            names = {target.id for target in targets if isinstance(target, ast.Name)}
            if not names <= candidates or any(
                _callee_name(n.func) in rule.names for n in ast.walk(stmt) if isinstance(n, ast.Call)
            ):
                continue
            if names & set().union(
                *(_loads(other) for other in tree.body if id(other) not in gone and other is not stmt)
            ):
                continue
            gone.add(id(stmt))
            span = index.lines_span(stmt)
            remove |= _with_comments(index, span)
            candidates |= _loads(stmt)
            changes.append(f"removed {', '.join(sorted(names))}, which only fed a removed write, at {span.lines()}")
            grown = True
    if not remove and not replace:
        return code, [], notes
    return _rewrite_lines(code, remove, replace), changes, notes


def _theme_write(stmt: ast.stmt) -> tuple[ast.expr, str, str, bool, list[ast.expr]] | None:
    """`(target, suffix, mode, utf8, values)` for `with open(<theme .html or .svg path>, "w"|"wb") as f:` whose body
    only writes to `f` (`values` are what it writes), else None."""
    if not (isinstance(stmt, ast.With) and len(stmt.items) == 1):
        return None
    item = stmt.items[0]
    call = item.context_expr
    if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == "open"):
        return None
    if not call.args or len(call.args) > 2 or any(kw.arg not in ("mode", "encoding") for kw in call.keywords):
        return None
    target = call.args[0]
    suffix = next((suffix for suffix in (HTML_SUFFIX, SVG_SUFFIX) if _theme_path(target, suffix)), None)
    mode = _open_mode(call)
    handle = item.optional_vars.id if isinstance(item.optional_vars, ast.Name) else None
    if suffix is None or mode not in ("w", "wb") or handle is None:
        return None
    values: list[ast.expr] = []
    for inner in stmt.body:
        if not (isinstance(inner, ast.Expr) and _is_call(inner.value, "write") and isinstance(inner.value, ast.Call)):
            return None
        write = inner.value
        if not (isinstance(write.func, ast.Attribute) and isinstance(write.func.value, ast.Name)):
            return None
        if write.func.value.id != handle or len(write.args) != 1 or write.keywords:
            return None
        values.append(write.args[0])
    encodings = [kw.value for kw in call.keywords if kw.arg == "encoding"]
    utf8 = all(isinstance(e, ast.Constant) and str(e.value).lower() in ("utf-8", "utf8") for e in encodings)
    return target, suffix, mode, utf8, values


# --- guards and file paths ---------------------------------------------------------------


def _loads(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}


def _with_comments(index: SourceIndex, span: Span) -> set[int]:
    """The lines of `span` and the comment lines directly above it."""
    lines = set(range(span.first_line, span.last_line + 1))
    line = span.first_line - 1
    while line >= 1 and index.line_text(line).lstrip().startswith("#"):
        lines.add(line)
        line -= 1
    return lines


def _sys_aliases(body: list[ast.stmt]) -> set[str]:
    """The names `sys` is imported as."""
    return {
        alias.asname or alias.name
        for stmt in body
        if isinstance(stmt, ast.Import)
        for alias in stmt.names
        if alias.name == "sys"
    }


def _is_sys_path(node: ast.expr, aliases: set[str]) -> bool:
    """`sys.path` (under any name `sys` is imported as) or a subscript of it."""
    if isinstance(node, ast.Subscript):
        node = node.value
    name = dotted_name(node)
    return name is not None and any(name == f"{alias}.path" for alias in aliases)


def _mentions_sys_path(node: ast.AST, aliases: set[str]) -> bool:
    return any(isinstance(n, ast.Attribute) and _is_sys_path(n, aliases) for n in ast.walk(node))


def _inner(stmt: ast.If | ast.For | ast.While | ast.Try) -> list[ast.stmt]:
    statements = [*stmt.body, *stmt.orelse]
    if isinstance(stmt, ast.Try):
        statements += [*stmt.finalbody, *(inner for handler in stmt.handlers for inner in handler.body)]
    return statements


def _assigned(stmt: ast.stmt) -> set[str]:
    """The names a plain assignment binds (`a = b = ...`, `a: T = ...`); empty for anything else."""
    if isinstance(stmt, ast.Assign) and all(isinstance(target, ast.Name) for target in stmt.targets):
        return {target.id for target in stmt.targets if isinstance(target, ast.Name)}
    if isinstance(stmt, ast.AnnAssign) and stmt.value is not None and isinstance(stmt.target, ast.Name):
        return {stmt.target.id}
    return set()


def _binds(stmt: ast.stmt) -> set[str]:
    """Names bound by an assignment, or by an `if` or `try` made only of assignments and `pass`."""
    if isinstance(stmt, ast.If | ast.Try):
        inner = _inner(stmt)
        if not all(isinstance(s, ast.Pass) or _assigned(s) for s in inner):
            return set()
        return set().union(*(_assigned(s) for s in inner))
    return _assigned(stmt)


def _is_guard(stmt: ast.stmt, aliases: set[str]) -> bool:
    """A statement that only changes `sys.path` or `sys.modules` (compound ones may hold private helpers and `pass`).

    `del sys.modules[...]` and `sys.dont_write_bytecode = ...` serve the guard too
    (pygal's indicator-rsi and plotnine's spiral-timeseries, 2026-10-26).
    """
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
        callee = dotted_name(stmt.value.func)
        return callee is not None and any(
            callee.startswith((f"{alias}.path.", f"{alias}.modules.")) for alias in aliases
        )
    if isinstance(stmt, ast.Delete):
        modules = {f"{alias}.modules" for alias in aliases}
        return all(isinstance(t, ast.Subscript) and dotted_name(t.value) in modules for t in stmt.targets)
    if isinstance(stmt, ast.Assign):
        flags = {f"{alias}.dont_write_bytecode" for alias in aliases}
        if all(dotted_name(target) in flags for target in stmt.targets):
            return True
        return all(_is_sys_path(target, aliases) for target in stmt.targets)
    if isinstance(stmt, ast.AugAssign):
        return _is_sys_path(stmt.target, aliases)
    if isinstance(stmt, ast.If | ast.For | ast.While | ast.Try):
        inner = _inner(stmt)
        helper = [
            isinstance(s, ast.Pass) or bool(_assigned(s)) and all(n.startswith("_") for n in _assigned(s))
            for s in inner
        ]
        guards = [_is_guard(s, aliases) for s in inner]
        return any(guards) and all(g or h for g, h in zip(guards, helper, strict=True))
    return False


def _module_aliases(body: list[ast.stmt], module: str) -> set[str]:
    """Names that refer to `module` or to an object imported from it."""
    names: set[str] = set()
    for stmt in body:
        if isinstance(stmt, ast.Import):
            names |= {alias.asname or alias.name for alias in stmt.names if alias.name == module}
        elif isinstance(stmt, ast.ImportFrom) and stmt.module == module and stmt.level == 0:
            names |= {alias.asname or alias.name for alias in stmt.names}
    return names


def _computes_path(stmt: ast.stmt, path_names: set[str], os_names: set[str], pathlib_names: set[str]) -> bool:
    """Whether a statement computes a file location: `__file__`, `os.path.*`, `os.getcwd()`, `pathlib`."""
    for node in ast.walk(stmt):
        if isinstance(node, ast.Name):
            if node.id == "__file__" or (isinstance(node.ctx, ast.Load) and node.id in path_names):
                return True
        elif isinstance(node, ast.Call):
            parts = (dotted_name(node.func) or "").split(".")
            if parts[0] in pathlib_names:
                return True
            if parts[0] in os_names and len(parts) >= 2 and parts[1] in ("path", "getcwd"):
                return True
    return False


def _theme_file_path(node: ast.expr, suffix: str = PNG_SUFFIX) -> bool:
    """A path whose file name is `f"plot-{THEME}<suffix>"`: `os.path.join(d, f)`, `d / f`, `str(d / f)`, `f"{d}/..."`."""
    if isinstance(node, ast.JoinedStr):
        return _directory_fstring(node, suffix)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return is_theme_target(node.right, suffix)
    if isinstance(node, ast.Call) and not node.keywords:
        callee = dotted_name(node.func) or ""
        if callee.endswith("path.join") and len(node.args) >= 2:
            return is_theme_target(node.args[-1], suffix)
        if callee in ("str", "os.fspath") and len(node.args) == 1:
            return _theme_file_path(node.args[0], suffix)
    return False


def _directory_fstring(node: ast.JoinedStr, suffix: str) -> bool:
    """`f"{d}/plot-{THEME}<suffix>"`: a formatted directory in front of the theme file name (lets-plot's
    shap-summary, plotnine's candlestick-volume)."""
    if len(node.values) < 4:
        return False
    *head, before, theme, tail = node.values
    return (
        isinstance(before, ast.Constant)
        and isinstance(before.value, str)
        and before.value.endswith("/plot-")
        and isinstance(theme, ast.FormattedValue)
        and isinstance(theme.value, ast.Name)
        and theme.value.id == THEME_NAME
        and theme.conversion == -1
        and theme.format_spec is None
        and isinstance(tail, ast.Constant)
        and tail.value == suffix
        and any(isinstance(part, ast.FormattedValue) for part in head)
    )


def _rewrite_savefig_targets(code: str, *, library: str) -> StepResult:
    rule = save_rule(library)
    suffixes = (
        ((PNG_SUFFIX, STANDARD_TARGET), (HTML_SUFFIX, HTML_TARGET)) if rule.html else ((PNG_SUFFIX, STANDARD_TARGET),)
    )
    tree = ast.parse(code)
    index = SourceIndex(code)
    assigned: dict[str, list[ast.Assign]] = {}
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            assigned.setdefault(stmt.targets[0].id, []).append(stmt)
    edits: list[TextEdit] = []
    changes: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", None)
        if name not in rule.names:
            continue
        target = save_target(node, rule, name)
        if target is None or any(is_theme_target(target, suffix) for suffix, _ in suffixes):
            continue
        value: ast.expr | None = target
        if isinstance(target, ast.Name):
            earlier = [stmt for stmt in assigned.get(target.id, []) if stmt.lineno < node.lineno]
            value = earlier[-1].value if earlier else None
        if value is None:
            continue
        literal = next((literal for suffix, literal in suffixes if _theme_file_path(value, suffix)), None)
        if literal is not None:
            span = index.node_span(target)
            edits.append((span.start, span.end, literal))
            old = _WHITESPACE.sub(" ", code[span.start : span.end])
            changes.append(f"{name} target {old} -> {literal} at {span.lines()}")
    if not edits:
        return code, [], []
    return _apply(code, edits), changes, []


def _find_spec_test(test: ast.expr) -> str | None:
    """`X` for the test `X and X.origin != __file__` (or `X is not None and __file__ != X.origin`)."""
    if not (isinstance(test, ast.BoolOp) and isinstance(test.op, ast.And) and len(test.values) == 2):
        return None
    present, origin = test.values
    if (
        isinstance(present, ast.Compare)
        and len(present.ops) == 1
        and isinstance(present.ops[0], ast.IsNot)
        and isinstance(present.comparators[0], ast.Constant)
        and present.comparators[0].value is None
    ):
        present = present.left
    if not (isinstance(present, ast.Name) and isinstance(origin, ast.Compare) and len(origin.ops) == 1):
        return None
    if not isinstance(origin.ops[0], ast.NotEq):
        return None
    sides = {dotted_name(origin.left), dotted_name(origin.comparators[0])}
    return present.id if sides == {f"{present.id}.origin", "__file__"} else None


def _dedented(code: str, index: SourceIndex, statements: list[ast.stmt]) -> str:
    """The whole lines of `statements`, dedented to the module level."""
    first = index.lines_span(statements[0]).first_line
    last = index.lines_span(statements[-1]).last_line
    return textwrap.dedent(code[index.line_start(first) : index.line_end(last)])


def _strip_find_spec_guard(code: str) -> StepResult:
    """`X = importlib.util.find_spec("pkg")` and `if X and X.origin != __file__: <imports> else: ...` -> the imports."""
    tree = ast.parse(code)
    body = tree.body
    specs: dict[str, ast.Assign] = {}
    for stmt in body:
        if not (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name)):
            continue
        call = stmt.value
        if isinstance(call, ast.Call) and dotted_name(call.func) == "importlib.util.find_spec":
            specs[stmt.targets[0].id] = stmt
    if not specs:
        return code, [], []
    index = SourceIndex(code)
    replace: dict[int, tuple[int, str]] = {}
    hoisted: list[ast.If] = []
    changes: list[str] = []
    notes: list[str] = []
    for stmt in body:
        if not isinstance(stmt, ast.If):
            continue
        name = _find_spec_test(stmt.test)
        if name is None or name not in specs or specs[name].lineno > stmt.lineno:
            continue
        span = index.lines_span(stmt)
        if not all(isinstance(inner, ast.Import | ast.ImportFrom) for inner in stmt.body):
            notes.append(f"find_spec guard: the if at {span.lines()} holds more than imports; left in place")
            continue
        replace[span.first_line] = (span.last_line, _dedented(code, index, stmt.body))
        hoisted.append(stmt)
        changes.append(f"replaced the find_spec guard at {span.lines()} with its imports")
    remove: set[int] = set()
    for name, assignment in specs.items():
        users = [stmt for stmt in body if stmt is not assignment and name in _loads(stmt)]
        if users and all(any(user is stmt for stmt in hoisted) for user in users):
            span = index.lines_span(assignment)
            remove |= _with_comments(index, span)
            changes.append(f"removed the unused find_spec result {name} at {span.lines()}")
    if not replace:
        return code, [], notes
    return _rewrite_lines(code, remove, replace), changes, notes


def _hoist_try_guard(code: str) -> StepResult:
    """A module-level `try:` of imports only whose `finally:` only changes `sys.path` -> its imports."""
    tree = ast.parse(code)
    aliases = _sys_aliases(tree.body)
    if not aliases:
        return code, [], []
    index = SourceIndex(code)
    replace: dict[int, tuple[int, str]] = {}
    changes: list[str] = []
    for stmt in tree.body:
        if not (isinstance(stmt, ast.Try) and stmt.finalbody and not stmt.handlers and not stmt.orelse):
            continue
        if not all(isinstance(inner, ast.Import | ast.ImportFrom) for inner in stmt.body):
            continue
        if not all(_is_guard(inner, aliases) for inner in stmt.finalbody):
            continue
        span = index.lines_span(stmt)
        replace[span.first_line] = (span.last_line, _dedented(code, index, stmt.body))
        changes.append(f"replaced the try/finally sys.path guard at {span.lines()} with its imports")
    if not replace:
        return code, [], []
    return _rewrite_lines(code, set(), replace), changes, []


def _import_module_rewrite(stmt: ast.stmt, callees: set[str]) -> str | None:
    """The import for `NAME = importlib.import_module("module")[.ATTR]` (`callees` name `import_module`), or None."""
    if not (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name)):
        return None
    name, call, attribute = stmt.targets[0].id, stmt.value, None
    if isinstance(stmt.value, ast.Attribute):
        call, attribute = stmt.value.value, stmt.value.attr
    if not (isinstance(call, ast.Call) and dotted_name(call.func) in callees):
        return None
    if len(call.args) != 1 or call.keywords or not isinstance(call.args[0], ast.Constant):
        return None
    module = call.args[0].value
    if not isinstance(module, str) or not _MODULE_NAME.fullmatch(module):
        return None
    if attribute is None:
        return f"import {module}" if module == name else f"import {module} as {name}"
    return f"from {module} import {attribute}" + ("" if attribute == name else f" as {name}")


def _import_bindings(stmt: ast.Import | ast.ImportFrom) -> tuple[set[str], set[str]]:
    """The names an import binds and the top-level modules it imports."""
    if isinstance(stmt, ast.Import):
        bound = {alias.asname or alias.name.split(".")[0] for alias in stmt.names}
        return bound, {alias.name.split(".")[0] for alias in stmt.names}
    return {alias.asname or alias.name for alias in stmt.names}, {(stmt.module or "").split(".")[0]}


def _strip_path_guard(code: str) -> StepResult:
    tree = ast.parse(code)
    body = tree.body
    sys_aliases = _sys_aliases(body)
    import_module = {"importlib.import_module"} | {
        alias.asname or alias.name
        for stmt in body
        if isinstance(stmt, ast.ImportFrom) and stmt.module == "importlib" and stmt.level == 0
        for alias in stmt.names
        if alias.name == "import_module"
    }
    rewrites = {
        id(stmt): rewrite for stmt in body if (rewrite := _import_module_rewrite(stmt, import_module)) is not None
    }
    loads = {id(stmt): _loads(stmt) for stmt in body}
    os_names, pathlib_names = _module_aliases(body, "os"), _module_aliases(body, "pathlib")

    # Names bound by statements that compute a file location, transitively.
    path_names: set[str] = set()
    grown = True
    while grown:
        grown = False
        for stmt in body:
            names = _binds(stmt)
            if names and not names <= path_names and _computes_path(stmt, path_names, os_names, pathlib_names):
                path_names |= names
                grown = True

    # The guard, plus `os.chdir(<the script's directory>)`: the run form already runs in its directory.
    guard = [
        stmt
        for stmt in body
        if _is_guard(stmt, sys_aliases)
        or (
            isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Call)
            and any(dotted_name(stmt.value.func) == f"{alias}.chdir" for alias in os_names)
            and _computes_path(stmt, path_names, os_names, pathlib_names)
        )
    ]
    removed = {id(stmt) for stmt in guard}
    guard_loads: set[str] = set().union(*(loads[id(stmt)] for stmt in guard))
    grown = True
    while grown:  # dead helpers of the guard, dead sys.path snapshots and dead file-location assignments
        grown = False
        for stmt in body:
            names = _binds(stmt)
            if id(stmt) in removed or not names:
                continue
            if not (names <= guard_loads or names <= path_names or _mentions_sys_path(stmt, sys_aliases)):
                continue
            used = any(
                names & loads[id(other)]
                for other in body
                if other is not stmt and id(other) not in removed and id(other) not in rewrites
            )
            if not used:
                removed.add(id(stmt))
                grown = True

    imports = [stmt for stmt in body if isinstance(stmt, ast.Import | ast.ImportFrom)]
    kept_loads = set().union(
        *(loads[id(s)] for s in body if id(s) not in removed and id(s) not in rewrites and s not in imports)
    )
    dropped_loads = set().union(*(loads[id(s)] for s in body if id(s) in removed or id(s) in rewrites))
    removed_bound = set().union(*(_binds(stmt) for stmt in body if id(stmt) in removed))
    for stmt in imports:
        bound, modules = _import_bindings(stmt)
        if bound & kept_loads:
            continue
        if bound & dropped_loads or modules <= GUARD_MODULES:
            removed.add(id(stmt))
            removed_bound |= bound

    index = SourceIndex(code)
    replace: dict[int, tuple[int, str]] = {}
    for stmt in body:  # `del _sys, _here` loses the names whose binding went
        if not isinstance(stmt, ast.Delete) or not all(isinstance(t, ast.Name) for t in stmt.targets):
            continue
        deleted = [t.id for t in stmt.targets if isinstance(t, ast.Name)]
        left = [name for name in deleted if name not in removed_bound]
        if not left:
            removed.add(id(stmt))
        elif len(left) < len(deleted):
            span = index.lines_span(stmt)
            replace[span.first_line] = (span.last_line, f"del {', '.join(left)}{_newline(index, span.last_line)}")

    remove: set[int] = set()
    changes: list[str] = []
    for stmt in body:
        if id(stmt) not in removed:
            continue
        span = index.lines_span(stmt)
        remove |= _with_comments(index, span)
        if stmt in guard:
            label = "the sys.path guard"
        elif stmt in imports or isinstance(stmt, ast.Delete):
            label = f"the unused `{ast.unparse(stmt)}`"
        elif _mentions_sys_path(stmt, sys_aliases):
            label = "an unused sys.path snapshot"
        else:
            label = "an unused file-path helper"
        changes.append(f"removed {label} at {span.lines()}")

    for stmt in body:
        statement = rewrites.get(id(stmt))
        if statement is None or id(stmt) in removed:
            continue
        span = index.lines_span(stmt)
        replace[span.first_line] = (span.last_line, statement + _newline(index, span.last_line))
        changes.append(f"{ast.unparse(stmt)} -> {statement} at {span.lines()}")

    notes: list[str] = []
    leftover = [stmt for stmt in body if id(stmt) not in removed and _mentions_sys_path(stmt, sys_aliases)]
    if leftover:
        lines = ", ".join(str(stmt.lineno) for stmt in leftover)
        notes.append(f"sys.path guard: statements at line {lines} use sys.path in other ways; left in place")
    if not remove and not replace:
        return code, [], notes
    return _rewrite_lines(code, remove, replace), changes, notes


def _newline(index: SourceIndex, line: int) -> str:
    text = index.line_text(line)
    return text[len(text.rstrip("\r\n")) :]


def _rewrite_lines(code: str, remove: set[int], replace: dict[int, tuple[int, str]]) -> str:
    """Drop and replace whole lines, then trim blank lines where the removed lines were.

    At each removal point the blank lines around it shrink to two (PEP 8 between
    module-level statements), or to none at the start or the end of the file (pygal's
    and lets-plot's files end on the writes the normaliser removes).
    """
    index = SourceIndex(code)
    out: list[str] = []
    joins: list[int] = []
    line = 1
    while line <= index.line_count:
        if line in replace:
            last, text = replace[line]
            out.append(text)
            line = last + 1
        elif line in remove:
            if not joins or joins[-1] != len(out):
                joins.append(len(out))
            line += 1
        else:
            out.append(index.line_text(line))
            line += 1

    def blank(text: str) -> bool:
        return bool(text) and not text.strip()

    limit = len(out)
    for join in reversed(joins):
        join = min(join, limit)  # the blank lines up to a later removal point may have gone with it
        before = 0
        while join - before - 1 >= 0 and blank(out[join - before - 1]):
            before += 1
        after = 0
        while join + after < len(out) and blank(out[join + after]):
            after += 1
        at_end = not "".join(out[join + after :])
        allowed = 0 if join - before == 0 or at_end else 2
        excess = before + after - allowed
        cut_after = min(after, max(excess, 0))
        cut_before = max(excess, 0) - cut_after
        del out[join : join + cut_after]
        del out[join - cut_before : join]
        limit = join - cut_before
    return "".join(out)
