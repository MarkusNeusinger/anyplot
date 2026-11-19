"""The record of each chat turn that a feedback case carries: the root's tool calls and the guards' verdicts.

A case that holds no tool call and no guard line leaves root causes to inference: whether a refusal came from the
output guard or from the root, whether the root bound a column, which kind of condition a filter stored. So every
`/messages` turn leaves one `TurnRecord` in a bounded ring per session (`TurnRecords`, `Services.turns`), written next
to the turn's `chat_turn` line at each of its ends (`agents/main.py` `_keep_turn`): the normal end, the cancelled one,
and a turn refused before the scope judge. The session bundle carries the ring under `turns`, in every form
(`GET /v1/sessions/{sid}/bundle`). Per turn:

* `turn`, the session's user turn (`RequestLedger.turn`, the number `last_run.turn` uses): turn N is the N-th `user`
  line of the bundle's transcript, a withheld message's placeholder and an action's fixed line included. A turn the
  route refused before the scope judge (`session_closed`, `budget_halt`, `message_limit` among its `guards`) stores no
  line, so its number is that of the line the next turn writes; a turn cancelled before its run began has none either.
* `action`, `kind`, `refusal` and `error`, as the `chat_turn` line writes them (`telemetry.turn_codes`).
* `tools`: every root tool call of the turn in the order the guards saw them, refused ones included
  (`RequestLedger.tool_calls`): the tool's name, the guards' verdict, what it did, and the code of its answer
  (`OutcomeCode`). A call that had not answered when the turn ended reads `unfinished`. Its `shape` is the shape of
  its typed arguments (`CallShape`, built by `call_shape` before the guards answer): per data operation its name and
  the codes of its kind, and for a condition the test, the shape of its value and the kind of its column, never the
  value or the column; for a plot run or a kept request whether it carried a change request, and counts.
* `guards`: the verdicts of the turn's hooks (`ledger.TURN_HOOKS`) in the order they were logged
  (`RequestLedger.guards`, filled by `attribution`): (hook, verdict) and nothing else of the line.
* `prep_ops`: the operations of the turn's `prepare_data` calls that changed the data, in order.
* `tools_dropped`, `guards_dropped`, `prep_ops_dropped`: what each list's bound left out (`MAX_RECORD_TOOLS` and
  `MAX_RECORD_PREP_OPS` keep the first entries, `MAX_RECORD_GUARDS` the latest).

Closed codes, booleans and small counts only, besides the record's own bounded counters: the turn's number and the
three dropped counts. Of a call's arguments the record keeps only those that are closed codes already and the shape of
the rest, never a column name, a value of the data, a bound, an expression, a text, a result, a word of the user, an
id, a hash or a time. The guarantee is structural: each value is closed to its set before the model sees it (`other`
outside it), and the models forbid any other field. The scope judge's `attack` is recorded as `out_of_scope`, as the
`refusal` event and the transcript's placeholder fold it. The record is no join key: a turn's sequence of hooks and
verdicts is a fingerprint of the session's attribution lines, which carry the user and the session hash, so the triage
never matches a case's record against a log or telemetry line, by sequence or by time.
"""

import math
import re
from collections import deque
from collections.abc import Callable, Mapping, Sequence
from datetime import date, datetime
from typing import Annotated, Any, Literal, get_args

from pydantic import BaseModel, ConfigDict, Field

from .data.generate import GenerateErrorCode
from .data.parse import YEAR_MONTH
from .data.prepare import (
    MAX_CONDITIONS,
    MAX_KEYS,
    MAX_OPERATIONS,
    Aggregate,
    Blank,
    Condition,
    DateFormat,
    DateNumber,
    DateUnit,
    Decimal,
    Derive,
    DeriveHow,
    DropColumns,
    DropRows,
    Extract,
    How,
    Keep,
    KeepRows,
    Operation,
    Period,
    PrepareArgs,
    PrepareErrorCode,
    QueryOperation,
    Rolling,
    RollingHow,
    SetType,
    Sort,
    TargetType,
    Test,
    Unsupported,
    UnsupportedFamily,
)
from .data.query import QueryArgs
from .dataset_versions import VersionRefusal
from .language import LanguageTarget
from .plot_view import ViewRefused, route
from .plugins.ledger import CallOutcome, GuardVerdict, RequestLedger, SafetyCode, ToolCall, TurnHook, guard_verdict
from .schemas import (
    CURRENT_VERSION,
    MAX_EXPECTED_TEXTS,
    MAX_REMEMBER,
    ORIGINAL_VERSION,
    ColumnDtype,
    FailureReason,
    FromVersion,
    KeepRequestArgs,
    MemoryKind,
    NotReadyReason,
    PipelineArgs,
    SwitchArgs,
    Theme,
)
from .telemetry import (
    PREP_OPS,
    TOOL_NAMES,
    Count,
    ErrorCode,
    PrepOp,
    RefusalCode,
    ToolName,
    TurnAction,
    TurnKind,
    closed,
    turn_codes,
)


MAX_KEPT_TURNS = 50
"""The turns a session's ring keeps, the latest ones; older ones leave it and count as `dropped`. A long session runs
10 to 30 turns, and a turn's record is about 0.6 KB of JSON for a plot turn and 2.4 KB for a turn of four calls (a
question, a data change, a plot) with their shapes. At its bounds (`MAX_RECORD_TOOLS` calls, each with a `CallShape` at
its schema maximum, and every other list full) it is about 104 KB, so even a ring of such turns (about 4.9 MiB) stays
below a sixth of the bundle's 32 MiB cap (`api.routers.agent.MAX_BUNDLE_BYTES`), as a test measures."""
MAX_RECORD_TOOLS = 32
"""The tool calls a turn's record keeps, the first ones; the rest count as `tools_dropped`. A turn makes at most
`AGENT_MAX_LLM_CALLS` (16) model calls, and the caps bound the data and plot tools to ten calls per turn."""
MAX_RECORD_GUARDS = 24
"""The guard verdicts a turn's record keeps, the latest ones; the earlier ones count as `guards_dropped`. A turn logs
about 15 at most: the judge, a language detection, the queue's, the reply checks, the output guard's two. The latest
are kept because the verdicts that explain how a turn ended come last (the reply checks, the output guard, a halt)."""
MAX_RECORD_PREP_OPS = 16
"""The `prepare_data` operations a turn's record keeps, the first ones; the rest count as `prep_ops_dropped`. A turn
makes at most two calls of five operations (`tool_safety.TURN_CAPS`, `prepare.MAX_OPERATIONS`)."""
MAX_TURN = 100_000
"""The highest turn number a record holds, as the telemetry envelope's `turn`."""

SessionToolCode = Literal[
    "session_not_open",
    "run_active",
    "unavailable",
    "invalid_arguments",
    "invalid_bindings",
    "invalid_language",
    "invalid_operations",
    "unsupported_operation",
    "unknown_version",
    "same_library",
    "plot_type_switch_unavailable",
    "library_unavailable",
    "guard_unavailable",
    "data_refused",
    "daily_limit",
    "busy",
    "capacity",
    "run_limit",
    "invalid_code",
    "run_failed",
    "code_error",
    "timeout",
    "unparseable",
    "no_numbers",
    "internal",
    "memory_full",
    "unknown_entry",
]
"""The error codes the root's tools answer with themselves (`agents/anyplot/tools/session.py`), pinned by a test that
reads every code written there; the data operations' own codes come from their modules."""
OutcomeCode = (
    SafetyCode
    | SessionToolCode
    | PrepareErrorCode
    | GenerateErrorCode
    | VersionRefusal
    | FailureReason
    | NotReadyReason
    | Literal["other"]
)
"""The code of a root tool's answer (`ToolCall.code`): an error's `code`, the `reason` of a run or a call that stopped
`not_ready` or of a run that `failed`, or ToolSafety's refusal of the result; `other` for any code outside the set."""


def literal_values(kind: Any) -> frozenset[str]:
    """Every string of a `Literal` type, or of a union of them, nested ones included."""
    values: set[str] = set()
    for arg in get_args(kind):
        if isinstance(arg, str):
            values.add(arg)
        else:
            values |= literal_values(arg)
    return frozenset(values)


OUTCOME_CODES = literal_values(OutcomeCode)

SCOPE_VERDICTS = frozenset(
    {
        # The judge's own verdicts (`models.Verdict`), `attack` folded into `out_of_scope` (`guard_line`).
        "in_scope",
        "out_of_scope",
        "needs_data",
        "other_library",
        # Refusals before the judge's call, and its outage.
        "unsupported_content",
        "locked_out",
        "service_paused",
        "budget",
        "guard_unavailable",
        # A paste note's rescue, the session's closing and its warning.
        "paste_note_rescues_spent",
        "paste_note_in_scope",
        "session_closed",
        "close_warning",
        # A served library named in any spelling, and the language offer; the two detection verdicts stay so a
        # record written before the offer replaced the detection still reads as itself.
        "served_library_in_scope",
        "language_offer",
        "language_offer_failed",
        "language_detected",
        "language_write_failed",
    }
)
HOOK_VERDICTS: dict[str, frozenset[str]] = {
    "scope_guard": SCOPE_VERDICTS,
    "output_guard": frozenset({"reply_too_long", "shortened", "reply_cut"}),
    "empty_reply": frozenset({"reasked", "empty_kept", "no_reply"}),
    "root_refusal": frozenset({"reasked", "kept"}),
    "number_provenance": frozenset({"clean", "unsourced_logged", "reasked", "withheld", "kept", "error"}),
    "reply_language": frozenset({"mismatch", "reasked", "reask_failed", "error", "not_offered"}),
    "shipped_reply": frozenset({"dropped", "kept"}),
    "plot_button": frozenset({"dropped", "kept", "asked"}),
    "budget_exempt": frozenset({"exempt"}),
    "budget_halt": frozenset(get_args(RefusalCode)),
    "queue": frozenset({"started", "expired", "withdrawn", "run_limit", "full"}),
    "session_closed": frozenset({"session_closed"}),
    "message_limit": frozenset({"rate_limited", "daily_limit"}),
}
"""Each turn hook's verdicts (`ledger.TURN_HOOKS`), pinned by a test against every verdict the hooks' lines write; a
verdict outside its hook's set reads `other`. `budget_exempt` writes none (`exempt`), and the Budget plugin's
`budget_halt` the refusal it set (`RequestLedger.note_guard`)."""
HookVerdict = Literal[
    "in_scope",
    "out_of_scope",
    "needs_data",
    "other_library",
    "unsupported_content",
    "locked_out",
    "service_paused",
    "budget",
    "guard_unavailable",
    "paste_note_rescues_spent",
    "paste_note_in_scope",
    "session_closed",
    "close_warning",
    "served_library_in_scope",
    "language_offer",
    "language_offer_failed",
    "language_detected",
    "language_write_failed",
    "not_offered",
    "reply_too_long",
    "shortened",
    "reply_cut",
    "reasked",
    "empty_kept",
    "no_reply",
    "clean",
    "unsourced_logged",
    "withheld",
    "mismatch",
    "reask_failed",
    "error",
    "dropped",
    "kept",
    "asked",
    "exempt",
    "rate_limited",
    "daily_limit",
    "started",
    "expired",
    "withdrawn",
    "run_limit",
    "full",
    "other",
]
"""Every verdict a record's guard line may hold: the union of `HOOK_VERDICTS`, and `other`."""
OUTSIDE_HOOKS = frozenset(
    {
        # A tool call's lines: the record's call entries carry their verdict and outcome.
        "tool",
        "tool_error",
        "budget_pipeline",
        "data_code",
        "data_judge",
        # The guard on a taken role (`data/emptied.py`): the call it refused carries its code in the record.
        "emptied_role",
        # The run's and the model's lines: the session's last run (`last_run.rounds`) carries the run.
        "model",
        "run",
        "answer_schema",
        "pipeline_result",
        "pipeline_adapt",
        "pipeline_check",
        "pipeline_render",
        "pipeline_review",
        # The paste, conversion and copy routes, which run outside a turn.
        "paste_limit",
        "convert_limit",
        "data_convert",
        "data_transcribe",
        "data_language",
        "file_name_judge",
        "notes_judge",
        "dataset_copy",
    }
)
"""The attribution hooks a turn's record leaves out, each for its reason: with `TURN_HOOKS` every hook the service
logs, pinned by a test, so a new hook is placed in one of the two before it ships. `data_judge` stays out because
`run_data_code`'s own outcome carries its verdict (`data_refused`, `guard_unavailable`)."""


class _Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


ValueShape = Literal["number", "iso_date", "iso_datetime", "year_month", "year_quarter", "year", "text", "list", "none"]
"""The shape of a condition's value (`value_shape`), never the value: the form its text has, in this order of
precedence. `list` for an "any of" list (`Condition.values`), `none` for no value or an empty one (`is_missing`,
`not_missing`); `year` for four digits, whatever they mean; `year_month` (`2024-03`) and `year_quarter` (`2024-Q1`)
for the labels a period `aggregate` writes; `iso_date` for `YYYY-MM-DD` and `iso_datetime` for one with a time, each a
real date; `number` for the engine's number shape; `text` for anything else, a value of only spaces included, which a
text test compares as it is."""
ColumnKind = ColumnDtype | Literal["unknown"]
"""The kind of a condition's column as the profile of the stored table the call starts from classes it
(`ColumnProfile.dtype`), or `unknown`: no stored table to read (a call from an earlier version, a session without
data), a column that table lacks, or a condition after an operation of the same call that may change a column's kind
or name (anything but `KIND_KEEPING_OPS`) or after the call read its table anew (`view_reread`). A kind the call's own
earlier steps would give is never guessed."""
FromKind = Literal["current", "original", "numbered"]
"""Which version a data call starts from (`FromVersion`): `numbered` for one named by its number, never the number."""
Direction = Literal["ascending", "descending"]
KeepMode = Literal["where", "first_n"]
"""How a `keep_rows` says its rows: by conditions (`where`), or as the first rows (`n`), never how many."""
KeepTarget = Literal["plot", "table"]
"""`KeepRows.target`, pinned equal by a test. Recorded only for a `prepare_data` whose `from_version` is `current`:
`query_data` ignores it, and a call that names the version it starts from rebuilds the table and sends every selection
to it."""
PlotBase = Literal["catalogue", "previous"]
"""`PipelineArgs.base`, pinned equal by a test."""
CombineChoice = Literal["sum", "mean"]
"""`PipelineArgs.combine`, pinned equal by a test."""
QueryOnlyOp = Literal["fit"]
"""The operations only `query_data` takes beside `Operation`'s (`prepare.QueryOperation`), by the models' own `op`,
pinned equal by a test. A `fit` is recorded by its name alone: its `x` and `y` are column names."""
RecordedOpName = PrepOp | QueryOnlyOp
"""Every operation name a call's shape records (`RecordedOp.op`); any other reads `other`."""
RECORDED_OPS = literal_values(RecordedOpName)
KIND_KEEPING_OPS = frozenset({"drop_rows", "keep_rows", "sort", "drop_columns", "reset_view"})
"""The operations after which every column of the stored table that is still there keeps its name and its kind: they
choose or order the rows of the call's own frame, drop columns, or clear the view of the plot. After any other
operation of a call, the record reads the kind of a later condition's column as `unknown`. `apply_view` is not one:
the rows it puts in the table's place are read anew, and a column's kind may change with them (whole numbers left in
a number column read as integers)."""
RANK_KEEPING_OPS = (DropRows, KeepRows)
"""The operations after which the rows keep the ranking of the `sort` before them, as the engine carries it
(`prepare._ROW_FILTERS`, pinned equal by a test): they only take rows out."""
CONDITION_OPS = (KeepRows, DropRows, Blank)
"""The operations whose conditions the record keeps. `classify` is not one: its rules name labels for a new column
rather than the rows a call works on, and its ten rules of three conditions would outgrow an operation's shape."""
SHAPED_TOOLS = frozenset(
    {"prepare_data", "query_data", "plot_pipeline", "keep_plot_request", "set_language", "switch_plot"}
)
"""The root tools whose arguments have a shape in the record (`call_shape`); any other call's `shape` is None.
`run_data_code` has none: its one closed argument, `source_language`, describes the user's own text rather than what
the call asks of the data, and the turn's `kind` already reads `example` when the call stored example data."""
_YEAR = re.compile(r"[0-9]{4}")
_YEAR_QUARTER = re.compile(r"[0-9]{4}-Q[1-4]")
_ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
_ISO_DATETIME = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}[T ].+")
_NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")
"""The engine's number shape (`prepare._number`, pinned by a test): a dot decimal with an optional exponent."""


class RecordedCondition(_Record):
    """One condition of a `keep_rows`, `drop_rows` or `blank`: its test, the shape of its value and the kind of its
    column."""

    test: Test | Literal["other"]
    value_shape: ValueShape
    column_kind: ColumnKind


class RecordedOp(_Record):
    """One data operation of a `prepare_data` or `query_data` call: its name and, by its kind, the codes its arguments
    already are or the shape they have. A field that does not apply to the operation is None.

    `keep_rows`: `mode`, `target` (in a `prepare_data` from `current` only, `KeepTarget`), with `first_n` the `order`
    of the top N (the direction of the call's last `sort` before it, with only row filters between them, as the engine
    keeps that ranking), and with `where` its `conditions`. `drop_rows` and `blank`: their `conditions`. `sort`:
    `order`. `aggregate`: `how`, `period` and `keys`, the count of its `by` columns (0 for a question's aggregate
    over every row, `QueryAggregate`). `set_type`: `type`,
    `date_format`, `decimal`. `derive` and `rolling`: `how`. `date_number`: `unit`. `extract`: `keep`. `unsupported`:
    `family`. Any other operation, `classify` among them (`CONDITION_OPS`): its name alone."""

    op: RecordedOpName | Literal["other"]
    mode: KeepMode | None = None
    target: KeepTarget | None = None
    order: Direction | None = None
    conditions: list[RecordedCondition] | None = Field(default=None, max_length=MAX_CONDITIONS)
    how: How | DeriveHow | RollingHow | None = None
    period: Period | None = None
    keys: Annotated[int, Field(ge=0, le=MAX_KEYS)] | None = None
    type: TargetType | None = None
    date_format: DateFormat | None = None
    decimal: Decimal | None = None
    unit: DateUnit | None = None
    keep: Keep | None = None
    family: UnsupportedFamily | None = None


class CallShape(_Record):
    """The shape of one root tool call's typed arguments, closed codes, booleans and small counts only. A field that
    does not apply to the tool is None.

    `prepare_data`, `query_data`: `operations` in order and `from_version`; `query_data` also `limit`, whether the call
    named a row limit. A `query_data` whose first operation is `apply_view` asked of the rows the plot draws.
    `plot_pipeline`: `base`, `theme`, `combine`, `change_request`, whether one was given, the count of
    `expected_texts`, and the kind of each `remember` item in order. `keep_plot_request`: `change_request`,
    `expected_texts` and `remember` as for `plot_pipeline`. `set_language`: `applies_to`. `switch_plot`: `plot`. Every
    list holds at most what the tool's own arguments may hold, so no bound drops an entry."""

    operations: list[RecordedOp] | None = Field(default=None, max_length=MAX_OPERATIONS)
    from_version: FromKind | None = None
    limit: bool | None = None
    base: PlotBase | None = None
    theme: Theme | None = None
    combine: CombineChoice | None = None
    change_request: bool | None = None
    expected_texts: Annotated[int, Field(ge=0, le=MAX_EXPECTED_TEXTS)] | None = None
    remember: list[MemoryKind] | None = Field(default=None, max_length=MAX_REMEMBER)
    applies_to: LanguageTarget | None = None
    plot: bool | None = None


class RecordedCall(_Record):
    """One root tool call: its name (`other` for a name the model made up), the guards' verdict, what it did, the
    code of its answer (None for an answer without one, and for a call a guard refused), and the shape of its
    arguments (None for a tool without one, and for arguments that did not validate)."""

    tool: ToolName | Literal["other"]
    verdict: GuardVerdict
    outcome: CallOutcome
    code: OutcomeCode | None = None
    shape: CallShape | None = None


class GuardLine(_Record):
    """One turn hook's verdict, without any other field of its line."""

    guard: TurnHook
    verdict: HookVerdict


class TurnRecord(_Record):
    """One turn of the session: closed codes, booleans and bounded counts only (module docstring)."""

    turn: Annotated[int, Field(ge=0, le=MAX_TURN)]
    action: TurnAction | Literal["other"]
    kind: TurnKind
    refusal: RefusalCode | None = None
    error: ErrorCode | None = None
    tools: list[RecordedCall] = Field(default_factory=list, max_length=MAX_RECORD_TOOLS)
    tools_dropped: Count = 0
    guards: list[GuardLine] = Field(default_factory=list, max_length=MAX_RECORD_GUARDS)
    guards_dropped: Count = 0
    prep_ops: list[PrepOp] = Field(default_factory=list, max_length=MAX_RECORD_PREP_OPS)
    prep_ops_dropped: Count = 0


def outcome_code(value: object) -> str | None:
    """`value` as an `OutcomeCode`: itself when it is one, `other` for any other text, None for no text."""
    if not isinstance(value, str) or not value:
        return None
    return value if value in OUTCOME_CODES else "other"


def result_code(result: Any) -> str | None:
    """The closed code of a root tool's answer (`OutcomeCode`): an error's `code`; the `reason` of an answer that
    stopped `not_ready` or of a run that `failed`; None for any other answer. Only an error's `code` is read as a code:
    `get_current_code`'s `ok` answer holds the program text under that key."""
    if not isinstance(result, dict):
        return None
    status = result.get("status")
    if status == "error":
        return outcome_code(result.get("code"))
    if status in ("not_ready", "failed"):
        return outcome_code(result.get("reason"))
    return None


def guard_line(hook: str, verdict: str | None) -> GuardLine | None:
    """A turn hook's verdict as the record keeps it, or None for a hook outside `TURN_HOOKS`; `attack` reads
    `out_of_scope`, a verdict outside its hook's set `other`."""
    allowed = HOOK_VERDICTS.get(hook)
    if allowed is None:
        return None
    if hook == "scope_guard" and verdict == "attack":
        verdict = "out_of_scope"
    return GuardLine.model_validate({"guard": hook, "verdict": verdict if verdict in allowed else "other"})


def recorded_call(call: ToolCall) -> RecordedCall:
    """A ledger's `ToolCall` as the record keeps it, its name, verdict and code closed again; its shape is a
    `CallShape` already, or None."""
    return RecordedCall.model_validate(
        {
            "tool": call.tool if call.tool in TOOL_NAMES else "other",
            "verdict": guard_verdict(call.verdict),
            "outcome": call.outcome,
            "code": outcome_code(call.code),
            "shape": call.shape if isinstance(call.shape, CallShape) else None,
        }
    )


ColumnKinds = Mapping[str, str] | None
"""The kind of each column of the stored table a call starts from, by name (`ColumnProfile.dtype`); None without one."""


def _no_kinds() -> ColumnKinds:
    return None


TESTS = literal_values(Test)
COLUMN_KINDS = literal_values(ColumnKind)


def value_shape(condition: Condition) -> ValueShape:
    """The shape of a condition's value (`ValueShape`): `none` only for a missing or empty value, and the number, date
    and period shapes read from the text stripped, as the engine strips it to read a number or a date; a four-digit
    year before a number, a real date before anything that only looks like one. A value of only spaces is `text`: a
    text test uses it as it is."""
    if condition.values is not None:
        return "list"
    if not condition.value:
        return "none"
    text = condition.value.strip()
    if _YEAR.fullmatch(text):
        return "year"
    if YEAR_MONTH.fullmatch(text):
        return "year_month"
    if _YEAR_QUARTER.fullmatch(text):
        return "year_quarter"
    if _ISO_DATE.fullmatch(text) and _reads(date.fromisoformat, text):
        return "iso_date"
    if _ISO_DATETIME.fullmatch(text) and _reads(datetime.fromisoformat, text):
        return "iso_datetime"
    if _NUMBER.fullmatch(text) and math.isfinite(float(text)):
        return "number"
    return "text"


def _reads(parse: Callable[[str], object], text: str) -> bool:
    try:
        parse(text)
    except ValueError:
        return False
    return True


def condition_shape(condition: Condition, kinds: ColumnKinds) -> RecordedCondition:
    """One condition as the record keeps it: its test, the shape of its value, the kind of its column (`unknown`
    without the table's kinds, or for a column the table lacks)."""
    kind = kinds.get(condition.column) if kinds is not None else None
    return RecordedCondition.model_validate(
        {
            "test": condition.test if condition.test in TESTS else "other",
            "value_shape": value_shape(condition),
            "column_kind": kind if kind in COLUMN_KINDS else "unknown",
        }
    )


def _direction(descending: bool) -> Direction:
    return "descending" if descending else "ascending"


def operation_shape(
    operation: Operation | QueryOperation, ranked: Direction | None, kinds: ColumnKinds, *, targeted: bool = True
) -> RecordedOp:
    """One data operation as the record keeps it (`RecordedOp`): `ranked` is the direction of the `sort` that still
    ranks the rows it gets, `kinds` the column kinds its conditions read (`operations_shape`), and `targeted` whether
    the call lands a `keep_rows` by its `target` (a `prepare_data` from `current`)."""
    fields: dict[str, Any] = {"op": operation.op if operation.op in RECORDED_OPS else "other"}
    if isinstance(operation, CONDITION_OPS) and operation.where is not None:
        fields["conditions"] = [condition_shape(condition, kinds) for condition in operation.where]
    if isinstance(operation, KeepRows):
        fields["mode"] = "where" if operation.where is not None else "first_n"
        if targeted:
            fields["target"] = operation.target
        if operation.where is None:
            fields["order"] = ranked
    elif isinstance(operation, Sort):
        fields["order"] = _direction(operation.descending)
    elif isinstance(operation, Aggregate):
        fields.update(how=operation.how, period=operation.period, keys=len(operation.by))
    elif isinstance(operation, SetType):
        fields.update(type=operation.type, date_format=operation.date_format, decimal=operation.decimal)
    elif isinstance(operation, Derive | Rolling):
        fields["how"] = operation.how
    elif isinstance(operation, DateNumber):
        fields["unit"] = operation.unit
    elif isinstance(operation, Extract):
        fields["keep"] = operation.keep
    elif isinstance(operation, Unsupported):
        fields["family"] = operation.family
    return RecordedOp.model_validate(fields)


def operations_shape(
    operations: Sequence[Operation | QueryOperation],
    kinds_of: Callable[[], ColumnKinds],
    reread_at: int | None = None,
    *,
    targeted: bool = True,
) -> list[RecordedOp]:
    """A call's operations as the record keeps them, in order. The stored table's column kinds (`kinds_of`, read only
    when an operation has conditions) hold for a condition while every operation before it keeps them
    (`KIND_KEEPING_OPS`; a `drop_columns` takes its columns out), and up to `reread_at`, where the table is read anew
    before the rest applies (`view_reread`); after either, a condition's column reads `unknown`. A `sort` ranks the
    rows until an operation other than a row filter follows it (`RANK_KEEPING_OPS`)."""
    wanted = any(isinstance(operation, CONDITION_OPS) and operation.where is not None for operation in operations)
    kinds = kinds_of() if wanted else None
    ranked: Direction | None = None
    shapes = []
    for index, operation in enumerate(operations):
        if index == reread_at:
            kinds = None
        shapes.append(operation_shape(operation, ranked, kinds, targeted=targeted))
        if isinstance(operation, Sort):
            ranked = _direction(operation.descending)
        elif not isinstance(operation, RANK_KEEPING_OPS):
            ranked = None
        if kinds is None:
            continue
        if isinstance(operation, DropColumns):
            kinds = {name: kind for name, kind in kinds.items() if name not in operation.columns}
        elif operation.op not in KIND_KEEPING_OPS:
            kinds = None
    return shapes


def view_reread(operations: Sequence[Operation]) -> int | None:
    """Where a `prepare_data` call reads its table anew: the first operation that lands in the view of the plot
    (`plot_view.route`) when operations of the table come before it, which store a version the view then applies to;
    None when nothing is read anew within the call (no view part, or no table part before it)."""
    try:
        routed = route(list(operations))
    except ViewRefused:  # the call is refused for its order; nothing applies
        return None
    view = len(routed.selections) + (2 if routed.top is not None else 0)
    return len(operations) - view if view and routed.table else None


def from_kind(version: FromVersion) -> FromKind:
    """Which version a data call starts from, without its number."""
    if version == CURRENT_VERSION:
        return "current"
    return "original" if version == ORIGINAL_VERSION else "numbered"


def call_shape(tool: str, args: BaseModel, kinds_of: Callable[[], ColumnKinds] = _no_kinds) -> CallShape | None:
    """The shape of a root call's validated arguments (`CallShape`), None for a tool outside `SHAPED_TOOLS`.

    `kinds_of` gives the column kinds of the session's current table (ToolSafety's `column_kinds`): a call from an
    earlier version reads none, so its conditions' columns are `unknown`. An operation's name and a condition's test
    read `other` outside their sets; every other value comes from the validated arguments, whose closed types the
    record's models share, and the models refuse anything else, so no value outside a set reaches the record."""
    if tool not in SHAPED_TOOLS:
        return None
    if isinstance(args, PrepareArgs | QueryArgs):
        current = args.from_version == CURRENT_VERSION
        reads = kinds_of if current else _no_kinds
        # Only `prepare_data` splits a call into the table's steps and the view's (`query_data` applies all at once),
        # and only one from `current` lands a `keep_rows` by its `target`: a call that names the version it starts
        # from rebuilds the table, so every selection lands in it (`tools.session.prepare_data`, `table_only`).
        prepare = isinstance(args, PrepareArgs)
        reread = view_reread(args.operations) if isinstance(args, PrepareArgs) else None
        fields: dict[str, Any] = {
            "operations": operations_shape(args.operations, reads, reread, targeted=prepare and current),
            "from_version": from_kind(args.from_version),
        }
        if isinstance(args, QueryArgs):
            fields["limit"] = "limit" in args.model_fields_set
        return CallShape.model_validate(fields)
    if isinstance(args, PipelineArgs | KeepRequestArgs):
        fields = {
            "change_request": bool(args.change_request.strip()),
            "expected_texts": len(args.expected_texts),
            "remember": [item.kind for item in args.remember],
        }
        if isinstance(args, PipelineArgs):
            fields.update(base=args.base, theme=args.theme, combine=args.combine)
        return CallShape.model_validate(fields)
    if isinstance(args, SwitchArgs):
        return CallShape(plot=args.plot)
    if tool == "set_language":
        # ToolSafety's own model, which this module cannot import; its `applies_to` is a `LanguageTarget`.
        return CallShape.model_validate({"applies_to": getattr(args, "applies_to", None)})
    return None


def build(ledger: RequestLedger, action: str | None, failure: str | None = None) -> TurnRecord:
    """The record of the turn the ledger holds; `failure` is the route's own error of the turn, as `_telemetry_turn`
    gets it. A call still open when the turn ended stays `unfinished`."""
    codes = turn_codes(ledger, failure)
    calls = [recorded_call(call) for call in ledger.tool_calls]
    lines = [line for hook, verdict in ledger.guards if (line := guard_line(hook, verdict)) is not None]
    ops = [op for op in [*ledger.prep_ops, *ledger.view_ops] if op in PREP_OPS]
    return TurnRecord.model_validate(
        {
            "turn": min(max(ledger.turn, 0), MAX_TURN),
            "action": closed(action or "text", get_args(TurnAction)),
            "kind": codes.kind,
            "refusal": codes.refusal,
            "error": codes.error,
            "tools": calls[:MAX_RECORD_TOOLS],
            "tools_dropped": max(len(calls) - MAX_RECORD_TOOLS, 0),
            "guards": lines[-MAX_RECORD_GUARDS:],
            "guards_dropped": max(len(lines) - MAX_RECORD_GUARDS, 0),
            "prep_ops": ops[:MAX_RECORD_PREP_OPS],
            "prep_ops_dropped": max(len(ops) - MAX_RECORD_PREP_OPS, 0),
        }
    )


class TurnRecords:
    """The turn records of each session, a ring of the latest `MAX_KEPT_TURNS`, with a count of the older ones that
    left it. The session bundle is the only reader; nothing here is logged, and a session's ring goes with the session
    (`Services.purge_session`). In memory like the sessions (`InMemorySessionService`), so a ring lives exactly as
    long as its session and writes no event into it."""

    def __init__(self, per_session: int = MAX_KEPT_TURNS) -> None:
        self.per_session = per_session
        self._rings: dict[str, deque[TurnRecord]] = {}
        self._dropped: dict[str, int] = {}

    def add(self, session_id: str, record: TurnRecord) -> None:
        ring = self._rings.setdefault(session_id, deque(maxlen=self.per_session))
        if len(ring) == ring.maxlen:
            self._dropped[session_id] = self._dropped.get(session_id, 0) + 1
        ring.append(record)

    def all(self, session_id: str) -> list[TurnRecord]:
        """The session's records in turn order. A record lands when its turn's stream ends, and a stream the run
        registry dropped as stale (`Runtime.drop_stale`) can end after a newer turn's; the sort is stable, so a turn
        refused before the judge stays before the turn that shares its number."""
        return sorted(self._rings.get(session_id, ()), key=lambda record: record.turn)

    def dropped(self, session_id: str) -> int:
        return self._dropped.get(session_id, 0)

    def bundle(self, session_id: str) -> dict[str, Any]:
        """The bundle's `turns`: `records` in turn order, and `dropped`, the older turns the ring no longer holds."""
        return {
            "records": [record.model_dump(mode="json") for record in self.all(session_id)],
            "dropped": self.dropped(session_id),
        }

    def delete_session(self, session_id: str) -> None:
        self._rings.pop(session_id, None)
        self._dropped.pop(session_id, None)
