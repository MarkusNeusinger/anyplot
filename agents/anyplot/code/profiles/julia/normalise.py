"""The Julia normaliser: Makie catalogue code in, code that renders the exact canvas out.

The Julia counterpart of `profiles/r/normalise.py`. `normalise(code)` makes these
rewrites, in the order `_STEPS` runs them, each only when it applies:

1. **Catalogue header.** The four comment lines that open every catalogue file
   (`# anyplot.ai`, `# <spec-id>: <title>`, `# Library: ...`, `# Quality: ...`, all 325
   files on 2026-10-29) go with the blank lines after them. Only lines of that shape go,
   so a comment below the header stays.
2. **Save target.** `save(joinpath(@__DIR__, "plot-$(THEME).png"), fig; ...)` (4 files:
   bode-basic, dendrogram-basic, piano-roll-midi, root-locus-basic) becomes
   `save("plot-$(THEME).png", fig; ...)`, so the file lands in the working directory
   and the protected save (`regions.py`) has the standard target in every catalogue file
   whose save is a top-level statement. The validator refuses `@__DIR__` everywhere else.
3. **Catalogue title.** Every string literal in the catalogue title form
   (`normalise.is_catalogue_title`, the Python profile's rule, shared for parity:
   `[<descriptive> · ]<spec-id> · julia · makie · anyplot.ai`) becomes `""`; the call
   that shows it stays. All 325 files hold exactly one such literal (plain strings; one
   writes `\\$2.00` with an escape, none interpolates), in `Axis(...; title = ...)` or bound
   to a name first (`title_str = "..."`).
4. **`resolution =`.** The `resolution` keyword of the `Figure(...)` call becomes `size`
   (122 files). Makie 0.24 still accepts `resolution` and renders the same PNG, but warns
   on every run ("The `resolution` keyword for `Scene`s and `Figure`s has been
   deprecated", measured in the J1 image on 2026-10-29), which would fill the render's
   stderr tail that the repair reads; Makie maps the one to the other unchanged, and the
   catalogue prompt (`prompts/library/makie.md`) asks for `size`. The keyword shorthand
   `Figure(; resolution)`, which passes the variable `resolution`, becomes
   `Figure(; size = resolution)`, the same value (review of 2026-10-29: it raised before).
   A call that already passes `size` keeps both with a note.
5. **Canvas**, last: only `px_per_unit` of the protected save changes, never the
   figure's `size`, so the layout in Makie's units (font sizes, line widths, which
   `px_per_unit` scales) stays, as R's dpi and lets-plot's scale rewrites do (owner
   decision of 2026-10-29 for R). CairoMakie rounds the figure size to whole units and
   then `size * px_per_unit` to whole pixels (measured in the J1 image, CairoMakie 0.15.16:
   `(1600, 900)` at 1.9999 gives 3200x1800, at 2.0004 3201x1800, `(1066.6667, 600)` at 3
   gives 3201x1800, `(1000, 562.5)` at 3.2 gives 3200x1798, and a save without
   `px_per_unit` renders at 2). The new `px_per_unit` is the shortest decimal that renders
   the target exactly, else one within 16 px. All 325 catalogue figures are `(1600, 900)`
   or `(1200, 1200)` at `px_per_unit = 2` already (the J1 sweep rendered 252 at 3200x1800
   and 68 at 2400x2400 of the 320 that render), so the step changes no catalogue file; it
   stands for the files a regeneration brings. A figure size that is not one literal
   tuple on the file's only `Figure(...)` call (also when a theme or `resize_to_layout!`
   sizes the figure), an aspect no `px_per_unit` brings within 16 px of a target, or a
   save that is not the protected one leave the save alone with a note, which
   `measure_canvas` and the readiness scan report.

Each step is checked with tree-sitter and dropped with a note when its result has a
syntax problem the input did not have; code with syntax problems is returned unchanged.
The result is idempotent: `normalise(normalise(x)) == normalise(x)` (a corpus test).
"""

import math
import re
from collections.abc import Callable
from fractions import Fraction

from tree_sitter import Node

from ...normalise import MAX_IMAGE_PIXELS, TARGETS, TOLERANCE, Canvas, Normalised, is_catalogue_title
from ...treesitter import (
    Source,
    jl_arguments,
    jl_callee,
    jl_macro_name,
    jl_named,
    jl_number,
    jl_string,
    jl_unwrap,
    syntax_problems,
    walk,
)
from .regions import STANDARD_TARGET, SaveCall, find_regions, is_save_call, is_standard_target


HEADER_FIRST_LINE = "# anyplot.ai"
HEADER_LINE = re.compile(r"# (?:anyplot\.ai\s*$|[a-z0-9]+(?:-[a-z0-9]+)*: |Library: |Quality: )")
FIGURE_NAMES = frozenset({"Figure", "Makie.Figure", "CairoMakie.Figure"})
RESIZE_NAMES = frozenset({"resize!", "resize_to_layout!", "set_theme!", "with_theme", "update_theme!"})
"""Calls that can size a figure after (or instead of) its constructor: the canvas is then unknown statically."""
DEFAULT_SIZE = (600.0, 450.0)
"""Makie 0.24's figure size without `size` (measured: `Figure()` at `px_per_unit = 2` renders 1200x900)."""
DEFAULT_PX_PER_UNIT = 2.0
"""CairoMakie 0.15's `px_per_unit` when the save passes none (measured: `(1600, 900)` renders 3200x1800)."""
MAX_SCALE_DECIMALS = 6

TextEdit = tuple[int, int, str]  # replace code[start:end] with the text
StepResult = tuple[str, list[str], list[str]]  # the code, the changes made, the notes on what was left alone


def normalise(code: str) -> str:
    """The normalised code; see the module docstring."""
    return normalise_report(code).code


def normalise_report(code: str) -> Normalised:
    """`normalise` with the list of changes made and the notes on what was left alone."""
    problems = syntax_problems(Source(code, "julia").tree)
    if problems:
        return Normalised(code, (), (f"syntax: {problems[0].message()}; nothing was normalised",))
    changes: list[str] = []
    notes: list[str] = []
    for name, step in _STEPS:
        new_code, step_changes, step_notes = step(code)
        if new_code != code and syntax_problems(Source(new_code, "julia").tree):
            notes.append(f"{name}: the rewrite would not parse; left unchanged")
            continue
        code = new_code
        changes.extend(step_changes)
        notes.extend(step_notes)
    return Normalised(code, tuple(changes), tuple(notes))


# --- header ------------------------------------------------------------------------------


def _strip_header(code: str) -> StepResult:
    lines = code.splitlines(keepends=True)
    if not lines or lines[0].rstrip() != HEADER_FIRST_LINE:
        return code, [], []
    end = 0
    while end < len(lines) and HEADER_LINE.match(lines[end]):
        end += 1
    header_end = end
    while end < len(lines) and not lines[end].strip():
        end += 1
    span = "line 1" if header_end == 1 else f"lines 1-{header_end}"
    return "".join(lines[end:]), [f"removed the catalogue header at {span}"], []


# --- save target -------------------------------------------------------------------------


def _plain_save_target(code: str) -> StepResult:
    """`save(joinpath(@__DIR__, "plot-$(THEME).png"), ...)` writes the standard target into the working directory."""
    source = Source(code, "julia")
    edits: list[TextEdit] = []
    changes: list[str] = []
    for node in walk(source.root):
        if not is_save_call(source, node):
            continue
        arguments = jl_arguments(source, node)
        target = next((argument for argument in arguments if argument.position == 0), None)
        value = jl_unwrap(target.value) if target is not None else None
        if value is None or value.type != "call_expression" or jl_callee(source, value) != "joinpath":
            continue
        parts = jl_arguments(source, value)
        if (
            len(parts) != 2
            or len(value.children) != 2
            or any(part.position is None or part.splat for part in parts)
            or jl_macro_name(source, jl_unwrap(parts[0].value)) != "@__DIR__"
            or jl_named(jl_unwrap(parts[0].value))[1:]
            or not is_standard_target(source, parts[1].value)
        ):
            continue
        span = source.node_span(value)
        edits.append((span.start, span.end, STANDARD_TARGET))
        changes.append(
            f"saved {STANDARD_TARGET} in the working directory instead of next to the script at {span.lines()}"
        )
    return _apply(code, edits), changes, []


# --- title -------------------------------------------------------------------------------


def _strip_title(code: str) -> StepResult:
    source = Source(code, "julia")
    edits: list[TextEdit] = []
    changes: list[str] = []
    for node in walk(source.root):
        if node.type != "string_literal":
            continue
        value = jl_string(source, node)
        if value is None or not is_catalogue_title(value):
            continue
        span = source.node_span(node)
        edits.append((span.start, span.end, '""'))
        changes.append(f"emptied the catalogue title at {span.lines()}")
    return _apply(code, edits), changes, []


# --- resolution --------------------------------------------------------------------------


def figure_calls(source: Source) -> list[Node]:
    """Every `Figure(...)` call of the file."""
    return [
        node for node in walk(source.root) if node.type == "call_expression" and jl_callee(source, node) in FIGURE_NAMES
    ]


def _resolution_to_size(code: str) -> StepResult:
    source = Source(code, "julia")
    edits: list[TextEdit] = []
    changes: list[str] = []
    notes: list[str] = []
    for call in figure_calls(source):
        arguments = jl_arguments(source, call)
        names = [argument.name for argument in arguments]
        resolution = next((argument for argument in arguments if argument.name == "resolution"), None)
        if resolution is None:
            continue
        span = source.node_span(call)
        if "size" in names:
            notes.append(f"resolution: the Figure at {span.lines()} passes size and resolution; both stay")
            continue
        if resolution.node.type == "identifier":
            # `Figure(; resolution)` passes the variable as `resolution = resolution`: the same value under `size`
            key_span = source.node_span(resolution.node)
            edits.append((key_span.start, key_span.end, "size = resolution"))
        else:
            named = jl_named(resolution.node)
            if not named:
                notes.append(f"resolution: the Figure at {span.lines()} passes resolution in a form left alone")
                continue
            key_span = source.node_span(named[0])
            edits.append((key_span.start, key_span.end, "size"))
        changes.append(f"renamed the Figure's deprecated resolution keyword to size at {key_span.lines()}")
    return _apply(code, edits), changes, notes


# --- canvas ------------------------------------------------------------------------------


def _figure_size(source: Source) -> tuple[float, float] | str:
    """The figure size in Makie's units from the file's only `Figure(...)` call, or a note why it is unknown."""
    calls = figure_calls(source)
    if len(calls) != 1:
        return f"the file creates {len(calls)} figures, so the canvas is unknown"
    resizers = sorted(
        {
            name
            for node in walk(source.root)
            if node.type in ("call_expression", "broadcast_call_expression")
            for name in [jl_callee(source, node) or ""]
            if name.rsplit(".", 1)[-1] in RESIZE_NAMES
        }
    )
    if resizers:
        return f"{', '.join(resizers)} can size the figure, so the canvas is unknown"
    arguments = jl_arguments(source, calls[0])
    size = next((argument for argument in arguments if argument.name in ("size", "resolution")), None)
    if size is None:
        if any(argument.splat for argument in arguments):
            return "the Figure takes splatted keywords, so the canvas is unknown"
        return DEFAULT_SIZE
    value = jl_unwrap(size.value)
    items = jl_named(value) if value.type == "tuple_expression" else []
    numbers = [jl_number(source, item) for item in items]
    if len(numbers) != 2 or any(number is None for number in numbers):
        return f"the Figure's size ({source.text(size.value)}) is not a tuple of two number literals"
    width, height = (number for number in numbers if number is not None)
    if not (width > 0 and height > 0 and math.isfinite(width) and math.isfinite(height)):
        return f"the Figure's size ({source.text(size.value)}) is not a positive size"
    if min(units((width, height))) < 1:
        return f"the Figure's size ({source.text(size.value)}) rounds to less than one unit"
    return width, height


def _scale(save: SaveCall) -> float | str:
    """The protected save's `px_per_unit` (CairoMakie's 2 without one), or a note why it is unknown."""
    if save.px_per_unit is None:
        return DEFAULT_PX_PER_UNIT
    number = save.px_per_unit_number
    if number is None:
        return f"the save's px_per_unit ({save.px_per_unit}) is not a number literal"
    if not (number > 0 and math.isfinite(number)):
        return f"the save's px_per_unit ({save.px_per_unit}) is not a positive number"
    return number


def units(size: tuple[float, float]) -> tuple[int, int]:
    """The figure size as CairoMakie keeps it: each side rounded to a whole unit, ties to even (module docstring)."""
    return round(size[0]), round(size[1])


def pixels(size: tuple[float, float], scale: float) -> tuple[int, int]:
    """The PNG size `save` writes for `size` at `px_per_unit = scale` (module docstring, step 5)."""
    width, height = units(size)
    return round(width * scale), round(height * scale)


def _nearest_target(size: tuple[float, float]) -> tuple[int, int]:
    width, height = units(size)
    return min(TARGETS, key=lambda target: abs(math.log((width / height) / (target[0] / target[1]))))


def _shortest(low: Fraction, high: Fraction, accept: Callable[[float], bool]) -> str | None:
    """The shortest decimal literal in `[low, high)` that `accept`s, an integer first."""
    if low >= high:
        return None
    for decimals in range(MAX_SCALE_DECIMALS + 1):
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


def plan_scale(size: tuple[float, float]) -> tuple[tuple[int, int], str, bool] | None:
    """The target, the `px_per_unit` literal that renders `size` on it, and whether exactly; None when none does.

    An exact hit on both sides is preferred; failing that, a scale that renders one side
    exactly and the other within `TOLERANCE`. The search runs on exact fractions of the
    whole-unit sides, for `t - 1/2 <= side * scale < t + 1/2`, and checks each candidate in
    floating point, as Julia multiplies and rounds.
    """
    ordered = sorted(TARGETS, key=lambda target: target != _nearest_target(size))
    width, height = (Fraction(side) for side in units(size))
    if width <= 0 or height <= 0:
        return None
    half = Fraction(1, 2)
    for target in ordered:
        tw, th = target

        def exact(scale: float, t: tuple[int, int] = target) -> bool:
            return pixels(size, scale) == t

        low = max((tw - half) / width, (th - half) / height)
        high = min((tw + half) / width, (th + half) / height)
        literal = _shortest(low, high, exact)
        if literal is not None:
            return target, literal, True
    for target in ordered:

        def near(scale: float, t: tuple[int, int] = target) -> bool:
            rendered = pixels(size, scale)
            return abs(rendered[0] - t[0]) <= TOLERANCE and abs(rendered[1] - t[1]) <= TOLERANCE

        for side, wanted in ((width, target[0]), (height, target[1])):
            literal = _shortest((wanted - half) / side, (wanted + half) / side, near)
            if literal is not None:
                return target, literal, False
    return None


def measure_canvas(code: str) -> Canvas:
    """The canvas the protected save renders, as far as its literals tell; `figsize` is the size in Makie's units."""
    source = Source(code, "julia")
    regions = find_regions(source)
    if regions.save is None:
        return Canvas(None, None, None, None, "no protected save, so the canvas is unknown")
    size = _figure_size(source)
    if isinstance(size, str):
        return Canvas(None, None, None, None, size)
    scale = _scale(regions.save)
    if isinstance(scale, str):
        return Canvas(size, None, None, None, scale)
    target = _nearest_target(size)
    rendered = pixels(size, scale)
    if rendered == target:
        return Canvas(size, scale, rendered, target, None)
    over = " (over R2's pixel cap)" if rendered[0] * rendered[1] > MAX_IMAGE_PIXELS else ""
    note = f"the save renders {rendered[0]}x{rendered[1]}{over}, not {target[0]}x{target[1]}"
    return Canvas(size, scale, rendered, target, note)


def _normalise_canvas(code: str) -> StepResult:
    source = Source(code, "julia")
    regions = find_regions(source)
    save = regions.save
    if save is None:
        return code, [], ["canvas: no protected save; the canvas was left alone"]
    size = _figure_size(source)
    if isinstance(size, str):
        return code, [], [f"canvas: {size}; px_per_unit was left alone"]
    scale = _scale(save)
    if isinstance(scale, str):
        return code, [], [f"canvas: {scale}; left alone"]
    shown_size = f"({size[0]:g}, {size[1]:g})"
    plan = plan_scale(size)
    if plan is None:
        aspect = size[0] / size[1]
        return (
            code,
            [],
            [
                f"canvas: the figure size {shown_size} has aspect {aspect:.3f}; no px_per_unit renders 3200x1800 "
                f"(16:9) or 2400x2400 (1:1) within {TOLERANCE} px without changing the size"
            ],
        )
    target, literal, exact = plan
    if pixels(size, scale) == target and (exact or float(literal) == scale):
        return code, [], []
    if save.px_per_unit_span is not None:
        edit: TextEdit = (save.px_per_unit_span.start, save.px_per_unit_span.end, literal)
    else:
        end = save.span.end - 1  # before the call's closing parenthesis
        separator = ", " if save.keywords else "; "
        edit = (end, end, f"{separator}px_per_unit = {literal}")
    rendered = pixels(size, float(literal))
    shown = f"{rendered[0]}x{rendered[1]}"
    old = save.px_per_unit or f"the default {DEFAULT_PX_PER_UNIT:g}"
    change = f"set the save's px_per_unit from {old} to {literal}: the figure size {shown_size} renders {shown}"
    notes = [] if exact else [f"canvas: {shown_size} renders {shown}, within {TOLERANCE} px of {target[0]}x{target[1]}"]
    return _apply(code, [edit]), [change], notes


# --- helpers -----------------------------------------------------------------------------


def _apply(code: str, edits: list[TextEdit]) -> str:
    """`code` with each `(start, end, text)` applied; the edits do not overlap."""
    out: list[str] = []
    cursor = 0
    for start, end, text in sorted(edits):
        out += [code[cursor:start], text]
        cursor = end
    out.append(code[cursor:])
    return "".join(out)


_STEPS: tuple[tuple[str, Callable[[str], StepResult]], ...] = (
    ("header", _strip_header),
    ("save target", _plain_save_target),
    ("title", _strip_title),
    ("resolution", _resolution_to_size),
    ("canvas", _normalise_canvas),
)
