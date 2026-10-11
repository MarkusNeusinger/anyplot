"""Runtime settings of the anyplot agent network.

Every value comes from an `AGENT_*` environment variable, except `ENVIRONMENT`,
which the service shares with the API and reads without the prefix, and the
Google Cloud project, which also falls back to `GOOGLE_CLOUD_PROJECT`. The
defaults are the pinned production values, so an unset variable can never select
another provider, model or location.

| Variable | Default | Meaning |
|---|---|---|
| `AGENT_PROVIDER` | `anthropic-vertex` | Model family of every agent and the scope judge: `anthropic-vertex` (Claude on Vertex AI) or `gemini` |
| `AGENT_MODEL` | `claude-haiku-5-5` | Model of every agent; an exact id that matches the provider (`gemini-...`, or a model in `CLAUDE_MODELS`) |
| `AGENT_JUDGE_MODEL` | `claude-haiku-5-5` | Model of the scope and dataset judge; same rule |
| `AGENT_LOCATION` | `eu` | Vertex AI location of every model call: `eu`, `us` or `global` |
| `AGENT_PROJECT`, else `GOOGLE_CLOUD_PROJECT` | `anyplot` | Google Cloud project that serves (and bills) the model calls |
| `AGENT_LIBRARIES` | `matplotlib,seaborn` | Enabled libraries; each needs a phase-1 runtime (`matplotlib`, `seaborn`) |
| `AGENT_RENDERER` | `remote` | Render backend: `remote` (the anyplot-renderer service, phase 1), `sandbox` (in-process sandboxes, not used in phase 1), `local` (development only) or `fake` (development and test only) |
| `AGENT_RENDER_URL` | unset | The anyplot-renderer service URL the `remote` backend calls; `https://` outside development and test |
| `AGENT_RENDER_TOKEN` | unset | Development only: an ID token for the renderer (`gcloud auth print-identity-token`); without it the backend mints one from Application Default Credentials |
| `AGENT_RENDER_IMAGE` | `anyplot-renderer:dev` | Image the `local` renderer runs with Docker (build it from `agents/renderer/Dockerfile`) |
| `AGENT_RENDER_CONCURRENCY` | `1` | Renders (one theme each) that may run at the same time; serial, because one 4 GiB instance holds one sandbox safely (spikes S and S2) |
| `AGENT_WATERMARK` | `true` | Append the footer strip ("made with any.plot()", "anyplot.ai/<spec-id>") to the PNGs the artifact route and the feedback bundle serve; `false` serves the raw renders. Gates, reviewer and `plot.py` always see the raw render |
| `AGENT_RUN_CONCURRENCY` | `1` | Pipeline runs (whole `/messages` turns) in flight per instance; the run queue holds the rest |
| `AGENT_RUNS_PER_MINUTE` | `1` | Runs that may start within any 60 seconds (a sliding window) |
| `AGENT_QUEUE_MAX_WAIT_S` | `600` | Longest wait in the run queue; it also sizes the queue (`AGENT_RUNS_PER_MINUTE` x this / 60 entries) |
| `AGENT_MAX_ATTEMPTS` | `2` | Adapter attempts per pipeline run, 1 to 3: the first and at most one repair round by default; the eval harness sets 1 or 3 to measure no repair or a second repair round |
| `AGENT_ROOT_THINKING_BUDGET` | `0` | For measurements, Claude only: 0 keeps the root's thinking off; 1 to 4,096 turns on adaptive thinking and adds that many tokens to its output cap |
| `AGENT_ADAPTER_THINKING_BUDGET` | `0` | The same for the adapter; the eval harness sets both with `--thinking-budget ROOT,ADAPTER` |
| `AGENT_MAX_LLM_CALLS` | `12` | LLM calls per request (the `RunConfig` cap) |
| `AGENT_REQUEST_TOKEN_BUDGET` | `160000` | Cost-weighted tokens per request, in input-token equivalents: an uncached input token counts 1, a cache read 0.1, a cache write 1.25, an output token 5 (`plugins/ledger.BUDGET_WEIGHTS`, the list-price ratios) |
| `AGENT_DAILY_TOKEN_BUDGET` | `2000000` | Cost-weighted tokens per user and day, weighted the same way: about 54 median runs on a warm cache, where the run cap binds first, and about 26 for a user whose every request starts cold |
| `AGENT_DAILY_PIPELINE_RUNS` | `40` | Pipeline runs per user and day |
| `AGENT_GLOBAL_DAILY_TOKEN_BUDGET` | `6000000` | Cost-weighted tokens per day across all users, three users at their daily budget; reaching it pauses the service |
| `AGENT_RENDER_TIMEOUT_S` | `60` | Seconds per render, host-enforced |
| `AGENT_REQUEST_DEADLINE_S` | `180` | Hard request deadline, enforced through `abort_signal` |
| `AGENT_SOFT_DEADLINE_S` | `140` | Soft deadline inside the pipeline; below the hard one |
| `AGENT_JUDGE_TIMEOUT_S` | `4` | Wall-clock budget of one judge verdict, its single retry and the half-second wait before it included |
| `AGENT_KEEP_REFUSALS` | `false` | Keep the text and verdict of each message the scope judge refused, in a bounded in-memory ring per session that only the feedback bundle shows; never in a log |
| `AGENT_ATTACK_STRIKES` | `3` | `attack` verdicts per user and day after which the user gets the budget refusal for the rest of the day |
| `AGENT_SESSION_IDLE_S` | `3600` | Idle seconds after which the sweeper drops a session and its stores |
| `AGENT_ALLOWED_CALLERS` | empty | Service-account emails allowed to call `/v1` (comma-separated) |
| `AGENT_SERVICE_URLS` | empty | ID-token audiences accepted on `/v1` (comma-separated): the service URL, which Cloud Run requires as the audience even for a request to a tag URL |
| `AGENT_DEV_FIXTURE` | unset | Development only: an eval fixture case id that seeds every new session |
| `ENVIRONMENT` | `production` | Deployment environment, shared with the API; `development` (the caller check off) is refused on Cloud Run |

The output caps of the model calls are constants in `models.py`, not settings, each with
ample headroom above the measured answers: root and reviewer 4,096 tokens, the adapter
8,192 for an edit-only call and 16,384 when a full file is allowed (12,288 on Gemini,
which the soft deadline bounds), and the judge 256. A thinking measurement on Claude adds
its `AGENT_*_THINKING_BUDGET` to the cap of its kind.

No `.env` file is read here: the service runs on Cloud Run environment variables only,
and the tests stay hermetic. `adk web` is different: it walks up from the agent
directory to the first `.env` it finds and loads it (`google/adk/cli/utils/envs.py`),
which in this repository is the root `.env` with production values, so run it with
`ADK_DISABLE_LOAD_DOTENV=1` (agents/README.md).
"""

import json
from functools import lru_cache
from typing import Annotated, Any, Literal, Self

from pydantic import AliasChoices, Field, PositiveFloat, PositiveInt, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from core.constants import SUPPORTED_LIBRARIES

from .code.normalise import SUPPORTED_LIBRARIES as RUNTIME_LIBRARIES
from .schemas import MAX_ATTEMPTS


FAKE_RENDERER_ENVIRONMENTS = frozenset({"development", "test"})
"""Where `AGENT_RENDERER=fake` (fixture PNGs, no code runs) is allowed."""


Location = Literal["eu", "us", "global"]
"""Vertex AI multi-region endpoints. A regional id such as europe-west4 serves
neither Gemini 3.x Flash nor the eu Claude quota, so it is refused rather than tried."""

Provider = Literal["anthropic-vertex", "gemini"]
"""Model families: Claude through Vertex AI's Anthropic endpoint, or Gemini through Vertex AI."""

Renderer = Literal["sandbox", "local", "fake", "remote"]
"""Render backends: `remote` (the anyplot-renderer service, phase 1), `sandbox` (Cloud
Run sandboxes inside this service, a stub that phase 1 does not use), `local` (Docker,
development only) and `fake` (unit tests)."""

RENDER_URL_PATTERN = r"^https?://[A-Za-z0-9.-]{1,253}(:[0-9]{1,5})?/?$"
"""A service origin: scheme, host and optional port, no path, query or credentials."""

LOCATIONS: tuple[str, ...] = ("eu", "us", "global")
MODEL_PREFIXES: dict[str, str] = {"anthropic-vertex": "claude-", "gemini": "gemini-"}
CLAUDE_MODELS: tuple[str, ...] = ("claude-haiku-5-5",)
"""Claude models that accept disabled thinking at effort low and medium (`models.make_content_config`);
Claude Opus 5.5, Sonnet 5.5 and Fable 5.1 answer disabled thinking with a 400. The structured
answers (`output_config.format`) would work on all of them."""
FIXTURE_PATTERN = r"^[a-z0-9][a-z0-9-]{0,79}$"
MAX_THINKING_BUDGET = 4_096
"""The most output room a thinking measurement may add to a Claude cap (`AGENT_*_THINKING_BUDGET`).

It keeps the adapter's full-file cap (16,384 plus 4,096) below the Anthropic SDK's limit
for a request that does not stream (about 21,300 tokens), and a full-file call that uses
all of it at about 60 s, the `pipeline.ADAPTER_P95_S` the deadline reserves."""


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

    renderer: Renderer = "remote"
    """Render backend (`AGENT_RENDERER`); `local` only in development, `fake` only in development and test."""

    render_url: str | None = Field(default=None, pattern=RENDER_URL_PATTERN)
    """The anyplot-renderer service URL (`AGENT_RENDER_URL`), also the audience of its ID token.
    The `remote` backend refuses to start without it; plain `http://` only in development and test."""

    render_token: SecretStr | None = None
    """Development only (`AGENT_RENDER_TOKEN`): an ID token for the renderer, typically from
    `gcloud auth print-identity-token`. Without it the `remote` backend mints one itself."""

    render_image: str = Field(default="anyplot-renderer:dev", pattern=r"^[A-Za-z0-9][A-Za-z0-9._/:@-]{0,199}$")
    """Image the local renderer runs (`AGENT_RENDER_IMAGE`), built from `agents/renderer/Dockerfile`."""

    render_concurrency: PositiveInt = 1
    """Theme renders that may run at the same time (`AGENT_RENDER_CONCURRENCY`), enforced for
    every backend by `render/serial.py`. Serial by default: spikes S and S2 showed one 4 GiB
    instance serves one sandbox at a time safely."""

    watermark: bool = True
    """Whether the served PNGs carry the footer strip (`AGENT_WATERMARK`, `render/watermark.py`).
    It applies to the artifact route and the feedback bundle only; the gates, the reviewer, the
    render store and the exported `plot.py` always work with the raw render. Off, both routes
    serve the raw PNGs; the eval harness turns it off so its renders compare with its baselines."""

    run_concurrency: PositiveInt = 1
    """Pipeline runs in flight per instance (`AGENT_RUN_CONCURRENCY`); the run queue holds the rest."""

    runs_per_minute: PositiveInt = 1
    """Runs that may start within any 60 seconds (`AGENT_RUNS_PER_MINUTE`), a sliding window."""

    queue_max_wait_s: PositiveInt = 600
    """Longest wait in the run queue in seconds (`AGENT_QUEUE_MAX_WAIT_S`). Queued time does not
    count toward the request deadline; the queue holds `runs_per_minute * queue_max_wait_s / 60`
    entries and refuses more with `capacity`. That length assumes runs shorter than the 60 s
    rate window: longer runs delay later starts, so admission does not guarantee a start."""

    max_attempts: int = Field(default=2, ge=1, le=MAX_ATTEMPTS)
    """Adapter attempts per pipeline run (`AGENT_MAX_ATTEMPTS`), 1 to 3, enforced by the loop
    in `pipeline.py`. The default 2 is the design's "at most one repair round"; the eval harness
    (`--max-attempts`) sets 1 to measure no repair and 3 to measure a second repair round. Every
    attempt after the first needs `ADAPTER_P95_S` plus `RENDER_P95_S` left of the soft deadline."""

    root_thinking_budget: int = Field(default=0, ge=0, le=MAX_THINKING_BUDGET)
    """Claude thinking of the root, for measurements (`AGENT_ROOT_THINKING_BUDGET`): 0 (the default)
    keeps it off. Above 0 the root thinks adaptively at its effort and its output cap grows by this
    many tokens, so the reply keeps the whole measured headroom (`models.make_content_config`).
    Claude Haiku 5.5 takes no thinking budget of its own (`budget_tokens` is a 400), so this is the
    room thinking may use, not a limit the model sees. The root replays its thinking blocks after a
    tool result; an account that enforces the history-editing check of preserved thinking may refuse
    that call, which a measurement run shows as pipeline errors."""

    adapter_thinking_budget: int = Field(default=0, ge=0, le=MAX_THINKING_BUDGET)
    """The same for the adapter (`AGENT_ADAPTER_THINKING_BUDGET`). The adapter is single-turn, so
    nothing is replayed; its structured answer (`output_config.format`) lets it think first."""

    max_llm_calls: PositiveInt = 12
    """LLM calls per request (`AGENT_MAX_LLM_CALLS`), the `RunConfig` cap."""

    request_token_budget: PositiveInt = 160_000
    """Cost-weighted tokens per request (`AGENT_REQUEST_TOKEN_BUDGET`), in input-token equivalents
    (`plugins/ledger.BUDGET_WEIGHTS`). A reviewed run with two adapter attempts books a median of
    about 39,500 with a warm prompt cache (72,200 plain tokens) and about 77,700 on a cold one,
    where each agent's first call writes its prefix; with a second review the costliest run comes
    to about 115,000, and with three attempts about 117,300, so the budget leaves about 36 % on top.
    A review starts only while `pipeline.REVIEW_RESERVE_TOKENS` is left for it and the root's
    closing reply."""

    daily_token_budget: PositiveInt = 2_000_000
    """Cost-weighted tokens per user and day (`AGENT_DAILY_TOKEN_BUDGET`), weighted like the request
    budget: about 54 median runs with a warm cache, where the 40 runs of `daily_pipeline_runs`
    bind first, and about 26 for a user whose every request starts cold (77,700 each), where
    this budget binds."""

    daily_pipeline_runs: PositiveInt = 40
    """Pipeline runs per user and day (`AGENT_DAILY_PIPELINE_RUNS`)."""

    global_daily_token_budget: PositiveInt = 6_000_000
    """Cost-weighted tokens per day across all users (`AGENT_GLOBAL_DAILY_TOKEN_BUDGET`), three users
    at their daily budget; reaching it pauses the service."""

    render_timeout_s: PositiveInt = 60
    """Seconds per render, host-enforced (`AGENT_RENDER_TIMEOUT_S`)."""

    request_deadline_s: PositiveInt = 180
    """Hard request deadline in seconds, enforced through `abort_signal` (`AGENT_REQUEST_DEADLINE_S`)."""

    soft_deadline_s: PositiveInt = 140
    """Soft deadline in seconds inside the pipeline (`AGENT_SOFT_DEADLINE_S`); below the hard one."""

    judge_timeout_s: PositiveFloat = 4.0
    """Seconds for one judge verdict including its one retry and the back-off before it (`AGENT_JUDGE_TIMEOUT_S`)."""

    keep_refusals: bool = False
    """Keep the text and verdict of every message the scope judge refused (`AGENT_KEEP_REFUSALS`), in a
    bounded in-memory ring per session that only the feedback bundle shows, so false refusals can be
    found and promoted to the scope eval. Off by default; for phase 1, where only the owner's data is
    in the service. The text never reaches a log."""

    attack_strikes: PositiveInt = 3
    """`attack` verdicts of the scope or dataset judge per user and day (`AGENT_ATTACK_STRIKES`) after
    which the user gets the budget refusal for the rest of the (UTC) day."""

    session_idle_s: PositiveInt = 3600
    """Idle seconds before the sweeper drops a session (`AGENT_SESSION_IDLE_S`)."""

    allowed_callers: Annotated[list[str], NoDecode] = []
    """Service-account emails allowed to call `/v1` (`AGENT_ALLOWED_CALLERS`, comma-separated).
    Empty means no caller passes the check outside development."""

    service_urls: Annotated[list[str], NoDecode] = []
    """ID-token audiences accepted on `/v1` (`AGENT_SERVICE_URLS`, comma-separated): the
    service URL, which Cloud Run requires as `aud` even for a request to a traffic tag's
    URL. Empty means no caller passes outside development."""

    dev_fixture: str | None = Field(default=None, pattern=FIXTURE_PATTERN)
    """Eval fixture case that seeds every new session (`AGENT_DEV_FIXTURE`); development only."""

    environment: str = Field(default="production", validation_alias="ENVIRONMENT")
    """Deployment environment (`ENVIRONMENT`, shared with the API, no prefix). Unset is
    `production`, so a missing variable never skips the caller check."""

    cloud_run_service: str | None = Field(default=None, validation_alias="K_SERVICE")
    """The Cloud Run service name (`K_SERVICE`, set by Cloud Run itself); development is refused when set."""

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

    @field_validator("dev_fixture", "render_url", "render_token", mode="before")
    @classmethod
    def _blank_is_none(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            return None
        return value.strip() if isinstance(value, str) else value

    @field_validator("render_url")
    @classmethod
    def _origin_without_slash(cls, value: str | None) -> str | None:
        return value.rstrip("/") if value else value

    @field_validator("libraries")
    @classmethod
    def _known_libraries(cls, value: list[str]) -> list[str]:
        """Every enabled library is a catalogue library with a runtime (normaliser and adapter).

        One registry for the settings, `/v1/status`, eligibility and the adapter
        construction: a library the runtime cannot serve is refused here instead of
        being reported as enabled and failing at session creation.
        """
        unknown = sorted(set(value) - SUPPORTED_LIBRARIES)
        if unknown:
            raise ValueError(f"unknown libraries in AGENT_LIBRARIES: {', '.join(unknown)}")
        without_runtime = sorted(set(value) - RUNTIME_LIBRARIES)
        if without_runtime:
            raise ValueError(
                f"libraries with no runtime in AGENT_LIBRARIES: {', '.join(without_runtime)} "
                f"(the phase-1 runtime serves {', '.join(sorted(RUNTIME_LIBRARIES))})"
            )
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
            if self.provider == "anthropic-vertex" and value not in CLAUDE_MODELS:
                raise ValueError(
                    f"{name}={value!r} is not a supported Claude model ({', '.join(CLAUDE_MODELS)}): "
                    "the agents run with thinking disabled, which newer Claude models refuse with a 400"
                )
        if self.provider != "anthropic-vertex" and (self.root_thinking_budget or self.adapter_thinking_budget):
            raise ValueError(
                "AGENT_ROOT_THINKING_BUDGET and AGENT_ADAPTER_THINKING_BUDGET apply to Claude only; "
                "Gemini thinks by a level per agent kind"
            )
        if self.is_development and self.cloud_run_service:
            raise ValueError(
                "ENVIRONMENT=development is refused on Cloud Run (K_SERVICE is set): it would skip the caller check"
            )
        if self.renderer == "local" and self.environment != "development":
            raise ValueError(
                f"AGENT_RENDERER=local is allowed only when ENVIRONMENT=development, not {self.environment!r}"
            )
        if self.renderer == "fake" and self.environment not in FAKE_RENDERER_ENVIRONMENTS:
            raise ValueError(
                "AGENT_RENDERER=fake runs no code and returns fixture PNGs; it is allowed only when "
                f"ENVIRONMENT is development or test, not {self.environment!r}"
            )
        if self.dev_fixture is not None and self.environment != "development":
            raise ValueError(
                f"AGENT_DEV_FIXTURE is allowed only when ENVIRONMENT=development, not {self.environment!r}"
            )
        if (
            self.render_url
            and self.render_url.startswith("http://")
            and self.environment not in FAKE_RENDERER_ENVIRONMENTS
        ):
            raise ValueError(
                "AGENT_RENDER_URL must be https:// outside development and test: the request carries an ID token"
            )
        if self.render_token is not None and not self.is_development:
            raise ValueError(
                f"AGENT_RENDER_TOKEN is allowed only when ENVIRONMENT=development, not {self.environment!r}: "
                "a deployed service mints its own token from the metadata server"
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
