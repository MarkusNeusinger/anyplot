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
reviewer answers, and `error_details` are dropped. A message is sanitised: URLs
(with protocol-relative `//host` links), `data:`, `javascript:` and `mailto:` links,
HTML tags (an unclosed one too) and markdown images are removed, links keep their
text, fenced (backtick or tilde) and indented code blocks longer than 10 lines become
`[code omitted]`, bare web addresses, e-mail addresses and phone numbers are removed
(`anyplot/contact_filter.py`), `[[spec:id]]` tokens stay only for the session's own
spec, and the text is capped at 3,000 characters. The plot event's `changes` and
`residual_defects` are model-written too, so each goes through the same sanitiser
and becomes one plain line.

The output guard then checks the root's reply itself: a reply of more than
`MAX_REPLY_SENTENCES` sentences (root.md asks for two to five) that never mentions
the plot, its data or its code (`PLOT_WORDS`) becomes the fixed `out_of_scope`
refusal. Each check writes a content-free `output_guard` attribution line (the
verdict, the kinds of contact detail removed, the sentence count).

The sanitiser is a backstop, not an HTML filter: the UI must render message and
plot text as plain text, never as HTML or unescaped markdown.
"""

import json
import re
from typing import Any

from google.adk.events.event import Event

from agents.anyplot.contact_filter import contact_kinds, strip_contacts
from agents.anyplot.pipeline import STATUS_KEY
from agents.anyplot.plugins.ledger import RequestLedger, attribution
from agents.anyplot.policy import refusal


PROTOCOL = "anyplot/1"
ROOT_AUTHOR = "anyplot"
PIPELINE_AUTHOR = "plot_pipeline"
HALT_AUTHOR = "model"  # ADK's author of the event a before_run halt emits
STEPS = frozenset({"adapting", "checking", "rendering", "reviewing", "repairing"})
QUEUED_STEP = "queued"
"""The status step the route sends while the run waits in the run queue; no pipeline event carries it."""
PLOT_FIELDS = ("status", "reason", "attempts", "artifacts", "changes", "residual_defects", "version")
MODEL_WRITTEN_FIELDS = ("changes", "residual_defects")
MAX_MESSAGE_CHARS = 3_000
MAX_CODE_LINES = 10
CODE_OMITTED = "[code omitted]"
MAX_REPLY_SENTENCES = 5
"""The upper end of root.md's "two to five sentences, or a short list" rule.

A reply longer than this that never mentions the plot, its data or its code is not
a plot reply (an essay, an email, a recipe that got past the judge), so the
translator sends the fixed out-of-scope refusal instead. A plot reply that runs a
little long names the plot anyway, so the rule costs no legitimate reply."""
PLOT_WORDS = re.compile(
    r"(?i)\b(?:"
    r"plot|chart|graph|diagram|figure|axis|axes|x-axis|y-axis|label|title|legend|colou?r|palette|marker|bar|"
    r"line|scatter|column|row|data|dataset|binding|role|spec|theme|render|version|code|tick|scale|grid|"
    r"series|value|font|export|download|style|"
    r"diagramm|grafik|abbildung|achse|beschriftung|titel|legende|farbe|markierung|balken|linie|spalte|"
    r"zeile|daten|datensatz|zuordnung|rolle|darstellung|skala|raster|wert|schrift|stil"
    r")(?:s|es|e|en|n|er|ern|ed|d|ing|ting|ted|led|ling)?\b"
)
"""Words, English and German, any of which ties a reply to the plot, with their common endings
(`colors`, `labelled`, `Spalten`, `Werte`); a longer word that only starts with one (`still`) does not count."""
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+|\n+")
_WORD = re.compile(r"[^\W\d_]{2,}")

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
    text = strip_contacts(text)
    text = _SPEC_TOKEN.sub(spec_token, text)
    text = _BLANK_LINES.sub("\n\n", text).strip()
    if len(text) > MAX_MESSAGE_CHARS:
        text = text[: MAX_MESSAGE_CHARS - 1].rstrip() + "…"
    return text


def sentence_count(text: str) -> int:
    """Sentences and list items in `text`: the pieces between sentence ends and line breaks that hold a word."""
    return sum(1 for piece in _SENTENCE_END.split(text) if _WORD.search(piece))


def off_topic_reply(text: str) -> bool:
    """A reply longer than `MAX_REPLY_SENTENCES` that never mentions the plot, its data or its code."""
    return sentence_count(text) > MAX_REPLY_SENTENCES and not PLOT_WORDS.search(text)


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
        stripped = contact_kinds(text)
        off_topic = off_topic_reply(clean)
        if stripped or off_topic:
            attribution(
                "output_guard",
                self.ledger,
                verdict="off_topic_reply" if off_topic else "contacts_stripped",
                contacts=stripped,
                sentences=sentence_count(clean),
            )
        if off_topic:
            self.ledger.refuse("out_of_scope", refusal("out_of_scope", self.ledger.lang))
            return self.refusal()
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
