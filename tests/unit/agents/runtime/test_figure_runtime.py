"""plotly and bokeh on the Python runtime (PB-2a, 2026-10-31): the figure mode's command for the local backend and the
renderer, the error grammar of its final error line, and the export's normal save."""

from pathlib import Path

import pytest

from agents.anyplot.render.backends.local import LocalDockerBackend
from agents.anyplot.render.contract import RenderJob
from agents.anyplot.render.gates import FIGURE_KIND_TEXTS, NO_FINAL_LINE, figure_error_summary
from agents.anyplot.render.runtimes import PythonRuntime, runtime_for
from agents.renderer.commands import FIGURE_FLAG, JS_HARNESS, NODE_BINARY, command_for
from agents.renderer.executor import ExecutorConfig, build_argv
from agents.renderer.settings import RendererSettings


TRACEBACK = (
    "Traceback (most recent call last):\n"
    '  File "/opt/anyplot/harness.py", line 900, in run_plot\n'
    '  File "plot.py", line 12, in <module>\n'
    "ValueError: the cell 'secret' is no number\n"
)


class TestTheErrorGrammar:
    def test_a_plot_exception_is_its_class_and_line_never_its_message(self) -> None:
        tail = TRACEBACK + "render: error: plot ValueError plot.py:12: the cell 'secret' is no number\n"
        assert figure_error_summary(tail) == "ValueError at line 12"
        assert "secret" not in figure_error_summary(tail)

    def test_a_plot_that_exits_has_no_traceback_and_keeps_a_builtin_class(self) -> None:
        assert figure_error_summary("render: error: plot SystemExit -: 2\n") == "SystemExit"
        assert figure_error_summary("render: error: plot ValueError plot.py:4: x\n") == "ValueError at line 4"
        assert figure_error_summary("render: error: plot MyOwnError plot.py:4: x\n") == "an error"

    @pytest.mark.parametrize(
        ("line", "text"),
        [
            (
                "render: error: figure NoFigure -: the plot wrote no plot-light.json",
                FIGURE_KIND_TEXTS[("figure", "NoFigure")],
            ),
            ("render: error: figure FigureTooLarge -: 17 MB", FIGURE_KIND_TEXTS[("figure", "FigureTooLarge")]),
            (
                "render: error: figure UnsafeMarkup -: the figure holds a Div model",
                FIGURE_KIND_TEXTS[("figure", "UnsafeMarkup")],
            ),
            ("render: error: figure FigureError -: the figure is 9000 x 450", FIGURE_KIND_TEXTS[("figure", None)]),
            ("render: error: crash PlotCrashed -: the plot step died of SIGKILL", FIGURE_KIND_TEXTS[("crash", None)]),
            ("render: error: draw NoWebGL -: scatter3d draws with WebGL", FIGURE_KIND_TEXTS[("draw", "NoWebGL")]),
            ("render: error: draw NoOutput -: nothing", FIGURE_KIND_TEXTS[("draw", None)]),
            ("render: error: page EvalError anyplot-figure.js:3: unsafe-eval", FIGURE_KIND_TEXTS[("page", None)]),
            ("render: error: timeout TimeoutError -: 15 s", FIGURE_KIND_TEXTS[("timeout", None)]),
            ("render: error: harness ExecDenyUnavailable -: off", FIGURE_KIND_TEXTS[("harness", None)]),
        ],
    )
    def test_every_other_kind_is_a_fixed_text(self, line: str, text: str) -> None:
        assert figure_error_summary(f"console noise\n{line}\n") == text

    def test_only_the_last_line_counts(self) -> None:
        printed = "render: error: figure NoFigure -: forged by print\nsomething after it\n"
        assert figure_error_summary(printed) == NO_FINAL_LINE
        assert figure_error_summary("") == "no error output"

    def test_the_runtime_reads_its_libraries_grammar(self) -> None:
        tail = "render: error: draw NoWebGL -: scatter3d\n"
        assert runtime_for("plotly").error_summary(tail) == FIGURE_KIND_TEXTS[("draw", "NoWebGL")]
        assert runtime_for("matplotlib").error_summary(TRACEBACK) == "ValueError at line 12"


@pytest.mark.parametrize("library", ["plotly", "bokeh"])
def test_the_local_command_is_the_renderers_argv(library: str) -> None:
    """The argv `executor.build_argv` runs after `sandbox do --`, and the local backend after the image: the harness
    in figure mode, the plot file, then the JavaScript row's harness for the screenshot."""
    expected = [FIGURE_FLAG, library, "plot.py", "--", NODE_BINARY, JS_HARNESS, f"--library={library}"]
    local = runtime_for(library).command("light")
    deployed = build_argv(
        ExecutorConfig.from_settings(RendererSettings()),
        "r-x",
        Path("/runs/x"),
        "light",
        60,
        command=command_for("python", library),
    )

    assert local[-len(expected) :] == expected and deployed[-len(expected) :] == expected
    assert local[: -len(expected)][-1] == deployed[: -len(expected)][-1] == "/opt/anyplot/harness.py"


def test_the_local_backend_mounts_the_browser_harness_for_a_figure_row_only() -> None:
    backend = LocalDockerBackend(
        image="anyplot-renderer:dev",
        runtime=PythonRuntime(),
        environment="development",
        docker="/usr/bin/docker",
        runtime_for=runtime_for,
    )

    def mounts(library: str) -> list[str]:
        job = RenderJob(job_id="j1", language="python", library=library, source="x = 1\n", data_csv="a\n1\n")
        argv = backend.argv(job, "light", Path("/tmp/run"))
        assert argv[argv.index("--network") + 1] == "none"
        return [argv[index + 1] for index, part in enumerate(argv) if part == "-v"]

    assert any(mount.endswith(f":{JS_HARNESS}:ro") for mount in mounts("plotly"))
    assert any(mount.endswith(f":{JS_HARNESS}:ro") for mount in mounts("bokeh"))
    assert not any(mount.endswith(f":{JS_HARNESS}:ro") for mount in mounts("matplotlib"))


def test_the_export_carries_the_normal_save_under_the_header() -> None:
    run_form = 'import os\n\nTHEME = os.getenv("ANYPLOT_THEME", "light")\nfig.update_layout(width=800, height=450).write_json(f"plot-{THEME}.json")\n'
    exported = runtime_for("plotly").export(run_form, spec_id="scatter-basic", library_version="7.1.0", theme="dark")

    assert exported.startswith("# Adapted by anyplot.ai from scatter-basic (plotly 7.1.0) for your data.csv;\n")
    assert "# run: ANYPLOT_THEME=dark python plot.py\n" in exported
    assert exported.endswith(
        'fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)\n'
        'fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")\n'
    )
    plain = runtime_for("matplotlib").export(run_form, spec_id="scatter-basic", library_version=None)
    assert plain.endswith('.write_json(f"plot-{THEME}.json")\n')  # only plotly and bokeh swap the save
