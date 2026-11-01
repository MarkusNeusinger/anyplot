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
| `AGENT_TRANSPORT` | `vertex` | How Claude calls travel: `vertex` (live) or `claude-cli` (development and test only: the local Claude Code CLI on your subscription; calls it cannot answer, the root's, go to Vertex AI; `cli_transport.py`) |
| `AGENT_ADAPTER_MODEL`, `AGENT_REVIEWER_MODEL` | unset | `claude-cli` only: the adapter's or the reviewer's model for an experiment, any of `cli_transport.CLI_MODELS` |
| `AGENT_REVIEWER_MODE` | `catalogue` | The reviewer's rubric: `catalogue` (the offline scorer's catalogue rubric; the verdict decided by code from the points) or `checklist` (the narrow checklist, live before 2026-10-13) |
| `AGENT_REVIEW_BAR` | `0.95` | `catalogue` reviews: the share of the technical points (VQ, SC, DQ) a render needs to need no repair (1.0 before 2026-10-14; owner decision pending) |
| `AGENT_STATUS_BAR` | `0.95` | `catalogue` reviews: the ship bar; a shipped render at or above it, with no measured gate or validator finding left, shows without notes (`ok`) |
| `AGENT_STATUS_SCORE` | `0` | `catalogue` reviews: the review score (0 to 100) a shipped render also needs for `ok`; 0 turns the condition off (owner decision pending) |
| `AGENT_GATE_REPAIR` | `review` | When measured findings of a render (advisory gate lines, ADAPTATION findings) start a repair: `review` (they go to the self-review and, as gate notes, to the review, and a round whose render still has them after its review is repaired with them) or `first` (straight to the repair round, skipping the self-review and the review; live before 2026-10-14) |
| `AGENT_EXPECT_CHECK` | `repair` | A text or number format the user asked for (the root's `expected_texts`) that the render's drawn texts do not show, or, for a render without drawn texts on a runtime whose reviewer checks them (R, altair, pygal, lets-plot), that the review cannot find in the image: `repair` (a finding the repair round gets, and an unfixed miss is a residual line), `note` (the residual line only) or `off` (owner decision pending) |
| `AGENT_SHIP_CLEAN_MARGIN` | `3` | `catalogue` reviews with `AGENT_SHIP_BEST`: a render without measured findings ships over a higher-scored one with them when it meets the ship bar or is at most this many points below it |
| `AGENT_REPAIR_SELF_REVIEW` | `false` | With `AGENT_SELF_REVIEW` on, whether a repair round proofreads its render too, not only the first round |
| `AGENT_SHIP_BEST` | `true` | `catalogue` reviews: review every render and ship the best-scored version, not the last |
| `AGENT_CHECK_RETRY` | `true` | An adapter answer that fails its check gets one more call in the same round (a full file allowed) instead of ending it |
| `AGENT_SELF_REVIEW` | `true` | The adapter sees its first render once and may improve it before the review; not a repair, no extra round |
| `AGENT_HIGHLIGHTS`, `AGENT_SCORER_HIGHLIGHTS` | `off` | Experiments: let the adapter add one data-derived highlight, and exempt it from SC-01 in the scorer rubric |
| `AGENT_CLI_CONCURRENCY` | `3` | `claude-cli` only: CLI calls at the same time |
| `AGENT_CLI_CALL_LOG` | unset | `claude-cli` only: a file each CLI call appends one JSON line to (model, effort, seconds, ok) |
| `AGENT_LOCATION` | `eu` | Vertex AI location of every model call: `eu`, `us` or `global` |
| `AGENT_PROJECT`, else `GOOGLE_CLOUD_PROJECT` | `anyplot` | Google Cloud project that serves (and bills) the model calls |
| `AGENT_LIBRARIES` | `matplotlib,seaborn` | Enabled libraries; each needs a runtime in the registry (`RUNTIME_LIBRARIES`: `matplotlib`, `seaborn`, `plotnine`, `altair`, `pygal` and `letsplot` on the Python runtime, `plotly` and `bokeh` on it since 2026-10-31, `ggplot2` on the R runtime since 2026-10-29, `makie` on the Julia runtime since 2026-10-30, `chartjs`, `d3`, `echarts` and `highcharts` on the JavaScript runtime since 2026-10-30, `muix` on it since 2026-10-31: all 15). The default stays `matplotlib,seaborn`; the deploy (`agents/cloudbuild.yaml` `_LIBRARIES`) names every library with a runtime for the admin's live tests (the six Python ones since 2026-10-28, ggplot2 since 2026-10-29, Makie, Chart.js, D3, ECharts and Highcharts since 2026-10-30, MUI X, plotly and bokeh since 2026-10-31), and each library's eval matrix gates the public release |
| `AGENT_RENDERER` | `remote` | Render backend: `remote` (the anyplot-renderer service, phase 1), `sandbox` (in-process sandboxes, not used in phase 1), `local` (development only) or `fake` (development and test only) |
| `AGENT_RENDER_URL` | unset | The anyplot-renderer service URL the `remote` backend calls; `https://` outside development and test |
| `AGENT_RENDER_TOKEN` | unset | Development only: an ID token for the renderer (`gcloud auth print-identity-token`); without it the backend mints one from Application Default Credentials |
| `AGENT_RENDER_IMAGE` | `anyplot-renderer:dev` | Image the `local` renderer runs with Docker (build it from `agents/renderer/Dockerfile`) |
| `AGENT_RENDER_CONCURRENCY` | `1` | Renders (one theme each) that may run at the same time; serial, because one 4 GiB instance holds one sandbox safely (spikes S and S2) |
| `AGENT_WATERMARK` | `true` | Append the footer strip ("made with any.plot()", "anyplot.ai/<spec-id>") to the PNGs the artifact route and the feedback bundle serve; `false` serves the raw renders. Gates, reviewer and `plot.py` always see the raw render |
| `AGENT_RUN_CONCURRENCY` | `5` | Sandbox runs (a `plot_pipeline` or `run_data_code` call, held until its turn ends) in flight in the whole instance, every lane together (1 before 2026-11-01); the run queue holds the rest. A chat turn without one never enters the queue |
| `AGENT_RUNS_PER_MINUTE` | `6` | Sandbox runs that may start within any 60 seconds (a sliding window), spaced at least 60 / this seconds apart: one start every 10 seconds at the default, in every lane (1 a minute before 2026-11-01); one start per turn |
| `AGENT_QUEUE_MAX_WAIT_S` | `600` | Longest wait in the run queue; it also sizes the queue (`AGENT_RUNS_PER_MINUTE` x this / 60 entries, 60 at the defaults) |
| `AGENT_USER_MAX_RUNS` | `2` | Sandbox runs one public user may have queued or running at the same time, across all their sessions (browser windows; 3 before 2026-11-01); one more ends its turn with `error{code:"run_limit"}`. Everything else in a session (chat turns, pastes, data steps, the theme toggle, file conversions) runs at once, whatever the user's other sessions do |
| `AGENT_ADMIN_USER_MAX_RUNS` | `5` | The same for an admin (`X-Anyplot-Tier: admin` from an allowed caller), whose runs share the concurrency and the rate with everyone's; `GET /v1/status` reports it to an admin as `user_max_runs`, which the fan-out keeps to |
| `AGENT_USER_MESSAGES_PER_MINUTE` | `10` | Chat turns (typed messages and actions) per user within any 60 seconds; more get the `rate_limited` refusal before the scope judge runs. An admin is exempt |
| `AGENT_USER_MESSAGES_PER_DAY` | `200` | Chat turns per user and UTC day; more get the `daily_limit` refusal before the scope judge runs. An admin is exempt |
| `AGENT_SESSION_REFUSALS` | `3` | Scope-judge refusals (`out_of_scope` or `attack`, not `needs_data`, and `other_library` only with `AGENT_OTHER_LIBRARY_COUNTS`) after which the session is closed: the last of them and every later turn, and every paste, get the `session_closed` refusal |
| `AGENT_OTHER_LIBRARY_COUNTS` | `false` | Whether an `other_library` refusal (this plot in another library or language) counts toward `AGENT_SESSION_REFUSALS` |
| `AGENT_SESSION_CLOSE_WARNING` | `true` | The counted refusal one before the closing one carries the fixed `close_warning` suffix |
| `AGENT_USER_PASTES_PER_MINUTE` | `10` | Dataset pastes per user within any 60 seconds, across sessions; more get `429 rate_limited` before any parser or model reads the paste |
| `AGENT_USER_PASTES_PER_DAY` | `100` | Dataset pastes per user and UTC day; more get `429 daily_limit` |
| `AGENT_USER_CONVERSIONS_PER_MINUTE` | `5` | File conversions (a dropped spreadsheet, Parquet, Arrow or NumPy file read in the sandbox) per user within any 60 seconds, across sessions; more get `429 rate_limited`. The paste that follows a conversion counts as one paste |
| `AGENT_USER_CONVERSIONS_PER_DAY` | `30` | File conversions per user and UTC day; more get `429 daily_limit` |
| `AGENT_CONVERT_TIMEOUT_S` | `10` | Seconds one conversion may run in the sandbox, at most 15 |
| `AGENT_CONVERT_SLOT_WAIT_S` | `20` | Seconds a conversion waits for the render slot, behind every pipeline render; then `503 capacity` |
| `AGENT_MAX_ATTEMPTS` | `2` | Adapter attempts per pipeline run, 1 to 3: the first and at most one repair round by default; the eval harness sets 1 or 3 to measure no repair or a second repair round |
| `AGENT_ROOT_THINKING_BUDGET` | `1024` | Claude only: adaptive thinking of the root, with that many tokens added to its output cap; 0 turns it off (the 2026-10-11 measurement: with thinking on root and adapter every run passed the gates and 51.6 % ended `ok`, against 91.0 % and 28.7 % without) |
| `AGENT_ADAPTER_THINKING_BUDGET` | `8192` | The same for the adapter (2,048 before 2026-10-14, when effort `high` thought past it); the eval harness overrides both with `--thinking-budget ROOT,ADAPTER` |
| `AGENT_REVIEWER_THINKING_BUDGET` | `4096` | The same for the reviewer; 0 turns its thinking off |
| `AGENT_ROOT_EFFORT`, `AGENT_ADAPTER_EFFORT`, `AGENT_REVIEWER_EFFORT` | `medium`, `high`, `high` | Claude's effort per agent kind (`low`, `medium`, `high`), set by the 2026-10-13 measurements; on the claude-cli transport also how much the CLI thinks |
| `AGENT_MAX_LLM_CALLS` | `16` | LLM calls per request (the `RunConfig` cap) |
| `AGENT_REQUEST_TOKEN_BUDGET` | `800000` | Cost-weighted tokens per request, in input-token equivalents: an uncached input token counts 1, a cache read 0.1, a cache write 1.25, an output token 5 (`plugins/ledger.BUDGET_WEIGHTS`, the list-price ratios) |
| `AGENT_DAILY_TOKEN_BUDGET` | `10000000` | Cost-weighted tokens per user and day, weighted the same way: about $1 at Claude Haiku 5.5's $0.10 per million input-token equivalents (8,000,000 before 2026-11-01). An admin is exempt |
| `AGENT_DAILY_PIPELINE_RUNS` | `50` | Pipeline runs per user and day (40 before 2026-11-01). An admin is exempt |
| `AGENT_GLOBAL_DAILY_TOKEN_BUDGET` | `100000000` | Cost-weighted tokens per day across all users, admins included: about $10, the runaway guard of the whole service (24,000,000 before 2026-11-01); reaching it pauses the service |
| `AGENT_RENDER_TIMEOUT_S` | `60` | Seconds per render, host-enforced |
| `AGENT_DATA_CODE` | `true` | Whether the root has `run_data_code`: a data-generating snippet (Python, JavaScript, R, a formula) translated to Python, validated and run in the renderer's sandbox |
| `AGENT_DATA_RUN_TIMEOUT_S` | `20` | Seconds one data snippet may run, at most 30 |
| `AGENT_DAILY_DATA_RUNS` | `30` | `run_data_code` runs per user and day. An admin is exempt |
| `AGENT_NARROWED_BINDINGS` | `keep` | The root's `set_bindings` that only leaves out confirmed number series (`y2`, `y3`, ...): `keep` keeps the user's confirmation, `reset` asks for `.confirm()` again |
| `AGENT_REQUEST_DEADLINE_S` | `540` | Hard request deadline, enforced through `abort_signal` |
| `AGENT_SOFT_DEADLINE_S` | `480` | Soft deadline inside the pipeline; below the hard one |
| `AGENT_JUDGE_TIMEOUT_S` | `4` | Wall-clock budget of one judge verdict, its single retry and the half-second wait before it included |
| `AGENT_KEEP_REFUSALS` | `false` | Keep the text and verdict of each message the scope judge refused, in a bounded in-memory ring per session that only the feedback bundle shows; never in a log |
| `AGENT_ATTACK_STRIKES` | `3` | `attack` verdicts per user and day after which the user gets the `locked_out` refusal (and a paste `429 locked_out`) for the rest of the day |
| `AGENT_SESSION_IDLE_S` | `3600` | Idle seconds after which the sweeper drops a session and its stores |
| `AGENT_ALLOWED_CALLERS` | empty | Service-account emails allowed to call `/v1` (comma-separated) |
| `AGENT_SERVICE_URLS` | empty | ID-token audiences accepted on `/v1` (comma-separated): the service URL, which Cloud Run requires as the audience even for a request to a tag URL |
| `AGENT_DEV_FIXTURE` | unset | Development only: an eval fixture case id that seeds every new session |
| `ENVIRONMENT` | `production` | Deployment environment, shared with the API; `development` (the caller check off) is refused on Cloud Run |

The output caps of the model calls are constants in `models.py`, not settings, each with
ample headroom above the measured answers: root and reviewer 4,096 tokens, the adapter
40,960 on Claude for edit-only and full-file calls since 2026-10-30 (8,192 and 12,288 on
Gemini, which the soft deadline bounds), and the judge 256. A thinking measurement on
Claude adds its `AGENT_*_THINKING_BUDGET` to the cap of its kind.

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

from .cli_transport import CLI_MODELS
from .render.runtimes import RUNTIME_LIBRARIES
from .schemas import MAX_ATTEMPTS


FAKE_RENDERER_ENVIRONMENTS = frozenset({"development", "test"})
"""Where `AGENT_RENDERER=fake` (fixture PNGs, no code runs) is allowed."""


Location = Literal["eu", "us", "global"]
"""Vertex AI multi-region endpoints. A regional id such as europe-west4 serves
neither Gemini 3.x Flash nor the eu Claude quota, so it is refused rather than tried."""

Provider = Literal["anthropic-vertex", "gemini"]
"""Model families: Claude through Vertex AI's Anthropic endpoint, or Gemini through Vertex AI."""

Effort = Literal["low", "medium", "high"]
"""Claude efforts an agent kind may run at; Haiku 5.5 takes disabled thinking up to `high`."""

ReviewerMode = Literal["checklist", "catalogue"]
"""The reviewer's rubric: the catalogue rubric the offline scorer uses (live since 2026-10-13) or the
narrow checklist of phase 1 (legacy)."""

Transport = Literal["vertex", "claude-cli"]
"""How Claude calls travel: Vertex AI (live), or the local Claude Code CLI for experiments."""

TRANSPORT_ENVIRONMENTS = frozenset({"development", "test"})
"""Where `AGENT_TRANSPORT=claude-cli` is allowed: never on a deployed service."""

CLI_JUDGE_TIMEOUT_S = 90.0
"""The judge's budget on the CLI, which starts a process per call: the live 4 s would fail closed."""

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
MAX_THINKING_BUDGET = 8_192
"""The most output room thinking may add to a Claude cap (`AGENT_*_THINKING_BUDGET`).

Since 2026-10-30 the adapter's cap with this room (40,960 plus 8,192) is past the Anthropic
SDK's limit for a request that does not stream (about 21,300 tokens), which the Vertex client's
own timeout lifts (`models.CLAUDE_REQUEST_TIMEOUT_S`); a call that uses all of it takes about
143 s, which the soft deadline holds."""


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

    transport: Transport = "vertex"
    """How Claude calls travel (`AGENT_TRANSPORT`): `vertex` (live), or `claude-cli` (development
    and test only: the local Claude Code CLI on the developer's subscription, `cli_transport.py`)."""

    adapter_model: str | None = None
    """Experiments: the adapter's model (`AGENT_ADAPTER_MODEL`); on `claude-cli` any of `CLI_MODELS`."""

    reviewer_model: str | None = None
    """Experiments: the reviewer's model (`AGENT_REVIEWER_MODEL`); on `claude-cli` any of `CLI_MODELS`."""

    reviewer_mode: ReviewerMode = "catalogue"
    """What the reviewer judges with (`AGENT_REVIEWER_MODE`): `catalogue` (live since 2026-10-13: the
    offline scorer's catalogue rubric, `scoring.py`; the code decides from the points, and the defect lines
    feed the repair) or `checklist` (the narrow checklist of `prompts/reviewer.md`, live before). The
    2026-10-13 measurement: the checklist named 2 of 37 agreed technical deductions, the rubric on Haiku 28."""

    review_bar: float = Field(default=0.95, gt=0, le=1)
    """`catalogue` reviews only (`AGENT_REVIEW_BAR`): the share of the technical points (VQ, SC, DQ) a
    render needs, with no technical item at zero, to need no repair. Of the 55 technical points, 0.95
    lets a render lose two without a repair round; 1.0 (before 2026-10-14) sent nearly every render
    to the repair. `AGENT_SHIP_BEST` keeps a repair that scores lower from shipping. A product choice:
    the measurement is in `agents/README.md`, the value the owner's."""

    status_bar: float = Field(default=0.95, gt=0, le=1)
    """`catalogue` reviews only (`AGENT_STATUS_BAR`): the owner's ship bar. A shipped render at or above
    it is shown without the review's notes (`ok`, unless a measured finding is left, see
    `pipeline.finish`); below it the review's lines become residual notes (`needs_attention`)."""

    status_score: int = Field(default=0, ge=0, le=100)
    """`catalogue` reviews only (`AGENT_STATUS_SCORE`): the review score a shipped render also needs
    to show without notes; 0 turns the condition off. A product choice left to the owner: the catalogue
    originals score about 80 on the user scorer, so a value above that would mark plots as good as the
    catalogue's own as `needs_attention`."""

    gate_repair: Literal["review", "first"] = "review"
    """When the measured findings of a render that passed the host gates start a repair (`AGENT_GATE_REPAIR`):
    the advisory gate lines (G3, G5, G7, G8, G9, G10, G11, G12) and the ADAPTATION validator's soft findings.

    `review`: they go to the round's self-review as findings, then to the review as gate notes, and a
    round whose render still has them after its review goes to the repair with them and the review's
    lines together. `first` (live before 2026-10-14): they send the round straight to the repair,
    skipping its self-review and review, so a run with two rounds repaired them blind and reviewed only
    the repair. Either way a render whose canvas missed goes straight to the repair."""

    expect_check: Literal["repair", "note", "off"] = "repair"
    """What a requested text or number format the render does not show does (`AGENT_EXPECT_CHECK`,
    `grounding.expected_misses` over the root's `expected_texts`, or `grounding.reviewed_misses` when a
    render without drawn texts hands them to its review, `RuntimeAdapter.review_texts`).

    `repair`: it is a measured finding like an advisory gate line: the self-review and the review see
    it, a round whose render still misses it is repaired with it, and a shipped render that still
    misses it carries it as a residual line (`needs_attention`); a miss the review reports sends its
    round to the repair whatever the points, as a visible defect does. `note`: only the residual line,
    no repair round for it. `off`: no check, and no texts for the review. The choice between `repair`
    and `note` is a product decision left to the owner: a repair round costs about 40 s, a false miss
    would spend it."""

    repair_self_review: bool = False
    """`AGENT_REPAIR_SELF_REVIEW`: whether a repair round proofreads its render before the review, as the
    first round does. Off (the default), round 1 still proofreads and repair rounds go straight to the
    review; `AGENT_SELF_REVIEW=false` turns every proofread off, this setting included. Off since
    2026-10-14: the reviewer scores the repaired render anyway, and `AGENT_SHIP_BEST` ships the better of
    the two; the measurement is in `agents/README.md`."""

    ship_clean_margin: int = Field(default=3, ge=0, le=100)
    """`catalogue` reviews with `AGENT_SHIP_BEST` (`AGENT_SHIP_CLEAN_MARGIN`): a render without measured
    findings ships over a higher-scored one with them when it meets the ship bar or scores at most this
    many points below it; otherwise the higher score ships with its findings as notes (owner, 2026-10-14)."""

    highlights: Literal["off", "data"] = "off"
    """Experiments (`AGENT_HIGHLIGHTS`): `data` lets the adapter add at most one highlight of a
    salient feature of the user's data, computed from `df` (`prompts/adapter_highlights.md`)."""

    ship_best: bool = True
    """`catalogue` reviews only (`AGENT_SHIP_BEST`): every render is reviewed, and the best-scored
    version ships instead of the last one."""

    self_review: bool = True
    """`AGENT_SELF_REVIEW`: after the first render that passes the gates, the adapter sees that render
    once and may improve its code before the review. It is the adapter proofreading its work, not a
    repair (owner, 2026-10-13): it gets an attempt on top of `AGENT_MAX_ATTEMPTS` and no round of its own."""

    check_retry: bool = True
    """`AGENT_CHECK_RETRY`: an adapter answer that fails its check (edits that do not apply, a validator
    finding, a broken schema, code that crashes) gets one more call in the same round, which may send a
    full file, instead of ending the round; a second miss ends it. On since 2026-10-13: a failed edit
    apply in a repair round had shipped an earlier, unreviewed render. A miss that only changed the
    protected theme statements, with no retry left, is restored instead (`edits.restore_protected`)."""

    repair_sees_render: bool = False
    """Experiments (`AGENT_REPAIR_SEES_RENDER`): a repair sees the render the review's findings describe,
    and its self-review sees that render next to the repaired one, so it can tell whether it got better."""

    cli_concurrency: PositiveInt = 3
    """`claude-cli` only: CLI calls at the same time (`AGENT_CLI_CONCURRENCY`)."""

    cli_call_log: str | None = None
    """`claude-cli` only: a file each CLI call appends one JSON line to (`AGENT_CLI_CALL_LOG`)."""

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

    run_concurrency: PositiveInt = 5
    """Sandbox runs in flight in the whole instance, every lane together (`AGENT_RUN_CONCURRENCY`); the run queue holds
    the rest. Only a turn whose root calls `plot_pipeline` or `run_data_code` takes a run, from that call to the end of
    the turn. 5 since 2026-11-01 (owner decision; 1 before): a 15-library fan-out took about 20 minutes through one
    slot and one start a minute, while each run renders for about 5 s of its 60 to 240 s and spends the rest in model
    calls that wait on the network. Renders stay serial in the one render slot (`AGENT_RENDER_CONCURRENCY`)."""

    runs_per_minute: PositiveInt = 6
    """Sandbox runs that may start within any 60 seconds (`AGENT_RUNS_PER_MINUTE`), a sliding window, and spaced at
    least `60 / runs_per_minute` seconds apart (`RunQueue.start_gap_s`), in every lane; a chat turn without a sandbox
    run never counts. 6 since 2026-11-01 (owner decision, "1 start every 10 s"; 1 before): the gap keeps the five
    runs of a fan-out from reaching the render slot at the same moment."""

    queue_max_wait_s: PositiveInt = 600
    """Longest wait in the run queue in seconds (`AGENT_QUEUE_MAX_WAIT_S`). Queued time does not
    count toward the request deadline; the queue holds `runs_per_minute * queue_max_wait_s / 60`
    entries (60 at the defaults) and refuses more with `capacity`. That length assumes runs end
    within the time their starts take: longer runs delay later starts, so admission does not
    guarantee a start."""

    user_max_runs: PositiveInt = 2
    """Sandbox runs one public user may have in the run queue at the same time, waiting and running together, across
    all their sessions (`AGENT_USER_MAX_RUNS`; 2 since 2026-11-01, 3 before). Owner decision of 2026-10-21: a user's
    browser windows work in parallel, and only their sandbox runs share the queue; one more than this ends its turn
    with `error{code:"run_limit"}` instead of `capacity`, so the page can say that the user's own runs fill it."""

    admin_user_max_runs: PositiveInt = 5
    """The same for an admin (`AGENT_ADMIN_USER_MAX_RUNS`, owner decision of 2026-11-01): the admin's runs share the
    concurrency and the rate with everyone's; `GET /v1/status` reports this cap to an admin as `user_max_runs`, and
    the fan-out starts at most that many plots at once."""

    user_messages_per_minute: PositiveInt = 10
    """Chat turns per user within any 60 seconds (`AGENT_USER_MESSAGES_PER_MINUTE`), typed messages and actions
    alike, counted in the usage book. Checked before the scope judge, so a flood costs no model call: since chat turns
    no longer wait in the run queue (2026-10-14), this is what bounds them. An admin is exempt (2026-11-01): a fan-out
    starts a turn per library."""

    user_messages_per_day: PositiveInt = 200
    """Chat turns per user and UTC day (`AGENT_USER_MESSAGES_PER_DAY`), checked like the minute's; an admin is
    exempt."""

    session_refusals: PositiveInt = 3
    """Scope-judge refusals of type `out_of_scope` or `attack` after which a session is closed
    (`AGENT_SESSION_REFUSALS`): the refusal that reaches it and every later turn of the session answer
    `session_closed`, and the user starts a new session. `needs_data` refusals never count. Counted from the
    session's withheld messages, so it ends with the session."""

    other_library_counts: bool = False
    """Whether an `other_library` refusal (this plot in another library or language, answered with a fixed
    pointer to the catalogue) counts toward `session_refusals` (`AGENT_OTHER_LIBRARY_COUNTS`). Off by default:
    the request is in good faith and close to the scope, so it never closes a session (live test of
    2026-10-14). Owner decision of 2026-10-14: it does not count."""

    session_close_warning: bool = True
    """Whether the counted refusal that leaves a session one refusal before it closes carries the fixed
    `close_warning` suffix ("One more request outside this scope will close this chat.";
    `AGENT_SESSION_CLOSE_WARNING`). Owner decision of 2026-10-14: on."""

    user_pastes_per_minute: PositiveInt = 10
    """Dataset pastes per user within any 60 seconds (`AGENT_USER_PASTES_PER_MINUTE`), across sessions, checked
    before any parser or model reads the paste: each paste may spend dataset-judge calls (one per ~4 kB part
    of the judged view), a notes-judge call and a transcriber call. Only a paste that reaches the pre-filter or
    a model counts (a formula, code or unparseable text is refused for free). More get `429 rate_limited`.
    Owner decision of 2026-10-14."""

    user_pastes_per_day: PositiveInt = 100
    """Dataset pastes per user and UTC day (`AGENT_USER_PASTES_PER_DAY`), checked like the minute's; more get
    `429 daily_limit`. Owner decision of 2026-10-14."""

    user_conversions_per_minute: PositiveInt = 5
    """File conversions per user within any 60 seconds (`AGENT_USER_CONVERSIONS_PER_MINUTE`), across sessions: a
    dropped spreadsheet, Parquet, Arrow or NumPy file read in the renderer's sandbox (`POST .../dataset/convert`).
    Its own counter, apart from the pastes: a conversion spends sandbox time, no tokens, and the paste that
    follows it counts as one paste. More get `429 rate_limited`. Owner decision of 2026-10-15."""

    user_conversions_per_day: PositiveInt = 30
    """File conversions per user and UTC day (`AGENT_USER_CONVERSIONS_PER_DAY`); more get `429 daily_limit`."""

    convert_timeout_s: float = Field(default=10.0, gt=0, le=15)
    """Seconds one conversion may run in the sandbox (`AGENT_CONVERT_TIMEOUT_S`), host-enforced; at most the
    renderer's 15 s (`wire.MAX_CONVERT_TIMEOUT_S`). Short, so a conversion never holds the render slot for long."""

    convert_slot_wait_s: float = Field(default=20.0, gt=0, le=60)
    """Seconds a conversion waits for the instance's render slot (`AGENT_CONVERT_SLOT_WAIT_S`), behind every
    pipeline render (the `toggle` lane); past it the route answers `503 capacity`."""

    max_attempts: int = Field(default=2, ge=1, le=MAX_ATTEMPTS)
    """Adapter attempts per pipeline run (`AGENT_MAX_ATTEMPTS`), 1 to 3, enforced by the loop
    in `pipeline.py`. The default 2 is the design's "at most one repair round"; the eval harness
    (`--max-attempts`) sets 1 to measure no repair and 3 to measure a second repair round. Every
    attempt after the first needs `ADAPTER_P95_S` plus `RENDER_P95_S` left of the soft deadline."""

    root_thinking_budget: int = Field(default=1_024, ge=0, le=MAX_THINKING_BUDGET)
    """Claude thinking of the root (`AGENT_ROOT_THINKING_BUDGET`): 0 turns it off. Above 0 the root
    thinks adaptively at its effort and its output cap grows by this many tokens, so the reply keeps
    the whole measured headroom (`models.make_content_config`). On by default since 2026-10-11: the
    root reads the user's questions, and the measurement of that day put the pass rate of 122 cases
    at 100 % and the `ok` rate at 51.6 % with thinking on root and adapter (91.0 % and 28.7 % with it
    off), for a median of $0.0063 instead of $0.0038 per plot and a p50 of 31.5 s instead of 13.6 s.
    Claude Haiku 5.5 takes no thinking budget of its own (`budget_tokens` is a 400), so this is the
    room thinking may use, not a limit the model sees. The root replays its thinking blocks after a
    tool result; an account that enforces the history-editing check of preserved thinking may refuse
    that call, which a measurement run shows as pipeline errors."""

    adapter_thinking_budget: int = Field(default=8_192, ge=0, le=MAX_THINKING_BUDGET)
    """The same for the adapter (`AGENT_ADAPTER_THINKING_BUDGET`), on by default since 2026-10-11:
    it is the lever behind the pass rate (without it the structured answer misses its edit anchors
    in a third of the runs). The adapter is single-turn, so nothing is replayed; its structured
    answer (`output_config.format`) lets it think first. Both budgets are ignored on Gemini, which
    thinks by a level per agent kind; a non-zero budget set explicitly there is refused, an
    explicit 0 (`--thinking-budget 0,0`) is accepted. 8,192 since 2026-10-14 (2,048 before): at
    effort `high`, 10 of 80 first adapter calls of the Vertex check thought through the whole
    10,240-token cap and ended with `MAX_TOKENS` and no plan, while finished calls used up to
    11,251 tokens with a 95th percentile of 9,063."""

    reviewer_thinking_budget: int = Field(default=4_096, ge=0, le=MAX_THINKING_BUDGET)
    """Claude only (`AGENT_REVIEWER_THINKING_BUDGET`): adaptive thinking for the reviewer with that many
    tokens added to its output cap, on since 2026-10-13 with `reviewer_effort` high; 0 turns it off.
    4,096 since 2026-10-14 (2,048 before): the cap of 12,288 is twice the 6,144 at which 3 of 118
    reviews of the Vertex check were cut off; finished reviews used at most 6,141 tokens."""

    root_effort: Effort = "medium"
    """Claude's `effort` for the root (`AGENT_ROOT_EFFORT`): `medium` since 2026-10-13 (`low` before). The
    root chats, prepares and generates data, and starts the plot pipeline; at `low` it merged two filters
    into one wrong drop condition in the hard prep cases, at `medium` and `high` it solved all 33. It runs on
    Vertex AI even on the claude-cli transport, which cannot carry its tool chat."""

    adapter_effort: Effort = "high"
    """Claude's `effort` for the adapter (`AGENT_ADAPTER_EFFORT`): `high` since 2026-10-13 (`medium` before).
    On the claude-cli transport it is also how much the CLI thinks."""

    reviewer_effort: Effort = "high"
    """Claude's `effort` for the reviewer (`AGENT_REVIEWER_EFFORT`): `high` since 2026-10-13 (`low` before),
    with `reviewer_thinking_budget`. A stricter reviewer alone scored lower on unseen specs; together with
    the adapter at high it was the best configuration on seeds and unseen specs, by both judges."""

    max_llm_calls: PositiveInt = 16
    """LLM calls per request (`AGENT_MAX_LLM_CALLS`), the `RunConfig` cap. 16 since 2026-10-13 (12 before):
    two rounds with a self-review and a check retry each take up to six adapter calls, two reviews and
    the root's two calls, so 16 leaves room and never stops a round."""

    request_token_budget: PositiveInt = 800_000
    """Cost-weighted tokens per request (`AGENT_REQUEST_TOKEN_BUDGET`), in input-token equivalents
    (`plugins/ledger.BUDGET_WEIGHTS`). 800,000 since 2026-10-13 (160,000 before) for the live flow: a
    self-review per round adds an adapter call with an image, the catalogue reviewer reads the rubric
    (about 20,000 tokens, cached after the first call), and adapter and reviewer think at effort high.
    On the claude-cli transport such runs booked a median of about 278,000 and at most about 458,000;
    the budget is a guard against runaway requests, never a reason to cut a round short (owner rule),
    and the Vertex AI spend cap stays the money limit. The numbers of the old flow: a reviewed
    run with two adapter attempts booked a median of
    about 39,500 with a warm prompt cache (72,200 plain tokens) and about 77,700 on a cold one,
    where each agent's first call writes its prefix; with a second review the costliest run comes
    to about 115,000, and with three attempts about 117,300, so the budget leaves about 36 % on top.
    A review starts only while `pipeline.REVIEW_RESERVE_TOKENS` is left for it and the root's
    closing reply."""

    daily_token_budget: PositiveInt = 10_000_000
    """Cost-weighted tokens per user and day (`AGENT_DAILY_TOKEN_BUDGET`), weighted like the request budget: about $1
    at Claude Haiku 5.5's $0.10 per million input-token equivalents (`agents/evals/pricing.py`). 10,000,000 since
    2026-11-01 (owner decision; 8,000,000 from 2026-10-13, 2,000,000 before). The old flow's numbers: about 54 median
    runs with a warm cache and about 26 for a user whose every request starts cold (77,700 each). An admin is exempt
    (owner decision of 2026-11-01): one fan-out over the 15 libraries booked 3,047,083 in the measurement of that day,
    so the global budget is an admin's only daily cap on model spend."""

    daily_pipeline_runs: PositiveInt = 50
    """Pipeline runs per user and day (`AGENT_DAILY_PIPELINE_RUNS`; 50 since 2026-11-01, 40 before); an admin is
    exempt."""

    global_daily_token_budget: PositiveInt = 100_000_000
    """Cost-weighted tokens per day across all users (`AGENT_GLOBAL_DAILY_TOKEN_BUDGET`), admins included: about $10,
    the runaway guard of the whole service, which binds every tier; reaching it pauses the service. 100,000,000 since
    2026-11-01 (owner decision; 24,000,000, three users at their daily budget, before): ten public users at their
    daily budget, or about thirty admin fan-outs. The Vertex AI spend cap stays the money limit."""

    render_timeout_s: PositiveInt = 60
    """Seconds per render, host-enforced (`AGENT_RENDER_TIMEOUT_S`)."""

    data_code: bool = True
    """Whether the root has `run_data_code` (`AGENT_DATA_CODE`): a data-generating snippet the user pasted or
    typed, translated to Python by the root, validated and run in the renderer's sandbox (owner decision of
    2026-10-14). On by default because the renderer and the agents deploy from main; the tool answers
    `unavailable` while a renderer without `POST /run-data` serves."""

    data_run_timeout_s: float = Field(default=20.0, gt=0, le=30)
    """Seconds one data snippet may run in the sandbox (`AGENT_DATA_RUN_TIMEOUT_S`), host-enforced; at most the
    renderer's 30 s (`wire.MAX_DATA_TIMEOUT_S`)."""

    daily_data_runs: PositiveInt = 30
    """`run_data_code` runs per user and day (`AGENT_DAILY_DATA_RUNS`), counted before each run; an admin is exempt."""

    narrowed_bindings: Literal["keep", "reset"] = "keep"
    """What the root's `set_bindings` does to the user's confirmation when the new bindings only leave out members
    of a confirmed number family such as `y2` (`AGENT_NARROWED_BINDINGS`, `session_state.narrows`; owner decision
    of 2026-10-15, "e.g. drops the 2nd line"): `keep` moves the confirmation to them, so a step-2 note such as
    "only co2_per_capita" plots in the same turn; `reset` asks for `.confirm()` again, as every other binding
    change does (leaving out `series` or any single role, or a renumbered member)."""

    request_deadline_s: PositiveInt = 540
    """Hard request deadline in seconds, enforced through `abort_signal` (`AGENT_REQUEST_DEADLINE_S`).

    540 since 2026-10-13 (180 before). With the self-review a round takes about 60 s, and at a soft
    deadline of 140 s the repair round was skipped in 11 of 20 measured runs; at 240 s the flow
    reached +3.0 on unseen specs. The owner's rule: a complicated plot must never ship unfinished
    because time ran out, so the deadlines leave room far above the measured maximum (155 s on the
    CLI). The run queue's 600 s wait plus 540 s stays below the BFF's 1,190 s turn cap and the
    services' 1,200 s Cloud Run timeout."""

    soft_deadline_s: PositiveInt = 480
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
    which the user gets the `locked_out` refusal for the rest of the (UTC) day, in every session and on
    the paste route (`429 locked_out`); before 2026-10-14 it was the misleading `budget` text."""

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
                f"(the runtime registry serves {', '.join(sorted(RUNTIME_LIBRARIES))})"
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
        cli = self.transport == "claude-cli"
        if cli and self.environment not in TRANSPORT_ENVIRONMENTS:
            raise ValueError(
                f"AGENT_TRANSPORT=claude-cli is allowed only when ENVIRONMENT is development or test, "
                f"not {self.environment!r}"
            )
        if cli and self.provider != "anthropic-vertex":
            raise ValueError(
                "AGENT_TRANSPORT=claude-cli carries Claude calls; it needs AGENT_PROVIDER=anthropic-vertex"
            )
        per_kind = (("AGENT_ADAPTER_MODEL", self.adapter_model), ("AGENT_REVIEWER_MODEL", self.reviewer_model))
        if not cli and any(value for _, value in per_kind):
            raise ValueError(
                "AGENT_ADAPTER_MODEL and AGENT_REVIEWER_MODEL are experiment settings for "
                "AGENT_TRANSPORT=claude-cli; on Vertex AI every kind runs AGENT_MODEL"
            )
        for name, value in per_kind:
            if value is not None and value not in CLI_MODELS:
                raise ValueError(
                    f"{name}={value!r} is not a model of the claude-cli transport ({', '.join(CLI_MODELS)})"
                )
        for name, value in (("AGENT_MODEL", self.model), ("AGENT_JUDGE_MODEL", self.judge_model)):
            if not value.startswith(prefix):
                raise ValueError(
                    f"{name}={value!r} does not match AGENT_PROVIDER={self.provider}: "
                    f"that provider serves model ids starting with {prefix!r}"
                )
            if self.provider == "anthropic-vertex" and value not in CLAUDE_MODELS:
                raise ValueError(
                    f"{name}={value!r} is not a supported Claude model ({', '.join(CLAUDE_MODELS)}): "
                    "the reviewer runs with thinking disabled, which newer Claude models refuse with a 400"
                )
        explicit_thinking = {
            "root_thinking_budget",
            "adapter_thinking_budget",
            "reviewer_thinking_budget",
        } & self.model_fields_set
        if self.provider != "anthropic-vertex" and any(getattr(self, name) for name in explicit_thinking):
            raise ValueError(
                "AGENT_ROOT_THINKING_BUDGET, AGENT_ADAPTER_THINKING_BUDGET and AGENT_REVIEWER_THINKING_BUDGET "
                "apply to Claude only; Gemini thinks by a level per agent kind"
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
