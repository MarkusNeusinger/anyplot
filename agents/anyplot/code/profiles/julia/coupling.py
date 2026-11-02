"""The Julia readiness detection: the structure a Makie file needs, and the literals that couple it to its sample.

The Julia counterpart of `profiles/r/coupling.py`. `readiness.py` decides `blocked` from
the security validator and the reasons here (`structure_reasons`), and `clean` or
`coupled` from `coupling`: each category found is one hint for the adapter. The
heuristics are static and deliberately simple, as in the Python and R profiles:

* `data-block`: the file lacks the adaptable-code layout (`prompts/adaptable-code.md`):
  a `# Data` and a `# Plot` marker and column constants with `# role:` comments. On
  2026-10-29, 218 of the 325 catalogue files carry both markers (loosely matched, as in R)
  and none carries column constants: no catalogue Makie file builds its data as a
  `DataFrame` (they build vectors), so every adaptation introduces `df[!, COL]`. A
  missing marker never blocks (owner decision of 2026-10-29).
* `synthetic-data`: `Random.seed!`, the random draws (`rand`, `randn`, `randexp`,
  `randperm`, `shuffle`, also as `Random.*` and broadcast), a dataset package
  (`using RDatasets`, `RDatasets.dataset(...)`, `PalmerPenguins.load()`; an ADAPTATION
  finding, never a block, as R's gapminder), and a vector literal of more than 20
  numbers. Inside the `# Data` block of a file with column constants they are the block
  the adapter swaps, so they count only outside it, and a seed there counts not at all;
  with a marker but no constants the hint names the block's lines instead of listing them.
* `limits`: `xlims!`, `ylims!`, `zlims!` and `limits!` set by literals, and the `limits`,
  `xticks` and `yticks` keywords of any call set by literals: numbers, ranges and
  vectors of numbers, dates (`Date(2024, 1, 1)`). A literal 0 alone is a baseline and is
  not flagged.
* `color-scale`: `colorrange =` and `levels =` set by literals, with the same 0 rule.
* `annotations`: `text!`, `annotation!`, `hlines!`, `vlines!`, `hspan!`, `vspan!`,
  `ablines!`, `bracket!`, `arrows!`, `arrows2d!` and `band!` placed by literal
  positional coordinates or a literal `position =`, the same 0 rule.
* `statistics`: the critical values (`core.adaptability.CRITICAL_VALUES`) and strings that
  state a statistic (`"r = 0.87"`, `"n = 180"`), the Python profile's pattern; an
  interpolated value (`"r = $(round(r; digits = 2))"`) is computed and is not flagged.
* `palette`: an Imprint palette (`IMPRINT_PALETTE`, `IMPRINT`, or a list starting with the
  brand green) with fewer than 6 entries.
* `deprecated-api`: Makie 0.24 calls that still render with a warning, `arrows!` and
  `arrows` (16 catalogue files; `arrows2d!` replaces them, with `tipwidth`, `tiplength`
  and `shaftwidth` for `arrowsize`, `arrowcolor`, `linecolor` and `linewidth`). The J1
  sweep of 2026-10-29 found them; the deprecated `resolution` keyword is rewritten by the
  normaliser instead.

This module imports only the standard library, tree-sitter, `core.*`, `treesitter.py`
and `regions.py` (2026-10-29): the detection is meant to move to `core/` later, so the
regen gate's adapt route can use the same Julia check as the agent.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass

from tree_sitter import Node

from core.adaptability import CRITICAL_VALUES
from core.palette import IMPRINT

from ...treesitter import (
    JlArgument,
    Source,
    first_line,
    jl_arguments,
    jl_callee,
    jl_named,
    jl_number,
    jl_string,
    jl_unwrap,
    syntax_problems,
    walk,
)
from .regions import IMPRINT_NAMES, SAVE_KEYWORDS, STANDARD_TARGET, THEME_STATEMENT, Regions, find_regions


MIN_PALETTE_ENTRIES = 6
MAX_LITERAL_NUMBERS = 20
"""The ADAPTATION validator's limit for a vector literal of numbers (`code/validate.py`)."""

CATEGORIES: tuple[tuple[str, str, str], ...] = (
    (
        "data-block",
        "The sample data is not in one replaceable block:",
        "write df = load_user_data() where the sample is built, read its columns as df[!, COL] with column "
        "constants, and drop the sample's own variables.",
    ),
    ("synthetic-data", "Synthetic data generation at", "replace it with columns of df = load_user_data()."),
    ("limits", "Literal axis limits or ticks at", "derive them from df or drop them."),
    (
        "color-scale",
        "Literal color range or levels at",
        "derive them from df (extrema, a midpoint only for diverging data) unless the values fix the scale "
        "(a correlation's -1 to 1).",
    ),
    ("annotations", "Annotations at literal data coordinates at", "place them from df values or drop them."),
    ("statistics", "Literal statistics at", "compute them from df or drop them."),
    (
        "palette",
        "Short palette at",
        "if df has more groups, extend it in order with further Imprint positions, written out as literals.",
    ),
    (
        "deprecated-api",
        "Makie calls deprecated in 0.24 at",
        "use arrows2d!(ax, x, y, u, v; shaftwidth, tipwidth, tiplength, color) instead of arrows!.",
    ),
)
"""Category id, hint prefix, hint advice; the order is the order of the hints."""

RNG_CALLS = frozenset({"seed!", "rand", "randn", "randexp", "rand!", "randn!", "randexp!", "randperm", "shuffle"})
SEED = "seed!"
DATASET_PACKAGES = frozenset({"RDatasets", "PalmerPenguins"})
"""Data-only packages of the toolchain project (owner decision of 2026-10-29): loading one is synthetic data, a
coupling hint here and an ADAPTATION finding (`dataset-package`) in the validator, never a SECURITY one."""
LIMIT_CALLS = frozenset({"xlims!", "ylims!", "zlims!", "limits!"})
LIMIT_KEYWORDS = frozenset({"limits", "xticks", "yticks"})
COLOR_KEYWORDS = frozenset({"colorrange", "levels"})
ANNOTATION_CALLS = frozenset(
    {"text!", "annotation!", "hlines!", "vlines!", "hspan!", "vspan!", "ablines!", "bracket!", "arrows!", "arrows2d!"}
)
DEPRECATED_CALLS = frozenset({"arrows!", "arrows"})
DATE_CALLS = frozenset({"Date", "DateTime", "Dates.Date", "Dates.DateTime"})
RANGE_CALLS = frozenset({"range", "LinRange", "collect", "reverse"})
MAX_SNIPPET_CHARS = 48
MAX_LINE_SNIPPET_CHARS = 2 * MAX_SNIPPET_CHARS

# A statistic stated in a string: a symbol, a relation, then a number (the Python profile's pattern,
# `code/readiness.py` and `core.adaptability`).
_STATISTIC = re.compile(r"(?<![\w.])(?:r|R|R²|R\^2|ρ|τ|p|n|μ|σ)\s*(?:=|≈|~|<|>|≤|≥)\s*[-−+]?\.?\d")
_WHITESPACE = re.compile(r"\s+")
_IMPRINT_GREEN = IMPRINT[0].upper()

Findings = dict[str, list[tuple[int, str]]]
"""Per category, `(line, snippet)` for each flagged line, in line order."""


def structure_reasons(code: str | Source, regions: Regions | None = None) -> list[str]:
    """The blocking reasons the regions alone give: `syntax`, `no-theme` and `savefig-target`.

    A save other than the protected one, a protected save that writes anything but the
    standard target or passes anything but the figure and `px_per_unit`, and a file
    without a top-level save are each a `savefig-target`; the SECURITY validator reports
    the same with its rule ids.
    """
    source = code if isinstance(code, Source) else Source(code, "julia")
    problems = syntax_problems(source.tree, limit=1)
    if problems:
        return [f"syntax: {problems[0].message()} does not parse"]
    regions = regions if regions is not None else find_regions(source)
    reasons: list[str] = []
    if regions.theme is None:
        reasons.append(f"no-theme: no top-level {THEME_STATEMENT}")
    save = regions.save
    for call in regions.saves:
        if call is save:
            continue
        where = "is not the final top-level save" if call.statement is not None else "is not a top-level statement"
        reasons.append(f"savefig-target: save at {call.span.lines()} {where}")
    if save is None:
        reasons.append(f"savefig-target: no top-level save({STANDARD_TARGET}, fig; px_per_unit = 2)")
    else:
        where = save.span.lines()
        if not save.standard_target:
            target = _snippet(save.target or "no file argument")
            reasons.append(f"savefig-target: save at {where} writes {target}, not {STANDARD_TARGET}")
        extra = [name for name in save.keywords if name not in SAVE_KEYWORDS]
        if save.positional != 2 or save.splat or extra:
            reasons.append(f"savefig-target: save at {where} passes more than the figure and px_per_unit")
    return reasons


def data_block(regions: Regions) -> tuple[int, int] | None:
    """The lines of the `# Data` block: its marker to the line before the `# Plot` marker that follows it."""
    data, plot = regions.data_marker, regions.plot_marker
    if data is None or plot is None or plot.line <= data.line:
        return None
    return data.line, plot.line - 1


def is_layout_complete(regions: Regions) -> bool:
    """Whether the file carries the adaptable-code layout: both markers in order and column constants."""
    return data_block(regions) is not None and bool(regions.columns)


@dataclass(frozen=True, slots=True)
class Coupling:
    """What couples a file to its sample (`profiles/r/coupling.Coupling`, the same fields)."""

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


def base_name(name: str | None) -> str:
    """The function's own name: `seed!` for `Random.seed!`, `""` for None."""
    return (name or "").rsplit(".", 1)[-1]


def loaded_packages(source: Source, node: Node) -> list[str]:
    """The packages a `using` or `import` statement loads (`using A, B: c`, `import A.B`), by their first name; the
    validator refuses a path of more than one name on its own."""
    if node.type not in ("using_statement", "import_statement"):
        return []
    found: list[str] = []
    for child in jl_named(node):
        head = child
        if head.type in ("selected_import", "import_alias"):
            inner = jl_named(head)
            head = inner[0] if inner else head
        if head.type == "import_path":
            inner = jl_named(head)
            head = inner[0] if inner else head
        if head.type == "identifier":
            found.append(source.text(head))
    return found


def coupling(code: str | Source, regions: Regions | None = None) -> Coupling:
    """The coupling of a file that reads cleanly; see the module docstring."""
    source = code if isinstance(code, Source) else Source(code, "julia")
    regions = regions if regions is not None else find_regions(source)
    found: dict[str, dict[int, list[str]]] = {category: {} for category, _, _ in CATEGORIES}
    block = data_block(regions)
    complete = block is not None and bool(regions.columns)
    block_synthetic = False

    def flag(category: str, node: Node) -> None:
        texts = found[category].setdefault(first_line(node), [])
        text = _snippet(source.text(node))
        if text not in texts:
            texts.append(text)

    for node in walk(source.root):
        line = first_line(node)
        inside = block is not None and block[0] <= line <= block[1]
        synthetic = False
        if node.type in ("call_expression", "broadcast_call_expression"):
            name = jl_callee(source, node)
            base = base_name(name)
            # A seed alone fabricates nothing: with the layout complete it counts only beside a draw outside the block.
            if base in RNG_CALLS and not (complete and base == SEED):
                synthetic = True
            elif (name or "").split(".", 1)[0] in DATASET_PACKAGES:
                synthetic = True
            if base in DEPRECATED_CALLS:
                flag("deprecated-api", node)
            _limits(source, node, base, flag)
        elif node.type in ("using_statement", "import_statement"):
            synthetic = any(package in DATASET_PACKAGES for package in loaded_packages(source, node))
        elif node.type in ("vector_expression", "matrix_expression") and _numbers(source, node) > MAX_LITERAL_NUMBERS:
            synthetic = node.parent is None or node.parent.type not in ("vector_expression", "matrix_row")
        elif node.type in ("integer_literal", "float_literal"):
            value = jl_number(source, node)
            if value is not None and value in CRITICAL_VALUES:
                flag("statistics", node)
        elif node.type == "string_literal":
            text = jl_string(source, node)
            if text is None:  # an interpolated string: only its literal parts state anything
                text = "\x00".join(source.text(child) for child in node.children if child.type == "content")
            if _STATISTIC.search(text):
                flag("statistics", node)
        if synthetic and inside:
            block_synthetic = block_synthetic or not complete  # a complete layout's block is swapped whole
        elif synthetic:
            flag("synthetic-data", node)

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


def _layout(regions: Regions, block: tuple[int, int] | None) -> str | None:
    """What the adaptable-code layout lacks, or None when it is complete."""
    if block is not None and regions.columns:
        return None
    if block is not None:
        return f"the # Data block at lines {block[0]}-{block[1]} has no column constants with a role comment"
    data, plot = regions.data_marker, regions.plot_marker
    if data is not None and plot is not None:
        return f"the # Plot marker at line {plot.line} comes before the # Data marker at line {data.line}"
    if data is not None:
        return f"no # Plot marker after the # Data marker at line {data.line}"
    if plot is not None:
        return f"no # Data marker before the # Plot marker at line {plot.line}"
    return "no # Data and # Plot markers, so the sample is built among the plot code"


def _limits(source: Source, node: Node, base: str, record: Callable[[str, Node], None]) -> None:
    """The `limits`, `color-scale` and `annotations` findings of one call, handed to `record`."""
    arguments: list[JlArgument] = jl_arguments(source, node)
    positional = [argument.value for argument in arguments if argument.position is not None]
    if base in LIMIT_CALLS:
        if _has_literal(source, positional[1:] if len(positional) > 2 else positional):
            record("limits", node)
    elif base in ANNOTATION_CALLS:
        values = positional[1:] if positional and positional[0].type == "identifier" else positional
        values = [value for value in values if jl_unwrap(value).type != "string_literal"]
        values += [argument.value for argument in arguments if argument.name == "position"]
        if _has_literal(source, values):
            record("annotations", node)
    for argument in arguments:
        if argument.name in LIMIT_KEYWORDS and _has_literal(source, [argument.value]):
            record("limits", argument.node)
        elif argument.name in COLOR_KEYWORDS and _has_literal(source, [argument.value]):
            record("color-scale", argument.node)


def _literal_values(source: Source, value: Node) -> list[float | str]:
    """The literal values `value` sets: numbers and `"date"` for a date built from literals; through tuples, vectors,
    ranges (`0:5:20`), `range`, `LinRange`, `collect` and signs. Without recursion."""
    found: list[float | str] = []
    stack = [value]
    while stack:
        node = jl_unwrap(stack.pop())
        number = jl_number(source, node)
        if number is not None:
            found.append(number)
            continue
        if node.type in ("tuple_expression", "vector_expression", "range_expression", "matrix_row"):
            stack.extend(item for item in jl_named(node) if item.type != "assignment")
            continue
        if node.type != "call_expression":
            continue
        name = jl_callee(source, node) or ""
        arguments = [argument.value for argument in jl_arguments(source, node) if argument.position is not None]
        if name in DATE_CALLS and arguments and all(jl_number(source, item) is not None for item in arguments):
            found.append("date")
        elif base_name(name) in RANGE_CALLS:
            stack.extend(arguments)
    return found


def _has_literal(source: Source, values: list[Node]) -> bool:
    """Any data-scale literal among `values`: a non-zero number or a literal date."""
    return any(item != 0 for value in values for item in _literal_values(source, value))


def _numbers(source: Source, node: Node) -> int:
    """The numbers of a vector or matrix literal and of the vectors inside it."""
    count = 0
    stack = [node]
    while stack:
        current = stack.pop()
        for item in jl_named(current):
            item = jl_unwrap(item)
            if jl_number(source, item) is not None:
                count += 1
            elif item.type in ("vector_expression", "matrix_expression", "matrix_row"):
                stack.append(item)
    return count


def _snippet(text: str, limit: int = MAX_SNIPPET_CHARS) -> str:
    """The Python profile's `readiness.snippet_of`, which this module may not import (module docstring)."""
    text = _WHITESPACE.sub(" ", text).strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"
