"""The `anyplot/1` stream translator: ADK events in, a fixed set of sanitised SSE events out.

ADK events are never forwarded. `Translator` maps them to the protocol the BFF
re-validates (`api/routers/agent.py`, `_EVENT_FIELDS`):

| Event | Fields | Comes from |
|---|---|---|
| `ready` | `v`, `run_id` | the start of the request, before it waits in the run queue |
| `status` | `step: "queued"`, `position`, `waiting` | the run queue, while the run waits: at once, on every change, and every 15 s unchanged (`position` 1 runs next; `waiting` counts every queued entry, this one included) |
| `status` | `step`, `attempt` | the pipeline's content-free `custom_metadata` progress events |
| `message` | `text` | a final, non-partial text response authored by the root (`anyplot`) |
| `plot` | `status`, `reason`, `attempts`, `artifacts`, `changes`, `residual_defects`, `version` | the pipeline's `PlotResult` output event; `version`, the stored version's number, only on `ok` and `needs_attention` |
| `refusal` | `code`, `text` | the request ledger's refusal, in place of the message: `out_of_scope`, `needs_data` (data that would have to be fetched) and `unsupported_content` from the scope guard, `budget` from the budgets; a user already over the daily budget gets it right after `ready`, without waiting in the queue |
| `error` | `code`, `ref` | `guard_unavailable`, `capacity` (also when the run waited the queue's maximum), `deadline` or `internal` |
| `done` | `llm_calls`, `tokens` | the end of every run, always last |

Function calls and responses, tool outputs, thoughts, partial chunks, adapter and
reviewer answers, and `error_details` are dropped. A message goes through the
output sanitiser (`anyplot/output_guard.sanitize`: no URL, link target, HTML, image
or long code block, at most 1,200 characters); the plot event's `changes` and
`residual_defects` are model-written too, so each goes through the same sanitiser and
becomes one plain line. Personal data in them (names, addresses, e-mail addresses,
phone numbers) stays: the user may plot and discuss their own table.

The output guard's length cap (`output_guard.reply_too_long`) runs earlier, in the
ScopeGuard plugin before ADK stores the root's reply: a refused reply reaches the
translator as the ledger's `out_of_scope` refusal, so it goes out as a `refusal` event,
and a reply after a `plot_pipeline` call arrives already cut at the cap.
"""

import json
from typing import Any

from google.adk.events.event import Event

from agents.anyplot.output_guard import plain_line, sanitize
from agents.anyplot.pipeline import STATUS_KEY
from agents.anyplot.plugins.ledger import RequestLedger


PROTOCOL = "anyplot/1"
ROOT_AUTHOR = "anyplot"
PIPELINE_AUTHOR = "plot_pipeline"
HALT_AUTHOR = "model"  # ADK's author of the event a before_run halt emits
STEPS = frozenset({"adapting", "checking", "rendering", "reviewing", "repairing"})
QUEUED_STEP = "queued"
"""The status step the route sends while the run waits in the run queue; no pipeline event carries it."""
PLOT_FIELDS = ("status", "reason", "attempts", "artifacts", "changes", "residual_defects", "version")
MODEL_WRITTEN_FIELDS = ("changes", "residual_defects")


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

    def translate(self, event: Event) -> list[str]:
        out: list[str] = []
        status = (event.custom_metadata or {}).get(STATUS_KEY)
        if isinstance(status, dict) and status.get("step") in STEPS:
            attempt = status.get("attempt")
            out.append(sse("status", {"step": status["step"], "attempt": attempt if isinstance(attempt, int) else 1}))
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

        `version` goes out only when the result was stored as a version.
        """
        data = {key: output[key] for key in PLOT_FIELDS if key in output}
        if not isinstance(data.get("version"), int):
            data.pop("version", None)
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
        return [sse("message", {"text": clean})] if clean else []

    def error(self, code: str) -> list[str]:
        if self.closing_sent:
            return []
        self.closing_sent = True
        return [sse("error", {"code": code, "ref": self.ledger.request_id})]

    def done(self, *, bindings: list[dict[str, Any]] | None = None, data_confirmed: bool | None = None) -> str:
        """The closing event; with the session's bindings and confirmation state when the route has them.

        The root's `set_bindings` tool can change the bindings during a turn, which the page
        could not learn otherwise: it syncs its dropdowns and its step from these two fields,
        so a confirmation never covers bindings the user has not seen.
        """
        payload: dict[str, Any] = {
            "llm_calls": self.ledger.llm_calls,
            "tokens": self.ledger.tokens + self.ledger.judge_tokens,
        }
        if bindings is not None:
            payload["bindings"] = bindings
        if data_confirmed is not None:
            payload["data_confirmed"] = data_confirmed
        return sse("done", payload)
