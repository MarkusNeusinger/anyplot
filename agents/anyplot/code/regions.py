"""Find the catalogue conventions in plot source by AST, as spans the other code modules work around.

A catalogue implementation (`plots/*/implementations/python/{matplotlib,seaborn}.py`)
follows conventions that the adapter must keep and the normaliser rewrites:

* the theme block: `THEME = os.getenv("ANYPLOT_THEME", "light")`, then module-level
  tokens whose value tests the theme, such as
  `PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"` (`PAGE_BG`, `ELEVATED_BG`,
  `INK`, `INK_SOFT`, `INK_MUTED`, `GRID`, `BRAND`, ...);
* the Imprint palette list, `IMPRINT = [...]` (124 files) or `IMPRINT_PALETTE = [...]`
  (89 files);
* one final `plt.savefig(f"plot-{THEME}.png", dpi=..., facecolor=PAGE_BG)` statement
  (also `fig.savefig` and `g.figure.savefig`);
* the canvas: `figsize=` and `dpi=` on the figure creation call (`plt.subplots`,
  `plt.figure`, `plt.subplot_mosaic`, `sns.clustermap`), `set_size_inches` and
  `set_dpi` on the figure of a seaborn grid, and `dpi=` on savefig;
* in an adapted working form, the placeholder statement `df = load_user_data()`.

Lines are 1-based and inclusive; offsets are 0-based character offsets into the
source string with an exclusive end, so `code[span.start:span.end]` is the region.
`ast` reports columns in UTF-8 bytes; `SourceIndex` converts them, so non-ASCII text
before a node (the catalogue uses `·`, `→` and `≈`) does not shift a span.
"""

import ast
import bisect
import re
from dataclasses import dataclass
from typing import Literal


PLACEHOLDER = "df = load_user_data()"
PLACEHOLDER_FUNC = "load_user_data"
THEME_NAME = "THEME"
THEME_ENV = "ANYPLOT_THEME"
STANDARD_TARGET = 'f"plot-{THEME}.png"'
IMPRINT_NAMES = frozenset({"IMPRINT", "IMPRINT_PALETTE"})
# Callees (last dotted component) that create a figure and may carry `dpi=` without `figsize=`.
FIGURE_FUNCS = frozenset({"figure", "subplots", "subplot_mosaic"})
SIZE_METHODS = frozenset({"set_size_inches", "set_dpi"})
HEX_COLOR = re.compile(r"#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?")  # used with fullmatch

# Python's universal newlines: a physical line ends at CR LF, LF or a lone CR.
_NEWLINE = re.compile(r"\r\n|\r|\n")

RegionKind = Literal["theme", "theme_token", "placeholder", "savefig"]
SizeMethod = Literal["set_size_inches", "set_dpi"]
Number = int | float


@dataclass(frozen=True, slots=True)
class Span:
    """A region of a source string: lines `first_line..last_line` and characters `[start, end)`."""

    first_line: int
    last_line: int
    start: int
    end: int

    def overlaps(self, start: int, end: int) -> bool:
        """Whether the half-open character range `[start, end)` shares a character with this span."""
        return start < self.end and self.start < end

    def lines(self) -> str:
        """`line 12` or `lines 12-14`, for messages."""
        if self.first_line == self.last_line:
            return f"line {self.first_line}"
        return f"lines {self.first_line}-{self.last_line}"


class SourceIndex:
    """Maps `ast` positions (1-based line, UTF-8 byte column) to character offsets and back."""

    def __init__(self, code: str) -> None:
        self.code = code
        self._starts = [0, *(match.end() for match in _NEWLINE.finditer(code))]

    @property
    def line_count(self) -> int:
        """Number of lines; a trailing newline opens an empty last line."""
        return len(self._starts)

    def line_start(self, line: int) -> int:
        """Offset of the first character of `line`."""
        return self._starts[line - 1]

    def line_end(self, line: int) -> int:
        """Offset just past the newline that ends `line` (the end of the source on the last line)."""
        return self._starts[line] if line < len(self._starts) else len(self.code)

    def line_text(self, line: int) -> str:
        """The text of `line` including its newline."""
        return self.code[self.line_start(line) : self.line_end(line)]

    def line_of(self, offset: int) -> int:
        """The 1-based line that holds the character at `offset`."""
        return bisect.bisect_right(self._starts, offset)

    def offset(self, line: int, col: int) -> int:
        """Character offset of the `ast` position `line`, `col` (col in UTF-8 bytes)."""
        start = self._starts[line - 1]
        prefix = self.code[start : start + col]
        if prefix.isascii():
            return start + col
        raw = self.code[start : self.line_end(line)].encode("utf-8")[:col]
        return start + len(raw.decode("utf-8"))

    def node_span(self, node: ast.stmt | ast.expr | ast.keyword) -> Span:
        """The exact characters of `node`."""
        first, col, last, end_col = _position(node)
        return Span(first, last, self.offset(first, col), self.offset(last, end_col))

    def lines_span(self, node: ast.stmt | ast.expr | ast.keyword) -> Span:
        """The whole lines of `node`, newline of its last line included."""
        first, _, last, _ = _position(node)
        return Span(first, last, self.line_start(first), self.line_end(last))


def _position(node: ast.stmt | ast.expr | ast.keyword) -> tuple[int, int, int, int]:
    if node.end_lineno is None or node.end_col_offset is None:  # never for parsed source
        raise ValueError(f"{type(node).__name__} has no end position")
    return node.lineno, node.col_offset, node.end_lineno, node.end_col_offset


@dataclass(frozen=True, slots=True)
class Region:
    """A protected statement; `span` covers its whole lines."""

    kind: RegionKind
    name: str
    span: Span


@dataclass(frozen=True, slots=True)
class Palette:
    """A module-level list or tuple literal of colour strings; `span` covers its whole lines."""

    name: str
    entries: tuple[str, ...]
    span: Span


@dataclass(frozen=True, slots=True)
class Keyword:
    """One `name=value` argument; `value` is the literal value, or None when `literal` is False."""

    name: str
    span: Span
    value_span: Span
    value: object
    literal: bool


@dataclass(frozen=True, slots=True)
class FigureCall:
    """A figure creation call with its canvas keywords."""

    func: str
    span: Span
    figsize: Keyword | None
    dpi: Keyword | None


@dataclass(frozen=True, slots=True)
class SizeCall:
    """`<figure>.set_size_inches(w, h)` or `<figure>.set_dpi(d)`.

    `value` is `(w, h)` or `d` when the arguments are numeric literals, else None.
    `value_span` covers the argument(s), so a dpi rewrite replaces exactly them.
    """

    func: str
    method: SizeMethod
    span: Span
    value: tuple[Number, Number] | Number | None
    value_span: Span | None


@dataclass(frozen=True, slots=True)
class SavefigCall:
    """A `savefig(...)` call.

    `statement` is the whole lines of the enclosing statement when the call is a
    module-level expression statement, else None. `target` is the source of the file
    argument (first positional or `fname=`); `literal_target` its value when it is a
    plain string such as `"plot.png"` (a single-theme target). `items` are the argument
    spans in source order, so a keyword can be cut together with its separating comma.
    """

    func: str
    span: Span
    statement: Span | None
    target: str | None
    standard_target: bool
    literal_target: str | None
    dpi: Keyword | None
    keywords: tuple[Keyword, ...]
    items: tuple[Span, ...]
    has_splat: bool


@dataclass(frozen=True, slots=True)
class Regions:
    """Everything `find_regions` located in one source string."""

    theme: Region | None
    theme_tokens: tuple[Region, ...]
    placeholders: tuple[Region, ...]
    imprint: Palette | None
    palettes: tuple[Palette, ...]
    figure_calls: tuple[FigureCall, ...]
    size_calls: tuple[SizeCall, ...]
    savefig_calls: tuple[SavefigCall, ...]
    savefig: SavefigCall | None

    @property
    def protected(self) -> tuple[Region, ...]:
        """The regions an edit may not touch: THEME, the theme tokens, the placeholder, the final savefig.

        The Imprint palette is not protected: the adapter may extend it, and the
        ADAPTATION validator checks that its existing entries keep their order.
        """
        regions = [*([self.theme] if self.theme else []), *self.theme_tokens, *self.placeholders]
        if self.savefig is not None and self.savefig.statement is not None:
            regions.append(Region("savefig", self.savefig.func, self.savefig.statement))
        return tuple(sorted(regions, key=lambda region: region.span.start))


def dotted_name(node: ast.expr) -> str | None:
    """`a.b.c` for a chain of names and attributes, else None."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(node.id)
    return ".".join(reversed(parts))


def is_theme_assignment(stmt: ast.stmt) -> bool:
    """`THEME = os.getenv("ANYPLOT_THEME", ...)`, the only form the SECURITY validator allows for `os`."""
    if isinstance(stmt, ast.Assign):
        if len(stmt.targets) != 1:
            return False
        target, value = stmt.targets[0], stmt.value
    elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
        target, value = stmt.target, stmt.value
    else:
        return False
    if not (isinstance(target, ast.Name) and target.id == THEME_NAME and isinstance(value, ast.Call)):
        return False
    return (
        dotted_name(value.func) == "os.getenv"
        and len(value.args) in (1, 2)
        and isinstance(value.args[0], ast.Constant)
        and value.args[0].value == THEME_ENV
    )


def tests_theme(value: ast.expr) -> bool:
    """Whether a value tests the theme: `x if THEME == "light" else y`, or `THEME != "dark"` itself."""
    test = value.test if isinstance(value, ast.IfExp) else value
    if not isinstance(test, ast.Compare):
        return False
    operands = [test.left, *test.comparators]
    return any(isinstance(op, ast.Eq | ast.NotEq) for op in test.ops) and any(
        isinstance(operand, ast.Name) and operand.id == THEME_NAME for operand in operands
    )


def is_placeholder(node: ast.AST) -> bool:
    """The statement `df = load_user_data()`."""
    return (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "df"
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == PLACEHOLDER_FUNC
        and not node.value.args
        and not node.value.keywords
    )


def is_standard_target(node: ast.expr) -> bool:
    """Exactly `f"plot-{THEME}.png"`: no conversion, no format spec."""
    if not isinstance(node, ast.JoinedStr) or len(node.values) != 3:
        return False
    head, middle, tail = node.values
    return (
        isinstance(head, ast.Constant)
        and head.value == "plot-"
        and isinstance(middle, ast.FormattedValue)
        and isinstance(middle.value, ast.Name)
        and middle.value.id == THEME_NAME
        and middle.conversion == -1
        and middle.format_spec is None
        and isinstance(tail, ast.Constant)
        and tail.value == ".png"
    )


def _assigned_names(stmt: ast.stmt) -> list[str] | None:
    """The names a module-level assignment binds, or None for anything else."""
    if isinstance(stmt, ast.Assign):
        targets = stmt.targets
    elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
        targets = [stmt.target]
    else:
        return None
    if not all(isinstance(target, ast.Name) for target in targets):
        return None
    return [target.id for target in targets if isinstance(target, ast.Name)]


def _literal(node: ast.expr) -> tuple[object, bool]:
    try:
        return ast.literal_eval(node), True
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        return None, False


def _keyword(index: SourceIndex, keyword: ast.keyword) -> Keyword:
    value, literal = _literal(keyword.value)
    return Keyword(
        name=keyword.arg or "**",
        span=index.node_span(keyword),
        value_span=index.node_span(keyword.value),
        value=value,
        literal=literal,
    )


def _palette(index: SourceIndex, stmt: ast.stmt, names: list[str]) -> Palette | None:
    value = stmt.value if isinstance(stmt, ast.Assign | ast.AnnAssign) else None
    if len(names) != 1 or not isinstance(value, ast.List | ast.Tuple) or not value.elts:
        return None
    entries = [elt.value for elt in value.elts if isinstance(elt, ast.Constant) and isinstance(elt.value, str)]
    if len(entries) != len(value.elts):
        return None
    return Palette(name=names[0], entries=tuple(entries), span=index.lines_span(stmt))


def as_number(value: object) -> Number | None:
    """`value` when it is an int or float (never a bool), else None."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return value


def as_size(value: object) -> tuple[Number, Number] | None:
    """`(w, h)` when `value` is a pair of numbers, else None."""
    if not isinstance(value, tuple | list) or len(value) != 2:
        return None
    width, height = as_number(value[0]), as_number(value[1])
    if width is None or height is None:
        return None
    return width, height


def _size_call(index: SourceIndex, call: ast.Call, method: SizeMethod) -> SizeCall:
    value: tuple[Number, Number] | Number | None = None
    value_span: Span | None = None
    if call.args and all(kw.arg == "forward" for kw in call.keywords):
        first, last = index.node_span(call.args[0]), index.node_span(call.args[-1])
        value_span = Span(first.first_line, last.last_line, first.start, last.end)
        literals = [_literal(arg) for arg in call.args]
        if all(ok for _, ok in literals):
            values = [literal for literal, _ in literals]
            if method == "set_dpi" and len(values) == 1:
                value = as_number(values[0])
            elif method == "set_size_inches":
                value = as_size(values[0] if len(values) == 1 else tuple(values))
    return SizeCall(
        func=ast.unparse(call.func), method=method, span=index.node_span(call), value=value, value_span=value_span
    )


def _savefig_call(index: SourceIndex, call: ast.Call, statement: Span | None) -> SavefigCall:
    keywords = tuple(_keyword(index, kw) for kw in call.keywords)
    items = sorted([index.node_span(arg) for arg in call.args] + [kw.span for kw in keywords], key=lambda s: s.start)
    target_node = call.args[0] if call.args else next((kw.value for kw in call.keywords if kw.arg == "fname"), None)
    return SavefigCall(
        func=ast.unparse(call.func),
        span=index.node_span(call),
        statement=statement,
        target=ast.unparse(target_node) if target_node is not None else None,
        standard_target=target_node is not None and is_standard_target(target_node),
        literal_target=(
            target_node.value if isinstance(target_node, ast.Constant) and isinstance(target_node.value, str) else None
        ),
        dpi=next((kw for kw in keywords if kw.name == "dpi"), None),
        keywords=keywords,
        items=tuple(items),
        has_splat=any(kw.arg is None for kw in call.keywords) or any(isinstance(a, ast.Starred) for a in call.args),
    )


def find_regions(code: str, tree: ast.Module | None = None) -> Regions:
    """Locate the conventions in `code`; raises `SyntaxError` when it does not parse.

    Pass `tree` when the caller already parsed exactly this `code`.
    """
    if tree is None:
        tree = ast.parse(code)
    index = SourceIndex(code)

    theme: Region | None = None
    tokens: list[Region] = []
    palettes: list[Palette] = []
    imprint: Palette | None = None
    module_savefig: dict[int, Span] = {}  # id(call) -> statement lines, for module-level savefig statements
    for stmt in tree.body:
        if theme is None and is_theme_assignment(stmt):
            theme = Region("theme", THEME_NAME, index.lines_span(stmt))
            continue
        names = _assigned_names(stmt)
        if names is not None and isinstance(stmt, ast.Assign | ast.AnnAssign) and stmt.value is not None:
            if THEME_NAME not in names and tests_theme(stmt.value):
                tokens.append(Region("theme_token", ", ".join(names), index.lines_span(stmt)))
            palette = _palette(index, stmt, names)
            if palette is not None:
                if imprint is None and palette.name in IMPRINT_NAMES:
                    imprint = palette
                if len(palette.entries) >= 2 and all(HEX_COLOR.fullmatch(entry) for entry in palette.entries):
                    palettes.append(palette)
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            module_savefig[id(stmt.value)] = index.lines_span(stmt)

    placeholders: list[Region] = []
    figure_calls: list[FigureCall] = []
    size_calls: list[SizeCall] = []
    savefig_calls: list[SavefigCall] = []
    for node in ast.walk(tree):
        if is_placeholder(node) and isinstance(node, ast.Assign):
            placeholders.append(Region("placeholder", PLACEHOLDER, index.lines_span(node)))
        if not isinstance(node, ast.Call):
            continue
        callee = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", None)
        if callee == "savefig":
            savefig_calls.append(_savefig_call(index, node, module_savefig.get(id(node))))
        elif callee in SIZE_METHODS:
            method: SizeMethod = "set_size_inches" if callee == "set_size_inches" else "set_dpi"
            size_calls.append(_size_call(index, node, method))
        else:
            keywords = {kw.arg: kw for kw in node.keywords if kw.arg in ("figsize", "dpi")}
            if "figsize" in keywords or ("dpi" in keywords and callee in FIGURE_FUNCS):
                figure_calls.append(
                    FigureCall(
                        func=ast.unparse(node.func),
                        span=index.node_span(node),
                        figsize=_keyword(index, keywords["figsize"]) if "figsize" in keywords else None,
                        dpi=_keyword(index, keywords["dpi"]) if "dpi" in keywords else None,
                    )
                )

    by_start = sorted(savefig_calls, key=lambda call: call.span.start)
    final = by_start[-1] if by_start else None
    return Regions(
        theme=theme,
        theme_tokens=tuple(tokens),
        placeholders=tuple(sorted(placeholders, key=lambda region: region.span.start)),
        imprint=imprint,
        palettes=tuple(palettes),
        figure_calls=tuple(sorted(figure_calls, key=lambda call: call.span.start)),
        size_calls=tuple(sorted(size_calls, key=lambda call: call.span.start)),
        savefig_calls=tuple(by_start),
        savefig=final if final is not None and final.statement is not None else None,
    )
