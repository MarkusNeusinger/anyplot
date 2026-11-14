"""The `anyplot/1` stream translator: ADK events in, a fixed set of sanitised SSE events out.

ADK events are never forwarded. `Translator` maps them to the protocol the BFF
re-validates (`api/routers/agent.py`, `_EVENT_FIELDS`):

| Event | Fields | Comes from |
|---|---|---|
| `ready` | `v`, `run_id` | the start of the request; a turn starts at once, without the run queue |
| `status` | `step: "queued"`, `position`, `waiting` | the run queue, mid-turn, while the turn's first sandbox run (`plot_pipeline` or `run_data_code`) waits for the slot: at once, on every change, and every 15 s unchanged (`position` 1 runs next; `waiting` counts every queued entry, this one included); a turn without a sandbox run never sends it |
| `status` | `step: "started"` | the run queue, once, right after the last `queued` status, when the entry that waited holds its slot; the only end of the wait a turn without pipeline steps has before its reply. A turn that never waited, an expired or withdrawn wait, and a turn's second sandbox run send none |
| `status` | `step`, `attempt`, `max_attempts`, and on `repairing` `outcome`, `findings`, `defects` | the pipeline's content-free `custom_metadata` progress events; `max_attempts` is the run's round cap (`AGENT_MAX_ATTEMPTS`), so the page counts "try 2 of 3" from the server; the step that opens a repair round says how the round before it ended (`RoundOutcome`, a count) and the rubric ids it repairs (`VQ-05`, closed codes) |
| `message` | `text` | a final, non-partial text response authored by the root (`anyplot`) |
| `plot` | `status`, `reason`, `attempts`, `artifacts`, `changes`, `residual_defects`, `version`, `memory`, `rounds` | the pipeline's `PlotResult` output event; `version`, the stored version's number, only on `ok` and `needs_attention`; `memory`, only with `version`, the plot memory the version stands on as entry ids, `{kept, added}` (the entries from before the run it kept, the ones it added; two empty lists for a session without memory), from the ledger (`shipped_memory`), set once the memory is settled with the version; `rounds`, how each attempt ended (`{attempt, outcome, findings, step, shipped, defects, gates_failed, sandbox_failures}`: the step it ended in, whether its render is the one shipped, the rubric ids it passed on to the repair, and the closed ids of the gates its renders failed and of a crash, which the page does not show) |
| `refusal` | `code`, `text` | the request ledger's refusal, in place of the message: `out_of_scope`, `needs_data` (data that would have to be fetched), `other_library` (this plot in another library or language: a fixed pointer to the catalogue, not counted toward closing by default), `unsupported_content`, `locked_out` (past the day's `attack` strikes) and `session_closed` (the session's third counted refusal) from the scope guard, `budget` from the budgets (`service_paused` when only the service's day budget is spent, for every user); the refusal one before the closing one ends with the fixed `close_warning` sentence; right after `ready`, before the scope judge: `locked_out`, `budget` for a user over the daily budget, `service_paused` for everyone else once the service's day budget is spent, `rate_limited` or `daily_limit` past the user's message limits, `session_closed` in a closed session |
| `error` | `code`, `ref` | `guard_unavailable`, `capacity` (also when a sandbox run found the queue full or waited its maximum; the turn ends there, without a `plot`), `run_limit` (the user already has `AGENT_USER_MAX_RUNS` sandbox runs queued or running in other sessions; the turn ends the same way), `deadline`, `no_reply` (the root wrote no reply, also when asked once more: `plugins/empty_reply.py`) or `internal` |
| `done` | `llm_calls`, `tokens`, and after a run `bindings`, `data_confirmed`, `language` (`{language, source}`, the session language and how it was set), `suggestion` (the `.to_long()` offer in the session language, or null, when the session has data) and, when the turn changed the data (`prepare_data`, `generate_data`), `dataset`, and last `turn` (`TurnOutcome`: `answer`, `data`, `plot`, `switch`, `language`, `kept` or `memory`) after a turn that ended without an error, a refusal or the user's stop | the end of every run, always last; the route adds the session's sync fields (`_session_sync` in `agents/main.py`) and `turn` (`turn_outcome`, from the ledger's record of the root's tool calls) |

The route numbers every event on its way out (`id: <run_id>.<n>`, `agents/turn_log.py`) and keeps the
session's latest turn, which `GET /v1/sessions/{sid}/turn` reads to the end for a page that lost the stream.

Function calls and responses, tool outputs, thoughts, partial chunks, adapter and
reviewer answers, and `error_details` are dropped. A message goes through the
output sanitiser (`anyplot/output_guard.sanitize`: no URL, link target, HTML, image
or long code block, at most 1,200 characters); the plot event's `changes` and
`residual_defects` are model-written too, so each goes through the same sanitiser and
becomes one plain line. Personal data in them (names, addresses, e-mail addresses,
phone numbers) stays: the user may plot and discuss their own table.

The output guard's length cap (`output_guard.reply_too_long`) runs earlier, in the
ScopeGuard plugin before ADK stores the root's reply: a reply over the cap arrives
already shortened by the root or cut at the cap, never as a refusal. A final reply
without text sends no `message`; the EmptyReply plugin asks the root once more for one
and, when it stays empty, fails the turn with `no_reply`, which the route sends as the
`error` event. A reply the sanitiser empties fails the turn the same way here, unless
the turn sent a plot, asked for a library switch or stored a change
(`empty_reply.carries_answer`).
"""

import json
import re
from typing import Any, Literal, get_args

from google.adk.events.event import Event

from agents.anyplot.output_guard import plain_line, sanitize
from agents.anyplot.pipeline import STATUS_KEY
from agents.anyplot.plugins.empty_reply import NO_REPLY, carries_answer
from agents.anyplot.plugins.ledger import CallOutcome, RequestLedger
from agents.anyplot.schemas import MEMORY_ENTRY_ID_PATTERN, RoundOutcome
from agents.anyplot.telemetry import ends_with_question


PROTOCOL = "anyplot/1"
MAX_DONE_EVENT_CHARS = 512 * 1024
"""The BFF relays a `done` event of at most this many characters (`api/routers/agent.py`,
`_MAX_DONE_EVENT_CHARS`; 64 KiB for every other event). A `done` that carries `dataset` holds
20 preview rows and the profile of up to 50 columns with their names, top values, sample rows
and warnings, the notes pasted with the data (2,000 characters), the bindings twice, the change
lines, up to `MAX_DONE_ROLES` spec roles and
the session language, every string at its schema maximum and JSON-escaped at its worst about 393,000 characters;
the bound is proven by `tests/unit/agents/runtime/test_stream.py`, so a changed dataset
always reaches the page."""
NO_SUGGESTION: Any = object()
"""`Translator.done`'s default for `suggestion`: no data, so the event carries no `suggestion` key (a `null` one
says that the data has no offer)."""
MAX_DONE_ROLES = 50
"""The spec roles a `done` event's `dataset` lists at most. No catalogue spec comes near (a
binding set holds at most 50 columns), but a role list has no bound of its own: one bullet
can name many roles that share a description, and the cap keeps the bound above provable."""
ROOT_AUTHOR = "anyplot"
PIPELINE_AUTHOR = "plot_pipeline"
HALT_AUTHOR = "model"  # ADK's author of the event a before_run halt emits
STEPS = frozenset({"adapting", "checking", "rendering", "reviewing", "repairing"})
QUEUED_STEP = "queued"
"""The status step the route sends while the run waits in the run queue; no pipeline event carries it."""
STARTED_STEP = "started"
"""The status step the route sends once a run that waited leaves the run queue; no pipeline event carries it.
A turn without pipeline steps (a summary that runs data code) has nothing else that tells the page the wait is
over, so its queue position would stay on screen until the reply."""
PLOT_FIELDS = (
    "status",
    "reason",
    "attempts",
    "artifacts",
    "changes",
    "residual_defects",
    "version",
    "rounds",
    "new_data",
)
ROUND_OUTCOMES = frozenset(get_args(RoundOutcome))
RUBRIC_ID = re.compile(r"[A-Z]{2}-[0-9]{2}")
"""A rubric id a repairing status names (`schemas.RubricId`)."""
MODEL_WRITTEN_FIELDS = ("changes", "residual_defects")
MEMORY_ID = re.compile(MEMORY_ENTRY_ID_PATTERN)
TurnOutcome = Literal["answer", "data", "plot", "switch", "language", "kept", "memory"]
"""What a turn changed, the `done` event's `turn` (`turn_outcome`)."""
TURN_ORDER: tuple[TurnOutcome, ...] = ("data", "plot", "switch", "language", "kept", "memory")
"""The outcome of a turn that changed several things: the first of these it changed, the order the page reads its
own stream in (`turnOutcome` in `app/src/hooks/useAgentSession.ts`), so the server's word and the page's agree
wherever the stream shows the change. `kept` and `memory` come last: the page sees them in the memory it reads after
the turn, and they only tell a turn that changed nothing visible from a question."""
CALL_CHANGES: dict[tuple[str, CallOutcome], TurnOutcome] = {
    ("prepare_data", "changed"): "data",
    ("prepare_data", "viewed"): "kept",
    ("generate_data", "changed"): "data",
    ("run_data_code", "changed"): "data",
    ("set_bindings", "changed"): "data",
    ("plot_pipeline", "shipped"): "plot",
    ("plot_pipeline", "failed"): "plot",
    ("plot_pipeline", "not_ready"): "plot",
    ("plot_pipeline", "kept"): "kept",
    ("keep_plot_request", "kept"): "kept",
    ("switch_plot", "changed"): "switch",
    ("set_language", "changed"): "language",
    ("forget", "changed"): "memory",
}
"""What a root tool call changed, by its name and outcome (`ledger.ToolCall`); every other call changes nothing.

A bindings change is a change of the data card, where the bindings stand. A `set_language` call counts also when it
named the language already set: it stores the choice (source `chosen`), which detection never writes over. A
`plot_pipeline` call that stopped `not_ready` for missing data or open roles is a plot turn, as the page shows it (a
failed plot card); one refused for unconfirmed data (`unconfirmed`) shows no card and changes nothing, unless it kept
the wish (`kept`). A `prepare_data` call that changed the view of the plot alone (`viewed`) is `kept` too: the data
card stays as it is, and what changed shows with the next plot, in the same turn when the root runs it (`plot`)."""


def turn_outcome(ledger: RequestLedger) -> TurnOutcome:
    """What the turn changed (`TurnOutcome`), from the record of the root's tool calls (`RequestLedger.tool_calls`),
    never from the reply: `answer` when no call changed anything (the readers, a refused or failed write), else the
    first change in `TURN_ORDER`. The paste conversions of a summary turn (`conversions_made`) change the data without
    a tool call."""
    changes = {CALL_CHANGES.get((call.tool, call.outcome)) for call in ledger.tool_calls}
    if ledger.conversions_made is not None:
        changes.add("data")
    return next((outcome for outcome in TURN_ORDER if outcome in changes), "answer")


def plot_memory(memory: dict[str, list[str]] | None) -> dict[str, list[str]] | None:
    """A shipped version's plot memory as the `plot` event carries it, `{kept, added}` (entry ids only), or None when
    the server holds none for it: never two empty lists for a memory nobody read."""
    if not isinstance(memory, dict):
        return None
    kept, added = memory.get("kept"), memory.get("added")
    if not isinstance(kept, list) or not isinstance(added, list):
        return None
    return {"kept": _entry_ids(kept), "added": _entry_ids(added)}


def _entry_ids(items: list[Any]) -> list[str]:
    """Plot memory entry ids (`m3`), closed by their pattern: never an entry's text."""
    return [item for item in items if isinstance(item, str) and MEMORY_ID.fullmatch(item)]


def sse(event: str, data: dict[str, Any]) -> str:
    """One server-sent event in the wire format."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, separators=(',', ':'))}\n\n"


def _final_text(event: Event) -> str:
    if event.partial or not event.content or not event.content.parts:
        return ""
    if event.get_function_calls() or event.get_function_responses():
        return ""
    return "".join(part.text for part in event.content.parts if part.text and not part.thought)


class Translator:
    """Turns one run's ADK events into `anyplot/1` SSE strings."""

    def __init__(self, ledger: RequestLedger, run_id: str, *, spec_id: str | None = None) -> None:
        self.ledger = ledger
        self.run_id = run_id
        self.spec_id = spec_id
        self.plot_sent = False
        self.closing_sent = False

    def ready(self) -> str:
        return sse("ready", {"v": PROTOCOL, "run_id": self.run_id})

    @staticmethod
    def queued(position: int, waiting: int) -> str:
        """Where the run waits: `position` 1 runs next, `waiting` counts every queued entry, this one included."""
        return sse("status", {"step": QUEUED_STEP, "position": position, "waiting": waiting})

    @staticmethod
    def started() -> str:
        """The run that waited in the queue holds its slot now; sent once, after its last `queued` status."""
        return sse("status", {"step": STARTED_STEP})

    def translate(self, event: Event) -> list[str]:
        out: list[str] = []
        status = (event.custom_metadata or {}).get(STATUS_KEY)
        if isinstance(status, dict) and status.get("step") in STEPS:
            attempt = status.get("attempt")
            data: dict[str, Any] = {"step": status["step"], "attempt": attempt if isinstance(attempt, int) else 1}
            cap = status.get("max_attempts")
            if isinstance(cap, int) and not isinstance(cap, bool) and cap >= 1:
                data["max_attempts"] = cap
            findings = status.get("findings")
            if status.get("outcome") in ROUND_OUTCOMES and isinstance(findings, int):
                data.update(outcome=status["outcome"], findings=findings)
                defects = status.get("defects")
                if isinstance(defects, list):
                    # Rubric ids only (`VQ-05`): closed codes the page names in words, never text.
                    data["defects"] = [item for item in defects if isinstance(item, str) and RUBRIC_ID.fullmatch(item)]
            out.append(sse("status", data))
            return out
        if event.author == PIPELINE_AUTHOR and isinstance(event.output, dict) and "status" in event.output:
            if not self.plot_sent:
                self.plot_sent = True
                out.append(sse("plot", self._plot(event.output)))
            return out
        if event.author in (ROOT_AUTHOR, HALT_AUTHOR):
            text = _final_text(event)
            if not text.strip() or not event.is_final_response():
                return out
            out.extend(self._reply(text))
        return out

    def _plot(self, output: dict[str, Any]) -> dict[str, Any]:
        """The plot event: the allowlisted fields, the model-written lines sanitised to one plain line each.

        `version` goes out only when the result was stored as a version, and `memory` (`plot_memory`) only with it;
        `new_data` only for the page's "plot the new data", where the card's label says where the plot started.
        """
        data = {key: output[key] for key in PLOT_FIELDS if key in output}
        if data.get("new_data") is None:
            data.pop("new_data", None)
        if not isinstance(data.get("version"), int):
            data.pop("version", None)
        elif (memory := plot_memory(self.ledger.shipped_memory)) is not None:
            data["memory"] = memory
        for key in MODEL_WRITTEN_FIELDS:
            if isinstance(data.get(key), list):
                lines = (plain_line(item, spec_id=self.spec_id) for item in data[key] if isinstance(item, str))
                data[key] = [line for line in lines if line]
        return data

    def refusal(self) -> list[str]:
        """The ledger's refusal as the closing event, once; nothing without a refusal."""
        if self.ledger.refusal is None or self.closing_sent:
            return []
        self.closing_sent = True
        code, refusal_text = self.ledger.refusal
        return [sse("refusal", {"code": code, "text": refusal_text})]

    def _reply(self, text: str) -> list[str]:
        if self.ledger.refusal is not None:
            return self.refusal()
        if self.ledger.error is not None:
            return self.error(self.ledger.error)
        clean = sanitize(text, spec_id=self.spec_id)
        if clean:
            # The usage telemetry's `asked_question`: a bool computed here, the reply itself is never kept.
            self.ledger.reply_question = ends_with_question(clean)
            return [sse("message", {"text": clean})]
        if not self.plot_sent and not carries_answer(self.ledger):
            # A reply the sanitiser emptied (only a link, an HTML block, another spec's token) leaves the user as little
            # as an empty one: the route ends the turn with `no_reply`, as EmptyReply does, and a paste stays pending.
            # A plot, a switch or a stored change is the turn's answer, which sending it again would repeat.
            self.ledger.fail(NO_REPLY)
        return []

    def error(self, code: str) -> list[str]:
        if self.closing_sent:
            return []
        self.closing_sent = True
        return [sse("error", {"code": code, "ref": self.ledger.request_id})]

    def done(
        self,
        *,
        bindings: list[dict[str, Any]] | None = None,
        data_confirmed: bool | None = None,
        dataset: dict[str, Any] | None = None,
        language: dict[str, Any] | None = None,
        suggestion: object = NO_SUGGESTION,
        switch: dict[str, Any] | None = None,
        turn: TurnOutcome | None = None,
    ) -> str:
        """The closing event; with the session's bindings, confirmation state and a changed dataset when the route has them.

        The root's `set_bindings` tool can change the bindings during a turn, and its
        `prepare_data` or `generate_data` tool the dataset itself, which the page could
        not learn otherwise: it syncs its dropdowns, its step and its preview table from
        these fields, so a confirmation never covers bindings or data the user has not
        seen. `dataset` is `{preview, profile, bindings, warnings, context_lines, roles,
        changes, version}`, the dataset route's shape plus the change lines of the turn, only after
        a turn that changed the data; `version` is 1 when `generate_data` made the
        session's first data. `language` is the session language as `{language, source}`
        (`source` one of `default`, `pasted`, `detected` and `chosen`), which the scope guard's
        detection or the root's `set_language` may have set during the turn; the page's
        chip follows it. `suggestion` is the wide-table offer (`.to_long()`) as the dataset route answers it, or
        `null` for none, after every run on a session with data: its new column names follow the session
        language, which the turn may have changed, so the page's card always names what `.to_long()` applies.
        `switch` is `{library, plot}` after a turn whose root asked for a switch the user wanted in the chat
        (`switch_plot`, 2026-11-02): the page carries it out with the switch route and, with `plot`, the carry run.
        `turn` is what the turn changed (`turn_outcome`), after a turn that ended without an error, a refusal or the
        user's stop (`main.ended_well`); it goes last, so the fields before it read as they did without it.
        """
        payload: dict[str, Any] = {
            "llm_calls": self.ledger.llm_calls,
            "tokens": self.ledger.tokens + self.ledger.judge_tokens,
        }
        if bindings is not None:
            payload["bindings"] = bindings
        if data_confirmed is not None:
            payload["data_confirmed"] = data_confirmed
        if dataset is not None:
            payload["dataset"] = dataset
        if language is not None:
            payload["language"] = language
        if suggestion is not NO_SUGGESTION:
            payload["suggestion"] = suggestion
        if switch is not None:
            payload["switch"] = switch
        if turn is not None:
            payload["turn"] = turn
        return sse("done", payload)
