"""Find the catalogue conventions in plot source by AST, as spans the other code modules work around.

A catalogue implementation (`plots/*/implementations/python/<library>.py`) follows
conventions that the adapter must keep and the normaliser rewrites:

* the theme block: `THEME = os.getenv("ANYPLOT_THEME", "light")`, then module-level
  tokens that pick a fixed value per theme, such as
  `PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"` (`PAGE_BG`, `ELEVATED_BG`,
  `INK`, `INK_SOFT`, `INK_MUTED`, `GRID`, `BRAND`, ...). A token's value tests the
  theme and is built only from literals, `THEME` and earlier tokens
  (`EDGE = INK_SOFT if THEME == "light" else PAGE_BG` is one). An assignment whose
  branch reads anything else, such as box-basic's
  `_tight_text_color = INK if THEME == "dark" else IMPRINT_PALETTE[tightest_idx]`, is
  plot code that follows the data, not a token: the adapter must be able to rewrite it
  (in the 650 matplotlib and seaborn files it is the only one of 2,745);
* the Imprint palette list, `IMPRINT = [...]` (124 files) or `IMPRINT_PALETTE = [...]`
  (89 files);
* one final save statement that writes `f"plot-{THEME}.png"`: the library's save call
  (`SAVE_RULES`): `plt.savefig(f"plot-{THEME}.png", dpi=..., facecolor=PAGE_BG)` for
  matplotlib and seaborn (also `fig.savefig` and `g.figure.savefig`),
  `plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")` or
  `ggsave(plot, f"plot-{THEME}.png", ...)` for plotnine (the file is the second
  positional of `ggsave`), `chart.save(f"plot-{THEME}.png", scale_factor=4.0)` for
  altair, whose files also save `f"plot-{THEME}.html"` and reopen the PNG with PIL to
  pad it (`_canvas.save(f"plot-{THEME}.png")`), `chart.render_to_png(f"plot-{THEME}.png")`
  or `cairosvg.svg2png(bytestring=..., write_to=f"plot-{THEME}.png")` for pygal (with
  `chart.render_to_file(f"plot-{THEME}.html")`), and
  `ggsave(plot, f"plot-{THEME}.png", path=".", scale=2)` for lets-plot (with the HTML
  save). Every call of the library's save names is a save call; the protected final one
  is the last module-level statement among those that write the PNG. plotly and bokeh
  have no save name: their save is the pinned statement that writes the figure as
  `f"plot-{THEME}.json"` (`code/figure.py`), and the last module-level one is protected;
* the canvas: `figsize=` and `dpi=` on the figure creation call (`plt.subplots`,
  `plt.figure`, `plt.subplot_mosaic`, `sns.clustermap`), `set_size_inches` and
  `set_dpi` on the figure of a seaborn grid, and `dpi=` on savefig (the other libraries
  size their canvas elsewhere, `SaveRule.canvas`);
* in an adapted working form, the placeholder statement `df = load_user_data()`.

Lines are 1-based and inclusive; offsets are 0-based character offsets into the
source string with an exclusive end, so `code[span.start:span.end]` is the region.
`ast` reports columns in UTF-8 bytes; `SourceIndex` converts them, so non-ASCII text
before a node (the catalogue uses `·`, `→` and `≈`) does not shift a span.
"""

import ast
import bisect
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Literal

from .figure import FIGURE_TARGET, FigureKind, figure_saves


PLACEHOLDER = "df = load_user_data()"
PLACEHOLDER_FUNC = "load_user_data"
THEME_NAME = "THEME"
THEME_ENV = "ANYPLOT_THEME"
STANDARD_TARGET = 'f"plot-{THEME}.png"'
HTML_TARGET = 'f"plot-{THEME}.html"'
PNG_SUFFIX = ".png"
HTML_SUFFIX = ".html"
IMPRINT_NAMES = frozenset({"IMPRINT", "IMPRINT_PALETTE"})
# Callees (last dotted component) that create a figure and may carry `dpi=` without `figsize=`.
FIGURE_FUNCS = frozenset({"figure", "subplots", "subplot_mosaic"})
SIZE_METHODS = frozenset({"set_size_inches", "set_dpi"})
HEX_COLOR = re.compile(r"#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?")  # used with fullmatch

# Python's universal newlines: a physical line ends at CR LF, LF or a lone CR.
_NEWLINE = re.compile(r"\r\n|\r|\n")

RegionKind = Literal["theme", "theme_token", "placeholder", "savefig"]
SizeMethod = Literal["set_size_inches", "set_dpi"]
CanvasRewrite = Literal["figure", "pygal", "letsplot"]
"""How the normaliser sets a library's canvas: matplotlib's figure size times dpi (`figure`), pygal's chart size
through the PNG save's output size (`pygal`), lets-plot's `scale=` on the PNG save (`letsplot`)."""
Number = int | float


@dataclass(frozen=True)
class SaveRule:
    """How one library's code writes the plot file (module docstring, "one final save statement").

    `names` are the callee names (the last dotted component) that save the plot; the
    file is the positional at `positions[name]` (0 unless listed) or one of
    `target_keywords`; a name in `keyword_only` takes its file by keyword alone
    (`cairosvg.svg2png`, whose first positional is the SVG). `keywords[name]` lists the
    keywords a save may take, None for any (matplotlib's `savefig`, whose settings the
    validator checks one by one). `html` admits a second save of exactly
    `f"plot-{THEME}.html"` next to the PNG, `reopens` a `.open(...)` of the PNG (altair's
    PIL padding block), `directory` the one literal every save passes as `path=`
    (lets-plot, whose `ggsave` writes into `./lets-plot-images` without it), `writes[name]`
    the one suffix a save name may write where the names each write one kind of file
    (pygal: `render_to_file` writes SVG text, so only the HTML; a name not listed writes any
    target of the rule), and `canvas` names the normaliser's canvas rewrite for the library,
    None where it has none yet. `figure` names a library that saves its figure as JSON through
    one pinned statement (`code/figure.py`: plotly and bokeh, drawn by the renderer's figure
    mode) and has no save name at all.
    """

    names: frozenset[str]
    target_keywords: frozenset[str]
    positions: Mapping[str, int] = field(default_factory=lambda: MappingProxyType({}))
    keywords: Mapping[str, frozenset[str] | None] = field(default_factory=lambda: MappingProxyType({}))
    keyword_only: frozenset[str] = frozenset()
    html: bool = False
    reopens: bool = False
    directory: str | None = None
    writes: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))
    canvas: CanvasRewrite | None = "figure"
    figure: FigureKind | None = None

    @property
    def verb(self) -> str:
        """The save name a message uses for this library: `savefig` for matplotlib, `save` for the others."""
        return "savefig" if "savefig" in self.names and len(self.names) == 1 else "save"

    def target_position(self, name: str) -> int:
        """The position of the file argument of `name`; -1 for a save that takes its file by keyword only."""
        if name in self.keyword_only:
            return -1
        return self.positions.get(name, 0)

    def allowed_keywords(self, name: str) -> frozenset[str] | None:
        return self.keywords.get(name)

    def writes_suffix(self, name: str, suffix: str) -> bool:
        """Whether the save name `name` may write a file ending in `suffix` (`PNG_SUFFIX` or `HTML_SUFFIX`)."""
        only = self.writes.get(name)
        return only is None or only == suffix


_PLOTNINE_SAVE_KEYWORDS = frozenset({"filename", "format", "width", "height", "units", "dpi", "limitsize", "verbose"})
"""`ggplot.save(filename, format, path, width, height, units, dpi, limitsize, verbose, **kwargs)` without `path=`
(a directory joined onto the file) and without the `**kwargs` it hands to savefig."""
_ALTAIR_SAVE_KEYWORDS = frozenset({"fp", "format", "scale_factor", "ppi", "inline", "embed_options"})
"""`Chart.save(fp, format, override_data_transformer, scale_factor, mode, vegalite_version, vega_version,
vegaembed_version, embed_options, json_kwds, webdriver, engine, inline, **kwargs)`: the size and the HTML embedding
only; `webdriver=` and `engine=` choose how the PNG is made and stay with altair's default, vl-convert in process."""
_PYGAL_SVG2PNG_KEYWORDS = frozenset(
    {
        "bytestring",
        "write_to",
        "dpi",
        "scale",
        "output_width",
        "output_height",
        "parent_width",
        "parent_height",
        "background_color",
        "negate_colors",
        "invert_images",
    }
)
"""`cairosvg.svg2png(bytestring, *, file_obj, url, dpi, parent_width, parent_height, scale, unsafe,
background_color, negate_colors, invert_images, write_to, output_width, output_height)` without `url=` and
`file_obj=`, which read the main input through cairosvg's unrestricted fetcher (any path, any URL), and `unsafe=`
(external entities and hrefs)."""
_PYGAL_SAVE_KEYWORDS: Mapping[str, frozenset[str] | None] = MappingProxyType(
    {
        # `render_to_png(filename=None, dpi=72, **kwargs)` and `render_to_file(filename, **kwargs)` hand their
        # `**kwargs` to `render()` and from there into the chart's config (`css=`, `js=`, `defs=`), so a save takes
        # none of them.
        "render_to_png": frozenset({"filename", "dpi"}),
        "render_to_file": frozenset({"filename"}),
        "svg2png": _PYGAL_SVG2PNG_KEYWORDS,
    }
)
_LETSPLOT_SAVE_KEYWORDS = frozenset({"filename", "path", "scale", "w", "h", "unit", "dpi"})
"""`ggsave(plot, filename, *, path=None, iframe=True, scale=None, w=None, h=None, unit=None, dpi=None)`: the file, the
directory (`SaveRule.directory`) and the raster size; `iframe=` shapes only the HTML and no catalogue file passes it."""
_MATPLOTLIB_SAVE = SaveRule(names=frozenset({"savefig"}), target_keywords=frozenset({"fname"}))
SAVE_RULES: Mapping[str, SaveRule] = MappingProxyType(
    {
        "matplotlib": _MATPLOTLIB_SAVE,
        "seaborn": _MATPLOTLIB_SAVE,
        # `plot.save(...)`, `ggsave(plot, ...)` and, after `fig = plot.draw()`, matplotlib's `fig.savefig(...)`.
        "plotnine": SaveRule(
            names=frozenset({"save", "ggsave", "savefig"}),
            target_keywords=frozenset({"filename", "fname"}),
            positions=MappingProxyType({"ggsave": 1}),
            keywords=MappingProxyType({"save": _PLOTNINE_SAVE_KEYWORDS, "ggsave": _PLOTNINE_SAVE_KEYWORDS}),
            canvas=None,
        ),
        "altair": SaveRule(
            names=frozenset({"save"}),
            target_keywords=frozenset({"fp"}),
            keywords=MappingProxyType({"save": _ALTAIR_SAVE_KEYWORDS}),
            html=True,
            reopens=True,
            canvas=None,
        ),
        # `chart.render_to_png(f"plot-{THEME}.png")` (220 of 325 catalogue files end on it),
        # `cairosvg.svg2png(bytestring=chart.render(), write_to=f"plot-{THEME}.png", ...)` (92) and
        # `chart.render_to_file(f"plot-{THEME}.html")`. libcairo writes the PNG with its own `fopen`, which the
        # harness's audit hook never sees, so the file rests on this rule alone (survey of 2026-10-24).
        "pygal": SaveRule(
            names=frozenset({"render_to_png", "render_to_file", "svg2png"}),
            target_keywords=frozenset({"filename", "write_to"}),
            keywords=_PYGAL_SAVE_KEYWORDS,
            keyword_only=frozenset({"svg2png"}),
            html=True,
            writes=MappingProxyType(
                {"render_to_png": PNG_SUFFIX, "svg2png": PNG_SUFFIX, "render_to_file": HTML_SUFFIX}
            ),
            canvas="pygal",
        ),
        # `ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)` and the same call for the HTML: every one of the 325
        # catalogue files saves both, the file as the second positional or `filename=`; 292 pass `path="."`, and the
        # normaliser adds it to the other saves.
        "letsplot": SaveRule(
            names=frozenset({"ggsave"}),
            target_keywords=frozenset({"filename"}),
            positions=MappingProxyType({"ggsave": 1}),
            keywords=MappingProxyType({"ggsave": _LETSPLOT_SAVE_KEYWORDS}),
            html=True,
            directory=".",
            canvas="letsplot",
        ),
        # The figure as JSON through one pinned statement (`code/figure.py`), which the renderer's figure mode draws:
        # `fig.update_layout(width=800, height=450).write_json(f"plot-{THEME}.json")` for plotly, `with open(...) as
        # figure_file: json.dump(json_item(p), figure_file)` for bokeh. No save name: the catalogue's `write_image`,
        # `write_html`, `export_png` and `save` start a browser or write HTML, so the normaliser replaces them and the
        # validator refuses them (PB-2a, 2026-10-31).
        "plotly": SaveRule(names=frozenset(), target_keywords=frozenset(), canvas=None, figure="plotly"),
        "bokeh": SaveRule(names=frozenset(), target_keywords=frozenset(), canvas=None, figure="bokeh"),
    }
)
"""The save rule of every library with a Python code profile; `SUPPORTED_LIBRARIES` of the normaliser is its keys."""
SAVE_NAMES: frozenset[str] = frozenset(name for rule in SAVE_RULES.values() for name in rule.names)
"""Every save name of every rule: a call by one of them is a save call in every profile, allowed or not. plotly's and
bokeh's rules name none (`SaveRule.figure`)."""


def save_rule(library: str) -> SaveRule:
    """The save rule of `library`; `ValueError` for a library without a Python code profile."""
    try:
        return SAVE_RULES[library]
    except KeyError:
        raise ValueError(f"no save rule for library {library!r}; supported: {sorted(SAVE_RULES)}") from None


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
    """A save call: `savefig(...)`, or the library's own save (`SaveRule.names`).

    `statement` is the whole lines of the enclosing statement when the call is a
    module-level expression statement, else None. `target` is the source of the file
    argument (the rule's positional or keyword); `literal_target` its value when it is a
    plain string such as `"plot.png"` (a single-theme target). `standard_target` is
    exactly `f"plot-{THEME}.png"`, `html_target` exactly `f"plot-{THEME}.html"` (altair's
    second file). `items` are the argument spans in source order, so a keyword can be cut
    together with its separating comma.
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
    html_target: bool = False

    @property
    def name(self) -> str:
        """The callee's last dotted component: `savefig`, `save` or `ggsave`."""
        return self.func.rsplit(".", 1)[-1]


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
        """The regions an edit may not touch: THEME, the theme tokens, the placeholder, the final save statement.

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


def is_theme_constant(value: ast.expr, known: set[str]) -> bool:
    """Whether `value` is built only from literals and the names in `known` (THEME and earlier tokens).

    A conditional expression and a comparison are walked part by part; any other node
    must be a literal (`ast.literal_eval` accepts it: strings, numbers, and lists,
    tuples or dicts of them).
    """
    if isinstance(value, ast.IfExp):
        return all(is_theme_constant(part, known) for part in (value.test, value.body, value.orelse))
    if isinstance(value, ast.Compare):
        return all(is_theme_constant(part, known) for part in (value.left, *value.comparators))
    if isinstance(value, ast.Name):
        return value.id in known
    return _literal(value)[1]


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


def is_theme_target(node: ast.expr, suffix: str = PNG_SUFFIX) -> bool:
    """Exactly `f"plot-{THEME}<suffix>"`: no conversion, no format spec."""
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
        and tail.value == suffix
    )


def is_standard_target(node: ast.expr) -> bool:
    """Exactly `f"plot-{THEME}.png"`: no conversion, no format spec."""
    return is_theme_target(node, PNG_SUFFIX)


def save_target(call: ast.Call, rule: SaveRule, name: str) -> ast.expr | None:
    """The file argument of the save call `name` under `rule`: its positional, else one of the rule's keywords."""
    position = rule.target_position(name)
    if (
        position >= 0
        and len(call.args) > position
        and not any(isinstance(arg, ast.Starred) for arg in call.args[: position + 1])
    ):
        return call.args[position]
    return next((kw.value for kw in call.keywords if kw.arg in rule.target_keywords), None)


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
    except ValueError, TypeError, SyntaxError, MemoryError, RecursionError:
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


def _savefig_call(index: SourceIndex, call: ast.Call, statement: Span | None, rule: SaveRule, name: str) -> SavefigCall:
    keywords = tuple(_keyword(index, kw) for kw in call.keywords)
    items = sorted([index.node_span(arg) for arg in call.args] + [kw.span for kw in keywords], key=lambda s: s.start)
    target_node = save_target(call, rule, name)
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
        html_target=target_node is not None and is_theme_target(target_node, HTML_SUFFIX),
    )


def _figure_names(tree: ast.Module, kind: FigureKind) -> list[tuple[ast.stmt, str]]:
    """Each module-level pinned figure save of `kind` with its save's callee: `write_json` or `json.dump`."""
    return [(stmt, "write_json" if kind == "plotly" else "json.dump") for stmt, _ in figure_saves(tree, kind)]


def _figure_call(index: SourceIndex, stmt: ast.stmt, func: str) -> SavefigCall:
    """A pinned figure save as the region's save call: the whole statement, the figure's own target."""
    return SavefigCall(
        func=func,
        span=index.node_span(stmt),
        statement=index.lines_span(stmt),
        target=FIGURE_TARGET,
        standard_target=True,
        literal_target=None,
        dpi=None,
        keywords=(),
        items=(),
        has_splat=False,
    )


def find_regions(code: str, tree: ast.Module | None = None, *, library: str = "matplotlib") -> Regions:
    """Locate the conventions in `code`; raises `SyntaxError` when it does not parse.

    Pass `tree` when the caller already parsed exactly this `code`. `library` picks the
    save rule (`SAVE_RULES`): which calls count as save calls and where their file is.
    """
    rule = save_rule(library)
    if tree is None:
        tree = ast.parse(code)
    index = SourceIndex(code)

    theme: Region | None = None
    tokens: list[Region] = []
    known = {THEME_NAME}  # the names a token's value may read: THEME and the tokens above it
    palettes: list[Palette] = []
    imprint: Palette | None = None
    module_savefig: dict[int, Span] = {}  # id(call) -> statement lines, for module-level savefig statements
    for stmt in tree.body:
        if theme is None and is_theme_assignment(stmt):
            theme = Region("theme", THEME_NAME, index.lines_span(stmt))
            continue
        names = _assigned_names(stmt)
        if names is not None and isinstance(stmt, ast.Assign | ast.AnnAssign) and stmt.value is not None:
            value = stmt.value
            if THEME_NAME not in names and tests_theme(value) and is_theme_constant(value, known):
                tokens.append(Region("theme_token", ", ".join(names), index.lines_span(stmt)))
                known.update(names)
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
        if callee in rule.names:
            savefig_calls.append(_savefig_call(index, node, module_savefig.get(id(node)), rule, callee))
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

    if rule.figure is not None:
        # plotly and bokeh have no save name: their save is the pinned figure statement (`code/figure.py`), and the
        # last module-level one is the protected final save.
        savefig_calls = [_figure_call(index, stmt, name) for stmt, name in _figure_names(tree, rule.figure)]
    by_start = sorted(savefig_calls, key=lambda call: call.span.start)
    # The protected final save is the last module-level statement that writes the PNG: altair's files end on
    # the HTML save and pad the PNG inside an `if` (`_canvas.save(...)`), after the save that is protected.
    writers = [call for call in by_start if call.standard_target] or by_start
    statements = [call for call in writers if call.statement is not None]
    final = statements[-1] if statements else (writers[-1] if writers else None)
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
