#!/usr/bin/env python3
"""Static contract check of one implementation file (record-only).

The generator prompt mandates a few things that show in the source without
running it. The catalogue audit of 2026-11-08 found legacy files that miss
them behind compliant staged renders, so ``impl-review.yml`` checks the file at
the PR head, and on a regeneration its predecessor, with this script (rule
step P2b). Record-only for now: it writes a job-summary line and a notice and
always exits 0; nothing reads the result yet.

Each rule is a text pattern over the code, named by its key in the record. A
rule says what the code contains, not what the render shows:

- ``title``: the code lacks the mandated title tail
  ``{language} · {library} · anyplot.ai``, or never names the spec id outside
  the header (``prompts/plot-generator.md``, "Title format").
- ``theme``: the code never names ``ANYPLOT_THEME``; in JavaScript, neither
  ``ANYPLOT_THEME`` nor ``ANYPLOT_TOKENS``, the two globals of the render
  harness.
- ``save``: the code builds no file name from ``plot-`` and a theme value, or
  it names a bare ``plot.png``, ``plot.html`` or ``plot.svg``. JavaScript is
  exempt, because the harness saves.
- ``legacy-colour``: the code holds a brand hex of an earlier palette: Python
  blue and yellow of the pyplots.ai era, or the variant-D palette
  (``prompts/quality-criteria.md``, VQ-07, lists all but the yellow).
- ``colormap``: a named library colormap sits in a colormap position
  (``prompts/default-style-guide.md``, "Continuous Data": only the two
  Imprint colormaps are allowed).
- ``palette``: the code holds a six-digit hex that is neither an Imprint
  colour, nor an anchor, nor a stop of the continuous ramps, nor a theme
  token of the style guide. The owner's
  rule (2026-11-11): use the Imprint colours unless there is a very good
  reason, so this rule records a deviation; whether the reason is good is
  for a reader to judge, never for this script.

Then one rule per setting a library prompt states as mandatory, a hard rule
or forbidden, where the source shows it (``MANDATES``; each carries the
prompt's own words). A regeneration carries a line that a gate checks into
nearly every file, and a line that is only read into about half of them, so
these rules make the read lines checkable:

- ``bokeh-page-paint``: the screenshot never paints the browser page in the
  page colour, so a light line runs along the top and left edge of the PNG.
- ``bokeh-toolbar``: the figure keeps its toolbar.
- ``pygal-tick-sizes``: the style sets one of ``label_font_size`` and
  ``major_label_font_size``, or the two to different numbers.
- ``pygal-grid-colour``: a chart that draws guide lines leaves one of their
  two colours at pygal's black.
- ``altair-autosize``: a single or layered chart does not fit its size.
  Compound charts cannot fit and are exempt: the concat, facet and repeat
  calls, a row, column or facet channel, and ``|`` or ``&`` next to a name
  bound to a chart. A chart composed out of a list or by a function
  (``functools.reduce(operator.or_, charts)``) is not recognised as one.
- ``plotly-autosize``: the layout turns autosize on.
- ``letsplot-wrap``: a fixed-aspect plot is not wrapped in a grid that
  paints the canvas.
- ``bbox-tight``: matplotlib or seaborn saves with ``bbox_inches="tight"``.
- ``animation``: Chart.js, ECharts, Highcharts or MUI X leave the entrance
  animation on. A switch counts as a literal ``false``, as a name bound to
  ``false``, or as a named object that holds it, once for each place the
  object is used; a value the file does not resolve leaves the file unjudged.

Comments and the generated header never count. The patterns are deliberately
narrow: a rule that flags a compliant file is worse than no rule, so a
colormap name counts only where a colormap goes, never as a data label such
as ``"Oranges"``, and a setting counts as present in any spelling the
catalogue uses for it. The patterns that look for code (a call, an import,
an operator, a switch) read the code with its string literals emptied, so a
title that names ``coord_fixed(`` is no call and ``"animation: false"`` in a
JavaScript string is no switch. Python strings go by their tokens; JavaScript
strings by a scan that keeps a template's ``${...}`` fields and an object key
in quotes. The patterns that read a value inside a string (a page colour set
from a script, ``"tight"``) use the code with its strings.

Stdlib only: ``impl-review.yml`` runs a copy taken at the workflow's own ref
with the job's pinned ``python3``, so a PR head cannot choose its own rules.

Subcommands::

    contract_check.py check --source NEW --spec-id S --language L --library B \
        [--prev PREV] [--out RECORD.json]
    contract_check.py selfcheck FILE --spec-id S --language L --library B

``check`` records, for ``impl-review.yml``. ``--source`` and ``--prev`` may
name files that do not exist: a missing new file reads as ``unreadable``, a
missing predecessor as a first generation.

``selfcheck`` is the generator's own run on the file it wrote
(``prompts/workflow-prompts/impl-generate-claude.md``, Step 2b). It prints
plain lines, writes no record and no job summary: one line per broken rule
with what it found and the prompt's words, ``palette`` marked advisory, and a
verdict line. It exits 0 when nothing must be fixed, 1 when something must,
and 2 when the file cannot be read.
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import os
import re
import sys
import tokenize
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple


RECORD_VERSION = 2
RULES = (
    "title",
    "theme",
    "save",
    "legacy-colour",
    "colormap",
    "palette",
    "bokeh-page-paint",
    "bokeh-toolbar",
    "pygal-tick-sizes",
    "pygal-grid-colour",
    "altair-autosize",
    "plotly-autosize",
    "letsplot-wrap",
    "bbox-tight",
    "animation",
)
# A deviation the owner allows with a good reason: the self-check names it, the generator decides.
ADVISORY = frozenset({"palette"})
LANGUAGES = ("python", "r", "julia", "javascript")

# Python blue and yellow, then the variant-D palette. An alpha suffix (#RRGGBBAA) counts too.
LEGACY_HEXES = ("306998", "FFD43B", "9418DB", "B71D27", "16B8F3", "D359A7", "BA843E")
LEGACY_RE = re.compile(r"#(?:" + "|".join(LEGACY_HEXES) + r")(?:[0-9A-Fa-f]{2})?\b", re.IGNORECASE)

# prompts/default-style-guide.md: the eight Imprint hues, the amber anchor, the
# stops of the continuous ramps, the ink and muted pairs, and the page,
# elevated and soft-ink tokens of both themes.
# tests/unit/automation/scripts/test_contract_check.py keeps this set equal to
# core/palette.py and inside the style guide.
PALETTE_HEXES = frozenset(
    {
        "#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314",  # Imprint
        "#DDCC77",  # amber
        "#66E2B2", "#024582", "#351E45", "#404C02", "#CDD9FF", "#6F7E20", "#686762",  # ramp stops (core.palette.RAMP_STOPS)
        "#1A1A17", "#F0EFE8",  # ink (and the dark page)
        "#6B6A63", "#A8A79F",  # muted
        "#FAF8F1", "#FFFDF6", "#242420",  # light page, elevated light, elevated dark
        "#4A4A44", "#B8B7B0",  # soft ink
    }
)  # fmt: skip
HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}\b")
PALETTE_DETAIL_CAP = 8

# Named colormaps of the libraries' own registries (matplotlib, seaborn, plotly, bokeh, ColorBrewer).
_NAMED = (
    r"(?:viridis|cividis|plasma|inferno|magma|turbo|jet|hsv|rainbow|gist_\w+|nipy_spectral|Spectral|BrBG|RdBu"
    r"|RdYlGn|RdYlBu|RdGy|PuOr|PiYG|PRGn|coolwarm|bwr|seismic|Blues|Greens|Reds|Oranges|Purples|Greys|YlOrRd"
    r"|YlOrBr|YlGnBu|YlGn|GnBu|BuGn|BuPu|PuBu|PuRd|RdPu|OrRd|hot|cool|copper|bone|gray|grey|binary|terrain"
    r"|ocean|twilight\w*|cubehelix|mako|rocket|flare|crest|icefire|vlag|Portland|Jet|Hot|Electric|Bluered"
    r"|Picnic|Rainbow|Viridis|Cividis|Plasma|Inferno|Magma|Turbo|Blackbody|Earth)(?:_r|256|\d{1,2})?"
)
# A keyword may be the tail of a longer name (`coloraxis_colorscale`, `mpl_cm`), never of a word.
_KW = r"(?<![A-Za-z0-9])"
COLORMAP_RES: dict[str, tuple[re.Pattern[str], ...]] = {
    "python": tuple(
        re.compile(pattern)
        for pattern in (
            rf"{_KW}(?:cmap|cmap_name|colorscale|color_continuous_scale|continuous_scale|palette)\s*=\s*[\"']{_NAMED}[\"']",
            # Vega schemes are always names (Altair builds an Imprint scale from a `range`).
            rf"{_KW}scheme\s*=\s*[\"'][A-Za-z][\w-]*[\"']",
            rf"(?:color_palette|get_cmap|scale_\w+_cmap)\(\s*[\"']{_NAMED}[\"']",
            rf"colormaps\[\s*[\"']{_NAMED}[\"']\s*\]",
            rf"{_KW}cm\.{_NAMED}\b",
            r"\bscale_\w+_(?:viridis\w*|brewer|distiller)\b",
            r"\b(?:Viridis|Inferno|Magma|Plasma|Cividis|Turbo)256\b",
            r"\bbokeh\.palettes\b[^\n]*\b(?:Spectral|RdBu|BrBG|Blues|Greens|Reds)\d+",
        )
    ),
    "r": tuple(
        re.compile(pattern)
        for pattern in (
            r"\bscale_\w+_(?:viridis\w*|brewer|distiller|fermenter)\(",
            r"\b(?:rainbow|heat\.colors|terrain\.colors|topo\.colors|cm\.colors|hsv|hcl\.colors)\(",
            r"\bbrewer\.pal\(|\bRColorBrewer::|\bviridisLite::|\bviridis::",
        )
    ),
    "julia": tuple(
        re.compile(pattern) for pattern in (rf"colou?rmap\s*=\s*(?::|\"){_NAMED}\b", rf"cgrad\(\s*(?::|\"){_NAMED}\b")
    ),
    "javascript": tuple(
        re.compile(pattern)
        for pattern in (
            r"\b(?:d3\.)?interpolate(?:Viridis|Turbo|Rainbow|Sinebow|Plasma|Inferno|Magma|Cividis|Cool|Warm"
            r"|Cubehelix\w*|Spectral|RdBu|RdYlGn|RdYlBu|BrBG|PuOr|PiYG|PRGn|Blues|Greens|Reds|Oranges|Purples"
            r"|Greys|YlOrRd|YlGnBu)\b",
            r"\b(?:d3\.)?scheme(?:Category10|Tableau10|Set[123]|Paired|Pastel[12]|Dark2|Accent|Spectral|RdBu"
            r"|BrBG|Blues|Greens|Reds)\b",
        )
    ),
}

THEME_RES = {
    "python": re.compile(r"[\"']ANYPLOT_THEME[\"']"),
    "r": re.compile(r"[\"']ANYPLOT_THEME[\"']"),
    "julia": re.compile(r"\"ANYPLOT_THEME\""),
    "javascript": re.compile(r"\bANYPLOT_(?:TOKENS|THEME)\b"),
}
# `plot-` followed by a value: an f-string or glue field, a %s, a Julia $ interpolation, or the
# end of the string and a `+`, `*` or `,` (concatenation, paste0, string).
SAVE_RE = re.compile(r"plot-(?:\{|%s|\$|[\"']\s*[+*,])")
BARE_SAVE_RE = re.compile(r"[\"'](?:\./)?plot\.(?:png|html|svg)[\"']")

# What each base rule finds, then the rule's own words and where they stand. The self-check prints them.
_GENERATE = "prompts/workflow-prompts/impl-generate-claude.md"
BASE_REASONS: dict[str, tuple[str, str, str]] = {
    "title": (
        "the title lacks the mandated tail with this language and library, or the code never names the spec id",
        "prompts/plot-generator.md",
        "{spec-id} · {language} · {library} · anyplot.ai",
    ),
    "theme": (
        "the code never reads the theme",
        _GENERATE,
        'Read `ANYPLOT_THEME` (`"light"` or `"dark"`, default `"light"`) and render accordingly.',
    ),
    "save": (
        "no file name is built from `plot-` and the theme, or a bare `plot.png`, `plot.html` or `plot.svg` is named",
        _GENERATE,
        "Save output as `plot-{THEME}.png` (theme-suffixed).",
    ),
    "legacy-colour": (
        "a brand colour of an earlier palette is in the code",
        "prompts/quality-criteria.md",
        "legacy `#306998` (Python Blue)",
    ),
    "colormap": (
        "a named library colormap stands where a colormap goes",
        _GENERATE,
        "No other cmaps — never viridis/cividis/BrBG/Reds/Blues/Greens or jet/hsv/rainbow.",
    ),
    "palette": (
        "these colours are outside the style guide's palette; keep one only for a reason that holds, such as a "
        "semantic exception of the style guide or a colour the spec names, and name it in the commit line",
        "prompts/default-style-guide.md",
        "Use Imprint palette positions 1→N in order for categorical data (see Color Philosophy). No custom hexes.",
    ),
}

# The page colour, in each way the catalogue sets it: a style property from a script, or CSS in the saved HTML.
_PAGE_PAINT_RE = re.compile(
    r"(?:documentElement|body)\.style\.(?:background|setProperty\(\s*[\"']background)"
    r"|(?:html|body)\s*\{[^}]*background"
    r"|<body[^>]*style=[\"'][^\"']*background"
)
_TOOLBAR_OFF_RE = re.compile(r"toolbar_location[\"']?\s*[=:]\s*None")
# A style key as a keyword (`label_font_size=44`) or as a dict key (`"label_font_size": 44`, for `Style(**kw)`).
# `label_font_size` alone, never the tail of `major_label_font_size` or `value_label_font_size`.
_PYGAL_MINOR_RE = re.compile(r"(?<![\w])[\"']?label_font_size[\"']?\s*[=:]\s*([^,\n)}]+)")
_PYGAL_MAJOR_RE = re.compile(r"\b[\"']?major_label_font_size[\"']?\s*[=:]\s*([^,\n)}]+)")
_PYGAL_GUIDE_RE = re.compile(r"(?<![\w])[\"']?guide_stroke_color[\"']?\s*[=:]")
_PYGAL_MAJOR_GUIDE_RE = re.compile(r"\b[\"']?major_guide_stroke_color[\"']?\s*[=:]")
# Chart types that draw no guide lines, and the world maps.
_PYGAL_GUIDELESS = frozenset({"Pie", "Treemap", "Gauge", "SolidGauge", "Funnel"})
_PYGAL_FROM_IMPORT_RE = re.compile(r"^\s*from\s+pygal\s+import\s+\(?([^)\n]+)", re.MULTILINE)
_PYGAL_MODULE_RE = re.compile(r"^\s*import\s+pygal(?:\s+as\s+(\w+))?\s*$", re.MULTILINE)
_ALTAIR_FIT_RE = re.compile(
    r"autosize\s*=\s*(?:alt\.AutoSizeParams\((?:\s*[\"']fit|[^)]*type\s*=\s*[\"']fit)"
    r"|\{[^}]*[\"']type[\"']\s*:\s*[\"']fit|[\"']fit)"
)
# Compound charts cannot fit: the concat, facet and repeat calls, a row, column or facet channel, and an `|`
# or `&` next to a name the code binds to an altair chart (`_altair_chart_names`). A layer (`alt.layer`, `+`)
# fits like a single chart, so it is judged. A pandas mask (`(df.a > 0) & (df.b > 0)`) is no composition.
_ALTAIR_COMPOUND_RE = re.compile(
    r"\balt\.(?:h|v)?concat\(|\.(?:facet|repeat)\(|\balt\.(?:Row|Column|Facet)\("
    r"|\b(?:row|column|facet)\s*=\s*(?:alt\.|[\"'])"
    r"|\)\s*[|&]=?\s*\(?\s*alt\.Chart\b"
)
_ALTAIR_CHART_ROOTS = ("Chart", "LayerChart", "layer", "hconcat", "vconcat", "concat", "HConcatChart", "VConcatChart")
_ASSIGNMENT_RE = re.compile(r"^\s*(\w+)\s*(?::[^=\n]+)?=(?!=)\s*\(?\s*([\w.]+)", re.MULTILINE)
_PLOTLY_AUTOSIZE_RE = re.compile(r"\bautosize[\"']?\s*[=:]\s*True\b")
_LETSPLOT_FIXED_RE = re.compile(r"\bcoord_(?:fixed|polar|map)\(")
_LETSPLOT_WRAP_RE = re.compile(r"\bgg(?:grid|bunch)\(")
_BBOX_TIGHT_RE = re.compile(r"bbox_inches\s*=\s*[\"']tight[\"']")
_JS_FALSE_NAME_RE = re.compile(r"\b(?:const|let|var)\s+(\w+)\s*=\s*false\b")
_JS_ANIMATION_VALUE_RE = re.compile(r"\banimation[\"']?\s*[:=]\s*([A-Za-z_$][\w$]*)")
_SKIP_ANIMATION_RE = re.compile(r"\bskipAnimation\b(?!\s*(?:=\s*\{\s*false\s*\}|:\s*false\b))")
_FSTRING_START = frozenset(
    getattr(tokenize, name) for name in ("FSTRING_START", "TSTRING_START") if hasattr(tokenize, name)
)
_FSTRING_END = frozenset(getattr(tokenize, name) for name in ("FSTRING_END", "TSTRING_END") if hasattr(tokenize, name))


def _without_strings(code: str) -> str:
    """Python ``code`` with every string literal emptied to ``""``, for the patterns that look for code.

    A title that names ``coord_fixed(`` or a label with an ``&`` in it no longer counts as code. An
    f-string goes whole, its fields included. Code that does not tokenize comes back unchanged. The
    patterns that read a value inside a string (a page colour in a script, ``"tight"``) use the code
    as it is.
    """
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(code).readline))
    except tokenize.TokenError, SyntaxError:
        return code
    starts = [0]
    for line in code.split("\n"):
        starts.append(starts[-1] + len(line) + 1)
    spans: list[tuple[int, int]] = []
    depth, opened = 0, 0
    for token in tokens:
        offset = starts[token.start[0] - 1] + token.start[1]
        if token.type in _FSTRING_START:
            if depth == 0:
                opened = offset
            depth += 1
        elif token.type in _FSTRING_END:
            depth -= 1
            if depth == 0:
                spans.append((opened, starts[token.end[0] - 1] + token.end[1]))
        elif token.type == tokenize.STRING and depth == 0:
            spans.append((offset, starts[token.end[0] - 1] + token.end[1]))
    for begin, end in reversed(spans):
        code = code[:begin] + '""' + code[end:]
    return code


def _number(code: str, expr: str) -> float | str:
    """A size as a number: a literal, or a name the code assigns a literal on a line of its own; else its text.

    The assignment may carry a type (``FS_TICK: int = 44``).
    """
    expr = expr.strip()
    if re.fullmatch(r"\d+(?:\.\d+)?", expr):
        return float(expr)
    if re.fullmatch(r"[A-Za-z_]\w*", expr):
        assigned = re.search(rf"^\s*{expr}\s*(?::[^=\n]+)?=\s*(\d+(?:\.\d+)?)\s*$", code, re.MULTILINE)
        if assigned:
            return float(assigned.group(1))
    return expr


def _pygal_two_tick_sizes(code: str) -> bool:
    minor, major = _PYGAL_MINOR_RE.search(code), _PYGAL_MAJOR_RE.search(code)
    if not minor and not major:
        return False
    if not (minor and major):
        return True
    small, large = _number(code, minor.group(1)), _number(code, major.group(1))
    if isinstance(small, float) and isinstance(large, float):
        return small != large
    return False  # two names the code does not resolve: not judged


def _pygal_chart_types(code: str) -> set[str]:
    """The pygal chart types the code builds: ``pygal.Pie(``, an alias of the module, or a name imported from it."""
    modules = {"pygal"} | {alias for alias in _PYGAL_MODULE_RE.findall(code) if alias}
    types = set()
    for module in modules:
        types |= set(re.findall(rf"\b{module}\.([A-Z]\w*)\s*\(", code))
    for imported in _PYGAL_FROM_IMPORT_RE.findall(code):
        for item in imported.split(","):
            name, _, alias = item.strip().partition(" as ")
            if name[:1].isupper() and re.search(rf"\b{alias.strip() or name}\s*\(", code):
                types.add(name)
    return types - {"Style"}


def _pygal_black_guides(code: str) -> bool:
    structure = _without_strings(code)
    charts = _pygal_chart_types(structure)
    if "pygal_maps_" in structure or (charts and charts <= _PYGAL_GUIDELESS):
        return False
    if re.search(r"\bshow_y_guides\s*=\s*False", structure) and not re.search(r"\bshow_x_guides\s*=\s*True", structure):
        return False
    return not (_PYGAL_GUIDE_RE.search(code) and _PYGAL_MAJOR_GUIDE_RE.search(code))


def _altair_chart_names(code: str) -> set[str]:
    """Names bound to an altair chart: from ``alt.Chart`` and the other chart builders, or from such a name."""
    assignments = _ASSIGNMENT_RE.findall(code)
    names: set[str] = set()
    while True:
        found = {
            name
            for name, value in assignments
            if value.split(".")[0] in names or (value.startswith("alt.") and value.split(".")[1] in _ALTAIR_CHART_ROOTS)
        }
        if found <= names:
            return names
        names |= found


def _altair_compound(code: str) -> bool:
    structure = _without_strings(code)
    if _ALTAIR_COMPOUND_RE.search(structure):
        return True
    names = _altair_chart_names(structure)
    return any(re.search(rf"\b{name}\s*[|&]|[|&]=?\s*\(?\s*{name}\b", structure) for name in names)


_JS_OBJECT_KEY_RE = re.compile(r"\s*:")


def _js_scan(code: str, index: int, in_field: bool) -> tuple[str, int]:
    """``code`` from ``index`` with its string literals emptied; in a template field, up to its closing brace.

    Returns the text and the index where the scan stopped. A quote that is still open at the end of its
    line closes there, as in the comment scan (an apostrophe in JSX text). A string followed by a colon
    is an object key (``"animation": false``) and keeps its text.
    """
    out: list[str] = []
    depth = 0
    size = len(code)
    while index < size:
        char = code[index]
        if char in "'\"":
            end = index + 1
            while end < size and code[end] not in (char, "\n"):
                end += 2 if code[end] == "\\" else 1
            end = min(end + 1 if end < size and code[end] == char else end, size)
            out.append(code[index:end] if _JS_OBJECT_KEY_RE.match(code, end) else char * 2)
            index = end
        elif char == "`":
            out.append("`")
            index += 1
            while index < size and code[index] != "`":
                if code[index] == "\\":
                    index += 2
                elif code.startswith("${", index):
                    field, index = _js_scan(code, index + 2, in_field=True)
                    out.append("${" + field + "}")
                    index += 1
                else:
                    index += 1
            out.append("`")
            index += 1
        elif in_field and char == "}" and depth == 0:
            return "".join(out), index
        else:
            depth += {"{": 1, "}": -1}.get(char, 0)
            out.append(char)
            index += 1
    return "".join(out), index


def _js_without_strings(code: str) -> str:
    """JavaScript ``code`` (comments already gone) with the text of every string and template emptied.

    A template's ``${...}`` fields stay code. A regular expression literal that holds a quote
    (``/'/g``) reads as a string to the end of its line: a known edge, which only ever hides code.
    """
    return _js_scan(code, 0, in_field=False)[0]


def _animation_switches(code: str) -> int | None:
    """How often the code turns animation off: a literal ``false``, a name bound to it, or a named object that
    holds the switch, counted where it is used. None when a value is a name the code does not resolve.

    A switch written inside a string (``const note = "animation: false"``) is text, not a switch.
    """
    code = _js_without_strings(code)
    false_names = set(_JS_FALSE_NAME_RE.findall(code))
    values = _JS_ANIMATION_VALUE_RE.findall(code)
    if any(value not in false_names | {"false", "true"} for value in values):
        return None
    switches = sum(value in false_names | {"false"} for value in values)
    off = "|".join(["false", *sorted(false_names)])
    holder = re.compile(rf"\b(?:const|let|var)\s+(\w+)\s*=\s*\{{[^{{}}]*\banimation[\"']?\s*:\s*(?:{off})\b")
    for name in holder.findall(code):
        # The object's own switch counts once for every place it is used, not for its definition.
        # A spread (`...NAME`) is a use; a member access (`obj.NAME`) is another name.
        switches += len(re.findall(rf"(?:(?<=\.\.\.)|(?<![\w$.])){re.escape(name)}(?![\w$])", code)) - 2
    return switches


_FIXED_ASPECT_CALLS = frozenset({"coord_fixed", "coord_polar", "coord_map"})
_WRAPPER_CALLS = frozenset({"gggrid", "ggbunch"})


def _call_name(node: ast.AST) -> str | None:
    if not isinstance(node, ast.Call):
        return None
    if isinstance(node.func, ast.Name):
        return node.func.id
    return node.func.attr if isinstance(node.func, ast.Attribute) else None


def _outside_wrappers(node: ast.AST):
    """The nodes of ``node`` without the arguments of a ``gggrid`` or ``ggbunch`` call: a theme in there
    paints a panel's own plot box, not the wrapper's canvas."""
    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        if _call_name(current) not in _WRAPPER_CALLS:
            stack.extend(ast.iter_child_nodes(current))


def _paints_the_page(node: ast.AST, page_themes: set[str]) -> bool:
    """A ``theme(plot_background=element_rect(fill=...))``, or a name bound to one (``anyplot_theme``)."""
    if isinstance(node, ast.Name):
        return node.id in page_themes
    if _call_name(node) != "theme" or not isinstance(node, ast.Call):
        return False
    return any(
        keyword.arg == "plot_background"
        and isinstance(keyword.value, ast.Call)
        and _call_name(keyword.value) == "element_rect"
        and any(inner.arg == "fill" for inner in keyword.value.keywords)
        for keyword in node.keywords
    )


def _letsplot_unwrapped(code: str) -> bool:
    """A fixed-aspect plot that no ``gggrid`` or ``ggbunch`` both holds and paints in the page colour.

    The statements are read in order. A name holds the fixed-aspect plot when its value calls a fixed
    coordinate system or names such a name; a wrapper holds it when its arguments do. The wrapper is
    painted when the expression it stands in, or a later statement on the name it went to, adds a theme
    with a ``plot_background`` fill outside the wrapper's arguments. A file that does not parse is
    judged by the calls alone.
    """
    structure = _without_strings(code)
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return bool(_LETSPLOT_FIXED_RE.search(structure)) and not _LETSPLOT_WRAP_RE.search(structure)
    statements: list[tuple[set[str], ast.AST, bool]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = {name.id for target in node.targets for name in ast.walk(target) if isinstance(name, ast.Name)}
            statements.append((targets, node.value, False))
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)) and node.value is not None:
            targets = {name.id for name in ast.walk(node.target) if isinstance(name, ast.Name)}
            statements.append((targets, node.value, isinstance(node, ast.AugAssign)))
        elif isinstance(node, ast.Expr):
            statements.append((set(), node.value, False))
    statements.sort(key=lambda item: (getattr(item[1], "lineno", 0), getattr(item[1], "col_offset", 0)))
    fixed: set[str] = set()
    page_themes: set[str] = set()
    holders: set[str] = set()
    any_fixed = wrapped = painted = False
    for targets, value, augmented in statements:
        nodes = list(ast.walk(value))
        names = {node.id for node in nodes if isinstance(node, ast.Name)} | (targets if augmented else set())
        calls_fixed = any(_call_name(node) in _FIXED_ASPECT_CALLS for node in nodes)
        any_fixed |= calls_fixed
        if calls_fixed or names & fixed:
            fixed |= targets
        builds_plot = any(_call_name(node) in {"ggplot", *_WRAPPER_CALLS} for node in nodes)
        if not builds_plot and any(_paints_the_page(node, page_themes) for node in nodes):
            page_themes |= targets  # a theme the file names, such as `anyplot_theme`
        holding = [
            node
            for node in nodes
            if isinstance(node, ast.Call)
            and _call_name(node) in _WRAPPER_CALLS
            and any(
                (isinstance(inner, ast.Name) and inner.id in fixed) or _call_name(inner) in _FIXED_ASPECT_CALLS
                for argument in [*node.args, *(keyword.value for keyword in node.keywords)]
                for inner in ast.walk(argument)
            )
        ]
        if holding or names & holders:
            wrapped |= bool(holding)
            holders |= targets
            painted |= any(_paints_the_page(node, page_themes) for node in _outside_wrappers(value))
    return any_fixed and not (wrapped and painted)


def _too_few_animation_switches(needed: int) -> Callable[[str], bool]:
    def breaks(code: str) -> bool:
        switches = _animation_switches(code)
        return switches is not None and switches < needed

    return breaks


class Mandate(NamedTuple):
    """One setting a library prompt mandates, as a test over the code, with the prompt's own words."""

    key: str
    library: str
    breaks: Callable[[str], bool]
    found: str
    quote: str


MANDATES: tuple[Mandate, ...] = (
    Mandate(
        "bokeh-page-paint",
        "bokeh",
        lambda code: "webdriver" in _without_strings(code) and not _PAGE_PAINT_RE.search(code),
        "the screenshot never paints the browser page in the page colour, so a light line runs along the top "
        "and left edge of the PNG",
        "IMPORTANT: paint the page in the theme's page color.",
    ),
    Mandate(
        "bokeh-toolbar",
        "bokeh",
        lambda code: not _TOOLBAR_OFF_RE.search(code),
        "the figure keeps bokeh's toolbar, which takes room from the plot",
        "**Do not omit `toolbar_location=None`**",
    ),
    Mandate(
        "pygal-tick-sizes",
        "pygal",
        _pygal_two_tick_sizes,
        "the style sets `label_font_size` and `major_label_font_size` to different sizes, or only one of them, "
        "so one axis shows tick labels in two sizes",
        "major tick labels: the same size, or one axis shows two sizes",
    ),
    Mandate(
        "pygal-grid-colour",
        "pygal",
        _pygal_black_guides,
        "the chart draws guide lines but the style leaves `guide_stroke_color` or `major_guide_stroke_color` at "
        "pygal's black, which almost vanishes on the dark page",
        "Set both from `INK_MUTED` in the `Style`, as above, so the grid stays a muted tone in both themes.",
    ),
    Mandate(
        "altair-autosize",
        "altair",
        lambda code: not _altair_compound(code) and not _ALTAIR_FIT_RE.search(code),
        "the chart does not fit its width and height, so title, axes and legend land outside them",
        'Both with `autosize=alt.AutoSizeParams(type="fit", contains="padding")`',
    ),
    Mandate(
        "plotly-autosize",
        "plotly",
        lambda code: bool(_PLOTLY_AUTOSIZE_RE.search(code)),
        "the layout turns autosize on, which overrides the width and height",
        "`fig.update_layout(autosize=True)` is **forbidden**",
    ),
    Mandate(
        "letsplot-wrap",
        "letsplot",
        _letsplot_unwrapped,
        "a fixed-aspect plot is not held by a `gggrid` or `ggbunch` that carries the page colour "
        "(`theme(plot_background=element_rect(fill=PAGE_BG, ...))` on the wrapper), so the canvas outside its "
        "plot box stays transparent",
        "Wrap the finished plot in a one-panel `gggrid` of the canvas size that carries the page color.",
    ),
    Mandate(
        "bbox-tight",
        "matplotlib",
        lambda code: bool(_BBOX_TIGHT_RE.search(code)),
        'the figure is saved with `bbox_inches="tight"`, which trims the canvas',
        '**Do not use `bbox_inches="tight"` on `savefig`.**',
    ),
    Mandate(
        "bbox-tight",
        "seaborn",
        lambda code: bool(_BBOX_TIGHT_RE.search(code)),
        'the figure is saved with `bbox_inches="tight"`, which trims the canvas',
        '**Do not use `bbox_inches="tight"` on `savefig`.**',
    ),
    Mandate(
        "animation",
        "chartjs",
        _too_few_animation_switches(1),
        "the chart keeps its entrance animation, so the screenshot can catch a frame before the last",
        "`animation: false` is mandatory",
    ),
    Mandate(
        "animation",
        "echarts",
        _too_few_animation_switches(1),
        "the chart keeps its entrance animation, so the screenshot can catch a frame before the last",
        "**`animation: false` is mandatory**",
    ),
    Mandate(
        "animation",
        "highcharts",
        # Both switches, the chart's and the series': with only one the series still grow in.
        _too_few_animation_switches(2),
        "the chart and its series do not both turn animation off, so the series can still grow in when the "
        "screenshot is taken",
        "**`animation: false` is mandatory** (both `chart.animation` and",
    ),
    Mandate(
        "animation",
        "muix",
        lambda code: not _SKIP_ANIMATION_RE.search(_js_without_strings(code)),
        "no chart component passes `skipAnimation`, so the screenshot can catch a frame before the last",
        "**`skipAnimation` is mandatory**",
    ),
)


def strip_header(language: str, source: str) -> str:
    """The source without its generated header: the leading comment lines and, in Python, the docstring.

    The header is whatever the file starts with, however long: the run of
    comment lines (R's ``#'``, JavaScript's ``//#`` directives, a Python
    ``# ruff: noqa`` line), then a Python docstring.
    """
    lines = source.lstrip("﻿").split("\n")
    marker = "//" if language == "javascript" else "#"
    first_code = 0
    in_block = False
    for index, line in enumerate(lines):
        bare = line.strip()
        if language == "javascript" and (in_block or bare.startswith("/*")):
            in_block = "*/" not in bare
            first_code = index + 1
            continue
        if not bare or bare.startswith(marker):
            first_code = index + 1
            continue
        break
    rest = "\n".join(lines[first_code:])
    if language == "python":
        for quote in ('"""', "'''"):
            if rest.startswith(quote):
                end = rest.find(quote, len(quote))
                return rest[end + len(quote) :] if end != -1 else ""
    return rest


# Per language: the line-comment marker, the block-comment delimiters, and the string quotes.
_COMMENT_SYNTAX: dict[str, tuple[str, tuple[str, str] | None, str]] = {
    "python": ("#", None, "\"'"),
    "r": ("#", None, "\"'"),
    "julia": ("#", ("#=", "=#"), '"'),
    "javascript": ("//", ("/*", "*/"), "\"'`"),
}


def _scan_out_comments(code: str, marker: str, block: tuple[str, str] | None, quotes: str) -> str:
    """``code`` without line comments and block comments, read character by character.

    A marker inside a string literal is text, not a comment. A quote that is
    still open at the end of its line closes there (an apostrophe in JSX text,
    Julia's transpose), except a backtick: a template literal spans lines.
    """
    out: list[str] = []
    quote = ""
    index = 0
    size = len(code)
    while index < size:
        char = code[index]
        if quote:
            out.append(char)
            if char == "\\" and index + 1 < size:
                out.append(code[index + 1])
                index += 2
                continue
            if char == quote or (char == "\n" and quote != "`"):
                quote = ""
            index += 1
            continue
        if block and code.startswith(block[0], index):
            end = code.find(block[1], index + len(block[0]))
            index = size if end == -1 else end + len(block[1])
            continue
        if code.startswith(marker, index):
            end = code.find("\n", index)
            index = size if end == -1 else end
            continue
        if char in quotes:
            quote = char
        out.append(char)
        index += 1
    return "".join(out)


def _python_comment_columns(code: str) -> dict[int, int] | None:
    """Row to column of every comment token, or None when the code does not tokenize."""
    columns: dict[int, int] = {}
    try:
        for token in tokenize.generate_tokens(io.StringIO(code).readline):
            if token.type == tokenize.COMMENT:
                columns[token.start[0]] = token.start[1]
    except tokenize.TokenError, SyntaxError:
        return None
    return columns


def strip_comments(language: str, code: str) -> str:
    """The code without comments: Python by its tokens, the others by a scan that knows strings.

    A ``#`` or ``//`` inside a string stays (a hex colour, a URL, ``"Issue # 42"``).
    Line comments and whole block comments go (JavaScript ``/* */``, Julia
    ``#= =#``), over as many lines as they span, and so do the lines they leave empty.
    """
    columns = _python_comment_columns(code) if language == "python" else None
    if columns is not None:
        lines = code.split("\n")
        for row, column in columns.items():
            lines[row - 1] = lines[row - 1][:column]
    else:
        lines = _scan_out_comments(code, *_COMMENT_SYNTAX[language]).split("\n")
    return "\n".join(line for line in lines if line.strip())


def custom_hexes(code: str) -> list[str]:
    """The six-digit hexes of ``code`` outside the style guide's set, upper case, in order of appearance."""
    seen: list[str] = []
    for match in HEX_RE.findall(code):
        value = match.upper()
        if value not in PALETTE_HEXES and value not in seen:
            seen.append(value)
    return seen


def check(source: str, *, spec_id: str, language: str, library: str) -> tuple[list[str], dict[str, list[str]]]:
    """The rules ``source`` breaks, in ``RULES`` order, and per rule what it found (the palette rule's hexes)."""
    code = strip_comments(language, strip_header(language, source))
    found = []
    details: dict[str, list[str]] = {}
    if f"{language} · {library} · anyplot.ai" not in code or spec_id not in code:
        found.append("title")
    if not THEME_RES[language].search(code):
        found.append("theme")
    if language != "javascript" and (not SAVE_RE.search(code) or BARE_SAVE_RE.search(code)):
        found.append("save")
    if LEGACY_RE.search(code):
        found.append("legacy-colour")
    if any(pattern.search(code) for pattern in COLORMAP_RES[language]):
        found.append("colormap")
    hexes = custom_hexes(code)
    if hexes:
        found.append("palette")
        details["palette"] = hexes[:PALETTE_DETAIL_CAP]
    found += [mandate.key for mandate in MANDATES if mandate.library == library and mandate.breaks(code)]
    return found, details


def violations(source: str, *, spec_id: str, language: str, library: str) -> list[str]:
    """The rules ``source`` breaks, in ``RULES`` order."""
    return check(source, spec_id=spec_id, language=language, library=library)[0]


def _read(path: str | None) -> str | None:
    if not path:
        return None
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError, UnicodeDecodeError:
        return None


def build_record(new: str | None, prev: str | None, *, spec_id: str, language: str, library: str) -> dict:
    """The record of one check: the new file's violations, the predecessor's, and the ones only the new file has."""
    record: dict = {"version": RECORD_VERSION, "spec_id": spec_id, "language": language, "library": library}
    if new is None:
        return {
            **record,
            "status": "unreadable",
            "violations": [],
            "prev_violations": None,
            "new_only": [],
            "details": {},
        }
    now, details = check(new, spec_id=spec_id, language=language, library=library)
    before = None if prev is None else violations(prev, spec_id=spec_id, language=language, library=library)
    new_only = now if before is None else [rule for rule in now if rule not in before]
    return {
        **record,
        "status": "clean" if not now else "violations",
        "violations": now,
        "prev_violations": before,
        "new_only": new_only,
        "details": details,
    }


def summary_line(record: dict) -> str:
    """One Markdown line for the job summary."""
    if record["status"] == "unreadable":
        return "**Contract check (record-only):** unreadable (no implementation file at the PR head)"
    if record["status"] == "clean":
        return "**Contract check (record-only):** clean"
    line = "**Contract check (record-only):** " + ", ".join(record["violations"])
    if record["prev_violations"] is not None:
        line += " (new in this version: " + (", ".join(record["new_only"]) or "none") + ")"
    if record["details"].get("palette"):
        line += "; outside the palette: " + ", ".join(f"`{value}`" for value in record["details"]["palette"])
    return line


def notice_line(record: dict) -> str:
    """One log line, the same shape as ``canvas_gate`` and ``render_hash``."""
    prev = "n/a" if record["prev_violations"] is None else (",".join(record["prev_violations"]) or "none")
    line = (
        f"::notice::contract_check library={record['library']} status={record['status']} "
        f"violations={','.join(record['violations']) or 'none'} prev={prev} "
        f"new_only={','.join(record['new_only']) or 'none'}"
    )
    if record["details"].get("palette"):
        line += " palette_hexes=" + ",".join(record["details"]["palette"])
    return line


def reason(key: str, library: str) -> tuple[str, str, str]:
    """What rule ``key`` found in a ``library`` file, and the words of the prompt that sets it, with their path."""
    if key in BASE_REASONS:
        return BASE_REASONS[key]
    mandate = next(mandate for mandate in MANDATES if mandate.key == key and mandate.library == library)
    return mandate.found, f"prompts/library/{library}.md", mandate.quote


def selfcheck_lines(source: str | None, *, spec_id: str, language: str, library: str) -> tuple[list[str], int]:
    """The generator's own run: one line per broken rule, then the verdict line, and the exit code.

    0 when nothing must be fixed (an advisory line may remain), 1 when something must, 2 when there is no file.
    """
    if source is None:
        return ["contract: not run (the file is missing or not UTF-8 text)"], 2
    found, details = check(source, spec_id=spec_id, language=language, library=library)
    lines = []
    for key in found:
        what, path, quote = reason(key, library)
        if key in ADVISORY:
            listed = ", ".join(details.get(key, []))
            lines.append(f"{key} (advisory): {listed}: {what} → {path}: “{quote}”")
        else:
            lines.append(f"{key}: {what} → {path}: “{quote}”")
    must = [key for key in found if key not in ADVISORY]
    advisory = [key for key in found if key in ADVISORY]
    if must:
        lines.append(f"contract: fix ({', '.join(must)})")
    else:
        lines.append("contract: pass" + (f" (advisory: {', '.join(advisory)})" if advisory else ""))
    return lines, 1 if must else 0


def cmd_selfcheck(args: argparse.Namespace) -> int:
    lines, code = selfcheck_lines(_read(args.file), spec_id=args.spec_id, language=args.language, library=args.library)
    print("\n".join(lines))
    return code


def cmd_check(args: argparse.Namespace) -> int:
    record = build_record(
        _read(args.source), _read(args.prev), spec_id=args.spec_id, language=args.language, library=args.library
    )
    print(notice_line(record))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(summary_line(record) + "\n")
    if args.out:
        Path(args.out).write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = parser.add_subparsers(dest="command", required=True)
    check_parser = sub.add_parser("check", help="check one implementation file, record-only")
    check_parser.add_argument("--source", required=True, help="the implementation at the PR head")
    check_parser.add_argument(
        "--prev", help="the predecessor from main (a regeneration); a missing file is a first generation"
    )
    check_parser.add_argument("--spec-id", required=True)
    check_parser.add_argument("--language", required=True, choices=LANGUAGES)
    check_parser.add_argument("--library", required=True)
    check_parser.add_argument("--out", help="write the record as one JSON line")
    check_parser.set_defaults(func=cmd_check)
    self_parser = sub.add_parser("selfcheck", help="the generator's own run on its file: plain lines, exit 0/1/2")
    self_parser.add_argument("file", help="the implementation file the session wrote")
    self_parser.add_argument("--spec-id", required=True)
    self_parser.add_argument("--language", required=True, choices=LANGUAGES)
    self_parser.add_argument("--library", required=True)
    self_parser.set_defaults(func=cmd_selfcheck)
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
