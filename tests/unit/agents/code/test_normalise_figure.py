"""The normaliser's plotly and bokeh steps (PB-2a, 2026-10-31): the figure save, plotly express's render mode, the
screenshot block that goes, and `.format` as an f-string (`agents/anyplot/code/normalise.py`, step 7)."""

import ast

import pytest

from agents.anyplot.code.figure import figure_saves
from agents.anyplot.code.normalise import measure_canvas, normalise, normalise_report
from agents.anyplot.code.readiness import scan

from .conftest import REPO_ROOT, source


PLOTLY = source("""
    import os

    import kaleido
    import plotly.graph_objects as go
    import plotly.express as px

    THEME = os.getenv("ANYPLOT_THEME", "light")
    W, H = 1600, 900
    fig = px.scatter(x=[1, 2], y=[3, 4])
    fig.add_trace(go.Scatter(x=[1], y=[2]))
    fig.show()

    # Save
    fig.write_image(f"plot-{THEME}.png", width=W, height=H, scale=3)
    fig.update_xaxes(rangeslider={"visible": True})
    fig.write_html(
        f"plot-{THEME}.html",
        include_plotlyjs="cdn",
    )
""")


def test_plotlys_save_block_becomes_the_figure_save() -> None:
    report = normalise_report(PLOTLY, library="plotly")

    assert report.code == source("""
        import os

        import plotly.graph_objects as go
        import plotly.express as px

        THEME = os.getenv("ANYPLOT_THEME", "light")
        W, H = 1600, 900
        fig = px.scatter(x=[1, 2], y=[3, 4], render_mode="svg")
        fig.add_trace(go.Scatter(x=[1], y=[2]))

        # Save
        fig.update_layout(width=1600, height=900).write_json(f"plot-{THEME}.json")
    """)
    assert report.notes == ()
    assert normalise(report.code, library="plotly") == report.code


@pytest.mark.parametrize(
    ("save", "size", "note"),
    [
        ('fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)', (800, 450), False),
        ('fig.write_image(os.path.join(d, f"plot-{THEME}.png"), width=600, height=600, scale=4)', (600, 600), False),
        ('fig.write_image(f"plot-{THEME}.png", width=w, height=450)', None, True),
        ('fig.write_image(f"plot-{THEME}.png", "png", 4, 800, 450)', None, True),
        ('fig.write_image(f"plot-{THEME}.png", width=100, height=450)', None, True),
    ],
)
def test_plotlys_size_moves_into_the_figure_when_the_normaliser_can_read_it(
    save: str, size: tuple[int, int] | None, note: bool
) -> None:
    code = f'import os\n\nimport plotly.graph_objects as go\n\nTHEME = os.getenv("ANYPLOT_THEME", "light")\nfig = go.Figure()\n{save}\n'
    report = normalise_report(code, library="plotly")
    saves = figure_saves(ast.parse(report.code), "plotly")

    assert len(saves) == 1 and saves[0][1].size == size
    assert any(text.startswith("figure save:") for text in report.notes) is note


def test_plotly_keeps_a_single_theme_save_for_the_readiness_scan() -> None:
    code = (
        'import plotly.graph_objects as go\n\nfig = go.Figure()\nfig.write_image("plot.png", width=800, height=450)\n'
    )
    report = normalise_report(code, library="plotly")

    assert report.code == code and "figure save: no module-level write_image" in report.notes[0]


def test_plotly_express_keeps_a_render_mode_it_names() -> None:
    code = 'import plotly.express as px\nfrom plotly.express import line as ln\n\na = px.scatter(render_mode="webgl")\nb = ln(x=[1])\nc = px.bar(x=[1])\n'
    result = normalise(code, library="plotly")

    assert 'a = px.scatter(render_mode="webgl")' in result
    assert 'b = ln(x=[1], render_mode="svg")' in result and "c = px.bar(x=[1])\n" in result


BOKEH_SELENIUM = source("""
    import io
    import os
    import sys
    import time
    from pathlib import Path

    from bokeh.io import output_file, save
    from bokeh.plotting import figure
    from PIL import Image
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    THEME = os.getenv("ANYPLOT_THEME", "light")
    html_path = Path(f"plot-{THEME}.html")
    color = "#{:02X}{:02X}{:02X}".format(0, 158, 115)
    p = figure(width=4800, height=2700)
    p.line([1, 2], [3, 4], color=color)

    # Save interactive HTML
    output_file(html_path)
    save(p)

    # Screenshot with headless Chrome
    W, H = 3200, 1800
    opts = Options()
    for arg in ("--headless=new", f"--window-size={W},{H}"):
        opts.add_argument(arg)
    driver = webdriver.Chrome(options=opts)
    driver.get(f"file://{html_path.resolve()}")
    time.sleep(3)
    raw = driver.get_screenshot_as_png()
    driver.quit()
    Image.open(io.BytesIO(raw)).crop((0, 0, W, H)).save(f"plot-{THEME}.png")
""")


def test_bokehs_screenshot_block_becomes_the_figure_save() -> None:
    report = normalise_report(BOKEH_SELENIUM, library="bokeh")

    assert report.code == source("""
        import json
        import os

        from bokeh.embed import json_item
        from bokeh.plotting import figure

        THEME = os.getenv("ANYPLOT_THEME", "light")
        color = f"#{0:02X}{158:02X}{115:02X}"
        p = figure(width=4800, height=2700)
        p.line([1, 2], [3, 4], color=color)

        with open(f"plot-{THEME}.json", "w", encoding="utf-8") as figure_file:
            json.dump(json_item(p), figure_file)
    """)
    assert normalise(report.code, library="bokeh") == report.code


def test_bokehs_export_png_form_and_its_alias_form() -> None:
    exported = source("""
        import os

        import bokeh.io
        import bokeh.plotting

        figure = bokeh.plotting.figure
        export_png = bokeh.io.export_png
        THEME = os.getenv("ANYPLOT_THEME", "light")
        layout = figure(width=3200, height=1800)
        export_png(layout, filename=f"plot-{THEME}.png")
        bokeh.io.output_file(f"plot-{THEME}.html")
        bokeh.io.save(layout)
    """)
    result = normalise(exported, library="bokeh")

    assert "export_png" not in result and "bokeh.io" not in result and "import bokeh.plotting\n" in result
    assert result.endswith("    json.dump(json_item(layout), figure_file)\n")


def test_a_bokeh_save_of_no_named_plot_stays_with_a_note() -> None:
    code = "from bokeh.io import save\nfrom bokeh.layouts import column\n\nsave(column())\n"
    report = normalise_report(code, library="bokeh")

    assert report.code == code and "saves no named plot" in report.notes[0]


@pytest.mark.parametrize(
    ("call", "expected"),
    [
        ('"{} and {}".format(a, b)', 'f"{a} and {b}"'),
        ('"{1}-{0}".format(a, b)', 'f"{b}-{a}"'),
        ('"{:.1f}".format(x + 1)', 'f"{(x + 1):.1f}"'),
        ('"{!r}".format(a)', 'f"{a!r}"'),
        ('"{{literal}} {}".format(a)', 'f"{{literal}} {a}"'),
        ('"a\\n{}\\"".format(a)', 'f"a\\n{a}\\""'),
    ],
)
def test_format_becomes_the_f_string_it_stands_for(call: str, expected: str) -> None:
    code = f"a, b, x = 1, 2, 3.0\ns = {call}\n"
    result = normalise(code, library="plotly")

    assert result == f"a, b, x = 1, 2, 3.0\ns = {expected}\n"
    namespace: dict[str, object] = {}
    exec(code, namespace)  # noqa: S102 - the test compares the two forms' values
    before = namespace["s"]
    exec(result, namespace)  # noqa: S102
    assert namespace["s"] == before


@pytest.mark.parametrize(
    "call",
    ['"{}{}".format(*rgb)', '"{0.real}".format(a)', '"{}".format(a, b)', '"{x}".format(x=1)', '"{} {0}".format(a, b)'],
)
def test_a_format_call_the_rule_cannot_read_stays(call: str) -> None:
    code = f"s = {call}\n"
    report = normalise_report(code, library="bokeh")

    assert report.code == code and any(note.startswith("str.format:") for note in report.notes)


def test_the_other_libraries_keep_their_format_calls() -> None:
    code = 's = "{}".format(1)\n'
    assert normalise(code, library="matplotlib") == code


@pytest.mark.parametrize("library", ["plotly", "bokeh"])
def test_the_figure_mode_draws_every_canvas(library: str) -> None:
    canvas = measure_canvas("x = 1\n", library=library)
    assert canvas.on_target and canvas.pixels is None


@pytest.mark.parametrize("library", ["plotly", "bokeh"])
def test_the_normalised_catalogue_ends_on_the_figure_save(library: str) -> None:
    """Measured on 2026-10-31: 318 of 325 plotly files (7 save a single-theme `"plot.png"`) and 321 of 325 bokeh files
    (4 save no named plot at module level) end on the pinned save; every file normalises idempotently."""
    paths = sorted(REPO_ROOT.glob(f"plots/*/implementations/python/{library}.py"))
    ending = 0
    for path in paths:
        result = normalise(path.read_text(encoding="utf-8"), library=library)
        tree = ast.parse(result)
        saves = figure_saves(tree, library)  # type: ignore[arg-type]
        if saves:
            ending += saves[-1][0] is tree.body[-1]
        assert normalise(result, library=library) == result, path
    assert len(paths) == 325 and ending == (318 if library == "plotly" else 321)


class TestReadiness:
    HEAD = 'import os\n\nimport plotly.graph_objects as go\n\nTHEME = os.getenv("ANYPLOT_THEME", "light")\n'
    SAVE = 'fig.update_layout(width=800, height=450).write_json(f"plot-{THEME}.json")\n'

    @pytest.mark.parametrize(
        ("body", "name", "line"),
        [
            ("fig = go.Figure(go.Scatter3d(x=[1], y=[1], z=[1]))\n", "Scatter3d", 6),
            ("fig = go.Figure()\nfig.add_scattergl(x=[1], y=[1])\n", "Scattergl", 7),
            ('fig = go.Figure(data=[{"type": "surface", "z": [[1]]}])\n', "Surface", 6),
            ("import plotly.express as px\nfig = px.scatter_3d(x=[1], y=[1], z=[1])\n", "scatter_3d", 7),
            (
                'import plotly.express as px\nfig = px.scatter(x=[1], y=[1], render_mode="webgl")\n',
                'render_mode="webgl"',
                7,
            ),
        ],
    )
    def test_a_webgl_trace_blocks_with_its_own_reason(self, body: str, name: str, line: int) -> None:
        result = scan(self.HEAD + body + self.SAVE, spec_id="s", library="plotly", enabled_libraries=["plotly"])

        assert result.status == "blocked"
        assert [reason for reason in result.reasons if reason.startswith("webgl:")] == [
            f"webgl: {name} at line {line} draws with WebGL, which the renderer's browser does not have"
        ]

    def test_plotly_literals_that_fit_only_the_catalogue_couple(self) -> None:
        body = (
            'fig = go.Figure(go.Scatter(x=[1], y=[1]))\nfig.update_layout(xaxis={"range": [0, 11], "dtick": 2})\n'
            "fig.update_yaxes(range=[35, 105])\nfig.add_hline(y=50)\nfig.add_vline(x=0)\n"
        )
        result = scan(self.HEAD + body + self.SAVE, spec_id="s", library="plotly", enabled_libraries=["plotly"])

        assert result.status == "coupled" and result.reasons == ["limits: 2 lines", "annotations: 1 line"]

    def test_bokeh_literals_that_fit_only_the_catalogue_couple(self) -> None:
        code = source("""
            import json
            import os

            from bokeh.embed import json_item
            from bokeh.models import Label, LinearColorMapper, Span
            from bokeh.plotting import figure

            THEME = os.getenv("ANYPLOT_THEME", "light")
            p = figure(width=4800, height=2700, x_range=(0, 10.5))
            p.y_range.end = 104
            p.y_range.start = 0
            p.add_layout(Span(location=50, dimension="width"))
            p.add_layout(Label(x=2, y=3, text="peak"))
            mapper = LinearColorMapper(palette=["#009E73"], low=0, high=100)
            with open(f"plot-{THEME}.json", "w", encoding="utf-8") as figure_file:
                json.dump(json_item(p), figure_file)
        """)
        result = scan(code, spec_id="s", library="bokeh", enabled_libraries=["bokeh"])

        assert result.status == "coupled"
        assert result.reasons == ["limits: 2 lines", "color-scale: 1 line", "annotations: 2 lines"]
