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

from ...code.loader import to_run_form
from ...code.normalise import normalise
from ...code.validate import validate_security
from ..contract import Theme
from ..png import MAX_PNG_BYTES, MAX_PROBE_BYTES, read_output


IMAGE_PYTHON = "/app/.venv/bin/python"
IMAGE_HARNESS = "/opt/anyplot/harness.py"
HARNESS_SOURCE = Path(__file__).resolve().parents[1] / "harness.py"


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
            "HOME": "/tmp",
            "PYTHONDONTWRITEBYTECODE": "1",
            "ANYPLOT_RLIMIT_CPU_S": str(self.cpu_seconds),
        }

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
        except (ValueError, OSError):
            probe = None  # the probe is advisory; a broken one is simply absent
        return png, probe
