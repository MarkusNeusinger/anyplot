"""What text pasted into the data panel is, before any parser reads it: code, a data request, a formula, or neither.

The dataset route (`agents/main.py`, `upload_dataset`) asks `classify_paste` first,
because these kinds would otherwise take a wrong path: a snippet such as
`np.linspace(0, 10, 100)` parses as a one-row table, the transcriber would compute
a formula's rows itself, and a request for data ("Beispieldaten") holds no table for it
to read. Code answers `422 code`, a data request `422 data_request` and a formula
`422 formula`; the page offers to move code or a formula to the chat, and sends a data
request there itself, where the root runs code (`run_data_code`), generates example data
with code it writes (`run_data_code` with `source_language` `example`) or computes the
formula (`generate_data`). Only text the chat takes (`schemas.MAX_MESSAGE_CHARS`, 2,000
characters) can move there; longer code is refused all the same (it is never a table),
and the page asks to shorten it.

**A data request** asks for data instead of holding it: example, sample, test or random
data ("Beispieldaten", "generiere Zufallszahlen mit Kategorien", "example data with 3
categories"). `looks_like_data_request` reads one line of at most `MAX_REQUEST_WORDS`
words for a phrase of `_REQUEST` (German, English, French, Spanish, Italian, Portuguese,
Dutch and Polish) and holding fewer than `generate.MIN_DATA_VALUES` values of its own
(`generate.stated_values`: the counts a request names, "3 Kategorien und 20 Zeilen", stay
below it; "Beispieldaten: Hund 7, Katze 3, Vogel 4" is data for the transcriber). A
request in other words or another language reaches the transcriber, whose answer says so
(`TranscribedTable.asks_for_data`).

**Code** is told from data line by line. A line is code when it has the shape of a
statement no table cell has: an import (`import x`, `from x import y`, `library(x)`,
`require(x)`), a definition (`def f(`, `function f(`, `const|let|var x =`), an R
assignment (`x <- ...`), a loop header (`for (`, `for x in ...:`, `while (`), a call of
a known data module at the start of the line or on the right of an assignment
(`np.`, `pd.`, `Math.`, `random.`, `math.`, `scipy.`, `stats.`, `console.log(`,
`print(`, `set.seed(`, `rnorm(`, `seq(`, `runif(`, `data.frame(`), or an arrow function
(`=>`). Text is code when at least one line is, and code-shaped lines (those, plus
comments, braces, `return`, and lines ending in `;`, `{` or `:`) are at least half of the
first `SCAN_LINES` non-empty lines, so a table with a stray `print(...)` cell stays a
table. A formula (`y = sin(x)`, `y = x**2 from -3 to 3`) has none of these shapes and
stays the formula guard's (`generate.looks_like_formula`).

No ADK import.
"""

import re
from typing import Literal

from ..schemas import MAX_MESSAGE_CHARS
from .generate import MIN_DATA_VALUES, looks_like_formula, stated_values


PasteKind = Literal["code", "data_request", "formula"]
SCAN_LINES = 200
"""Non-empty lines read from the top; a pasted table is decided long before."""
MIN_CODE_SHARE = 0.5
_DATA_MODULES = r"(?:np|numpy|pd|pandas|math|Math|random|scipy|stats|st|rng|torch|tf|sp|R)"
MAX_LINE_SCAN = 400
"""Characters of a stripped line the patterns read: with the line stripped and capped, and no two quantifiers
competing for the same spaces before an anchor, matching stays linear in the line (CodeQL, #12172 review)."""
_STRONG = re.compile(
    r"^(?:"
    r"import\s+[A-Za-z_][\w.]*(?:\s+as\s+\w+)?(?:\s*,\s*[A-Za-z_][\w.]*)*;?$"
    r"|from\s+[A-Za-z_][\w.]*\s+import\s+\S"
    r"|(?:library|require|suppressPackageStartupMessages)\s*\(\s*['\"]?\w+['\"]?\s*\)"
    r"|def\s+[A-Za-z_]\w*\s*\("
    r"|(?:async\s+)?function\s*\*?\s*[A-Za-z_$]?[\w$]*\s*\("
    r"|(?:const|let|var)\s+[A-Za-z_$][\w$]*\s*="
    r"|[A-Za-z_.][\w.]*(?:\[[^\]]*\])?\s*<-\s*\S"
    r"|for\s*\(|while\s*\(|for\s+[A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*\s+in[ \t]+\S.*:$"
    r"|(?:print|console\.log|set\.seed|cat|plot|hist|lines)\s*\("
    rf"|{_DATA_MODULES}\.[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*\s*\("
    rf"|[A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*\s*=\s*(?:{_DATA_MODULES}\.[A-Za-z_][\w.]*\s*\(|\[.+\bfor\b.+\bin\b.+\])"
    r"|[A-Za-z_]\w*\s*=\s*(?:rnorm|runif|rbinom|rpois|seq|rep|c|data\.frame|tibble|cumsum|sapply|lapply)\s*\("
    r")"
)
"""A line no table has: an import, a definition, an assignment from a data module or an R function, a loop."""
_ARROW = re.compile(r"\)[ \t]*=>|\b[A-Za-z_$][\w$]*[ \t]*=>")
_SHAPED = re.compile(
    r"^(?:#|//|/\*|\*|[{}\])]+;?$|return\b|else\b|elif\b|if\s*\(|if[ \t]+\S.*:$|end$)"
    r"|[;{:]$"
)
"""A line code has as well, which alone proves nothing: a comment, a brace, `return`, a line ending in `;`, `{`, `:`."""

MAX_REQUEST_WORDS = 30
"""The longest line the data-request guard reads, in words; a longer one is prose for the transcriber, whose answer
says whether it asks for data."""
_REQUEST = re.compile(
    r"(?i)\b(?:"
    # German compounds: Beispieldaten, Test-Daten, Zufallszahlen, Dummywerte, Beispieldatensatz
    r"(?:beispiel|test|dummy|demo|zufalls|fantasie|phantasie|muster|übungs|uebungs|fake|probe)[- ]?"
    r"(?:daten(?:satz|sätze|saetze)?|werte|zahlen|tabelle)"
    # zufällige Daten, erfundene Werte, beliebige Zahlen
    r"|(?:zufällig|zufaellig|erfunden|ausgedacht|künstlich|kuenstlich|synthetisch|beliebig|irgendwelch)\w{0,3}"
    r"\s+(?:daten|werte|zahlen)"
    # generiere Daten, erstelle mir eine Tabelle, denk dir ein paar Werte aus
    r"|(?:generier|erzeug|erstell|mach|gib|denk\s+dir)\w{0,3}"
    r"\s+(?:(?:mir|uns|bitte|mal|ein|eine|einen|einige|paar|etwas|irgendwelche)\s+){0,3}(?:daten|werte|zahlen|tabelle)"
    # example data, random numbers, sample sales data, made-up values
    r"|(?:example|sample|test|dummy|fake|mock|demo|toy|synthetic|random|made[- ]up|invented|placeholder|fictional"
    r"|fictitious|arbitrary)\s+(?:\w+\s+)?(?:data(?:set)?|values|numbers|records|table)"
    # generate some data, make me a table, give me some numbers
    r"|(?:generate|create|make|give|invent|simulate)"
    r"\s+(?:(?:me|us|up|some|a|an|few|random|fake|example|sample|test)\s+){0,3}(?:data(?:set)?|values|numbers|table)"
    # French, Spanish and Portuguese, Italian
    r"|(?:données|donnees|valeurs|nombres|chiffres)\s+(?:d['’]exemple|de\s+test|aléatoires|aleatoires|fictives|factices"
    r"|synthétiques|synthetiques)"
    r"|(?:exemple|jeu)\s+de\s+(?:données|donnees)"
    r"|(?:datos|dados|valores|números|numeros)\s+(?:de\s+(?:ejemplo|exemplo|prueba|teste)|aleatorios|aleatórios"
    r"|ficticios|fictícios|sintéticos|sinteticos)"
    r"|(?:dati|valori|numeri)\s+(?:di\s+(?:esempio|prova)|casuali|fittizi|sintetici)"
    # Dutch, Polish
    r"|(?:voorbeeld|test|willekeurige|nep)\s*(?:data|gegevens|getallen|waarden)"
    r"|(?:przykładowe|przykladowe|testowe|losowe)\s+(?:dane|liczby|wartości|wartosci)"
    r")\b"
)
"""A phrase that asks for data to be made up: every alternative starts at a fixed word, and its gaps are bounded."""


def looks_like_code(text: str) -> bool:
    """Whether pasted text is a program (Python, JavaScript, R, ...) rather than a table or a formula."""
    lines = [line.strip()[:MAX_LINE_SCAN] for line in text.splitlines() if line.strip()][:SCAN_LINES]
    if not lines:
        return False
    strong = sum(1 for line in lines if _STRONG.search(line) or _ARROW.search(line))
    if not strong:
        return False
    shaped = sum(1 for line in lines if _STRONG.search(line) or _ARROW.search(line) or _SHAPED.search(line))
    return shaped / len(lines) >= MIN_CODE_SHARE


def looks_like_data_request(text: str) -> bool:
    """Whether pasted text asks for data instead of holding it ("Beispieldaten", "random numbers with 3 categories").

    One line of at most `MAX_REQUEST_WORDS` words that the chat takes (`MAX_MESSAGE_CHARS`), no
    JSON, with a phrase of `_REQUEST` and fewer than `MIN_DATA_VALUES` values of its own. A
    table, even one under the header `Testdaten`, has several lines or its values, and
    stays the parser's.
    """
    stripped = text.strip()
    if not stripped or len(stripped) > MAX_MESSAGE_CHARS or len(stripped.splitlines()) > 1:
        return False
    if stripped.startswith(("{", "[")) or len(stripped.split()) > MAX_REQUEST_WORDS:
        return False
    return _REQUEST.search(stripped) is not None and stated_values(stripped) < MIN_DATA_VALUES


def request_for_chat(text: str, *, without_table: bool) -> bool:
    """Whether text the transcriber says asks for data (`TranscribedTable.asks_for_data`) goes to the chat as a data
    request: the chat takes it (`MAX_MESSAGE_CHARS`), and the transcriber found no table in it (`without_table`, the
    rubric's one `text` column) or it holds fewer than `MIN_DATA_VALUES` values of its own. A request that names its
    sizes ("3 Kategorien, 4 Regionen und 12 Monate") goes, while a table in words that the model also read as one is
    never sent away on a misreading."""
    stripped = text.strip()
    if not 0 < len(stripped) <= MAX_MESSAGE_CHARS:
        return False
    return without_table or stated_values(stripped) < MIN_DATA_VALUES


def classify_paste(text: str) -> PasteKind | None:
    """`code`, `data_request` or `formula` (only text the chat takes, `MAX_MESSAGE_CHARS`), or None for anything the
    parser should read. A data request that names a curve ("Beispieldaten für eine Gaußkurve") is a data request: the
    page sends it to the chat by itself, where the root picks the tool."""
    if looks_like_code(text):
        return "code"
    if looks_like_data_request(text):
        return "data_request"
    if len(text) <= MAX_MESSAGE_CHARS and looks_like_formula(text):
        return "formula"
    return None
