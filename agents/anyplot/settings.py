"""Runtime settings of the anyplot agent network.

Every value comes from an `AGENT_*` environment variable, except `ENVIRONMENT`,
which the service shares with the API and reads without the prefix, and the
Google Cloud project, which also falls back to `GOOGLE_CLOUD_PROJECT`. The
defaults are the pinned production values, so an unset variable can never select
another provider, model or location.

| Variable | Default | Meaning |
|---|---|---|
| `AGENT_PROVIDER` | `anthropic-vertex` | Model family of every agent and the scope judge: `anthropic-vertex` (Claude on Vertex AI) or `gemini` |
| `AGENT_MODEL` | `claude-haiku-5-5` | Model of every agent; an exact id that matches the provider (`claude-...` or `gemini-...`) |
| `AGENT_JUDGE_MODEL` | `claude-haiku-5-5` | Model of the scope and dataset judge; same rule |
| `AGENT_LOCATION` | `eu` | Vertex AI location of every model call: `eu`, `us` or `global` |
| `AGENT_PROJECT`, else `GOOGLE_CLOUD_PROJECT` | `anyplot` | Google Cloud project that serves (and bills) the model calls |
| `AGENT_LIBRARIES` | `matplotlib,seaborn` | Libraries with an enabled runtime |
| `AGENT_RENDERER` | `sandbox` | Render backend: `sandbox`, `local` (development only), `fake` or `remote` |
| `AGENT_RENDER_IMAGE` | `anyplot-agents:dev` | Image the `local` renderer runs with Docker |
| `AGENT_RENDER_CONCURRENCY` | `2` | Renders (one theme each) that may run at the same time |
| `AGENT_MAX_LLM_CALLS` | `12` | LLM calls per request (the `RunConfig` cap) |
| `AGENT_REQUEST_TOKEN_BUDGET` | `80000` | Tokens per request |
| `AGENT_DAILY_TOKEN_BUDGET` | `1000000` | Tokens per user and day |
| `AGENT_DAILY_PIPELINE_RUNS` | `40` | Pipeline runs per user and day |
| `AGENT_GLOBAL_DAILY_TOKEN_BUDGET` | `3000000` | Tokens per day across all users; reaching it pauses the service |
| `AGENT_RENDER_TIMEOUT_S` | `60` | Seconds per render, host-enforced |
| `AGENT_REQUEST_DEADLINE_S` | `180` | Hard request deadline, enforced through `abort_signal` |
| `AGENT_SOFT_DEADLINE_S` | `140` | Soft deadline inside the pipeline; below the hard one |
| `AGENT_JUDGE_TIMEOUT_S` | `4` | Wall-clock budget of one judge verdict, its single retry included |
| `AGENT_SESSION_IDLE_S` | `3600` | Idle seconds after which the sweeper drops a session and its stores |
| `AGENT_ALLOWED_CALLERS` | empty | Service-account emails allowed to call `/v1` (comma-separated) |
| `AGENT_SERVICE_URLS` | empty | ID-token audiences accepted on `/v1`: the service URL and the candidate-tag URL (comma-separated) |
| `AGENT_DEV_FIXTURE` | unset | Development only: an eval fixture case id that seeds every new session |
| `ENVIRONMENT` | `development` | Deployment environment, shared with the API |

No `.env` file is read: the service runs on Cloud Run environment variables only,
`adk web` loads its own `.env` from the agent directory into the environment, and
the tests stay hermetic.
"""

import json
from functools import lru_cache
from typing import Annotated, Any, Literal, Self

from pydantic import AliasChoices, Field, PositiveFloat, PositiveInt, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from core.constants import SUPPORTED_LIBRARIES


Location = Literal["eu", "us", "global"]
"""Vertex AI multi-region endpoints. A regional id such as europe-west4 serves
neither Gemini 3.x Flash nor the eu Claude quota, so it is refused rather than tried."""

Provider = Literal["anthropic-vertex", "gemini"]
"""Model families: Claude through Vertex AI's Anthropic endpoint, or Gemini through Vertex AI."""

Renderer = Literal["sandbox", "local", "fake", "remote"]
"""Render backends: `sandbox` (Cloud Run sandboxes, phase 1), `local` (Docker,
development only), `fake` (unit tests) and `remote` (the phase-2 renderer split)."""

LOCATIONS: tuple[str, ...] = ("eu", "us", "global")
MODEL_PREFIXES: dict[str, str] = {"anthropic-vertex": "claude-", "gemini": "gemini-"}
FIXTURE_PATTERN = r"^[a-z0-9][a-z0-9-]{0,79}$"


def _split_list(value: Any) -> Any:
    """Accept a JSON array or a comma-separated string for a list setting.

    `AGENT_LIBRARIES=matplotlib,seaborn` is the documented form; pydantic-settings
    would otherwise insist on JSON. An empty string is an empty list.
    """
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        if stripped.startswith("["):
            return json.loads(stripped)
        return [item.strip() for item in stripped.split(",") if item.strip()]
    return value


class AgentSettings(BaseSettings):
    """Settings of the anyplot-agents service, read from `AGENT_*` variables."""

    model_config = SettingsConfigDict(
        env_prefix="AGENT_", case_sensitive=False, extra="ignore", validate_by_name=True, validate_by_alias=True
    )

    provider: Provider = "anthropic-vertex"
    """Model family of every agent and the judge (`AGENT_PROVIDER`)."""

    model: str = "claude-haiku-5-5"
    """Model of every agent (`AGENT_MODEL`). An exact id, never an alias."""

    judge_model: str = "claude-haiku-5-5"
    """Model of the scope and dataset judge (`AGENT_JUDGE_MODEL`)."""

    location: Location = "eu"
    """Vertex AI location of every model call (`AGENT_LOCATION`): `eu`, `us` or `global`."""

    project: str = Field(default="anyplot", validation_alias=AliasChoices("AGENT_PROJECT", "GOOGLE_CLOUD_PROJECT"))
    """Google Cloud project of the model calls (`AGENT_PROJECT`, else `GOOGLE_CLOUD_PROJECT`)."""

    libraries: Annotated[list[str], NoDecode] = Field(default=["matplotlib", "seaborn"], min_length=1)
    """Libraries with an enabled runtime (`AGENT_LIBRARIES`, comma-separated)."""

    renderer: Renderer = "sandbox"
    """Render backend (`AGENT_RENDERER`); `local` only in development."""

    render_image: str = Field(default="anyplot-agents:dev", pattern=r"^[A-Za-z0-9][A-Za-z0-9._/:@-]{0,199}$")
    """Image the local renderer runs (`AGENT_RENDER_IMAGE`)."""

    render_concurrency: PositiveInt = 2
    """Theme renders that may run at the same time (`AGENT_RENDER_CONCURRENCY`)."""

    max_llm_calls: PositiveInt = 12
    """LLM calls per request (`AGENT_MAX_LLM_CALLS`), the `RunConfig` cap."""

    request_token_budget: PositiveInt = 80_000
    """Tokens per request (`AGENT_REQUEST_TOKEN_BUDGET`)."""

    daily_token_budget: PositiveInt = 1_000_000
    """Tokens per user and day (`AGENT_DAILY_TOKEN_BUDGET`)."""

    daily_pipeline_runs: PositiveInt = 40
    """Pipeline runs per user and day (`AGENT_DAILY_PIPELINE_RUNS`)."""

    global_daily_token_budget: PositiveInt = 3_000_000
    """Tokens per day across all users (`AGENT_GLOBAL_DAILY_TOKEN_BUDGET`); reaching it pauses the service."""

    render_timeout_s: PositiveInt = 60
    """Seconds per render, host-enforced (`AGENT_RENDER_TIMEOUT_S`)."""

    request_deadline_s: PositiveInt = 180
    """Hard request deadline in seconds, enforced through `abort_signal` (`AGENT_REQUEST_DEADLINE_S`)."""

    soft_deadline_s: PositiveInt = 140
    """Soft deadline in seconds inside the pipeline (`AGENT_SOFT_DEADLINE_S`); below the hard one."""

    judge_timeout_s: PositiveFloat = 4.0
    """Seconds for one judge verdict including its one retry (`AGENT_JUDGE_TIMEOUT_S`)."""

    session_idle_s: PositiveInt = 3600
    """Idle seconds before the sweeper drops a session (`AGENT_SESSION_IDLE_S`)."""

    allowed_callers: Annotated[list[str], NoDecode] = []
    """Service-account emails allowed to call `/v1` (`AGENT_ALLOWED_CALLERS`, comma-separated).
    Empty means no caller passes the check outside development."""

    service_urls: Annotated[list[str], NoDecode] = []
    """ID-token audiences accepted on `/v1` (`AGENT_SERVICE_URLS`, comma-separated): the
    service URL and the candidate-tag URL. Empty means no caller passes outside development."""

    dev_fixture: str | None = Field(default=None, pattern=FIXTURE_PATTERN)
    """Eval fixture case that seeds every new session (`AGENT_DEV_FIXTURE`); development only."""

    environment: str = Field(default="development", validation_alias="ENVIRONMENT")
    """Deployment environment (`ENVIRONMENT`, shared with the API, no prefix)."""

    @field_validator("model", "judge_model")
    @classmethod
    def _pinned_model_id(cls, value: str) -> str:
        """Refuse floating aliases such as `gemini-flash-latest`.

        The alias is undocumented on Vertex AI, the version it serves cannot be
        observed, and it answered 404 once when its target retired.
        """
        value = value.strip()
        if not value:
            raise ValueError("a model id is required")
        if value == "latest" or value.endswith("-latest"):
            raise ValueError(f"{value!r} is a floating alias; pin an exact model id such as 'claude-haiku-5-5'")
        return value

    @field_validator("location", mode="before")
    @classmethod
    def _multi_region_location(cls, value: Any) -> Any:
        """Explain why a regional location such as europe-west4 is refused."""
        if isinstance(value, str):
            value = value.strip().lower()
            if value not in LOCATIONS:
                raise ValueError(
                    f"AGENT_LOCATION must be eu, us or global, not {value!r}: "
                    "regional endpoints such as europe-west4 serve no Gemini 3.x Flash model"
                )
        return value

    @field_validator("project")
    @classmethod
    def _project_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("a Google Cloud project id is required")
        return value

    @field_validator("libraries", "allowed_callers", "service_urls", mode="before")
    @classmethod
    def _parse_list(cls, value: Any) -> Any:
        return _split_list(value)

    @field_validator("dev_fixture", mode="before")
    @classmethod
    def _blank_fixture_is_none(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            return None
        return value.strip() if isinstance(value, str) else value

    @field_validator("libraries")
    @classmethod
    def _known_libraries(cls, value: list[str]) -> list[str]:
        unknown = sorted(set(value) - SUPPORTED_LIBRARIES)
        if unknown:
            raise ValueError(f"unknown libraries in AGENT_LIBRARIES: {', '.join(unknown)}")
        return list(dict.fromkeys(value))

    @field_validator("environment")
    @classmethod
    def _normalise_environment(cls, value: str) -> str:
        return value.strip().lower()

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        """Cross-field rules: provider and model ids agree, development-only features stay there."""
        prefix = MODEL_PREFIXES[self.provider]
        for name, value in (("AGENT_MODEL", self.model), ("AGENT_JUDGE_MODEL", self.judge_model)):
            if not value.startswith(prefix):
                raise ValueError(
                    f"{name}={value!r} does not match AGENT_PROVIDER={self.provider}: "
                    f"that provider serves model ids starting with {prefix!r}"
                )
        if self.renderer == "local" and self.environment != "development":
            raise ValueError(
                f"AGENT_RENDERER=local is allowed only when ENVIRONMENT=development, not {self.environment!r}"
            )
        if self.dev_fixture is not None and self.environment != "development":
            raise ValueError(
                f"AGENT_DEV_FIXTURE is allowed only when ENVIRONMENT=development, not {self.environment!r}"
            )
        if self.soft_deadline_s >= self.request_deadline_s:
            raise ValueError(
                f"AGENT_SOFT_DEADLINE_S ({self.soft_deadline_s}) must be below "
                f"AGENT_REQUEST_DEADLINE_S ({self.request_deadline_s})"
            )
        return self

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


@lru_cache(maxsize=1)
def get_settings() -> AgentSettings:
    """The process-wide settings, read once from the environment."""
    return AgentSettings()
