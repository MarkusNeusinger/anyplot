"""The names people write for the catalogue's libraries (core/library_names.py)."""

import pytest

from core.constants import LIBRARY_NAMES, SUPPORTED_LIBRARIES
from core.library_names import LIBRARY_ALIASES, OUTSIDE_TOOLS, NamedTools, name_key, named_tools, resolve_library


COMMON_FORMS = {
    "d3": ["d3", "D3", "d3js", "d3.js", "D3.js", "d3 js", "D3-JS"],
    "chartjs": ["chartjs", "chart.js", "Chart.js", "chart js", "Chart-JS", "CHARTJS"],
    "echarts": ["echarts", "ECharts", "echarts.js", "apache echarts", "Apache ECharts"],
    "highcharts": ["highcharts", "Highcharts", "highcharts.js"],
    "muix": ["mui", "MUI", "mui x", "MUI X", "muix", "mui-x", "mui x charts", "MUI X Charts", "mui charts"],
    "makie": ["makie", "Makie", "makie.jl", "Makie.jl", "makie jl", "cairomakie", "CairoMakie", "GLMakie"],
    "ggplot2": ["ggplot", "ggplot2", "GGPLOT2"],
    "letsplot": ["lets-plot", "letsplot", "lets plot", "lets_plot", "Lets-Plot"],
    "plotnine": ["plotnine", "Plotnine"],
    "pygal": ["pygal", "Pygal"],
    "bokeh": ["bokeh", "Bokeh"],
    "altair": ["altair", "Altair", "Vega-Altair"],
    "plotly": ["plotly", "Plotly", "plotly express"],
    "seaborn": ["seaborn", "Seaborn"],
    "matplotlib": ["matplotlib", "Matplotlib", "mpl", "pyplot"],
}


def test_every_catalogue_library_has_its_forms() -> None:
    assert set(COMMON_FORMS) == SUPPORTED_LIBRARIES
    assert set(LIBRARY_ALIASES) <= SUPPORTED_LIBRARIES


@pytest.mark.parametrize(("library", "form"), [(lib, form) for lib, forms in COMMON_FORMS.items() for form in forms])
def test_every_common_form_resolves_and_is_named_in_a_sentence(library: str, form: str) -> None:
    assert resolve_library(form) == library
    assert named_tools(f"please make this in {form}, thanks") == NamedTools(frozenset({library}), False)
    assert named_tools(f"erstell das bitte mal in {form}") == NamedTools(frozenset({library}), False)


@pytest.mark.parametrize("library", sorted(SUPPORTED_LIBRARIES))
def test_the_id_and_the_display_name_resolve(library: str) -> None:
    assert resolve_library(library) == library and resolve_library(LIBRARY_NAMES[library]) == library


@pytest.mark.parametrize(
    "name",
    ["Vega-Lite", "vegalite", "nivo", "Recharts", "Plots.jl", "plotly.js", "BokehJS", "Excel", "Tableau", "MATLAB"],
)
def test_a_tool_outside_the_catalogue_resolves_to_no_library(name: str) -> None:
    assert resolve_library(name) is None
    assert named_tools(f"this plot in {name}") == NamedTools(frozenset(), True)


@pytest.mark.parametrize(
    "text",
    [
        "R base graphics",
        "base R please",
        "Julia Plots.jl",
        "port it to C++",
        "give me the C# code",
        "Kannst du das in Excel machen?",
        "in Power BI",
        "vega lite",
    ],
)
def test_other_tools_and_languages_are_named_as_outside(text: str) -> None:
    named = named_tools(text)
    assert named.outside and not named.libraries


@pytest.mark.parametrize(
    "text",
    [
        "make a chart",
        "plot it",
        "a graph please",
        "the x axis",
        "vitamin id3 levels",  # never inside a longer word
        "a pyecharts chart",  # pyecharts is its own library
        "let's plot this",  # the apostrophe makes it English, not lets-plot
        "a database report",
        "in matplotlib.js",  # a suffix the name does not include: another product, not the catalogue library
        "bokeh.js",
        "seaborn js",
        "ggplot2.jl",
        "",
    ],
)
def test_a_word_that_names_no_library_names_none(text: str) -> None:
    assert not named_tools(text).libraries
    assert resolve_library(text) is None


def test_the_longer_name_wins_where_two_start() -> None:
    assert named_tools("plotly.js") == NamedTools(frozenset(), True)  # the JavaScript library, not Plotly
    assert named_tools("Vega-Altair") == NamedTools(frozenset({"altair"}), False)  # Altair, not Vega
    assert named_tools("ggplot2") == NamedTools(frozenset({"ggplot2"}), False)
    assert named_tools("port the d3 plot to vega-lite") == NamedTools(frozenset({"d3"}), True)
    assert named_tools("d3 or chart.js?") == NamedTools(frozenset({"d3", "chartjs"}), False)


@pytest.mark.parametrize("name", ["Seaborn!", "d3 please", "chart", "plot", "mui x y", " "])
def test_only_a_name_as_a_whole_resolves(name: str) -> None:
    assert resolve_library(name) is None


def test_no_name_belongs_to_two_owners() -> None:
    """The table raises at import when one key has two owners; the outside names share none with the catalogue."""
    catalogue = {name_key(name) for library in SUPPORTED_LIBRARIES for name in (library, LIBRARY_NAMES[library])}
    catalogue |= {name_key(name) for names in LIBRARY_ALIASES.values() for name in names}
    assert not catalogue & {name_key(name) for name in OUTSIDE_TOOLS}


def test_the_width_and_case_of_a_name_are_ignored() -> None:
    assert resolve_library("Ｄ３．ｊｓ") == "d3"  # full-width forms, as a phone keyboard may send them
    assert name_key("D3.js") == name_key("d3 JS") == "d3js"


@pytest.mark.parametrize("form", ["chart  js", "lets   plot", "mui  x", "d3 . js"])
def test_any_run_of_separators_joins_a_names_parts(form: str) -> None:
    assert resolve_library(form) is not None and named_tools(f"in {form} please").libraries


def test_a_name_that_is_also_a_word_still_names_the_library() -> None:
    """The table reads names, not intent: "vitamin d3" names D3. Only the judge's `other_library` for such a message
    would be lifted (`scope_guard.served_library_request`), and a question about vitamin levels is not one."""
    assert named_tools("plot the vitamin d3 levels") == NamedTools(frozenset({"d3"}), False)
    assert named_tools("make the bars shiny") == NamedTools(frozenset(), False)  # Shiny only as R Shiny
    assert named_tools("an observable trend") == NamedTools(frozenset(), False)
    assert named_tools("as an R Shiny app") == NamedTools(frozenset(), True)
