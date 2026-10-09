"""The `anyplot/1` stream translator: ADK events in, a fixed set of sanitised SSE events out.

ADK events are never forwarded. `Translator` maps them to the protocol the BFF
re-validates (`api/routers/agent.py`, `_EVENT_FIELDS`):

| Event | Fields | Comes from |
|---|---|---|
| `ready` | `v`, `run_id` | the start of the request, before it waits in the run queue |
| `status` | `step: "queued"`, `position`, `waiting` | the run queue, while the run waits: at once, on every change, and every 15 s unchanged (`position` 1 runs next; `waiting` counts every queued entry, this one included) |
| `status` | `step`, `attempt` | the pipeline's content-free `custom_metadata` progress events |
| `message` | `text` | a final, non-partial text response authored by the root (`anyplot`) |
| `plot` | `status`, `reason`, `attempts`, `artifacts`, `changes`, `residual_defects` | the pipeline's `PlotResult` output event |
| `refusal` | `code`, `text` | the request ledger's refusal (scope guard or budget), in place of the message |
| `error` | `code`, `ref` | `guard_unavailable`, `capacity` (also when the run waited the queue's maximum), `deadline` or `internal` |
| `done` | `llm_calls`, `tokens` | the end of every run, always last |

Function calls and responses, tool outputs, thoughts, partial chunks, adapter and
reviewer answers, and `error_details` are dropped. A message is sanitised: URLs
(with protocol-relative `//host` links), `data:`, `javascript:` and `mailto:` links,
HTML tags (an unclosed one too) and markdown images are removed, links keep their
text, fenced (backtick or tilde) and indented code blocks longer than 10 lines become
`[code omitted]`, `[[spec:id]]` tokens stay only for the session's own spec, and the
text is capped at 3,000 characters. The plot event's `changes` and
`residual_defects` are model-written too, so each goes through the same sanitiser
and becomes one plain line.

The sanitiser is a backstop, not an HTML filter: the UI must render message and
plot text as plain text, never as HTML or unescaped markdown.
"""

import json
import re
from typing import Any

from google.adk.events.event import Event

from agents.anyplot.pipeline import STATUS_KEY
from agents.anyplot.plugins.ledger import RequestLedger


PROTOCOL = "anyplot/1"
ROOT_AUTHOR = "anyplot"
PIPELINE_AUTHOR = "plot_pipeline"
HALT_AUTHOR = "model"  # ADK's author of the event a before_run halt emits
STEPS = frozenset({"adapting", "checking", "rendering", "reviewing", "repairing"})
QUEUED_STEP = "queued"
"""The status step the route sends while the run waits in the run queue; no pipeline event carries it."""
PLOT_FIELDS = ("status", "reason", "attempts", "artifacts", "changes", "residual_defects")
MODEL_WRITTEN_FIELDS = ("changes", "residual_defects")
MAX_MESSAGE_CHARS = 3_000
MAX_CODE_LINES = 10
CODE_OMITTED = "[code omitted]"

# A fenced block (backticks or tildes, three or more, closed by the same run or the end).
_FENCE = re.compile(r"(?ms)^[ \t]{0,3}(`{3,}|~{3,})[^\n]*\n(.*?)(?:^[ \t]{0,3}\1[ \t]*$|\Z)")
# A run of indented lines (four spaces or a tab), the other markdown code block.
_INDENTED = re.compile(r"(?m)(?:^(?: {4}|\t)[^\n]*(?:\n|\Z))+")
_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_LINK = re.compile(r"\[([^\]]+)\]\((?:[^)]*)\)")
_HTML = re.compile(r"</?[A-Za-z][^>]*>")
_HTML_UNCLOSED = re.compile(r"(?m)</?[A-Za-z][^>\n]*$")
_URL = re.compile(
    r"(?i)\b(?:https?|ftp)://\S+|\bwww\.\S+|\b(?:data|javascript|file|mailto):\S+|(?<![\w:/])//[^\s/]+\S*"
)
_SPEC_TOKEN = re.compile(r"\[\[spec:([a-z0-9-]{1,100})\]\]")
_BLANK_LINES = re.compile(r"\n{3,}")


def sse(event: str, data: dict[str, Any]) -> str:
    """One server-sent event in the wire format."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, separators=(',', ':'))}\n\n"


def sanitize(text: str, *, spec_id: str | None = None) -> str:
    """The deterministic output sanitiser for root messages."""

    def code_block(match: re.Match[str]) -> str:
        return match.group(0) if len(match.group(2).splitlines()) <= MAX_CODE_LINES else CODE_OMITTED

    def indented_block(match: re.Match[str]) -> str:
        block = match.group(0)
        if len(block.splitlines()) <= MAX_CODE_LINES:
            return block
        return CODE_OMITTED + ("\n" if block.endswith("\n") else "")

    def spec_token(match: re.Match[str]) -> str:
        return match.group(0) if spec_id is not None and match.group(1) == spec_id else ""

    text = _FENCE.sub(code_block, text)
    text = _INDENTED.sub(indented_block, text)
    text = _IMAGE.sub("", text)
    text = _LINK.sub(r"\1", text)
    text = _HTML.sub("", text)
    text = _HTML_UNCLOSED.sub("", text)
    text = _URL.sub("", text)
    text = _SPEC_TOKEN.sub(spec_token, text)
    text = _BLANK_LINES.sub("\n\n", text).strip()
    if len(text) > MAX_MESSAGE_CHARS:
        text = text[: MAX_MESSAGE_CHARS - 1].rstrip() + "…"
    return text


def plain_line(text: str, *, spec_id: str | None = None) -> str:
    """A model-written note as one sanitised line: no code block, link target, URL, HTML or image."""
    return " ".join(sanitize(text, spec_id=spec_id).replace(CODE_OMITTED, " ").split())


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
        """The plot event: the allowlisted fields, the model-written lines sanitised to one plain line each."""
        data = {key: output[key] for key in PLOT_FIELDS if key in output}
        for key in MODEL_WRITTEN_FIELDS:
            if isinstance(data.get(key), list):
                lines = (plain_line(item, spec_id=self.spec_id) for item in data[key] if isinstance(item, str))
                data[key] = [line for line in lines if line]
        return data

    def _reply(self, text: str) -> list[str]:
        if self.ledger.refusal is not None:
            if self.closing_sent:
                return []
            self.closing_sent = True
            code, refusal_text = self.ledger.refusal
            return [sse("refusal", {"code": code, "text": refusal_text})]
        if self.ledger.error is not None:
            return self.error(self.ledger.error)
        clean = sanitize(text, spec_id=self.spec_id)
        return [sse("message", {"text": clean})] if clean else []

    def error(self, code: str) -> list[str]:
        if self.closing_sent:
            return []
        self.closing_sent = True
        return [sse("error", {"code": code, "ref": self.ledger.request_id})]

    def done(self) -> str:
        return sse(
            "done", {"llm_calls": self.ledger.llm_calls, "tokens": self.ledger.tokens + self.ledger.judge_tokens}
        )
