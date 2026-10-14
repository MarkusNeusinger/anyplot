"""What text pasted into the data panel is, before any parser reads it: code, a formula, or neither.

The dataset route (`agents/main.py`, `upload_dataset`) asks `classify_paste` first,
because both kinds would otherwise take a wrong path: a snippet such as
`np.linspace(0, 10, 100)` parses as a one-row table, and the transcriber would compute
a formula's rows itself. Code answers `422 code` and a formula `422 formula`; the page
offers to move either to the chat, where the root runs code (`run_data_code`) or
computes the formula (`generate_data`). Only text the chat takes
(`schemas.MAX_MESSAGE_CHARS`, 2,000 characters) can move there; longer code is refused
all the same (it is never a table), and the page asks to shorten it.

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
from .generate import looks_like_formula


PasteKind = Literal["code", "formula"]
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


def classify_paste(text: str) -> PasteKind | None:
    """`code`, `formula` (only text the chat takes, `MAX_MESSAGE_CHARS`) or None for anything the parser should read."""
    if looks_like_code(text):
        return "code"
    if len(text) <= MAX_MESSAGE_CHARS and looks_like_formula(text):
        return "formula"
    return None
