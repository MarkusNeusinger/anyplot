"""Find the catalogue conventions in ggplot2 source, as spans the other R modules work around.

The R counterpart of `code/regions.py`. A catalogue implementation
(`plots/*/implementations/r/ggplot2.R`, 325 files on 2026-10-29) follows conventions
the adapter must keep and the normaliser rewrites:

* the theme block: exactly `THEME <- Sys.getenv("ANYPLOT_THEME", "light")` (all 325),
  then top-level tokens that pick a fixed value per theme,
  `PAGE_BG <- if (THEME == "light") "#FAF8F1" else "#1A1A17"` (1,313 of that shape). A
  token's value tests the theme and is built only from literals, `THEME` and earlier
  tokens, so `FILL_ALPHA <- if (THEME == "light") 0.40 else 0.50` and
  `LABEL_COLOR <- if (THEME == "light") INK else "#FFFFFF"` are tokens too (11 such);
  a branch that calls a function (`scales::alpha(...)`, 2 files) is plot code the
  adapter may rewrite, as in Python. Unlike Python's, the theme statement pins its
  default: `Sys.getenv` takes exactly the two strings above;
* the Imprint palette, `IMPRINT_PALETTE <- c("#009E73", ...)` (or `IMPRINT`);
* one protected save: the single top-level `ggsave(...)`, the last statement of every
  catalogue file, `filename = sprintf("plot-%s.png", THEME)` and
  `device = ragg::agg_png` with the keywords `SAVE_KEYWORDS` (317 files pass exactly
  filename, plot, device, width, height, units and dpi, 8 also `bg`); logistic-regression
  binds the target to `output_file` first, which the normaliser inlines. Every call of
  `ggsave` is a save call; the protected one is the last top-level statement among those
  that write the standard target;
* the markers of the adaptable-code convention (`prompts/adaptable-code.md`): comment
  lines at column 0, matched loosely because the catalogue decorates them
  (`# Data` in 40 files, `# --- Data: ...` and `# Data — ...` in 247): `DATA_MARKER`
  and `PLOT_MARKER`;
* column constants: `MONTH <- "Month"  # role: x` (4 files), a top-level assignment of
  a string or a `c(...)` of strings with a `# role:` comment on its lines
  (`core.adaptability.ROLE_COMMENT`);
* in an adapted working form, the placeholder statement `df <- load_user_data()`.

Lines are 1-based and inclusive, offsets 0-based character offsets with an exclusive
end, as in `code/regions.py`; `Span` is `treesitter.Span`. A region of kind `theme`,
`theme_token`, `placeholder` or `savefig` uses the kind names of the Python profile, so
the edit applier's failure kinds and the attribution log stay the same for R.

This module imports only the standard library, tree-sitter, `core.*` and
`code/treesitter.py` (2026-10-29): the R detection is meant to move to `core/` later,
so the regen gate's adapt route can run the same checks as the agent.
"""

import re
from dataclasses import dataclass
from typing import Literal

from tree_sitter import Node

from core.adaptability import ROLE_COMMENT

from ...treesitter import (
    R_LITERALS,
    Argument,
    Source,
    Span,
    column,
    first_line,
    last_line,
    r_argument,
    r_arguments,
    r_assignment,
    r_callee,
    r_identifier,
    r_number,
    r_operator,
    r_string_value,
    r_unwrap,
    statements,
    walk,
)


PLACEHOLDER = "df <- load_user_data()"
PLACEHOLDER_FUNC = "load_user_data"
THEME_NAME = "THEME"
THEME_ENV = "ANYPLOT_THEME"
THEME_DEFAULT = "light"
THEME_STATEMENT = f'{THEME_NAME} <- Sys.getenv("{THEME_ENV}", "{THEME_DEFAULT}")'
SAVE_NAME = "ggsave"
SAVE_NAMES = frozenset({SAVE_NAME, f"ggplot2::{SAVE_NAME}"})
"""The callees that save a plot: `ggsave` and its qualified form (`ggplot2:::ggsave` is refused by the validator)."""
SAVE_DEVICE = "ragg::agg_png"
TARGET_FORMAT = "plot-%s.png"
STANDARD_TARGET = f'sprintf("{TARGET_FORMAT}", {THEME_NAME})'
SAVE_KEYWORDS = ("filename", "plot", "device", "width", "height", "units", "dpi", "bg")
"""The keywords the protected save may pass, in the catalogue's order; every one by name, none positional."""
IMPRINT_NAMES = frozenset({"IMPRINT", "IMPRINT_PALETTE"})
HEX_COLOR = re.compile(r"#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?")  # used with fullmatch
DATA_MARKER = re.compile(r"^#[ #=-]*Data\b")
PLOT_MARKER = re.compile(r"^#[ #=-]*Plot\b")
"""The markers at column 0, loosely: `# Data`, `## Data`, `# --- Data: ...`, `# ==== Plot`; never `#' Data`."""
LEFT_ASSIGNMENTS = frozenset({"<-", "="})
"""The operators of a top-level binding the regions read; `<<-` and the right arrows bind too, but no convention
uses them, so a token or constant written that way is plot code (and the validator refuses `<<-`)."""

RegionKind = Literal["theme", "theme_token", "placeholder", "savefig"]
MarkerKind = Literal["data", "plot"]


@dataclass(frozen=True, slots=True)
class Region:
    """A protected statement; `span` covers its whole lines."""

    kind: RegionKind
    name: str
    span: Span


@dataclass(frozen=True, slots=True)
class Palette:
    """A top-level `NAME <- c("#...", ...)` of colour strings; `span` covers its whole lines."""

    name: str
    entries: tuple[str, ...]
    span: Span


@dataclass(frozen=True, slots=True)
class SaveArgument:
    """One argument of a save call: its name (None when positional), its spans, its text and numeric value."""

    name: str | None
    span: Span
    value_span: Span | None
    text: str
    number: float | None


@dataclass(frozen=True, slots=True)
class SaveCall:
    """A `ggsave(...)` call.

    `statement` is the whole lines of the call when it is a top-level statement, else
    None. `target` is the source of the file argument (`filename=`, or the first
    positional), `standard_target` whether it is exactly `sprintf("plot-%s.png", THEME)`,
    `literal_target` its value when it is a plain string such as `"plot.png"`, and
    `device` the source of `device=`.
    """

    span: Span
    statement: Span | None
    arguments: tuple[SaveArgument, ...]
    target: str | None
    standard_target: bool
    literal_target: str | None
    device: str | None

    def argument(self, name: str) -> SaveArgument | None:
        return next((argument for argument in self.arguments if argument.name == name), None)

    @property
    def keywords(self) -> tuple[str, ...]:
        """The argument names in source order, `?` for a positional one."""
        return tuple(argument.name or "?" for argument in self.arguments)


@dataclass(frozen=True, slots=True)
class Marker:
    """A `# Data` or `# Plot` marker comment at column 0."""

    kind: MarkerKind
    line: int
    text: str


@dataclass(frozen=True, slots=True)
class ColumnConstant:
    """`NAME <- "Column"  # role: x`: a top-level string (or `c(...)` of strings) with a role comment."""

    name: str
    role: str
    values: tuple[str, ...]
    span: Span


@dataclass(frozen=True, slots=True)
class Regions:
    """Everything `find_regions` located in one source string."""

    theme: Region | None
    theme_tokens: tuple[Region, ...]
    placeholders: tuple[Region, ...]
    imprint: Palette | None
    palettes: tuple[Palette, ...]
    saves: tuple[SaveCall, ...]
    save: SaveCall | None
    markers: tuple[Marker, ...]
    columns: tuple[ColumnConstant, ...]

    @property
    def protected(self) -> tuple[Region, ...]:
        """The regions an edit may not touch: THEME, the theme tokens, the placeholder, the protected save.

        The Imprint palette is not protected: the adapter may extend it, and the
        ADAPTATION validator checks that its existing entries keep their order.
        """
        regions = [*([self.theme] if self.theme else []), *self.theme_tokens, *self.placeholders]
        if self.save is not None and self.save.statement is not None:
            regions.append(Region("savefig", SAVE_NAME, self.save.statement))
        return tuple(sorted(regions, key=lambda region: region.span.start))

    @property
    def data_marker(self) -> Marker | None:
        return next((marker for marker in self.markers if marker.kind == "data"), None)

    @property
    def plot_marker(self) -> Marker | None:
        return next((marker for marker in self.markers if marker.kind == "plot"), None)


def is_theme_statement(source: Source, node: Node) -> bool:
    """Exactly `THEME <- Sys.getenv("ANYPLOT_THEME", "light")` (or with `=`): the only `Sys.getenv` R code may call."""
    assignment = r_assignment(source, node)
    if assignment is None or assignment.operator not in LEFT_ASSIGNMENTS or assignment.target.type != "identifier":
        return False
    if assignment.name != THEME_NAME:
        return False
    value = r_unwrap(assignment.value)
    if value.type != "call" or r_callee(source, value) != "Sys.getenv":
        return False
    arguments = r_arguments(source, value)
    return (
        len(arguments) == 2
        and all(argument.name is None and argument.value is not None for argument in arguments)
        and [_string(source, argument.value) for argument in arguments] == [THEME_ENV, THEME_DEFAULT]
    )


def tests_theme(source: Source, value: Node) -> bool:
    """Whether a value tests the theme: `if (THEME == "light") x else y`, or `THEME != "dark"` itself."""
    value = r_unwrap(value)
    test = value.child_by_field_name("condition") if value.type == "if_statement" else value
    if test is None:
        return False
    test = r_unwrap(test)
    if r_operator(source, test) not in ("==", "!="):
        return False
    sides = [test.child_by_field_name("lhs"), test.child_by_field_name("rhs")]
    return any(side is not None and r_identifier(source, r_unwrap(side)) == THEME_NAME for side in sides)


def is_theme_constant(source: Source, value: Node, known: set[str]) -> bool:
    """Whether `value` is built only from literals and the names in `known` (THEME and earlier tokens).

    An `if` with both branches and an `==` or `!=` comparison are walked part by part;
    any other node must be a literal: a string, a number (signed too), `TRUE`, `FALSE`,
    `NULL`, `NA`, `Inf` or `NaN`. The walk keeps its own stack, so a deeply nested value
    cannot exhaust Python's.
    """
    stack = [value]
    while stack:
        node = r_unwrap(stack.pop())
        if node.type == "if_statement":
            parts = [node.child_by_field_name(name) for name in ("condition", "consequence", "alternative")]
            if any(part is None for part in parts):
                return False
            stack.extend(part for part in parts if part is not None)
        elif node.type == "binary_operator" and r_operator(source, node) in ("==", "!="):
            sides = [node.child_by_field_name("lhs"), node.child_by_field_name("rhs")]
            if any(side is None for side in sides):
                return False
            stack.extend(side for side in sides if side is not None)
        elif node.type == "identifier":
            if r_identifier(source, node) not in known:
                return False
        elif node.type == "string":
            if r_string_value(source, node) is None:
                return False
        elif node.type not in R_LITERALS and r_number(source, node) is None:
            return False
    return True


def is_placeholder(source: Source, node: Node) -> bool:
    """The statement `df <- load_user_data()` (or with `=`)."""
    assignment = r_assignment(source, node)
    if assignment is None or assignment.operator not in LEFT_ASSIGNMENTS or assignment.target.type != "identifier":
        return False
    value = assignment.value
    return (
        assignment.name == "df"
        and value.type == "call"
        and r_callee(source, value) == PLACEHOLDER_FUNC
        and not r_arguments(source, value)
    )


def is_standard_target(source: Source, node: Node) -> bool:
    """Exactly `sprintf("plot-%s.png", THEME)`: two positional arguments, the format and the bare THEME."""
    node = r_unwrap(node)
    if node.type != "call" or r_callee(source, node) != "sprintf":
        return False
    arguments = r_arguments(source, node)
    if len(arguments) != 2 or any(argument.name is not None or argument.value is None for argument in arguments):
        return False
    first, second = (argument.value for argument in arguments)
    return (
        first is not None
        and second is not None
        and _string(source, first) == TARGET_FORMAT
        and r_identifier(source, r_unwrap(second)) == THEME_NAME
    )


def save_target(arguments: list[Argument]) -> Argument | None:
    """The file argument of a `ggsave` call: `filename=`, else its first positional."""
    return r_argument(arguments, "filename", 0)


def is_save_call(source: Source, node: Node) -> bool:
    return node.type == "call" and r_callee(source, node) in SAVE_NAMES


def find_regions(code: str | Source) -> Regions:
    """Locate the conventions in `code`; never raises. Code with syntax problems is read as far as it parses."""
    source = code if isinstance(code, Source) else Source(code, "r")
    theme: Region | None = None
    tokens: list[Region] = []
    known = {THEME_NAME}  # the names a token's value may read: THEME and the tokens above it
    palettes: list[Palette] = []
    imprint: Palette | None = None
    top = statements(source.root)
    top_ids = {node.id for node in top}
    for node in top:
        if theme is None and is_theme_statement(source, node):
            theme = Region("theme", THEME_NAME, source.lines_span(node))
            continue
        assignment = r_assignment(source, node)
        if assignment is None or assignment.operator not in LEFT_ASSIGNMENTS or assignment.target.type != "identifier":
            continue
        name = assignment.name
        if name is None:
            continue
        if name != THEME_NAME and tests_theme(source, assignment.value):
            if is_theme_constant(source, assignment.value, known):
                tokens.append(Region("theme_token", name, source.lines_span(node)))
                known.add(name)
        palette = _palette(source, node, name, assignment.value)
        if palette is not None:
            if imprint is None and palette.name in IMPRINT_NAMES:
                imprint = palette
            if len(palette.entries) >= 2 and all(HEX_COLOR.fullmatch(entry) for entry in palette.entries):
                palettes.append(palette)

    placeholders: list[Region] = []
    saves: list[SaveCall] = []
    for node in walk(source.root):
        if is_placeholder(source, node):
            placeholders.append(Region("placeholder", PLACEHOLDER, source.lines_span(node)))
        elif is_save_call(source, node):
            saves.append(_save_call(source, node, node.id in top_ids))

    writers = [call for call in saves if call.standard_target] or saves
    statements_ = [call for call in writers if call.statement is not None]
    return Regions(
        theme=theme,
        theme_tokens=tuple(tokens),
        placeholders=tuple(placeholders),
        imprint=imprint,
        palettes=tuple(palettes),
        saves=tuple(saves),
        save=statements_[-1] if statements_ else None,
        markers=_markers(source),
        columns=_columns(source, top),
    )


def _string(source: Source, node: Node | None) -> str | None:
    return r_string_value(source, r_unwrap(node)) if node is not None else None


def _strings(source: Source, value: Node) -> tuple[str, ...] | None:
    """The strings of a string literal or of a `c(...)` of string literals (positional), else None."""
    value = r_unwrap(value)
    single = _string(source, value)
    if single is not None:
        return (single,)
    if value.type != "call" or r_callee(source, value) != "c":
        return None
    arguments = r_arguments(source, value)
    texts = [_string(source, argument.value) if argument.name is None else None for argument in arguments]
    if not texts or any(text is None for text in texts):
        return None
    return tuple(text for text in texts if text is not None)


def _palette(source: Source, node: Node, name: str, value: Node) -> Palette | None:
    value = r_unwrap(value)
    if value.type != "call":
        return None
    entries = _strings(source, value)
    if entries is None:
        return None
    return Palette(name=name, entries=entries, span=source.lines_span(node))


def _save_call(source: Source, call: Node, top_level: bool) -> SaveCall:
    arguments = r_arguments(source, call)
    found: list[SaveArgument] = []
    for argument in arguments:
        if argument.node is None:
            continue
        value = argument.value
        found.append(
            SaveArgument(
                name=argument.name,
                span=source.node_span(argument.node),
                value_span=source.node_span(value) if value is not None else None,
                text=source.text(value) if value is not None else "",
                number=r_number(source, value) if value is not None else None,
            )
        )
    target = save_target(arguments)
    target_value = target.value if target is not None else None
    device = r_argument(arguments, "device")
    return SaveCall(
        span=source.node_span(call),
        statement=source.lines_span(call) if top_level else None,
        arguments=tuple(found),
        target=source.text(target_value) if target_value is not None else None,
        standard_target=target_value is not None and is_standard_target(source, target_value),
        literal_target=_string(source, target_value),
        device=source.text(device.value) if device is not None and device.value is not None else None,
    )


def _markers(source: Source) -> tuple[Marker, ...]:
    found: list[Marker] = []
    for node in source.root.children:
        if node.type != "comment" or column(node) != 0:
            continue
        text = source.text(node)
        kind: MarkerKind | None = "data" if DATA_MARKER.match(text) else "plot" if PLOT_MARKER.match(text) else None
        if kind is not None:
            found.append(Marker(kind, first_line(node), text))
    return tuple(found)


def _columns(source: Source, top: list[Node]) -> tuple[ColumnConstant, ...]:
    """Top-level string constants with a `# role:` comment on one of their lines (`core.adaptability`'s rule)."""
    roles: dict[int, str] = {}
    for node in source.root.children:
        if node.type == "comment" and column(node) > 0:
            match = ROLE_COMMENT.match(source.text(node))
            if match:  # a further comment after the role (`# role: y  # note`) is not part of it
                roles[first_line(node)] = match.group("rest").split("#", 1)[0].strip()
    found: list[ColumnConstant] = []
    for node in top:
        assignment = r_assignment(source, node)
        if assignment is None or assignment.operator not in LEFT_ASSIGNMENTS or assignment.target.type != "identifier":
            continue
        role = next((roles[line] for line in range(first_line(node), last_line(node) + 1) if line in roles), None)
        values = _strings(source, assignment.value)
        if role is None or values is None or assignment.name is None:
            continue
        found.append(ColumnConstant(assignment.name, role, values, source.lines_span(node)))
    return tuple(found)
