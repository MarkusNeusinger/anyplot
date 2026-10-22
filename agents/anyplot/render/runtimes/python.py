"""The Python runtime (matplotlib and seaborn in phase 1).

The command is the catalogue's CI render command (`MPLBACKEND=Agg
ANYPLOT_THEME=<theme> python plot.py`) with the isolated interpreter and the probe
harness in front. The environment is complete, never inherited: the theme, the Agg
backend, a writable matplotlib cache and `HOME` under `/tmp` (the root filesystem is
read-only), and the harness's resource limits.

`normalise`, `loader_block` and `validate` are the deterministic code modules in
`agents/anyplot/code/`; this class only binds them to the runtime interface.
"""

import json
from pathlib import Path
from typing import Any

from agents.renderer.wire import run_cpu_seconds

from ...code.loader import to_run_form
from ...code.normalise import normalise
from ...code.validate import validate_security
from ..contract import Theme
from ..harness import CONVERT_FLAG, DATA_FLAG
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

    def __init__(
        self,
        *,
        python: str = IMAGE_PYTHON,
        harness: str = IMAGE_HARNESS,
        cpu_seconds: int = 60,
        mplconfig: str = "/tmp/mplconfig",
    ) -> None:
        self.python = python
        self.harness = harness
        self.cpu_seconds = cpu_seconds
        self.mplconfig = mplconfig

    def command(self, theme: Theme) -> list[str]:
        return [self.python, "-I", self.harness, self.file_name]

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
        return [self.python, "-I", self.harness, DATA_FLAG, DATA_FILE_NAME]

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
        return [self.python, "-I", self.harness, CONVERT_FLAG, CONVERT_INPUT_NAME]

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
