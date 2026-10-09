"""The render contract: what a render job is, what comes back, and the two protocols around it.

A `RenderJob` carries the run form of one code version, the canonical `data.csv` and
the themes to render (a pipeline run asks for one, the theme toggle for the other);
a `RenderBackend` runs it once per theme in isolation and returns raw outputs (exit
status, the PNG bytes as written, the savefig probe, a stderr tail). The host gates
(`gates.py`) judge those outputs; the backend never does.

A `RuntimeAdapter` describes one language runtime: the file name the code is written
to, the command (the CI command, with the probe harness in front for Python), the
environment per theme, and the code transforms the pipeline applies before a render
(`normalise`, `loader_block`, `validate`). Phase 1 has one runtime (Python, for
matplotlib and seaborn, `runtimes/python.py`); later languages add runtimes, not
backends.

No ADK import: the render layer is plain code.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from ..schemas import RENDER_ID_PATTERN, Theme


THEMES: tuple[Theme, Theme] = ("light", "dark")
"""Every theme, in the order artifacts and reviewer images are listed."""
MAX_STDERR_CHARS = 2_000
_RENDER_ID = re.compile(RENDER_ID_PATTERN)


class RendererUnavailable(RuntimeError):
    """The backend cannot run at all here (no Docker, production refusal, not built yet)."""


@dataclass(frozen=True)
class RenderJob:
    """One code version to render in every theme of `themes`."""

    job_id: str
    language: str
    library: str
    source: str
    data_csv: str
    themes: tuple[Theme, ...] = THEMES
    timeout_s: float = 60.0

    def __post_init__(self) -> None:
        if not _RENDER_ID.fullmatch(self.job_id):
            raise ValueError("job_id must match the render id pattern")
        if not self.themes or any(theme not in THEMES for theme in self.themes):
            raise ValueError("themes must be light and/or dark")
        if self.timeout_s <= 0:
            raise ValueError("timeout_s must be positive")


@dataclass
class ThemeOutput:
    """What one theme's run left behind, before any gate looked at it."""

    theme: Theme
    exit_code: int | None
    timed_out: bool = False
    png: bytes | None = None
    probe: dict[str, Any] | None = None
    stderr_tail: str = ""
    wall_s: float = 0.0

    def __post_init__(self) -> None:
        self.stderr_tail = self.stderr_tail[-MAX_STDERR_CHARS:]


@dataclass
class RenderResult:
    """The raw outputs of every theme of one job."""

    job_id: str
    outputs: dict[Theme, ThemeOutput] = field(default_factory=dict)


class RenderBackend(Protocol):
    """Runs a job's code once per theme in isolation and collects the raw outputs."""

    name: str

    async def render(self, job: RenderJob) -> RenderResult: ...


class RuntimeAdapter(Protocol):
    """One language runtime: how its code is written, run, prepared and collected."""

    language: str
    file_name: str

    def command(self, theme: Theme) -> list[str]:
        """The argv that renders the code file in the work directory (never a shell string)."""
        ...

    def env(self, theme: Theme) -> dict[str, str]:
        """The complete environment of one theme's run; nothing is inherited."""
        ...

    def normalise(self, code: str, library: str) -> str:
        """The canvas and catalogue-header normaliser of this runtime."""
        ...

    def loader_block(self, working: str, *, columns: list[str], dtypes: dict[str, str], parse_dates: list[str]) -> str:
        """The working form with its data placeholder replaced by the `data.csv` loader."""
        ...

    def validate(self, code: str, library: str) -> list[str]:
        """SECURITY findings on code, one line each; empty when the code may run."""
        ...

    def collect(self, run_dir: Path, theme: Theme) -> tuple[bytes | None, dict[str, Any] | None]:
        """The PNG and the probe one theme's run left in `run_dir`, read without following links."""
        ...
