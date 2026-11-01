"""ScopeGuard: every free-text message is judged before any agent sees it, failing closed.

`on_user_message_callback`, the first hook of an invocation:

* a structured action (`RequestLedger.kind == "action"`, set by the `/v1` route for
  "Create plot") is not judged;
* a message with a non-text part is withheld with the `unsupported_content` refusal;
* the per-user and global daily budget is checked before the judge runs, and the
  judge's tokens are booked to the ledger and the usage book;
* the judge sees all text parts inside `<user_message>`, the root's last real reply
  (at most 500 characters; never a fixed refusal or the outage line, `is_service_text`)
  inside `<last_assistant_turn>`, and the user's last three
  earlier turns (500 characters each, 1,500 in all, oldest first, as a JSON list)
  inside `<earlier_user_turns>`, so a request split across turns is judged as a
  whole; the fence tags are neutralised in all three;
* a timeout, transport error or unparseable answer after the one retry, which
  waits a short back-off first (`models.JUDGE_RETRY_BACKOFF_S`), inside the 4-second
  budget blocks with the error `guard_unavailable`;
* `out_of_scope` and `attack` withhold the message with the fixed `out_of_scope`
  refusal, `needs_data` (a request for data the service would have to fetch) with
  the fixed `needs_data` refusal, and `other_library` (this plot in another library or
  language) with the fixed `other_library` answer, a pointer to the catalogue, each in
  the language the judge names (`policy.refusal`: English, German, French, Spanish,
  Italian, Portuguese, Dutch, Polish, Chinese, Vietnamese and Russian, English for every
  other language); the run ends there, at the first turn;
* an `attack` verdict is a strike against the user (`UsageBook.add_strike`), once
  per distinct message text: from `AGENT_ATTACK_STRIKES` strikes on, the daily check
  above refuses the user with the `locked_out` refusal for the rest of the day (a
  spent token budget keeps the `budget` refusal);
* the session's `AGENT_SESSION_REFUSALS`-th counted refusal (`counted_codes`: `out_of_scope`
  or `attack`, and `other_library` only with `AGENT_OTHER_LIBRARY_COUNTS`; `needs_data`
  never counts, `scope_refusals`) closes the session: that refusal goes out as
  `session_closed` instead, and the `/messages` route answers every later turn of the
  session with the same refusal before the judge runs (the paste route with
  `403 session_closed`), so the user starts a new session. With
  `AGENT_SESSION_CLOSE_WARNING` the counted refusal one before it carries the fixed
  `close_warning` suffix. The strikes above are per user and day and count `attack`
  only; this count is per session and needs no state of its own;
* the judge's `lang` for the session's first in-scope typed message becomes the
  session language with the source `detected` (`session_state.LANGUAGE`, the replies'
  language; a plot the session already has keeps its own, `session_state.plot_language`), unless one
  is set: a later message never changes it, a choice (`chosen`) never yields to it, a
  refused message never sets it, and an `en` verdict counts only for a message of at
  least three words, because the judge also answers `en` for a message without a clear
  language (`sin x` keeps the default, and the next typed message is judged again). A
  language derived from the pasted data (source `pasted`) counts as unset here: the
  first typed message's language replaces it. The write is a content-free state event appended after the judge's line and the refusal
  branch; it never raises, so a failed write is one `language_write_failed` line and the
  accepted message still goes through;
* with `AGENT_KEEP_REFUSALS`, a refused message's text and verdict go into the
  session's bounded refusal ring (`services.RefusalStore`), which only the feedback
  bundle shows; the attribution line never carries the text.

A withheld message is replaced before ADK stores it: by
`[message withheld by scope policy: <code>]` after the judge's refusal (`out_of_scope`
or `needs_data`, `withheld_text`), so the judge's next context keeps the verdict, and by
the bare `[message withheld by scope policy]` otherwise. `before_run_callback` then halts the run with the refusal text, which
ADK emits as one final event (author `model`); the stream translator turns the
ledger's refusal or error into `refusal` or `error` events. The judge's context
skips that halt event's text, as it skips every fixed reply (`judge_context`): after a
refusal the judge sees the withheld placeholder, with its refusal code, among the user
turns and the last reply a model wrote, never the refusal text, which primed it to refuse
the next message alike.

`on_event_callback` is the output side: the root's final reply goes through the
output guard's length cap (`output_guard.reply_too_long`, the same in every language)
before ADK stores it. A reply over the cap is replaced, in the stored event too, by
the fixed `out_of_scope` refusal in the ledger's language, and the ledger's refusal
makes the translator send it as a `refusal` event; so a refused reply never reaches
the user, the judge's next context or the root's own. A turn that called
`plot_pipeline` is the exception: its reply describes a plot the user already has, so
it is stored and sent cut at the cap, as the sanitiser cuts it, instead of being
refused after the plot. Either case writes a content-free `output_guard` attribution
line (`reply_too_long` or `reply_cut`, with the reply's length); an internal failure
lets the reply through to the translator's sanitiser.

The plugin never raises: an internal failure of the input side is a
`guard_unavailable` block.
"""

import json
import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Literal

from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event
from google.adk.events.event_actions import EventActions
from google.adk.plugins.base_plugin import BasePlugin
from google.genai import types

from ..language import DEFAULT_LANGUAGE
from ..models import JudgeUnavailable, JudgeVerdict
from ..output_guard import reply_length, reply_too_long, sanitize
from ..policy import fence, fixed_replies, refusal, refusals, scope_rubric
from ..services import KeptRefusal, get_services
from ..session_state import LANGUAGE_SOURCE, SPEC_ID, language_delta
from ..settings import get_settings
from .ledger import RequestLedger, attribution, judge_budget_tokens, ledger_for


logger = logging.getLogger(__name__)

WITHHELD = "[message withheld by scope policy]"
GUARD_UNAVAILABLE_TEXT = "The request could not be checked right now. Please try again in a moment."
MAX_CONTEXT_CHARS = 500
"""The root's last reply as the judge sees it."""
MAX_USER_TURNS = 3
MAX_USER_TURN_CHARS = 500
MAX_USER_CONTEXT_CHARS = 1_500
"""The earlier user turns the judge sees: the last three, 500 characters each, 1,500 in all (about 400 tokens)."""
ROOT_AGENT = "anyplot"
USER_AUTHOR = "user"
MIN_ENGLISH_DETECTION_WORDS = 3
"""An `en` verdict records the session language only for a message of at least this many words:
the judge also answers `en` for a message without a clear language, such as `sin x`."""
HALT_AUTHOR = "model"
"""ADK's author of the event a `before_run_callback` halt emits: the fixed refusal or the outage text."""

Turn = tuple[Literal["user", "assistant"], str]


REFUSAL_CODES: dict[str, str] = {
    "out_of_scope": "out_of_scope",
    "attack": "out_of_scope",
    "needs_data": "needs_data",
    "other_library": "other_library",
}
"""The `refusal` event code of each refusing verdict. `attack` shares the out-of-scope reply, so an
attacker learns nothing about how the message was classified."""
CLOSE_WARNING = "close_warning"
"""The `refusals.yaml` entry appended to the counted refusal one before the closing one (`AGENT_SESSION_CLOSE_WARNING`)."""
LOCKED_OUT = "locked_out"
"""The refusal code (and `refusals.yaml` entry) of a user past `AGENT_ATTACK_STRIKES` today."""
JUDGED_REFUSALS = frozenset(REFUSAL_CODES.values())
"""The refusal codes a withheld placeholder may carry (`withheld_text`)."""


def refusal_code(verdict: str) -> str:
    """The refusal code (and `refusals.yaml` entry) for a verdict other than `in_scope`."""
    return REFUSAL_CODES.get(verdict, "out_of_scope")


def withheld_text(code: str | None = None) -> str:
    """The placeholder a withheld message is stored as: with the refusal code for a judged refusal.

    `[message withheld by scope policy: needs_data]` keeps the earlier verdict for the judge's next
    context, so "do it anyway" after a `needs_data` refusal gets `needs_data` again, without a
    natural-language refusal text in that context (which primed the judge, `judge_context`). Only
    the refusal codes appear (`attack` is `out_of_scope` there too); a refusal before the judge
    (`budget`, `unsupported_content`) or an outage keeps the bare `WITHHELD`.
    """
    return f"{WITHHELD[:-1]}: {code}]" if code in JUDGED_REFUSALS else WITHHELD


def _withheld(code: str | None = None) -> types.Content:
    return types.Content(role="user", parts=[types.Part(text=withheld_text(code))])


SESSION_CLOSED = "session_closed"
"""The refusal code (and `refusals.yaml` entry) of a session closed after `AGENT_SESSION_REFUSALS` refusals."""
COUNTED_PLACEHOLDER = withheld_text("out_of_scope")
"""The stored form of every `out_of_scope` and `attack` refusal: what `scope_refusals` always counts."""


def counted_codes(other_library_counts: bool | None = None) -> frozenset[str]:
    """The refusal codes that count toward closing a session: `out_of_scope` (which `attack` shares), and
    `other_library` only with `AGENT_OTHER_LIBRARY_COUNTS`. `needs_data` never counts."""
    if other_library_counts is None:
        other_library_counts = get_settings().other_library_counts
    return frozenset({"out_of_scope", "other_library"} if other_library_counts else {"out_of_scope"})


def scope_refusals(events: Sequence[Event], counted: frozenset[str] | None = None) -> int:
    """The session's counted scope-judge refusals (`counted_codes`), counted from its withheld messages.

    `out_of_scope` and `attack` store the same placeholder (`withheld_text("out_of_scope")`), a
    `needs_data` or `other_library` refusal its own, and a refusal sent before the judge (budget,
    unsupported content, the message limits, a closed session) the bare one or nothing, so only the
    counted kinds match. The count lives in the session's own events: it ends with the session, and no
    state is written for it.
    """
    placeholders = {withheld_text(code) for code in (counted_codes() if counted is None else counted)}
    count = 0
    for event in events:
        if event.author != USER_AUTHOR or not event.content or not event.content.parts:
            continue
        if "".join(part.text or "" for part in event.content.parts) in placeholders:
            count += 1
    return count


def session_turns(invocation_context: InvocationContext) -> list[Turn]:
    """The session's text turns so far, oldest first: the user's messages and the replies they got.

    ADK calls `on_user_message_callback` before it stores the new message, so the
    message being judged is never among them. A withheld message appears as its
    placeholder, which tells the judge that an earlier turn was refused, and the halt
    event after it (author `model`) as the assistant turn that carried the fixed
    refusal, which `judge_context` then leaves out.
    """
    turns: list[Turn] = []
    for event in invocation_context.session.events:
        if event.author not in (USER_AUTHOR, ROOT_AGENT, HALT_AUTHOR) or not event.content or not event.content.parts:
            continue
        text = "".join(part.text or "" for part in event.content.parts if part.text and not part.thought).strip()
        if text:
            turns.append(("user" if event.author == USER_AUTHOR else "assistant", text))
    return turns


def is_service_text(text: str) -> bool:
    """Whether an assistant turn is the service's own fixed text (a refusal or the outage line), not a model's reply."""
    stripped = text.strip()
    for warning in refusals().get(CLOSE_WARNING, {}).values():
        if stripped.endswith(warning) and stripped != warning:
            stripped = stripped[: -len(warning)].strip()  # a refusal with the closing warning appended
            break
    return stripped == GUARD_UNAVAILABLE_TEXT or stripped in fixed_replies()


def judge_context(turns: Sequence[Turn]) -> tuple[str, list[str]]:
    """The root's last real reply (at most `MAX_CONTEXT_CHARS`) and the last `MAX_USER_TURNS` user turns, oldest first.

    A fixed refusal or the outage line (`is_service_text`) is never the context: the
    live case of 2026-10-14 had the German `needs_data` refusal for a weather question
    prime the judge to refuse the next message, a question about the user's own data,
    as `needs_data` too. The judge sees the last reply a model wrote instead (or none),
    and the withheld placeholder among the user turns still marks the refused one.
    Each user turn keeps at most `MAX_USER_TURN_CHARS` characters and all of them
    together at most `MAX_USER_CONTEXT_CHARS`, the newest first when the budget runs out.
    """
    assistant = next((text for role, text in reversed(turns) if role == "assistant" and not is_service_text(text)), "")[
        :MAX_CONTEXT_CHARS
    ]
    earlier: list[str] = []
    left = MAX_USER_CONTEXT_CHARS
    for role, text in reversed(turns):
        if role != "user":
            continue
        if len(earlier) == MAX_USER_TURNS or left <= 0:
            break
        piece = text[: min(MAX_USER_TURN_CHARS, left)]
        earlier.append(piece)
        left -= len(piece)
    return assistant, earlier[::-1]


def judge_input(message_text: str, context: str, earlier: Sequence[str] = ()) -> str:
    """The judge's input: the earlier user turns, the root's last reply and the message, each fenced, in that order."""
    parts = []
    if earlier:
        parts.append(fence("earlier_user_turns", json.dumps(list(earlier), ensure_ascii=False)))
    if context:
        parts.append(fence("last_assistant_turn", context))
    parts.append(fence("user_message", message_text))
    return "\n".join(parts)


class ScopeGuardPlugin(BasePlugin):
    """Judges free text, withholds out-of-scope and attack messages, and halts the run with a fixed reply."""

    def __init__(self, name: str = "anyplot_scope_guard") -> None:
        super().__init__(name=name)

    async def on_user_message_callback(
        self, *, invocation_context: InvocationContext, user_message: types.Content
    ) -> types.Content | None:
        ledger = ledger_for(invocation_context.invocation_id)
        try:
            return await self._judge(invocation_context, ledger, user_message)
        except Exception as exc:  # the guard fails closed
            logger.warning("scope guard failed: %s", type(exc).__name__)
            ledger.fail("guard_unavailable")
            return _withheld()

    async def _judge(
        self, invocation_context: InvocationContext, ledger: RequestLedger, user_message: types.Content
    ) -> types.Content | None:
        if ledger.kind == "action":
            return None
        parts = user_message.parts or []
        if not parts or any(part.text is None for part in parts):
            ledger.refuse("unsupported_content", refusal("unsupported_content", ledger.lang))
            attribution("scope_guard", ledger, verdict="unsupported_content")
            return _withheld()
        services = get_services()
        settings = get_settings()
        user = ledger.user_id or invocation_context.session.user_id
        if not services.usage.daily_ok(user, settings):
            reason = LOCKED_OUT if services.usage.locked_out(user, settings) else "budget"
            ledger.refuse(reason, refusal(reason, ledger.lang))
            attribution("scope_guard", ledger, verdict=reason)
            return _withheld()
        text = "\n".join(part.text or "" for part in parts)
        context, earlier = judge_context(session_turns(invocation_context))
        try:
            verdict = await services.judge.judge(judge_input(text, context, earlier), scope_rubric())
        except JudgeUnavailable:
            ledger.fail("guard_unavailable")
            attribution("scope_guard", ledger, verdict="guard_unavailable")
            return _withheld()
        weighted = judge_budget_tokens(
            verdict.tokens, verdict.input_tokens, verdict.output_tokens, settings.judge_model
        )
        ledger.judge_tokens += verdict.tokens
        ledger.book_judge(verdict.input_tokens, verdict.output_tokens, verdict.tokens)
        ledger.budget_tokens += weighted
        services.usage.add_tokens(user, weighted)
        ledger.lang = verdict.lang
        strikes = services.usage.add_strike(user, text) if verdict.verdict == "attack" else None
        attribution(
            "scope_guard",
            ledger,
            verdict=verdict.verdict,
            lang=verdict.lang,
            judge_tokens=verdict.tokens,
            judge_input=verdict.input_tokens,
            judge_output=verdict.output_tokens,
            **({"strikes": strikes} if strikes is not None else {}),
        )
        if verdict.verdict != "in_scope":
            if settings.keep_refusals:
                services.refusals.add(
                    invocation_context.session.id,
                    KeptRefusal(verdict.verdict, verdict.lang, text, datetime.now(UTC).isoformat(timespec="seconds")),
                )
            code = refusal_code(verdict.verdict)
            shown = code
            text_out = refusal(code, verdict.lang)
            counted = counted_codes(settings.other_library_counts)
            if code in counted:
                count = scope_refusals(invocation_context.session.events, counted) + 1
                if count >= settings.session_refusals:
                    shown = SESSION_CLOSED  # the route refuses every later turn of the session before the judge
                    text_out = refusal(SESSION_CLOSED, verdict.lang)
                    attribution("scope_guard", ledger, verdict=SESSION_CLOSED, refusals=count)
                elif settings.session_close_warning and count == settings.session_refusals - 1:
                    # The live test of 2026-10-14 closed a session without warning: the refusal before the closing
                    # one says so, in a fixed suffix of the same language.
                    text_out = f"{text_out} {refusal(CLOSE_WARNING, verdict.lang)}"
                    attribution("scope_guard", ledger, verdict=CLOSE_WARNING, refusals=count)
            ledger.refuse(shown, text_out)
            return _withheld(code)
        await self._detect(invocation_context, ledger, verdict, text)
        return None

    @staticmethod
    async def _detect(
        invocation_context: InvocationContext, ledger: RequestLedger, verdict: JudgeVerdict, text: str
    ) -> bool:
        """The session's first in-scope typed message sets the session language, once (`detected`).

        Called only for an accepted message, after the judge's attribution line, so the
        attack strike and the refusal never depend on it. Never raises: the message is
        already accepted and booked, so a failed state write (a DELETE racing the turn, a
        store outage) is a log line, not a refusal. ADK applies the delta to the session's
        state in place, so the root's session block of this very turn names the language.
        """
        session = invocation_context.session
        if session.state.get(LANGUAGE_SOURCE) in ("detected", "chosen"):
            return False
        if verdict.lang == DEFAULT_LANGUAGE and len(text.split()) < MIN_ENGLISH_DETECTION_WORDS:
            return False  # "English or unclear": the next typed message gets its chance
        event = Event(
            invocation_id=invocation_context.invocation_id,
            author=USER_AUTHOR,
            actions=EventActions(state_delta=language_delta(verdict.lang, "detected")),
        )
        try:
            await invocation_context.session_service.append_event(session=session, event=event)
        except Exception as exc:
            logger.warning("language detection failed: %s", type(exc).__name__)
            attribution("scope_guard", ledger, verdict="language_write_failed")
            return False
        attribution("scope_guard", ledger, verdict="language_detected", lang=verdict.lang)
        return True

    async def on_event_callback(self, *, invocation_context: InvocationContext, event: Event) -> Event | None:
        try:
            return self._guard_reply(invocation_context, event)
        except Exception as exc:  # the translator's sanitiser still runs
            logger.warning("output guard failed: %s", type(exc).__name__)
            return None

    @staticmethod
    def _guard_reply(invocation_context: InvocationContext, event: Event) -> Event | None:
        """A final reply of the root over the cap, replaced; None keeps the event.

        After a `plot_pipeline` call in this turn the reply describes a plot the user already has, so it is
        cut at the cap as the sanitiser cuts it; otherwise it becomes the fixed `out_of_scope` refusal.
        """
        if event.author != ROOT_AGENT or event.partial or not event.content or not event.content.parts:
            return None
        if event.get_function_calls() or event.get_function_responses() or not event.is_final_response():
            return None
        text = "".join(part.text for part in event.content.parts if part.text and not part.thought)
        ledger = ledger_for(invocation_context.invocation_id)
        if not text.strip() or ledger.refusal is not None or ledger.error is not None:
            return None
        state_spec = invocation_context.session.state.get(SPEC_ID)
        spec_id = state_spec if isinstance(state_spec, str) else None  # its tokens stay, as in the stream
        if not reply_too_long(text, spec_id=spec_id):
            return None
        chars = reply_length(text, spec_id=spec_id)
        if ledger.pipeline_calls:
            attribution("output_guard", ledger, verdict="reply_cut", chars=chars)
            cut = sanitize(text, spec_id=spec_id)
            return Event(author=event.author, content=types.Content(role="model", parts=[types.Part(text=cut)]))
        attribution("output_guard", ledger, verdict="reply_too_long", chars=chars)
        fixed = refusal("out_of_scope", ledger.lang)
        ledger.refuse("out_of_scope", fixed)
        return Event(author=event.author, content=types.Content(role="model", parts=[types.Part(text=fixed)]))

    async def before_run_callback(self, *, invocation_context: InvocationContext) -> types.Content | None:
        try:
            ledger = ledger_for(invocation_context.invocation_id)
            if ledger.refusal is not None:
                return types.Content(role="model", parts=[types.Part(text=ledger.refusal[1])])
            if ledger.error is not None:
                return types.Content(role="model", parts=[types.Part(text=GUARD_UNAVAILABLE_TEXT)])
            return None
        except Exception as exc:
            logger.warning("scope guard halt failed: %s", type(exc).__name__)
            return types.Content(role="model", parts=[types.Part(text=GUARD_UNAVAILABLE_TEXT)])
