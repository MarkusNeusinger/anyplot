"""The runtime registry (agents/anyplot/render/runtimes): a library's runtime, and what it binds."""

from pathlib import Path

import pytest

from agents.anyplot.code import edits
from agents.anyplot.code.normalise import SUPPORTED_LIBRARIES as NORMALISED_LIBRARIES
from agents.anyplot.code.profiles.r import regions as r_regions
from agents.anyplot.code.regions import PLACEHOLDER
from agents.anyplot.data.kinds import read_kinds
from agents.anyplot.render.contract import BLOCKING_RULES
from agents.anyplot.render.runtimes import (
    PYTHON_LIBRARIES,
    R_LIBRARIES,
    RUNTIME_CLASSES,
    RUNTIME_LIBRARIES,
    PythonRuntime,
    RRuntime,
    has_runtime,
    language_of,
    runtime_for,
)
from agents.anyplot.render.runtimes.python import ADAPTATION_TARGETS as PYTHON_TARGETS
from agents.anyplot.schemas import CODE_ARTIFACTS, AdaptPlan, Edit
from agents.anyplot.settings import AgentSettings
from core.constants import SUPPORTED_LIBRARIES
from tests.unit.agents.code.conftest import R_CATALOGUE, R_CATALOGUE_NORMALISED


class TestRegistry:
    def test_the_registry_serves_the_python_and_the_r_libraries(self) -> None:
        assert PYTHON_LIBRARIES == NORMALISED_LIBRARIES
        assert PYTHON_LIBRARIES == {"matplotlib", "seaborn", "plotnine", "altair", "pygal", "letsplot"}
        assert R_LIBRARIES == edits.R_LIBRARIES == {"ggplot2"}
        assert RUNTIME_LIBRARIES == PYTHON_LIBRARIES | R_LIBRARIES <= SUPPORTED_LIBRARIES
        assert {language_of(library) for library in RUNTIME_LIBRARIES} == set(RUNTIME_CLASSES) == {"python", "r"}

    @pytest.mark.parametrize("library", sorted(PYTHON_LIBRARIES))
    def test_a_python_runtime_is_bound_to_its_library(self, library: str) -> None:
        runtime = runtime_for(library, cpu_seconds=45)
        assert isinstance(runtime, PythonRuntime)
        assert runtime.library == library and runtime.language == "python" == language_of(library)
        assert runtime.file_name == "plot.py" and runtime.code_artifact == "plot.py" in CODE_ARTIFACTS
        assert runtime.placeholder == PLACEHOLDER and runtime.cpu_seconds == 45 and runtime.render_p95_s == 15.0
        assert runtime.blocking_rules == BLOCKING_RULES and runtime.adaptation_targets == PYTHON_TARGETS
        assert has_runtime(library)

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
        assert has_runtime("ggplot2")
        with pytest.raises(ValueError, match="python library"):
            RRuntime(library="matplotlib")

    def test_a_library_without_a_runtime_is_refused_but_known(self) -> None:
        assert language_of("makie") == "julia" and not has_runtime("makie")
        with pytest.raises(ValueError, match="no runtime for 'makie'"):
            runtime_for("makie")
        with pytest.raises(ValueError, match="unknown library"):
            language_of("excel")

    def test_the_settings_accept_ggplot2_and_refuse_a_library_the_registry_does_not_serve(self) -> None:
        assert AgentSettings(libraries=["matplotlib", "ggplot2"]).libraries == ["matplotlib", "ggplot2"]
        with pytest.raises(ValueError, match="no runtime"):
            AgentSettings(libraries=["matplotlib", "makie"])


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
        assert line.startswith("R reads 3 integers beyond ±2^53 (9,007,199,254,740,992) as the nearest double")
        assert "2 in 'id', 1 in 'code'" in line and "read such a column as text" in line
        assert runtime_for("matplotlib").loader_notes(kinds) == []
        assert runtime_for("ggplot2").loader_notes(read_kinds("n\n1\n", {"n": "integer"})) == []

    def test_loader_notes_name_at_most_five_columns(self) -> None:
        header = ",".join(f"c{index}" for index in range(7))
        csv_text = header + "\n" + ",".join(["9007199254740993"] * 7) + "\n"
        kinds = read_kinds(csv_text, {f"c{index}": "integer" for index in range(7)})
        (line,) = runtime_for("ggplot2").loader_notes(kinds)
        assert line.startswith("R reads 7 integers") and "1 in 'c4', and 2 more columns;" in line
        one = read_kinds("id\n9007199254740993\n", {"id": "integer"})
        assert runtime_for("ggplot2").loader_notes(one)[0].startswith("R reads 1 integer beyond")

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
