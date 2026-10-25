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
        assert RUNTIME_LIBRARIES == PYTHON_LIBRARIES == NORMALISED_LIBRARIES == {"matplotlib", "seaborn"}
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
