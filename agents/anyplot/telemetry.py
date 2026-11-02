"""Content-free usage telemetry: four canonical events, one wide JSON line each.

The admin-only chat ("Use with my data") writes one line per event to stdout on its own
logger (`TELEMETRY_LOGGER`, shipped by `enable_attribution_log` in `agents/main.py`), and a
Cloud Logging sink routes the lines with `jsonPayload.log_type="agent_telemetry"` into the
`agent-telemetry` log bucket, which BigQuery reads through a linked dataset
(`docs/reference/agent-telemetry.md`). The per-hook attribution lines (`plugins/ledger.py`)
stay on their logger for debugging; the sink never takes them, because they carry the HMAC
user id.

Owner rule of 2026-10-16: no line ever holds a user input, question, reply, data value,
column name, file or sheet name, or cell, only enums, coarse buckets, counts and ids from
closed sets. Every event is a pydantic model with `extra="forbid"` whose fields are
`Literal` sets, bounded integers, booleans or ids that match a fixed pattern (`SpecId`,
`ModelId`, `DefectId`, `GateId`), so text from the user cannot reach a line even by
mistake: a value outside its set fails validation and the line is dropped with a warning
that names the event and the field only. Content reaches anyone only through the explicit
feedback-case submission (`api/agent_cases.py`).

| Event | When | One line per |
|---|---|---|
| `data_input` | a paste or a dropped file reached the dataset route (or the conversion refused the file) | input |
| `chat_turn` | a `/messages` turn ended | turn |
| `pipeline_run` | a `plot_pipeline` run ended | run (`run_index` 1 is the session's first plot) |
| `outcome` | the page's beacon: copied code or image, downloaded a file, saved the session, sent feedback | action and version |

Envelope (every line): `log_type`, `schema`, `event`, `service` and `revision` (Cloud
Run's `K_SERVICE` and `K_REVISION`), `source` (`live`; `fanout` for every line of a session
the admin's "plot in all libraries" fan-out opened, `RequestLedger.fanout`; or `harness` for the
eval harnesses, `harness()`), `session` (a salted hash), `spec_id`, `library`, `turn` (the
session's user turns so far, from the request ledger), and `idempotency_key`, a hash of
session, turn, attempt and event: the BigQuery base view keeps one row per key, so a
line Cloud Logging delivers twice or a pipeline node ADK re-runs counts once.

The session hash is an HMAC-SHA256 of the session id under a random per-process salt
(`plugins/ledger.SESSION_SALT`): the id travels in every `/v1` request URL that Cloud Run
logs, and a plain hash of it could be recomputed from those. Sessions live in memory and
die with the instance (`max-instances=1`), so a salt that dies with the process keeps one
session's lines together and still unlinkable to the request log. The attribution lines'
`session` uses the same salt under another domain (`ledger.salted`), so telemetry rows
and debug lines cannot be joined by it either.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
from collections import OrderedDict
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Annotated, Any, Literal, cast, get_args

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, ValidationError

from core.constants import MAX_AGENT_VERSION, SUPPORTED_LIBRARIES

from .data.warning_codes import BindingWarningCode, WarningCode, binding_warning_codes, warning_codes
from .language import canonical
from .plugins.ledger import RequestLedger, StepUsage, salted


if TYPE_CHECKING:
    from google.adk.events.event import Event

    from .data.parse import ParsedDataset
    from .render.contract import ThemeOutput
    from .schemas import DatasetProfile


TELEMETRY_LOGGER = "anyplot.agents.telemetry"
"""The logger of the telemetry lines; `agents/main.py` `enable_attribution_log` ships it to stdout next to the
attribution logger, each with a handler of its own."""
logger = logging.getLogger(TELEMETRY_LOGGER)
warn = logging.getLogger(__name__)

LOG_TYPE: Literal["agent_telemetry"] = "agent_telemetry"
SCHEMA: Literal[1] = 1
"""The line format's version: a field renamed or removed is a new schema; a field added is not."""

Source = Literal["live", "fanout", "harness"]
SOURCE: ContextVar[Source] = ContextVar("anyplot_telemetry_source", default="live")
"""The source of the lines written in this context. A context variable, not a module global: the eval harnesses
run the app in process (`evals/matrix.py`, `evals/prep.py`), and only the requests they send, which run in the
harness's own context, may be tagged `harness`; a live request served by the same process keeps `live`, or
`fanout` when its session was opened by the admin's fan-out (`emit`)."""


@contextmanager
def harness() -> Iterator[None]:
    """Tag every line written inside the block, in this context and the tasks it starts, `harness`; the previous
    source is back on every exit, an exception included."""
    token = SOURCE.set("harness")
    try:
        yield
    finally:
        SOURCE.reset(token)


def session_key(session_id: str) -> str:
    """The salted hash of a session id: 16 hex characters, stable for this process only."""
    return salted(session_id, "telemetry", 16)


def idempotency_key(session: str, turn: int, attempt: str, event: str) -> str:
    return hashlib.sha256(f"{session}|{turn}|{attempt}|{event}".encode()).hexdigest()[:24]


# --- Closed sets --------------------------------------------------------------------------


def _library(value: str) -> str:
    if value not in SUPPORTED_LIBRARIES:
        raise ValueError("not a supported library")
    return value


Library = Annotated[str, AfterValidator(_library)]
"""One of `core.constants.SUPPORTED_LIBRARIES`."""
SpecId = Annotated[str, Field(pattern=r"^[a-z0-9-]{1,100}$")]
ModelId = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,79}$")]
"""A model id as the price table keys it (`claude-haiku-5-5`, `gemini-3.8-flash`): `model_id` drops version
suffixes before a line is written."""
DefectId = Annotated[str, Field(pattern=r"^[A-Z]{2}-[0-9]{2}$")]
GateId = Annotated[str, Field(pattern=r"^(?:R[0-9](?:-[a-z_]{1,24})?|G[0-9]{1,2})$")]

InputFormat = Literal[
    "csv",
    "tsv",
    "semicolon",
    "pipe",
    "whitespace",
    "json",
    "json_lines",
    "json_stat",
    "api_json",
    "xlsx",
    "xlsm",
    "xlsb",
    "xls",
    "ods",
    "parquet",
    "feather",
    "arrow",
    "npy",
    "npz",
    "transcribed",
    "formula",
    "code",
    "other",
]
Entry = Literal["paste", "file"]
DataOutcome = Literal[
    "ok",
    "transcribed",
    "unparseable",
    "too_large",
    "code",
    "formula",
    "data_refused",
    "guard_unavailable",
    "capacity",
    "rate_limited",
    "daily_limit",
    "locked_out",
    "file_refused",
    "file_failed",
    "convert_unavailable",
    "other",
]
DataCause = Literal[
    # the parser's refusals (`parse.ParseErrorCode`)
    "too_long",
    "unparseable",
    "no_table",
    "too_many_columns",
    "too_many_rows",
    "cell_too_long",
    "control_chars",
    # the paste route's own
    "free_text_one_column",
    # the transcriber's
    "prefilter",
    "cut_off",
    "timeout",
    "transcribed_unparseable",
    "transcribed_no_table",
    # the file conversion's (`wire.ConvertRefusal` and `main.CONVERT_FAILURES`)
    "unsupported",
    "encrypted",
    "pickle",
    "hdf5",
    "corrupt",
    "archive_limits",
    "too_large",
    "empty",
    "sheet_not_found",
    "array_shape",
    "object_array",
    "formulas_only",
    "too_complex",
    "unreadable",
    "other",
]
SizeBucket = Literal["lt1k", "1k_10k", "10k_100k", "100k_1m", "ge1m"]
RowsBucket = Literal["1_10", "11_100", "101_1k", "1k_10k", "gt10k"]
ColsBucket = Literal["1", "2", "3_5", "6_10", "11_20", "gt20"]
CategoriesBucket = Literal["le5", "6_12", "13_50", "gt50"]
MissingBucket = Literal["none", "lt5", "5_30", "gt30"]
SpecFit = Literal["direct", "needs_reshape", "missing_role", "incompatible"]

TurnKind = Literal["plot", "prep", "formula", "code", "talk", "refused", "error"]
TurnAction = Literal["text", "create_plot", "summarize_data"]
ToolName = Literal[
    "get_dataset_profile",
    "get_spec_brief",
    "get_current_code",
    "set_bindings",
    "set_language",
    "keep_plot_request",
    "prepare_data",
    "query_data",
    "generate_data",
    "run_data_code",
    "plot_pipeline",
]
TOOL_NAMES: frozenset[str] = frozenset(get_args(ToolName))
PrepOp = Literal[
    "rename",
    "drop_columns",
    "drop_rows",
    "set_type",
    "aggregate",
    "sort",
    "pivot_longer",
    "pivot_wider",
    "classify",
    "derive",
    "make_date",
    "row_number",
]
PREP_OPS: frozenset[str] = frozenset(get_args(PrepOp))
ConversionOutcome = Literal["none", "date", "number", "index", "asked"]
"""What a turn did about a required role left open (`data/conversions.py`): `none` when the session block listed no
conversion; `date`, `number` or `index` for the column `prepare_data` made; `asked` when a conversion was listed and
none was made, so the root asked or skipped it (`asked_question` tells the two apart)."""
RefusalCode = Literal[
    "out_of_scope",
    "needs_data",
    "other_library",
    "unsupported_content",
    "locked_out",
    "session_closed",
    "budget",
    "rate_limited",
    "daily_limit",
    "other",
]
ErrorCode = Literal["guard_unavailable", "capacity", "run_limit", "deadline", "internal", "cancelled", "other"]
"""`cancelled`: the client closed the stream before the turn ended (the page's cancel, a reload, a lost connection);
`run_limit`: the turn's sandbox run would have been one more than `AGENT_USER_MAX_RUNS` across the user's sessions."""
LanguageSource = Literal["default", "pasted", "detected", "chosen"]
Step = Literal["root", "adapter", "reviewer", "judge", "other"]

PlotStatus = Literal["ok", "needs_attention", "failed", "not_ready"]
FailureReason = Literal["validation", "render", "deadline", "budget", "error"]
NotReadyReason = Literal["no_dataset", "incomplete_bindings", "data_unconfirmed"]
"""`schemas.NotReadyReason`: why a `not_ready` run did not start (pinned equal by a test)."""
ScoreBucket = Literal["lt50", "50_69", "70_79", "80_89", "90_plus"]
SandboxFailure = Literal["syntax", "name", "key", "value", "type", "timeout", "memory", "other"]
PipelineStage = Literal[
    "budget",
    "deadline",
    "error",
    "adapter_schema",
    "adapter_truncated",
    "adapter_full_code",
    "edit_apply",
    "validator",
    "loader",
    "render",
    "gates",
    "not_rereviewed",
    "reviewer_unreadable",
    "reviewer_defects",
    "reviewer_ok",
    "self_review",
    "other",
]
"""`pipeline.Stage` (pinned equal by a test), `other` for a stage added there first: `stage` and `stages` go through
`closed` and `closed_list`, so a new stage never drops the line."""
RoundScore = ScoreBucket | Literal["unscored"]
"""A round's review score bucket in `round_scores`; `unscored` for a round no review scored (a failed render, a
checklist review, a review the deadline skipped), so the list's position stays the round's number."""
PlotLanguage = Literal["en", "de", "fr", "es", "it", "pt", "nl", "pl", "zh", "vi", "ru", "ja", "other"]
"""The session language as a code of `language.ENGLISH_NAMES` (the chip's ten, Polish and Japanese; pinned equal by a
test), `other` for every other language: the session language is free text the pattern bounds (`Swedish`), and a rare
language would single a user out, so the value itself never reaches a line (`plot_language`)."""
Readiness = Literal["clean", "coupled"]
"""The readiness of the catalogue file the session adapts (`code.readiness.ReadinessStatus`): `blocked` never opens."""
LoaderNote = Literal["inexact", "submillisecond", "offset"]
"""The kinds of cells a runtime's loader changes when it reads `data.csv` (`data.kinds.ColumnKinds`, pinned equal by a
test): integers past ±2^53 read as the nearest double (R), timestamps cut to the millisecond (Julia), timestamps with a
UTC offset read in UTC (R, Julia). Never the note's sentence, which names columns and counts."""
EditFailure = Literal[
    "zero_match",
    "stale_match",
    "multi_match",
    "protected:theme",
    "protected:theme_token",
    "protected:placeholder",
    "protected:savefig",
    "drift:theme",
    "drift:theme_token",
    "drift:savefig",
    "drift:rebind",
    "working_unparseable",
    "other",
]
"""`code.edits.FAILURE_KINDS` (pinned equal by a test), `other` for a kind added there first."""
ValidatorRule = Literal[
    "banned-attribute",
    "banned-call",
    "banned-import",
    "banned-keyword",
    "banned-name",
    "banned-statement",
    "data-frame",
    "dataset-package",
    "dunder",
    "encoding",
    "literal-budget",
    "literal-data",
    "markup-code",
    "module-value",
    "os-use",
    "palette-prefix",
    "placeholder-count",
    "placeholder-use",
    "rc-key",
    "relative-import",
    "rng",
    "savefig-target",
    "size",
    "star-import",
    "string-length",
    "syntax",
    "unavailable-import",
    "url-literal",
    "other",
]
"""The rule ids of the validators of every language (`code/validate.py`, `code/profiles/*/validate.py`) and the
pipeline's `literal-budget`; a test collects the ids from the validators' sources, and a rule added there first is
`other` until it is added here."""
ReviewerMode = Literal["catalogue", "checklist"]
"""`settings.ReviewerMode` (pinned equal by a test)."""
PromptHash = Annotated[str, Field(pattern=r"^[0-9a-f]{16}$")]
"""The first 16 hex characters of the SHA-256 of a static instruction (`policy.prompt_hash`)."""

OutcomeAction = Literal[
    "copied_code",
    "copied_image",
    "downloaded_png",
    "downloaded_code",
    "downloaded_page",
    "opened_preview",
    "downloaded_data",
    "saved_session",
    "feedback",
]
"""What the user did with a result; `downloaded_page` is a JavaScript plot's interactive `plot.html` (JS-4b), and
`opened_preview` that page shown in the card (JS-4b-2), a look and no keep. The BFF (`api/routers/agent.py`) and the
page (`app/src/lib/agent.ts`) carry the same set."""
OUTCOME_ACTIONS: tuple[str, ...] = get_args(OutcomeAction)
Reaction = Literal["thumbs_up", "thumbs_down", "bug", "idea"]
"""The feedback reactions (`core/database/models.py` `FEEDBACK_REACTIONS`; pinned by a test)."""

Count = Annotated[int, Field(ge=0, le=10_000_000)]
Ms = Annotated[int, Field(ge=0, le=86_400_000)]
Version = Annotated[int, Field(ge=0, le=MAX_AGENT_VERSION)]
"""A plot version number as the routes take it (`core.constants.MAX_AGENT_VERSION`); 0 is the session itself."""


def _list() -> Any:
    """A list field of at most 64 items, empty by default (each field gets its own `FieldInfo`)."""
    return Field(default_factory=list, max_length=64)


class _Event(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class StepTokens(_Event):
    """What one kind of agent spent in a turn or a run: calls and tokens by kind, and its model."""

    step: Step
    model: ModelId | None = None
    calls: Count = 0
    input: Count = 0
    output: Count = 0
    """Candidates plus thoughts: every output token, as the price table bills them."""
    cached: Count = 0
    cache_write: Count = 0
    thoughts: Count | None = None
    """The thinking tokens among `output`, a part of it, never added to it; None where no split is known (the judges,
    which book a plain total)."""


class DataInput(_Event):
    event: Literal["data_input"] = "data_input"
    format: InputFormat
    entry: Entry
    outcome: DataOutcome
    cause: DataCause | None = None
    size_bucket: SizeBucket
    rows_bucket: RowsBucket | None = None
    cols_bucket: ColsBucket | None = None
    numeric_cols: Count = 0
    integer_cols: Count = 0
    datetime_cols: Count = 0
    text_cols: Count = 0
    boolean_cols: Count = 0
    max_categories_bucket: CategoriesBucket | None = None
    missing_bucket: MissingBucket | None = None
    warnings: list[WarningCode] = _list()
    tables: Count = 0
    sheets: Count = 0
    notes: bool = False
    """Notes pasted around the table passed the screen and were kept (their text never is)."""
    file_name: bool = False
    """The input came with a file name (never the name)."""
    spec_fit: SpecFit | None = None
    judge_input: Count = 0
    judge_output: Count = 0
    judge_model: ModelId | None = None
    latency_ms: Ms = 0


class ChatTurn(_Event):
    event: Literal["chat_turn"] = "chat_turn"
    kind: TurnKind
    action: TurnAction
    asked_question: bool = False
    """The root's final reply ends with a question mark: computed on the server, the reply itself never logged."""
    tools: list[ToolName] = _list()
    prep_ops: list[PrepOp] = _list()
    prep_calls: Count = 0
    conversion: ConversionOutcome = "none"
    undo: bool = False
    to_long: bool = False
    manual_binding_changed: bool = False
    binding_warnings: list[BindingWarningCode] = _list()
    refusal: RefusalCode | None = None
    error: ErrorCode | None = None
    reply_reasked: bool = False
    language_source: LanguageSource | None = None
    """How the session language was set, as the turn left it (detection or `set_language` may set it in the turn)."""
    plot_language: PlotLanguage | None = None
    """The session language as the turn left it, as a closed code (`plot_language`)."""
    llm_calls: Count = 0
    steps: list[StepTokens] = _list()
    latency_ms: Ms = 0


class PipelineRun(_Event):
    event: Literal["pipeline_run"] = "pipeline_run"
    run_index: Annotated[int, Field(ge=1, le=10_000)]
    base: Literal["catalogue", "previous"]
    status: PlotStatus
    reason: FailureReason | NotReadyReason | None = None
    stage: PipelineStage | None = None
    attempts: Count = 0
    rounds: Count = 0
    reviews: Count = 0
    score_round1: ScoreBucket | None = None
    score_round2: ScoreBucket | None = None
    shipped_attempt: Count | None = None
    shipped_round: Count | None = None
    version: Version | None = None
    """The session's number of the version this run shipped (`PlotResult.version`, the number the page sends back as
    `outcome.version`), so an outcome joins the run that made its plot; None when the run shipped nothing, or a
    version past `MAX_AGENT_VERSION`, which no outcome can name (`version_number`)."""
    shipped_score: ScoreBucket | None = None
    """The bucket of the shipped render's own review score; None when it shipped unscored (a checklist review, no
    review left) or shipped nothing."""
    forced_repair: list[DefectId] = _list()
    """Review ids that forced a repair whatever the score (`pipeline.VISIBLE_DEFECT_IDS`)."""
    gates_failed: list[GateId] = _list()
    reviewer_defects: list[DefectId] = _list()
    residual_defects: list[DefectId] = _list()
    sandbox_failures: list[SandboxFailure] = _list()
    drift_restored: bool = False
    """A plan's drift of the protected theme statements was restored after the round's check retry
    (`edits.restore_protected`)."""
    stages: list[PipelineStage] = _list()
    """The stage that ended each attempt, in order (`pipeline.Run.stages`): retries, proofreads and repairs with their
    causes; `stage` is what stopped the run, also a limit before the next attempt."""
    round_scores: list[RoundScore] = _list()
    """The bucket of each round's latest review score, in round order, `unscored` for a round without one;
    `score_round1` and `score_round2` repeat the first two for the views."""
    plot_language: PlotLanguage | None = None
    """The run's plot language (`pipeline.Run.language`), as a closed code (`plot_language`)."""
    readiness: Readiness | None = None
    """The readiness of the catalogue file the session adapts, as the session opened it."""
    loader_notes: list[LoaderNote] = _list()
    """The kinds of cells the runtime's loader changed reading this run's data (`pipeline.loader_codes`)."""
    edit_failures: list[EditFailure] = _list()
    """The distinct kinds of the edit failures that ended an attempt (a plan restored after drift is
    `drift_restored`, not here)."""
    validator_rules: list[ValidatorRule] = _list()
    """The distinct rule ids that rejected a plan's code in any check of the run (SECURITY, the blocking ADAPTATION
    rules, `literal-budget`)."""
    adaptation_rules: list[ValidatorRule] = _list()
    """The distinct soft ADAPTATION rule ids of any check of the run: defect lines, the code still rendered."""
    reviewer_mode: ReviewerMode | None = None
    ship_best: bool | None = None
    """`AGENT_SHIP_BEST` as set; it takes effect with `reviewer_mode` `catalogue` only (`pipeline.ship_best`)."""
    self_review: bool | None = None
    repair_self_review: bool | None = None
    adapter_prompt: PromptHash | None = None
    """The hash of the run's adapter instruction (`policy.adapter_instruction` of the library)."""
    reviewer_prompt: PromptHash | None = None
    """The hash of the run's reviewer instruction, in its mode (`sub_agents.reviewer.REVIEWER_MODES`)."""
    adapt_ms: Ms = 0
    check_ms: Ms = 0
    render_ms: Ms = 0
    review_ms: Ms = 0
    total_ms: Ms = 0
    steps: list[StepTokens] = _list()


class Outcome(_Event):
    event: Literal["outcome"] = "outcome"
    action: OutcomeAction
    version: Version = 0
    reaction: Reaction | None = None


AnyEvent = DataInput | ChatTurn | PipelineRun | Outcome
EVENTS: tuple[str, ...] = ("data_input", "chat_turn", "pipeline_run", "outcome")


class _Envelope(_Event):
    severity: Literal["INFO"] = "INFO"
    log_type: Literal["agent_telemetry"] = LOG_TYPE
    schema_: Literal[1] = Field(default=SCHEMA, alias="schema")
    service: Annotated[str, Field(pattern=r"^[a-z0-9-]{1,63}$")]
    revision: Annotated[str, Field(pattern=r"^[a-z0-9-]{1,100}$")]
    source: Source
    session: Annotated[str, Field(pattern=r"^[0-9a-f]{0,16}$")]
    spec_id: SpecId | None = None
    library: Library | None = None
    turn: Annotated[int, Field(ge=0, le=100_000)] = 0
    idempotency_key: Annotated[str, Field(pattern=r"^[0-9a-f]{24}$")]

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


def _service() -> tuple[str, str]:
    service = os.environ.get("K_SERVICE") or "anyplot-agents"
    revision = os.environ.get("K_REVISION") or "local"
    clean = re.compile(r"[^a-z0-9-]")
    return clean.sub("-", service.lower())[:63] or "anyplot-agents", clean.sub("-", revision.lower())[:100] or "local"


def emit(event: AnyEvent, ledger: RequestLedger, *, attempt: str = "0") -> dict[str, Any] | None:
    """Write one telemetry line for `event` with the ledger's envelope; the record, or None when it failed validation.

    Never raises: telemetry must not break a turn. `attempt` separates two lines of the same
    event in one turn (a second paste, the version of an outcome) in the idempotency key.
    A live line of a session the admin's fan-out opened (`ledger.fanout`) is `fanout`, so every
    `source = 'live'` filter leaves the fan-out's test sessions out; the harness's stays `harness`.
    """
    try:
        service, revision = _service()
        session = session_key(ledger.session_id)
        source = SOURCE.get()
        envelope = _Envelope(
            service=service,
            revision=revision,
            source="fanout" if source == "live" and ledger.fanout else source,
            session=session,
            spec_id=ledger.spec_id or None,
            library=ledger.library or None,
            turn=ledger.turn,
            idempotency_key=idempotency_key(session, ledger.turn, attempt, event.event),
        )
        record = {**envelope.model_dump(mode="json", by_alias=True), **event.model_dump(mode="json")}
    except ValidationError as exc:
        fields = sorted({str(error["loc"][0]) for error in exc.errors() if error.get("loc")})
        warn.warning("telemetry line dropped: %s fails %s", event.event, ", ".join(fields))
        return None
    logger.info(json.dumps(record, sort_keys=True))
    return record


def build(model: type[AnyEvent], **fields: Any) -> AnyEvent | None:
    """`model(**fields)`, or None (with a warning that names the fields only) when a value is outside its set."""
    try:
        return model(**fields)
    except ValidationError as exc:
        names = sorted({str(error["loc"][0]) for error in exc.errors() if error.get("loc")})
        warn.warning("telemetry event invalid: %s fails %s", model.__name__, ", ".join(names))
        return None


def write(model: type[AnyEvent], ledger: RequestLedger, *, attempt: str = "0", **fields: Any) -> dict[str, Any] | None:
    """`build` then `emit`; never raises."""
    try:
        event = build(model, **fields)
        return emit(event, ledger, attempt=attempt) if event is not None else None
    except Exception as exc:  # telemetry never breaks a request
        warn.warning("telemetry failed: %s", type(exc).__name__)
        return None


# --- Buckets ------------------------------------------------------------------------------


def size_bucket(size: int) -> SizeBucket:
    if size < 1024:
        return "lt1k"
    if size < 10 * 1024:
        return "1k_10k"
    if size < 100 * 1024:
        return "10k_100k"
    if size < 1024 * 1024:
        return "100k_1m"
    return "ge1m"


def rows_bucket(rows: int) -> RowsBucket:
    if rows <= 10:
        return "1_10"
    if rows <= 100:
        return "11_100"
    if rows <= 1000:
        return "101_1k"
    if rows <= 10_000:
        return "1k_10k"
    return "gt10k"


def cols_bucket(columns: int) -> ColsBucket:
    if columns <= 1:
        return "1"
    if columns == 2:
        return "2"
    if columns <= 5:
        return "3_5"
    if columns <= 10:
        return "6_10"
    if columns <= 20:
        return "11_20"
    return "gt20"


def categories_bucket(categories: int) -> CategoriesBucket:
    if categories <= 5:
        return "le5"
    if categories <= 12:
        return "6_12"
    if categories <= 50:
        return "13_50"
    return "gt50"


def missing_bucket(missing: int, cells: int) -> MissingBucket:
    if missing <= 0 or cells <= 0:
        return "none"
    share = missing / cells
    if share < 0.05:
        return "lt5"
    if share <= 0.30:
        return "5_30"
    return "gt30"


def score_bucket(score: int | None) -> ScoreBucket | None:
    if score is None:
        return None
    if score < 50:
        return "lt50"
    if score < 70:
        return "50_69"
    if score < 80:
        return "70_79"
    if score < 90:
        return "80_89"
    return "90_plus"


def ms(seconds: float) -> int:
    return max(0, min(86_400_000, round(seconds * 1000)))


# --- Facts from the code's own objects ---------------------------------------------------


JSON_FORMATS: dict[str, InputFormat] = {
    "json_records": "json",
    "json_columns": "json",
    "json_pairs": "json",
    "json_lines": "json_lines",
    "json_stat": "json_stat",
}
API_JSON_WARNINGS = frozenset({"fields_beside_records_to_notes", "list_fields_beside_left_out"})
"""Warnings the parser writes only when it found the records inside an API answer (`parse._api_records`)."""


def input_format(
    source_format: str | None, *, convert_kind: str | None = None, warnings: Iterable[str] = ()
) -> InputFormat:
    """The closed input format of a parsed table: the dropped file's kind, else the parser's `source_format`."""
    if convert_kind is not None:
        return cast(InputFormat, closed(convert_kind, get_args(InputFormat)))
    if source_format is None:
        return "other"
    if source_format in JSON_FORMATS:
        if source_format == "json_records" and API_JSON_WARNINGS & set(warnings):
            return "api_json"
        return JSON_FORMATS[source_format]
    return cast(InputFormat, closed(source_format, get_args(InputFormat)))


def profile_fields(profile: DatasetProfile) -> dict[str, Any]:
    """The buckets and counts of a parsed table's profile: no name, no value."""
    dtypes = [column.dtype for column in profile.columns]
    text_unique = [column.unique for column in profile.columns if column.dtype == "text"]
    missing = sum(column.missing for column in profile.columns)
    return {
        "rows_bucket": rows_bucket(profile.rows),
        "cols_bucket": cols_bucket(len(profile.columns)),
        "numeric_cols": dtypes.count("number"),
        "integer_cols": dtypes.count("integer"),
        "datetime_cols": dtypes.count("datetime"),
        "text_cols": dtypes.count("text"),
        "boolean_cols": dtypes.count("boolean"),
        "max_categories_bucket": categories_bucket(max(text_unique)) if text_unique else None,
        "missing_bucket": missing_bucket(missing, profile.rows * len(profile.columns)),
    }


def parsed_fields(parsed: ParsedDataset) -> dict[str, Any]:
    """`profile_fields` plus the warning codes, the table count and whether notes were kept."""
    codes = warning_codes(parsed.warnings)
    return {
        **profile_fields(parsed.profile),
        "warnings": codes,
        "tables": len(parsed.tables) or 1,
        "notes": bool(parsed.context_lines),
    }


def spec_fit(*, complete: bool, bound: int, reshape: bool) -> SpecFit:
    """How the table fits the spec at the paste: a wide-table suggestion first (`data/shape.py`), then the bindings."""
    if reshape:
        return "needs_reshape"
    if complete:
        return "direct"
    return "missing_role" if bound else "incompatible"


_EXCEPTION_CLASSES: dict[str, SandboxFailure] = {
    "SyntaxError": "syntax",
    "IndentationError": "syntax",
    "TabError": "syntax",
    "NameError": "name",
    "UnboundLocalError": "name",
    "KeyError": "key",
    "ValueError": "value",
    "TypeError": "type",
    "MemoryError": "memory",
    "TimeoutError": "timeout",
}


def sandbox_failure(output: ThemeOutput) -> SandboxFailure | None:
    """The closed class of a render that failed in the sandbox, from the exit, the renderer's reason and the
    exception class of the traceback (`gates.error_summary`, never the message); None for a run that exited 0."""
    from .render.gates import error_summary

    if output.timed_out or output.reason == "timeout":
        return "timeout"
    if output.reason == "memory":
        return "memory"
    if output.exit_code == 0 and output.png is not None:
        return None
    name = error_summary(output.stderr_tail).split(" ", 1)[0]
    return _EXCEPTION_CLASSES.get(name, "other")


def step_of(agent: str) -> Step:
    if agent == "anyplot":
        return "root"
    if agent.startswith("adapter"):
        return "adapter"
    if agent == "reviewer":
        return "reviewer"
    return "other"


def step_tokens(
    usage: dict[str, StepUsage], *, steps: Iterable[Step], judge_model: str | None = None
) -> list[dict[str, Any]]:
    """The ledger's per-agent usage folded by step and model, for the steps asked for, in a fixed step order.

    One entry per (step, model), so two models in one step (an experiment's adapter model beside the default)
    are each priced at their own rate by the cost view. The judges book no model of their own (`book_judge`):
    their entry carries `judge_model`, the settings' judge model, so the cost view can price it. They book no
    split of their output either, so their `thoughts` is None; every other step's is its thinking tokens.
    """
    wanted = list(steps)
    folded: dict[tuple[Step, str | None], dict[str, Any]] = {}
    for agent, spent in usage.items():
        step: Step = "judge" if agent == "judge" else step_of(agent)
        if step not in wanted:
            continue
        model = model_id(spent.model or (judge_model if step == "judge" else None))
        item = folded.setdefault(
            (step, model),
            {
                "step": step,
                "model": model,
                "calls": 0,
                "input": 0,
                "output": 0,
                "cached": 0,
                "cache_write": 0,
                "thoughts": None if step == "judge" else 0,
            },
        )
        item["calls"] += spent.calls
        item["input"] += spent.input
        item["output"] += spent.output
        item["cached"] += spent.cached
        item["cache_write"] += spent.cache_write
        if item["thoughts"] is not None:
            item["thoughts"] += spent.thoughts
    return [folded[key] for key in sorted(folded, key=lambda key: (wanted.index(key[0]), key[1] or ""))]


_MODEL_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")
_MODEL_SUFFIX = re.compile(r"(?:@.*|-[0-9]{8})$")


def model_id(value: str | None) -> str | None:
    """A model id as the price table keys it, else None: lower case, without a `models/` prefix and without a
    version suffix (`claude-haiku-5-5@20261001` and `claude-haiku-5-5-20261001` are `claude-haiku-5-5`). A
    provider's odd version string becomes None and never fails the whole line."""
    if not value:
        return None
    text = _MODEL_SUFFIX.sub("", value.strip().lower().removeprefix("models/"))
    return text if _MODEL_ID.fullmatch(text) else None


def ends_with_question(text: str) -> bool:
    """The reply's last visible character is a question mark (Latin, full-width or Arabic), past closing quotes,
    brackets and Markdown emphasis."""
    stripped = text.rstrip().rstrip(")\"'»”’*_`").rstrip()
    return stripped.endswith(("?", "？", "؟"))


def user_turns(events: Iterable[Event]) -> int:
    """The session's user turns so far: events by the user with text, not the routes' state-only events."""
    count = 0
    for event in events:
        if event.author != "user" or not event.content or not event.content.parts:
            continue
        if any(part.text for part in event.content.parts):
            count += 1
    return count


def turn_kind(ledger: RequestLedger) -> TurnKind:
    """What a turn did, in order of weight: a refusal, an error, a plot, data from code or a formula, a prep, talk."""
    if ledger.refusal is not None:
        return "refused"
    if ledger.error is not None:
        return "error"
    if "plot_pipeline" in ledger.tools:
        return "plot"
    if "run_data_code" in ledger.tools:
        return "code"
    if "generate_data" in ledger.tools:
        return "formula"
    if "prepare_data" in ledger.tools:
        return "prep"
    return "talk"


def closed(value: str | None, allowed: Iterable[str], fallback: str = "other") -> str | None:
    """`value` when it is in `allowed`, `fallback` for any other value, None for None."""
    if value is None:
        return None
    return value if value in set(allowed) else fallback


def closed_set(values: Iterable[str], allowed: Iterable[str]) -> list[str]:
    """The distinct `values`, each `closed` (`other` outside `allowed`), sorted."""
    known = set(allowed)
    return sorted({value if value in known else "other" for value in values})


def closed_list(values: Iterable[str], allowed: Iterable[str]) -> list[str]:
    """Every one of `values` in its order, each `closed` (`other` outside `allowed`): a sequence such as `stages`."""
    known = set(allowed)
    return [value if value in known else "other" for value in values]


def plot_language(language: str | None) -> PlotLanguage | None:
    """The session language as a closed code: a code of `PlotLanguage` (`Deutsch` and `German` are `de`), `other` for
    any other language (`Swedish`, `sv`, `Klingon`), None without a session."""
    if language is None:
        return None
    return cast(PlotLanguage, closed(canonical(language), get_args(PlotLanguage)))


def version_number(number: int | None) -> int | None:
    """A shipped version's number for `pipeline_run.version`: None past `MAX_AGENT_VERSION` (and for none), so a
    session that somehow shipped more versions than any route or outcome can name still writes its run lines."""
    return number if number is not None and 1 <= number <= MAX_AGENT_VERSION else None


def readiness(status: str | None) -> Readiness | None:
    """A readiness status as the closed set, None for any other value (`blocked` never opens a session)."""
    return cast(Readiness, status) if status in get_args(Readiness) else None


# --- Per-session marks between turns ------------------------------------------------------

MAX_MARKED_SESSIONS = 4096


@dataclass
class SessionMarks:
    """What happened in a session between two telemetry lines, in memory only (the session dies with the instance).

    The data routes set the flags a `chat_turn` reports (`undo`, `to_long`, `manual_binding_changed`,
    `binding_warnings`) and the next turn takes them; the conversion route keeps the dropped file's kind
    for the paste that follows; the pipeline numbers its runs per session, once per invocation (`run_index`).
    """

    inputs: int = 0
    convert_kind: str | None = None
    convert_sheets: int = 0
    undo: bool = False
    to_long: bool = False
    manual_binding_changed: bool = False
    binding_warnings: set[str] = field(default_factory=set)
    conversion: ConversionOutcome = "none"
    runs: dict[str, int] = field(default_factory=dict)


_MARKS: OrderedDict[str, SessionMarks] = OrderedDict()


def marks(session_id: str) -> SessionMarks:
    found = _MARKS.get(session_id)
    if found is None:
        found = _MARKS[session_id] = SessionMarks()
        while len(_MARKS) > MAX_MARKED_SESSIONS:
            _MARKS.popitem(last=False)
    else:
        _MARKS.move_to_end(session_id)
    return found


def forget(session_id: str) -> None:
    _MARKS.pop(session_id, None)


def take_turn_marks(session_id: str) -> dict[str, Any]:
    """The flags the data routes set since the last turn, cleared as they are read."""
    mark = marks(session_id)
    taken = {
        "undo": mark.undo,
        "to_long": mark.to_long,
        "manual_binding_changed": mark.manual_binding_changed,
        "binding_warnings": sorted(mark.binding_warnings),
        "conversion": mark.conversion,
    }
    mark.undo = mark.to_long = mark.manual_binding_changed = False
    mark.binding_warnings = set()
    mark.conversion = "none"
    return taken


def note_binding_warnings(session_id: str, sentences: list[str]) -> None:
    if sentences:
        marks(session_id).binding_warnings.update(binding_warning_codes(sentences))


def note_conversion(session_id: str, outcome: ConversionOutcome) -> None:
    """What this turn did about an open role; a column made stands, `asked` only fills a turn that made none."""
    mark = marks(session_id)
    if outcome != "asked" or mark.conversion == "none":
        mark.conversion = outcome


def run_index(session_id: str, invocation_id: str | None) -> int:
    """The session's run number for this invocation: 1 for its first plot run; the same number when ADK re-runs
    the node in the same invocation, so the line keeps its idempotency key."""
    mark = marks(session_id)
    key = invocation_id or f"run-{len(mark.runs) + 1}"
    if key not in mark.runs:
        mark.runs[key] = len(mark.runs) + 1
    return mark.runs[key]


def next_input(session_id: str) -> int:
    mark = marks(session_id)
    mark.inputs += 1
    return mark.inputs


REFUSAL_OUTCOMES: dict[str, DataOutcome] = {
    "too_long": "too_large",
    "unparseable": "unparseable",
    "code": "code",
    "formula": "formula",
    "data_refused": "data_refused",
    "guard_unavailable": "guard_unavailable",
    "capacity": "capacity",
    "rate_limited": "rate_limited",
    "daily_limit": "daily_limit",
    "locked_out": "locked_out",
    "convert_unavailable": "convert_unavailable",
}
"""The dataset routes' refusal codes as a `data_input` outcome; any other code is `unparseable`'s sibling `other`."""


@dataclass
class InputFacts:
    """The content-free facts of one dataset input, collected along the route and written once (`write`).

    `format` is fixed up front for a dropped binary file (its kind) and a confirmed transcription, set by the
    parse for every other paste (`parsed`), and by the refusal for code and formulas (`refused`).
    """

    session_id: str
    entry: Entry
    size: int
    format: str | None = None
    sheets: int = 0
    fields: dict[str, Any] = field(default_factory=dict)
    outcome: str | None = None
    cause: str | None = None

    @classmethod
    def for_paste(cls, session_id: str, *, size: int, source: bool, confirmed: bool) -> InputFacts:
        """A paste's facts; a paste that names a file after a conversion takes the converted file's kind.

        The kind is only read here: the route clears it (`clear_converted`) once the paste passed its limits, so a
        paste refused at the rate limit and sent again still knows the file it came from."""
        mark = marks(session_id)
        kind, sheets = mark.convert_kind, mark.convert_sheets
        fmt: str | None = None
        if source and kind is not None:
            fmt = kind
        elif confirmed:
            fmt = "transcribed"
        return cls(session_id, "file" if source else "paste", size, fmt, sheets if fmt == kind else 0)

    def parsed(self, parsed: ParsedDataset) -> None:
        self.fields.update(parsed_fields(parsed))
        if self.format is None:
            self.format = input_format(parsed.profile.source_format, warnings=self.fields["warnings"])

    def transcribed(self, parsed: ParsedDataset) -> None:
        self.fields.update(parsed_fields(parsed))
        self.outcome = "transcribed"

    def stored(self, parsed: ParsedDataset, *, complete: bool, bound: int, reshape: bool, file_name: bool) -> None:
        self.parsed(parsed)
        self.fields.update(spec_fit=spec_fit(complete=complete, bound=bound, reshape=reshape), file_name=file_name)
        self.outcome = "ok"

    def refused(self, code: str) -> None:
        if code in ("code", "formula"):
            self.format = code
        if self.outcome is None:
            self.outcome = REFUSAL_OUTCOMES.get(code, "other")

    def write(self, ledger: RequestLedger, clock: Clock, judge_model: str | None = None) -> dict[str, Any] | None:
        """The `data_input` line; an input that neither stored nor refused (an exception) writes `other`."""
        judge = ledger.steps.get("judge")
        index = next_input(self.session_id)
        return write(
            DataInput,
            ledger,
            attempt=f"in{index}",
            format=closed(self.format, get_args(InputFormat)) or "other",
            entry=self.entry,
            outcome=self.outcome or "other",
            cause=closed(self.cause, get_args(DataCause)),
            size_bucket=size_bucket(self.size),
            sheets=self.sheets,
            judge_input=judge.input if judge else 0,
            judge_output=judge.output if judge else 0,
            judge_model=model_id(judge_model) if judge else None,
            latency_ms=clock.ms(),
            **self.fields,
        )


def file_refusal(
    session_id: str, ledger: RequestLedger, *, size: int, kind: str | None, code: str, clock: Clock
) -> dict[str, Any] | None:
    """The `data_input` line of a dropped file the conversion refused or failed on (`/dataset/convert`)."""
    if code.startswith("file_"):
        cause: str | None = code.removeprefix("file_")
        outcome = (
            "file_refused"
            if cause in get_args(DataCause) and cause not in ("timeout", "too_complex", "unreadable")
            else "file_failed"
        )
    else:
        cause, outcome = None, REFUSAL_OUTCOMES.get(code, "other")
    facts = InputFacts(session_id, "file", size, kind or "other", outcome=outcome, cause=cause)
    return facts.write(ledger, clock)


def clear_converted(session_id: str) -> None:
    """The paste that followed a conversion reached the parser: the file's kind is spent."""
    mark = marks(session_id)
    mark.convert_kind, mark.convert_sheets = None, 0


def converted(session_id: str, *, kind: str, sheets: int) -> None:
    """A conversion succeeded: the paste that follows it with the file's name is that kind of file."""
    mark = marks(session_id)
    mark.convert_kind, mark.convert_sheets = kind, sheets


class Clock:
    """A monotonic stopwatch for `latency_ms`."""

    def __init__(self) -> None:
        self.started = time.monotonic()

    def ms(self) -> int:
        return ms(time.monotonic() - self.started)
