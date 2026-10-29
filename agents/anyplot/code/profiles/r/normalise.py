"""The R normaliser: ggplot2 catalogue code in, code that renders the exact canvas out.

The R counterpart of `code/normalise.py`. `normalise(code)` makes these rewrites, in the
order `_STEPS` runs them, each only when it applies:

1. **Catalogue header.** The roxygen header that opens every catalogue file (four `#'`
   lines: `#' anyplot.ai`, `#' <spec-id>: <title>`, `#' Library: ...`, `#' Quality: ...`,
   all 325 files on 2026-10-29) goes with the blank lines after it; the whole leading run
   of `#'` lines goes, so a second header would too.
2. **Save target.** A `ggsave` whose `filename =` is a name bound once, at the top
   level, to exactly `sprintf("plot-%s.png", THEME)` and read nowhere else gets that call
   inlined, and the binding goes (logistic-regression's `output_file`, 1 file). The
   protected save (`regions.py`) then has the standard target in every catalogue file.
3. **Catalogue title.** Every string literal in the catalogue title form
   (`normalise.is_catalogue_title`, the Python profile's rule, shared for parity:
   `[<descriptive> · ]<spec-id> · r · ggplot2 · anyplot.ai`) becomes `""`; the call that
   shows it stays. All 325 files hold exactly one such literal: 176 in `labs(title =)`,
   139 bound to a name first (`plot_title <- "..."`), 8 inside `paste0` or `sprintf`, 2
   elsewhere. A title split over `paste0("<descriptive> · <spec-id> · ", "r · ggplot2 ·
   anyplot.ai")` keeps its first part, which does not have the form on its own, with a
   note (4 files outside the map specs), and a title that was a `sprintf` format leaves
   `sprintf("", ...)`, which R evaluates to `""` with a warning that the arguments are
   unused (line-timeseries-rolling), also with a note. Known issue, not worked around
   (owner decision of 2026-10-29): 67 catalogue files size the title's font from
   `nchar(<title name>)` (66 in the design pass's count), which then sees 0 characters;
   the adapter writes a new title anyway.
4. **Canvas**, last: only `dpi =` of the protected save changes, so the PNG lands on
   3200x1800 or 2400x2400 while the layout in inches stays (the counterpart of lets-plot's
   scale-only rewrite, owner decision of 2026-10-29). ggsave hands `width` and `height`
   in inches and `res = dpi` to `ragg::agg_png`, which renders `floor(inches * dpi)`
   pixels per side: ragg truncates (measured on 2026-10-29 in the toolchain image, R 4.6.1:
   13.333 in at 240 dpi gives 3199 px, 16 x 9 in at 200 dpi exactly 3200x1800). The dpi is
   the shortest decimal for which `inches * dpi`, in R's double arithmetic, lies in
   `[t, t + 1)` for the target `t`. In the catalogue 219 saves are 8 x 4.5 in at 400 dpi
   and 72 are 6 x 6 at 400 (both on target already), 32 are 16 x 9 at 300 (4800x2700,
   rewritten to 200), and one each 9 x 9 and 12 x 12 at 300 (2700x2700 and 3600x3600,
   rewritten to 266.7 and 200). Width or
   height not a number literal, `units = "px"` (whose pixels no dpi changes), an aspect
   no dpi brings within 16 px of a target, or a save that is not the protected one leave
   the save alone with a note, which `measure_canvas` and the readiness scan report.

Each step is checked with tree-sitter and dropped with a note when its result has a
syntax problem the input did not have; code with syntax problems is returned unchanged.
The result is idempotent: `normalise(normalise(x)) == normalise(x)` (a corpus test).
"""

import math
from collections.abc import Callable
from fractions import Fraction

from tree_sitter import Node

from ...normalise import MAX_IMAGE_PIXELS, TARGETS, TOLERANCE, Canvas, Normalised, is_catalogue_title
from ...treesitter import (
    Source,
    Visit,
    first_line,
    last_line,
    r_arguments,
    r_bindings,
    r_callee,
    r_identifier,
    r_is_lookup,
    r_string_value,
    statements,
    syntax_problems,
    visits,
)
from .regions import STANDARD_TARGET, SaveCall, find_regions, is_standard_target, save_target


HEADER_FIRST_LINE = "#' anyplot.ai"
HEADER_PREFIX = "#'"
SPLIT_TITLE_CALLS = frozenset({"paste0", "paste"})
FORMAT_CALLS = frozenset({"sprintf", "gettextf"})
DEFAULT_DPI = 300.0
"""ggsave's `dpi` when the save passes none."""
NAMED_DPI = {"print": 300.0, "screen": 72.0, "retina": 320.0}
"""ggsave's dpi names."""
UNITS_PER_INCH = {"in": 1.0, "cm": 2.54, "mm": 25.4}
"""ggsave's divisors from a unit to inches (`plot_dim`)."""
DEFAULT_UNITS = "in"
MAX_DPI_DECIMALS = 6

TextEdit = tuple[int, int, str]  # replace code[start:end] with the text
StepResult = tuple[str, list[str], list[str]]  # the code, the changes made, the notes on what was left alone


def normalise(code: str) -> str:
    """The normalised code; see the module docstring."""
    return normalise_report(code).code


def normalise_report(code: str) -> Normalised:
    """`normalise` with the list of changes made and the notes on what was left alone."""
    problems = syntax_problems(Source(code, "r").tree)
    if problems:
        return Normalised(code, (), (f"syntax: {problems[0].message()}; nothing was normalised",))
    changes: list[str] = []
    notes: list[str] = []
    for name, step in _STEPS:
        new_code, step_changes, step_notes = step(code)
        if new_code != code and syntax_problems(Source(new_code, "r").tree):
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
    while end < len(lines) and lines[end].startswith(HEADER_PREFIX):
        end += 1
    header_end = end
    while end < len(lines) and not lines[end].strip():
        end += 1
    span = "line 1" if header_end == 1 else f"lines 1-{header_end}"
    return "".join(lines[end:]), [f"removed the catalogue header at {span}"], []


# --- save target -------------------------------------------------------------------------


def _inline_save_target(code: str) -> StepResult:
    """Inline a top-level name bound once to the standard target and read only as a `ggsave` `filename =`."""
    source = Source(code, "r")
    top = statements(source.root)
    bindings = r_bindings(source, source.root)
    edits: list[TextEdit] = []
    changes: list[str] = []
    for node in top:
        if node.type != "call" or r_callee(source, node) != "ggsave":
            continue
        target = save_target(r_arguments(source, node))
        if target is None or target.name != "filename" or target.value is None:
            continue
        name = r_identifier(source, target.value)
        if name is None:
            continue
        bound = [site for bound_name, site in bindings if bound_name == name]
        if len(bound) != 1 or bound[0].parent is None or bound[0].parent.type != "program":
            continue
        statement = bound[0]
        value = statement.child_by_field_name("rhs")
        if value is None or not is_standard_target(source, value):
            continue
        reads = [
            visit.node
            for visit in visits(source.root)
            if visit.node.type == "identifier" and r_is_lookup(visit) and r_identifier(source, visit.node) == name
        ]
        if len(reads) != 1 or reads[0].start_byte != target.value.start_byte:
            continue
        if not _alone_on_its_lines(source, statement):
            continue
        lines = source.lines_span(statement)
        read = source.node_span(target.value)
        edits += [(lines.start, lines.end, ""), (read.start, read.end, STANDARD_TARGET)]
        changes.append(
            f"inlined {name} as the save target at {read.lines()} and removed its binding at {lines.lines()}"
        )
    return _apply(code, edits), changes, []


def _alone_on_its_lines(source: Source, node: Node) -> bool:
    """Whether no other top-level node (statement or comment) shares a line with the statement `node`."""
    first, last = first_line(node), last_line(node)
    return all(
        other.start_byte == node.start_byte or last_line(other) < first or first_line(other) > last
        for other in source.root.children
    )


# --- title -------------------------------------------------------------------------------


def _strip_title(code: str) -> StepResult:
    source = Source(code, "r")
    edits: list[TextEdit] = []
    changes: list[str] = []
    notes: list[str] = []
    for visit in visits(source.root):
        node = visit.node
        if node.type != "string" or (
            visit.parent is not None and visit.parent.type == "argument" and visit.field == "name"
        ):
            continue
        value = r_string_value(source, node)
        if value is None or not is_catalogue_title(value):
            continue
        span = source.node_span(node)
        edits.append((span.start, span.end, '""'))
        changes.append(f"emptied the catalogue title at {span.lines()}")
        call = _enclosing_call(visit)
        callee = r_callee(source, call) if call is not None else None
        if call is not None and callee in SPLIT_TITLE_CALLS:
            others = [
                argument
                for argument in r_arguments(source, call)
                if argument.value is not None
                and argument.value.start_byte != node.start_byte
                and r_string_value(source, argument.value)
            ]
            if others:
                notes.append(
                    f"title: the catalogue title at {span.lines()} is split over {callee}(); its other parts stay"
                )
        elif call is not None and callee in FORMAT_CALLS:
            notes.append(
                f"title: the catalogue title at {span.lines()} was a {callee} format; it now formats an empty "
                "string, and R warns that its arguments are unused"
            )
    return _apply(code, edits), changes, notes


def _enclosing_call(visit: Visit) -> Node | None:
    """The call a string is a direct argument value of, else None."""
    parent = visit.parent
    if parent is None or parent.type != "argument":
        return None
    arguments = parent.parent
    call = arguments.parent if arguments is not None else None
    return call if call is not None and call.type == "call" else None


# --- canvas ------------------------------------------------------------------------------


def _canvas_inputs(source: Source, save: SaveCall) -> tuple[tuple[float, float], float, str] | str:
    """The protected save's size in inches, its dpi and the dpi's source; or a note why the canvas is unknown.

    The inches are computed in floating point as ggsave computes them (`width / 2.54` for
    cm), so a rounding of R's arithmetic shows in the pixel count as it would in the PNG.
    """
    width, height = save.argument("width"), save.argument("height")
    if width is None or height is None:
        return "the save passes no width and height, so ragg sizes the PNG from the open device"
    if width.number is None or height.number is None:
        return f"the save's width and height ({width.text}, {height.text}) are not number literals"
    if not (width.number > 0 and height.number > 0 and math.isfinite(width.number) and math.isfinite(height.number)):
        return f"the save's width and height ({width.text}, {height.text}) are not a positive size"
    units_argument = save.argument("units")
    units = DEFAULT_UNITS
    if units_argument is not None:
        units_value = units_argument.text.strip("\"'")
        if units_argument.number is not None or units_value not in (*UNITS_PER_INCH, "px"):
            return f"the save's units ({units_argument.text}) are not a literal unit"
        units = units_value
    if units == "px":
        return "the save sizes the PNG in px, whose pixels no dpi changes"
    divisor = UNITS_PER_INCH[units]
    size = (width.number / divisor, height.number / divisor)
    dpi_argument = save.argument("dpi")
    if dpi_argument is None:
        return size, DEFAULT_DPI, "default"
    if dpi_argument.number is not None:
        return size, dpi_argument.number, dpi_argument.text
    named = NAMED_DPI.get(dpi_argument.text.strip("\"'"))
    if named is None:
        return f"the save's dpi ({dpi_argument.text}) is not a number literal"
    return size, named, dpi_argument.text


def _pixels(size: tuple[float, float], dpi: float) -> tuple[int, int]:
    """`inches * dpi` per side in R's double arithmetic, truncated as ragg truncates (module docstring, step 4)."""
    return math.floor(size[0] * dpi), math.floor(size[1] * dpi)


def _nearest_target(size: tuple[float, float]) -> tuple[int, int]:
    width, height = size
    return min(TARGETS, key=lambda target: abs(math.log((width / height) / (target[0] / target[1]))))


def _shortest(low: Fraction, high: Fraction, accept: Callable[[float], bool]) -> str | None:
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


def plan_dpi(size: tuple[float, float]) -> tuple[tuple[int, int], str, bool] | None:
    """The target, the dpi literal that renders `size` (inches) on it, and whether exactly; None when none does.

    An exact hit on both sides is preferred; failing that, a dpi that renders one side
    exactly and the other within `TOLERANCE`. The search runs on exact fractions of the
    sides, for `t <= inches * dpi < t + 1` (ragg truncates), and checks each candidate in
    floating point, as R multiplies.
    """
    ordered = sorted(TARGETS, key=lambda target: target != _nearest_target(size))
    width, height = Fraction(size[0]), Fraction(size[1])
    for target in ordered:
        tw, th = target

        def exact(dpi: float, t: tuple[int, int] = target) -> bool:
            return _pixels(size, dpi) == t

        low = max(tw / width, th / height)
        high = min((tw + 1) / width, (th + 1) / height)
        literal = _shortest(low, high, exact)
        if literal is not None:
            return target, literal, True
    for target in ordered:

        def near(dpi: float, t: tuple[int, int] = target) -> bool:
            pixels = _pixels(size, dpi)
            return abs(pixels[0] - t[0]) <= TOLERANCE and abs(pixels[1] - t[1]) <= TOLERANCE

        for side, pixels in ((width, target[0]), (height, target[1])):
            literal = _shortest(pixels / side, (pixels + 1) / side, near)
            if literal is not None:
                return target, literal, False
    return None


def measure_canvas(code: str) -> Canvas:
    """The canvas the protected save renders, as far as its literals tell; `figsize` is the size in inches."""
    source = Source(code, "r")
    regions = find_regions(source)
    if regions.save is None:
        return Canvas(None, None, None, None, "no protected ggsave, so the canvas is unknown")
    inputs = _canvas_inputs(source, regions.save)
    if isinstance(inputs, str):
        return Canvas(None, None, None, None, inputs)
    size, dpi, _ = inputs
    target = _nearest_target(size)
    pixels = _pixels(size, dpi)
    if pixels == target:
        return Canvas(size, dpi, pixels, target, None)
    over = " (over R2's pixel cap)" if pixels[0] * pixels[1] > MAX_IMAGE_PIXELS else ""
    note = f"the save renders {pixels[0]}x{pixels[1]}{over}, not {target[0]}x{target[1]}"
    return Canvas(size, dpi, pixels, target, note)


def _normalise_canvas(code: str) -> StepResult:
    source = Source(code, "r")
    regions = find_regions(source)
    save = regions.save
    if save is None:
        return code, [], ["canvas: no protected ggsave; the canvas was left alone"]
    inputs = _canvas_inputs(source, save)
    if isinstance(inputs, str):
        return code, [], [f"canvas: {inputs}; the dpi was left alone"]
    size, dpi, dpi_text = inputs
    plan = plan_dpi(size)
    inches = f"{size[0]:g} x {size[1]:g} in"
    if plan is None:
        aspect = size[0] / size[1]
        return (
            code,
            [],
            [
                f"canvas: {inches} has aspect {aspect:.3f}; no dpi renders 3200x1800 (16:9) or 2400x2400 (1:1) "
                f"within {TOLERANCE} px without changing the size"
            ],
        )
    target, literal, exact = plan
    if _pixels(size, dpi) == target and (exact or float(literal) == dpi):
        return code, [], []
    dpi_argument = save.argument("dpi")
    if dpi_argument is not None and dpi_argument.value_span is not None:
        edit: TextEdit = (dpi_argument.value_span.start, dpi_argument.value_span.end, literal)
    else:
        last = save.arguments[-1].span if save.arguments else None
        if last is None:
            return code, [], ["canvas: the save has no arguments; the dpi was left alone"]
        edit = (last.end, last.end, f", dpi = {literal}")
    rendered = _pixels(size, float(literal))
    shown = f"{rendered[0]}x{rendered[1]}"
    change = f"set the save's dpi from {dpi_text} to {literal}: {inches} renders {shown}"
    notes = [] if exact else [f"canvas: {inches} renders {shown}, within {TOLERANCE} px of {target[0]}x{target[1]}"]
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
    ("save target", _inline_save_target),
    ("title", _strip_title),
    ("canvas", _normalise_canvas),
)
