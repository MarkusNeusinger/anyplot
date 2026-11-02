"""The JavaScript readiness detection: the structure a file needs, and the literals that couple it to its sample.

The JavaScript counterpart of `profiles/julia/coupling.py`. `readiness.py` decides
`blocked` from the security validator and the reasons here (`structure_reasons`), and
`clean` or `coupled` from `coupling`: each category found is one hint for the adapter. The
heuristics are static and deliberately simple, as in the other profiles:

* `data-block`: the file lacks the adaptable-code layout (`prompts/adaptable-code.md`, the
  library prompts' "Data block"): a `// Data` and a `// Plot` marker and column constants
  with `// role:` comments. On 2026-10-30, 1,344 of the 1,617 catalogue files carry the
  `// Data` marker, 134 the `// Plot` marker and 121 column constants (MUI X files
  regenerated for 9.16). A missing marker never blocks (owner decision of 2026-10-29).
* `synthetic-data`: `Math.random()`, D3's random sources (`d3.randomNormal`, ...),
  `crypto.getRandomValues`, the multipliers and increments of the generators the catalogue
  writes by hand (`seed * 1664525 + 1013904223`, mulberry32's `0x6D2B79F5`, ...; 470
  files), and an array literal of more than 20 numbers. Inside the `// Data` block of a
  file with column constants they are the block the adapter swaps, so they count only
  outside it; with a marker but no constants the hint names the block's lines instead.
* `limits`: the axis keys of the chart configurations set by literals (`min`, `max`,
  `suggestedMin`, `suggestedMax`, `softMin`, `softMax`, `floor`, `ceiling`,
  `tickPositions`), D3's `.domain([...])` on a position scale and `.tickValues([...])`.
  A literal 0 alone is a baseline and is not flagged.
* `color-scale`: `min` and `max` under `visualMap`, `colorAxis` or `colorMap`, and
  `.domain([...])` on a D3 colour scale (`scaleSequential`, `scaleDiverging`, ...), the
  same 0 rule.
* `annotations`: ECharts' `markLine`, `markPoint` and `markArea` placed by literal
  `xAxis`, `yAxis` or `coord`, Highcharts' `plotLines` and `plotBands` by literal
  `value`, `from` or `to`, MUI X's `<ChartsReferenceLine x={...} />` with a literal, a D3
  scale applied to a literal (`x(2015)`, `yScale(new Date(2024, 0, 1))`), and the pixel
  converters (`getPixelForValue(50)`, `toPixels`, `convertToPixel`) on one; the same 0
  rule.
* `statistics`: the critical values (`core.adaptability.CRITICAL_VALUES`) and strings,
  templates and JSX text that state a statistic (`"r = 0.87"`), the Python profile's
  pattern; a template's substitution is computed and is not read.
* `palette`: an Imprint palette written out (`IMPRINT_PALETTE`, `IMPRINT`, or a list
  starting with the brand green) with fewer than 6 entries; the catalogue reads
  `t.palette` instead (2026-10-30).
* `deprecated-api`: MUI X 7 imports that the image's MUI X 9 does not export: a module
  of an allowlisted package that is not on the allowlist (`@mui/x-charts/ChartContainer`,
  51 files) and a name of `allowlist.REMOVED_EXPORTS` (`ChartContainer` from the package
  root, 1 file). Owner decision of 2026-10-30 (question 13): such a file is `coupled`
  with this note, never blocked for its version alone; the image's allowlist names the
  modules, so the hint is exact.

This module imports only the standard library, tree-sitter, `core.*`, `treesitter.py`,
`regions.py` and `allowlist.py` (2026-10-30): the detection is meant to move to `core/`
later, so the regen gate's adapt route can use the same JavaScript check as the agent.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass

from tree_sitter import Node

from core.adaptability import CRITICAL_VALUES
from core.palette import IMPRINT

from ...treesitter import (
    Source,
    first_line,
    js_arguments,
    js_callee,
    js_named,
    js_number,
    js_object,
    js_property,
    js_string,
    js_unwrap,
    syntax_problems,
    walk,
)
from .allowlist import MUI_PACKAGE, REMOVED_EXPORTS, mui_version, package_of, specifiers
from .regions import IMPRINT_NAMES, WINDOW, Regions, find_regions, grammar_for


MIN_PALETTE_ENTRIES = 6
MAX_LITERAL_NUMBERS = 20
"""The ADAPTATION validator's limit for an array literal of numbers (`code/validate.py`)."""

CATEGORIES: tuple[tuple[str, str, str], ...] = (
    (
        "data-block",
        "The sample data is not in one replaceable block:",
        "write const data = loadUserData(); where the sample is built, read its fields as d[COL] with column "
        "constants, and drop the sample's own variables.",
    ),
    ("synthetic-data", "Synthetic data generation at", "replace it with the records of const data = loadUserData();."),
    ("limits", "Literal axis limits or ticks at", "derive them from data or drop them."),
    (
        "color-scale",
        "Literal color range at",
        "derive it from data (the extent, a midpoint only for diverging data) unless the values fix the scale "
        "(a correlation's -1 to 1).",
    ),
    ("annotations", "Annotations at literal data coordinates at", "place them from data values or drop them."),
    ("statistics", "Literal statistics at", "compute them from data or drop them."),
    ("palette", "Short palette at", "take the colours from t.palette in order instead of a short list."),
    (
        "deprecated-api",
        f"MUI X 7 imports the image's MUI X {mui_version()} lacks at",
        "use MUI X 9's (ChartContainer is ChartsContainer from @mui/x-charts/ChartsContainer).",
    ),
)
"""Category id, hint prefix, hint advice; the order is the order of the hints."""

RANDOM_CALLS = frozenset({"Math.random", "crypto.getRandomValues", "window.crypto.getRandomValues"})
D3_RANDOM = re.compile(r"^d3\.random[A-Z]\w*$")
PRNG_CONSTANTS = frozenset(
    {1664525.0, 1013904223.0, 1103515245.0, 16807.0, 48271.0, 1831565813.0, 214013.0, 2531011.0, 22695477.0}
)
"""The multipliers and increments of the pseudo-random generators the catalogue writes by hand (Numerical Recipes'
LCG in 470 files, glibc's, MINSTD's, mulberry32's `0x6D2B79F5`, Microsoft's), 2026-10-30: a value no plot reads from
its data."""
LIMIT_KEYS = frozenset(
    {"min", "max", "suggestedMin", "suggestedMax", "softMin", "softMax", "floor", "ceiling", "tickPositions"}
)
COLOR_CONTAINERS = frozenset({"visualMap", "colorAxis", "colorMap"})
COLOR_KEYS = frozenset({"min", "max"})
MARK_CONTAINERS = frozenset({"markLine", "markPoint", "markArea"})
MARK_KEYS = frozenset({"xAxis", "yAxis", "coord"})
BAND_CONTAINERS = frozenset({"plotLines", "plotBands"})
BAND_KEYS = frozenset({"value", "from", "to"})
COLOR_SCALES = re.compile(r"^d3\.scale(?:Sequential|Diverging|Quantize|Quantile|Threshold)\w*$")
DOMAIN_METHODS = frozenset({"domain"})
TICK_METHODS = frozenset({"tickValues"})
PIXEL_METHODS = frozenset({"getPixelForValue", "toPixels", "convertToPixel"})
SCALE_NAME = re.compile(r"^(?:[xy][0-9]?|[xy]Scale\w*|[xy]Axis\w*|scale[XY]\w*)$")
"""The names D3 code gives its position scales (`x`, `y0`, `xScale`, `scaleY`): a call of one maps a data value."""
REFERENCE_ELEMENTS = frozenset({"ChartsReferenceLine"})
REFERENCE_ATTRIBUTES = frozenset({"x", "y"})
DATE_CONSTRUCTORS = frozenset({"Date", "Date.UTC"})
MAX_SNIPPET_CHARS = 48
MAX_LINE_SNIPPET_CHARS = 2 * MAX_SNIPPET_CHARS

# A statistic stated in a string: a symbol, a relation, then a number (the Python profile's pattern,
# `code/readiness.py` and `core.adaptability`).
_STATISTIC = re.compile(r"(?<![\w.])(?:r|R|R²|R\^2|ρ|τ|p|n|μ|σ)\s*(?:=|≈|~|<|>|≤|≥)\s*[-−+]?\.?\d")
_WHITESPACE = re.compile(r"\s+")
_IMPRINT_GREEN = IMPRINT[0].upper()

Findings = dict[str, list[tuple[int, str]]]
"""Per category, `(line, snippet)` for each flagged line, in line order."""


def structure_reasons(code: str | Source, regions: Regions | None = None, *, library: str = "chartjs") -> list[str]:
    """The blocking reasons the regions alone give: `syntax`, `no-theme` and `savefig-target`.

    A file that reads neither `window.ANYPLOT_TOKENS` nor `window.ANYPLOT_THEME` ignores the
    theme (`no-theme`); the orientation directive must be one top-level comment of its own
    (`savefig-target`, the rule id of the output target in every language: here the harness
    saves and the directive sets its canvas). The SECURITY validator reports the same with
    its rule ids.
    """
    source = code if isinstance(code, Source) else Source(code, grammar_for(library))
    problems = syntax_problems(source.tree, limit=1)
    if problems:
        return [f"syntax: {problems[0].message()} does not parse"]
    regions = regions if regions is not None else find_regions(source)
    reasons: list[str] = []
    if not regions.reads_theme:
        reasons.append(f"no-theme: nothing reads {WINDOW}.ANYPLOT_TOKENS or {WINDOW}.ANYPLOT_THEME")
    for directive in regions.directives:
        if not directive.comment:
            reasons.append(
                f"savefig-target: line {directive.line} holds the orientation directive's text outside a comment "
                "of its own, which the harness reads all the same"
            )
    if len(regions.directives) > 1:
        lines = ", ".join(str(directive.line) for directive in regions.directives)
        reasons.append(f"savefig-target: {len(regions.directives)} orientation directives at lines {lines}; keep one")
    return reasons


def data_block(regions: Regions) -> tuple[int, int] | None:
    """The lines of the `// Data` block: its marker to the line before the `// Plot` marker that follows it."""
    data, plot = regions.data_marker, regions.plot_marker
    if data is None or plot is None or plot.line <= data.line:
        return None
    return data.line, plot.line - 1


def is_layout_complete(regions: Regions) -> bool:
    """Whether the file carries the adaptable-code layout: both markers in order and column constants."""
    return data_block(regions) is not None and bool(regions.columns)


@dataclass(frozen=True, slots=True)
class Coupling:
    """What couples a file to its sample (`profiles/julia/coupling.Coupling`, the same fields)."""

    findings: Findings
    block: tuple[int, int] | None
    block_synthetic: bool
    layout: str | None

    @property
    def categories(self) -> list[str]:
        """The categories found, in `CATEGORIES` order: each is one hint."""
        present = set(self.findings)
        if self.layout is not None:
            present.add("data-block")
        if self.block_synthetic:
            present.add("synthetic-data")
        return [category for category, _, _ in CATEGORIES if category in present]


def pair_key(source: Source, pair: Node) -> str | None:
    """The key of an object's `pair` when it is a plain name or a string (`min: 0`, `"min": 0`), else None."""
    key = pair.child_by_field_name("key")
    if key is None:
        return None
    if key.type == "property_identifier":
        return source.text(key)
    return js_string(source, key)


def containers(source: Source, node: Node) -> set[str]:
    """The keys of the object pairs `node` sits in, at any depth (`markLine` for a pair inside `markLine: {...}`)."""
    found: set[str] = set()
    current = node.parent
    while current is not None:
        if current.type == "pair":
            key = pair_key(source, current)
            if key is not None:
                found.add(key)
        current = current.parent
    return found


def coupling(code: str | Source, regions: Regions | None = None, *, library: str = "chartjs") -> Coupling:
    """The coupling of a file that reads cleanly; see the module docstring."""
    source = code if isinstance(code, Source) else Source(code, grammar_for(library))
    regions = regions if regions is not None else find_regions(source)
    found: dict[str, dict[int, list[str]]] = {category: {} for category, _, _ in CATEGORIES}
    block = data_block(regions)
    complete = block is not None and bool(regions.columns)
    block_synthetic = False

    def flag(category: str, node: Node, text: str | None = None) -> None:
        texts = found[category].setdefault(first_line(node), [])
        shown = _snippet(text if text is not None else source.text(node))
        if shown not in texts:
            texts.append(shown)

    for node in walk(source.root):
        line = first_line(node)
        inside = block is not None and block[0] <= line <= block[1]
        synthetic = False
        kind = node.type
        if kind in ("call_expression", "new_expression"):
            name = js_callee(source, node) or ""
            if name in RANDOM_CALLS or D3_RANDOM.match(name):
                synthetic = True
            _call_findings(source, node, flag)
        elif kind == "member_expression" and D3_RANDOM.match(_dotted_text(source, node)):
            synthetic = node.parent is None or node.parent.type != "call_expression"
        elif kind == "number":
            value = js_number(source, node)
            if value is not None and abs(value) in PRNG_CONSTANTS:
                synthetic = True
            elif value is not None and value in CRITICAL_VALUES:
                flag("statistics", node)
        elif kind == "array" and _numbers(source, node) > MAX_LITERAL_NUMBERS:
            synthetic = node.parent is None or node.parent.type != "array"
        elif kind == "pair":
            _pair_findings(source, node, flag)
        elif kind in ("string", "template_string", "jsx_text"):
            text = _literal_text(source, node)
            if _STATISTIC.search(text):
                flag("statistics", node)
        elif kind == "jsx_attribute":
            _reference_line(source, node, flag)
        if synthetic and inside:
            block_synthetic = block_synthetic or not complete  # a complete layout's block is swapped whole
        elif synthetic:
            flag("synthetic-data", node)

    for line, text in removed_imports(regions):
        found["deprecated-api"].setdefault(line, []).append(text)
    findings: Findings = {
        category: sorted((line, _snippet(", ".join(parts), MAX_LINE_SNIPPET_CHARS)) for line, parts in lines.items())
        for category, lines in found.items()
        if lines
    }
    for palette in regions.palettes:
        is_imprint = palette.name in IMPRINT_NAMES or palette.entries[0].upper() == _IMPRINT_GREEN
        if is_imprint and len(palette.entries) < MIN_PALETTE_ENTRIES:
            findings.setdefault("palette", []).append(
                (palette.span.first_line, f"{palette.name} ({len(palette.entries)} entries)")
            )
    return Coupling(findings, block, block_synthetic, _layout(regions, block))


def removed_imports(regions: Regions) -> list[tuple[int, str]]:
    """The MUI X 7 imports the image's MUI X does not export: `(line, what)` per module or name (module docstring,
    `deprecated-api`)."""
    found: list[tuple[int, str]] = []
    for module in regions.imports:
        specifier = module.specifier
        if specifier is None or package_of(specifier) is None:
            continue  # a module outside the allowlisted packages is the validator's `banned-import`
        if specifier not in specifiers():
            found.append((module.span.first_line, f'"{specifier}"'))
        elif package_of(specifier) == MUI_PACKAGE:
            found += [
                (module.span.first_line, f'{name} from "{specifier}"')
                for name in module.names
                if name in REMOVED_EXPORTS
            ]
    return found


def _dotted_text(source: Source, node: Node) -> str:
    """`d3.randomNormal` for a plain member chain over a name, else `""`."""
    parts: list[str] = []
    current = node
    for _ in range(1000):
        if current.type != "member_expression":
            break
        prop = js_property(source, current)
        inner = js_object(current)
        if prop is None or inner is None:
            return ""
        parts.append(prop)
        current = js_unwrap(inner)
    if current.type != "identifier":
        return ""
    return ".".join([source.text(current), *reversed(parts)])


def _scale_constructor(source: Source, node: Node) -> str:
    """The `d3.scale...` call a method chain starts from (`d3.scaleLinear().domain(...)` is `d3.scaleLinear`), or
    `""`."""
    current: Node | None = node
    for _ in range(1000):
        if current is None:
            return ""
        current = js_unwrap(current)
        if current.type == "call_expression":
            name = js_callee(source, current) or ""
            if name.startswith("d3.scale"):
                return name
            function = current.child_by_field_name("function")
            current = js_object(js_unwrap(function)) if function is not None else None
        elif current.type in ("member_expression", "subscript_expression"):
            current = js_object(current)
        else:
            return ""
    return ""


def _call_findings(source: Source, call: Node, record: Callable[..., None]) -> None:
    """The `limits`, `color-scale` and `annotations` findings of one call, handed to `record`."""
    function = call.child_by_field_name("function")
    arguments = js_arguments(call)
    if function is None or call.type != "call_expression":
        return
    function = js_unwrap(function)
    method = js_property(source, function) if function.type in ("member_expression", "subscript_expression") else None
    if method in DOMAIN_METHODS and _has_literal(source, arguments):
        inner = js_object(function)
        scale = _scale_constructor(source, js_unwrap(inner)) if inner is not None else ""
        record("color-scale" if COLOR_SCALES.match(scale) else "limits", call)
    elif method in TICK_METHODS and _has_literal(source, arguments):
        record("limits", call)
    elif method in PIXEL_METHODS and _has_literal(source, arguments[:1]):
        record("annotations", call)
    elif function.type == "identifier" and SCALE_NAME.match(source.text(function)) and len(arguments) == 1:
        if _has_literal(source, arguments):
            record("annotations", call)


def _pair_findings(source: Source, pair: Node, record: Callable[..., None]) -> None:
    key = pair_key(source, pair)
    value = pair.child_by_field_name("value")
    if key is None or value is None or not _has_literal(source, [value]):
        return
    around = containers(source, pair)
    if key in COLOR_KEYS and around & COLOR_CONTAINERS:
        record("color-scale", pair)
    elif key in MARK_KEYS and around & MARK_CONTAINERS:
        record("annotations", pair)
    elif key in BAND_KEYS and around & BAND_CONTAINERS:
        record("annotations", pair)
    elif key in LIMIT_KEYS and not around & (COLOR_CONTAINERS | MARK_CONTAINERS | BAND_CONTAINERS):
        record("limits", pair)


def _reference_line(source: Source, attribute: Node, record: Callable[..., None]) -> None:
    """`<ChartsReferenceLine x={20} />`: a reference line placed by a literal."""
    element = attribute.parent
    name = element.child_by_field_name("name") if element is not None else None
    named = js_named(attribute)
    if name is None or source.text(name) not in REFERENCE_ELEMENTS or len(named) != 2:
        return
    if source.text(named[0]) not in REFERENCE_ATTRIBUTES:
        return
    value = named[1]
    inner = js_named(value) if value.type == "jsx_expression" else [value]
    if _has_literal(source, inner):
        record("annotations", attribute)


def _literal_values(source: Source, value: Node) -> list[float | str]:
    """The literal values `value` sets: numbers, `"date"` for a date built from literals (`new Date(2024, 0, 1)`), and
    numbers through arrays and signs. Without recursion."""
    found: list[float | str] = []
    stack = [value]
    while stack:
        node = js_unwrap(stack.pop())
        number = js_number(source, node)
        if number is not None:
            found.append(number)
            continue
        if node.type == "array":
            stack.extend(js_named(node))
            continue
        if node.type in ("new_expression", "call_expression"):
            name = js_callee(source, node) or ""
            arguments = js_arguments(node)
            if name in DATE_CONSTRUCTORS and arguments:
                if all(js_number(source, item) is not None for item in arguments) or (
                    len(arguments) == 1 and js_string(source, js_unwrap(arguments[0])) is not None
                ):
                    found.append("date")
    return found


def _has_literal(source: Source, values: list[Node]) -> bool:
    """Any data-scale literal among `values`: a non-zero number or a literal date."""
    return any(item != 0 for value in values for item in _literal_values(source, value))


def _numbers(source: Source, node: Node) -> int:
    """The numbers of an array literal and of the arrays inside it."""
    count = 0
    stack = [node]
    while stack:
        current = stack.pop()
        for item in js_named(current):
            item = js_unwrap(item)
            if js_number(source, item) is not None:
                count += 1
            elif item.type == "array":
                stack.append(item)
    return count


def _literal_text(source: Source, node: Node) -> str:
    """A string's value, a template's literal parts, or JSX text: what a statistic is read from."""
    if node.type == "jsx_text":
        return source.text(node)
    value = js_string(source, node)
    if value is not None:
        return value
    return "\x00".join(source.text(child) for child in node.children if child.type == "string_fragment")


def _layout(regions: Regions, block: tuple[int, int] | None) -> str | None:
    """What the adaptable-code layout lacks, or None when it is complete."""
    if block is not None and regions.columns:
        return None
    if block is not None:
        return f"the // Data block at lines {block[0]}-{block[1]} has no column constants with a role comment"
    data, plot = regions.data_marker, regions.plot_marker
    if data is not None and plot is not None:
        return f"the // Plot marker at line {plot.line} comes before the // Data marker at line {data.line}"
    if data is not None:
        return f"no // Plot marker after the // Data marker at line {data.line}"
    if plot is not None:
        return f"no // Data marker before the // Plot marker at line {plot.line}"
    return "no // Data and // Plot markers, so the sample is built among the plot code"


def _snippet(text: str, limit: int = MAX_SNIPPET_CHARS) -> str:
    """The Python profile's `readiness.snippet_of`, which this module may not import (module docstring)."""
    text = _WHITESPACE.sub(" ", text).strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"
