"""ScopeGuard: every free-text message is judged before any agent sees it, failing closed.

`on_user_message_callback`, the first hook of an invocation:

* a structured action (`RequestLedger.kind == "action"`, set by the `/v1` route for
  "Create plot") is not judged;
* a message with a non-text part is withheld with the `unsupported_content` refusal;
* the per-user and global daily budget is checked before the judge runs (the
  `service_paused` refusal when only the global one is spent, `ledger.day_refusal`),
  and the judge's tokens are booked to the ledger and the usage book;
* the judge sees all text parts inside `<user_message>`, the root's last real reply
  (at most 500 characters; never a fixed refusal or the outage line, `is_service_text`)
  inside `<last_assistant_turn>`, and the user's last three
  earlier turns (500 characters each, 1,500 in all, oldest first, as a JSON list)
  inside `<earlier_user_turns>`, so a request split across turns is judged as a
  whole; the fence tags are neutralised in every block;
* a timeout, transport error or unparseable answer after the one retry, which
  waits a short back-off first (`models.JUDGE_RETRY_BACKOFF_S`), inside the 4-second
  budget blocks with the error `guard_unavailable`;
* `out_of_scope` and `attack` withhold the message with the fixed `out_of_scope`
  refusal, `needs_data` (a request for data the service would have to fetch) with
  the fixed `needs_data` refusal, and `other_library` (this plot in another library or
  language) with the fixed `other_library` answer, a pointer to the catalogue, each in
  the session language, whatever language the message is in (English until the user
  picks another, like every reply; `policy.refusal`: English, German, French, Spanish,
  Italian, Portuguese, Dutch, Polish, Chinese, Vietnamese and Russian, English for every
  other language); the run ends there, at the first turn;
* the note sent with a paste not summarized yet (`RequestLedger.paste_note`) is judged
  as notes that came with a table: a `<pasted_table>` block before the message names the
  spec's title and the table's column names on one bounded line, never a cell
  (`paste_table_line`, which the route writes to `RequestLedger.paste_table` when the
  table is still stored). Such a note is never `needs_data` or `out_of_scope` while that
  table is there: it came with the data it is about, and the judge read a statistic's
  name in it ("unemployment rate per country") as a request to fetch figures and a
  question about the table's entries as general advice (persona tests of 2026-11-06).
  Either verdict goes on as `in_scope`, with a `paste_note_in_scope` attribution line
  after the judge's. A rescued `out_of_scope` counts toward no refusal, so at most
  `AGENT_PASTE_NOTE_RESCUES` go on per user and day (`UsageBook.note_rescue_ok`, twice
  as many per network); past that the verdict stands (`paste_note_rescues_spent`) and
  the note is refused and counted as any message. `attack` refuses the note as any
  message, and `other_library` gets its fixed pointer to the catalogue;
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
* the judge's `lang` for an in-scope typed message never sets the session language:
  when it names another language, the page offers it
  once (`language.offer`), and the user's click on the offer sets it. There is no offer
  after a pick (`chosen`), for a language offered before, for a refused message, or for
  an `en` verdict on a message under three words, because the judge also answers `en`
  for a message without a clear language (`sin x`). The offer is recorded as
  `session_state.LANGUAGE_OFFERED` in a content-free state event after the judge's line
  and the refusal branch, and kept on the ledger (`RequestLedger.language_offer`), which
  the turn's `done` carries. The write never raises, so a failed one is a
  `language_offer_failed` line, and the accepted message still goes through without an offer;
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
before ADK stores it. A reply over the cap is never refused: the persona tests of
2026-11-06 got the fixed `out_of_scope` refusal for an on-topic summary of a pasted
bank export and for an on-topic answer about the user's data, both too long. The root
is asked once for a shorter reply instead, the way ReplyLanguage asks again
(`reply_language.follow_up_request` and `ask_root`): its own request without tools, the
long reply as its previous turn and `SHORTEN_LINE`. The shorter answer replaces the
reply when it fits the cap and is whole (not cut at the output cap, not surely in
another language than the session's, ShippedReply's check run on it); otherwise the
shorter of the two is stored and sent cut at the cap, as the sanitiser cuts it. At
most one such ask per turn (`RequestLedger.reply_shortened`), booked like any call
(`budget.book_response`). The stored event holds the reply at the length the user reads
it (a shorter answer as the root wrote it, like any reply the translator sanitises on
its way out; a cut one as the sanitiser cut it), so a long reply never re-enters the
judge's or the root's context whole. Each step writes a
content-free `output_guard` attribution line: `reply_too_long` (the reply's length),
then `shortened` (the new length) or `reply_cut` (the length cut, and the `reason` the
shorter answer was not used: `asked`, `no_request`, `budget`, `error`, `cut_off`,
`empty`, `language` or `too_long`). An internal failure lets the reply through to the
translator's sanitiser, which cuts it at the cap too.

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
from google.adk.models.llm_request import LlmRequest
from google.adk.plugins.base_plugin import BasePlugin
from google.genai import types

from ..language import offer
from ..language_detect import mismatch
from ..models import JudgeUnavailable, JudgeVerdict
from ..output_guard import MAX_MESSAGE_CHARS, reply_length, reply_too_long, sanitize
from ..policy import fence, fixed_replies, refusal, refusals, scope_rubric
from ..services import KeptRefusal, get_services
from ..session_state import SPEC_ID, offered_delta, read_session
from ..settings import get_settings
from .budget import book_response
from .ledger import RequestLedger, attribution, budget_allows, day_refusal, finish_name, judge_budget_tokens, ledger_for
from .reply_language import ask_root, checked_language, follow_up_request, reply_text
from .shipped_reply import scrub_shipped_reply


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
HALT_AUTHOR = "model"
"""ADK's author of the event a `before_run_callback` halt emits: the fixed refusal or the outage text."""
PASTE_NOTE_PASSES = frozenset({"needs_data", "out_of_scope"})
"""The verdicts a note sent with a stored paste goes on with as `in_scope` (owner decision of 2026-11-06), `out_of_scope`
within the day's `AGENT_PASTE_NOTE_RESCUES`: it came with the table it is about, so nothing is to be fetched and a
question about the table is no general advice. `attack` refuses it as any message, and `other_library` gets its fixed
pointer to the catalogue."""
MAX_TABLE_COLUMNS = 20
MAX_TABLE_NAME_CHARS = 40
MAX_TABLE_TITLE_CHARS = 120
"""The `<pasted_table>` line's bounds (`paste_table_line`): at most 20 column names of 40 characters each and a
title of 120, about 1,100 characters at their worst, beside a judge input of about 2,500 tokens."""
SHORTEN_TARGET_CHARS = 800
"""The length the output guard asks a too-long reply to be rewritten in: two thirds of the cap
(`output_guard.MAX_MESSAGE_CHARS`), since a model counts characters loosely."""
SHORTEN_LINE = (
    "Your last reply is {chars} characters long, and the chat shows at most {limit}. Write the same reply again in "
    "at most {target} characters: the same language and the same answer, with every notice it gives, and column "
    "names, values and code unchanged; leave out detail. Answer with the reply only."
)

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


def _one_line(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def paste_table_line(title: str, columns: Sequence[str]) -> str:
    """The table a paste note came with, as the scope judge reads it: the spec's title and the column names, no cell.

    One line, bounded (`MAX_TABLE_COLUMNS`, `MAX_TABLE_NAME_CHARS`, `MAX_TABLE_TITLE_CHARS`), each name JSON-quoted
    (it is the user's text, screened at the paste by the dataset judge), and the count of the names left out. The
    title is catalogue text that started as a public issue: `judge_input` fences the whole line as data.
    """
    names = [
        json.dumps(_one_line(name, MAX_TABLE_NAME_CHARS), ensure_ascii=False) for name in columns[:MAX_TABLE_COLUMNS]
    ]
    more = len(columns) - len(names)
    listed = ", ".join(names) + (f", and {more} more" if more > 0 else "")
    return f"Plot: {_one_line(title, MAX_TABLE_TITLE_CHARS)}. Columns of the pasted table: {listed or 'none'}."


def judge_input(message_text: str, context: str, earlier: Sequence[str] = (), table: str | None = None) -> str:
    """The judge's input: the earlier user turns, the root's last reply, the pasted table and the message, each fenced.

    `table` is the `<pasted_table>` line of a note sent with a paste (`paste_table_line`), right before the note.
    """
    parts = []
    if earlier:
        parts.append(fence("earlier_user_turns", json.dumps(list(earlier), ensure_ascii=False)))
    if context:
        parts.append(fence("last_assistant_turn", context))
    if table:
        parts.append(fence("pasted_table", table))
    parts.append(fence("user_message", message_text))
    return "\n".join(parts)


def _replaced(event: Event, text: str) -> Event:
    """The root's final reply event with `text` in place of its reply, as the output guard stores and sends it.

    A copy of the event, so its id, invocation, actions and usage stay with it whatever ADK's runner merges back.
    """
    return event.model_copy(update={"content": types.Content(role="model", parts=[types.Part(text=text)])})


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
        if not services.usage.daily_ok(user, settings, tier=ledger.tier):
            # `locked_out`, `service_paused` or `budget`
            reason = day_refusal(services.usage, user, settings, tier=ledger.tier)
            ledger.refuse(reason, refusal(reason, ledger.lang))
            attribution("scope_guard", ledger, verdict=reason)
            return _withheld()
        text = "\n".join(part.text or "" for part in parts)
        context, earlier = judge_context(session_turns(invocation_context))
        table = ledger.paste_table if ledger.paste_note else None
        try:
            verdict = await services.judge.judge(judge_input(text, context, earlier, table), scope_rubric())
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
        # `ledger.lang` stays the session language's: a refusal follows the session, never the message, so a German
        # message in an English session gets the English refusal, as every reply there is English.
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
        if verdict.verdict in PASTE_NOTE_PASSES and ledger.paste_note and ledger.paste_table:
            # The note came with the data it is about: the root reads it beside the table. A statistic's name in it
            # reads as a request for figures, a question about the table as general advice; an attack stays refused.
            # A rescued `out_of_scope` counts toward no refusal, so the user's day caps how many go on.
            if verdict.verdict == "out_of_scope" and not services.usage.note_rescue_ok(user, settings):
                attribution("scope_guard", ledger, verdict="paste_note_rescues_spent")
            else:
                if verdict.verdict == "out_of_scope":
                    services.usage.add_note_rescue(user)
                attribution("scope_guard", ledger, verdict="paste_note_in_scope")
                verdict = verdict.model_copy(update={"verdict": "in_scope"})
        if verdict.verdict != "in_scope":
            if settings.keep_refusals:
                services.refusals.add(
                    invocation_context.session.id,
                    KeptRefusal(verdict.verdict, verdict.lang, text, datetime.now(UTC).isoformat(timespec="seconds")),
                )
            code = refusal_code(verdict.verdict)
            shown = code
            text_out = refusal(code, ledger.lang)
            counted = counted_codes(settings.other_library_counts)
            if code in counted:
                count = scope_refusals(invocation_context.session.events, counted) + 1
                if count >= settings.session_refusals:
                    shown = SESSION_CLOSED  # the route refuses every later turn of the session before the judge
                    text_out = refusal(SESSION_CLOSED, ledger.lang)
                    attribution("scope_guard", ledger, verdict=SESSION_CLOSED, refusals=count)
                elif settings.session_close_warning and count == settings.session_refusals - 1:
                    # The live test of 2026-10-14 closed a session without warning: the refusal before the closing
                    # one says so, in a fixed suffix of the same language.
                    text_out = f"{text_out} {refusal(CLOSE_WARNING, ledger.lang)}"
                    attribution("scope_guard", ledger, verdict=CLOSE_WARNING, refusals=count)
            ledger.refuse(shown, text_out)
            return _withheld(code)
        await self._offer(invocation_context, ledger, verdict, text)
        return None

    @staticmethod
    async def _offer(
        invocation_context: InvocationContext, ledger: RequestLedger, verdict: JudgeVerdict, text: str
    ) -> bool:
        """An in-scope typed message in another language than the session's makes the page offer it, once.

        Called only for an accepted message, after the judge's attribution line, so the attack
        strike and the refusal never depend on it. It records the language as offered and keeps
        the offer on the ledger for the turn's `done`; the session language stays as it is. Never
        raises: the message is already accepted and booked, so a failed state write (a DELETE
        racing the turn, a store outage) is a log line and no offer, never a refusal.
        """
        session = invocation_context.session
        try:
            view = read_session(session.state)
            if view is None:
                return False
            found = offer(view.language, view.language_source, view.language_offered, verdict.lang, len(text.split()))
            if found is None:
                return False
            event = Event(
                invocation_id=invocation_context.invocation_id,
                author=USER_AUTHOR,
                actions=EventActions(state_delta=offered_delta(view.language_offered, found)),
            )
            await invocation_context.session_service.append_event(session=session, event=event)
        except Exception as exc:
            logger.warning("language offer failed: %s", type(exc).__name__)
            attribution("scope_guard", ledger, verdict="language_offer_failed")
            return False
        ledger.language_offer = (found, "message")
        attribution("scope_guard", ledger, verdict="language_offer", lang=found, basis="message")
        return True

    async def on_event_callback(self, *, invocation_context: InvocationContext, event: Event) -> Event | None:
        try:
            return await self._guard_reply(invocation_context, event)
        except Exception as exc:  # the translator's sanitiser still runs
            logger.warning("output guard failed: %s", type(exc).__name__)
            return None

    @classmethod
    async def _guard_reply(cls, invocation_context: InvocationContext, event: Event) -> Event | None:
        """A final reply of the root over the cap, replaced; None keeps the event.

        The root is asked once for a shorter reply (`_shorter`), which replaces the reply when it fits the cap;
        otherwise the shorter of the two is cut at the cap as the sanitiser cuts it. Never a refusal: a long reply is
        an on-topic one at least as often as not, and the judge on the input side decides what a request is for.
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
        attribution("output_guard", ledger, verdict="reply_too_long", chars=chars)
        shorter, reason = await cls._shorter(invocation_context, ledger, text, chars)
        if shorter is not None:
            if not reply_too_long(shorter, spec_id=spec_id):
                attribution("output_guard", ledger, verdict="shortened", chars=reply_length(shorter, spec_id=spec_id))
                return _replaced(event, shorter)
            reason = "too_long"
            if reply_length(shorter, spec_id=spec_id) < chars:
                text, chars = shorter, reply_length(shorter, spec_id=spec_id)
        attribution("output_guard", ledger, verdict="reply_cut", chars=chars, reason=reason)
        return _replaced(event, sanitize(text, spec_id=spec_id))

    @staticmethod
    async def _shorter(
        invocation_context: InvocationContext, ledger: RequestLedger, text: str, chars: int
    ) -> tuple[str | None, str]:
        """The root's shorter answer for a too-long reply, asked once per turn; else None and why not.

        Its own request without tools, the long reply as its previous turn and `SHORTEN_LINE`, the way ReplyLanguage
        asks again. The answer is no use when it was cut at the output cap, holds no text, or is surely in another
        language than the session's; ShippedReply's check runs on it, since no plugin sees this direct call.
        """
        request = ledger.root_request
        if ledger.reply_shortened:
            return None, "asked"
        if not isinstance(request, LlmRequest):
            return None, "no_request"
        if not budget_allows(ledger, get_services().usage, get_settings()):
            return None, "budget"
        ledger.reply_shortened = True
        line = SHORTEN_LINE.format(chars=chars, limit=MAX_MESSAGE_CHARS, target=SHORTEN_TARGET_CHARS)
        turns = [
            types.Content(role="model", parts=[types.Part(text=text)]),
            types.Content(role="user", parts=[types.Part(text=line)]),
        ]
        try:
            answer = await ask_root(follow_up_request(request, turns))
        except Exception as exc:
            logger.warning("output guard re-ask failed: %s", type(exc).__name__)
            return None, "error"
        if answer is None:
            return None, "error"
        book_response(ledger, ROOT_AGENT, invocation_context.session.user_id, answer)
        if finish_name(answer.finish_reason) == "MAX_TOKENS":
            return None, "cut_off"
        scrub_shipped_reply(ledger, answer)
        again = reply_text(answer)
        if again is None or again in fixed_replies():
            return None, "empty"
        language = checked_language(invocation_context.session.state)
        if language is not None and mismatch(again, language) is not None:
            return None, "language"
        return again, ""

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
