"""A deterministic, offline guess of the language a reply is written in, for the reply-language check.

The root writes every reply in the session language (`language.py`), and the prompt says
so in three places; a live test of 2026-10-14 still saw English replies in a German
session (#12176). The check that follows each final reply (`plugins/reply_language.py`)
needs the reply's language without a model call: the scope judge names the language of
the user's message, never of the root's reply, so its `lang` field is no help here, and
a judge call per reply would add a second model call (about a second, and its tokens) to
every turn. No language-identification package is in the image either
(`langdetect`, `lingua` and `fasttext` would add 10 to 100 MB of models and a dependency
for a dozen languages).

So `detect` is a small classifier over the languages the session language table knows
(`language.ENGLISH_NAMES`): the script decides Russian (Cyrillic), Chinese (Han without
kana) and Japanese (kana), Vietnamese letters (`ơ`, `ư`, `đ`, the dotted vowels) together
with at least two Vietnamese function words decide Vietnamese, and for the Latin-script languages a count of frequent function words
(`STOPWORDS`, words such as `the`, `und`, `est`, `para`, `het`, `się`) picks one. It
returns None whenever it is not sure: fewer than `MIN_WORDS` words, fewer than
`MIN_HITS` function words of the leader, a runner-up within half of the leader, or a
leader whose words are under `MIN_SHARE` of the text. Text in code fences, backticks and
double or single quotes (column names, category values, code), and everything after an
unclosed backtick, is left out before counting, since the
user's German column names may stand in an English sentence and say nothing about it.

The check acts only on a confident mismatch, so an unsure guess costs nothing; a wrong
"sure" guess costs one re-ask, which is asked to keep the reply as it is. No package
import: it is pure Python and costs about 50 microseconds for a five-sentence reply.
"""

import re
import unicodedata

from .language import canonical


MIN_WORDS = 6
MIN_HITS = 3
MIN_SHARE = 0.12
RUNNER_UP_RATIO = 0.5
"""The runner-up's function words must be at most half of the leader's for a sure guess."""

STOPWORDS: dict[str, frozenset[str]] = {
    "en": frozenset(
        (
            *("the", "and", "of", "to", "that", "this", "with", "for", "it", "you", "your", "on", "are"),
            *("have", "has", "which", "can", "not", "or", "from", "these", "there", "what", "each", "by"),
            *("its", "they", "if", "but", "into", "would", "should", "is", "be", "were", "one", "shows"),
        )
    ),
    "de": frozenset(
        (
            *("der", "die", "das", "und", "ist", "sind", "nicht", "mit", "für", "auf", "den", "dem", "des"),
            *("ein", "eine", "einen", "einer", "zu", "von", "im", "sich", "auch", "wie", "oder", "aber"),
            *("wird", "werden", "ich", "du", "bei", "nach", "aus", "hat", "haben", "kann", "diese", "dieser"),
            *("zeigt", "jeweils", "jede", "jeder", "noch", "nur", "möchtest", "sie"),
        )
    ),
    "fr": frozenset(
        (
            *("le", "les", "des", "et", "est", "sont", "une", "du", "pour", "avec", "dans", "qui", "pas"),
            *("ne", "sur", "au", "aux", "ce", "cette", "ces", "il", "elle", "vous", "votre", "nous", "mais"),
            *("ou", "par", "être", "été", "chaque", "aussi", "peut", "voulez", "montre"),
        )
    ),
    "es": frozenset(
        (
            *("el", "los", "las", "y", "es", "son", "una", "del", "para", "con", "por", "que", "se", "su"),
            *("sus", "al", "como", "más", "pero", "este", "esta", "estos", "hay", "está", "puede", "usted"),
            *("cada", "también", "muestra", "quieres"),
        )
    ),
    "it": frozenset(
        (
            *("il", "gli", "della", "delle", "dei", "degli", "e", "è", "sono", "per", "che", "non", "nel"),
            *("nella", "alla", "questo", "questa", "ogni", "anche", "più", "ma", "ha", "hanno", "puoi"),
            *("mostra", "vuoi", "colonna", "colonne"),
        )
    ),
    "pt": frozenset(
        (
            *("o", "os", "as", "é", "são", "uma", "do", "da", "dos", "das", "com", "não", "no", "na"),
            *("nos", "em", "ao", "seu", "sua", "também", "cada", "mais", "mas", "pode", "você", "mostra"),
            *("quer", "coluna", "colunas"),
        )
    ),
    "nl": frozenset(
        (
            *("het", "een", "en", "zijn", "van", "voor", "met", "op", "dat", "niet", "ook", "als", "aan"),
            *("bij", "naar", "er", "je", "u", "uw", "wordt", "worden", "kan", "deze", "dit", "elke", "maar"),
            *("om", "tot", "toont", "wil", "kolom", "kolommen"),
        )
    ),
    "pl": frozenset(
        (
            *("się", "nie", "jest", "są", "że", "dla", "przez", "oraz", "lub", "czy", "który", "która"),
            *("które", "jako", "tylko", "może", "w", "z", "na", "do", "od", "jak", "po", "ale", "ten", "ta"),
            *("kolumna", "kolumny", "chcesz", "pokazuje"),
        )
    ),
    "vi": frozenset(
        (
            *("của", "và", "là", "các", "những", "được", "cho", "với", "trong", "này", "có", "không"),
            *("một", "cột", "dữ", "liệu", "bạn", "từ", "theo", "mỗi"),
        )
    ),
}
"""Frequent function words per Latin-script language, lower case. A word may sit in two lists (`is` is
English and Dutch): the runner-up rule keeps such overlaps from deciding alone."""

DETECTABLE: frozenset[str] = frozenset((*STOPWORDS, "ru", "zh", "ja"))
"""The languages `detect` can name: the session language table's codes (`language.ENGLISH_NAMES`)."""

_QUOTED = re.compile(
    r"```.*?```|`[^`]*`|\"[^\"]*\"|„[^“”]*[“”]|“[^”]*”|«[^»]*»|‘[^’]*’|(?<!\w)'[^'\n]*'(?!\w)", re.DOTALL
)
"""Quoted text: code fences and spans, double quotes in their typographic forms, and single quotes that are no
apostrophe (one inside a word, `don't`, `l'axe`, starts nothing)."""
_WORD = re.compile(r"[^\W\d_]+")
_VIETNAMESE = frozenset("ơưđăạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ")
MIN_VIETNAMESE_LETTERS = 3
MIN_VIETNAMESE_WORDS = 2


def _scripts(text: str) -> tuple[int, int, int, int]:
    """The letters of `text` by script: (all, Cyrillic, Han, kana)."""
    letters = cyrillic = han = kana = 0
    for char in text:
        if not char.isalpha():
            continue
        letters += 1
        name = unicodedata.name(char, "")
        if name.startswith("CYRILLIC"):
            cyrillic += 1
        elif name.startswith("CJK UNIFIED"):
            han += 1
        elif name.startswith(("HIRAGANA", "KATAKANA")):
            kana += 1
    return letters, cyrillic, han, kana


def detect(text: str) -> str | None:
    """The language `text` is written in as a code of `DETECTABLE`, or None when the guess is not sure."""
    body = _QUOTED.sub(" ", text)
    if "`" in body:  # an unclosed fence or span: what follows is code or a name, never the reply's language
        body = body[: body.index("`")]
    letters, cyrillic, han, kana = _scripts(body)
    if not letters:
        return None
    if kana and (kana + han) / letters > 0.3:
        return "ja"
    if han / letters > 0.3:
        return "zh"
    if cyrillic / letters > 0.5:
        return "ru"
    lowered = body.lower()
    words = _WORD.findall(lowered)
    if sum(char in _VIETNAMESE for char in lowered) >= MIN_VIETNAMESE_LETTERS:
        # The letters alone also occur in a Vietnamese name inside another language's reply.
        if sum(word in STOPWORDS["vi"] for word in words) >= MIN_VIETNAMESE_WORDS:
            return "vi"
    if len(words) < MIN_WORDS:
        return None
    hits = sorted(((sum(word in stop for word in words), code) for code, stop in STOPWORDS.items()), reverse=True)
    (best, code), (second, _) = hits[0], hits[1]
    if best < MIN_HITS or best / len(words) < MIN_SHARE or second > best * RUNNER_UP_RATIO:
        return None
    return code


def expected_code(session_language: str) -> str | None:
    """The `DETECTABLE` code of a session language (`de`, `Deutsch`, `German`), None for one `detect` cannot name."""
    code = canonical(session_language)
    return code if code in DETECTABLE else None


def mismatch(reply: str, session_language: str) -> str | None:
    """The language the reply is surely written in when it is not the session language; else None."""
    expected = expected_code(session_language)
    if expected is None:
        return None
    found = detect(reply)
    return found if found is not None and found != expected else None
