"""The normaliser: catalogue code in, code that renders the exact canvas out (matplotlib and seaborn).

`normalise(code, library=...)` makes four rewrites, each only when it applies:

1. **Catalogue header and title.** The four-line module docstring that opens every
   catalogue file (lines `anyplot.ai`, `<spec-id>: <title>`, `Library: ...`,
   `Quality: ...`) and the blank lines after it go. Every string literal in the
   catalogue title form, `[<descriptive> · ]<spec-id> · [<language> · ]<library> ·
   anyplot.ai` (also with the legacy `pyplots.ai`, or with the descriptive part ended by
   a newline), becomes `""`: it names the catalogue's spec and demo data, and the
   catalogue title rule does not apply to user plots. The call that shows it stays, so
   code that positions the title keeps working. A title the adapter wrote in its own
   words does not have that form and stays, and so does a title built by an f-string.
2. **Savefig target.** A target that is a path whose file name is the theme f-string,
   such as `os.path.join(script_dir, f"plot-{THEME}.png")`, `OUT / f"plot-{THEME}.png"`,
   or a module-level name assigned one of those (`output_path`), becomes the literal
   `f"plot-{THEME}.png"` in every savefig call, so the file lands next to the run form.
   A single-theme target such as `"plot.png"` stays (the readiness scan blocks it).
3. **`sys.path` guard and file paths.** A file named `matplotlib.py` or `seaborn.py`
   shadows the installed package when run from its own directory, so 120 of 650
   catalogue files strip their directory from `sys.path` first. The run form is
   `plot.py`, so the guard goes: every module-level statement that only changes
   `sys.path` (an assignment to it, a `sys.path.*()` call, or an `if`, `for`, `while` or
   `try` holding only such statements, private helper assignments and `pass`), whatever
   `sys` is imported as. Then every module-level assignment that is no longer used and
   only served the guard or computed a file location (from `__file__`, `os.path.*`,
   `pathlib` or `os.getcwd()`, or from another such name) goes, repeated until none is
   left, with the `del` of those names, the comment lines directly above every removed
   statement, and each import (`sys`, `os as _os`, `pathlib`, ...) that only they used.
   Three files load their modules through `NAME = importlib.import_module("dotted.name")`,
   which becomes `import dotted.name as NAME`, and `import importlib` goes once unused.
4. **Canvas.** Every `savefig` loses `bbox_inches=` and `pad_inches=` (`"tight"` crops
   the canvas by 30 to 50 px, the documented cause of the drift that the
   `impl-review.yml` canvas gate catches), and the dpi is rescaled so that
   `figsize * dpi` renders exactly 3200x1800 (16:9) or 2400x2400 (1:1). The figure size
   stays; the target is the one the figure's aspect reaches, so `(8, 4.5)` and `(16, 9)`
   map to 3200x1800 at dpi 400 and 200, `(6, 6)`, `(12, 12)` and `(16, 16)` to 2400x2400 at
   dpi 400, 200 and 150. The new dpi is written on `savefig` (added when missing) and on
   every literal `dpi=` of a figure creation call and `set_dpi(...)`, so code that
   measures in pixels before saving sees the same dpi. An integer dpi is used when one
   hits the target exactly; otherwise the shortest decimal that does (matplotlib
   truncates `figsize * dpi` to whole pixels, so `(7, 7)` gets dpi 342.9). When no dpi
   hits it exactly, because the aspect is a hair off (`(16, 9.05)`), the dpi renders one
   side exactly and the other within the 16 px of the canvas gate (3200x1810); the
   change line names the pixels and the offset, and `measure_canvas` and the readiness
   scan report it as a `canvas:` note. The figure
   size comes from the last literal `set_size_inches(w, h)` (seaborn grids), else from
   the single literal `figsize=`. The canvas rewrite is all or nothing: when the figure
   size is missing or not a literal, when its aspect reaches neither target within 16 px,
   or when a savefig takes `**kwargs`, `bbox_inches` and the dpi stay as they are and a
   note says why (`readiness.scan` reports it as a `canvas:` reason).

Each rewrite is checked with `ast.parse` and dropped with a note if it would not parse.
The result is idempotent: `normalise(normalise(x)) == normalise(x)`.
"""

import ast
import math
import re
from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction

from .regions import (
    STANDARD_TARGET,
    Number,
    Regions,
    SavefigCall,
    SourceIndex,
    Span,
    as_number,
    dotted_name,
    find_regions,
    is_standard_target,
)


SUPPORTED_LIBRARIES = frozenset({"matplotlib", "seaborn"})
# Modules whose import goes whenever nothing kept uses it: the guard family, all banned
# by the SECURITY validator.
GUARD_MODULES = frozenset({"sys", "importlib", "pathlib"})
LANDSCAPE = (3200, 1800)
SQUARE = (2400, 2400)
TARGETS = (LANDSCAPE, SQUARE)
TOLERANCE = 16  # px per axis, the impl-review.yml canvas gate
DEFAULT_DPI = 100  # matplotlib's figure.dpi; savefig.dpi defaults to the figure's
DROPPED_SAVEFIG_KEYWORDS = ("bbox_inches", "pad_inches")
HEADER_FIRST_LINE = "anyplot.ai"
MAX_DPI_DECIMALS = 6

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


@dataclass(frozen=True, slots=True)
class Normalised:
    """The normalised code, what changed, and what was left alone and why."""

    code: str
    changes: tuple[str, ...]
    notes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Canvas:
    """The canvas a source renders, as far as its literals tell.

    `pixels` is what matplotlib writes for `figsize` at `dpi`: each side truncated to
    whole pixels, as `RendererAgg` does. `target` is the nearer of the two canvases
    (the impl-review.yml rule). `note` is None exactly when `pixels == target`.
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
    steps: tuple[tuple[str, Callable[[str], tuple[str, list[str], list[str]]]], ...] = (
        ("header", _strip_header),
        ("savefig target", _rewrite_savefig_targets),
        ("sys.path guard", _strip_path_guard),
        ("title", _strip_title),
        ("canvas", _normalise_canvas),
    )
    for name, step in steps:
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


def measure_canvas(code: str) -> Canvas:
    """The canvas `code` renders, judged from its literals; raises `SyntaxError` if it does not parse."""
    regions = find_regions(code)
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
    target = min(TARGETS, key=lambda t: abs(pixels[0] - t[0]) + abs(pixels[1] - t[1]))
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
    ordered = sorted(TARGETS, key=lambda t: abs(math.log((width / height) / (t[0] / t[1]))))

    for target in ordered:
        tw, th = target

        def exact(d: float, t: tuple[int, int] = target) -> bool:
            return _pixels((width, height), d) == t

        low = max(Fraction(tw) / Fraction(width), Fraction(th) / Fraction(height))
        high = min(Fraction(tw + 1) / Fraction(width), Fraction(th + 1) / Fraction(height))
        literal = _nicest(low, high, exact)
        if literal is not None:
            return target, literal

    for target in ordered:
        tw, th = target

        def near(d: float, t: tuple[int, int] = target) -> bool:
            pw, ph = _pixels((width, height), d)
            return abs(pw - t[0]) <= TOLERANCE and abs(ph - t[1]) <= TOLERANCE

        for side, pixels in ((width, tw), (height, th)):
            literal = _nicest(Fraction(pixels) / Fraction(side), Fraction(pixels + 1) / Fraction(side), near)
            if literal is not None:
                return target, literal

    return (
        f"figsize {_fmt_size(size)} has aspect {width / height:.3f}; no dpi renders 3200x1800 (16:9) "
        f"or 2400x2400 (1:1) within {TOLERANCE} px without changing the figure size"
    )


def _pixels(size: tuple[Number, Number], dpi: float) -> tuple[int, int]:
    return int(float(size[0]) * dpi), int(float(size[1]) * dpi)


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


def _normalise_canvas(code: str) -> tuple[str, list[str], list[str]]:
    regions = find_regions(code)
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


# --- header and sys.path guard -----------------------------------------------------------


def _strip_header(code: str) -> tuple[str, list[str], list[str]]:
    tree = ast.parse(code)
    if not tree.body:
        return code, [], []
    first = tree.body[0]
    if not (
        isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str)
    ):
        return code, [], []
    text = first.value.value.strip()
    if not text or text.splitlines()[0].strip() != HEADER_FIRST_LINE:
        return code, [], []
    span = SourceIndex(code).lines_span(first)
    new_code = _rewrite_lines(code, set(range(span.first_line, span.last_line + 1)), {})
    return new_code, [f"removed the catalogue header at {span.lines()}"], []


def _strip_title(code: str) -> tuple[str, list[str], list[str]]:
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


def _loads(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}


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
    """A statement that only changes `sys.path` or `sys.modules` (compound ones may hold private helpers and `pass`)."""
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
        callee = dotted_name(stmt.value.func)
        return callee is not None and any(
            callee.startswith((f"{alias}.path.", f"{alias}.modules.")) for alias in aliases
        )
    if isinstance(stmt, ast.Assign):
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


def _theme_file_path(node: ast.expr) -> bool:
    """A path whose file name is `f"plot-{THEME}.png"`: `os.path.join(d, f)`, `d / f`, `str(d / f)`."""
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return is_standard_target(node.right)
    if isinstance(node, ast.Call) and not node.keywords:
        callee = dotted_name(node.func) or ""
        if callee.endswith("path.join") and len(node.args) >= 2:
            return is_standard_target(node.args[-1])
        if callee in ("str", "os.fspath") and len(node.args) == 1:
            return _theme_file_path(node.args[0])
    return False


def _rewrite_savefig_targets(code: str) -> tuple[str, list[str], list[str]]:
    tree = ast.parse(code)
    index = SourceIndex(code)
    assigned: dict[str, list[ast.Assign]] = {}
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            assigned.setdefault(stmt.targets[0].id, []).append(stmt)
    edits: list[TextEdit] = []
    changes: list[str] = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "savefig"):
            continue
        target = node.args[0] if node.args else next((kw.value for kw in node.keywords if kw.arg == "fname"), None)
        if target is None or is_standard_target(target):
            continue
        value: ast.expr | None = target
        if isinstance(target, ast.Name):
            earlier = [stmt for stmt in assigned.get(target.id, []) if stmt.lineno < node.lineno]
            value = earlier[-1].value if earlier else None
        if value is not None and _theme_file_path(value):
            span = index.node_span(target)
            edits.append((span.start, span.end, STANDARD_TARGET))
            old = _WHITESPACE.sub(" ", code[span.start : span.end])
            changes.append(f"savefig target {old} -> {STANDARD_TARGET} at {span.lines()}")
    if not edits:
        return code, [], []
    return _apply(code, edits), changes, []


def _import_module_rewrite(stmt: ast.stmt) -> tuple[str, str] | None:
    """`(module, name)` for `name = importlib.import_module("module")`."""
    if not (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name)):
        return None
    call = stmt.value
    if not (isinstance(call, ast.Call) and dotted_name(call.func) == "importlib.import_module"):
        return None
    if len(call.args) != 1 or call.keywords or not isinstance(call.args[0], ast.Constant):
        return None
    module = call.args[0].value
    if not isinstance(module, str) or not _MODULE_NAME.fullmatch(module):
        return None
    return module, stmt.targets[0].id


def _import_bindings(stmt: ast.Import | ast.ImportFrom) -> tuple[set[str], set[str]]:
    """The names an import binds and the top-level modules it imports."""
    if isinstance(stmt, ast.Import):
        bound = {alias.asname or alias.name.split(".")[0] for alias in stmt.names}
        return bound, {alias.name.split(".")[0] for alias in stmt.names}
    return {alias.asname or alias.name for alias in stmt.names}, {(stmt.module or "").split(".")[0]}


def _strip_path_guard(code: str) -> tuple[str, list[str], list[str]]:
    tree = ast.parse(code)
    body = tree.body
    sys_aliases = {
        alias.asname or alias.name
        for stmt in body
        if isinstance(stmt, ast.Import)
        for alias in stmt.names
        if alias.name == "sys"
    }
    rewrites = {id(stmt): rewrite for stmt in body if (rewrite := _import_module_rewrite(stmt)) is not None}
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
    while grown:  # dead helpers of the guard and dead file-location assignments, until none is left
        grown = False
        for stmt in body:
            names = _binds(stmt)
            if id(stmt) in removed or not names or not (names <= guard_loads or names <= path_names):
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
        remove.update(range(span.first_line, span.last_line + 1))
        line = span.first_line - 1
        while line >= 1 and index.line_text(line).lstrip().startswith("#"):
            remove.add(line)
            line -= 1
        if stmt in guard:
            label = "the sys.path guard"
        elif stmt in imports or isinstance(stmt, ast.Delete):
            label = f"the unused `{ast.unparse(stmt)}`"
        else:
            label = "an unused file-path helper"
        changes.append(f"removed {label} at {span.lines()}")

    for stmt in body:
        rewrite = rewrites.get(id(stmt))
        if rewrite is None or id(stmt) in removed:
            continue
        module, name = rewrite
        span = index.lines_span(stmt)
        statement = f"import {module}" if module == name else f"import {module} as {name}"
        replace[span.first_line] = (span.last_line, statement + _newline(index, span.last_line))
        changes.append(f"{name} = importlib.import_module({module!r}) -> {statement} at {span.lines()}")

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
    module-level statements), or to none at the start of the file.
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

    for join in reversed(joins):
        before = 0
        while join - before - 1 >= 0 and blank(out[join - before - 1]):
            before += 1
        after = 0
        while join + after < len(out) and blank(out[join + after]):
            after += 1
        allowed = 0 if join - before == 0 else 2
        excess = before + after - allowed
        if excess <= 0:
            continue
        cut_after = min(after, excess)
        cut_before = excess - cut_after
        del out[join : join + cut_after]
        del out[join - cut_before : join]
    return "".join(out)
