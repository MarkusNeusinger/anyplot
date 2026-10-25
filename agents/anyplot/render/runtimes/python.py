"""The Python runtime (matplotlib and seaborn in phase 1).

The command is the catalogue's CI render command (`MPLBACKEND=Agg
ANYPLOT_THEME=<theme> python plot.py`) with the isolated interpreter (no remote
debugging either, `harness.INTERPRETER_FLAGS`) and the probe harness in front. The environment is complete, never inherited: the theme, the Agg
backend, a writable matplotlib cache and `HOME` under `/tmp` (the root filesystem is
read-only), and the harness's resource limits.

`normalise`, `loader_block`, `validate` and the rest (`regions`, `readiness`, `security`,
`adaptation`, `apply_plan`, `restore_protected`, `new_literals`, `error_summary`, `export`)
are the deterministic code modules in `agents/anyplot/code/` and the error grammar of
`render/gates.py`; this class only binds them to the runtime interface, for one library.
"""

import json
from pathlib import Path
from typing import Any

from agents.renderer.wire import run_cpu_seconds

from ...code.edits import AppliedPlan, apply_plan, new_literals, restore_protected
from ...code.export import export_code
from ...code.loader import to_run_form
from ...code.normalise import normalise
from ...code.readiness import Readiness, scan
from ...code.regions import PLACEHOLDER, Regions, find_regions
from ...code.validate import Finding, validate_adaptation, validate_security
from ...schemas import AdaptPlan, CodeArtifact
from ..contract import Theme
from ..gates import error_summary
from ..harness import CONVERT_FLAG, DATA_FLAG, INTERPRETER_FLAGS
from ..png import MAX_PNG_BYTES, MAX_PROBE_BYTES, read_output


IMAGE_PYTHON = "/app/.venv/bin/python"
IMAGE_HARNESS = "/opt/anyplot/harness.py"
MPL_SEED = "/opt/mplconfig"
HARNESS_SOURCE = Path(__file__).resolve().parents[1] / "harness.py"
IMAGE_CONVERTER = "/opt/anyplot/convert.py"
CONVERTER_SOURCE = HARNESS_SOURCE.with_name("convert.py")
CONVERT_INPUT_NAME = "input.bin"
"""A conversion's file (the renderer's `wire.CONVERT_INPUT_FILE`)."""
DATA_FILE_NAME = "snippet.py"
"""A data run's code file (the renderer's `executor.SNIPPET_FILE`); `gates.error_summary` finds its frames by it."""
DATA_RLIMIT_AS_MB = 1024
DATA_RLIMIT_NPROC = 64
"""The renderer's deployed `RENDERER_RLIMIT_AS_MB` and `RENDERER_RLIMIT_NPROC` (pinned by a test), which the local
backend's data runs apply as well."""


class PythonRuntime:
    """matplotlib and seaborn code, run as `plot.py` under the probe harness."""

    language = "python"
    file_name = "plot.py"
    code_artifact: CodeArtifact = "plot.py"
    """The name the exported code downloads under (`schemas.CodeArtifact`)."""
    placeholder = PLACEHOLDER
    """The working form's data placeholder, which the loader replaces."""

    def __init__(
        self,
        *,
        library: str = "matplotlib",
        python: str = IMAGE_PYTHON,
        harness: str = IMAGE_HARNESS,
        cpu_seconds: int = 60,
        mplconfig: str = "/tmp/mplconfig",
        render_p95_s: float = 15.0,
    ) -> None:
        self.library = library
        self.python = python
        self.harness = harness
        self.cpu_seconds = cpu_seconds
        self.mplconfig = mplconfig
        self.render_p95_s = render_p95_s
        """Seconds a repair attempt's render is budgeted at against the soft deadline (`commands.py`)."""

    def command(self, theme: Theme) -> list[str]:
        return [self.python, *INTERPRETER_FLAGS, self.harness, self.file_name]

    def env(self, theme: Theme) -> dict[str, str]:
        return {
            "ANYPLOT_THEME": theme,
            "MPLBACKEND": "Agg",
            "MPLCONFIGDIR": self.mplconfig,
            # The renderer image's baked font cache; the harness copies it into
            # MPLCONFIGDIR and skips the copy where the directory does not exist.
            "ANYPLOT_MPL_SEED": MPL_SEED,
            "HOME": "/tmp",
            "PYTHONDONTWRITEBYTECODE": "1",
            "ANYPLOT_RLIMIT_CPU_S": str(self.cpu_seconds),
        }

    def data_command(self) -> list[str]:
        return [self.python, *INTERPRETER_FLAGS, self.harness, DATA_FLAG, DATA_FILE_NAME]

    def data_env(self, timeout_s: float | None = None) -> dict[str, str]:
        """A data run's environment: the renderer's `sandbox_env` limits for a data run, address space and processes
        included (inside Docker `RLIMIT_NPROC` counts the user's processes on the host, which one BLAS thread keeps
        far below the limit). With the run's `timeout_s`, the CPU cap is clamped to it as the renderer's executor
        clamps it (`wire.run_cpu_seconds`): a 20-second data run gets 20 CPU seconds, not the render's 60."""
        cpu_seconds = self.cpu_seconds if timeout_s is None else run_cpu_seconds(self.cpu_seconds, timeout_s)
        return {
            "HOME": "/tmp",
            "PYTHONDONTWRITEBYTECODE": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "ANYPLOT_RLIMIT_CPU_S": str(cpu_seconds),
            "ANYPLOT_RLIMIT_AS_MB": str(DATA_RLIMIT_AS_MB),
            "ANYPLOT_RLIMIT_NPROC": str(DATA_RLIMIT_NPROC),
        }

    def convert_command(self) -> list[str]:
        """A conversion: the harness in convert mode on the file written as `input.bin`."""
        return [self.python, *INTERPRETER_FLAGS, self.harness, CONVERT_FLAG, CONVERT_INPUT_NAME]

    def convert_env(self) -> dict[str, str]:
        """A data run's environment, with Arrow's system allocator (the renderer's `sandbox_env` for a conversion)."""
        return {**self.data_env(), "ARROW_DEFAULT_MEMORY_POOL": "system"}

    def normalise(self, code: str, library: str) -> str:
        return normalise(code, library=library)

    def loader_block(self, working: str, *, columns: list[str], dtypes: dict[str, str], parse_dates: list[str]) -> str:
        return to_run_form(working, columns=columns, dtypes=dtypes, parse_dates=parse_dates)

    def validate(self, code: str, library: str) -> list[str]:
        return [f"{finding.rule}: {finding.message}" for finding in validate_security(code, library=library)]

    def collect(self, run_dir: Path, theme: Theme) -> tuple[bytes | None, dict[str, Any] | None]:
        png = read_output(run_dir / f"plot-{theme}.png", MAX_PNG_BYTES)
        probe: dict[str, Any] | None = None
        try:
            raw = read_output(run_dir / f"probe-{theme}.json", MAX_PROBE_BYTES)
            loaded = json.loads(raw) if raw else None
            probe = loaded if isinstance(loaded, dict) else None
        except ValueError, OSError:
            probe = None  # the probe is advisory; a broken one is simply absent
        return png, probe

    # The code conventions of the language, for the pipeline (`agents/anyplot/code/`).

    def regions(self, code: str) -> Regions:
        return find_regions(code)

    def readiness(self, normalised: str, *, spec_id: str, enabled_libraries: list[str]) -> Readiness:
        return scan(normalised, spec_id=spec_id, library=self.library, enabled_libraries=enabled_libraries)

    def security(self, code: str) -> list[Finding]:
        return validate_security(code, library=self.library)

    def adaptation(self, code: str, *, original_palette: list[str]) -> list[Finding]:
        return validate_adaptation(code, original_palette=original_palette)

    def apply_plan(self, working: str, plan: AdaptPlan) -> AppliedPlan:
        return apply_plan(working, plan)

    def restore_protected(self, base: str, code: str) -> str | None:
        return restore_protected(base, code)

    def new_literals(self, base: str, code: str) -> list[str]:
        return new_literals(base, code)

    def error_summary(self, stderr_tail: str) -> str:
        """The exception class and the `plot.py` line of a failed render, never the message (`gates.error_summary`)."""
        return error_summary(stderr_tail, code_file=self.file_name)

    def export(self, run_form: str, *, spec_id: str, library_version: str | None, theme: str = "light") -> str:
        return export_code(
            run_form, spec_id=spec_id, library=self.library, library_version=library_version, theme=theme
        )
