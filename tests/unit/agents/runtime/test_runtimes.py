"""The runtime registry (agents/anyplot/render/runtimes): a library's runtime, and what it binds."""

import pytest

from agents.anyplot.code.normalise import SUPPORTED_LIBRARIES as NORMALISED_LIBRARIES
from agents.anyplot.code.regions import PLACEHOLDER
from agents.anyplot.render.runtimes import (
    PYTHON_LIBRARIES,
    RUNTIME_LIBRARIES,
    PythonRuntime,
    has_runtime,
    language_of,
    runtime_for,
)
from agents.anyplot.schemas import CODE_ARTIFACTS
from agents.anyplot.settings import AgentSettings
from core.constants import SUPPORTED_LIBRARIES


class TestRegistry:
    def test_the_registry_serves_exactly_the_normalised_python_libraries(self) -> None:
        assert RUNTIME_LIBRARIES == PYTHON_LIBRARIES == NORMALISED_LIBRARIES
        assert PYTHON_LIBRARIES == {"matplotlib", "seaborn", "plotnine", "altair", "pygal", "letsplot"}
        assert RUNTIME_LIBRARIES <= SUPPORTED_LIBRARIES

    @pytest.mark.parametrize("library", sorted(RUNTIME_LIBRARIES))
    def test_a_runtime_is_bound_to_its_library(self, library: str) -> None:
        runtime = runtime_for(library, cpu_seconds=45)
        assert isinstance(runtime, PythonRuntime)
        assert runtime.library == library and runtime.language == "python" == language_of(library)
        assert runtime.file_name == "plot.py" and runtime.code_artifact == "plot.py" in CODE_ARTIFACTS
        assert runtime.placeholder == PLACEHOLDER and runtime.cpu_seconds == 45 and runtime.render_p95_s == 15.0
        assert has_runtime(library)

    def test_a_library_without_a_runtime_is_refused_but_known(self) -> None:
        assert language_of("ggplot2") == "r" and not has_runtime("ggplot2")
        with pytest.raises(ValueError, match="no runtime for 'ggplot2'"):
            runtime_for("ggplot2")
        with pytest.raises(ValueError, match="unknown library"):
            language_of("excel")

    def test_the_settings_refuse_a_library_the_registry_does_not_serve(self) -> None:
        with pytest.raises(ValueError, match="no runtime"):
            AgentSettings(libraries=["matplotlib", "ggplot2"])


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


class TestRowEnvironment:
    """The local Docker backend renders with the library's command row as the renderer's `sandbox_env` does (1c)."""

    @pytest.mark.parametrize("library", sorted(RUNTIME_LIBRARIES))
    def test_the_render_env_carries_the_row_env_and_its_own_limit(self, library: str) -> None:
        from agents.renderer.commands import command_for
        from agents.renderer.executor import ExecutorConfig, sandbox_env
        from agents.renderer.settings import RendererSettings

        row = command_for("python", library)
        local = runtime_for(library).env("dark")
        deployed = sandbox_env(ExecutorConfig.from_settings(RendererSettings()), "dark", 60, command=row)
        for key, value in row.env.items():
            assert local[key] == deployed[key] == value, key
        if row.rlimit_as_mb is not None:
            assert local["ANYPLOT_RLIMIT_AS_MB"] == deployed["ANYPLOT_RLIMIT_AS_MB"] == str(row.rlimit_as_mb)
        else:
            assert "ANYPLOT_RLIMIT_AS_MB" not in local  # a local render keeps no configured limit, as before 1c
        assert local["ANYPLOT_THEME"] == "dark" and local["MPLBACKEND"] == "Agg" and local["HOME"] == "/tmp"

    def test_lets_plot_gets_its_allocator_fontconfig_and_limit_locally(self) -> None:
        env = runtime_for("letsplot", cpu_seconds=45).env("light")
        assert env["ARROW_DEFAULT_MEMORY_POOL"] == "system" and env["FONTCONFIG_FILE"] == "/opt/anyplot/fonts.conf"
        assert env["ANYPLOT_RLIMIT_AS_MB"] == "2048" and env["ANYPLOT_RLIMIT_CPU_S"] == "45"

    def test_the_other_python_libraries_keep_the_render_env_they_had(self) -> None:
        keys = {
            "ANYPLOT_THEME",
            "MPLBACKEND",
            "MPLCONFIGDIR",
            "ANYPLOT_MPL_SEED",
            "HOME",
            "PYTHONDONTWRITEBYTECODE",
            "ANYPLOT_RLIMIT_CPU_S",
        }
        for library in ("matplotlib", "seaborn", "plotnine", "altair", "pygal"):
            assert set(runtime_for(library).env("light")) == keys, library
        assert set(PythonRuntime().env("light")) == keys
