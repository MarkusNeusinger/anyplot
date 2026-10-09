"""ScopeGuard: every free-text message is judged before any agent sees it, failing closed.

`on_user_message_callback`, the first hook of an invocation:

* a structured action (`RequestLedger.kind == "action"`, set by the `/v1` route for
  "Create plot") is not judged;
* a message with a non-text part is withheld with the `unsupported_content` refusal;
* the per-user and global daily budget is checked before the judge runs, and the
  judge's tokens are booked to the ledger and the usage book;
* the judge sees all text parts inside `<user_message>` plus the root's last reply
  (at most 500 characters) inside `<last_assistant_turn>`, with the fence tags
  neutralised;
* a timeout, transport error or unparseable answer after the one retry inside the
  4-second budget blocks with the error `guard_unavailable`;
* `out_of_scope` and `attack` withhold the message with the fixed refusal for the
  judge's language (English and German, English as the fallback).

A withheld message is replaced by `[message withheld by scope policy]` before ADK
stores it. `before_run_callback` then halts the run with the refusal text, which
ADK emits as one final event; the stream translator turns the ledger's refusal or
error into `refusal` or `error` events. The plugin never raises: an internal
failure is a `guard_unavailable` block.
"""

import logging

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
ROOT_AGENT = "anyplot"


def _withheld() -> types.Content:
    return types.Content(role="user", parts=[types.Part(text=WITHHELD)])


def last_assistant_turn(invocation_context: InvocationContext) -> str:
    """The root's last final text in the session, at most 500 characters."""
    for event in reversed(invocation_context.session.events):
        if event.author != ROOT_AGENT or not event.content or not event.content.parts:
            continue
        text = "".join(part.text or "" for part in event.content.parts if part.text and not part.thought)
        if text.strip():
            return text.strip()[:MAX_CONTEXT_CHARS]
    return ""


def judge_input(message_text: str, context: str) -> str:
    parts = [fence("user_message", message_text)]
    if context:
        parts.append(fence("last_assistant_turn", context))
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
        try:
            verdict = await services.judge.judge(
                judge_input(text, last_assistant_turn(invocation_context)), scope_rubric()
            )
        except JudgeUnavailable:
            ledger.fail("guard_unavailable")
            attribution("scope_guard", ledger, verdict="guard_unavailable")
            return _withheld()
        ledger.judge_tokens += verdict.tokens
        services.usage.add_tokens(user, verdict.tokens)
        ledger.lang = verdict.lang
        attribution("scope_guard", ledger, verdict=verdict.verdict, lang=verdict.lang, judge_tokens=verdict.tokens)
        if verdict.verdict != "in_scope":
            ledger.refuse("out_of_scope", refusal("out_of_scope", verdict.lang))
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
