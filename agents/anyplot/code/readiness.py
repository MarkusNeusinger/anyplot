"""The readiness scan: can a catalogue implementation be adapted, and what must the adapter know?

`scan` runs on the normalised original (`normalise.normalise`) and answers:

* `blocked`: the pair is not eligible. The spec is one of the 13 map specs
  (`map-spec`); the library is not enabled (`library-disabled`) or has no normaliser
  yet (`unsupported-library`); the code does not parse (`syntax`); the SECURITY
  validator reports findings or fails (`security: <rule> ...`, quoting the validator's
  rule ids; it is asked only for a library with a normaliser); there is no module-level `THEME = os.getenv("ANYPLOT_THEME", ...)`
  (`no-theme`); or a save call of the library's rule (`regions.SAVE_RULES`: `savefig`,
  plotnine's `save` and `ggsave`, altair's `save`, pygal's `render_to_png`,
  `render_to_file` and `svg2png`, lets-plot's `ggsave`) writes anywhere but
  `f"plot-{THEME}.png"` (altair, pygal and lets-plot also `f"plot-{THEME}.html"`), a
  save name writes another kind of file than its target (`SaveRule.writes_suffix`:
  pygal's `render_to_file` writes SVG text, so only the HTML; `render_to_png` and
  `svg2png` only the PNG), a save of a library with a save directory
  (`SaveRule.directory`: lets-plot's `path="."`) does not pass it, or the last save of
  the PNG is missing or not a module-level statement (`savefig-target`; a plain string
  such as `"plot.png"` is reported as a single-theme target). Every blocking reason is listed; `hints` stays
  empty. What the normaliser leaves in place reaches the scan this way: a lets-plot
  star import or save alias it could not rewrite, a pygal `open()` write it kept and
  a guard it did not strip are SECURITY findings; a pygal theme `.svg` save it kept is
  a `savefig-target`.
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
* `color-scale`: a color mapping pinned to the catalogue's value range: `vmin`, `vmax`,
  `center` (on seaborn's `heatmap` and `clustermap` only), `vcenter`, `clim`, plotly's
  `zmin`/`zmax`/`zmid`, `range_color` and `color_continuous_midpoint` with a literal, `levels`
  of a contour as a list or range of literals (a count is not flagged), colorbar ticks (`cbar_kws={"ticks": [...]}`,
  `colorbar(ticks=...)`, `cbar.set_ticks(...)`), `set_clim`/`clim` and a norm
  (`Normalize`, `TwoSlopeNorm`, ...) built from literals; the same 0 rule. Live test
  round 8 of 2026-10-16: heatmap-basic in seaborn kept `vmin=0, vmax=100, center=50` and
  ticks 0 to 100 for data of 32 to 93, a washed-out scale with two ticks.
* `colorbar-position`: `cbar_pos` with literal figure coordinates (a seaborn
  `clustermap`): the same round kept the catalogue's top-left colorbar after the adapter
  dropped the dendrogram it sat beside.
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
normaliser could not put the canvas on 3200x1800 or 2400x2400 (`normalise.measure_canvas`:
matplotlib's figure size is not a literal or has another aspect, a pygal chart's size is
computed, set after its constructor or not 16:9 or 1:1, a lets-plot grid has no `ggsize`
of its own or no scale reaches either canvas; plotnine and altair size their canvas on
the save, which the normaliser does not read). The entry says what the render meets: a
PNG of a known size over R2's pixel cap is refused by R2; any other relies on the R3
canvas gate and its padding fallback, except a pygal or lets-plot PNG of unknown size
(`UNKNOWN_SIZE_CANVASES`), which can land over the cap, so no padding is promised. It
does not change the status.

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

from core.adaptability import CRITICAL_VALUES
from core.palette import IMPRINT
from core.spec_roles import MAP_SPECS

from ..schemas import MAX_NOTE_CHARS
from .normalise import MAX_IMAGE_PIXELS, SUPPORTED_LIBRARIES, Canvas, measure_canvas
from .regions import HTML_SUFFIX, IMPRINT_NAMES, PNG_SUFFIX, dotted_name, find_regions, save_rule
from .validate import validate_security


ReadinessStatus = Literal["blocked", "coupled", "clean"]

MIN_PALETTE_ENTRIES = 6
UNKNOWN_SIZE_CANVASES = frozenset({"pygal", "letsplot"})
"""The canvas rewrites (`SaveRule.canvas`) whose unknown size can be anything: pygal's and lets-plot's catalogue
charts render 4800x2700 or more, over R2's pixel cap, unless the normaliser sets their size."""
MAX_SECURITY_REASONS = 5
MAX_SNIPPET_CHARS = 48
MAX_LINE_SNIPPET_CHARS = 2 * MAX_SNIPPET_CHARS
"""A line's flagged parts together (`vmin=0, vmax=100, center=50`), each part at most `MAX_SNIPPET_CHARS`."""

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
COLOR_SCALE_KEYWORDS = frozenset(
    {"vmin", "vmax", "center", "vcenter", "clim", "zmin", "zmax", "zmid", "range_color", "color_continuous_midpoint"}
)
"""Keywords that pin a color mapping's range or midpoint (matplotlib, seaborn, plotly). Not `cmin`/`cmax`:
matplotlib's `hist2d` uses them as count thresholds that hide bins, no color range."""
CENTER_CALLS = frozenset({"heatmap", "clustermap"})
"""The calls whose `center` is a color mapping's midpoint (seaborn); elsewhere `center` places marks (a pie,
`nx.spring_layout`, a patch) and is no color scale (review of #12206)."""
CONTOUR_CALLS = frozenset({"contour", "contourf", "tricontour", "tricontourf"})
"""The calls whose `levels` are values on the color scale; seaborn's `kdeplot` takes `levels` as density
proportions (0 to 1), which fit any data (review of #12206)."""
COLORBAR_KEYWORDS = frozenset({"cbar_kws", "colorbar_kws"})
NORM_CALLS: dict[str, tuple[tuple[int, ...], frozenset[str]]] = {
    "Normalize": ((0, 1), frozenset({"vmin", "vmax"})),
    "LogNorm": ((0, 1), frozenset({"vmin", "vmax"})),
    "TwoSlopeNorm": ((0, 1, 2), frozenset({"vcenter", "vmin", "vmax"})),
    "CenteredNorm": ((0, 1), frozenset({"vcenter", "halfrange"})),
    "BoundaryNorm": ((0,), frozenset({"boundaries"})),
    "PowerNorm": ((1, 2), frozenset({"vmin", "vmax"})),
    "SymLogNorm": ((2, 3), frozenset({"vmin", "vmax"})),
}
"""Each norm's range, center or boundary arguments, by position and keyword; never an encoding parameter such
as `PowerNorm`'s `gamma` or `SymLogNorm`'s `linthresh` (review of #12206)."""
WEBGL_TRACES = frozenset(
    {
        "Scattergl",
        "Scatterpolargl",
        "Splom",
        "Scatter3d",
        "Surface",
        "Mesh3d",
        "Cone",
        "Streamtube",
        "Volume",
        "Isosurface",
        "Parcoords",
        "Scattermap",
        "Choroplethmap",
        "Densitymap",
        "Scattermapbox",
        "Choroplethmapbox",
        "Densitymapbox",
    }
)
"""plotly's trace types that draw with WebGL (plotly 7.1.0; the map traces through MapLibre), which the figure mode's
browser lacks: plotly draws a notice in their place, and the render fails as `draw NoWebGL` (PB-1, 2026-10-31)."""
WEBGL_EXPRESS = frozenset(
    {
        "scatter_3d",
        "line_3d",
        "scatter_matrix",
        "parallel_coordinates",
        "scatter_map",
        "line_map",
        "density_map",
        "choropleth_map",
        "scatter_mapbox",
        "line_mapbox",
        "density_mapbox",
        "choropleth_mapbox",
    }
)
"""The plotly express functions that make one of `WEBGL_TRACES`; `scatter` and `line` switch to `Scattergl` above
1,000 points unless `render_mode="svg"`, which the normaliser adds (`normalise.PX_RENDER_MODE`)."""
BOKEH_RANGE_CALLS = frozenset({"Range1d", "FixedTicker"})
"""bokeh's literal axis ranges and ticks: `Range1d(0, 100)`, `FixedTicker(ticks=[0, 25, 50])`."""
FIGURE_COUPLING: dict[
    str, tuple[frozenset[str], dict[str, frozenset[str]], dict[str, tuple[tuple[int, ...], frozenset[str]]]]
] = {
    # plotly: an axis's `range`, `tickvals` and `dtick` as keywords or dict keys (`xaxis={"range": [0, 11]}`); shapes
    # and annotations placed at data coordinates; `zmin`/`zmax` are COLOR_SCALE_KEYWORDS already.
    "plotly": (
        frozenset({"range", "tickvals", "dtick"}),
        {
            name: frozenset({"x", "y", "x0", "x1", "y0", "y1"})
            for name in ("add_annotation", "add_hline", "add_vline", "add_hrect", "add_vrect", "add_shape")
        },
        {},
    ),
    # bokeh: `x_range=(0, 10.5)`, `ticker=[...]`, `Range1d`/`FixedTicker` (`BOKEH_RANGE_CALLS`) and range stores;
    # `Span`, `Label`, `BoxAnnotation` and `Arrow` at data coordinates; a colour mapper's `low` and `high`.
    "bokeh": (
        frozenset({"x_range", "y_range", "ticker", "ticks"}),
        {
            "Span": frozenset({"location"}),
            "Label": frozenset({"x", "y"}),
            "BoxAnnotation": frozenset({"left", "right", "top", "bottom"}),
            "Arrow": frozenset({"x_start", "y_start", "x_end", "y_end"}),
        },
        {
            "LinearColorMapper": ((), frozenset({"low", "high"})),
            "LogColorMapper": ((), frozenset({"low", "high"})),
            "linear_cmap": ((2, 3), frozenset({"low", "high"})),
            "log_cmap": ((2, 3), frozenset({"low", "high"})),
        },
    ),
}
"""Per figure library: the limit keywords and dict keys, the annotation calls with their coordinate keywords, and the
colour mappers with their range positions and keywords (`_figure_coupling`)."""
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
    (
        "color-scale",
        "Literal color-scale range or colorbar ticks at",
        "derive them from df (min, max; a center only for diverging data) unless the values fix the scale "
        "(a correlation's -1 to 1).",
    ),
    (
        "colorbar-position",
        "Colorbar placed at literal figure coordinates at",
        "they fit the catalogue's layout; when you change the clustering, dendrograms or figure, keep the colorbar "
        "beside the plot: let the library place it (sns.heatmap's own colorbar when the clustering goes).",
    ),
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
    code_library = library if library in SUPPORTED_LIBRARIES else "matplotlib"  # an unsupported one is blocked above
    rule = save_rule(code_library)
    regions = find_regions(normalised_code, tree, library=code_library)
    if regions.theme is None:
        blocked.append('no-theme: no module-level THEME = os.getenv("ANYPLOT_THEME", ...)')
    for call in regions.savefig_calls:
        where = call.span.lines()
        suffix = PNG_SUFFIX if call.standard_target else HTML_SUFFIX if rule.html and call.html_target else None
        if suffix is not None:
            if not rule.writes_suffix(call.name, suffix):
                writes = rule.writes.get(call.name, "")
                blocked.append(
                    f"savefig-target: {call.name} writes only {writes} files, not {snippet_of(call.target or '')} "
                    f"at {where}"
                )
            continue
        if call.literal_target is not None:
            target = snippet_of(repr(call.literal_target))
            blocked.append(f"savefig-target: single-theme {call.name} target {target} at {where}")
        else:
            target = snippet_of(call.target or "no file argument")
            blocked.append(f'savefig-target: {call.name} saves to {target} at {where}, not f"plot-{{THEME}}.png"')
    if rule.directory is not None:
        directory = f'path="{rule.directory}"'
        for call in regions.savefig_calls:
            path = next((keyword for keyword in call.keywords if keyword.name == "path"), None)
            if path is None or not (path.literal and path.value == rule.directory):
                blocked.append(f"savefig-target: {call.name} at {call.span.lines()} does not save with {directory}")
    if not regions.savefig_calls:
        blocked.append(f"savefig-target: no {rule.verb} call")
    elif regions.savefig is None:
        blocked.append(f"savefig-target: the last {rule.verb} is not a module-level statement")
    if library == "plotly":
        blocked.extend(_webgl(tree))
    if blocked:
        return Readiness("blocked", [clip_reason(reason) for reason in blocked])

    findings = _coupling(normalised_code, tree, library)
    reasons: list[str] = []
    hints: list[str] = []
    for category, prefix, advice in _CATEGORIES:
        items = findings.get(category)
        if not items:
            continue
        count = len(items)
        reasons.append(f"{category}: {count} line{'s' if count != 1 else ''}")
        hints.append(format_hint(prefix, items, advice))
    canvas = measure_canvas(normalised_code, library=library)
    if canvas.note is not None:
        reasons.append(_canvas_reason(canvas, library))
    return Readiness("coupled" if hints else "clean", reasons, hints)


def _canvas_reason(canvas: Canvas, library: str) -> str:
    """The `canvas:` reason: the note and what the render meets; R3's padding only for a PNG under R2's pixel cap."""
    if canvas.pixels is not None and canvas.pixels[0] * canvas.pixels[1] > MAX_IMAGE_PIXELS:
        outcome = "R2 refuses a PNG over its pixel cap"
    elif canvas.pixels is None and save_rule(library).canvas in UNKNOWN_SIZE_CANVASES:
        outcome = "the PNG size shows only in the render, and R2 refuses one over its pixel cap"
    else:
        outcome = "the render relies on the R3 canvas gate and padding"
    return clip_reason(f"canvas: {canvas.note}; {outcome}")


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
        clip_reason(f"security: {finding.rule} at line {finding.line}: {finding.message}")
        if finding.line is not None
        else clip_reason(f"security: {finding.rule}: {finding.message}")
        for finding in findings[:MAX_SECURITY_REASONS]
    ]
    if len(findings) > MAX_SECURITY_REASONS:
        reasons.append(f"security: {len(findings) - MAX_SECURITY_REASONS} more findings")
    return reasons


# --- WebGL (plotly) ------------------------------------------------------------------------


def _webgl(tree: ast.Module) -> list[str]:
    """`webgl:` reasons for the plotly traces that draw with WebGL (`WEBGL_TRACES`): a `go.<Trace>(...)` or
    `fig.add_<trace>(...)` call, a plotly express function that makes one (`WEBGL_EXPRESS`), `render_mode="webgl"`, or a
    trace given as a dict whose `type` names one. The figure mode's browser has no WebGL, so plotly draws a notice
    instead and the render fails as `draw NoWebGL` (PB-1); one reason per trace name, at its first line."""
    lowered = {name.lower(): name for name in WEBGL_TRACES}
    found: dict[str, int] = {}
    for node in ast.walk(tree):
        name = None
        if isinstance(node, ast.Call):
            callee = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
            if callee in WEBGL_TRACES or callee in WEBGL_EXPRESS:
                name = callee
            elif callee.startswith("add_") and callee.removeprefix("add_") in lowered:
                name = lowered[callee.removeprefix("add_")]
            for keyword in node.keywords:
                value = keyword.value
                text = value.value if isinstance(value, ast.Constant) and isinstance(value.value, str) else None
                if keyword.arg == "render_mode" and text == "webgl":
                    name = name or 'render_mode="webgl"'
                elif keyword.arg == "type" and text in lowered:
                    name = name or lowered[text]
        elif isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values, strict=True):
                if isinstance(key, ast.Constant) and key.value == "type" and isinstance(value, ast.Constant):
                    if isinstance(value.value, str) and value.value in lowered:
                        name = lowered[value.value]
        if name is not None and name not in found:
            found[name] = getattr(node, "lineno", 0)
    return [
        f"webgl: {name} at line {line} draws with WebGL, which the renderer's browser does not have"
        for name, line in sorted(found.items(), key=lambda item: item[1])
    ]


# --- coupling heuristics -----------------------------------------------------------------


def _coupling(code: str, tree: ast.Module, library: str = "matplotlib") -> dict[str, list[tuple[int, str]]]:
    """Per category, `(line, snippet)` for each flagged line, in line order, one per line.

    A line's snippet names every flagged part of it, joined with `, ` (review of #12206: only the first literal
    reached the hint, so `vmax` and `center` after `vmin` were dropped), and a part inside another flagged part
    of the line counts once (a `Normalize(vmin=0, vmax=1)` call and its keywords).
    """
    aliases = _aliases(tree)
    generators = _generator_names(tree, aliases)
    found: dict[str, dict[int, list[ast.expr | ast.keyword]]] = {category: {} for category, _, _ in _CATEGORIES}
    snippets: dict[str, dict[int, str]] = {category: {} for category, _, _ in _CATEGORIES}

    def flag(category: str, node: ast.expr | ast.keyword) -> None:
        parts = found[category].setdefault(node.lineno, [])
        if any(_inside(node, part) for part in parts):
            return
        parts[:] = [part for part in parts if not _inside(part, node)] + [node]

    for node in ast.walk(tree):
        if library in FIGURE_COUPLING:
            for category, part in _figure_coupling(node, library):
                flag(category, part)
        if isinstance(node, ast.Call):
            callee = dotted_name(node.func)
            method = node.func.attr if isinstance(node.func, ast.Attribute) else callee
            resolved = _resolve(callee, aliases) if callee else ""
            if method in LIMIT_METHODS and _has_literal([*node.args, *(kw.value for kw in node.keywords)]):
                flag("limits", node)
            for keyword in _color_scale_literals(node, method):
                flag("color-scale", keyword)
            for keyword in node.keywords:
                if keyword.arg == "cbar_pos" and _has_literal([keyword.value]):
                    flag("colorbar-position", keyword)
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

    for category, lines in found.items():
        for line, parts in lines.items():
            ordered = sorted(parts, key=lambda part: (part.col_offset, part.end_col_offset or 0))
            texts = [snippet_of(ast.get_source_segment(code, part) or ast.unparse(part)) for part in ordered]
            snippets[category][line] = snippet_of(", ".join(dict.fromkeys(texts)), MAX_LINE_SNIPPET_CHARS)
    regions = find_regions(code, tree)
    for palette in regions.palettes:
        is_imprint = palette.name in IMPRINT_NAMES or palette.entries[0].upper() == _IMPRINT_GREEN
        if is_imprint and len(palette.entries) < MIN_PALETTE_ENTRIES:
            snippet = f"{palette.name} ({len(palette.entries)} entries)"
            snippets["palette"].setdefault(palette.span.first_line, snippet)
    return {category: sorted(lines.items()) for category, lines in snippets.items() if lines}


def _figure_coupling(node: ast.AST, library: str) -> list[tuple[str, ast.expr | ast.keyword]]:
    """plotly's and bokeh's literals that fit only the catalogue's data (module docstring, the plotly and bokeh rows):
    axis ranges, tick values and spacing, annotations at data positions and a colour mapper's range, with the 0 rule."""
    found: list[tuple[str, ast.expr | ast.keyword]] = []
    limits, annotations, scales = FIGURE_COUPLING[library]
    if isinstance(node, ast.Call):
        method = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
        for keyword in node.keywords:
            if keyword.arg in limits and _has_literal([keyword.value]):
                found.append(("limits", keyword))
        if method in BOKEH_RANGE_CALLS and _has_literal([*node.args, *(kw.value for kw in node.keywords)]):
            found.append(("limits", node))
        positions = annotations.get(method)
        if positions is not None:
            coordinates = [kw.value for kw in node.keywords if kw.arg in positions]
            if _has_literal(coordinates):
                found.append(("annotations", node))
        bounds = scales.get(method)
        if bounds is not None:
            values = [node.args[i] for i in bounds[0] if i < len(node.args)]
            values += [kw.value for kw in node.keywords if kw.arg in bounds[1]]
            if _has_literal(values):
                found.append(("color-scale", node))
    elif isinstance(node, ast.Dict):
        for key, value in zip(node.keys, node.values, strict=True):
            if isinstance(key, ast.Constant) and key.value in limits and _has_literal([value]):
                found.append(("limits", value))
    elif library == "bokeh" and isinstance(node, ast.Assign | ast.AugAssign):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            # `p.y_range.end = 105`, `p.x_range = Range1d(0, 10)` (the call above), `p.xaxis.ticker = [0, 5, 10]`
            if not isinstance(target, ast.Attribute):
                continue
            owner = dotted_name(target.value) or ""
            ranged = target.attr in ("start", "end", "bounds") and owner.endswith("_range")
            if (ranged or target.attr == "ticker") and _has_literal([node.value]):
                found.append(("limits", node.value))
    return found


def _inside(inner: ast.expr | ast.keyword, outer: ast.expr | ast.keyword) -> bool:
    """Whether `inner`'s source span lies within `outer`'s (the same node included)."""
    start = (inner.lineno, inner.col_offset)
    end = (inner.end_lineno or inner.lineno, inner.end_col_offset or 0)
    return (outer.lineno, outer.col_offset) <= start and end <= (
        outer.end_lineno or outer.lineno,
        outer.end_col_offset or 0,
    )


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


def _color_scale_literals(node: ast.Call, method: str | None) -> list[ast.expr | ast.keyword]:
    """The parts of `node` that fix a color mapping to the catalogue's value range by literals, with the 0 rule.

    A keyword of `COLOR_SCALE_KEYWORDS` (`vmin=0, vmax=100, center=50` on a heatmap, plotly's
    `zmin`), `levels` given as a list or range (a count such as `levels=10` is no value),
    colorbar `ticks` (`cbar_kws={"ticks": [...]}`, `colorbar(ticks=...)`), and the calls
    `set_clim`, `clim`, a norm of `NORM_CALLS` and `set_ticks` on a colorbar or its axes.
    """
    found: list[ast.expr | ast.keyword] = []
    for keyword in node.keywords:
        value = keyword.value
        if keyword.arg == "center" and method not in CENTER_CALLS:
            continue  # a pie's, a network layout's or a patch's center places marks, it maps no color
        if keyword.arg in COLOR_SCALE_KEYWORDS and _has_literal([value]):
            found.append(keyword)
        elif keyword.arg == "levels" and method in CONTOUR_CALLS and _number(value) is None and _has_literal([value]):
            found.append(keyword)
        elif keyword.arg == "ticks" and method == "colorbar" and _has_literal([value]):
            found.append(keyword)
        elif keyword.arg in COLORBAR_KEYWORDS and _ticks_literal(value):
            found.append(keyword)
    arguments = [*node.args, *(keyword.value for keyword in node.keywords)]
    if method in ("set_clim", "clim"):
        if _has_literal(arguments):
            found.append(node)
    elif method is not None and method in NORM_CALLS:
        positions, names = NORM_CALLS[method]
        bounds = [node.args[index] for index in positions if index < len(node.args)]
        bounds += [keyword.value for keyword in node.keywords if keyword.arg in names]
        if _has_literal(bounds):
            found.append(node)
    elif method == "set_ticks" and isinstance(node.func, ast.Attribute):
        receiver = (dotted_name(node.func.value) or "").casefold()
        if any(part in receiver for part in ("cbar", "colorbar", "cax")) and _has_literal(arguments):
            found.append(node)
    return found


def _ticks_literal(value: ast.expr) -> bool:
    """Whether a colorbar keyword dict (`{"ticks": [0, 50, 100]}` or `dict(ticks=...)`) sets literal ticks."""
    if isinstance(value, ast.Dict):
        return any(
            isinstance(key, ast.Constant) and key.value == "ticks" and _has_literal([item])
            for key, item in zip(value.keys, value.values, strict=True)
        )
    if isinstance(value, ast.Call) and dotted_name(value.func) == "dict":
        return any(keyword.arg == "ticks" and _has_literal([keyword.value]) for keyword in value.keywords)
    return False


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


# --- formatting (shared with the R profile's scan, `profiles/r/readiness.py`) -------------------


def snippet_of(text: str, limit: int = MAX_SNIPPET_CHARS) -> str:
    """`text` on one line, whitespace collapsed, at most `limit` characters."""
    text = _WHITESPACE.sub(" ", text).strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def clip_reason(text: str) -> str:
    """A reason or hint cut to `MAX_NOTE_CHARS`."""
    return text if len(text) <= MAX_NOTE_CHARS else text[: MAX_NOTE_CHARS - 1] + "…"


def format_hint(prefix: str, items: list[tuple[int, str]], advice: str) -> str:
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
    return clip_reason(f"{prefix} {'; '.join(shown)}{more}: {advice}")
