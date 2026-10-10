"""ScopeGuard: every free-text message is judged before any agent sees it, failing closed.

`on_user_message_callback`, the first hook of an invocation:

* a structured action (`RequestLedger.kind == "action"`, set by the `/v1` route for
  "Create plot") is not judged;
* a message with a non-text part is withheld with the `unsupported_content` refusal;
* the per-user and global daily budget is checked before the judge runs, and the
  judge's tokens are booked to the ledger and the usage book;
* the judge sees all text parts inside `<user_message>`, the root's last reply (at
  most 500 characters) inside `<last_assistant_turn>`, and the user's last three
  earlier turns (500 characters each, 1,500 in all, oldest first, as a JSON list)
  inside `<earlier_user_turns>`, so a request split across turns is judged as a
  whole; the fence tags are neutralised in all three;
* a timeout, transport error or unparseable answer after the one retry inside the
  4-second budget blocks with the error `guard_unavailable`;
* `out_of_scope` and `attack` withhold the message with the fixed `out_of_scope`
  refusal, and `needs_data` (a request for data the service would have to fetch) with
  the fixed `needs_data` refusal, each in the judge's language (English and German,
  English as the fallback); the run ends there, at the first turn.

A withheld message is replaced by `[message withheld by scope policy]` before ADK
stores it. `before_run_callback` then halts the run with the refusal text, which
ADK emits as one final event; the stream translator turns the ledger's refusal or
error into `refusal` or `error` events. The plugin never raises: an internal
failure is a `guard_unavailable` block.
"""

import json
import logging
from collections.abc import Sequence
from typing import Literal

from google.adk.agents.invocation_context import InvocationContext
from google.adk.plugins.base_plugin import BasePlugin
from google.genai import types

from ..models import JudgeUnavailable
from ..policy import fence, refusal, scope_rubric
from ..services import get_services
from ..settings import get_settings
from .ledger import RequestLedger, attribution, ledger_for


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

Turn = tuple[Literal["user", "assistant"], str]


REFUSAL_CODES: dict[str, str] = {"out_of_scope": "out_of_scope", "attack": "out_of_scope", "needs_data": "needs_data"}
"""The `refusal` event code of each refusing verdict. `attack` shares the out-of-scope reply, so an
attacker learns nothing about how the message was classified."""


def refusal_code(verdict: str) -> str:
    """The refusal code (and `refusals.yaml` entry) for a verdict other than `in_scope`."""
    return REFUSAL_CODES.get(verdict, "out_of_scope")


def _withheld() -> types.Content:
    return types.Content(role="user", parts=[types.Part(text=WITHHELD)])


def session_turns(invocation_context: InvocationContext) -> list[Turn]:
    """The session's text turns so far, oldest first: the user's messages and the root's replies.

    ADK calls `on_user_message_callback` before it stores the new message, so the
    message being judged is never among them. A withheld message appears as its
    placeholder, which tells the judge that an earlier turn was refused.
    """
    turns: list[Turn] = []
    for event in invocation_context.session.events:
        if event.author not in (USER_AUTHOR, ROOT_AGENT) or not event.content or not event.content.parts:
            continue
        text = "".join(part.text or "" for part in event.content.parts if part.text and not part.thought).strip()
        if text:
            turns.append(("user" if event.author == USER_AUTHOR else "assistant", text))
    return turns


def judge_context(turns: Sequence[Turn]) -> tuple[str, list[str]]:
    """The root's last reply (at most `MAX_CONTEXT_CHARS`) and the last `MAX_USER_TURNS` user turns, oldest first.

    Each user turn keeps at most `MAX_USER_TURN_CHARS` characters and all of them
    together at most `MAX_USER_CONTEXT_CHARS`, the newest first when the budget runs out.
    """
    assistant = next((text for role, text in reversed(turns) if role == "assistant"), "")[:MAX_CONTEXT_CHARS]
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
            ledger.refuse("budget", refusal("budget", ledger.lang))
            attribution("scope_guard", ledger, verdict="budget")
            return _withheld()
        text = "\n".join(part.text or "" for part in parts)
        context, earlier = judge_context(session_turns(invocation_context))
        try:
            verdict = await services.judge.judge(judge_input(text, context, earlier), scope_rubric())
        except JudgeUnavailable:
            ledger.fail("guard_unavailable")
            attribution("scope_guard", ledger, verdict="guard_unavailable")
            return _withheld()
        ledger.judge_tokens += verdict.tokens
        services.usage.add_tokens(user, verdict.tokens)
        ledger.lang = verdict.lang
        attribution(
            "scope_guard",
            ledger,
            verdict=verdict.verdict,
            lang=verdict.lang,
            judge_tokens=verdict.tokens,
            judge_input=verdict.input_tokens,
            judge_output=verdict.output_tokens,
        )
        if verdict.verdict != "in_scope":
            code = refusal_code(verdict.verdict)
            ledger.refuse(code, refusal(code, verdict.lang))
            return _withheld()
        return None

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
