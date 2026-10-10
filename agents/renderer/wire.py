"""The renderer's JSON contract: the body of `POST /render` and its answer.

The request is the agents' `RenderJob` (`agents/anyplot/render/contract.py`) field for
field; the answer is its `RenderResult`, one `ThemeRun` per theme, with the PNG as
base64 and the timings added. The renderer service (`main.py`) validates requests
with these models and the `remote` backend parses answers with them, so both sides
read one definition.

No ADK and no `agents.anyplot` import: importing that package loads ADK, which the
renderer image does not install. The limits that also exist on the agents side
(`MAX_PNG_BYTES`, `MAX_PROBE_BYTES`, `MAX_STDERR_CHARS`, the job id pattern) are
pinned equal by `tests/unit/agents/renderer/test_wire.py`.
"""

import json
import math
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


Theme = Literal["light", "dark"]
JOB_ID_PATTERN = r"^[A-Za-z0-9_-]{1,64}$"
"""The agents' `RENDER_ID_PATTERN`: a job id is opaque and never becomes a path or a sandbox name."""
LIBRARY_PATTERN = r"^[a-z0-9_-]{1,32}$"
MAX_SOURCE_CHARS = 128 * 1024
"""The run form: the validator parses at most 48 KB, the loader and the normaliser add little."""
MAX_DATA_CSV_CHARS = 2 * 1024 * 1024
"""The canonical `data.csv`: the parser takes at most 200 KB of pasted text, and canonical
dates and decimals grow it by well under a factor of ten."""
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
