"""The readiness scan: can a catalogue implementation be adapted, and what must the adapter know?

`scan` runs on the normalised original (`normalise.normalise`) and answers:

* `blocked`: the pair is not eligible. The spec is one of the 13 map specs
  (`map-spec`); the library is not enabled (`library-disabled`) or has no normaliser
  yet (`unsupported-library`); the code does not parse (`syntax`); the SECURITY
  validator reports findings or fails (`security: <rule> ...`, quoting the validator's
  rule ids; it is asked only for a library with a normaliser); there is no module-level `THEME = os.getenv("ANYPLOT_THEME", ...)`
  (`no-theme`); or a savefig saves anywhere but `f"plot-{THEME}.png"`, or the last one
  is missing or not a module-level statement (`savefig-target`; a plain string such
  as `"plot.png"` is reported as a single-theme savefig target). Every blocking reason
  is listed; `hints` stays empty.
* `coupled`: eligible, but the code holds literals that only fit the catalogue's own
  data. Each category becomes one hint for the adapter (a `Note` of at most 300
  characters that names the lines) and one `reasons` entry (`limits: 3 lines`).
* `clean`: eligible with nothing to point out.

The coupling heuristics, all static and deliberately simple:

* `limits`: `set_xlim`, `set_ylim`, `set_zlim`, `xlim`, `ylim`, `set_xticks`,
  `set_yticks`, `set_zticks`, `xticks`, `yticks`, `set_xbound`, `set_ybound`,
  `set_rlim`, `set_rmin`, `set_rmax`, `set_rticks` and `axis` with a numeric literal
  argument (also inside a list or tuple, a `range`/`arange`/`linspace` of literals, or
  a date built from literals). A literal 0 alone is a baseline, not a data-scale
  literal, and is not flagged; `max(y) * 1.15` is computed and is not flagged.
* `annotations`: `annotate` (`xy` in data coordinates), `text` (not on a figure, no
  `transform=` other than `transData`), `axhline`, `axvline`, `axhspan`, `axvspan`,
  `hlines` and `vlines` placed by a numeric literal, with the same 0 rule.
* `statistics`: the critical values 1.645, 1.96, 2.326, 2.576 and 3.291, and string
  literals that state a statistic, such as `"r = 0.87"`, `"p < 0.001"`, `"n = 180"`,
  `"R² ≈ 0.64"` (an f-string such as `f"r = {r:.2f}"` is computed and is not flagged).
* `palette`: a module-level Imprint palette list (named `IMPRINT` or
  `IMPRINT_PALETTE`, or starting with the brand green `#009E73`) with fewer than 6
  entries.
* `date-locators`: a `matplotlib.dates` locator other than `AutoDateLocator`, or
  `DateFormatter`.
* `synthetic-data`: `numpy.random.*` (including `default_rng` and `seed`), methods of a
  generator made by `default_rng` or `RandomState`, `scipy.stats` `.rvs(...)` draws and
  `sklearn.datasets` generators. The stdlib `random` module needs no rule: the SECURITY
  profile bans importing it, so such code is already blocked.

`reasons` can also carry one `canvas:` entry for any status that is not blocked: the
normaliser could not put the canvas on 3200x1800 or 2400x2400 (the figure size is
not a literal or has another aspect), so the render relies on the R3 canvas gate and
its padding fallback. It does not change the status.

The 13 map specs are the specs tagged both `plot_type: map` and
`data_type: geospatial` in their `specification.yaml`: bubble-map-geographic,
cartogram-area-distortion, choropleth-basic, contour-map-geographic,
flowmap-origin-destination, heatmap-geographic, map-connection-lines,
map-marker-clustered, map-projections, map-route-path, map-tile-background,
map-tilegrid and scatter-map-geographic. Their implementations across the 15
libraries pull basemaps, tiles or Natural Earth geometry from the network
(cartopy, geopandas, plotly `scattergeo`, OpenStreetMap tiles), which the sandbox
has no egress for. `scatter-pitch-events` (a sports pitch tagged `map`) and
`hexbin-map-geographic` (drawn from inline coordinates) are not on the list.
"""

import ast
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Literal

from core.palette import IMPRINT

from ..schemas import MAX_NOTE_CHARS
from .normalise import SUPPORTED_LIBRARIES, measure_canvas
from .regions import IMPRINT_NAMES, dotted_name, find_regions
from .validate import validate_security


ReadinessStatus = Literal["blocked", "coupled", "clean"]

MAP_SPECS = frozenset(
    {
        "bubble-map-geographic",
        "cartogram-area-distortion",
        "choropleth-basic",
        "contour-map-geographic",
        "flowmap-origin-destination",
        "heatmap-geographic",
        "map-connection-lines",
        "map-marker-clustered",
        "map-projections",
        "map-route-path",
        "map-tile-background",
        "map-tilegrid",
        "scatter-map-geographic",
    }
)
MIN_PALETTE_ENTRIES = 6
CRITICAL_VALUES = frozenset({1.645, 1.96, 2.326, 2.576, 3.291})
MAX_SECURITY_REASONS = 5
MAX_SNIPPET_CHARS = 48

LIMIT_METHODS = frozenset(
    {
        "set_xlim",
        "set_ylim",
        "set_zlim",
        "xlim",
        "ylim",
        "set_xticks",
        "set_yticks",
        "set_zticks",
        "xticks",
        "yticks",
        "set_xbound",
        "set_ybound",
        "set_rlim",
        "set_rmin",
        "set_rmax",
        "set_rticks",
        "axis",
    }
)
# Annotation methods: the positional indexes and keyword names that carry data coordinates.
DATA_COORDINATES: dict[str, tuple[tuple[int, ...], tuple[str, ...]]] = {
    "text": ((0, 1), ("x", "y")),
    "axhline": ((0,), ("y",)),
    "axvline": ((0,), ("x",)),
    "axhspan": ((0, 1), ("ymin", "ymax")),
    "axvspan": ((0, 1), ("xmin", "xmax")),
    "hlines": ((0, 1, 2), ("y", "xmin", "xmax")),
    "vlines": ((0, 1, 2), ("x", "ymin", "ymax")),
}
RANGE_CALLS = frozenset({"range", "arange", "linspace"})
DATE_CALLS = frozenset({"Timestamp", "datetime", "datetime64", "date", "to_datetime"})
GENERATOR_FACTORIES = frozenset({"default_rng", "RandomState", "Generator"})

# A statistic stated in a string: a symbol, a relation, then a number.
_STATISTIC = re.compile(r"(?<![\w.])(?:r|R|R²|R\^2|ρ|τ|p|n|μ|σ)\s*(?:=|≈|~|<|>|≤|≥)\s*[-−+]?\.?\d")
_WHITESPACE = re.compile(r"\s+")
_IMPRINT_GREEN = IMPRINT[0].upper()

# Category id, hint prefix, hint advice; the order is the order of `hints`.
_CATEGORIES: tuple[tuple[str, str, str], ...] = (
    ("limits", "Literal axis limits or ticks at", "derive them from df or drop them."),
    ("annotations", "Annotations at literal data coordinates at", "place them from df values or drop them."),
    ("statistics", "Literal statistics at", "compute them from df or drop them."),
    (
        "palette",
        "Short palette at",
        "if df has more groups, extend it in order with further Imprint positions, written out as literals.",
    ),
    (
        "date-locators",
        "Hard-coded date locators or formatters at",
        "use AutoDateLocator with ConciseDateFormatter or derive the interval from df.",
    ),
    ("synthetic-data", "Synthetic data generation at", "replace it with columns of df = load_user_data()."),
)


@dataclass(frozen=True, slots=True)
class Readiness:
    """The scan result: `reasons` explain the status, `hints` go to the adapter (coupled only)."""

    status: ReadinessStatus
    reasons: list[str] = field(default_factory=list)
    hints: list[str] = field(default_factory=list)


def scan(normalised_code: str, *, spec_id: str, library: str, enabled_libraries: Iterable[str]) -> Readiness:
    """Classify the normalised original of `spec_id` in `library`; never raises."""
    blocked: list[str] = []
    if spec_id in MAP_SPECS:
        blocked.append(f"map-spec: {spec_id} is one of the 13 map specs, which need network access for geodata")
    if library not in set(enabled_libraries):
        blocked.append(f"library-disabled: {library} is not enabled")
    if library not in SUPPORTED_LIBRARIES:
        blocked.append(f"unsupported-library: no normaliser for {library}")
    try:
        tree = ast.parse(normalised_code)
    except SyntaxError as exc:
        return Readiness("blocked", [*blocked, f"syntax: line {exc.lineno} does not parse"])
    if library in SUPPORTED_LIBRARIES:
        blocked.extend(_security(normalised_code, library))
    regions = find_regions(normalised_code, tree)
    if regions.theme is None:
        blocked.append('no-theme: no module-level THEME = os.getenv("ANYPLOT_THEME", ...)')
    for call in regions.savefig_calls:
        if call.standard_target:
            continue
        where = call.span.lines()
        if call.literal_target is not None:
            target = _snippet(repr(call.literal_target))
            blocked.append(f"savefig-target: single-theme savefig target {target} at {where}")
        else:
            target = _snippet(call.target or "no file argument")
            blocked.append(f'savefig-target: saves to {target} at {where}, not f"plot-{{THEME}}.png"')
    if not regions.savefig_calls:
        blocked.append("savefig-target: no savefig call")
    elif regions.savefig is None:
        blocked.append("savefig-target: the last savefig is not a module-level statement")
    if blocked:
        return Readiness("blocked", [_clip(reason) for reason in blocked])

    findings = _coupling(normalised_code, tree)
    reasons: list[str] = []
    hints: list[str] = []
    for category, prefix, advice in _CATEGORIES:
        items = findings.get(category)
        if not items:
            continue
        count = len(items)
        reasons.append(f"{category}: {count} line{'s' if count != 1 else ''}")
        hints.append(_hint(prefix, items, advice))
    canvas = measure_canvas(normalised_code)
    if canvas.note is not None:
        reasons.append(_clip(f"canvas: {canvas.note}; the render relies on the R3 canvas gate and padding"))
    return Readiness("coupled" if hints else "clean", reasons, hints)


def _security(code: str, library: str) -> list[str]:
    """SECURITY validator findings as blocking reasons; a validator that fails blocks too.

    `scan` calls this only for a library with a normaliser, which is a library the
    validator profiles too; for any other library `validate_security` raises
    `ValueError` (a caller bug, not a property of the code), and the scan has already
    blocked it as `unsupported-library`.
    """
    try:
        findings = validate_security(code, library=library)
    except Exception as exc:  # fail closed: a crashing validator never passes code
        return [f"security: the validator failed ({type(exc).__name__})"]
    reasons = [
        _clip(f"security: {finding.rule} at line {finding.line}: {finding.message}")
        if finding.line is not None
        else _clip(f"security: {finding.rule}: {finding.message}")
        for finding in findings[:MAX_SECURITY_REASONS]
    ]
    if len(findings) > MAX_SECURITY_REASONS:
        reasons.append(f"security: {len(findings) - MAX_SECURITY_REASONS} more findings")
    return reasons


# --- coupling heuristics -----------------------------------------------------------------


def _coupling(code: str, tree: ast.Module) -> dict[str, list[tuple[int, str]]]:
    """Per category, `(line, snippet)` for each flagged line, in line order, one per line."""
    aliases = _aliases(tree)
    generators = _generator_names(tree, aliases)
    found: dict[str, dict[int, str]] = {category: {} for category, _, _ in _CATEGORIES}

    def flag(category: str, node: ast.expr) -> None:
        found[category].setdefault(node.lineno, _snippet(ast.get_source_segment(code, node) or ast.unparse(node)))

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            callee = dotted_name(node.func)
            method = node.func.attr if isinstance(node.func, ast.Attribute) else callee
            resolved = _resolve(callee, aliases) if callee else ""
            if method in LIMIT_METHODS and _has_literal([*node.args, *(kw.value for kw in node.keywords)]):
                flag("limits", node)
            if method is not None and _annotation_literal(node, method):
                flag("annotations", node)
            if resolved.startswith("matplotlib.dates."):
                last = resolved.rsplit(".", 1)[-1]
                if (last.endswith("Locator") and last != "AutoDateLocator") or last == "DateFormatter":
                    flag("date-locators", node)
            if _is_synthetic(node, resolved, generators):
                flag("synthetic-data", node)
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, float) and node.value in CRITICAL_VALUES:
                flag("statistics", node)
            elif isinstance(node.value, str) and _STATISTIC.search(node.value):
                flag("statistics", node)

    regions = find_regions(code, tree)
    for palette in regions.palettes:
        is_imprint = palette.name in IMPRINT_NAMES or palette.entries[0].upper() == _IMPRINT_GREEN
        if is_imprint and len(palette.entries) < MIN_PALETTE_ENTRIES:
            snippet = f"{palette.name} ({len(palette.entries)} entries)"
            found["palette"].setdefault(palette.span.first_line, snippet)
    return {category: sorted(lines.items()) for category, lines in found.items() if lines}


def _aliases(tree: ast.Module) -> dict[str, str]:
    """Local name -> imported module or object, from every import in the file."""
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    aliases[alias.asname] = alias.name
                else:
                    top = alias.name.split(".")[0]
                    aliases[top] = top
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            for alias in node.names:
                aliases[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    return aliases


def _resolve(dotted: str, aliases: dict[str, str]) -> str:
    head, _, rest = dotted.partition(".")
    base = aliases.get(head, head)
    return f"{base}.{rest}" if rest else base


def _generator_names(tree: ast.Module, aliases: dict[str, str]) -> set[str]:
    """Names bound to a random generator: `rng = np.random.default_rng(42)`."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            callee = dotted_name(node.value.func)
            if callee and _resolve(callee, aliases).rsplit(".", 1)[-1] in GENERATOR_FACTORIES:
                names.update(target.id for target in node.targets if isinstance(target, ast.Name))
    return names


def _is_synthetic(node: ast.Call, resolved: str, generators: set[str]) -> bool:
    if resolved.startswith(("numpy.random.", "sklearn.datasets.")):
        return True
    if resolved.startswith("scipy.stats.") and resolved.endswith(".rvs"):
        return True
    func = node.func
    return isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id in generators


def _number(node: ast.expr) -> float | None:
    """The value of a numeric literal, a signed one, or arithmetic on literals."""
    if isinstance(node, ast.Constant):
        value = node.value
        return float(value) if isinstance(value, int | float) and not isinstance(value, bool) else None
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub | ast.UAdd):
        operand = _number(node.operand)
        if operand is None:
            return None
        return -operand if isinstance(node.op, ast.USub) else operand
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add | ast.Sub | ast.Mult | ast.Div):
        left, right = _number(node.left), _number(node.right)
        if left is None or right is None:
            return None
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        return left / right if right else None
    return None


def _literal_values(node: ast.expr) -> list[float | str]:
    """The literal values `node` places on an axis; dates built from literals count as `"date"`."""
    number = _number(node)
    if number is not None:
        return [number]
    if isinstance(node, ast.List | ast.Tuple):
        return [value for element in node.elts for value in _literal_values(element)]
    if isinstance(node, ast.Call):
        name = (dotted_name(node.func) or "").rsplit(".", 1)[-1]
        if name in RANGE_CALLS and node.args:
            numbers = [_number(arg) for arg in node.args]
            if all(value is not None for value in numbers):
                return [value for value in numbers if value is not None]
        if name in DATE_CALLS and node.args and all(isinstance(arg, ast.Constant) for arg in node.args):
            return ["date"]
    return []


def _has_literal(nodes: list[ast.expr]) -> bool:
    """Any data-scale literal among `nodes`: a non-zero number or a literal date."""
    return any(value != 0 for node in nodes for value in _literal_values(node))


def _annotation_literal(node: ast.Call, method: str) -> bool:
    keywords = {kw.arg: kw.value for kw in node.keywords if kw.arg}
    if method == "annotate":
        coords = keywords.get("xycoords")
        if coords is not None and not (isinstance(coords, ast.Constant) and coords.value == "data"):
            return False
        xy = node.args[1] if len(node.args) > 1 else keywords.get("xy")
        return xy is not None and _has_literal([xy])
    if method not in DATA_COORDINATES:
        return False
    if method == "text":
        receiver = dotted_name(node.func.value) if isinstance(node.func, ast.Attribute) else None
        if receiver is not None and "fig" in receiver.rsplit(".", 1)[-1]:
            return False  # figure coordinates
        transform = keywords.get("transform")
        if transform is not None and not (dotted_name(transform) or "").endswith("transData"):
            return False
    positions, names = DATA_COORDINATES[method]
    nodes = [node.args[i] for i in positions if i < len(node.args)]
    nodes += [keywords[name] for name in names if name in keywords]
    return _has_literal(nodes)


# --- formatting ----------------------------------------------------------------------------


def _snippet(text: str) -> str:
    text = _WHITESPACE.sub(" ", text).strip()
    return text if len(text) <= MAX_SNIPPET_CHARS else text[: MAX_SNIPPET_CHARS - 1] + "…"


def _clip(text: str) -> str:
    return text if len(text) <= MAX_NOTE_CHARS else text[: MAX_NOTE_CHARS - 1] + "…"


def _hint(prefix: str, items: list[tuple[int, str]], advice: str) -> str:
    """`<prefix> line 12 `x`; line 14 `y` and 3 more: <advice>`, at most `MAX_NOTE_CHARS`."""
    shown: list[str] = []
    for position, (line, snippet) in enumerate(items):
        rest = len(items) - position - 1
        candidate = [*shown, f"line {line} `{snippet}`"]
        more = f" and {rest} more" if rest else ""
        if len(f"{prefix} {'; '.join(candidate)}{more}: {advice}") > MAX_NOTE_CHARS and shown:
            break
        shown = candidate
    rest = len(items) - len(shown)
    more = f" and {rest} more" if rest else ""
    return _clip(f"{prefix} {'; '.join(shown)}{more}: {advice}")
