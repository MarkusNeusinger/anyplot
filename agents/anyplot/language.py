"""The session language, the language of the root's replies, and the plot language, the language of the plot's text.

The page is English, so a session starts in English (`en`, source `default`), whatever the
browser's locale, and stays in it until the user picks another language. A pick is the chip at the top, a request in
the chat (the root's `set_language` tool) or an accepted offer. When the scope judge names
another language for a typed message, or for the notes or column names of a paste, the page
offers it once (`offer`): one line with a button. Ignoring the line keeps everything as it is.
Accepting goes through `PUT /v1/sessions/{sid}/language` with `via: offer` (source `offer`).
The chip and `set_language` set source `chosen`, which is final: no offer comes after it.
Detection never sets the language itself.

Owner decision of 2026-11-01: the plot's text keeps its language. The first plot is written
in the session language; every later version keeps the language of the session's latest
plot, until the user asks for the plot's text in another language (the chip, or
`set_language` with `applies_to` `plot` or `both`; `session_state.plot_language`). A
follow-up message in another language changes the replies, never the plot.

A language is a short name or code that matches `LANGUAGE_PATTERN` (`de`, `English`,
`Swedish`). Because a chosen one is free text that only the pattern bounds, every
prompt that carries it fences it (`<reply_language>`, `<plot_language>`): data, never an instruction.

This module imports nothing from the package, so `schemas.py`, `session_state.py`,
the tools, the plugins and the routes can all share it without a cycle. The state
delta that sets the language (`session_state.language_delta`) lives next to the keys.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal


LANGUAGE_PATTERN = r"^[A-Za-z][A-Za-z -]{0,39}$"
"""A language name or code: a letter, then up to 39 letters, spaces or hyphens (ASCII only)."""
LANGUAGE_RE = re.compile(LANGUAGE_PATTERN)
MAX_LANGUAGE_CHARS = 40
LanguageSource = Literal["default", "chosen", "offer"]
SOURCES: frozenset[str] = frozenset(("default", "chosen", "offer"))
"""`default`: nobody picked yet (English). `chosen`: the chip or a request in the chat, final. `offer`: the user
accepted the page's offer of a language the judge named for a message or a paste."""
LEGACY_SOURCES: frozenset[str] = frozenset(("pasted", "detected"))
"""The sources detection wrote before 2026-11-08; a session that still holds one reads it as `default`."""
OfferBasis = Literal["message", "data"]
"""What an offer's language was found in: a typed message, or a paste's notes or column names."""
MIN_ENGLISH_OFFER_WORDS = 3
"""An `en` verdict offers English only for a message of at least this many words: the judge also answers `en` for a
message without a clear language, such as `sin x`."""
MAX_OFFERED = 12
"""The most languages a session records as offered (`session_state.LANGUAGE_OFFERED`)."""
LanguageTarget = Literal["both", "plot", "replies"]
LANGUAGE_TARGETS: frozenset[str] = frozenset(("both", "plot", "replies"))
"""What the root's `set_language` sets (`applies_to`): the replies, the plot's text, or both."""
DEFAULT_LANGUAGE = "en"
COMMON_LANGUAGES = ("en", "zh", "de", "vi", "es", "fr", "nl", "pt", "ru", "it")
"""The chip's list: the site's ten most used visitor languages (Plausible, owner's choice of 2026-10-12).

`refusals.yaml` has hand-written lines for each of them, and for Polish besides.
"""
_NAMES: dict[str, str] = {
    "english": "en",
    "german": "de",
    "deutsch": "de",
    "french": "fr",
    "francais": "fr",
    "spanish": "es",
    "espanol": "es",
    "italian": "it",
    "italiano": "it",
    "portuguese": "pt",
    "portugues": "pt",
    "dutch": "nl",
    "nederlands": "nl",
    "polish": "pl",
    "polski": "pl",
    "chinese": "zh",
    "vietnamese": "vi",
    "russian": "ru",
    "japanese": "ja",
}
"""The English names and the ASCII endonyms of the refusal languages and Japanese, by their code."""
ENGLISH_NAMES: dict[str, str] = {
    "en": "English",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "pl": "Polish",
    "zh": "Chinese",
    "vi": "Vietnamese",
    "ru": "Russian",
    "ja": "Japanese",
}
"""The English name of each code in `_NAMES`: server text, so a prompt may name the language outside a fence."""


@dataclass(frozen=True)
class NumberFormat:
    """How the text in a plot writes numbers in one language: its decimal and thousands marks and its short words
    for large numbers, each as `(power of ten, word)`, smallest first."""

    decimal: str
    thousands: str
    suffixes: tuple[tuple[int, str], ...]


NUMBER_FORMATS: dict[str, NumberFormat] = {
    "en": NumberFormat(".", ",", ((3, "k"), (6, "M"), (9, "B"))),
    "de": NumberFormat(",", ".", ((3, "Tsd."), (6, "Mio."), (9, "Mrd."))),
    "fr": NumberFormat(",", " ", ((3, "k"), (6, "M"), (9, "Md"))),
    "es": NumberFormat(",", ".", ((3, "mil"), (6, "M"), (9, "mil M"))),
    "it": NumberFormat(",", ".", ((3, "mila"), (6, "Mln"), (9, "Mld"))),
    "pt": NumberFormat(",", ".", ((3, "mil"), (6, "mi"), (9, "bi"))),
    "nl": NumberFormat(",", ".", ((3, "k"), (6, "mln"), (9, "mld"))),
    "pl": NumberFormat(",", " ", ((3, "tys."), (6, "mln"), (9, "mld"))),
    "ru": NumberFormat(",", " ", ((3, "тыс."), (6, "млн"), (9, "млрд"))),
    "vi": NumberFormat(",", ".", ((3, "N"), (6, "Tr"), (9, "Tỷ"))),
    "zh": NumberFormat(".", ",", ((4, "万"), (8, "亿"))),
    "ja": NumberFormat(".", ",", ((4, "万"), (8, "億"))),
}
"""The number format of each language in `ENGLISH_NAMES`, the server's own table (Q4 of the live test of 2026-10-14:
a German plot showed "6.0 M" and "5.30"). `locale` is a banned import in plot code, so the adapter formats with
`FuncFormatter` or an f-string and these marks (`number_format_table`), and gate G12 measures the decimal mark.
Chinese and Japanese group large numbers by ten thousand (万) and a hundred million (亿, 億). A language
outside the table has no number rule and no G12."""


def number_format(language: str) -> NumberFormat | None:
    """The number format of a session language (`de`, `Deutsch` and `German` share one), or None outside the table."""
    return NUMBER_FORMATS.get(canonical(language))


def number_format_table() -> str:
    """The table as Markdown rows for the adapter's static instruction: code, language, marks and words."""
    names = {" ": "space", " ": "narrow no-break space", " ": "no-break space"}
    rows = ["| Plot language | Decimal mark | Thousands mark | Large numbers |", "|---|---|---|---|"]
    for code, spec in NUMBER_FORMATS.items():
        words = ", ".join(f"10^{power}: {word}" for power, word in spec.suffixes)
        thousands = names.get(spec.thousands, f"`{spec.thousands}`")
        rows.append(f"| `{code}` ({ENGLISH_NAMES[code]}) | `{spec.decimal}` | {thousands} | {words} |")
    return "\n".join(rows)


def normalise(value: str) -> str:
    """The stored form of a language.

    One space between words and none outside them; a bare two-letter code in lower
    case (`DE` is `de`); a known English name or endonym as its code (`English` is `en`,
    `Deutsch` is `de`); anything else as typed (`Swedish`).
    """
    text = " ".join(value.split())
    code = _NAMES.get(text.lower())
    if code is not None:
        return code
    return text.lower() if len(text) == 2 else text


def canonical(value: str) -> str:
    """The comparison key: `normalise`, then case-folded, so `Swedish` and `swedish` are one language."""
    return normalise(value).casefold()


def same_language(a: str, b: str) -> bool:
    """Whether two values name the same language (`de`, `Deutsch` and `German` do)."""
    return canonical(a) == canonical(b)


def is_valid(value: str) -> bool:
    """Whether `value` matches `LANGUAGE_PATTERN`."""
    return bool(LANGUAGE_RE.fullmatch(value))


def read_source(value: object) -> LanguageSource:
    """A stored language source as the session reads it: one of `SOURCES`, else `default` (a legacy one too)."""
    if value == "chosen":
        return "chosen"
    if value == "offer":
        return "offer"
    return "default"


def offer(language: str, source: str, offered: Sequence[str], lang: str | None, words: int | None = None) -> str | None:
    """The language to offer the user for a judge's `lang`, in its stored form, or None for no offer.

    `language` and `source` are the session's, `offered` the languages it offered before
    (`session_state.LANGUAGE_OFFERED`). `words` is the word count of a typed message, None for a
    paste's notes or column names. There is no offer after a pick (`chosen`, final), for an invalid
    code, for the session language itself, for a language offered before (each language comes
    once), or once `MAX_OFFERED` languages were offered. The judges answer `en` for text without a
    clear language (`sin x`, `temperature_2m_max`, `x, y`), so `en` is offered only for a message
    of at least `MIN_ENGLISH_OFFER_WORDS` words, never for data. It can come only after the user
    accepted another language: the chat may offer English back, once.
    """
    if source == "chosen" or not lang or not is_valid(lang) or same_language(lang, language):
        return None
    seen = {canonical(item) for item in offered}
    if canonical(lang) in seen or len(seen) >= MAX_OFFERED:
        return None
    if canonical(lang) == DEFAULT_LANGUAGE and (words is None or words < MIN_ENGLISH_OFFER_WORDS):
        return None
    return normalise(lang)


def data_offer(
    language: str, source: str, offered: Sequence[str], notes_lang: str | None, header_lang: str | None
) -> str | None:
    """The language a paste offers (`offer` with no word count): the notes' `lang` first, else the column names'."""
    for lang in (notes_lang, header_lang):
        found = offer(language, source, offered, lang)
        if found is not None:
            return found
    return None


def english_name(language: str) -> str | None:
    """The English name of a session language from `ENGLISH_NAMES` (`de` and `Deutsch` are `German`), else None.

    Only a language the table knows gets a name: the value itself is free text the pattern
    bounds, so it reaches a prompt only fenced, and this name is the server's own word for it.
    """
    return ENGLISH_NAMES.get(canonical(language))


def refusal_lang(language: str) -> str:
    """The ISO 639-1 code `policy.refusal` looks up for a session language.

    A two-letter code as it is, a known name through the table (`Deutsch` is `de`),
    anything else English. Never the first two letters of a name: `Plattdeutsch` would
    read as Polish and `Esperanto` as Spanish.
    """
    text = canonical(language)
    return text if len(text) == 2 and text.isalpha() else DEFAULT_LANGUAGE
