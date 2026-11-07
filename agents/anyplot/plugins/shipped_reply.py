"""ShippedReply: the closing reply after a shipped plot never asks for `.confirm()`, and no reply names the plot button.

A shipped plot (`ok`, `needs_attention`) was drawn from the data the user confirmed: the
pipeline refuses unconfirmed data (`not_ready`, `data_unconfirmed`), the result says
`data_confirmed: true` (`tool_safety.fence_pipeline_notes`), and `root.md` forbids asking for
`.confirm()` in that reply. A feedback case still had the root tell the user after an `ok`
plot that the data was not confirmed and to press `.confirm()`. A prompt rule that failed
gets a code check:

* `after_model_callback` reads the root's final text reply (no tool call, not partial,
  not a fixed refusal) when the turn shipped a plot (`ledger.shipped_in_turn`), and looks
  for the button's name, `.confirm()`, which is the same in every language. Each sentence
  that names it is dropped, so the user sees the rest of the reply word for word. The
  reply is edited in place and the callback returns None, so ReplyLanguage, which follows,
  still checks the edited reply's language. A reply ReplyLanguage asks for again comes from
  a direct model call that no plugin sees, so ReplyLanguage runs the same check
  (`scrub_shipped_reply`) on it before it replaces the first one.
* It writes a content-free attribution line (`shipped_reply`, verdict `dropped` with the
  number of sentences, or `kept` when every sentence names the button and nothing would be
  left, so the reply stays as it was).

Drop rather than ask the root again: dropping costs no model call and changes nothing else.
After a shipped plot no sentence that names `.confirm()` is right, and every other sentence
stays as the model wrote it, so a notice the reply must carry (a loader note, a requested
text the plot lacks) is never reworded or lost, which a re-ask, a new generation of the
whole reply, cannot promise. The limit: a separate sentence that says the data is not
confirmed without naming the button stays, because no code check reads that claim in
every language. The plugin never raises; a failure keeps the reply as it was.

The page has no `.confirm()` any more: `.create_plot()` confirms the data in its own click,
and neither `root.md` nor the session block names the old button. The check stays as the
backstop for a reply that still names it, which after a shipped plot is wrong twice over.

The plot button, in every turn: since the composer row has four fixed places, the line at the
chat's foot names the plot button and what it waits for, and `root.md` says a reply never
tells the user to press it (`.create_plot()`, `.update_plot()`, `.plot_all()`). The prompt had
told the root to say so in four places while its reply rules forbade it, so the rule gets the
same code check: every root reply, not only after a shipped plot, drops the sentences that name
one of the three, whose names are the same in every language, and logs `plot_button` with the
same verdicts. A reply in which every sentence names it stays whole, as above; a sentence that
says what to check without naming the button stays. When the user's own message names the
button ("what does .update_plot() do?"), the answer is about it: nothing is dropped, and the
verdict is `asked`. No share-of-the-reply rule: it would keep exactly the replies the check is
for ("I added the column. Check the data and press .create_plot()").
"""

import logging
import re

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_response import LlmResponse
from google.adk.plugins.base_plugin import BasePlugin

from ..policy import fixed_replies
from .budget import ROOT_AGENT
from .ledger import RequestLedger, attribution, ledger_for
from .reply_language import reply_text


logger = logging.getLogger(__name__)

CONFIRM = re.compile(r"\bconfirm\(\)", re.IGNORECASE)
"""Step 1's button as a reply names it (`.confirm()`, also without the dot); `reconfirm()` is no match."""
PLOT_BUTTON = re.compile(r"\b(?:create_plot|update_plot|plot_all)\(\)", re.IGNORECASE)
"""The composer's plot button by any of its names (`.create_plot()`, `.update_plot()`, `.plot_all()`)."""
_CLOSERS = "\"'”’)\\]*_`"
_BREAK = re.compile(
    rf"((?<=[.!?…])[ \t]+|(?<=[.!?…][{_CLOSERS}])[ \t]+|(?<=[.!?…][{_CLOSERS}]{{2}})[ \t]+|(?<=[。！？])[ \t]*)"
)
"""Between two sentences of one line: after a full stop, a question or exclamation mark and a space, also when up
to two closing quotes, brackets or Markdown marks follow it (`."`, `.)`, `.**`), or after a CJK one. A dot inside
`.confirm()` or `3.5` is followed by no space, so it never ends a sentence. A break this finds is only a candidate:
`_sentences` joins the pieces again after an abbreviation, or before a piece that starts in lower case."""
_ABBREVIATIONS = frozenset(
    {
        # English
        "e.g.", "i.e.", "etc.", "vs.", "ca.", "approx.", "no.", "nr.", "fig.", "incl.", "max.", "min.", "resp.",
        # German
        "z.", "b.", "z.b.", "bzw.", "mio.", "mrd.", "tsd.", "usw.", "evtl.", "ggf.", "inkl.", "d.", "h.", "d.h.",
        "u.", "a.", "u.a.", "s.", "vgl.", "bspw.", "zzgl.", "abb.",
    }
)  # fmt: skip
"""Words that end in a dot without ending the sentence ("e.g. with a title", "z. B. mit Titel", "6,5 Mio. Euro"),
lower-cased; German nouns start in upper case, so the case of the next word alone cannot tell."""
_MARKER = re.compile(r"^\s*(?:[-*+•]|\d+[.)])\s+")
"""A list item's marker at the start of a line, which a dropped first sentence must not take with it."""
_BARE_MARKER = re.compile(r"^\s*(?:[-*+•]|\d+[.)])?\s*$")
"""A line with no sentence left: empty, or only a list marker."""


def _sentences(line: str) -> list[tuple[str, str]]:
    """The sentences of one line, each with the gap after it. A candidate break (`_BREAK`) after a known
    abbreviation, or before a piece that starts in lower case, is no break: the pieces stay one sentence."""
    parts = _BREAK.split(line)
    pieces = list(zip(parts[0::2], [*parts[1::2], ""], strict=True))
    joined: list[tuple[str, str]] = []
    for sentence, gap in pieces:
        if joined:
            before, between = joined[-1]
            words = before.split()
            after_abbreviation = bool(words) and words[-1].lower().lstrip("(\"'`*_") in _ABBREVIATIONS
            if after_abbreviation or sentence[:1].islower():
                joined[-1] = (before + between + sentence, gap)
                continue
        joined.append((sentence, gap))
    return joined


def drop_sentences(text: str, pattern: re.Pattern[str]) -> tuple[str, int]:
    """`text` without its sentences that `pattern` finds, and how many it dropped.

    Lines are kept apart (a list, paragraphs), a line left with only its list marker goes, and
    so does the blank line a dropped paragraph leaves behind.
    """
    lines: list[str] = []
    dropped = 0
    for line in text.split("\n"):
        if not pattern.search(line):
            lines.append(line)
            continue
        marker = _MARKER.match(line)
        prefix = marker.group(0) if marker else ""
        kept = ""
        for sentence, gap in _sentences(line[len(prefix) :]):
            if pattern.search(sentence):
                dropped += 1
                continue
            kept += sentence + gap
        kept = (prefix + kept).rstrip()
        if not _BARE_MARKER.match(kept):
            lines.append(kept)
    joined = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    return joined, dropped


def drop_confirm(text: str) -> tuple[str, int]:
    """`text` without its sentences that name `.confirm()`, and how many it dropped."""
    return drop_sentences(text, CONFIRM)


def drop_plot_button(text: str) -> tuple[str, int]:
    """`text` without its sentences that name the plot button, and how many it dropped."""
    return drop_sentences(text, PLOT_BUTTON)


def replace_reply(response: LlmResponse, text: str) -> None:
    """Put `text` in place of the response's reply text, in its first text part; thoughts stay as they are."""
    if response.content is None or not response.content.parts:
        return
    parts = []
    placed = False
    for part in response.content.parts:
        if part.text and not part.thought:
            if not placed:
                parts.append(part.model_copy(update={"text": text}))
                placed = True
            continue
        parts.append(part)
    response.content.parts = parts


def user_named_plot_button(ledger: RequestLedger) -> bool:
    """The user's own last message in the root's request names the plot button ("what does .update_plot() do?"):
    then the answer is about the button, and its sentences stay. Tool results come back as user content without
    text, so the last user content that has text is the user's message."""
    request = ledger.root_request
    contents = getattr(request, "contents", None) or []
    for content in reversed(contents):
        if getattr(content, "role", None) != "user":
            continue
        text = " ".join(part.text for part in content.parts or [] if part.text and not part.thought)
        if text:
            return bool(PLOT_BUTTON.search(text))
    return False


def scrub_shipped_reply(ledger: RequestLedger, response: LlmResponse) -> None:
    """Drop the `.confirm()` sentences of a root reply in a turn whose plot shipped, and the sentences that name
    the plot button in any turn, in place; never raises.

    The plugin's check, and ReplyLanguage's on the reply it asked for again, which no plugin sees. Each check logs
    its own line (`shipped_reply`, `plot_button`): `dropped`, `kept` when nothing would be left, or for the plot
    button `asked` when the user's message named it. When the two checks together would leave nothing, the reply
    goes out as the model wrote it, never as what the first check left of it.
    """
    try:
        if ledger.halted:
            return
        reply = reply_text(response)
        if reply is None or reply in fixed_replies():
            return
        edited = reply
        lines: list[tuple[str, str, int]] = []
        if ledger.shipped_in_turn and CONFIRM.search(edited):
            kept, dropped = drop_confirm(edited)
            lines.append(("shipped_reply", "dropped" if kept else "kept", dropped))
            edited = kept or edited
        if PLOT_BUTTON.search(edited):
            if user_named_plot_button(ledger):
                lines.append(("plot_button", "asked", 0))
            else:
                kept, dropped = drop_plot_button(edited)
                lines.append(("plot_button", "dropped" if kept else "kept", dropped))
                if not kept:
                    # Nothing would be left: the whole reply as written, also what the first check dropped.
                    edited = reply
                    lines = [(hook, "kept", count) for hook, _, count in lines]
                else:
                    edited = kept
        for hook, verdict, count in lines:
            attribution(hook, ledger, verdict=verdict, sentences=count)
        if edited != reply:
            replace_reply(response, edited)
    except Exception as exc:
        logger.warning("shipped reply check failed: %s", type(exc).__name__)


class ShippedReplyPlugin(BasePlugin):
    """Drops the sentences of the root's reply that ask for `.confirm()` after a shipped plot, or name the plot
    button in any turn."""

    def __init__(self, name: str = "anyplot_shipped_reply") -> None:
        super().__init__(name=name)

    async def after_model_callback(
        self, *, callback_context: CallbackContext, llm_response: LlmResponse
    ) -> LlmResponse | None:
        if callback_context.agent_name != ROOT_AGENT or llm_response.partial:
            return None
        scrub_shipped_reply(ledger_for(callback_context.invocation_id), llm_response)
        # Edited in place, never returned: a returned response would end the plugin chain before ReplyLanguage.
        return None
