"""Find the catalogue conventions in Makie source, as spans the other Julia modules work around.

The Julia counterpart of `profiles/r/regions.py`. A catalogue implementation
(`plots/*/implementations/julia/makie.jl`, 325 files on 2026-10-29) follows conventions
the adapter must keep and the normaliser rewrites:

* the theme block: exactly `THEME = get(ENV, "ANYPLOT_THEME", "light")`, as a `const`
  (281 files) or a plain assignment (44), then top-level tokens that pick a fixed value per
  theme, `const PAGE_BG = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"`
  (1,192 of that shape). A token's value tests the theme and is built only from literals
  (strings, numbers, symbols, `colorant"..."`, tuples of them), `THEME` and earlier
  tokens, so `const ALPHA = THEME == "light" ? 0.4 : 0.6` is a token too; a branch that
  calls a function (`RGBAf(...)`, 12 files) is plot code the adapter may rewrite, as in
  Python and R. The theme statement pins its default: `get` takes exactly `ENV` and the
  two strings above;
* the Imprint palette, `const IMPRINT_PALETTE = [colorant"#009E73", ...]` (or `IMPRINT`),
  as `colorant` strings or plain hex strings;
* one protected save: the top-level `save("plot-$(THEME).png", fig; px_per_unit = 2)`,
  the last statement of the catalogue files (318 at the top level, 11 of them spaced
  `px_per_unit=2`; 4 more through `joinpath(@__DIR__, ...)`, which the normaliser
  rewrites, so 322 after it; and 3 inside a `with_theme(...) do` block, which stay
  `blocked`). Every call of `save` is a save call;
  the protected one is the last top-level statement among those that write the standard
  target;
* the markers of the adaptable-code convention (`prompts/adaptable-code.md`): `# Data`
  and `# Plot` comment lines at column 0, matched loosely as in R (`# --- Data ---`), in
  113 and 99 of the 325 files on 2026-10-29: `DATA_MARKER` and `PLOT_MARKER`;
* column constants: `const MONTH = "Month"  # role: x` (or plain), a top-level
  assignment of a string or a vector of strings with a `# role:` comment on its lines
  (`core.adaptability.ROLE_COMMENT`);
* in an adapted working form, the placeholder statement `df = load_user_data()`, at the
  top level only, because the loader that replaces it imports packages.

Lines are 1-based and inclusive, offsets 0-based character offsets with an exclusive
end, as in `code/regions.py`; `Span` is `treesitter.Span`. A region of kind `theme`,
`theme_token`, `placeholder` or `savefig` uses the kind names of the Python profile, so
the edit applier's failure kinds and the attribution log stay the same for Julia.

This module imports only the standard library, tree-sitter, `core.*` and
`code/treesitter.py` (2026-10-29): the Julia detection is meant to move to `core/`
later, so the regen gate's adapt route can run the same checks as the agent.
"""

import re
from dataclasses import dataclass
from typing import Literal

from tree_sitter import Node

from core.adaptability import ROLE_COMMENT

from ...treesitter import (
    JL_LITERALS,
    JlArgument,
    Source,
    Span,
    column,
    first_line,
    jl_arguments,
    jl_assignment,
    jl_callee,
    jl_macro_string,
    jl_named,
    jl_number,
    jl_string,
    jl_unwrap,
    last_line,
    statements,
)


PLACEHOLDER = "df = load_user_data()"
PLACEHOLDER_FUNC = "load_user_data"
THEME_NAME = "THEME"
THEME_ENV = "ANYPLOT_THEME"
THEME_DEFAULT = "light"
ENV_NAME = "ENV"
THEME_STATEMENT = f'const {THEME_NAME} = get({ENV_NAME}, "{THEME_ENV}", "{THEME_DEFAULT}")'
SAVE_NAME = "save"
SAVE_NAMES = frozenset({SAVE_NAME, "Makie.save", "CairoMakie.save"})
"""The callees that save a figure: `save` and its qualified forms."""
STANDARD_TARGET = '"plot-$(THEME).png"'
SAVE_KEYWORDS = ("px_per_unit",)
"""The keywords the protected save may pass: the catalogue passes `px_per_unit` and nothing else (325 files)."""
COLOR_MACRO = "colorant"
IMPRINT_NAMES = frozenset({"IMPRINT", "IMPRINT_PALETTE"})
HEX_COLOR = re.compile(r"#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?")  # used with fullmatch
DATA_MARKER = re.compile(r"^#[ #=-]*Data\b")
PLOT_MARKER = re.compile(r"^#[ #=-]*Plot\b")
"""The markers at column 0, loosely: `# Data`, `## Data`, `# --- Data: ...`, `# ==== Plot`."""
BINDING_WRAPPERS = frozenset({"const_statement", "global_statement"})
"""The statements a top-level binding may stand in: `const X = ...` and `global X = ...`."""
CONSTANT_NAMES = frozenset({"nothing", "missing", "true", "false", "pi", "π", "Inf", "NaN"})
"""Names a theme token's value may read besides THEME and earlier tokens: Julia's constants."""

RegionKind = Literal["theme", "theme_token", "placeholder", "savefig"]
MarkerKind = Literal["data", "plot"]


@dataclass(frozen=True, slots=True)
class Region:
    """A protected statement; `span` covers its whole lines, `statement` its exact characters (`const` included)."""

    kind: RegionKind
    name: str
    span: Span
    statement: Span | None = None


@dataclass(frozen=True, slots=True)
class Palette:
    """A top-level `NAME = [colorant"#...", ...]` of colours; `span` covers its whole lines, `statement` the
    assignment's exact characters."""

    name: str
    entries: tuple[str, ...]
    span: Span
    statement: Span | None = None


@dataclass(frozen=True, slots=True)
class SaveCall:
    """A `save(...)` call.

    `statement` is the whole lines of the call when it is a top-level statement, else
    None. `target` is the source of its first positional argument, `standard_target`
    whether that is exactly `"plot-$(THEME).png"`, `figure` the source of the second,
    `keywords` the keyword names in source order, `positional` the number of positional
    arguments, and `px_per_unit` the keyword's value: its source, its number when it is a
    literal, and its span.
    """

    span: Span
    statement: Span | None
    target: str | None
    standard_target: bool
    figure: str | None
    keywords: tuple[str, ...]
    positional: int
    splat: bool
    px_per_unit: str | None
    px_per_unit_number: float | None
    px_per_unit_span: Span | None


@dataclass(frozen=True, slots=True)
class Marker:
    """A `# Data` or `# Plot` marker comment at column 0."""

    kind: MarkerKind
    line: int
    text: str


@dataclass(frozen=True, slots=True)
class ColumnConstant:
    """`const NAME = "Column"  # role: x`: a top-level string (or vector of strings) with a role comment."""

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
            regions.append(Region("savefig", SAVE_NAME, self.save.statement, self.save.span))
        return tuple(sorted(regions, key=lambda region: region.span.start))

    @property
    def data_marker(self) -> Marker | None:
        return next((marker for marker in self.markers if marker.kind == "data"), None)

    @property
    def plot_marker(self) -> Marker | None:
        return next((marker for marker in self.markers if marker.kind == "plot"), None)


def top_assignment(source: Source, node: Node) -> tuple[Node, str, Node] | None:
    """`(assignment, name, value)` for a top-level `NAME = value`, `const NAME = value` or `global NAME = value`
    that binds one plain name with `=`; None for anything else."""
    inner = node
    if node.type in BINDING_WRAPPERS:
        named = jl_named(node)
        if len(named) != 1:
            return None
        inner = named[0]
    assignment = jl_assignment(source, inner)
    if assignment is None or assignment.operator != "=" or assignment.target.type != "identifier":
        return None
    return inner, assignment.names[0], assignment.value


def is_theme_statement(source: Source, node: Node) -> bool:
    """Exactly `THEME = get(ENV, "ANYPLOT_THEME", "light")`, `const` or not: the only place code may read ENV."""
    found = top_assignment(source, node)
    if found is None or found[1] != THEME_NAME:
        return False
    value = jl_unwrap(found[2])
    if value.type != "call_expression" or jl_callee(source, value) != "get" or len(value.children) != 2:
        return False
    arguments = jl_arguments(source, value)
    if len(arguments) != 3 or any(argument.position is None or argument.splat for argument in arguments):
        return False
    first, second, third = (jl_unwrap(argument.value) for argument in arguments)
    return (
        first.type == "identifier"
        and source.text(first) == ENV_NAME
        and jl_string(source, second) == THEME_ENV
        and jl_string(source, third) == THEME_DEFAULT
    )


def tests_theme(source: Source, value: Node) -> bool:
    """Whether a value tests the theme: `THEME == "light" ? x : y`, or `THEME != "dark"` itself."""
    value = jl_unwrap(value)
    test = jl_named(value)[0] if value.type == "ternary_expression" and jl_named(value) else value
    test = jl_unwrap(test)
    if test.type != "binary_expression":
        return False
    named = jl_named(test)
    if len(named) != 3 or named[1].type != "operator" or source.text(named[1]) not in ("==", "!="):
        return False
    return any(side.type == "identifier" and source.text(side) == THEME_NAME for side in map(jl_unwrap, named[::2]))


def is_literal(source: Source, node: Node) -> bool:
    """A literal a theme token or a palette may hold: a static string, a number (signed too), `true`/`false`, a
    character, a symbol (`:left`) or a `colorant"..."` string."""
    node = jl_unwrap(node)
    if node.type in JL_LITERALS or jl_number(source, node) is not None:
        return True
    if node.type == "string_literal":
        return jl_string(source, node) is not None
    if node.type == "prefixed_string_literal":
        found = jl_macro_string(source, node)
        return found is not None and found[0] == COLOR_MACRO
    if node.type == "quote_expression":
        named = jl_named(node)
        return len(named) == 1 and named[0].type == "identifier"
    return False


def is_theme_constant(source: Source, value: Node, known: set[str]) -> bool:
    """Whether `value` is built only from literals, Julia's constants and the names in `known` (THEME and earlier
    tokens): ternaries, `==`/`!=` comparisons and tuples are walked part by part, without recursion."""
    stack = [value]
    while stack:
        node = jl_unwrap(stack.pop())
        if node.type == "ternary_expression":
            parts = jl_named(node)
            if len(parts) != 3:
                return False
            stack.extend(parts)
        elif node.type == "binary_expression":
            named = jl_named(node)
            if len(named) != 3 or named[1].type != "operator" or source.text(named[1]) not in ("==", "!="):
                return False
            stack.extend(named[::2])
        elif node.type == "tuple_expression":
            items = jl_named(node)
            if not items or any(item.type == "assignment" for item in items):
                return False
            stack.extend(items)
        elif node.type == "identifier":
            if source.text(node) not in known and source.text(node) not in CONSTANT_NAMES:
                return False
        elif not is_literal(source, node):
            return False
    return True


def is_placeholder(source: Source, node: Node) -> bool:
    """The statement `df = load_user_data()` (a plain assignment, no `const`)."""
    assignment = jl_assignment(source, node)
    if assignment is None or assignment.operator != "=" or assignment.target.type != "identifier":
        return False
    value = assignment.value
    return (
        assignment.names == ("df",)
        and value.type == "call_expression"
        and jl_callee(source, value) == PLACEHOLDER_FUNC
        and not jl_arguments(source, value)
        and len(value.children) == 2
    )


def is_standard_target(source: Source, node: Node) -> bool:
    """Exactly `"plot-$(THEME).png"`: the file name with THEME interpolated in parentheses."""
    node = jl_unwrap(node)
    return node.type == "string_literal" and source.text(node) == STANDARD_TARGET


def is_save_call(source: Source, node: Node) -> bool:
    return node.type == "call_expression" and jl_callee(source, node) in SAVE_NAMES


def find_regions(code: str | Source) -> Regions:
    """Locate the conventions in `code`; never raises. Code with syntax problems is read as far as it parses."""
    source = code if isinstance(code, Source) else Source(code, "julia")
    theme: Region | None = None
    tokens: list[Region] = []
    known = {THEME_NAME}  # the names a token's value may read: THEME and the tokens above it
    palettes: list[Palette] = []
    imprint: Palette | None = None
    placeholders: list[Region] = []
    top = statements(source.root)
    for node in top:
        if theme is None and is_theme_statement(source, node):
            theme = Region("theme", THEME_NAME, source.lines_span(node), source.node_span(node))
            continue
        if is_placeholder(source, node):
            placeholders.append(Region("placeholder", PLACEHOLDER, source.lines_span(node), source.node_span(node)))
            continue
        found = top_assignment(source, node)
        if found is None:
            continue
        _, name, value = found
        if name != THEME_NAME and tests_theme(source, value) and is_theme_constant(source, value, known):
            tokens.append(Region("theme_token", name, source.lines_span(node), source.node_span(node)))
            known.add(name)
        palette = _palette(source, node, name, value)
        if palette is not None:
            if imprint is None and palette.name in IMPRINT_NAMES:
                imprint = palette
            if len(palette.entries) >= 2 and all(HEX_COLOR.fullmatch(entry) for entry in palette.entries):
                palettes.append(palette)

    top_ids = {node.id for node in top}
    saves: list[SaveCall] = []
    stack = [source.root]
    while stack:
        node = stack.pop()
        if is_save_call(source, node):
            saves.append(_save_call(source, node, node.id in top_ids))
        stack.extend(reversed(node.children))
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


def colour_value(source: Source, node: Node) -> str | None:
    """The hex text of `colorant"#..."` or `"#..."`, else None."""
    node = jl_unwrap(node)
    if node.type == "prefixed_string_literal":
        found = jl_macro_string(source, node)
        return found[1] if found is not None and found[0] == COLOR_MACRO else None
    return jl_string(source, node)


def strings_of(source: Source, value: Node) -> tuple[str, ...] | None:
    """The strings of a string literal or of a vector of string literals (`["a", "b"]`), else None."""
    value = jl_unwrap(value)
    single = jl_string(source, value)
    if single is not None:
        return (single,)
    if value.type != "vector_expression":
        return None
    texts = [jl_string(source, jl_unwrap(item)) for item in jl_named(value)]
    if not texts or any(text is None for text in texts):
        return None
    return tuple(text for text in texts if text is not None)


def _palette(source: Source, node: Node, name: str, value: Node) -> Palette | None:
    value = jl_unwrap(value)
    if value.type != "vector_expression":
        return None
    entries = [colour_value(source, item) for item in jl_named(value)]
    if not entries or any(entry is None for entry in entries):
        return None
    return Palette(
        name=name,
        entries=tuple(entry for entry in entries if entry is not None),
        span=source.lines_span(node),
        statement=source.node_span(node),
    )


def _save_call(source: Source, call: Node, top_level: bool) -> SaveCall:
    arguments: list[JlArgument] = jl_arguments(source, call)
    positional = [argument for argument in arguments if argument.position is not None]
    keywords = [argument for argument in arguments if argument.position is None]
    target = positional[0].value if positional else None
    figure = positional[1].value if len(positional) > 1 else None
    scale = next((argument for argument in keywords if argument.name == "px_per_unit"), None)
    return SaveCall(
        span=source.node_span(call),
        statement=source.lines_span(call) if top_level else None,
        target=source.text(target) if target is not None else None,
        standard_target=target is not None and is_standard_target(source, target),
        figure=source.text(figure) if figure is not None else None,
        keywords=tuple(argument.name or "..." for argument in keywords),
        positional=len(positional),
        splat=any(argument.splat for argument in arguments),
        px_per_unit=source.text(scale.value) if scale is not None else None,
        px_per_unit_number=jl_number(source, scale.value) if scale is not None else None,
        px_per_unit_span=source.node_span(scale.value) if scale is not None else None,
    )


def _markers(source: Source) -> tuple[Marker, ...]:
    found: list[Marker] = []
    for node in source.root.children:
        if node.type != "line_comment" or column(node) != 0:
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
        if node.type == "line_comment" and column(node) > 0:
            match = ROLE_COMMENT.match(source.text(node))
            if match:  # a further comment after the role (`# role: y  # note`) is not part of it
                roles[first_line(node)] = match.group("rest").split("#", 1)[0].strip()
    found: list[ColumnConstant] = []
    for node in top:
        assignment = top_assignment(source, node)
        if assignment is None:
            continue
        role = next((roles[line] for line in range(first_line(node), last_line(node) + 1) if line in roles), None)
        values = strings_of(source, assignment[2])
        if role is None or values is None:
            continue
        found.append(ColumnConstant(assignment[1], role, values, source.lines_span(node)))
    return tuple(found)
