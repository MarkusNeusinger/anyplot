"""The SECURITY profiles of plotly and bokeh (PB-2a, 2026-10-31): their import surfaces, their bans and the pinned
figure save that `_lift_figure_save` takes out of the scan (`agents/anyplot/code/validate.py`, `code/figure.py`)."""

import pytest

from agents.anyplot.code.validate import validate_adaptation, validate_security

from .test_validate import BOKEH_HEADER, PLOTLY_FOOTER, PLOTLY_HEADER, bokeh_plot, plotly_plot


def findings(code: str, library: str) -> list[tuple[str, int | None]]:
    return [(finding.rule, finding.line) for finding in validate_security(code, library=library)]


def rules(code: str, library: str) -> set[str]:
    return {finding.rule for finding in validate_security(code, library=library)}


@pytest.mark.parametrize(("library", "build"), [("plotly", plotly_plot), ("bokeh", bokeh_plot)])
def test_the_minimal_files_pass_both_profiles(library: str, build) -> None:
    assert validate_security(build(), library=library) == []
    working = build().replace('df = pd.DataFrame({"a": [1, 2, 3]})', "df = load_user_data()")
    assert validate_adaptation(working, original_palette=[]) == []


PLOTLY_ROUTES = [
    pytest.param('fig0 = go.Figure()\nfig0.write_image(f"plot-{THEME}.png")\n', "banned-attribute", id="write_image"),
    pytest.param('go.Figure().write_html(f"plot-{THEME}.html")\n', "banned-attribute", id="write_html"),
    pytest.param("go.Figure().show()\n", "banned-attribute", id="show"),
    pytest.param("png = go.Figure().to_image()\n", "banned-attribute", id="to_image (kaleido)"),
    pytest.param("text = go.Figure().to_html()\n", "banned-call", id="to_html"),
    pytest.param("text = go.Figure().to_json()\n", "banned-call", id="to_json"),
    pytest.param('go.Figure().write_json("x.json")\n', "banned-call", id="write_json elsewhere"),
    pytest.param("full = go.Figure().full_figure_for_development()\n", "banned-attribute", id="kaleido's full figure"),
    pytest.param("w = go.FigureWidget()\n", "banned-attribute", id="the widget"),
    pytest.param("import plotly.io as pio\n", "banned-import", id="plotly.io"),
    pytest.param("import plotly.offline\n", "banned-import", id="plotly.offline"),
    pytest.param("import plotly\n", "banned-import", id="the package root"),
    pytest.param("import plotly.colors\nt = plotly.io.templates\n", "banned-attribute", id="io through colors"),
    pytest.param("import plotly.express as px\niris = px.data.iris()\n", "banned-attribute", id="px.data"),
    pytest.param("from plotly.express.data import iris\n", "banned-import", id="px.data by from-import"),
    pytest.param("import plotly.express as px\npx.set_mapbox_access_token('t')\n", "banned-attribute", id="token"),
    pytest.param(
        "import plotly.figure_factory as ff\nm = ff.create_county_choropleth(fips=[1], values=[1])\n",
        "banned-attribute",
        id="county choropleth reads shapefiles",
    ),
]


@pytest.mark.parametrize(("body", "rule"), PLOTLY_ROUTES)
def test_plotly_routes_are_refused(body: str, rule: str) -> None:
    assert rule in rules(plotly_plot(body), "plotly")


BOKEH_ROUTES = [
    pytest.param("from bokeh.models import CustomJS\n", "banned-attribute", id="CustomJS import"),
    pytest.param(
        "import bokeh.models\nf = bokeh.models.CustomJSTickFormatter(code='')\n", "banned-attribute", id="formatter"
    ),
    pytest.param("from bokeh.models import CustomJSHover\n", "banned-attribute", id="CustomJSHover"),
    pytest.param("from bokeh.models.callbacks import SetValue\n", "banned-import", id="callbacks module"),
    pytest.param("q = figure()\nq.js_on_event('tap', None)\n", "banned-attribute", id="js_on_event"),
    pytest.param("q = figure()\nq.x_range.js_link('start', q.y_range, 'start')\n", "banned-attribute", id="js_link"),
    pytest.param("from bokeh.models import Div\n", "banned-attribute", id="Div"),
    pytest.param("from bokeh.models import HTMLLabel\n", "banned-attribute", id="HTMLLabel"),
    pytest.param("from bokeh.models import SVGIcon\n", "banned-attribute", id="SVGIcon's raw SVG"),
    pytest.param("from bokeh.plotting import GMap\n", "banned-attribute", id="GMap"),
    pytest.param("from bokeh.models.dom import HTML\n", "banned-import", id="dom module"),
    pytest.param("q = figure()\nq.image_url(url=['a.png'], x=0, y=0)\n", "banned-attribute", id="image_url"),
    pytest.param("from bokeh.models import WMTSTileSource\n", "banned-attribute", id="tile source"),
    pytest.param("q = figure()\nq.add_tile('OSM')\n", "banned-attribute", id="add_tile"),
    pytest.param("from bokeh.models import AjaxDataSource\n", "banned-attribute", id="AjaxDataSource"),
    pytest.param("from bokeh.models import ImportedStyleSheet\n", "banned-attribute", id="imported stylesheet"),
    pytest.param("from bokeh.plotting import gmap\n", "banned-attribute", id="gmap"),
    pytest.param("from bokeh.plotting.gmap import gmap\n", "banned-import", id="gmap module"),
    pytest.param("from bokeh.plotting import output_file\n", "banned-attribute", id="output_file re-export"),
    pytest.param("from bokeh.plotting import curdoc\n", "banned-attribute", id="curdoc re-export"),
    pytest.param("from bokeh.plotting import save\n", "banned-call", id="save re-export"),
    pytest.param("from bokeh.plotting import show\n", "banned-attribute", id="show re-export"),
    pytest.param("import bokeh.io\n", "banned-import", id="bokeh.io"),
    pytest.param("from bokeh.embed import file_html\n", "banned-import", id="file_html"),
    pytest.param("import bokeh.sampledata\n", "banned-import", id="sampledata"),
    pytest.param("import bokeh.util.compiler\n", "banned-import", id="compiler (Node)"),
    pytest.param("import bokeh.themes\n", "banned-import", id="themes read files"),
    pytest.param('h = HoverTool(tooltips="<b>@a</b>")\n', "banned-keyword", id="an HTML tooltip template"),
    pytest.param(
        'TIPS = "<img src=x onerror=alert(1)>"\nh = HoverTool(tooltips=TIPS)\n',
        "banned-keyword",
        id="an HTML tooltip template through a name",
    ),
    pytest.param('h = HoverTool()\nh.tooltips = f"<i>{THEME}</i>"\n', "banned-keyword", id="a tooltips store"),
]


@pytest.mark.parametrize(("body", "rule"), BOKEH_ROUTES)
def test_bokeh_routes_are_refused(body: str, rule: str) -> None:
    assert rule in rules(bokeh_plot(body), "bokeh")


def test_bokeh_tooltip_pairs_pass() -> None:
    body = 'TIPS = [("x", "@a{0.0}")]\nh = HoverTool(tooltips=TIPS)\nh2 = HoverTool(tooltips=[("y", "@a")])\n'
    assert validate_security(bokeh_plot(body), library="bokeh") == []


class TestTheFigureSave:
    """The pinned statement is lifted out of the scan in exactly its shape; everything around it is checked."""

    @pytest.mark.parametrize(("header", "library"), [(PLOTLY_HEADER, "plotly"), (BOKEH_HEADER, "bokeh")])
    def test_a_file_without_it_is_a_finding(self, header: str, library: str) -> None:
        code = header.replace("import json\n", "").replace("from bokeh.embed import json_item\n", "")
        found = validate_security(code, library=library)

        assert [(finding.rule, finding.line) for finding in found] == [("savefig-target", None)]
        assert found[0].message.startswith("no save of the figure found: end with ")

    def test_a_second_save_is_a_finding(self) -> None:
        code = plotly_plot() + 'fig.write_json(f"plot-{THEME}.json")\n'
        assert findings(code, "plotly") == [("savefig-target", code.count("\n"))]

    def test_a_save_inside_a_block_is_scanned_and_refused(self) -> None:
        save = 'fig.update_layout(width=800, height=450).write_json(f"plot-{THEME}.json")\n'
        code = plotly_plot().replace(save, "if True:\n    " + save)
        assert {"savefig-target", "banned-call"} <= rules(code, "plotly")

    @pytest.mark.parametrize(
        "save",
        [
            'fig.update_layout(width=800, height=450).write_json(f"plot-{THEME}.json", pretty=True)\n',
            'fig.update_layout(width=800, height=450).write_json("plot.json")\n',
            'fig.update_layout(width=99999, height=450).write_json(f"plot-{THEME}.json")\n',
        ],
    )
    def test_a_save_of_another_shape_is_scanned_and_refused(self, save: str) -> None:
        code = PLOTLY_HEADER + PLOTLY_FOOTER.replace(
            'fig.update_layout(width=800, height=450).write_json(f"plot-{THEME}.json")\n', save
        )
        assert {"savefig-target", "banned-call"} <= rules(code, "plotly")

    @pytest.mark.parametrize("library", ["plotly", "bokeh"])
    def test_the_plot_is_never_an_imported_name(self, library: str) -> None:
        code = plotly_plot() if library == "plotly" else bokeh_plot()
        code = code.replace("fig.update_layout(width", "pd.update_layout(width").replace(
            "json_item(p)", "json_item(pd)"
        )
        assert "module-value" in rules(code, library)

    def test_json_read_elsewhere_keeps_its_import_in_the_scan(self) -> None:
        code = bokeh_plot('labels = json.loads("[]")\n')
        assert "banned-import" in rules(code, "bokeh")

    @pytest.mark.parametrize(
        "body",
        [
            "json = pd\n",
            "def open(path, mode, encoding):\n    return path\n",
            "from bokeh.models import ColumnDataSource as json_item\n",
            "open = print\n",
        ],
    )
    def test_the_names_the_save_reads_are_bound_only_by_their_imports(self, body: str) -> None:
        assert "savefig-target" in rules(bokeh_plot(body), "bokeh")

    def test_an_aliased_json_import_is_no_lift(self) -> None:
        code = bokeh_plot().replace("import json\n", "import json as js\nimport json\n")
        assert "banned-import" in rules(code, "bokeh")

    def test_open_and_dump_elsewhere_stay_refused(self) -> None:
        body = 'with open(f"plot-{THEME}.json", "w", encoding="utf-8") as f:\n    f.write("x")\n'
        assert {"banned-name"} <= rules(bokeh_plot(body), "bokeh")
        assert "banned-attribute" in rules(bokeh_plot("import numpy as np\nnp.zeros(1).dump('x')\n"), "bokeh")

    def test_the_lift_changes_no_line_number(self) -> None:
        code = bokeh_plot("import subprocess\n")
        assert ("banned-import", BOKEH_HEADER.count("\n") + 1) in findings(code, "bokeh")
