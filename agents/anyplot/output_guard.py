"""What the root writes, checked before anyone reads it: the sanitiser and the off-topic rule.

`sanitize(text)` is the deterministic sanitiser of every root message and every
model-written line of the plot event (`agents/stream.py`): URLs (with protocol-relative
`//host` links), `data:`, `javascript:` and `mailto:` links, HTML tags (an unclosed one
too) and markdown images are removed, links keep their text, fenced (backtick or tilde)
and indented code blocks longer than 10 lines become `[code omitted]`, bare web
addresses, e-mail addresses and phone numbers are removed (`contact_filter`),
`[[spec:id]]` tokens stay only for the session's own spec, and the text is capped at
`MAX_MESSAGE_CHARS`. It is a backstop, not an HTML filter: the UI must render message
and plot text as plain text, never as HTML or unescaped markdown.

`off_topic_reply(text, lang)` is the output guard's rule. A reply that is long (more
than `MAX_REPLY_SENTENCES` sentences or list items, or more than
`MAX_UNCHECKED_REPLY_CHARS` characters) must tie at least a third of its sentences to
the plot, its data, its code or its files: a word from `PLOT_WORDS` (English, German,
French, Spanish and Italian), inline code, or `[code omitted]`. A reply that fails
(an email, a cover letter, an advertisement that got past the judge) becomes the fixed
`out_of_scope` refusal. A single plot word no longer clears a long text: a phishing
mail that mentions a "verification code" once is still off topic. The rule applies
only in the languages the word list covers (`PLOT_WORD_LANGS`); a reply in another
language keeps only the sanitiser and the length cap. The ScopeGuard plugin runs the
rule on the root's final reply before ADK stores it (`on_event_callback`), so a
refused reply never re-enters the judge's or the root's context.

No ADK import.
"""

import re

from .contact_filter import strip_contacts


MAX_MESSAGE_CHARS = 1_200
"""The longest root message the stream sends. root.md asks for two to five sentences (about 300
to 700 characters) or a short list; the plot event carries the changes and residual defects itself."""
MAX_CODE_LINES = 10
CODE_OMITTED = "[code omitted]"
MAX_REPLY_SENTENCES = 5
"""The upper end of root.md's "two to five sentences, or a short list" rule."""
MAX_UNCHECKED_REPLY_CHARS = 500
"""A reply of at most `MAX_REPLY_SENTENCES` sentences and at most this many characters is never checked."""
MIN_PLOT_SHARE_DENOMINATOR = 3
"""A checked reply ties at least one in three of its sentences to the plot."""
PLOT_WORD_LANGS: frozenset[str] = frozenset({"en", "de", "fr", "es", "it"})
"""The languages `PLOT_WORDS` covers; the off-topic rule applies only to them."""

PLOT_WORDS = re.compile(
    r"(?i)\b(?:"
    # English
    r"plot|chart|graph|diagram|figure|axis|axes|x-axis|y-axis|label|title|legend|colou?r|palette|marker|bar|"
    r"line|scatter|column|row|data|dataset|binding|role|spec|theme|render|version|code|tick|scale|grid|"
    r"series|value|font|export|download|style|file|script|terminal|python|pip|folder|image|png|svg|csv|pdf|"
    r"package|install|library|matplotlib|seaborn|plotly|bokeh|altair|plotnine|pandas|numpy|"
    # German
    r"diagramm|grafik|abbildung|achse|beschriftung|titel|legende|farbe|markierung|balken|linie|spalte|"
    r"zeile|daten|datensatz|zuordnung|rolle|darstellung|skala|raster|wert|schrift|stil|datei|skript|ordner|"
    r"bild|paket|installier|bibliothek"
    r")(?:s|es|e|en|n|er|ern|ed|d|ing|ting|ted|led|ling)?\b"
    r"|\b(?:"
    # French
    r"graphique|diagramme|tracé|axe|étiquette|titre|légende|couleur|marqueur|barre|ligne|nuage|colonne|"
    r"donnée|valeur|échelle|grille|police|thème|fichier|dossier|rendu|"
    # Spanish
    r"gráfico|diagrama|eje|etiqueta|título|leyenda|paleta|marcador|barra|línea|columna|fila|dato|"
    r"valor|escala|cuadrícula|fuente|tema|código|archivo|carpeta|imagen|imágenes|"
    # Italian
    r"grafico|grafici|diagramma|asse|assi|etichetta|etichette|titolo|titoli|colore|colori|tavolozza|"
    r"linea|linee|colonna|colonne|riga|righe|dati|valore|valori|griglia|carattere|codice|cartella|"
    r"immagine|immagini"
    r")(?:s|x|es)?\b"
)
"""Words any of which ties a sentence to the plot, its data, its code or its files, with their common
endings (`colors`, `labelled`, `Spalten`, `barres`, `colores`); a longer word that only starts with one
(`still`) does not count."""
_INLINE_CODE = re.compile(r"`[^`\n]+`")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+|\n+")
_WORD = re.compile(r"[^\W\d_]{2,}")

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


def sanitize(text: str, *, spec_id: str | None = None) -> str:
    """The deterministic output sanitiser for root messages."""

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
    text = strip_contacts(text)
    text = _SPEC_TOKEN.sub(spec_token, text)
    text = _BLANK_LINES.sub("\n\n", text).strip()
    if len(text) > MAX_MESSAGE_CHARS:
        text = text[: MAX_MESSAGE_CHARS - 1].rstrip() + "…"
    return text


def plain_line(text: str, *, spec_id: str | None = None) -> str:
    """A model-written note as one sanitised line: no code block, link target, URL, HTML or image."""
    return " ".join(sanitize(text, spec_id=spec_id).replace(CODE_OMITTED, " ").split())


def sentences(text: str) -> list[str]:
    """The sentences and list items of `text`: the pieces between sentence ends and line breaks that hold a word."""
    return [piece for piece in _SENTENCE_END.split(text) if _WORD.search(piece)]


def sentence_count(text: str) -> int:
    """How many sentences and list items `text` has."""
    return len(sentences(text))


def ties_to_plot(sentence: str) -> bool:
    """Whether a sentence names the plot, its data, its code or its files, or quotes code."""
    return bool(PLOT_WORDS.search(sentence) or _INLINE_CODE.search(sentence) or CODE_OMITTED in sentence)


def off_topic_reply(text: str, lang: str = "en") -> bool:
    """A long reply in a covered language that ties fewer than a third of its sentences to the plot."""
    if lang not in PLOT_WORD_LANGS:
        return False
    pieces = sentences(text)
    if len(pieces) <= MAX_REPLY_SENTENCES and len(text) <= MAX_UNCHECKED_REPLY_CHARS:
        return False
    tied = sum(1 for piece in pieces if ties_to_plot(piece))
    return tied * MIN_PLOT_SHARE_DENOMINATOR < len(pieces)
