"""Runtime settings of the anyplot agent network.

Every value comes from an `AGENT_*` environment variable, except `ENVIRONMENT`,
which the service shares with the API and reads without the prefix. The defaults
are the pinned production values of docs/concepts/agent-network.md ("Serving and
infrastructure"), so an unset variable can never select another model or location.

No `.env` file is read: the service runs on Cloud Run environment variables only,
`adk web` loads its own `.env` from the agent directory into the environment, and
the tests stay hermetic.
"""

import json
from functools import lru_cache
from typing import Annotated, Any, Literal, Self

from pydantic import Field, PositiveInt, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from core.constants import SUPPORTED_LIBRARIES


Location = Literal["eu", "us", "global"]
"""Vertex AI multi-region endpoints. A regional id such as europe-west4 serves no
Gemini 3.x Flash model, so it is refused rather than tried."""

Renderer = Literal["sandbox", "local", "fake", "remote"]
"""Render backends: `sandbox` (Cloud Run sandboxes, phase 1), `local` (Docker,
development only), `fake` (unit tests) and `remote` (the phase-2 renderer split)."""

LOCATIONS: tuple[str, ...] = ("eu", "us", "global")


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

    model: str = "gemini-3.8-flash"
    """Gemini model of every agent (`AGENT_MODEL`). An exact id, never an alias."""

    judge_model: str = "gemini-3.5-flash-lite"
    """Gemini model of the scope judge (`AGENT_JUDGE_MODEL`)."""

    location: Location = "eu"
    """Vertex AI location of every model call (`AGENT_LOCATION`): `eu`, `us` or `global`."""

    libraries: Annotated[list[str], NoDecode] = Field(default=["matplotlib", "seaborn"], min_length=1)
    """Libraries with an enabled runtime (`AGENT_LIBRARIES`, comma-separated)."""

    renderer: Renderer = "sandbox"
    """Render backend (`AGENT_RENDERER`); `local` only in development."""

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

    allowed_callers: Annotated[list[str], NoDecode] = []
    """Service-account emails allowed to call `/v1` (`AGENT_ALLOWED_CALLERS`, comma-separated).
    Empty means no caller passes the check outside development."""

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
            raise ValueError(f"{value!r} is a floating alias; pin an exact model id such as 'gemini-3.8-flash'")
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

    @field_validator("libraries", "allowed_callers", mode="before")
    @classmethod
    def _parse_list(cls, value: Any) -> Any:
        return _split_list(value)

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
        """The local renderer runs Docker on the host and is for development only."""
        if self.renderer == "local" and self.environment != "development":
            raise ValueError(
                f"AGENT_RENDERER=local is allowed only when ENVIRONMENT=development, not {self.environment!r}"
            )
        if self.soft_deadline_s >= self.request_deadline_s:
            raise ValueError(
                f"AGENT_SOFT_DEADLINE_S ({self.soft_deadline_s}) must be below "
                f"AGENT_REQUEST_DEADLINE_S ({self.request_deadline_s})"
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> AgentSettings:
    """The process-wide settings, read once from the environment."""
    return AgentSettings()
