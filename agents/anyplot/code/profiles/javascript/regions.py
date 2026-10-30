"""Find the catalogue conventions in JavaScript and TSX source, as spans the other JavaScript modules work around.

The JavaScript counterpart of `profiles/julia/regions.py`. A catalogue implementation
(`plots/*/implementations/javascript/<library>.js` for Chart.js, D3, ECharts and
Highcharts, `muix.tsx` for MUI X; 1,617 files on 2026-10-30) runs inside the harness's page
(`automation/js-render/render.mjs`), which sets the theme, the tokens and the canvas, loads
the library and screenshots the mount node: the file saves nothing. The conventions the
adapter must keep and the normaliser rewrites:

* the token lines: top-level declarations that read the harness's globals
  `window.ANYPLOT_TOKENS`, `window.ANYPLOT_THEME` and `window.ANYPLOT_SIZE`
  (`const t = window.ANYPLOT_TOKENS;` in 1,602 files, `const { width, height } =
  window.ANYPLOT_SIZE;`, `const W = window.ANYPLOT_SIZE.width;`, `const isDark =
  window.ANYPLOT_THEME === "dark";`), and those that pick a value per theme through an
  earlier token (`const MUTED = isDark ? "#A8A79F" : "#6B6A63";`). A token's value is built
  only from literals, the globals' members, earlier tokens, comparisons, arithmetic,
  `||`, `&&`, `??`, `!` and ternaries, and it reads a global itself or tests an earlier
  token; `const p = t.palette` (a member, no test) and anything that calls a function or
  reads another name is plot code the adapter may rewrite, as in Python, R and Julia. A
  token binds one name or destructures plain names (`{ width: W, height: H }`). They are
  the `theme_token` regions; JavaScript has no THEME statement of its own;
* the orientation directive, `//# anyplot-orientation: square` (or `landscape`), which
  the harness reads as the first line anywhere in the file that matches its pattern
  (`orientationFromSource`: `//`, an optional `#`, `anyplot-orientation:`, any case) and
  which picks 2400x2400 over the default 3200x1800; 724 files carry one, after the header
  (2026-10-30). The normaliser puts exactly one, in that form, on the first line; it is
  the `savefig` region, because it fixes what the render writes as the final save does
  in the other languages, and the edits' drift check keeps it although it is a comment;
* the markers of the adaptable-code convention (`prompts/adaptable-code.md`, the library
  prompts' "Data block"): `// Data` and `// Plot` comment lines at column 0 of the top
  level, matched loosely (`// --- Data (in-memory, deterministic) ---`), in 1,344 and 134
  of the files on 2026-10-30;
* column constants: `const SALES = "Sales (k USD)";  // role: value`, a top-level
  declaration of a string (or an array of strings) with a `// role:` comment on its lines
  (124 MUI X files);
* in an adapted working form, the placeholder statement `const data = loadUserData();`,
  at the top level only, which the loader replaces with `const data = window.ANYPLOT_DATA;`;
* the Imprint palette: the harness hands it out as `window.ANYPLOT_TOKENS.palette`, and
  no catalogue file writes it out (2026-10-30); a top-level `IMPRINT_PALETTE` or `IMPRINT`
  array of hex strings is read as in the other profiles, for an adapter that writes one;
* MUI X's imports (`import { BarChart } from "@mui/x-charts/BarChart";`), with the names
  each brings in, for the validator's allowlist and the readiness hint on MUI X 7 imports.

Lines are 1-based and inclusive, offsets 0-based character offsets with an exclusive
end, as in `code/regions.py`; `Span` is `treesitter.Span`. The region kinds are the Python
profile's (`theme_token`, `placeholder`, `savefig`), so the edit applier's failure kinds
and the attribution log stay the same for JavaScript.

This module imports only the standard library, tree-sitter, `core.*` and
`code/treesitter.py` (2026-10-30): the JavaScript detection is meant to move to `core/`
later, so the regen gate's adapt route can run the same checks as the agent.
"""

import re
from dataclasses import dataclass
from typing import Literal

from tree_sitter import Node

from ...treesitter import (
    COMMENTS,
    JS_LINE_SEPARATORS,
    JS_LITERALS,
    Grammar,
    Source,
    Span,
    column,
    first_line,
    js_named,
    js_number,
    js_object,
    js_property,
    js_string,
    js_unwrap,
    last_line,
    statements,
)


LIBRARIES = ("chartjs", "d3", "echarts", "highcharts", "muix")
"""The JavaScript libraries of the catalogue, in the harness's order (`render.mjs`, `BUNDLES`)."""
TSX_LIBRARIES = frozenset({"muix"})
"""The libraries whose code is a TSX module (`plot.tsx`); the others' is a classic script (`plot.js`)."""
LIBRARY_GLOBALS: dict[str, str | None] = {
    "chartjs": "Chart",
    "d3": "d3",
    "echarts": "echarts",
    "highcharts": "Highcharts",
    "muix": None,
}
"""The global each library's bundle defines in the page (`render.mjs`, `BUNDLES`); MUI X is imported instead."""
PLACEHOLDER = "const data = loadUserData();"
PLACEHOLDER_FUNC = "loadUserData"
DATA_NAME = "data"
WINDOW = "window"
TOKEN_GLOBALS = ("ANYPLOT_TOKENS", "ANYPLOT_THEME", "ANYPLOT_SIZE")
"""The harness's render context the snippet reads (`render.mjs`, `buildHtml`)."""
THEME_GLOBALS = frozenset({"ANYPLOT_TOKENS", "ANYPLOT_THEME"})
"""The globals that carry the theme: a file that reads neither ignores it."""
DATA_GLOBAL = "ANYPLOT_DATA"
"""The table the harness injects (`ANYPLOT_DATA_JSON`, JS-2), read only by the loader's statement."""
DIRECTIVE = "//# anyplot-orientation: {orientation}"
DIRECTIVE_NAME = "anyplot-orientation"
_JS_SPACE = r"[\s" + chr(0xFEFF) + "]"
ORIENTATION_PATTERN = re.compile(
    rf"{_JS_SPACE}*(//#?{_JS_SPACE}*anyplot-orientation:{_JS_SPACE}*(square|landscape))(?![A-Za-z0-9_])", re.I
)
"""The harness's pattern (`orientationFromSource`: `^\\s*\\/\\/#?\\s*anyplot-orientation:\\s*(square|landscape)\\b`
with the flags `im`), matched at each line start (`LINE_START`). Python's `\\s` and U+FEFF cover every character
JavaScript's `\\s` does, its case folding is the wider, and `\\b` is JavaScript's ASCII one, so this finds at least
every line the harness reads."""
LINE_START = re.compile("^|(?<=[\n\r" + "".join(JS_LINE_SEPARATORS) + "])")
"""Where JavaScript's multi-line `^` matches: the start and after every line terminator."""
IMPRINT_NAMES = frozenset({"IMPRINT", "IMPRINT_PALETTE"})
HEX_COLOR = re.compile(r"#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?")  # used with fullmatch
DATA_MARKER = re.compile(r"^//[ /=#*-]*Data\b")
PLOT_MARKER = re.compile(r"^//[ /=#*-]*Plot\b")
"""The markers at column 0, loosely: `// Data`, `// --- Data ---`, `//// Plot`, `// ==== Plot: ...`."""
ROLE_COMMENT = re.compile(r"^//\s*role\s*:\s*(?P<rest>.*?)\s*$")
"""`core.adaptability.ROLE_COMMENT` with JavaScript's comment mark."""
DECLARATIONS = frozenset({"lexical_declaration", "variable_declaration"})
TOKEN_OPERATORS = frozenset(
    {"===", "!==", "==", "!=", "<", ">", "<=", ">=", "||", "&&", "??", "+", "-", "*", "/", "%", "**"}
)
COMPARISONS = frozenset({"===", "!==", "==", "!=", "<", ">", "<=", ">="})
TOKEN_UNARY = frozenset({"!", "-", "+"})

RegionKind = Literal["theme_token", "placeholder", "savefig"]
MarkerKind = Literal["data", "plot"]
Orientation = Literal["landscape", "square"]


def grammar_for(library: str) -> Grammar:
    """`tsx` for MUI X, `javascript` for the other libraries; `ValueError` for a library outside `LIBRARIES`."""
    if library not in LIBRARIES:
        raise ValueError(f"no JavaScript library {library!r}; expected one of {', '.join(LIBRARIES)}")
    return "tsx" if library in TSX_LIBRARIES else "javascript"


@dataclass(frozen=True, slots=True)
class Region:
    """A protected statement; `span` covers its whole lines, `statement` its exact characters."""

    kind: RegionKind
    name: str
    span: Span
    statement: Span | None = None


@dataclass(frozen=True, slots=True)
class Directive:
    """A line the harness would read as the orientation directive.

    `span` covers the whole line; `comment` is whether the line is a top-level `//` comment of its own (else the text
    stands in a string, a template or a block comment, where the harness reads it all the same).
    """

    orientation: Orientation
    line: int
    span: Span
    comment: bool
    text: str


@dataclass(frozen=True, slots=True)
class Palette:
    """A top-level `NAME = ["#...", ...]` of colours; `span` covers its whole lines, `statement` its exact
    characters."""

    name: str
    entries: tuple[str, ...]
    span: Span
    statement: Span | None = None


@dataclass(frozen=True, slots=True)
class Marker:
    """A `// Data` or `// Plot` marker comment at column 0."""

    kind: MarkerKind
    line: int
    text: str


@dataclass(frozen=True, slots=True)
class ColumnConstant:
    """`const NAME = "Column";  // role: x`: a top-level string (or array of strings) with a role comment."""

    name: str
    role: str
    values: tuple[str, ...]
    span: Span


@dataclass(frozen=True, slots=True)
class Import:
    """One `import` statement: its module specifier (None when it is no plain string), the names it imports from that
    module (`default` for a default import, `*` for a namespace import), and its lines."""

    specifier: str | None
    names: tuple[str, ...]
    span: Span
    type_only: bool


@dataclass(frozen=True, slots=True)
class Regions:
    """Everything `find_regions` located in one source string."""

    theme_tokens: tuple[Region, ...]
    placeholders: tuple[Region, ...]
    directives: tuple[Directive, ...]
    imprint: Palette | None
    palettes: tuple[Palette, ...]
    markers: tuple[Marker, ...]
    columns: tuple[ColumnConstant, ...]
    imports: tuple[Import, ...]
    reads_theme: bool
    """Whether anything reads `window.ANYPLOT_TOKENS` or `window.ANYPLOT_THEME`."""

    @property
    def directive(self) -> Directive | None:
        """The directive the harness reads: the first line that matches its pattern."""
        return self.directives[0] if self.directives else None

    @property
    def orientation(self) -> Orientation:
        """The canvas the harness picks: the first directive's, else landscape."""
        return self.directive.orientation if self.directive is not None else "landscape"

    @property
    def save(self) -> Region | None:
        """The directive as the protected `savefig` region, when it is a top-level comment of its own."""
        directive = self.directive
        if directive is None or not directive.comment:
            return None
        return Region("savefig", DIRECTIVE_NAME, directive.span, directive.span)

    @property
    def protected(self) -> tuple[Region, ...]:
        """The regions an edit may not touch: the token lines, the placeholder and the orientation directive.

        A palette the code writes out is not protected: the adapter may extend it, and the
        ADAPTATION validator checks that its existing entries keep their order.
        """
        regions = [*self.theme_tokens, *self.placeholders, *([self.save] if self.save is not None else [])]
        return tuple(sorted(regions, key=lambda region: region.span.start))

    @property
    def data_marker(self) -> Marker | None:
        return next((marker for marker in self.markers if marker.kind == "data"), None)

    @property
    def plot_marker(self) -> Marker | None:
        return next((marker for marker in self.markers if marker.kind == "plot"), None)


def declarator(node: Node) -> Node | None:
    """The one `variable_declarator` of a top-level `const`, `let` or `var` (also under `export`), else None."""
    if node.type == "export_statement":
        inner = node.child_by_field_name("declaration")
        if inner is None:
            return None
        node = inner
    if node.type not in DECLARATIONS:
        return None
    declarators = [child for child in js_named(node) if child.type == "variable_declarator"]
    return declarators[0] if len(declarators) == 1 else None


def declared_names(source: Source, name: Node) -> tuple[str, ...] | None:
    """The names a token's declarator binds: one identifier, or an object pattern of plain names (`{ width, height:
    H }`); None for any other pattern (defaults, rest, nesting)."""
    if name.type == "identifier":
        return (source.text(name),)
    if name.type != "object_pattern":
        return None
    names: list[str] = []
    for part in js_named(name):
        if part.type == "shorthand_property_identifier_pattern":
            names.append(source.text(part))
        elif part.type == "pair_pattern":
            key, value = part.child_by_field_name("key"), part.child_by_field_name("value")
            if key is None or value is None or key.type != "property_identifier" or value.type != "identifier":
                return None
            names.append(source.text(value))
        else:
            return None
    return tuple(names) if names else None


def global_read(source: Source, node: Node) -> str | None:
    """`ANYPLOT_TOKENS` for `window.ANYPLOT_TOKENS` (also `window?.ANYPLOT_TOKENS` and `window["ANYPLOT_TOKENS"]`):
    the member of `window` a member access reads, else None."""
    node = js_unwrap(node)
    inner = js_object(node)
    if inner is None:
        return None
    inner = js_unwrap(inner)
    if inner.type != "identifier" or source.text(inner) != WINDOW:
        return None
    return js_property(source, node)


def _chain(source: Source, node: Node) -> tuple[Node, Node | None] | None:
    """`(root, first)` of a chain of plain members and literal indexes (`t.palette[0]`, `window.ANYPLOT_SIZE.width`):
    the identifier it starts from and the access right after it (None for a bare identifier); None when a step is
    computed by code or the chain starts from anything else."""
    first: Node | None = None
    for _ in range(1000):
        node = js_unwrap(node)
        if node.type == "identifier":
            return node, first
        if node.type == "member_expression":
            if js_property(source, node) is None:
                return None
        elif node.type == "subscript_expression":
            index = node.child_by_field_name("index")
            if index is None or (js_property(source, node) is None and js_number(source, index) is None):
                return None
        else:
            return None
        inner = js_object(node)
        if inner is None:
            return None
        first, node = node, inner
    return None


def _token_value(source: Source, value: Node, known: set[str]) -> bool:
    """Whether a value is a token's (module docstring): built only from literals, the globals' members and the
    `known` tokens, and reading a global itself or testing a token. Walked without recursion."""
    reads = tests = False
    stack = [value]
    while stack:
        node = js_unwrap(stack.pop())
        kind = node.type
        if kind in JS_LITERALS or js_number(source, node) is not None:
            continue
        if kind in ("string", "template_string"):
            if js_string(source, node) is None:
                return False
            continue
        if kind in ("member_expression", "subscript_expression", "identifier"):
            chain = _chain(source, node)
            if chain is None:
                return False
            root, first = chain
            name = source.text(root)
            if name == WINDOW:
                if first is None or global_read(source, first) not in TOKEN_GLOBALS:
                    return False
                reads = True
            elif name not in known:
                return False
            continue
        if kind == "binary_expression":
            operator = node.child_by_field_name("operator")
            text = source.text(operator) if operator is not None else ""
            if text not in TOKEN_OPERATORS:
                return False
            if text in COMPARISONS:
                tests = True
            stack.extend(
                child for child in (node.child_by_field_name("left"), node.child_by_field_name("right")) if child
            )
            continue
        if kind == "unary_expression":
            operator = node.child_by_field_name("operator")
            argument = node.child_by_field_name("argument")
            if operator is None or argument is None or source.text(operator) not in TOKEN_UNARY:
                return False
            stack.append(argument)
            continue
        if kind == "ternary_expression":
            condition = node.child_by_field_name("condition")
            branches = [node.child_by_field_name("consequence"), node.child_by_field_name("alternative")]
            if condition is None or None in branches:
                return False
            tests = True
            stack.extend([condition, *(branch for branch in branches if branch is not None)])
            continue
        if kind == "array":
            items = js_named(node)
            if any(item.type == "spread_element" for item in items):
                return False
            stack.extend(items)
            continue
        if kind == "object":
            for part in js_named(node):
                key = part.child_by_field_name("key") if part.type == "pair" else None
                pair_value = part.child_by_field_name("value") if part.type == "pair" else None
                if key is None or pair_value is None or key.type not in ("property_identifier", "string", "number"):
                    return False
                stack.append(pair_value)
            continue
        return False
    return reads or tests


def is_placeholder(source: Source, node: Node) -> bool:
    """The statement `const data = loadUserData();` (a `const` of one name, no arguments)."""
    if node.type != "lexical_declaration":
        return False
    word = node.child_by_field_name("kind")
    found = declarator(node)
    if word is None or source.text(word) != "const" or found is None:
        return False
    name, value = found.child_by_field_name("name"), found.child_by_field_name("value")
    if name is None or value is None or name.type != "identifier" or source.text(name) != DATA_NAME:
        return False
    value = js_unwrap(value)
    function = value.child_by_field_name("function") if value.type == "call_expression" else None
    arguments = value.child_by_field_name("arguments") if value.type == "call_expression" else None
    return (
        function is not None
        and function.type == "identifier"
        and source.text(function) == PLACEHOLDER_FUNC
        and arguments is not None
        and arguments.type == "arguments"
        and not js_named(arguments)
    )


def find_directives(source: Source) -> tuple[Directive, ...]:
    """Every place the harness would read as the orientation directive, in order (module docstring)."""
    code = source.code
    own_lines = {
        source.char(node.start_byte)
        for node in source.root.children
        if node.type == "comment"
        and first_line(node) == last_line(node)
        and source.text(node).startswith("//")
        and not code[source.line_start(first_line(node)) : source.char(node.start_byte)].strip()
    }
    found: list[Directive] = []
    seen: set[int] = set()
    for start in LINE_START.finditer(code):
        hit = ORIENTATION_PATTERN.match(code, start.start())
        if hit is None or hit.start(1) in seen:
            continue  # a match after blank lines is found from each of them
        seen.add(hit.start(1))
        line = source.line_of(hit.start(1))
        orientation: Orientation = "square" if hit.group(2).lower() == "square" else "landscape"
        span = Span(line, line, source.line_start(line), source.line_end(line))
        found.append(Directive(orientation, line, span, hit.start(1) in own_lines, hit.group(1)))
    return tuple(found)


def find_regions(code: str | Source, *, library: str = "chartjs") -> Regions:
    """Locate the conventions in `code`; never raises. Code with syntax problems is read as far as it parses.

    `library` picks the grammar (`grammar_for`) when `code` is a string.
    """
    source = code if isinstance(code, Source) else Source(code, grammar_for(library))
    tokens: list[Region] = []
    known: set[str] = set()
    placeholders: list[Region] = []
    palettes: list[Palette] = []
    imprint: Palette | None = None
    imports: list[Import] = []
    top = statements(source.root)
    for node in top:
        if node.type == "import_statement":
            imports.append(_import(source, node))
            continue
        if is_placeholder(source, node):
            placeholders.append(Region("placeholder", PLACEHOLDER, source.lines_span(node), source.node_span(node)))
            continue
        found = declarator(node)
        if found is None:
            continue
        name, value = found.child_by_field_name("name"), found.child_by_field_name("value")
        if name is None or value is None:
            continue
        names = declared_names(source, name)
        if names is not None and _token_value(source, value, known):
            tokens.append(Region("theme_token", ", ".join(names), source.lines_span(node), source.node_span(node)))
            known.update(names)
            continue
        if name.type != "identifier":
            continue
        palette = _palette(source, node, source.text(name), value)
        if palette is not None:
            if imprint is None and palette.name in IMPRINT_NAMES:
                imprint = palette
            if len(palette.entries) >= 2 and all(HEX_COLOR.fullmatch(entry) for entry in palette.entries):
                palettes.append(palette)
    return Regions(
        theme_tokens=tuple(tokens),
        placeholders=tuple(placeholders),
        directives=find_directives(source),
        imprint=imprint,
        palettes=tuple(palettes),
        markers=_markers(source),
        columns=_columns(source, top),
        imports=tuple(imports),
        reads_theme=_reads_theme(source),
    )


def strings_of(source: Source, value: Node) -> tuple[str, ...] | None:
    """The strings of a string literal or of an array of string literals (`["a", "b"]`), else None."""
    value = js_unwrap(value)
    single = js_string(source, value)
    if single is not None:
        return (single,)
    if value.type != "array":
        return None
    texts = [js_string(source, js_unwrap(item)) for item in js_named(value)]
    if not texts or any(text is None for text in texts):
        return None
    return tuple(text for text in texts if text is not None)


def _palette(source: Source, node: Node, name: str, value: Node) -> Palette | None:
    entries = strings_of(source, value) if js_unwrap(value).type == "array" else None
    if entries is None:
        return None
    return Palette(name=name, entries=entries, span=source.lines_span(node), statement=source.node_span(node))


def _import(source: Source, node: Node) -> Import:
    specifier_node = node.child_by_field_name("source")
    specifier = js_string(source, specifier_node) if specifier_node is not None else None
    names: list[str] = []
    for clause in js_named(node):
        if clause.type != "import_clause":
            continue
        for part in js_named(clause):
            if part.type == "identifier":
                names.append("default")
            elif part.type == "namespace_import":
                names.append("*")
            elif part.type == "named_imports":
                for specifier_part in js_named(part):
                    imported = specifier_part.child_by_field_name("name")
                    if specifier_part.type == "import_specifier" and imported is not None:
                        names.append(js_string(source, imported) or source.text(imported))
    type_only = any(not child.is_named and source.text(child) == "type" for child in node.children)
    return Import(specifier, tuple(names), source.lines_span(node), type_only)


def _reads_theme(source: Source) -> bool:
    stack = [source.root]
    while stack:
        node = stack.pop()
        if node.type in ("member_expression", "subscript_expression") and global_read(source, node) in THEME_GLOBALS:
            return True
        stack.extend(node.children)
    return False


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
    """Top-level string constants with a `// role:` comment on one of their lines (`core.adaptability`'s rule)."""
    roles: dict[int, str] = {}
    stack = [source.root]
    while stack:
        node = stack.pop()
        if node.type in COMMENTS and column(node) > 0:
            match = ROLE_COMMENT.match(source.text(node))
            if match:  # a further comment after the role (`// role: y  // note`) is not part of it
                roles[first_line(node)] = match.group("rest").split("//", 1)[0].strip()
            continue
        stack.extend(node.children)
    found: list[ColumnConstant] = []
    for node in top:
        found_declarator = declarator(node)
        if found_declarator is None:
            continue
        name, value = found_declarator.child_by_field_name("name"), found_declarator.child_by_field_name("value")
        if name is None or value is None or name.type != "identifier":
            continue
        role = next((roles[line] for line in range(first_line(node), last_line(node) + 1) if line in roles), None)
        values = strings_of(source, value)
        if role is None or values is None:
            continue
        found.append(ColumnConstant(source.text(name), role, values, source.lines_span(node)))
    return tuple(found)
