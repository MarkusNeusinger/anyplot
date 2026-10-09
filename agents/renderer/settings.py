"""Runtime settings of the renderer service, read from `RENDERER_*` environment variables.

`ENVIRONMENT` (shared with the API and the agents, no prefix) and the Cloud Run
variables `K_SERVICE` and `K_REVISION` are read without the prefix. The defaults are
the deployed values, so an unset variable never weakens a limit.

| Variable | Default | Meaning |
|---|---|---|
| `RENDERER_ALLOWED_CALLERS` | empty | Emails whose ID token may call the service (comma-separated): the agents service account, and the owner's account for `adk web` |
| `RENDERER_AUDIENCES` | empty | Accepted ID-token `aud` values (comma-separated): the service URL and the candidate-tag URL, plus the OAuth client id of a developer's user token (see agents/README.md) |
| `RENDERER_SANDBOX_BINARY` | `/usr/local/gcp/bin/sandbox` | The Cloud Run sandbox launcher |
| `RENDERER_PYTHON` | `/app/.venv/bin/python` | The interpreter inside the sandbox (the image's own venv) |
| `RENDERER_HARNESS` | `/opt/anyplot/harness.py` | The probe harness inside the sandbox |
| `RENDERER_RUNS_DIR` | `/tmp/runs` | Root of the run directories: the size-limited in-memory volume |
| `RENDERER_MPL_SEED` | `/opt/mplconfig` | The baked matplotlib cache the harness copies into the sandbox |
| `RENDERER_MPLCONFIG` | `/tmp/mpl` | `MPLCONFIGDIR` inside the sandbox (its private `/tmp`) |
| `RENDERER_RUN_BUDGET_MB` | `64` | Bytes one run directory may hold before the watchdog kills the sandbox |
| `RENDERER_WATCH_INTERVAL_S` | `0.05` | How often the watchdog measures a live run directory |
| `RENDERER_SLOT_WAIT_S` | `30` | Longest wait for the render slot before `503 busy` |
| `RENDERER_MIN_MEM_AVAILABLE_MB` | `1024` | Below this `MemAvailable` a render is refused with `503 low_memory`; 0 switches the floor off |
| `RENDERER_RLIMIT_CPU_S` | `60` | CPU seconds of the sandboxed process (also capped by the job's timeout) |
| `RENDERER_RLIMIT_FSIZE_MB` | `50` | Largest file the sandboxed process may write |
| `RENDERER_RLIMIT_AS_MB` | `1024` | Address space of the sandboxed process; 0 leaves it unset |
| `RENDERER_RLIMIT_NPROC` | `64` | Processes and threads of the sandboxed process; 0 leaves it unset |
| `RENDERER_KILL_GRACE_S` | `10` | How long to wait for the launcher process to exit after a kill |
| `RENDERER_BIND_TMP` | `false` | Bind a directory of the run over the sandbox's `/tmp`, so `/tmp` counts toward the run budget (spike S2, untested) |
| `ENVIRONMENT` | `production` | `development` skips the caller check and is refused on Cloud Run |
"""

from functools import lru_cache
from typing import Annotated, Any, Self

from pydantic import Field, NonNegativeInt, PositiveFloat, PositiveInt, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


def _split_list(value: Any) -> Any:
    """A comma-separated string (the documented form) or a list; an empty string is an empty list."""
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return value


class RendererSettings(BaseSettings):
    """Settings of the anyplot-renderer service."""

    model_config = SettingsConfigDict(
        env_prefix="RENDERER_", case_sensitive=False, extra="ignore", validate_by_name=True, validate_by_alias=True
    )

    allowed_callers: Annotated[list[str], NoDecode] = []
    """Emails allowed to call the service (`RENDERER_ALLOWED_CALLERS`). Empty means nobody outside development."""

    audiences: Annotated[list[str], NoDecode] = []
    """Accepted ID-token audiences (`RENDERER_AUDIENCES`). Empty means nobody outside development."""

    sandbox_binary: str = "/usr/local/gcp/bin/sandbox"
    python: str = "/app/.venv/bin/python"
    harness: str = "/opt/anyplot/harness.py"
    runs_dir: str = "/tmp/runs"
    mpl_seed: str = "/opt/mplconfig"
    mplconfig: str = "/tmp/mpl"

    run_budget_mb: PositiveInt = 64
    """Per-run byte budget (`RENDERER_RUN_BUDGET_MB`). A run legitimately leaves a PNG of at most
    10 MiB, a probe and the two inputs; the 512 MiB volume is shared by every run directory."""

    watch_interval_s: PositiveFloat = 0.05
    slot_wait_s: PositiveFloat = 30.0
    min_mem_available_mb: NonNegativeInt = 1024
    rlimit_cpu_s: PositiveInt = 60
    rlimit_fsize_mb: PositiveInt = 50
    rlimit_as_mb: NonNegativeInt = 1024
    rlimit_nproc: NonNegativeInt = 64
    kill_grace_s: PositiveFloat = 10.0
    bind_tmp: bool = False

    environment: str = Field(default="production", validation_alias="ENVIRONMENT")
    """Deployment environment (`ENVIRONMENT`, no prefix). Unset is `production`, so the caller check stays on."""

    cloud_run_service: str | None = Field(default=None, validation_alias="K_SERVICE")
    revision: str | None = Field(default=None, validation_alias="K_REVISION")

    @field_validator("allowed_callers", "audiences", mode="before")
    @classmethod
    def _parse_list(cls, value: Any) -> Any:
        return _split_list(value)

    @field_validator("environment")
    @classmethod
    def _normalise_environment(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("sandbox_binary", "python", "harness", "runs_dir", "mpl_seed", "mplconfig")
    @classmethod
    def _absolute(cls, value: str) -> str:
        if not value.startswith("/"):
            raise ValueError(f"{value!r} must be an absolute path")
        return value

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.is_development and self.cloud_run_service:
            raise ValueError(
                "ENVIRONMENT=development is refused on Cloud Run (K_SERVICE is set): it would skip the caller check"
            )
        return self

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


@lru_cache(maxsize=1)
def get_settings() -> RendererSettings:
    """The process-wide settings, read once from the environment."""
    return RendererSettings()
