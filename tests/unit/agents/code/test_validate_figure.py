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
    pytest.param(
        "import plotly.express as px\nm = px.optional_imports.get_module('os')\n",
        "banned-attribute",
        id="px get_module",
    ),
    pytest.param(
        "import plotly.figure_factory as ff\nm = ff.optional_imports.get_module('os')\n",
        "banned-attribute",
        id="ff get_module",
    ),
    pytest.param("from plotly.express import optional_imports\n", "banned-attribute", id="optional_imports by from"),
    pytest.param("from plotly.optional_imports import get_module\n", "banned-import", id="the module"),
    pytest.param("import plotly.express as px\nc = px._core\n", "banned-attribute", id="a private module"),
    pytest.param("fig0 = go.Figure()\nfig0._layout['width'] = '1'\n", "banned-attribute", id="the layout dict"),
    pytest.param("fig0 = go.Figure(layout={'width': 900}, _validate=False)\n", "banned-keyword", id="_validate"),
    pytest.param(
        "fig0 = go.Figure()\nfig0.write_html('x.html', post_script='alert(1)', include_plotlyjs='x.js')\n",
        "banned-attribute",
        id="write_html with script keywords",
    ),
    pytest.param('fig0 = go.Figure()\nfig0.plotly_relayout({"width": "1"})\n', "banned-attribute", id="relayout"),
    pytest.param("fig0 = go.Figure()\nfig0.plotly_update(layout={})\n", "banned-attribute", id="update"),
    pytest.param("fig0 = go.Figure()\nfig0.plotly_restyle({})\n", "banned-attribute", id="restyle"),
    pytest.param("fig0 = go.Figure()\nfig0._validate = False\n", "banned-attribute", id="a private attribute"),
    pytest.param("t = go.Scatter(x=[1], _validate=False)\n", "banned-keyword", id="a private keyword"),
    pytest.param("t = go.Scatter(**{'_validate': False})\n", "banned-keyword", id="a private key"),
    pytest.param(
        "import plotly.express as px\nf = px.scatter(df, trendline='rolling', trendline_options={'function': 'mean'})\n",
        "banned-keyword",
        id="trendline_options dispatches by name",
    ),
    pytest.param("t = go.Scattergeo(lat=[1], lon=[1])\n", "banned-attribute", id="a geo trace fetches its map"),
    pytest.param(
        "import plotly.express as px\nf = px.scatter_map(df, lat='a', lon='a')\n", "banned-attribute", id="tiles"
    ),
    pytest.param("fig0 = go.Figure()\nfig0.update_geos(visible=False)\n", "banned-attribute", id="update_geos"),
    pytest.param("fig0 = go.Figure()\nfig0.add_layout_image(source='logo.png')\n", "url-literal", id="image source"),
    pytest.param(
        "fig0 = go.Figure()\nfig0.update_layout(images=[dict(source='logo.png')])\n", "url-literal", id="images list"
    ),
    pytest.param("LOGO = 'logo.png'\nimg = go.layout.Image(source=LOGO)\n", "url-literal", id="source through a name"),
    pytest.param("t = go.Choropleth(geojson='counties.json')\n", "url-literal", id="a relative geojson URL"),
    pytest.param("u = '//cdn.example.org/x.png'\n", "url-literal", id="a protocol-relative URL"),
    # The review of PB-2a: anything but None where a URL goes, a built string and a flat update key included.
    pytest.param(
        "fig0 = go.Figure()\nfig0.add_layout_image(source=''.join(['lo', 'go.png']))\n", "url-literal", id="a join"
    ),
    pytest.param("fig0 = go.Figure()\nfig0.add_layout_image(source=str(THEME))\n", "url-literal", id="str()"),
    pytest.param(
        "m = [dict(buttons=[dict(method='relayout', args=[{'images[0].source': 'x.png'}])])]\n"
        "fig0 = go.Figure()\nfig0.update_layout(updatemenus=m)\n",
        "url-literal",
        id="a flat key in an update's args",
    ),
    pytest.param("fig0 = go.Figure()\nfig0.layout.images[0].source = 'x.png'\n", "url-literal", id="a store"),
]


@pytest.mark.parametrize(
    "body",
    [
        pytest.param("t = go.Choropleth(geojson={'type': 'FeatureCollection', 'features': []})\n", id="geojson dict"),
        pytest.param("img = go.layout.Image(source=None)\n", id="no source"),
        pytest.param("s = go.Sankey(link=dict(source=[0, 1], target=[1, 0], value=[1, 1]))\n", id="sankey data"),
    ],
)
def test_url_contexts_take_none_or_data(body: str) -> None:
    assert "url-literal" not in rules(plotly_plot(body), "plotly")


def test_plotly_data_named_source_passes() -> None:
    body = (
        "edges = pd.DataFrame([{'source': 'A', 'target': 'B'}])\n"
        "s = go.Sankey(link=dict(source=[0, 1], target=[1, 0], value=[1, 1]))\n"
    )
    assert validate_security(plotly_plot(body), library="plotly") == []


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
    pytest.param("from bokeh.models import Model\nm = Model.lookup('x')\n", "banned-attribute", id="lookup by name"),
    pytest.param("from bokeh.core.properties import Instance\n", "banned-import", id="Instance by string"),
    pytest.param(
        "from bokeh.models import GlyphRenderer\nt = GlyphRenderer.glyph.property\n", "banned-attribute", id="property"
    ),
    pytest.param("q = figure()\nd = q.descriptors()\n", "banned-attribute", id="descriptors"),
    pytest.param("q = figure()\nd = q.properties_with_refs()\n", "banned-attribute", id="properties_with_refs"),
    pytest.param("q = figure()\nd = q.dataspecs()\n", "banned-attribute", id="dataspecs"),
    pytest.param("q = figure()\nd = q.parameters()\n", "banned-attribute", id="parameters"),
    pytest.param(
        "q = figure()\nd = q.query_properties_with_values(lambda d: True)\n", "banned-attribute", id="query descriptors"
    ),
    pytest.param("q = figure()\nc = q.model_class_reverse_map['Div']\n", "banned-attribute", id="a class by name"),
    pytest.param("h = HoverTool()\nh.set_from_json('tooltips', 'x')\n", "banned-attribute", id="set_from_json"),
    pytest.param("q = figure()\nq.apply_theme({'width': 'x'})\n", "banned-attribute", id="apply_theme"),
    pytest.param("from bokeh.plotting import Document\n", "banned-attribute", id="Document re-export"),
    pytest.param("import bokeh.themes\n", "banned-import", id="Theme"),
    pytest.param("from bokeh.models import ImageURLTexture\n", "banned-attribute", id="ImageURLTexture"),
    pytest.param("from bokeh.models import Switch\ns = Switch(on_icon='x.svg')\n", "banned-keyword", id="on_icon"),
    pytest.param("from bokeh.models import Document\n", "banned-attribute", id="a document of its own"),
    pytest.param(
        "from bokeh.models import Toggle\nt = Toggle(icon='x.svg')\n", "banned-keyword", id="icon reads a file"
    ),
    pytest.param(
        "from bokeh.models import Toggle\nt = Toggle()\nt.on_icon = 'x.svg'\n", "banned-attribute", id="store"
    ),
    pytest.param("q = figure()\nq._property_values\n", "banned-attribute", id="a private attribute"),
    pytest.param("q = figure(url='tiles/{Z}.png')\n", "url-literal", id="a relative URL"),
    # The review of PB-2a: what reaches a property without a name the rules read, and CSS and MathJax's HTML.
    pytest.param(
        's = "<img src=x onerror=alert(1)>"\nh = HoverTool(**{"tool" + "tips": s})\n', "banned-keyword", id="a"
    ),
    pytest.param(
        'opts = {}\nopts["tooltips"] = "%cimg src=x onerror=alert(1)>" % 60\nh = HoverTool(**opts)\n',
        "banned-keyword",
        id="b",
    ),
    pytest.param('h = HoverTool()\nh.update(**{"tool" + "tips": chr(60) + "b>x"})\n', "banned-keyword", id="c"),
    pytest.param(
        "from bokeh.models import Button, SetValue\nh = HoverTool()\n"
        "b = Button(label='x', js_event_callbacks={'button_click': [SetValue(obj=h, attr='tooltips', value='x')]})\n",
        "banned-keyword",
        id="d js_event_callbacks",
    ),
    pytest.param("from bokeh.models import SetValue\n", "banned-attribute", id="d SetValue"),
    pytest.param("from bokeh.models import ToggleVisibility\n", "banned-attribute", id="ToggleVisibility"),
    pytest.param(
        "from bokeh.models import Slider\ns = Slider(start=0, end=1, value=0, step=1, js_property_callbacks={})\n",
        "banned-keyword",
        id="js_property_callbacks",
    ),
    pytest.param("o = {'js_event_callbacks': {}}\n", "banned-keyword", id="a banned keyword as a dict key"),
    pytest.param("q = figure()\nq.set_select(HoverTool, {'tooltips': 'x'})\n", "banned-attribute", id="set_select"),
    pytest.param("q = figure()\nq.clone(**dict(width=1))\n", "banned-keyword", id="clone of a built dict"),
    pytest.param("def f(**kw):\n    return figure(**kw)\n", "banned-keyword", id="a parameter unpacked"),
    pytest.param("from bokeh.models import InlineStyleSheet\n", "banned-attribute", id="InlineStyleSheet"),
    pytest.param("from bokeh.models import GlobalInlineStyleSheet\n", "banned-attribute", id="global stylesheet"),
    pytest.param("from bokeh.models import Styles\n", "banned-attribute", id="Styles"),
    pytest.param("q = figure(styles={'background': 'url(x)'})\n", "banned-keyword", id="styles"),
    pytest.param("q = figure()\nq.stylesheets = [':host{}']\n", "banned-attribute", id="stylesheets"),
    pytest.param("from bokeh.models import MathML\n", "banned-attribute", id="MathML"),
    pytest.param(
        "from bokeh.models import Label\nl = Label(x=1, y=1, text=r'$$\\href{javascript:alert(1)}{x}$$')\n",
        "banned-keyword",
        id="MathJax href",
    ),
]


@pytest.mark.parametrize(
    "body",
    [
        pytest.param(
            'BASE = {"text_font_size": "28pt", "text_color": PAGE_BG}\nBOLD = {**BASE, "text_font_style": "bold"}\n'
            "from bokeh.models import Label\nl = Label(x=1, y=1, text='a', **BOLD)\nm = Label(x=2, y=1, text='b', **BASE)\n",
            id="module dicts read only by ** (the catalogue's line-reaction-coordinate, spc-xbar-r)",
        ),
        pytest.param("q = figure(**{'width': 800})\n", id="a dict literal"),
    ],
)
def test_bokeh_unpacking_of_literal_options_passes(body: str) -> None:
    assert validate_security(bokeh_plot(body), library="bokeh") == []


@pytest.mark.parametrize(
    "body",
    [
        'BASE = {"text_color": PAGE_BG}\nBASE["text_font_size"] = "9pt"\nq = figure(**BASE)\n',
        'BASE = {"text_color": PAGE_BG}\nBASE.update(width=1)\nq = figure(**BASE)\n',
        "BASE = dict(width=1)\nq = figure(**BASE)\n",
        "BASE = {'width': 1}\nfor BASE in [{}]:\n    pass\nq = figure(**BASE)\n",
    ],
)
def test_bokeh_unpacking_of_a_changed_or_built_dict_is_refused(body: str) -> None:
    assert "banned-keyword" in rules(bokeh_plot(body), "bokeh")


def test_bokeh_the_figure_files_handle_is_named_by_the_save_alone() -> None:
    code = bokeh_plot() + "n = figure_file.name\n"
    assert "savefig-target" in rules(code, "bokeh")


@pytest.mark.parametrize(("body", "rule"), BOKEH_ROUTES)
def test_bokeh_routes_are_refused(body: str, rule: str) -> None:
    assert rule in rules(bokeh_plot(body), "bokeh")


class TestBokehTooltips:
    """BokehJS parses a template string and each pair's value as HTML; the profile reads every text either can take
    (owner decision of 2026-10-31: templates as the catalogue writes them, no `{safe}`)."""

    @pytest.mark.parametrize(
        "body",
        [
            pytest.param('TIPS = [("x", "@a{0.0}")]\nh = HoverTool(tooltips=TIPS)\n', id="pairs through a name"),
            pytest.param('h = HoverTool(tooltips=[("y", "@a"), ("n", "$index")])\n', id="pairs"),
            pytest.param('h = HoverTool(tooltips="<b>@a</b> &times; <i>@a{0.00}</i><br/>")\n', id="a template"),
            pytest.param(
                'INK = "#1A1A17" if THEME == "light" else "#F0EFE8"\nBG = INK\n'
                'h = HoverTool(tooltips=f"""<div style="color:{BG};padding:8px">'
                '<span class=\'k\'>@a</span></div>""")\n',
                id="an f-string over theme constants, as chord-basic writes it",
            ),
            pytest.param('UCL = 3.5\nh = HoverTool(tooltips=[("UCL", f"{UCL:.3f}")])\n', id="a formatted number"),
            pytest.param('h = HoverTool(tooltips=[(f"d < {2:.1f}", "@a")])\n', id="a label is text"),
            pytest.param('h = HoverTool(tooltips=[("cmp", "@a < 5 <= @a")])\n', id="a comparison is text"),
            pytest.param("h = HoverTool(tooltips=None)\n", id="no tooltips"),
        ],
    )
    def test_allowed(self, body: str) -> None:
        assert validate_security(bokeh_plot(body), library="bokeh") == []

    @pytest.mark.parametrize(
        ("body", "rule"),
        [
            pytest.param('h = HoverTool(tooltips=[("x", "@a{safe}")])\n', "banned-keyword", id="{safe}"),
            pytest.param('h = HoverTool(tooltips="<div>@a{ safe }</div>")\n', "banned-keyword", id="{ safe }"),
            pytest.param('F = "safe"\nh = HoverTool(tooltips=f"@a{{{F}}}")\n', "banned-keyword", id="{safe} by name"),
            pytest.param('h = HoverTool(tooltips="<img src=x onerror=alert(1)>")\n', "banned-keyword", id="img"),
            pytest.param('h = HoverTool(tooltips=[("x", "<img src=x>")])\n', "banned-keyword", id="img in a pair"),
            pytest.param('h = HoverTool(tooltips="<a href=\\"#\\">@a</a>")\n', "banned-keyword", id="a link"),
            pytest.param('h = HoverTool(tooltips="<b onclick=\\"x\\">@a</b>")\n', "banned-keyword", id="a handler"),
            pytest.param('h = HoverTool(tooltips="<b style=x>@a</b>")\n', "banned-keyword", id="unquoted"),
            pytest.param(
                'h = HoverTool(tooltips="<div style=\\"background:url(x.png)\\">@a</div>")\n',
                "banned-keyword",
                id="a CSS URL",
            ),
            pytest.param(
                'h = HoverTool(tooltips="<div style=\\"color:@a\\">x</div>")\n', "banned-keyword", id="a field in style"
            ),
            pytest.param(
                'h = HoverTool(tooltips="<div style=\\"u&#114;l(x)\\">x</div>")\n', "banned-keyword", id="an entity"
            ),
            pytest.param('h = HoverTool(tooltips="<b>@a</b" + ">")\n', "banned-keyword", id="a concatenation"),
            pytest.param('h = HoverTool(tooltips=f"<b>{THEME}</b>")\n', "banned-keyword", id="an unreadable value"),
            pytest.param(
                'for name in ["a"]:\n    h = HoverTool(tooltips=[("Server", name)])\n',
                "banned-keyword",
                id="a loop variable's text, as the catalogue's horizon-basic writes it",
            ),
            pytest.param('h = HoverTool(tooltips=[("x", f"{THEME:.3}")])\n', "banned-keyword", id="a text spec"),
            pytest.param('h = HoverTool(tooltips=[("x", f"{THEME!r}")])\n', "banned-keyword", id="a conversion"),
            pytest.param('h = HoverTool(tooltips=["@a"])\n', "banned-keyword", id="no pair"),
            pytest.param(
                'TIPS = [("x", "@a")]\nTIPS.append(("y", "<img src=x>"))\nh = HoverTool(tooltips=TIPS)\n',
                "banned-keyword",
                id="a list changed after its binding",
            ),
            pytest.param(
                'h = HoverTool(tooltips=[("x", "@a")])\nh.tooltips.append(("y", "@a"))\n',
                "banned-attribute",
                id="a tooltips list changed in place",
            ),
            pytest.param('h = HoverTool()\nh.tooltips = "<img src=x>"\n', "banned-keyword", id="a store"),
            pytest.param('h = HoverTool(**{"tooltips": "<img src=x>"})\n', "banned-keyword", id="an unpacked key"),
            pytest.param(
                'OPTS = {"tooltips": [("x", "<b>@a</b>")]}\nTIP = "<img src=x>"\n', "banned-keyword", id="a piece"
            ),
            pytest.param('OPEN = "<"\n', "banned-keyword", id="a lone opening bracket"),
        ],
    )
    def test_refused(self, body: str, rule: str) -> None:
        assert rule in rules(bokeh_plot(body), "bokeh")

    def test_a_refused_template_is_one_finding(self) -> None:
        found = validate_security(bokeh_plot('h = HoverTool(tooltips="<img src=x>")\n'), library="bokeh")
        assert [finding.rule for finding in found] == ["banned-keyword"]
        assert "<img" not in found[0].message


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
