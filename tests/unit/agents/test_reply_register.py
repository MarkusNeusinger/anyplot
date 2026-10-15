"""One register per language: the fixed texts and the root's rule address the user informally.

Live test round 4 of 2026-10-15: a German summary said "Aus Ihren Notizen ..." while the
refusals and the rest of the chat said "du". The fixed refusals set the register (`refusals.yaml`:
du, tu, tú, je), and root.md tells the model to keep it. This test keeps both true.
"""

import re
from pathlib import Path

import pytest

from agents.anyplot.policy import refusals


ROOT = Path(__file__).resolve().parents[3]
PROMPT = ROOT / "agents" / "anyplot" / "prompts" / "root.md"

FORMAL: dict[str, re.Pattern[str]] = {
    # German: the capitalised pronouns of `Sie`; "ihre" in lower case is "her" or "their".
    "de": re.compile(r"\b(?:Sie|Ihnen|Ihr|Ihre|Ihren|Ihrem|Ihrer|Ihres)\b"),
    "fr": re.compile(r"\b(?:vous|votre|vos)\b", re.IGNORECASE),
    # Spanish: only `usted`, since `su` and `sus` are also "its" and "their".
    "es": re.compile(r"\b(?:usted|ustedes)\b", re.IGNORECASE),
    "nl": re.compile(r"\b(?:u|uw)\b", re.IGNORECASE),
}
"""The words of the formal address, per language, that an informal text never holds."""
GERMAN_DU = re.compile(r"\b(?:du|dich|dir|dein\w*)\b", re.IGNORECASE)


def formal_words(text: str, lang: str) -> list[str]:
    """The words of the formal address in `text`, for a language that has one here; else none."""
    pattern = FORMAL.get(lang)
    return pattern.findall(text) if pattern else []


@pytest.mark.parametrize("lang", sorted(FORMAL))
def test_every_fixed_text_addresses_the_user_informally(lang: str) -> None:
    formal = {
        reason: words
        for reason, texts in refusals().items()
        if lang in texts and (words := formal_words(texts[lang], lang))
    }

    assert formal == {}


def test_the_german_texts_that_address_the_user_say_du() -> None:
    """At least the texts that speak to the user directly carry the informal pronoun, so the register is visible."""
    addressed = [texts["de"] for texts in refusals().values() if "de" in texts and GERMAN_DU.search(texts["de"])]

    assert len(addressed) >= 5


@pytest.mark.parametrize(
    ("text", "lang", "words"),
    [
        ("Aus Ihren Notizen habe ich den Titel übernommen.", "de", ["Ihren"]),
        ("Können Sie die Spalte umbenennen?", "de", ["Sie"]),
        ("Aus deinen Notizen habe ich den Titel übernommen; ihre Einheit ist kWh.", "de", []),
        ("Pouvez-vous confirmer vos données ?", "fr", ["vous", "vos"]),
        ("Kunt u uw gegevens bevestigen?", "nl", ["u", "uw"]),
        ("Pruébalo de nuevo, por favor.", "es", []),
        ("Could you confirm the data?", "en", []),
    ],
)
def test_the_check_tells_the_registers_apart(text: str, lang: str, words: list[str]) -> None:
    assert formal_words(text, lang) == words


def test_root_prompt_keeps_one_register() -> None:
    language = PROMPT.read_text(encoding="utf-8").split("## Language", 1)[1].split("\n## ", 1)[0]

    assert "Address the user informally" in language
    assert "German `du`" in language
    assert "never switch to the formal" in language
