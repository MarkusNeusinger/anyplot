"""The JavaScript render harness's figure mode (`automation/js-render/render.mjs --library=<plotly|bokeh>
--figure=<file>`, PB-1 of step 4 in agentic/specs/261024-agent-all-libraries.md), run through Node and Chromium, and
the whole two-step render through the Python harness.

Each case draws a figure with the package's own bundled JavaScript, taken from the installed Python package as the
renderer takes it, so the module runs where Node, the lock's packages, Playwright's browser and plotly or bokeh are
present and is skipped elsewhere; the renderer image's CI step (`ci-image.yml`) renders through the built image. The
harness is copied into a checkout's layout, as in `test_js_render_sandbox.py`.
"""

import importlib.util
import json
import os
import re
import shutil
import struct
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from agents.anyplot.render import harness as python_harness
from agents.anyplot.render.runtimes.python import HARNESS_SOURCE


REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS = REPO_ROOT / "automation" / "js-render" / "render.mjs"
SANDBOX_ENV = {"ANYPLOT_SANDBOX": "1", "ANYPLOT_NO_HTML": "1"}
ERROR_LINE = re.compile(
    r"^render: error: (page|import|build|draw|crash|data|timeout|harness|figure) ([A-Za-z_$][\w$]*) (\S+:\d+|-): (.*)$"
)
"""The final error line's grammar, with figure mode's `figure` kind."""
BAR = {"data": [{"type": "bar", "x": ["a", "b", "c"], "y": [3, 1, 2]}], "layout": {"title": {"text": "bars"}}}


def package_dir(name: str) -> Path | None:
    spec = importlib.util.find_spec(name)
    return Path(next(iter(spec.submodule_search_locations))) if spec and spec.submodule_search_locations else None


def plotly_figure(width: float | None = None, height: float | None = None, **layout: object) -> dict[str, object]:
    figure = json.loads(json.dumps(BAR))
    if width is not None:
        figure["layout"]["width"] = width
    if height is not None:
        figure["layout"]["height"] = height
    figure["layout"].update(layout)
    return figure


@dataclass
class Run:
    returncode: int
    stdout: str
    stderr: str
    work: Path

    @property
    def last_line(self) -> str:
        lines = self.stderr.strip().splitlines()
        return lines[-1] if lines else ""

    def png_size(self, theme: str = "light") -> tuple[int, int]:
        png = (self.work / f"plot-{theme}.png").read_bytes()
        assert png[:8] == b"\x89PNG\r\n\x1a\n"
        return struct.unpack(">II", png[16:24])


@dataclass
class Harness:
    root: Path
    node: str

    @property
    def render_mjs(self) -> Path:
        return self.root / "automation" / "js-render" / "render.mjs"

    def environment(self, extra: dict[str, str] | None = None, *, sandbox: bool = True) -> dict[str, str]:
        environment = {key: value for key, value in os.environ.items() if not key.startswith("ANYPLOT_")}
        environment |= {"ANYPLOT_THEME": "light", "ANYPLOT_NODE_MODULES": str(self.root / "node_modules")}
        if sandbox:
            environment |= SANDBOX_ENV
        return environment | (extra or {})

    def draw(
        self,
        tmp_path: Path,
        figure: object,
        *,
        library: str = "plotly",
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        sandbox: bool = True,
        package: bool = True,
    ) -> Run:
        work = tmp_path / "work"
        work.mkdir(parents=True, exist_ok=True)
        if figure is not None:
            text = figure if isinstance(figure, str) else json.dumps(figure)
            (work / "plot-light.json").write_text(text, encoding="utf-8")
        extra = dict(env or {})
        found = package_dir(library) if library in ("plotly", "bokeh") else None
        if package and found is not None:
            extra["ANYPLOT_FIGURE_PACKAGE"] = str(found)
        argv = args if args is not None else [f"--library={library}", "--figure=plot-light.json"]
        done = subprocess.run(
            [self.node, str(self.render_mjs), *argv],
            cwd=work,
            env=self.environment(extra, sandbox=sandbox),
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        return Run(done.returncode, done.stdout, done.stderr, work)


def _node_modules() -> Path | None:
    root = Path(os.environ.get("ANYPLOT_NODE_MODULES", REPO_ROOT / "node_modules"))
    return root if (root / "playwright" / "package.json").is_file() else None


@pytest.fixture(scope="module")
def harness(tmp_path_factory: pytest.TempPathFactory) -> Harness:
    node = shutil.which("node")
    modules = _node_modules()
    if node is None or modules is None:
        pytest.skip("needs node on PATH and the lock's node_modules (npm ci, or ANYPLOT_NODE_MODULES)")
    if package_dir("plotly") is None:
        pytest.skip("needs plotly, whose bundled plotly.js draws the figures (the lib-plotly extra)")
    root = tmp_path_factory.mktemp("checkout")
    (root / "automation" / "js-render").mkdir(parents=True)
    shutil.copy(HARNESS, root / "automation" / "js-render" / "render.mjs")
    (root / "node_modules").symlink_to(modules.resolve(), target_is_directory=True)
    probe = Harness(root, node).draw(tmp_path_factory.mktemp("probe"), plotly_figure(800, 450))
    if probe.returncode != 0:
        pytest.skip(f"the harness cannot render here (no browser?): {probe.stderr.strip()[-300:]}")
    return Harness(root, node)


def bokeh_or_skip():
    if package_dir("bokeh") is None:
        pytest.skip("needs bokeh, whose bundled BokehJS draws the figures (the lib-bokeh extra)")
    import bokeh.embed
    import bokeh.layouts
    import bokeh.models
    import bokeh.plotting

    return bokeh


def bokeh_item(width: int, height: int, **kwargs: object) -> dict[str, object]:
    bokeh = bokeh_or_skip()
    plot = bokeh.plotting.figure(width=width, height=height, toolbar_location=None, **kwargs)
    plot.line([1, 2, 3], [3, 1, 2], line_width=4)
    return bokeh.embed.json_item(plot)


def assert_final_line(run: Run, kind: str, cls: str) -> str:
    assert run.returncode != 0, run.stderr
    match = ERROR_LINE.match(run.last_line)
    assert match is not None, run.stderr
    assert (match.group(1), match.group(2), match.group(3)) == (kind, cls, "-"), run.last_line
    return match.group(4)


class TestTheCanvas:
    @pytest.mark.parametrize(
        ("size", "pixels", "scale"),
        [
            ((800, 450), (3200, 1800), "4.000"),
            ((1600, 900), (3200, 1800), "2.000"),
            ((600, 600), (2400, 2400), "4.000"),
            ((1200, 1200), (2400, 2400), "2.000"),
            ((3600, 3600), (2400, 2400), "0.667"),
            ((1000, 700), (3200, 1800), "2.564"),
            ((700, 1000), (2400, 2400), "2.400"),
            ((None, None), (3200, 1800), "2.000"),
            ((1200, None), (3200, 1800), "2.667"),
            ((None, 600), (3200, 1800), "2.985"),
        ],
        ids=["800x450", "1600x900", "600x600", "1200x1200", "3600x3600", "wide", "tall", "no size", "width", "height"],
    )
    def test_a_plotly_figure_keeps_its_size_and_the_scale_makes_the_canvas(
        self, harness: Harness, tmp_path: Path, size: tuple, pixels: tuple[int, int], scale: str
    ) -> None:
        """The catalogue writes plotly at 800x450 scale 4 (146 files), 1600x900 scale 3 (116), 600x600 scale 4 (43)
        and 1200x1200 scale 3 (9): the layout stays, the scale follows the canvas."""
        run = harness.draw(tmp_path, plotly_figure(*size))

        assert run.returncode == 0, run.stderr
        assert run.png_size() == pixels
        assert f"at scale {scale}" in run.stdout
        assert not (run.work / "plot-light.html").exists()

    @pytest.mark.parametrize(
        ("size", "drawn"), [((1200, None), "1200x675"), ((None, 450), "800x450")], ids=["width", "height"]
    )
    def test_a_plotly_figure_with_one_side_keeps_it_and_gets_the_other_at_16_to_9(
        self, harness: Harness, tmp_path: Path, size: tuple, drawn: str
    ) -> None:
        """The side the code named is drawn, not replaced by 1600 x 900; the other follows the landscape aspect."""
        run = harness.draw(tmp_path, plotly_figure(*size))

        assert run.returncode == 0, run.stderr
        assert f"figure {drawn} at scale" in run.stdout

    def test_a_bokeh_figure_at_the_catalogues_4800_wide_draws_at_two_thirds(
        self, harness: Harness, tmp_path: Path
    ) -> None:
        run = harness.draw(tmp_path, bokeh_item(4800, 2700), library="bokeh")

        assert run.returncode == 0, run.stderr
        assert run.png_size() == (3200, 1800) and "figure 4800x2700 at scale 0.667" in run.stdout

    def test_a_bokeh_layout_is_measured_first(self, harness: Harness, tmp_path: Path) -> None:
        bokeh = bokeh_or_skip()
        plots = []
        for _ in range(2):
            plot = bokeh.plotting.figure(width=800, height=450, toolbar_location=None)
            plot.line([1, 2], [3, 4])
            plots.append(plot)
        run = harness.draw(tmp_path, bokeh.embed.json_item(bokeh.layouts.row(*plots)), library="bokeh")

        assert run.returncode == 0, run.stderr
        assert run.png_size() == (3200, 1800) and "figure 1600x450 at scale 2.000" in run.stdout

    def test_the_dark_theme_draws_too(self, harness: Harness, tmp_path: Path) -> None:
        run = harness.draw(tmp_path, plotly_figure(800, 450), env={"ANYPLOT_THEME": "dark"}, args=None)
        assert run.returncode == 0, run.stderr
        assert run.png_size("dark") == (3200, 1800)


class TestTheFigureIsData:
    def test_markup_in_a_text_stays_text(self, harness: Harness, tmp_path: Path) -> None:
        """A title that would close the JSON element and open a script draws as text and runs nothing."""
        title = "</script><script>fetch('http://127.0.0.1:9/title')</script><!--"
        run = harness.draw(tmp_path, plotly_figure(800, 450, title={"text": title}))

        assert run.returncode == 0, run.stderr
        assert "refused" not in run.stderr and "console error" not in run.stderr

    def test_an_event_handler_in_bokehs_markup_never_runs(self, harness: Harness, tmp_path: Path) -> None:
        """Sandbox mode's policy allows inline handlers; a figure page's admits scripts by its nonce alone. The handler
        would log a marker it builds at run time, so the source text the violation may quote never holds it; the
        assertions read what ran and which directive refused it, not Chromium's wording, which changes between
        versions ("Refused to execute inline event handler ..." locally, "Executing inline event handler violates
        ..." in CI)."""
        bokeh = bokeh_or_skip()
        plot = bokeh.plotting.figure(width=800, height=450, toolbar_location=None)
        plot.line([1, 2], [3, 4])
        handler = "console.error('handler' + '-ran'); fetch('http://127.0.0.1:9/div')"
        div = bokeh.models.Div(text=f'<img src=x onerror="{handler}"><b>bold</b>')
        run = harness.draw(tmp_path, bokeh.embed.json_item(bokeh.layouts.column(div, plot)), library="bokeh")

        assert run.returncode == 0, run.stderr
        assert "handler-ran" not in run.stderr
        assert "refused" not in run.stderr and "Failed to fetch" not in run.stderr
        assert "script-src" in run.stderr  # the console error names the directive that refused the handler

    def test_custom_js_cannot_compile(self, harness: Harness, tmp_path: Path) -> None:
        bokeh = bokeh_or_skip()
        plot = bokeh.plotting.figure(width=800, height=450)
        plot.line([1, 2], [3, 4])
        plot.xaxis.formatter = bokeh.models.CustomJSTickFormatter(code="return 'x'")
        run = harness.draw(tmp_path, bokeh.embed.json_item(plot), library="bokeh")

        assert "unsafe-eval" in assert_final_line(run, "page", "EvalError")
        assert not (run.work / "plot-light.png").exists()

    def test_a_webgl_trace_fails_instead_of_drawing_the_notice(self, harness: Harness, tmp_path: Path) -> None:
        figure = {"data": [{"type": "scattergl", "x": [1, 2], "y": [2, 1]}], "layout": {"width": 800, "height": 450}}
        run = harness.draw(tmp_path, figure)

        assert_final_line(run, "draw", "NoWebGL")
        assert not (run.work / "plot-light.png").exists()

    @pytest.mark.parametrize("trace", ["scatter3d", "surface", "parcoords", "scattermap"])
    def test_a_webgl_trace_without_a_notice_fails_before_it_draws(
        self, harness: Harness, tmp_path: Path, trace: str
    ) -> None:
        """PB-2a: a 3D scene shows no notice, it draws nothing but its colour bar, which the host gates pass; every
        WebGL trace type fails before the page is drawn, until the renderer draws WebGL."""
        figure = {"data": [{"type": trace}], "layout": {"width": 800, "height": 450}}
        run = harness.draw(tmp_path, figure)

        assert trace in assert_final_line(run, "draw", "NoWebGL")
        assert not (run.work / "plot-light.png").exists()


class TestTheFigureIsChecked:
    @pytest.mark.parametrize(
        ("figure", "cls", "text"),
        [
            ("{not json", "FigureError", "is not JSON"),
            ({"layout": {}}, "FigureError", "is not a plotly figure"),
            ([1, 2], "FigureError", "is not a plotly figure"),
            ({"data": [], "layout": []}, "FigureError", "is not a plotly figure"),
            (plotly_figure(100, 100), "FigureError", "outside 320 to 6400"),
            (plotly_figure(1e9, 450), "FigureError", "outside 320 to 6400"),
            (plotly_figure(400), "FigureError", "outside 320 to 6400"),
            (plotly_figure(None, 4000), "FigureError", "outside 320 to 6400"),
        ],
        ids=[
            "not json",
            "no data",
            "a list",
            "a list for a layout",
            "too small",
            "too large",
            "a width whose height is too small",
            "a height whose width is too large",
        ],
    )
    def test_a_figure_the_page_must_not_take_fails_as_figure(
        self, harness: Harness, tmp_path: Path, figure: object, cls: str, text: str
    ) -> None:
        run = harness.draw(tmp_path, figure)
        assert text in assert_final_line(run, "figure", cls)

    def test_a_bokeh_item_needs_its_root(self, harness: Harness, tmp_path: Path) -> None:
        item = bokeh_item(800, 450)
        item["root_id"] = "nowhere"
        run = harness.draw(tmp_path, item, library="bokeh")
        assert "is not a bokeh figure" in assert_final_line(run, "figure", "FigureError")

    def test_one_byte_over_the_cap_is_refused(self, harness: Harness, tmp_path: Path) -> None:
        text = json.dumps(plotly_figure(800, 450))
        padded = text + " " * (python_harness.FIGURE_MAX_BYTES + 1 - len(text))
        run = harness.draw(tmp_path, padded)
        assert "more than the 16777216-byte limit" in assert_final_line(run, "figure", "FigureTooLarge")

    def test_a_link_is_not_followed(self, harness: Harness, tmp_path: Path) -> None:
        work = tmp_path / "work"
        work.mkdir()
        (work / "real.json").write_text(json.dumps(plotly_figure(800, 450)), encoding="utf-8")
        (work / "plot-light.json").symlink_to("real.json")
        run = harness.draw(tmp_path, None)
        assert "could not be opened as a regular file" in assert_final_line(run, "figure", "FigureError")


class TestUsage:
    @pytest.mark.parametrize(
        ("args", "env", "sandbox", "package", "text"),
        [
            (None, {}, False, True, "--figure needs ANYPLOT_SANDBOX=1"),
            (["--library=plotly", "plot.js"], {}, True, True, "plotly draws a figure"),
            (
                ["--library=chartjs", "--figure=plot-light.json"],
                {},
                True,
                True,
                '--figure is for plotly and bokeh, not "chartjs"',
            ),
            (None, {"ANYPLOT_PAGE_ONLY": "1"}, True, True, "builds no page for a figure"),
            (None, {}, True, False, "--figure needs ANYPLOT_FIGURE_PACKAGE"),
            (None, {"ANYPLOT_FIGURE_PACKAGE": "/nonexistent"}, True, False, "bundle missing: /nonexistent/"),
        ],
        ids=["no sandbox", "no figure", "another library", "page only", "no package", "no bundle"],
    )
    def test_a_bad_call_is_a_usage_error(
        self,
        harness: Harness,
        tmp_path: Path,
        args: list[str] | None,
        env: dict[str, str],
        sandbox: bool,
        package: bool,
        text: str,
    ) -> None:
        run = harness.draw(tmp_path, plotly_figure(800, 450), args=args, env=env, sandbox=sandbox, package=package)
        assert run.returncode == 2 and text in run.stderr
        if sandbox:
            assert run.last_line.startswith("render: error: harness UsageError -: ")

    def test_a_code_file_named_after_a_figure_library_is_refused(self, harness: Harness, tmp_path: Path) -> None:
        work = tmp_path / "work"
        work.mkdir()
        (work / "bokeh.js").write_text("1;\n", encoding="utf-8")
        run = harness.draw(tmp_path, None, args=["bokeh.js"], sandbox=False)
        assert run.returncode == 2 and "bokeh draws a figure, not a code file" in run.stderr


PLOTLY_PLOT = """\
import os

import plotly.graph_objects as go

THEME = os.getenv("ANYPLOT_THEME", "light")
fig = go.Figure(go.Scatter(x=[1, 2, 3, 4], y=[2, 4, 3, 5], mode="lines+markers"))
fig.update_layout(
    width=800,
    height=450,
    title={"text": "two steps · plotly"},
    xaxis={"range": [0, 5], "dtick": 1},
    paper_bgcolor="#FAF8F1" if THEME == "light" else "#1A1A17",
)
fig.write_json(f"plot-{THEME}.json")
"""
"""A plotly plot whose axis range builds an info-array validator (`CODE_BUILDERS`) under the guard."""
BOKEH_PLOT = """\
import json
import os

from bokeh.embed import json_item
from bokeh.plotting import figure

THEME = os.getenv("ANYPLOT_THEME", "light")
p = figure(width=4800, height=2700, title="two steps · bokeh", toolbar_location=None)
p.line([1, 2, 3, 4], [2, 4, 3, 5], line_width=8)
p.background_fill_color = "#FAF8F1" if THEME == "light" else "#1A1A17"
with open(f"plot-{THEME}.json", "w", encoding="utf-8") as handle:
    json.dump(json_item(p), handle)
"""


class TestBothSteps:
    @pytest.mark.parametrize("theme", ["light", "dark"])
    @pytest.mark.parametrize(("library", "plot"), [("plotly", PLOTLY_PLOT), ("bokeh", BOKEH_PLOT)])
    def test_the_python_harness_renders_through_the_page(
        self, harness: Harness, tmp_path: Path, library: str, plot: str, theme: str
    ) -> None:
        """The whole two-step render: the plot under the guard (and the exec filter where the kernel has it), the
        figure, the package's own JavaScript in the page, a canonical PNG."""
        if package_dir(library) is None:
            pytest.skip(f"needs {library}")
        (tmp_path / "plot.py").write_text(plot, encoding="utf-8")
        environment = harness.environment(
            {
                "ANYPLOT_THEME": theme,
                "OPENBLAS_NUM_THREADS": "1",
                "ANYPLOT_RLIMIT_AS_MB": "2048",
                "ANYPLOT_RLIMIT_CPU_S": "60",
            }
        )
        done = subprocess.run(
            [
                sys.executable,
                *python_harness.INTERPRETER_FLAGS,
                str(HARNESS_SOURCE),
                python_harness.FIGURE_FLAG,
                library,
                "plot.py",
                "--",
                harness.node,
                str(harness.render_mjs),
                f"--library={library}",
            ],
            cwd=tmp_path,
            env=environment,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )

        assert done.returncode == 0, done.stderr
        png = (tmp_path / f"plot-{theme}.png").read_bytes()
        assert struct.unpack(">II", png[16:24]) == (3200, 1800)
        end = json.loads(
            [line for line in done.stdout.splitlines() if line.startswith("HARNESS ")][-1].split(" ", 1)[1]
        )
        assert set(end["steps"]) == {"plot", "screenshot"} and end["exec_deny"] in ("on", "unavailable", "unsupported")
