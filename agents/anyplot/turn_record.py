"""The record of each chat turn that a feedback case carries: the root's tool calls and the guards' verdicts.

Persona round 1 (2026-11-06) had to infer several root causes, because a case held no tool call and no guard line:
whether a refusal came from the output guard or from the root, and whether the root bound a column. So every
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
  (`OutcomeCode`). A call that had not answered when the turn ended reads `unfinished`.
* `guards`: the verdicts of the turn's hooks (`ledger.TURN_HOOKS`) in the order they were logged
  (`RequestLedger.guards`, filled by `attribution`): (hook, verdict) and nothing else of the line.
* `prep_ops`: the operations of the turn's `prepare_data` calls that changed the data, in order.
* `tools_dropped`, `guards_dropped`, `prep_ops_dropped`: what each list's bound left out (`MAX_RECORD_TOOLS` and
  `MAX_RECORD_PREP_OPS` keep the first entries, `MAX_RECORD_GUARDS` the latest).

Closed codes only, never an argument, a result, a word of the user, an id, a hash or a time. The guarantee is
structural: each value is closed to its set before the model sees it (`other` outside it), and the models forbid any
other field. The scope judge's `attack` is recorded as `out_of_scope`, as the `refusal` event and the transcript's
placeholder fold it. The record is no join key: a turn's sequence of hooks and verdicts is a fingerprint of the
session's attribution lines, which carry the user and the session hash, so the triage never matches a case's record
against a log or telemetry line, by sequence or by time.
"""

from collections import deque
from typing import Annotated, Any, Literal, get_args

from pydantic import BaseModel, ConfigDict, Field

from .data.generate import GenerateErrorCode
from .data.prepare import PrepareErrorCode
from .dataset_versions import VersionRefusal
from .plugins.ledger import CallOutcome, GuardVerdict, RequestLedger, SafetyCode, ToolCall, TurnHook, guard_verdict
from .schemas import FailureReason, NotReadyReason
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
"""The turns a session's ring keeps, the latest ones; older ones leave it and count as `dropped`. A persona session
runs 10 to 30 turns, and a turn's record is about 0.5 KB of JSON (3 KB at its bounds), so the ring stays far below
the bundle's 32 MiB cap (`api.routers.agent.MAX_BUNDLE_BYTES`)."""
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


class RecordedCall(_Record):
    """One root tool call: its name (`other` for a name the model made up), the guards' verdict, what it did, and the
    code of its answer (None for an answer without one, and for a call a guard refused)."""

    tool: ToolName | Literal["other"]
    verdict: GuardVerdict
    outcome: CallOutcome
    code: OutcomeCode | None = None


class GuardLine(_Record):
    """One turn hook's verdict, without any other field of its line."""

    guard: TurnHook
    verdict: HookVerdict


class TurnRecord(_Record):
    """One turn of the session, closed codes only (module docstring)."""

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
    """A ledger's `ToolCall` as the record keeps it, its name, verdict and code closed again."""
    return RecordedCall.model_validate(
        {
            "tool": call.tool if call.tool in TOOL_NAMES else "other",
            "verdict": guard_verdict(call.verdict),
            "outcome": call.outcome,
            "code": outcome_code(call.code),
        }
    )


def build(ledger: RequestLedger, action: str | None, failure: str | None = None) -> TurnRecord:
    """The record of the turn the ledger holds; `failure` is the route's own error of the turn, as `_telemetry_turn`
    gets it. A call still open when the turn ended stays `unfinished`."""
    codes = turn_codes(ledger, failure)
    calls = [recorded_call(call) for call in ledger.tool_calls]
    lines = [line for hook, verdict in ledger.guards if (line := guard_line(hook, verdict)) is not None]
    ops = [op for op in ledger.prep_ops if op in PREP_OPS]
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
