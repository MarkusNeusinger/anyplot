"""The R readiness detection: the structure a ggplot2 file needs, and the literals that couple it to its sample.

`readiness.py` decides `blocked` from the security validator and the reasons here
(`structure_reasons`), and `clean` or `coupled` from `coupling`: each category found is
one hint for the adapter. The heuristics are static and deliberately simple, as in the
Python profile (`code/readiness.py`):

* `data-block`: the file lacks the adaptable-code layout (`prompts/adaptable-code.md`):
  a `# Data` and a `# Plot` marker and column constants with `# role:` comments. 247 of
  the 325 catalogue files carry both markers, 4 also carry column constants. Without
  them the sample is built among the plot code, which the adapter rewrites into
  `df <- load_user_data()` (owner decision of 2026-10-29: a missing marker never blocks).
* `synthetic-data`: `set.seed`, the random draws (`rnorm`, `runif`, ...), `data()`, a
  built-in dataset read by name, and a `c(...)` of more than 20 numbers. Inside the
  `# Data` block of a file with column constants they are the block the adapter swaps,
  so they count only outside it, and a `set.seed` there counts not at all (it fabricates
  nothing by itself; box-basic seeds above its block); with a marker but no constants the
  hint names the block's lines instead of listing them.
* `limits`: `xlim`, `ylim`, `lims`, `expand_limits` and the `xlim =`/`ylim =` of a
  `coord_*`, and `limits =` and `breaks =` of a position, size, alpha or discrete scale,
  set by literals: numbers, dates (`as.Date("...")`), `seq` or `:` of numbers, and the
  category names of a discrete scale. A literal 0 alone is a baseline and is not flagged.
* `color-scale`: `limits =`, `breaks =` and `midpoint =` of a colour or fill scale set by
  literals, with the same 0 rule.
* `annotations`: `annotate()` placed by literal `x`, `y`, `xmin`, `xmax`, `ymin`, `ymax`,
  `xend` or `yend`, `geom_hline(yintercept =)`, `geom_vline(xintercept =)` and
  `geom_abline(intercept =)` at a literal, the same 0 rule.
* `statistics`: the critical values (`core.adaptability.CRITICAL_VALUES`) and strings that
  state a statistic (`"r = 0.87"`, `"n = 180"`), the Python profile's pattern; a
  `sprintf` format such as `"r = %.2f"` is computed and is not flagged.
* `palette`: an Imprint palette (`IMPRINT_PALETTE`, `IMPRINT`, or a list starting with the
  brand green) with fewer than 6 entries.

This module imports only the standard library, tree-sitter, `core.*`, `treesitter.py`
and `regions.py` (2026-10-29): the detection is meant to move to `core/` later, so the
regen gate's adapt route can use the same R check as the agent.
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
    r_arguments,
    r_callee,
    r_identifier,
    r_is_lookup,
    r_number,
    r_operator,
    r_string_value,
    r_unwrap,
    syntax_problems,
    visits,
)
from .regions import IMPRINT_NAMES, SAVE_DEVICE, STANDARD_TARGET, THEME_STATEMENT, Regions, find_regions


MIN_PALETTE_ENTRIES = 6
MAX_LITERAL_NUMBERS = 20
"""The ADAPTATION validator's limit for a `c(...)` of numbers (`code/validate.py`)."""

CATEGORIES: tuple[tuple[str, str, str], ...] = (
    (
        "data-block",
        "The sample data is not in one replaceable block:",
        "write df <- load_user_data() where the sample is built, keep only the column names of df in the plot "
        "code, and drop the sample's own variables.",
    ),
    ("synthetic-data", "Synthetic data generation at", "replace it with columns of df <- load_user_data()."),
    ("limits", "Literal axis limits, breaks or categories at", "derive them from df or drop them."),
    (
        "color-scale",
        "Literal color-scale limits, breaks or midpoint at",
        "derive them from df (range, a midpoint only for diverging data) unless the values fix the scale "
        "(a correlation's -1 to 1).",
    ),
    ("annotations", "Annotations at literal data coordinates at", "place them from df values or drop them."),
    ("statistics", "Literal statistics at", "compute them from df or drop them."),
    (
        "palette",
        "Short palette at",
        "if df has more groups, extend it in order with further Imprint positions, written out as literals.",
    ),
)
"""Category id, hint prefix, hint advice; the order is the order of the hints."""

RNG_CALLS = re.compile(
    r"^(?:set\.seed|r(?:norm|unif|pois|binom|exp|gamma|beta|t|chisq|f|lnorm|weibull|cauchy|geom|hyper|nbinom|logis"
    r"|multinom|signrank|wilcox|mvnorm)|mvrnorm|data)$"
)
DATASETS = frozenset(
    {
        "iris",
        "mtcars",
        "airquality",
        "faithful",
        "diamonds",
        "mpg",
        "economics",
        "txhousing",
        "midwest",
        "msleep",
        "ToothGrowth",
        "ChickWeight",
        "CO2",
        "PlantGrowth",
        "InsectSprays",
        "USArrests",
        "AirPassengers",
        "Titanic",
        "quakes",
        "Nile",
        "LakeHuron",
        "lynx",
        "sunspots",
        "co2",
        "nottem",
        "warpbreaks",
        "esoph",
        "longley",
        "morley",
        "chickwts",
        "stackloss",
        "swiss",
        "volcano",
        "precip",
        "eurodist",
        "penguins",
        "gapminder",
    }
)
"""Datasets read by name (base R, ggplot2, palmerpenguins and gapminder): the validator's list (`validate.DATASETS`)
narrowed to the catalogue's, plus the two dataset packages."""
LIMIT_CALLS = frozenset({"xlim", "ylim", "lims", "expand_limits"})
COORD_LIMITS = frozenset({"xlim", "ylim"})
SCALE_LIMITS = frozenset({"limits", "breaks"})
COLOR_SCALE = re.compile(r"^scale_(?:colou?r|fill)_")
COLOR_SCALE_KEYWORDS = frozenset({"limits", "breaks", "midpoint"})
ANNOTATE_KEYWORDS = frozenset({"x", "y", "xmin", "xmax", "ymin", "ymax", "xend", "yend"})
REFERENCE_LINES = {"geom_hline": "yintercept", "geom_vline": "xintercept", "geom_abline": "intercept"}
DATE_CALLS = frozenset({"as.Date", "as.POSIXct", "as.POSIXlt", "ISOdate", "ISOdatetime", "ymd", "ymd_hms"})
RANGE_CALLS = frozenset({"seq", "seq_len", "seq.int", "c", "rev"})
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
    standard target or through another device, and a file without a top-level save are
    each a `savefig-target`; the SECURITY validator reports the same with its rule ids.
    """
    source = code if isinstance(code, Source) else Source(code, "r")
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
        reasons.append(f"savefig-target: ggsave at {call.span.lines()} is not the final top-level save")
    if save is None:
        reasons.append(f"savefig-target: no top-level ggsave(filename = {STANDARD_TARGET}, ...)")
    else:
        where = save.span.lines()
        if not save.standard_target:
            target = _snippet(save.target or "no file argument")
            reasons.append(f"savefig-target: ggsave at {where} saves to {target}, not {STANDARD_TARGET}")
        if save.device != SAVE_DEVICE:
            reasons.append(f"savefig-target: ggsave at {where} does not render through device = {SAVE_DEVICE}")
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
    """What couples a file to its sample.

    `findings` holds the code of each category but `data-block`, line by line; the
    synthetic data inside a marked `# Data` block is not listed there but named by the
    block's lines (`block`, `block_synthetic`). `layout` says what the adaptable-code
    layout lacks, None when it is complete (both markers in order and column constants).
    """

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


def coupling(code: str | Source, regions: Regions | None = None) -> Coupling:
    """The coupling of a file that reads cleanly; see the module docstring."""
    source = code if isinstance(code, Source) else Source(code, "r")
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

    for visit in visits(source.root):
        node = visit.node
        line = first_line(node)
        inside = block is not None and block[0] <= line <= block[1]
        synthetic = False
        if node.type == "call":
            callee = (r_callee(source, node) or "").rsplit("::", 1)[-1]
            # A seed alone fabricates nothing: with the layout complete it counts only beside a draw outside the block.
            if RNG_CALLS.match(callee) and not (complete and callee == "set.seed"):
                synthetic = True
            elif callee == "c" and _numbers(source, node) > MAX_LITERAL_NUMBERS:
                synthetic = True
            _limits(source, node, callee, flag)
        elif node.type == "identifier" and r_is_lookup(visit) and r_identifier(source, node) in DATASETS:
            synthetic = True
        elif node.type in ("float", "integer"):
            value = r_number(source, node)
            if value is not None and value in CRITICAL_VALUES:
                flag("statistics", node)
        elif node.type == "string":
            text = r_string_value(source, node) or ""
            if _STATISTIC.search(text) and "%" not in text:
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


def _limits(source: Source, node: Node, callee: str, record: Callable[[str, Node], None]) -> None:
    """The `limits`, `color-scale` and `annotations` findings of one call, handed to `record`."""
    arguments = r_arguments(source, node)
    if callee in LIMIT_CALLS:
        values = [argument.value for argument in arguments if argument.value is not None]
        if _has_literal(source, values, strings=False):
            record("limits", node)
        return
    if callee.startswith("coord_"):
        for argument in arguments:
            if argument.name in COORD_LIMITS and argument.value is not None:
                if _has_literal(source, [argument.value], strings=False):
                    record("limits", argument.node or node)
        return
    if callee.startswith("scale_"):
        color = COLOR_SCALE.match(callee) is not None
        keywords = COLOR_SCALE_KEYWORDS if color else SCALE_LIMITS
        for argument in arguments:
            if argument.name not in keywords or argument.value is None:
                continue
            strings = not color and ("discrete" in callee or "manual" in callee)
            if _has_literal(source, [argument.value], strings=strings):
                record("color-scale" if color else "limits", argument.node or node)
        return
    if callee == "annotate":
        values = [argument.value for argument in arguments if argument.name in ANNOTATE_KEYWORDS and argument.value]
        if _has_literal(source, values, strings=False):
            record("annotations", node)
        return
    keyword = REFERENCE_LINES.get(callee)
    if keyword is not None:
        values = [argument.value for argument in arguments if argument.name == keyword and argument.value is not None]
        if _has_literal(source, values, strings=False):
            record("annotations", node)


def _literal_values(source: Source, value: Node, *, strings: bool) -> list[float | str]:
    """The literal values `value` sets: numbers, `"date"` for a date built from a string, category strings when
    `strings`; through `c()`, `seq()`, `rev()`, `:` and signs. Without recursion."""
    found: list[float | str] = []
    stack = [value]
    while stack:
        node = r_unwrap(stack.pop())
        number = r_number(source, node)
        if number is not None:
            found.append(number)
            continue
        if node.type == "string":
            if strings:
                found.append(r_string_value(source, node) or "")
            continue
        if node.type == "binary_operator" and r_operator(source, node) == ":":
            stack.extend(child for child in (node.child_by_field_name("lhs"), node.child_by_field_name("rhs")) if child)
            continue
        if node.type != "call":
            continue
        callee = (r_callee(source, node) or "").rsplit("::", 1)[-1]
        arguments = [argument.value for argument in r_arguments(source, node) if argument.value is not None]
        if callee in DATE_CALLS and arguments and _strings_only(source, arguments[0]):
            found.append("date")
        elif callee in RANGE_CALLS:
            stack.extend(arguments)
    return found


def _strings_only(source: Source, value: Node) -> bool:
    """A string literal or a `c()` of string literals: the text a literal date is built from."""
    node = r_unwrap(value)
    if node.type == "string":
        return True
    if node.type != "call" or r_callee(source, node) != "c":
        return False
    arguments = r_arguments(source, node)
    return bool(arguments) and all(
        argument.value is not None and r_unwrap(argument.value).type == "string" for argument in arguments
    )


def _has_literal(source: Source, values: list[Node], *, strings: bool) -> bool:
    """Any data-scale literal among `values`: a non-zero number, a literal date, or (with `strings`) a category."""
    return any(item != 0 for value in values for item in _literal_values(source, value, strings=strings))


def _numbers(source: Source, call: Node) -> int:
    """The numbers of a `c(...)` and the `c(...)` inside it."""
    count = 0
    stack = [call]
    while stack:
        node = stack.pop()
        for argument in r_arguments(source, node):
            if argument.value is None:
                continue
            value = r_unwrap(argument.value)
            if r_number(source, value) is not None:
                count += 1
            elif value.type == "call" and r_callee(source, value) == "c":
                stack.append(value)
    return count


def _snippet(text: str, limit: int = MAX_SNIPPET_CHARS) -> str:
    """The Python profile's `readiness.snippet_of`, which this module may not import (module docstring)."""
    text = _WHITESPACE.sub(" ", text).strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"
