"""The render contract: what a render job is, what comes back, and the two protocols around it.

A `RenderJob` carries the run form of one code version, the canonical `data.csv` and
the themes to render (a pipeline run asks for one, the theme toggle for the other);
a `RenderBackend` runs it once per theme in isolation and returns raw outputs (exit
status, the PNG bytes as written, the savefig probe, a stderr tail). The host gates
(`gates.py`) judge those outputs; the backend never does.

A `DataJob` is a data-generating snippet (`run_data_code`); `run_data` runs it once in
the same isolation and returns the harness's exit code and the `out.csv` it wrote
(`DataOutput`). A backend that cannot (a renderer deployed before `POST /run-data`)
raises `DataRunUnsupported`.

A `ConvertJob` is a binary data file (Excel, OpenDocument, Parquet, Feather, Arrow,
NumPy) the page dropped; `convert` reads it in the same isolation with the harness in
convert mode and returns the CSV text (or JSON records) for the paste box
(`ConvertOutput`). A backend without conversions raises `DataRunUnsupported` too.

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

from agents.renderer.wire import ConvertMeta

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
    reason: str | None = None
    """Why a renderer stopped or refused the run when it knows more than the exit code (the
    `remote` backend's `RunReason`: `disk_budget`, `file_budget`, `memory`, `output_rejected`,
    `timeout`); R1 turns it into a line that names the limit."""
    measured: int | None = None
    """The value that broke the limit (bytes, entries or MiB of `MemAvailable`, by `reason`)."""
    limit: int | None = None
    """The limit `measured` broke, in the same unit."""
    max_rss_mb: float | None = None
    """The harness's peak memory from its closing `HARNESS` line, when the backend reports it (`remote`).
    Advisory: the code under test shares stdout and can forge the line."""
    cpu_s: float | None = None
    """The harness's CPU seconds from the same line, equally advisory."""

    def __post_init__(self) -> None:
        self.stderr_tail = self.stderr_tail[-MAX_STDERR_CHARS:]


@dataclass
class RenderResult:
    """The raw outputs of every theme of one job."""

    job_id: str
    outputs: dict[Theme, ThemeOutput] = field(default_factory=dict)


class DataRunUnsupported(RendererUnavailable):
    """The backend has no data run: a renderer deployed before `POST /run-data` (404), or a backend without one."""


MAX_DATA_TIMEOUT_S = 30.0
"""A data run's longest time limit; the renderer's `wire.MAX_DATA_TIMEOUT_S` is the same (pinned by a test)."""


@dataclass(frozen=True)
class DataJob:
    """One data-generating snippet to run once in isolation (`run_data_code`); the harness writes its `df`."""

    job_id: str
    source: str
    timeout_s: float = 20.0

    def __post_init__(self) -> None:
        if not _RENDER_ID.fullmatch(self.job_id):
            raise ValueError("job_id must match the render id pattern")
        if not 0 < self.timeout_s <= MAX_DATA_TIMEOUT_S:
            raise ValueError("timeout_s must be positive and at most the data run limit")


@dataclass
class DataOutput:
    """What a data run left behind: the harness's exit code (`harness.DATA_EXIT`), and its `out.csv` after a 0.

    `stderr_tail` is the snippet's own output: the tool reads it only for an exception
    class and a line number (`gates.error_summary`), never passes it on.
    """

    exit_code: int | None
    timed_out: bool = False
    csv_text: str | None = None
    stderr_tail: str = ""
    wall_s: float = 0.0
    reason: str | None = None
    measured: int | None = None
    limit: int | None = None

    def __post_init__(self) -> None:
        self.stderr_tail = self.stderr_tail[-MAX_STDERR_CHARS:]


MAX_CONVERT_TIMEOUT_S = 15.0
"""A conversion's longest time limit; the renderer's `wire.MAX_CONVERT_TIMEOUT_S` is the same (pinned by a test)."""


@dataclass(frozen=True)
class ConvertJob:
    """One binary data file to convert to text in isolation (the dataset route's `/convert`); `sheet` names the
    sheet or `.npz` array the page chose, None for the first."""

    job_id: str
    data: bytes = field(repr=False)
    sheet: str | None = None
    timeout_s: float = 10.0

    def __post_init__(self) -> None:
        if not _RENDER_ID.fullmatch(self.job_id):
            raise ValueError("job_id must match the render id pattern")
        if not 0 < self.timeout_s <= MAX_CONVERT_TIMEOUT_S:
            raise ValueError("timeout_s must be positive and at most the conversion limit")


@dataclass
class ConvertOutput:
    """What a conversion left: the harness's exit code (`harness.CONVERT_EXIT`), the refusal it stands for with
    the measured value and the cap, or the text and its `meta` after a 0. `reason` is the renderer's run reason
    (`timeout`, `memory`, ...) when the host stopped the run."""

    exit_code: int | None
    timed_out: bool = False
    refusal: str | None = None
    measured: int | None = None
    limit: int | None = None
    damage: str | None = None
    """A `corrupt` refusal's broken part (`wire.ConvertDamage`), or None."""
    text: str | None = field(default=None, repr=False)
    meta: ConvertMeta | None = None
    reason: str | None = None
    wall_s: float = 0.0


class RenderBackend(Protocol):
    """Runs a job's code once per theme in isolation and collects the raw outputs; runs data snippets and file
    conversions the same way."""

    name: str

    async def render(self, job: RenderJob) -> RenderResult: ...

    async def run_data(self, job: DataJob) -> DataOutput: ...

    async def convert(self, job: ConvertJob) -> ConvertOutput: ...


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

    def data_command(self) -> list[str]:
        """The argv that runs a data snippet in the work directory with the harness in data mode."""
        ...

    def data_env(self, timeout_s: float | None = None) -> dict[str, str]:
        """The complete environment of a data run: no theme, no plotting settings; the CPU cap clamped to `timeout_s`
        when given, as the renderer clamps it."""
        ...

    def convert_command(self) -> list[str]:
        """The argv that converts the file `input.bin` in the work directory with the harness in convert mode."""
        ...

    def convert_env(self) -> dict[str, str]:
        """The complete environment of a conversion."""
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
