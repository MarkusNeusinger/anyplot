"""The runtime registry (agents/anyplot/render/runtimes): a library's runtime, and what it binds."""

from pathlib import Path

import pytest

from agents.anyplot.code import edits
from agents.anyplot.code.normalise import SUPPORTED_LIBRARIES as NORMALISED_LIBRARIES
from agents.anyplot.code.profiles.javascript import regions as js_regions
from agents.anyplot.code.profiles.julia import regions as jl_regions
from agents.anyplot.code.profiles.r import regions as r_regions
from agents.anyplot.code.regions import PLACEHOLDER
from agents.anyplot.data.kinds import ColumnKinds, read_kinds
from agents.anyplot.render.contract import BLOCKING_RULES, RenderJob
from agents.anyplot.render.runtimes import (
    JAVASCRIPT_LIBRARIES,
    JULIA_LIBRARIES,
    PYTHON_LIBRARIES,
    R_LIBRARIES,
    RUNTIME_CLASSES,
    RUNTIME_LIBRARIES,
    JavaScriptRuntime,
    JuliaRuntime,
    PythonRuntime,
    RRuntime,
    has_runtime,
    language_of,
    runtime_for,
)
from agents.anyplot.render.runtimes.python import ADAPTATION_TARGETS as PYTHON_TARGETS
from agents.anyplot.schemas import CODE_ARTIFACTS, AdaptPlan, Edit
from agents.anyplot.settings import AgentSettings
from agents.renderer import commands
from core.constants import SUPPORTED_LIBRARIES
from tests.unit.agents.code.conftest import (
    JS_CATALOGUE,
    JS_CATALOGUE_NORMALISED,
    JS_WORKING,
    JULIA_CATALOGUE,
    JULIA_CATALOGUE_NORMALISED,
    JULIA_WORKING,
    MUIX_WORKING,
    R_CATALOGUE,
    R_CATALOGUE_NORMALISED,
)


class TestRegistry:
    def test_the_registry_serves_the_python_r_julia_and_javascript_libraries(self) -> None:
        assert PYTHON_LIBRARIES == NORMALISED_LIBRARIES
        # plotly and bokeh joined through the renderer's figure mode (PB-2a, 2026-10-31).
        assert PYTHON_LIBRARIES == {
            "matplotlib",
            "seaborn",
            "plotnine",
            "altair",
            "pygal",
            "letsplot",
            "plotly",
            "bokeh",
        }
        assert R_LIBRARIES == edits.R_LIBRARIES == {"ggplot2"}
        assert JULIA_LIBRARIES == edits.JULIA_LIBRARIES == {"makie"}
        # MUI X joined the four with its fixtures (JS-4c, 2026-10-31).
        assert JAVASCRIPT_LIBRARIES == edits.JAVASCRIPT_LIBRARIES == {"chartjs", "d3", "echarts", "highcharts", "muix"}
        assert (
            RUNTIME_LIBRARIES
            == PYTHON_LIBRARIES | R_LIBRARIES | JULIA_LIBRARIES | JAVASCRIPT_LIBRARIES
            <= SUPPORTED_LIBRARIES
        )
        languages = {language_of(library) for library in RUNTIME_LIBRARIES}
        assert languages == set(RUNTIME_CLASSES) == {"python", "r", "julia", "javascript"}

    @pytest.mark.parametrize("library", sorted(PYTHON_LIBRARIES))
    def test_a_python_runtime_is_bound_to_its_library(self, library: str) -> None:
        runtime = runtime_for(library, cpu_seconds=45)
        assert isinstance(runtime, PythonRuntime)
        assert runtime.library == library and runtime.language == "python" == language_of(library)
        assert runtime.file_name == "plot.py" and runtime.code_artifact == "plot.py" in CODE_ARTIFACTS
        assert runtime.placeholder == PLACEHOLDER and runtime.cpu_seconds == 45 and runtime.render_p95_s == 15.0
        assert runtime.blocking_rules == BLOCKING_RULES and runtime.adaptation_targets == PYTHON_TARGETS
        # matplotlib's probe reports the drawn texts; the libraries that render without it hand them to the review
        assert runtime.review_texts is (library in {"altair", "pygal", "letsplot", "plotly", "bokeh"})
        assert has_runtime(library)
        # plotly and bokeh render in the row's two steps (PB-2a): the harness in figure mode before the screenshot's
        # command; every other library's command is plot mode's, as before.
        command = runtime.command("light")
        if library in ("plotly", "bokeh"):
            assert runtime.figure == library
            start = command.index("--figure")
            assert command[start - 1] == runtime.harness and command[start : start + 4] == [
                "--figure",
                library,
                "plot.py",
                "--",
            ]
            assert command[start + 4 :] == list(commands.command_for("python", library).argv)
        else:
            assert runtime.figure == "" and command[-1] == "plot.py" and "--figure" not in command

    def test_the_r_runtime_is_bound_to_ggplot2(self) -> None:
        """Dispatched by the library's language (`RUNTIME_CLASSES`), with the R row's reserve (`commands.py`)."""
        runtime = runtime_for("ggplot2", cpu_seconds=45)
        assert isinstance(runtime, RRuntime)
        assert runtime.library == "ggplot2" and runtime.language == "r" == language_of("ggplot2")
        assert runtime.file_name == "plot.R" and runtime.code_artifact == "plot.R" in CODE_ARTIFACTS
        assert runtime.placeholder == r_regions.PLACEHOLDER == "df <- load_user_data()"
        assert runtime.cpu_seconds == 45 and runtime.render_p95_s == 15.0
        assert runtime.blocking_rules == BLOCKING_RULES | {"dataset-package"}
        assert set(runtime.adaptation_targets) == set(PYTHON_TARGETS)
        assert runtime.review_texts is True  # no probe: the review finds the requested texts in the image
        assert has_runtime("ggplot2")
        with pytest.raises(ValueError, match="python library"):
            RRuntime(library="matplotlib")

    def test_the_julia_runtime_is_bound_to_makie(self) -> None:
        """Dispatched by the library's language (`RUNTIME_CLASSES`), with the Julia row's reserve (`commands.py`)."""
        runtime = runtime_for("makie", cpu_seconds=45)
        assert isinstance(runtime, JuliaRuntime)
        assert runtime.library == "makie" and runtime.language == "julia" == language_of("makie")
        assert runtime.file_name == "plot.jl" and runtime.code_artifact == "plot.jl" in CODE_ARTIFACTS
        assert runtime.placeholder == jl_regions.PLACEHOLDER == "df = load_user_data()"
        assert runtime.cpu_seconds == 45 and runtime.render_p95_s == 25.0
        assert runtime.blocking_rules == BLOCKING_RULES | {"dataset-package"}
        assert set(runtime.adaptation_targets) == set(PYTHON_TARGETS)
        assert runtime.review_texts is True  # no probe: the review finds the requested texts in the image
        assert has_runtime("makie")
        with pytest.raises(ValueError, match="r library"):
            JuliaRuntime(library="ggplot2")

    @pytest.mark.parametrize("library", sorted(JAVASCRIPT_LIBRARIES))
    def test_the_javascript_runtime_is_bound_to_its_library(self, library: str) -> None:
        """Dispatched by the library's language (`RUNTIME_CLASSES`), with the JavaScript row's reserve."""
        runtime = runtime_for(library, cpu_seconds=45)
        assert isinstance(runtime, JavaScriptRuntime)
        assert runtime.library == library and runtime.language == "javascript" == language_of(library)
        code_file = "plot.tsx" if library == "muix" else "plot.js"
        assert runtime.file_name == code_file and runtime.code_artifact == code_file in CODE_ARTIFACTS
        assert runtime.placeholder == js_regions.PLACEHOLDER == "const data = loadUserData();"
        assert runtime.cpu_seconds == 45 and runtime.render_p95_s == 15.0
        assert runtime.blocking_rules == BLOCKING_RULES | {"unavailable-import"}
        assert set(runtime.adaptation_targets) == set(PYTHON_TARGETS)
        assert runtime.review_texts is True  # no probe: the review finds the requested texts in the image
        assert has_runtime(library)
        with pytest.raises(ValueError, match="r library"):
            JavaScriptRuntime(library="ggplot2")

    def test_the_javascript_runtime_takes_muix_as_tsx(self) -> None:
        """MUI X's code is written and exported as TSX (`commands.CODE_FILE_OVERRIDES`), served since JS-4c."""
        runtime = runtime_for("muix")
        assert runtime.file_name == "plot.tsx" and runtime.code_artifact == "plot.tsx" in CODE_ARTIFACTS
        assert runtime.command("light")[-1] == "plot.tsx"
        assert runtime.security(MUIX_WORKING) == []

    def test_every_catalogue_library_has_a_runtime_and_another_is_refused(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """All 15 catalogue libraries are served since PB-2a (2026-10-31); a registry without one still refuses it."""
        assert RUNTIME_LIBRARIES == SUPPORTED_LIBRARIES
        assert language_of("plotly") == "python" and has_runtime("plotly") and has_runtime("bokeh")
        monkeypatch.setattr("agents.anyplot.render.runtimes.RUNTIME_LIBRARIES", RUNTIME_LIBRARIES - {"plotly"})
        with pytest.raises(ValueError, match="no runtime for 'plotly'"):
            runtime_for("plotly")
        with pytest.raises(ValueError, match="unknown library"):
            language_of("excel")

    def test_the_settings_accept_the_served_libraries_and_refuse_one_the_registry_does_not_serve(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        served = ["matplotlib", "plotly", "bokeh", "ggplot2", "makie", "d3", "highcharts", "muix"]
        assert AgentSettings(libraries=served).libraries == served
        monkeypatch.setattr("agents.anyplot.settings.RUNTIME_LIBRARIES", RUNTIME_LIBRARIES - {"plotly"})
        with pytest.raises(ValueError, match="no runtime"):
            AgentSettings(libraries=["matplotlib", "plotly"])


class TestPythonRuntimeBindings:
    """The runtime hands the pipeline the Python code modules, for its own library."""

    CODE = (
        'import os\nimport matplotlib.pyplot as plt\n\nTHEME = os.getenv("ANYPLOT_THEME", "light")\n'
        'PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"\nIMPRINT_PALETTE = ["#009E73", "#C475FD"]\n'
        "df = load_user_data()\nfig, ax = plt.subplots(figsize=(16, 9), dpi=200)\n"
        'ax.scatter(df["x"], df["y"])\nplt.savefig(f"plot-{THEME}.png", dpi=200, facecolor=PAGE_BG)\n'
    )

    def test_regions_security_and_adaptation_run_for_the_bound_library(self) -> None:
        runtime = runtime_for("seaborn")
        regions = runtime.regions(self.CODE)
        assert regions.theme is not None and regions.savefig is not None and len(regions.placeholders) == 1
        assert runtime.security(self.CODE) == []
        assert runtime.adaptation(self.CODE, original_palette=["#009E73", "#C475FD"]) == []
        assert runtime.security("import subprocess\n") != []  # the seaborn profile, not a crash

    def test_readiness_and_export_follow_the_library(self) -> None:
        runtime = runtime_for("matplotlib")
        readiness = runtime.readiness(
            self.CODE.replace("df = load_user_data()\n", "df = None\n"),
            spec_id="scatter-basic",
            enabled_libraries=["matplotlib"],
        )
        assert readiness.status in ("clean", "coupled")
        export = runtime.export("print(1)\n", spec_id="scatter-basic", library_version="3.11.2", theme="dark")
        assert export.startswith("# Adapted by anyplot.ai from scatter-basic (matplotlib 3.11.2)")
        assert "ANYPLOT_THEME=dark python plot.py" in export

    def test_error_summary_reads_a_python_traceback_for_plot_py(self) -> None:
        runtime = runtime_for("matplotlib")
        tail = 'Traceback (most recent call last):\n  File "plot.py", line 12, in <module>\nKeyError: "secret cell"\n'
        assert runtime.error_summary(tail) == "KeyError at line 12"

    def test_new_literals_and_the_plan_applier_are_bound(self) -> None:
        runtime = runtime_for("matplotlib")
        assert runtime.new_literals('x = "a"\n', 'x = "a"\ny = "new text"\n') == ["new text"]
        assert runtime.restore_protected(self.CODE, self.CODE) is None or isinstance(
            runtime.restore_protected(self.CODE, self.CODE), str
        )

    PLOTNINE = (
        "import os\nfrom plotnine import aes, geom_point, ggplot\n\n"
        'THEME = os.getenv("ANYPLOT_THEME", "light")\ndf = load_user_data()\n'
        'plot = ggplot(df, aes(x="x", y="y")) + geom_point()\n'
        'plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")\n'
    )

    def test_plotnine_and_altair_runtimes_read_their_own_save_rule(self) -> None:
        plotnine, altair = runtime_for("plotnine"), runtime_for("altair")
        regions = plotnine.regions(self.PLOTNINE)
        assert regions.savefig is not None and regions.savefig.name == "save" and regions.savefig.standard_target
        assert plotnine.security(self.PLOTNINE) == []
        assert altair.security(self.PLOTNINE) != []  # the plotnine import is refused with altair
        assert runtime_for("matplotlib").regions(self.PLOTNINE).savefig_calls == ()  # `.save` is no save there
        assert plotnine.file_name == altair.file_name == "plot.py" and altair.code_artifact == "plot.py"
        changed = self.PLOTNINE.replace("dpi=400", "dpi=100")
        assert plotnine.restore_protected(self.PLOTNINE, changed) == self.PLOTNINE


class TestRRuntimeBindings:
    """The R runtime hands the pipeline the R code profile of PR 3a, for ggplot2 (step 2c, PR 3b)."""

    WORKING = R_CATALOGUE_NORMALISED.replace(
        "set.seed(42)\ndf <- tibble::tibble(!!SPEND := runif(50, 5, 150), !!REVENUE := rnorm(50, 300, 40))\n",
        "df <- load_user_data()\n",
    )

    def test_the_working_form_has_one_placeholder(self) -> None:
        assert self.WORKING.count("df <- load_user_data()") == 1 and "rnorm" not in self.WORKING

    def test_normalise_regions_security_and_adaptation_are_the_r_profiles(self) -> None:
        runtime = runtime_for("ggplot2")
        assert runtime.normalise(R_CATALOGUE, "ggplot2") == R_CATALOGUE_NORMALISED
        regions = runtime.regions(self.WORKING)
        assert regions.imprint is not None and list(regions.imprint.entries)[:2] == ["#009E73", "#C475FD"]
        assert runtime.security(self.WORKING) == [] and runtime.validate(self.WORKING, "ggplot2") == []
        palette = list(regions.imprint.entries)
        assert runtime.adaptation(self.WORKING, original_palette=palette) == []
        assert "banned-name" in {f.rule for f in runtime.security('system("id")\n')}

    def test_a_dataset_package_is_a_blocking_adaptation_finding(self) -> None:
        """gapminder passes SECURITY and is `dataset-package`, which the R runtime's blocking set holds: the pipeline
        refuses the working form, while the readiness scan of a catalogue file with it stays `coupled`."""
        runtime = runtime_for("ggplot2")
        code = self.WORKING.replace("library(ragg)\n", "library(ragg)\nlibrary(gapminder)\n")
        assert runtime.security(code) == []
        rules = {f.rule for f in runtime.adaptation(code, original_palette=["#009E73"])}
        assert "dataset-package" in rules and rules <= runtime.blocking_rules
        assert "dataset-package" not in runtime_for("matplotlib").blocking_rules

    def test_readiness_and_export_follow_the_r_profile(self) -> None:
        runtime = runtime_for("ggplot2")
        readiness = runtime.readiness(R_CATALOGUE_NORMALISED, spec_id="scatter-demo", enabled_libraries=["ggplot2"])
        assert readiness.status in ("clean", "coupled")
        blocked = runtime.readiness(R_CATALOGUE_NORMALISED, spec_id="scatter-demo", enabled_libraries=["matplotlib"])
        assert blocked.status == "blocked" and blocked.reasons[0].startswith("library-disabled: ggplot2")
        export = runtime.export("print(1)\n", spec_id="scatter-basic", library_version="4.0.3", theme="dark")
        assert export.startswith("# Adapted by anyplot.ai from scatter-basic (ggplot2 4.0.3) for your data.csv;\n")
        assert "# run: ANYPLOT_THEME=dark Rscript plot.R\n" in export

    def test_the_loader_reads_data_csv_typed_from_the_kinds(self) -> None:
        runtime = runtime_for("ggplot2")
        run_form = runtime.loader_block(
            self.WORKING,
            columns=["Spend (k USD)", "Revenue (k USD)"],
            dtypes={"Spend (k USD)": "number", "Revenue (k USD)": "integer"},
            parse_dates=[],
            kinds={"Spend (k USD)": "number", "Revenue (k USD)": "integer"},
        )
        assert "load_user_data" not in run_form and 'df <- readr::read_csv(\n  "data.csv",' in run_form
        assert '"Revenue (k USD)" = readr::col_integer()' in run_form
        with pytest.raises(ValueError, match="no kind"):
            runtime.loader_block(self.WORKING, columns=["Spend (k USD)"], dtypes={}, parse_dates=[], kinds={})

    def test_loader_notes_count_the_integers_r_reads_inexactly_per_column(self) -> None:
        """Owner rule of 2026-10-15: no silent loss; `col_double()` is exact only up to 2^53."""
        csv_text = "id,code,n\n9007199254740993,9007199254740995,1\n-9007199254740999,12,2\n9007199254740992,13,3\n"
        kinds = read_kinds(csv_text, {"id": "integer", "code": "integer", "n": "integer"})
        assert kinds.inexact == {"id": 2, "code": 1}
        (line,) = runtime_for("ggplot2").loader_notes(kinds)
        assert line == (
            "R reads 3 integers past ±2^53 as the nearest double, so the plot can show them a unit or more off: "
            "2 in 'id', 1 in 'code'"
        )
        assert runtime_for("matplotlib").loader_notes(kinds) == []
        assert runtime_for("ggplot2").loader_notes(read_kinds("n\n1\n", {"n": "integer"})) == []
        one = read_kinds("id\n9007199254740993\n", {"id": "integer"})
        assert runtime_for("ggplot2").loader_notes(one)[0].startswith("R reads 1 integer past ±2^53")

    def test_the_loader_note_is_a_change_note_and_names_what_fits(self) -> None:
        """A "what changed" entry holds `MAX_CHANGE_CHARS` (owner decision of 2026-10-29): the columns that fit are
        named with their counts, the rest counted; the first column always fits, also at the name and count caps."""
        from agents.anyplot.schemas import MAX_CHANGE_CHARS, MAX_COLUMN_NAME_CHARS

        header = ",".join(f"c{index}" for index in range(7))
        csv_text = header + "\n" + ",".join(["9007199254740993"] * 7) + "\n"
        kinds = read_kinds(csv_text, {f"c{index}": "integer" for index in range(7)})
        (line,) = runtime_for("ggplot2").loader_notes(kinds)
        assert line.startswith("R reads 7 integers") and line.endswith("1 in 'c6'") and len(line) <= MAX_CHANGE_CHARS

        names = [chr(ord("a") + index) * MAX_COLUMN_NAME_CHARS for index in range(50)]
        wide = read_kinds(
            ",".join(names) + "\n" + ",".join(["9007199254740993"] * 50) + "\n", dict.fromkeys(names, "integer")
        )
        (crowded,) = runtime_for("ggplot2").loader_notes(wide)
        assert len(crowded) <= MAX_CHANGE_CHARS and f"1 in '{names[0]}'" in crowded
        assert crowded.endswith(", and 49 more columns")

    def test_edits_literals_and_errors_use_the_r_dialect(self) -> None:
        runtime = runtime_for("ggplot2")
        plan = AdaptPlan(edits=[Edit(find='labs(title = "",', replace='labs(title = "Umsatz",')])
        applied = runtime.apply_plan(self.WORKING, plan)
        assert applied.code is not None and 'labs(title = "Umsatz",' in applied.code
        assert runtime.new_literals(self.WORKING, applied.code) == ["Umsatz"]
        drifted = self.WORKING.replace("dpi      = 200", "dpi      = 300")
        assert runtime.restore_protected(self.WORKING, drifted) == self.WORKING
        tail = "Error in `geom_point()`:\n! Problem while computing aesthetics.\nCalls: ggsave -> print -> plot\n"
        assert runtime.error_summary(tail) == "error in geom_point(); calls: ggsave -> print -> plot"

    def test_the_command_is_the_renderers_r_row_in_exec_mode(self) -> None:
        """The argv `executor.build_argv` runs after `sandbox do --`: the harness, `--exec --`, R's own binary."""
        from agents.renderer.commands import R_BINARY, command_for
        from agents.renderer.executor import ExecutorConfig, build_argv
        from agents.renderer.settings import RendererSettings

        local = runtime_for("ggplot2").command("light")
        assert local[-7:] == ["--exec", "--", R_BINARY, "--no-echo", "--no-restore", "--no-save", "--file=plot.R"]
        config = ExecutorConfig.from_settings(RendererSettings())
        deployed = build_argv(config, "r-x", Path("/runs/x"), "light", 60, command=command_for("r", "ggplot2"))
        assert deployed[-7:] == local[-7:]

    def test_data_runs_and_conversions_stay_pythons(self) -> None:
        runtime, python = runtime_for("ggplot2", cpu_seconds=45), PythonRuntime(cpu_seconds=45)
        assert runtime.data_command() == python.data_command() and runtime.data_env(20) == python.data_env(20)
        assert runtime.convert_command() == python.convert_command() and runtime.convert_env() == python.convert_env()

    def test_collect_reads_the_png_and_no_probe(self, tmp_path: Path) -> None:
        (tmp_path / "plot-dark.png").write_bytes(b"\x89PNG data")
        (tmp_path / "probe-dark.json").write_text('{"texts": []}')
        assert runtime_for("ggplot2").collect(tmp_path, "dark") == (b"\x89PNG data", None)
        assert runtime_for("ggplot2").collect(tmp_path, "light") == (None, None)


class TestJuliaRuntimeBindings:
    """The Julia runtime hands the pipeline the Julia code profile of J2a, for Makie (step 5, J2b)."""

    COLUMNS = ["Ausgaben (k €)", "Umsatz $ (k)", "Zeit"]
    KINDS = {"Ausgaben (k €)": "number", "Umsatz $ (k)": "integer", "Zeit": "datetime"}

    def run_form(self) -> str:
        return runtime_for("makie").loader_block(
            JULIA_WORKING, columns=self.COLUMNS, dtypes={}, parse_dates=[], kinds=self.KINDS
        )

    def test_normalise_regions_security_and_adaptation_are_the_julia_profiles(self) -> None:
        runtime = runtime_for("makie")
        assert runtime.normalise(JULIA_CATALOGUE, "makie") == JULIA_CATALOGUE_NORMALISED
        regions = runtime.regions(JULIA_WORKING)
        assert regions.imprint is not None and list(regions.imprint.entries)[:2] == ["#009E73", "#C475FD"]
        assert runtime.security(JULIA_WORKING) == [] and runtime.validate(JULIA_WORKING, "makie") == []
        assert runtime.adaptation(JULIA_WORKING, original_palette=list(regions.imprint.entries)) == []
        assert "banned-name" in {f.rule for f in runtime.security("run(`ls`)\n")}  # the Julia profile, not a crash

    def test_a_dataset_package_is_a_blocking_adaptation_finding(self) -> None:
        """RDatasets passes SECURITY and is `dataset-package`, which the Julia runtime's blocking set holds, as R's."""
        runtime = runtime_for("makie")
        code = JULIA_WORKING.replace("using DataFrames\n", "using DataFrames\nusing RDatasets\n")
        assert runtime.security(code) == []
        rules = {f.rule for f in runtime.adaptation(code, original_palette=["#009E73"])}
        assert "dataset-package" in rules and rules <= runtime.blocking_rules

    def test_readiness_and_export_follow_the_julia_profile(self) -> None:
        runtime = runtime_for("makie")
        readiness = runtime.readiness(JULIA_CATALOGUE_NORMALISED, spec_id="scatter-demo", enabled_libraries=["makie"])
        assert readiness.status in ("clean", "coupled")
        blocked = runtime.readiness(JULIA_CATALOGUE_NORMALISED, spec_id="scatter-demo", enabled_libraries=["ggplot2"])
        assert blocked.status == "blocked" and blocked.reasons[0].startswith("library-disabled: makie")
        export = runtime.export("x = 1\n", spec_id="scatter-basic", library_version="0.24.16", theme="dark")
        assert export.startswith("# Adapted by anyplot.ai from scatter-basic (makie 0.24.16) for your data.csv;\n")
        assert "# run: ANYPLOT_THEME=dark julia --project=. plot.jl\n" in export

    def test_the_loader_reads_data_csv_typed_from_the_kinds(self) -> None:
        run_form = self.run_form()
        assert "load_user_data" not in run_form and "import CSV, DataFrames, Dates, TimeZones\n" in run_form
        assert '"Umsatz \\$ (k)" => Int64,' in run_form and '"Zeit" => String,' in run_form
        with pytest.raises(ValueError, match="no kind"):
            runtime_for("makie").loader_block(JULIA_WORKING, columns=["x"], dtypes={}, parse_dates=[], kinds={})

    def test_error_lines_are_the_working_forms(self) -> None:
        """The loader replaces one placeholder line with many; the summary takes them off again with the run form,
        and a line inside the loader is the placeholder's (J2a's finding, J2b)."""
        runtime = runtime_for("makie")
        run_form = self.run_form()
        working_lines, run_lines = JULIA_WORKING.splitlines(), run_form.splitlines()
        placeholder = working_lines.index("df = load_user_data()") + 1
        at_working = next(i for i, line in enumerate(working_lines, 1) if line.startswith("scatter!("))
        at_run = next(i for i, line in enumerate(run_lines, 1) if line.startswith("scatter!("))
        assert at_run - at_working > 20  # the timestamp loader is long

        def tail(line: int) -> str:
            return (
                "ERROR: LoadError: MethodError: no method matching scatter!(::Axis)\nStacktrace:\n"
                f" [1] top-level scope\n   @ /work/plot.jl:{line}\nin expression starting at /work/plot.jl:{line}\n"
            )

        assert (
            runtime.error_summary(tail(at_run), run_form=run_form) == f"MethodError for scatter!() at line {at_working}"
        )
        assert runtime.error_summary(tail(at_run)) == f"MethodError for scatter!() at line {at_run}"  # no run form
        inside = runtime.error_summary(tail(placeholder + 5), run_form=run_form)
        assert inside == f"MethodError for scatter!() at line {placeholder} (the data loader)"
        before = runtime.error_summary(tail(placeholder - 1), run_form=run_form)
        assert before == f"MethodError for scatter!() at line {placeholder - 1}"
        # Python and R take the run form and leave it unread: their summaries are as before.
        python_tail = 'Traceback (most recent call last):\n  File "plot.py", line 40, in <module>\nKeyError: "x"\n'
        assert runtime_for("matplotlib").error_summary(python_tail, run_form="x\n" * 50) == "KeyError at line 40"

    def test_loader_notes_count_the_timestamps_cut_to_the_millisecond_per_column(self) -> None:
        """Owner decision of 2026-10-29: Julia keeps milliseconds; the cut cells are announced with counts."""
        csv_text = (
            "Zeit,Start,n\n"
            "2024-01-31T08:00:00.123456,2024-01-31T08:00:00.120000,1\n"
            "2024-01-31T08:00:00.000001+01:00,2024-01-31 08:00:00.123456789Z,2\n"
            "2024-01-31T08:00:00.5,,3\n"
        )
        kinds = read_kinds(csv_text, {"Zeit": "datetime", "Start": "datetime", "n": "integer"})
        assert kinds.submillisecond == {"Zeit": 2, "Start": 1}
        line, shifted = runtime_for("makie").loader_notes(kinds)
        assert line == (
            "Julia keeps time to the millisecond, so the plot cuts the digits below it from 3 timestamps: "
            "2 in 'Zeit', 1 in 'Start'"
        )
        assert shifted.startswith("Julia converts 1 timestamp with a time-zone offset")  # the +01:00 cell; Z is UTC
        assert [note.split()[0] for note in runtime_for("ggplot2").loader_notes(kinds)] == ["R"]
        assert runtime_for("matplotlib").loader_notes(kinds) == []
        one = read_kinds("t\n2024-01-31T08:00:00.0000001\n", {"t": "datetime"})
        assert runtime_for("makie").loader_notes(one)[0].endswith("from 1 timestamp: 1 in 't'")
        whole = read_kinds("t,n\n2024-01-31T08:00:00.123,9007199254740993\n", {"t": "datetime", "n": "integer"})
        assert runtime_for("makie").loader_notes(whole) == []  # milliseconds fit; Julia reads every integer exactly

    def test_loader_notes_count_the_timestamps_read_in_utc_per_column(self) -> None:
        """Owner decision of 2026-10-30: R and Julia read a timestamp with an offset in UTC, so its clock time moves;
        the cells with an offset other than zero are announced with counts, in the same words for both."""
        csv_text = (
            "Ankunft,Abfahrt,Tag\n"
            "2024-01-31T08:00:00+01:00,2024-01-31 08:00-0500,2024-01-31\n"
            "2024-01-31T08:00:00.5-03:30,2024-01-31T08:00:00Z,2024-02-01\n"
            "2024-01-31T08:00:00+05,2024-01-31T08:00:00+00:00,\n"
            "2024-01-31T08:00:00,2024-01-31T08:00:00-00:00,2024-02-02\n"
        )
        kinds = read_kinds(csv_text, {"Ankunft": "datetime", "Abfahrt": "datetime", "Tag": "datetime"})
        assert kinds.offset == {"Ankunft": 3, "Abfahrt": 1}  # Z, ±00:00, no offset and plain dates keep their time
        expected = "converts 4 timestamps with a time-zone offset to UTC, so the plot shows their UTC clock time: "
        assert runtime_for("ggplot2").loader_notes(kinds) == [f"R {expected}3 in 'Ankunft', 1 in 'Abfahrt'"]
        assert runtime_for("makie").loader_notes(kinds) == [f"Julia {expected}3 in 'Ankunft', 1 in 'Abfahrt'"]
        assert runtime_for("matplotlib").loader_notes(kinds) == []  # pandas keeps the offset
        one = read_kinds("t\n2024-01-31T08:00:00+01:00\n", {"t": "datetime"})
        assert runtime_for("ggplot2").loader_notes(one) == [
            "R converts 1 timestamp with a time-zone offset to UTC, so the plot shows its UTC clock time: 1 in 't'"
        ]
        both = read_kinds("n,t\n9007199254740993,2024-01-31T08:00:00+01:00\n", {"n": "integer", "t": "datetime"})
        assert [note.split()[1] for note in runtime_for("ggplot2").loader_notes(both)] == ["reads", "converts"]

    def test_the_offset_note_is_a_change_note_and_names_what_fits(self) -> None:
        """The offset note's head is the longest of the loader notes: at the caps the first column still fits."""
        from agents.anyplot.schemas import MAX_CHANGE_CHARS, MAX_COLUMN_NAME_CHARS

        names = [chr(ord("a") + index) * MAX_COLUMN_NAME_CHARS for index in range(50)]
        cells = ",".join(["2024-01-31T08:00:00+01:00"] * 50)
        wide = read_kinds(",".join(names) + "\n" + cells + "\n", dict.fromkeys(names, "datetime"))
        for library in ("ggplot2", "makie"):
            (crowded,) = runtime_for(library).loader_notes(wide)
            assert len(crowded) <= MAX_CHANGE_CHARS and f"1 in '{names[0]}'" in crowded
            assert crowded.endswith(", and 49 more columns")

    def test_the_loader_note_is_a_change_note_and_names_what_fits(self) -> None:
        from agents.anyplot.schemas import MAX_CHANGE_CHARS, MAX_COLUMN_NAME_CHARS

        names = [chr(ord("a") + index) * MAX_COLUMN_NAME_CHARS for index in range(50)]
        cells = ",".join(["2024-01-31T08:00:00.1234"] * 50)
        wide = read_kinds(",".join(names) + "\n" + cells + "\n", dict.fromkeys(names, "datetime"))
        (crowded,) = runtime_for("makie").loader_notes(wide)
        assert len(crowded) <= MAX_CHANGE_CHARS and f"1 in '{names[0]}'" in crowded
        assert crowded.endswith(", and 49 more columns")

    def test_edits_literals_and_protected_lines_use_the_julia_dialect(self) -> None:
        runtime = runtime_for("makie")
        plan = AdaptPlan(edits=[Edit(find='title = "Umsatz nach Ausgaben"', replace='title = "Neuer Titel"')])
        applied = runtime.apply_plan(JULIA_WORKING, plan)
        assert applied.code is not None and 'title = "Neuer Titel"' in applied.code
        assert runtime.new_literals(JULIA_WORKING, applied.code) == ["Neuer Titel"]
        drifted = JULIA_WORKING.replace("px_per_unit = 2", "px_per_unit = 3")
        assert runtime.restore_protected(JULIA_WORKING, drifted) == JULIA_WORKING

    def test_the_command_is_the_renderers_julia_row_in_exec_mode(self) -> None:
        """The argv `executor.build_argv` runs after `sandbox do --`: the harness, `--exec --`, Julia's launcher."""
        from agents.renderer.commands import JULIA_BINARY, JULIA_FLAGS, command_for
        from agents.renderer.executor import ExecutorConfig, build_argv
        from agents.renderer.settings import RendererSettings

        local = runtime_for("makie").command("light")
        expected = ["--exec", "--", JULIA_BINARY, *JULIA_FLAGS, "plot.jl"]
        assert local[-len(expected) :] == expected
        config = ExecutorConfig.from_settings(RendererSettings())
        deployed = build_argv(config, "r-x", Path("/runs/x"), "light", 60, command=command_for("julia", "makie"))
        assert deployed[-len(expected) :] == expected

    def test_data_runs_and_conversions_stay_pythons(self) -> None:
        runtime, python = runtime_for("makie", cpu_seconds=45), PythonRuntime(cpu_seconds=45)
        assert runtime.data_command() == python.data_command() and runtime.data_env(20) == python.data_env(20)
        assert runtime.convert_command() == python.convert_command() and runtime.convert_env() == python.convert_env()

    def test_collect_reads_the_png_and_no_probe(self, tmp_path: Path) -> None:
        (tmp_path / "plot-dark.png").write_bytes(b"\x89PNG data")
        (tmp_path / "probe-dark.json").write_text('{"texts": []}')
        assert runtime_for("makie").collect(tmp_path, "dark") == (b"\x89PNG data", None)
        assert runtime_for("makie").collect(tmp_path, "light") == (None, None)


class TestJavaScriptRuntimeBindings:
    """The JavaScript runtime hands the pipeline the JavaScript code profile of JS-3 (step 3, JS-4a)."""

    def test_normalise_regions_security_and_adaptation_are_the_javascript_profiles(self) -> None:
        runtime = runtime_for("chartjs")
        assert runtime.normalise(JS_CATALOGUE, "chartjs") == JS_CATALOGUE_NORMALISED
        assert runtime.regions(JS_WORKING).placeholders
        assert runtime.security(JS_WORKING) == [] and runtime.validate(JS_WORKING, "chartjs") == []
        assert runtime.adaptation(JS_WORKING, original_palette=[]) == []
        assert "banned-name" in {f.rule for f in runtime.security('fetch("x");\n')}  # the JS profile, not a crash

    def test_an_import_the_image_lacks_is_a_blocking_adaptation_finding(self) -> None:
        """A MUI X 7 module fails the bundle step, so `unavailable-import` rejects the code before a render."""
        runtime = JavaScriptRuntime(library="muix")
        code = MUIX_WORKING.replace(
            'import Typography from "@mui/material/Typography";',
            'import Typography from "@mui/material/Typography";\n'
            'import { ChartContainer } from "@mui/x-charts/ChartContainer";',
        )
        assert runtime.security(code) == []
        rules = {f.rule for f in runtime.adaptation(code, original_palette=[])}
        assert "unavailable-import" in rules and rules <= runtime.blocking_rules

    def test_readiness_and_export_follow_the_javascript_profile(self) -> None:
        runtime = runtime_for("chartjs")
        readiness = runtime.readiness(JS_CATALOGUE_NORMALISED, spec_id="scatter-demo", enabled_libraries=["chartjs"])
        assert readiness.status in ("clean", "coupled")
        blocked = runtime.readiness(JS_CATALOGUE_NORMALISED, spec_id="scatter-demo", enabled_libraries=["d3"])
        assert blocked.status == "blocked" and blocked.reasons[0].startswith("library-disabled: chartjs")
        export = runtime.export("const x = 1;\n", spec_id="scatter-basic", library_version="4.5.1", theme="dark")
        assert export.startswith("// Adapted by anyplot.ai from scatter-basic (chartjs 4.5.1) for your data.csv;\n")
        assert (
            "// run: open plot.html in a browser, which runs this code with the chart library, the dark theme" in export
        )

    def test_the_loader_is_the_one_line_read_of_the_page_table(self) -> None:
        runtime = runtime_for("d3")
        run_form = runtime.loader_block(JS_WORKING, columns=["a"], dtypes={}, parse_dates=[], kinds={"a": "number"})
        assert run_form == JS_WORKING.replace("const data = loadUserData();", "const data = window.ANYPLOT_DATA;")
        assert len(run_form.splitlines()) == len(JS_WORKING.splitlines())
        with pytest.raises(ValueError, match="column types"):
            runtime.loader_block(JS_WORKING, columns=["a"], dtypes={}, parse_dates=[], kinds={})

    def test_data_json_is_the_typed_table_and_none_without_kinds(self) -> None:
        runtime = runtime_for("echarts")
        csv = "Tag,Wert,Gruppe\n2024-01-31,1.5,a\n,,b\n"
        kinds = read_kinds(csv, {"Tag": "datetime", "Wert": "number", "Gruppe": "text"}, ["Tag"])
        assert runtime.data_json(csv, kinds) == (
            '{"columns":["Tag","Wert","Gruppe"],"data":[["2024-01-31",1.5,"a"],[null,null,"b"]]}'
        )
        assert runtime.data_json(csv, None) is None
        # A timestamp that UTC moves before year 1 has no typed form: the pipeline drops the kinds, so the loader
        # refuses the run form with its reason instead of a page without a table (second opinion of 2026-10-30).
        early = "ts\n0001-01-01T00:30:00+01:00\n"
        with pytest.raises(ValueError):
            runtime.data_json(early, read_kinds(early, {"ts": "datetime"}, ["ts"]))
        assert runtime_for("matplotlib").data_json(csv, kinds) is None
        assert (
            runtime_for("ggplot2").data_json(csv, kinds) is None and runtime_for("makie").data_json(csv, kinds) is None
        )

    def test_a_render_job_carries_data_json_for_javascript_only(self) -> None:
        job = RenderJob("a" * 16, "javascript", "d3", "x", "a\n1\n", data_json='{"columns":["a"],"data":[[1]]}')
        assert job.data_json is not None
        with pytest.raises(ValueError, match="javascript job only"):
            RenderJob("a" * 16, "python", "matplotlib", "x", "a\n1\n", data_json="{}")

    @pytest.mark.parametrize("library", ["ggplot2", "makie", "chartjs"])
    @pytest.mark.parametrize("columns", [1, 2, 50])
    def test_every_loader_note_fits_a_change_note_at_the_limits(self, library: str, columns: int) -> None:
        """64-character column names (`MAX_COLUMN_NAME_CHARS`) at 20,000 cells each (`MAX_ROWS`): the head grows with
        the total and the language's name, so the first column's name is cut with an ellipsis where it must be;
        JavaScript's heads reached 201 to 208 characters before (second opinion of 2026-10-30)."""
        from agents.anyplot.schemas import MAX_CHANGE_CHARS, MAX_COLUMN_NAME_CHARS, MAX_ROWS

        counts = {f"{index:02d}".ljust(MAX_COLUMN_NAME_CHARS, "x"): MAX_ROWS for index in range(columns)}
        notes = runtime_for(library).loader_notes(
            ColumnKinds(kinds={}, inexact=counts, submillisecond=counts, offset=counts)
        )
        assert notes and all(len(note) <= MAX_CHANGE_CHARS for note in notes), [len(note) for note in notes]
        assert all("20,000 in '00" in note for note in notes)

    def test_loader_notes_count_what_the_typing_changes_per_column(self) -> None:
        """Integers past ±2^53, timestamps cut to the millisecond and timestamps converted to UTC, each one change
        note with its counts (owner rule of 2026-10-15), in that order; none for a table it reads exactly."""
        runtime = runtime_for("highcharts")
        kinds = ColumnKinds(
            kinds={}, inexact={"Kunden-ID": 2}, submillisecond={"Zeit": 3, "Ende": 1}, offset={"Zeit": 4}
        )
        assert runtime.loader_notes(kinds) == [
            "JavaScript reads 2 integers past ±2^53 as the nearest double, so the plot can show them a unit or more "
            "off: 2 in 'Kunden-ID'",
            "JavaScript keeps time to the millisecond, so the plot cuts the digits below it from 4 timestamps: "
            "3 in 'Zeit', 1 in 'Ende'",
            "JavaScript converts 4 timestamps with a time-zone offset to UTC, so the plot shows their UTC clock time: "
            "4 in 'Zeit'",
        ]
        assert runtime.loader_notes(ColumnKinds(kinds={})) == []

    def test_error_lines_name_the_loader_and_drop_the_wrapper(self) -> None:
        """The run form's loader is one line for one line, so a line maps to itself; a line on the loader is the data
        loader's, and a line past the code's end (a thrown value that is no `Error`) is the harness's wrapper."""
        runtime = runtime_for("chartjs")
        run_form = runtime.loader_block(JS_WORKING, columns=["a"], dtypes={}, parse_dates=[], kinds={"a": "number"})
        loader = run_form.splitlines().index("const data = window.ANYPLOT_DATA;") + 1
        tail = "console: 2 errors\nrender: error: page TypeError plot.js:{line}: x is undefined\n"
        assert runtime.error_summary(tail.format(line=20), run_form=run_form) == "TypeError at line 20"
        assert (
            runtime.error_summary(tail.format(line=loader), run_form=run_form)
            == f"TypeError at line {loader} (the data loader)"
        )
        past = len(run_form.splitlines()) + 3
        assert runtime.error_summary(tail.format(line=past), run_form=run_form) == "TypeError"
        assert runtime.error_summary(tail.format(line=past)) == f"TypeError at line {past}"

    def test_edits_literals_and_protected_lines_use_the_javascript_dialect(self) -> None:
        runtime = runtime_for("chartjs")
        plan = AdaptPlan(edits=[Edit(find='text: "Umsatz nach Ausgaben"', replace='text: "Neuer Titel"')])
        applied = runtime.apply_plan(JS_WORKING, plan)
        assert applied.code is not None and 'text: "Neuer Titel"' in applied.code
        assert runtime.new_literals(JS_WORKING, applied.code) == ["Neuer Titel"]
        drifted = JS_WORKING.replace('isDark ? "#A8A79F" : "#6B6A63"', 'isDark ? "#000000" : "#6B6A63"')
        assert drifted != JS_WORKING and runtime.restore_protected(JS_WORKING, drifted) == JS_WORKING

    def test_the_command_is_the_renderers_javascript_row_in_exec_mode(self) -> None:
        """The argv `executor.build_argv` runs after `sandbox do --`: the harness, `--exec --`, Node and render.mjs."""
        from agents.renderer.commands import JS_HARNESS, NODE_BINARY, command_for
        from agents.renderer.executor import ExecutorConfig, build_argv
        from agents.renderer.settings import RendererSettings

        local = runtime_for("echarts").command("light")
        expected = ["--exec", "--", NODE_BINARY, JS_HARNESS, "--library=echarts", "plot.js"]
        assert local[-len(expected) :] == expected
        config = ExecutorConfig.from_settings(RendererSettings())
        deployed = build_argv(
            config, "r-x", Path("/runs/x"), "light", 60, command=command_for("javascript", "echarts"), data_json=True
        )
        assert deployed[-len(expected) :] == expected

    async def test_the_theme_toggle_renders_the_other_theme_from_the_stored_table(self) -> None:
        """A version keeps its typed table, so the other theme renders from the same job as the first (Gemini's
        point about `theme_render.py` in the second opinion of 2026-10-30)."""
        from agents.anyplot.render.backends.fake import FakeBackend
        from agents.anyplot.schemas import PlotResult
        from agents.anyplot.services import CodeVersion, Services
        from agents.anyplot.theme_render import render_theme

        backend = FakeBackend()
        services = Services(backend_factory=lambda: backend)
        table = '{"columns":["a"],"data":[[1]]}'
        version = CodeVersion(
            number=1,
            working="",
            run_form="const data = window.ANYPLOT_DATA;\n",
            export="",
            data_csv="a\n1\n",
            data_json=table,
            render_id=services.renders.put("s1", {"light": b"\x89PNG"}),
            result=PlotResult(status="ok", attempts=1, artifacts=["plot-light.png", "plot.js", "data.csv"]),
            library="d3",
            code_artifact="plot.js",
        )

        await render_theme(services, AgentSettings(), "s1", version, "dark")

        job = backend.jobs[-1]
        assert (job.language, job.library, job.themes) == ("javascript", "d3", ("dark",))
        assert job.data_json == table and job.source == version.run_form

    def test_data_runs_and_conversions_stay_pythons(self) -> None:
        runtime, python = runtime_for("d3", cpu_seconds=45), PythonRuntime(cpu_seconds=45)
        assert runtime.data_command() == python.data_command() and runtime.data_env(20) == python.data_env(20)
        assert runtime.convert_command() == python.convert_command() and runtime.convert_env() == python.convert_env()

    def test_collect_reads_the_png_and_no_probe(self, tmp_path: Path) -> None:
        (tmp_path / "plot-dark.png").write_bytes(b"\x89PNG data")
        (tmp_path / "probe-dark.json").write_text('{"texts": []}')
        assert runtime_for("d3").collect(tmp_path, "dark") == (b"\x89PNG data", None)
        assert runtime_for("d3").collect(tmp_path, "light") == (None, None)


class TestRowEnvironment:
    """The local Docker backend renders with the library's command row as the renderer's `sandbox_env` does (1c)."""

    @pytest.mark.parametrize("library", sorted(RUNTIME_LIBRARIES))
    def test_the_render_env_is_the_renderers_key_for_key(self, library: str) -> None:
        """The deployed `sandbox_env` of the library's row, but for the two paths of the image's font cache, which a
        local render names as the image does, and the process limit, which the container's `--pids-limit` replaces
        (`PythonRuntime.env`, `RRuntime.env`): the PATH the delegate check reads, the file size, the threads and every
        row value, R's own variables and the exec filter's switch included."""
        from agents.renderer.commands import command_for
        from agents.renderer.executor import SANDBOX_PATH, ExecutorConfig, sandbox_env
        from agents.renderer.settings import RendererSettings

        row = command_for(language_of(library), library)
        local = runtime_for(library, cpu_seconds=60).env("dark")
        deployed = sandbox_env(ExecutorConfig.from_settings(RendererSettings()), "dark", 60, command=row)
        own_paths = {"MPLCONFIGDIR", "ANYPLOT_MPL_SEED"}
        deployed.pop("ANYPLOT_RLIMIT_NPROC", None)

        assert set(local) == set(deployed)
        assert {key: value for key, value in local.items() if key not in own_paths} == {
            key: value for key, value in deployed.items() if key not in own_paths
        }
        assert local["PATH"] == SANDBOX_PATH and "ANYPLOT_RLIMIT_NPROC" not in local
        assert ("ANYPLOT_RLIMIT_AS_MB" in local) is row.rlimit_as  # altair's V8 runs without one

    def test_the_deployed_limits_are_the_renderers_defaults(self) -> None:
        from agents.anyplot.render.runtimes.python import DATA_RLIMIT_AS_MB, DATA_RLIMIT_NPROC, RENDER_RLIMIT_FSIZE_MB
        from agents.renderer.settings import RendererSettings

        deployed = RendererSettings()
        assert (DATA_RLIMIT_AS_MB, DATA_RLIMIT_NPROC, RENDER_RLIMIT_FSIZE_MB) == (
            deployed.rlimit_as_mb,
            deployed.rlimit_nproc,
            deployed.rlimit_fsize_mb,
        )

    def test_lets_plot_gets_its_allocator_fontconfig_and_limit_locally(self) -> None:
        env = runtime_for("letsplot", cpu_seconds=45).env("light")
        assert env["ARROW_DEFAULT_MEMORY_POOL"] == "system" and env["FONTCONFIG_FILE"] == "/opt/anyplot/fonts.conf"
        assert env["ANYPLOT_RLIMIT_AS_MB"] == "2048" and env["ANYPLOT_RLIMIT_CPU_S"] == "45"

    def test_every_local_run_requires_the_exec_filter_as_the_renderer_does(self) -> None:
        """Renders, data runs and conversions in the local Docker backend, as the deployed `RENDERER_EXEC_DENY`."""
        from agents.renderer.commands import EXEC_DENY_ENV
        from agents.renderer.settings import RendererSettings

        runtime = runtime_for("matplotlib")
        assert RendererSettings().exec_deny == "required"
        assert {
            runtime.env("dark")[EXEC_DENY_ENV],
            runtime.data_env()[EXEC_DENY_ENV],
            runtime.convert_env()[EXEC_DENY_ENV],
        } == {"required"}

    def test_a_runtime_without_a_library_renders_as_matplotlib(self) -> None:
        assert PythonRuntime().env("light") == runtime_for("matplotlib").env("light")
