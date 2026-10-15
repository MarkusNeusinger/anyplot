"""The renderer's JSON contract: the bodies of `POST /render` and `POST /run-data` and their answers.

The render request is the agents' `RenderJob` (`agents/anyplot/render/contract.py`)
field for field; the answer is its `RenderResult`, one `ThemeRun` per theme, with the
PNG as base64 and the timings added. The data run request is the agents' `DataJob`
(a snippet that computes a table, `run_data_code`); its answer is `DataRunResponse`,
with the `out.csv` the harness wrote as text. The renderer service (`main.py`)
validates requests with these models and the `remote` backend parses answers with
them, so both sides read one definition.

No ADK and no `agents.anyplot` import: importing that package loads ADK, which the
renderer image does not install. The limits that also exist on the agents side
(`MAX_PNG_BYTES`, `MAX_PROBE_BYTES`, `MAX_STDERR_CHARS`, `MAX_CSV_BYTES`, the job id
pattern) are pinned equal by `tests/unit/agents/renderer/test_wire.py`.
"""

import base64
import binascii
import json
import math
from typing import Annotated, Any, Literal, get_args

from pydantic import BaseModel, ConfigDict, Field, field_validator


Theme = Literal["light", "dark"]
JOB_ID_PATTERN = r"^[A-Za-z0-9_-]{1,64}$"
"""The agents' `RENDER_ID_PATTERN`: a job id is opaque and never becomes a path or a sandbox name."""
LIBRARY_PATTERN = r"^[a-z0-9_-]{1,32}$"
MAX_SOURCE_CHARS = 128 * 1024
"""The run form: the validator parses at most 48 KB, the loader and the normaliser add little."""
MAX_DATA_CSV_CHARS = 4 * 1024 * 1024
"""The canonical `data.csv`: the agents' parser refuses a parse whose canonical CSV is larger
(`data/parse.py` `MAX_CANONICAL_BYTES`, pinned equal), so every stored dataset fits. Pastes take at
most 1 MiB and computed data 2 MiB (until 2026-10-14 this cap was 2 MiB and the paste cap 200 KB)."""
MAX_TIMEOUT_S = 120.0
MAX_PNG_BYTES = 10 * 1024 * 1024
"""Largest PNG the renderer returns; the agents' R2 gate (`render/png.py`) applies the same cap."""
MAX_PROBE_BYTES = 256 * 1024
MAX_PROBE_DEPTH = 16
"""Deepest nesting a probe may have; the harness writes three levels."""
MAX_PROBE_INT = 2**53
"""Largest integer magnitude a probe may hold: what a JSON number keeps exactly as a float."""
MAX_STDERR_CHARS = 2_000
"""The stderr tail a theme returns; the agents' `ThemeOutput` keeps the same number of characters."""
MAX_DATA_SOURCE_CHARS = 16 * 1024
"""A data snippet: the tool takes at most 6,000 characters, and stripping a `__main__` guard only shortens it."""
MAX_DATA_TIMEOUT_S = 30.0
"""A data run's time limit: a snippet computes a table of at most 20,000 rows, which takes well under a second."""
MAX_CSV_BYTES = 2 * 1024 * 1024
"""The `out.csv` a data run returns: the agents' cap for computed data (`data/parse.py` `MAX_COMPUTED_BYTES`, 2 MiB;
pastes take 1 MiB), which the harness applies before it writes; the executor reads at most this many bytes."""

DATA_STATUS_FILE = "status.json"
"""The data run's outcome the harness writes (`harness.DATA_STATUS_FILE`, pinned by a test)."""
MAX_DATA_STATUS_BYTES = 1024
"""Largest `status.json` a host reads; the harness writes well under 100 bytes."""
MAX_DATA_EXIT = 255


class DataStatus(BaseModel):
    """`status.json` as the hosts read it: the harness's own exit code, and the measured value and cap of a refusal.

    The executor and the local backend take the exit code from here rather than from
    the launcher, whose code loses it on Cloud Run (every non-zero exit is -13).
    """

    model_config = ConfigDict(extra="ignore")

    exit: int = Field(ge=0, le=MAX_DATA_EXIT)
    measured: int | None = Field(default=None, ge=0, le=MAX_PROBE_INT)
    limit: int | None = Field(default=None, ge=0, le=MAX_PROBE_INT)


def parse_data_status(raw: bytes | None) -> DataStatus | None:
    """The harness's `status.json`, or None when it is missing or not the expected shape (strict UTF-8 JSON)."""
    if raw is None or len(raw) > MAX_DATA_STATUS_BYTES:
        return None
    try:
        return DataStatus.model_validate_json(raw, strict=True)
    except ValueError:
        return None


RunReason = Literal["timeout", "disk_budget", "file_budget", "memory", "launcher", "output_rejected"]
"""Why a theme has no usable output, when the renderer knows more than the exit code:
`timeout` (killed at the job's time limit), `disk_budget` (killed for writing more bytes than
the per-run budget), `file_budget` (killed for creating more files and directories than the
per-run limit, or a tree too deep to measure), `memory` (killed because the instance's
`MemAvailable` fell below the renderer's floor during the run), `launcher` (the sandbox
launcher failed twice before the harness started), `output_rejected` (the PNG is not a
regular file or is over its cap). `measured` and `limit` carry the numbers where there are some."""


def clean_probe(raw: bytes | None) -> dict[str, Any] | None:
    """`probe-<theme>.json` as a JSON object the wire can carry, or None.

    The code under test can write this file, so it is untrusted: `NaN` and
    `Infinity` become null (the harness writes them for a text at an undefined
    position), and a probe that is not an object, nests deeper than
    `MAX_PROBE_DEPTH`, or holds a number that a float cannot carry exactly is
    dropped whole, because serialising it would fail the response (a nesting of
    256 levels) or the agents side's parse (about 200 levels, or an integer too
    large for a float).
    """
    if not raw:
        return None
    try:
        loaded = json.loads(raw, parse_constant=lambda _: None)
    except (ValueError, RecursionError):
        return None
    if not isinstance(loaded, dict) or not _probe_value_ok(loaded, 1):
        return None
    return loaded


def _probe_value_ok(value: Any, depth: int) -> bool:
    if depth > MAX_PROBE_DEPTH:
        return False
    if isinstance(value, dict):
        return all(_probe_value_ok(item, depth + 1) for item in value.values())
    if isinstance(value, list):
        return all(_probe_value_ok(item, depth + 1) for item in value)
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return True
    if isinstance(value, int):
        return abs(value) <= MAX_PROBE_INT
    if isinstance(value, float):
        return math.isfinite(value)
    return False


class RenderRequest(BaseModel):
    """One code version to render in every theme of `themes`, one sandbox per theme, in order."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(pattern=JOB_ID_PATTERN)
    language: Literal["python"]
    library: str = Field(pattern=LIBRARY_PATTERN)
    source: str = Field(min_length=1, max_length=MAX_SOURCE_CHARS)
    data_csv: str = Field(max_length=MAX_DATA_CSV_CHARS)
    themes: list[Theme] = Field(min_length=1, max_length=2)
    timeout_s: float = Field(gt=0, le=MAX_TIMEOUT_S)

    @field_validator("themes")
    @classmethod
    def _distinct(cls, value: list[Theme]) -> list[Theme]:
        if len(set(value)) != len(value):
            raise ValueError("themes must be distinct")
        return value


class ThemeRun(BaseModel):
    """What one theme's sandbox left behind, before any gate looked at it."""

    model_config = ConfigDict(extra="forbid")

    theme: Theme
    exit_code: int | None
    """The exit code of the sandboxed process; None when the renderer killed it."""
    timed_out: bool = False
    png_base64: str | None = None
    """`plot-<theme>.png` as the code wrote it (base64), at most `MAX_PNG_BYTES` before encoding."""
    probe: dict[str, Any] | None = None
    """`probe-<theme>.json` from the harness's savefig probe, when it is a JSON object."""
    stderr_tail: str = Field(default="", max_length=MAX_STDERR_CHARS)
    wall_s: float = Field(default=0.0, ge=0)
    attempts: int = Field(default=1, ge=1, le=2)
    """Sandbox launches for this theme: 2 when the first launcher call failed before the harness started."""
    reason: RunReason | None = None
    measured: int | None = None
    """The value that broke a limit: bytes (`disk_budget`, an oversized PNG for `output_rejected`),
    files and directories (`file_budget`; None for a tree too deep to measure), or MiB of
    `MemAvailable` (`memory`). None for the other reasons."""
    limit: int | None = None
    """The limit `measured` broke, in the same unit."""
    max_rss_mb: float | None = None
    """Peak resident memory the harness reported for itself (advisory: the code shares its stdout)."""
    cpu_s: float | None = None


class RenderTimings(BaseModel):
    """Where the request's time went."""

    model_config = ConfigDict(extra="forbid")

    slot_wait_s: float = Field(ge=0)
    """Time spent waiting for the renderer's one render slot."""
    total_s: float = Field(ge=0)


class RenderResponse(BaseModel):
    """The raw outputs of every theme of one job."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(pattern=JOB_ID_PATTERN)
    outputs: dict[Theme, ThemeRun]
    timings: RenderTimings
    version: str
    mem_available_mb: int | None = None
    """`MemAvailable` of the renderer instance after the job, in MiB (None where unreadable)."""


class DataRunRequest(BaseModel):
    """One data-generating snippet to run once in a sandbox of its own (`POST /run-data`); no theme, no data file."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(pattern=JOB_ID_PATTERN)
    source: str = Field(min_length=1, max_length=MAX_DATA_SOURCE_CHARS)
    timeout_s: float = Field(gt=0, le=MAX_DATA_TIMEOUT_S)


class DataRun(BaseModel):
    """What one data run's sandbox left behind: the exit code and the `out.csv` the harness wrote, nothing else
    the snippet printed except the stderr tail, which the agents side reads only for an exception class and line."""

    model_config = ConfigDict(extra="forbid")

    exit_code: int | None
    """The harness's exit code (`harness.DATA_EXIT`); None when the renderer killed the run."""
    timed_out: bool = False
    reason: RunReason | None = None
    measured: int | None = None
    limit: int | None = None
    csv_text: str | None = Field(default=None, max_length=MAX_CSV_BYTES)
    """`out.csv` as UTF-8 text, read only after an exit code of 0, at most `MAX_CSV_BYTES` bytes."""
    stderr_tail: str = Field(default="", max_length=MAX_STDERR_CHARS)
    wall_s: float = Field(default=0.0, ge=0)
    attempts: int = Field(default=1, ge=1, le=2)


class DataRunResponse(DataRun):
    """`POST /run-data`: the run, with the job id, the timings and the instance's figures added."""

    job_id: str = Field(pattern=JOB_ID_PATTERN)
    timings: RenderTimings
    version: str
    mem_available_mb: int | None = None


MAX_CONVERT_INPUT_BYTES = 5 * 1024 * 1024
"""The largest file `POST /convert` takes (`convert.MAX_INPUT_BYTES`, the agents' and the BFF's raw cap)."""
MAX_CONVERT_BASE64_CHARS = 4 * ((MAX_CONVERT_INPUT_BYTES + 2) // 3)
MAX_CONVERT_TIMEOUT_S = 15.0
"""A conversion's time limit: the agents ask for 10 s, so a conversion never holds the render slot for long."""
MAX_CONVERT_TEXT_BYTES = 1024 * 1024
"""The text a conversion returns: the paste cap (`data/parse.py` `MAX_INPUT_BYTES`), because it goes into the paste box."""
MAX_CONVERT_META_BYTES = 16 * 1024
MAX_SHEET_NAME_CHARS = 255
"""A requested sheet name: Excel allows 31 characters, OpenDocument any number; the converter names at most 100."""
CONVERT_INPUT_FILE = "input.bin"
CONVERT_REQUEST_FILE = "request.json"  # harness.CONVERT_REQUEST_FILE
CONVERT_META_FILE = "meta.json"  # harness.CONVERT_META_FILE
CONVERT_REFUSAL_BASE = 10
ConvertRefusal = Literal[
    "unsupported",
    "encrypted",
    "pickle",
    "hdf5",
    "corrupt",
    "archive_limits",
    "too_many_rows",
    "too_many_columns",
    "too_large",
    "empty",
    "sheet_not_found",
    "array_shape",
    "object_array",
]
CONVERT_REASONS: tuple[ConvertRefusal, ...] = get_args(ConvertRefusal)
"""Why the converter refused a file (`convert.REFUSALS`, `harness.CONVERT_REFUSALS`, pinned equal): the harness exits
with `CONVERT_REFUSAL_BASE` plus the index."""
ConvertKind = Literal["xlsx", "xlsm", "xlsb", "xls", "ods", "parquet", "feather", "arrow", "npy", "npz"]
ConvertWarning = Literal[
    "formulas_without_value", "hidden_sheets", "dropped_columns", "list_columns", "utc_timestamps", "renamed_columns"
]


def convert_refusal(exit_code: int | None) -> ConvertRefusal | None:
    """The refusal a convert-mode exit code stands for, or None for any other code."""
    if exit_code is None:
        return None
    index = exit_code - CONVERT_REFUSAL_BASE
    return CONVERT_REASONS[index] if 0 <= index < len(CONVERT_REASONS) else None


class ConvertRequest(BaseModel):
    """One file to convert to CSV text in a sandbox of its own (`POST /convert`), the bytes as base64."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(pattern=JOB_ID_PATTERN)
    data_base64: str = Field(min_length=4, max_length=MAX_CONVERT_BASE64_CHARS)
    sheet: str | None = Field(default=None, min_length=1, max_length=MAX_SHEET_NAME_CHARS)
    timeout_s: float = Field(gt=0, le=MAX_CONVERT_TIMEOUT_S)

    @field_validator("data_base64")
    @classmethod
    def _base64(cls, value: str) -> str:
        try:
            raw = base64.b64decode(value, validate=True)
        except (ValueError, binascii.Error):
            raise ValueError("data_base64 is not base64") from None
        if not raw or len(raw) > MAX_CONVERT_INPUT_BYTES:
            raise ValueError("the file is empty or over the cap")
        return value

    def data(self) -> bytes:
        return base64.b64decode(self.data_base64, validate=True)


class ConvertMeta(BaseModel):
    """`meta.json`, what the converter found (`convert.Conversion.meta`); read only after exit code 0."""

    model_config = ConfigDict(extra="forbid")

    kind: ConvertKind
    format: Literal["csv", "json"] = "csv"
    """`json` for a table with list columns: records the parser expands into long format."""
    rows: int = Field(ge=0, le=10 * MAX_PROBE_INT)
    columns: int = Field(ge=0, le=1_000)
    sheet: str | None = Field(default=None, max_length=MAX_SHEET_NAME_CHARS)
    sheets: list[Annotated[str, Field(max_length=MAX_SHEET_NAME_CHARS)]] = Field(default_factory=list, max_length=10)
    sheet_count: int = Field(default=0, ge=0, le=100_000)
    warnings: dict[ConvertWarning, Annotated[int, Field(ge=0, le=MAX_PROBE_INT)]] = Field(default_factory=dict)


class ConvertRun(BaseModel):
    """What one conversion's sandbox left: the exit code, the refusal it stands for, the text and the meta."""

    model_config = ConfigDict(extra="forbid")

    exit_code: int | None
    """The harness's exit code (`harness.CONVERT_EXIT`); None when the renderer killed the run."""
    timed_out: bool = False
    reason: RunReason | None = None
    refusal: ConvertRefusal | None = None
    measured: int | None = None
    limit: int | None = None
    text: str | None = Field(default=None, max_length=MAX_CONVERT_TEXT_BYTES)
    meta: ConvertMeta | None = None
    wall_s: float = Field(default=0.0, ge=0)
    attempts: int = Field(default=1, ge=1, le=2)


class ConvertResponse(ConvertRun):
    """`POST /convert`: the run, with the job id, the timings and the instance's figures added."""

    job_id: str = Field(pattern=JOB_ID_PATTERN)
    timings: RenderTimings
    version: str
    mem_available_mb: int | None = None


class RendererStatus(BaseModel):
    """`GET /status`: what the instance is doing and how much memory it has left."""

    model_config = ConfigDict(extra="forbid")

    name: Literal["anyplot-renderer"] = "anyplot-renderer"
    version: str
    revision: str | None = None
    in_flight: int
    waiting: int
    stuck: int
    """Sandbox launcher processes that did not exit after a kill; while any is alive, renders answer `503 stuck`."""
    mem_available_mb: int | None
    sandbox: bool
    """Whether the sandbox launcher binary exists and is executable on this instance."""
    volume: bool | None = None
    """Whether `RENDERER_RUNS_DIR` is the size-limited volume it must be: checked on Cloud Run
    only (None elsewhere); while it is False, renders answer `503 volume_missing`."""
