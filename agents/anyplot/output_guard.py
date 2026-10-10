"""What the root writes, checked before anyone reads it: the sanitiser and the reply cap.

`sanitize(text)` is the deterministic sanitiser of every root message and every
model-written line of the plot event (`agents/stream.py`): URLs (with protocol-relative
`//host` links), `data:`, `javascript:` and `mailto:` links, HTML tags (an unclosed one
too) and markdown images are removed, links keep their text, fenced (backtick or tilde)
and indented code blocks longer than 10 lines become `[code omitted]`, `[[spec:id]]`
tokens stay only for the session's own spec, and the text is capped at
`MAX_MESSAGE_CHARS`. Personal data stays: names, postal and e-mail addresses, phone
numbers and bare web addresses are what a user's own table holds, and the chat may
name them. It is a backstop, not an HTML filter: the UI must render message and plot
text as plain text, never as HTML or unescaped markdown.

`reply_too_long(text)` is the output guard's rule, the same in every language: a root
reply longer than `MAX_MESSAGE_CHARS` characters once sanitised becomes the fixed
`out_of_scope` refusal instead of being cut off. root.md asks for "two to five
sentences, or a short list": about 300 to 700 characters in English, up to about 900
in languages with longer words, and a list of eight short steps fits in about 600. The
cap leaves a third on top of that, so a reply root.md allows is never refused, while a
long email, essay or advertisement that got past the judge is.

The cap counts characters, not sentences. A sentence count needs a segmenter for every
script (Chinese and Japanese end a sentence without a space, Thai without a mark), and
it counts every list item as a sentence, so a cap of five sentences would refuse a list
of six steps. Characters need neither and no word list in any language. In scripts that
write a word in one or two characters the same cap admits more words; the cap bounds
how much text one reply can carry, and the scope judge on the input side decides what a
request is for. A short off-topic reply that got past the judge is not caught here.

The ScopeGuard plugin runs the rule on the root's final reply before ADK stores it
(`on_event_callback`), so a refused reply never re-enters the judge's or the root's
context.

No ADK import.
"""

import re


MAX_MESSAGE_CHARS = 1_200
"""The longest root message. A longer reply is refused (`reply_too_long`); the sanitiser cuts any other
text at this length as a backstop. The plot event carries the changes and residual defects itself."""
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


def _clean(text: str, *, spec_id: str | None) -> str:
    """The sanitised text before the length cap."""

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
    return _BLANK_LINES.sub("\n\n", text).strip()


def sanitize(text: str, *, spec_id: str | None = None) -> str:
    """The deterministic output sanitiser for root messages."""
    text = _clean(text, spec_id=spec_id)
    if len(text) > MAX_MESSAGE_CHARS:
        text = text[: MAX_MESSAGE_CHARS - 1].rstrip() + "…"
    return text


def plain_line(text: str, *, spec_id: str | None = None) -> str:
    """A model-written note as one sanitised line: no code block, link target, URL, HTML or image."""
    return " ".join(sanitize(text, spec_id=spec_id).replace(CODE_OMITTED, " ").split())


def reply_length(text: str) -> int:
    """The characters of a root reply as the user would read it: sanitised, before the cap."""
    return len(_clean(text, spec_id=None))


def reply_too_long(text: str) -> bool:
    """Whether a root reply is longer than `MAX_MESSAGE_CHARS` once sanitised, in any language."""
    return reply_length(text) > MAX_MESSAGE_CHARS
