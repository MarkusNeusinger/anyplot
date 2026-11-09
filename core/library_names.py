"""The names people write for the catalogue's libraries, and for the tools outside it.

One table for every place that reads a library's name in someone's words, so `d3`, `D3.js` and
`d3 js` are the same library everywhere: today the agent chat's scope guard, which never sends a
request for a library the chat serves to the catalogue as another library
(`agents/anyplot/plugins/scope_guard.served_library_request`), and the chat's `switch_plot` tool,
whose library argument a model writes (`agents/anyplot/schemas.SwitchArgs`).

A name matches whatever its case and Unicode width, and whatever separates its parts: spaces, dots,
hyphens, underscores, slashes or nothing. So `Chart.js` is also `chartjs`, `chart js` and
`Chart-JS`, and `lets-plot` is also `letsplot`, `lets plot` and `lets_plot`. A name never matches
inside a longer word: `id3` names no library, and `pyecharts` is not ECharts. Where two names start
at the same place, the longer one wins: `plotly.js` is the JavaScript library outside the catalogue,
not Plotly, and `Vega-Altair` is Altair, not Vega.

A word that names no library on its own, such as `chart`, `plot`, `graph` or `x`, is in no table:
`chart` is a library only as `chart js`, and `x` only after `mui`.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from .constants import LIBRARY_NAMES, SUPPORTED_LIBRARIES


LIBRARY_ALIASES: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "altair": ("Vega-Altair",),
        "echarts": ("ECharts", "ECharts.js"),
        "ggplot2": ("ggplot",),
        "highcharts": ("Highcharts.js",),
        "makie": ("CairoMakie", "GLMakie", "WGLMakie"),
        "matplotlib": ("mpl", "pyplot"),
        "muix": ("MUI", "MUI X", "MUI Charts"),
        "plotly": ("Plotly Express",),
    }
)
"""Each catalogue library's names besides its id and its display name (`constants.LIBRARY_NAMES`), which match too.

With the separator rule, the id and the display name already cover most forms: `D3.js` covers `d3js` and `d3 js`,
`MUI X Charts` covers `mui x charts`, `Makie.jl` covers `makie jl`, `lets-plot` covers `lets plot`. A short form
belongs here only when it names one library and nothing else: `sns`, `plt` and `px` are left out, because they are
also an abbreviation, a variable or a unit."""

OUTSIDE_TOOLS: tuple[str, ...] = (
    # JavaScript charting outside the catalogue.
    "Vega",
    "Vega-Lite",
    "Plotly.js",
    "BokehJS",
    "Observable Plot",
    "ObservableHQ",
    "nivo",
    "Recharts",
    "visx",
    "ApexCharts",
    "amCharts",
    "Google Charts",
    "C3.js",
    "NVD3",
    "dc.js",
    "billboard.js",
    "Chartist",
    "uPlot",
    "Frappe Charts",
    "AnyChart",
    "FusionCharts",
    "ZingChart",
    "CanvasJS",
    "three.js",
    "p5.js",
    "react-vis",
    "AG Charts",
    "Lightweight Charts",
    "Chartkick",
    "Mermaid",
    "Graphviz",
    # Python outside the catalogue.
    "pyecharts",
    "HoloViews",
    "hvPlot",
    "pyqtgraph",
    "VisPy",
    "Mayavi",
    "PyGWalker",
    "plotext",
    "ProPlot",
    "UltraPlot",
    "Folium",
    "Streamlit",
    "Gradio",
    # R outside the catalogue.
    "base R",
    "R base",
    "base graphics",
    "lattice",
    "highcharter",
    "echarts4r",
    "ggvis",
    "rCharts",
    "R Shiny",
    "Shiny app",
    # Julia outside the catalogue.
    "Plots.jl",
    "Gadfly",
    "UnicodePlots",
    "PGFPlotsX",
    # Programs.
    "Excel",
    "Google Sheets",
    "LibreOffice",
    "OpenOffice",
    "Tableau",
    "Power BI",
    "Looker",
    "Qlik",
    "Grafana",
    "Kibana",
    "Metabase",
    "Datawrapper",
    "SPSS",
    "Stata",
    "SAS",
    "Minitab",
    "OriginPro",
    "GraphPad",
    "SigmaPlot",
    "MATLAB",
    "Octave",
    "Mathematica",
    "Wolfram",
    "Maple",
    "gnuplot",
    "TikZ",
    "PGFPlots",
    "PowerPoint",
    "Keynote",
    "Google Slides",
    "Photoshop",
    "Illustrator",
    "Inkscape",
    "Figma",
    "Canva",
    # Languages none of the catalogue's libraries is written in.
    "Java",
    "C#",
    "C++",
    "F#",
    "Rust",
    "Golang",
    "Swift",
    "Kotlin",
    "PHP",
    "Ruby",
    "Perl",
    "Scala",
    "Dart",
    "Flutter",
    "Fortran",
    "COBOL",
    "VBA",
    "Visual Basic",
    "Haskell",
    "Lua",
)
"""Plotting libraries, programs and languages outside the catalogue, named the way people write them.

A message for this plot that names one of them asks for something the catalogue does not hold, even when it also
names a catalogue library ("port this D3 plot to Vega-Lite"). The list makes no request in-scope or not on its own:
it only keeps a message that names one from counting as a request for a catalogue library alone. A common word that
is also such a name (`origin`, `prism`, `dash`, `go`, `numbers`, `shiny`, `observable`) is left out or named with
its context (`R Shiny`, `Observable Plot`)."""

_SEPARATOR = r"[\s._/-]*"
_PART = re.compile(r"[0-9a-z+#]+")
_EDGE_BEFORE = r"(?<![^\W_])"
_EDGE_AFTER = rf"(?![^\W_])(?!{_SEPARATOR}j[sl](?![^\W_]))"
"""A name starts and ends at a letter or digit that has none next to it (an underscore counts as a separator), and
never right before a `.js` or `.jl` it does not include: `matplotlib.js` and `bokeh.js` name no catalogue library,
while `D3.js` and `Makie.jl` do, as names of their own."""


def _fold(text: str) -> str:
    return unicodedata.normalize("NFKC", text).casefold()


def name_key(name: str) -> str:
    """A name without its case, width and separators: `D3.js`, `d3 js` and `D3JS` are all `d3js`."""
    return "".join(_PART.findall(_fold(name)))


def _pattern(name: str) -> str:
    return _SEPARATOR.join(re.escape(part) for part in _PART.findall(_fold(name)))


def _names() -> list[tuple[str, str | None]]:
    """Every name with its owner: a catalogue library's id, or None for a tool outside the catalogue."""
    names: list[tuple[str, str | None]] = []
    for library in sorted(SUPPORTED_LIBRARIES):
        for name in (library, LIBRARY_NAMES[library], *LIBRARY_ALIASES.get(library, ())):
            names.append((name, library))
    names.extend((name, None) for name in OUTSIDE_TOOLS)
    return names


def _owners() -> dict[str, str | None]:
    owners: dict[str, str | None] = {}
    for name, owner in _names():
        key = name_key(name)
        if key in owners and owners[key] != owner:
            raise ValueError(f"the name {name!r} belongs to {owners[key]!r} and {owner!r}")
        owners[key] = owner
    return owners


def _alternatives() -> str:
    """Every name's pattern, the longest name first: a regex alternation takes the first alternative that matches."""
    keys = {_pattern(name): name_key(name) for name, _ in _names()}
    return "|".join(sorted(keys, key=lambda pattern: (-len(keys[pattern]), -len(pattern), pattern)))


_OWNERS = _owners()
_ALTERNATIVES = _alternatives()
_IN_TEXT = re.compile(f"{_EDGE_BEFORE}(?:{_ALTERNATIVES}){_EDGE_AFTER}")
_WHOLE = re.compile(f"(?:{_ALTERNATIVES})")


@dataclass(frozen=True)
class NamedTools:
    """What a text names: catalogue libraries by id, and whether it also names a tool outside the catalogue."""

    libraries: frozenset[str]
    outside: bool


def named_tools(text: str) -> NamedTools:
    """The catalogue libraries `text` names in any common form (`d3`, `Chart.js`, `mui x`), and whether it also names
    a tool outside the catalogue (`OUTSIDE_TOOLS`)."""
    libraries: set[str] = set()
    outside = False
    for match in _IN_TEXT.finditer(_fold(text)):
        owner = _OWNERS[name_key(match.group(0))]
        if owner is None:
            outside = True
        else:
            libraries.add(owner)
    return NamedTools(frozenset(libraries), outside)


def resolve_library(name: str) -> str | None:
    """The catalogue library's id that `name` is as a whole, in any common form (`D3.js`, `chart js`, `MUI X`), or None.

    A tool outside the catalogue, a word that names no library (`chart`) and a name with anything else around it
    (`Seaborn!`, `d3 please`) are None, so a caller keeps its own check for them.
    """
    match = _WHOLE.fullmatch(_fold(name).strip())
    return _OWNERS.get(name_key(match.group(0))) if match else None
