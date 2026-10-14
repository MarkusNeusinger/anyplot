"""The session language: one language for the root's replies and every text in the plot.

Owner decision of 2026-10-12. A session starts in English (`en`, source `default`),
whatever the browser's locale. A paste before any typed message sets the language its
notes or column names are written in (source `pasted`, `pasted_language`; owner request of
2026-10-14). The session's first in-scope typed message records the
language the scope judge names for it (source `detected`), also over `pasted`; a choice through
`PUT /v1/sessions/{sid}/language` or the root's `set_language` tool sets it for good
(source `chosen`), and detection never writes over a choice.

A language is a short name or code that matches `LANGUAGE_PATTERN` (`de`, `English`,
`Swedish`). Because a chosen one is free text that only the pattern bounds, every
prompt that carries it fences it as `<plot_language>`: data, never an instruction.

This module imports nothing from the package, so `schemas.py`, `session_state.py`,
the tools, the plugins and the routes can all share it without a cycle. The state
delta that sets the language (`session_state.language_delta`) lives next to the keys.
"""

import re
from typing import Literal


LANGUAGE_PATTERN = r"^[A-Za-z][A-Za-z -]{0,39}$"
"""A language name or code: a letter, then up to 39 letters, spaces or hyphens (ASCII only)."""
LANGUAGE_RE = re.compile(LANGUAGE_PATTERN)
MAX_LANGUAGE_CHARS = 40
LanguageSource = Literal["default", "pasted", "detected", "chosen"]
SOURCES: frozenset[str] = frozenset(("default", "pasted", "detected", "chosen"))
PASTE_OVERWRITES: frozenset[str] = frozenset(("default", "pasted"))
"""The sources a paste may write over: nothing the user typed or chose."""
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


def pasted_language(source: str, notes_lang: str | None, header_lang: str | None) -> str | None:
    """The session language a paste sets (source `pasted`), or None to keep the current one.

    Only while nothing the user typed or chose set it (`PASTE_OVERWRITES`): the scope
    judge's `lang` for the notes kept around the table first, else the dataset judge's
    `lang` for the column names. Both judges answer `en` for text without a clear language
    (`temperature_2m_max`, `x, y`), so `en` is no signal and keeps what is there: an
    English paste after a German one leaves `de`, and the default is English anyway.
    """
    if source not in PASTE_OVERWRITES:
        return None
    for lang in (notes_lang, header_lang):
        if lang and lang != DEFAULT_LANGUAGE and is_valid(lang):
            return normalise(lang)
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
