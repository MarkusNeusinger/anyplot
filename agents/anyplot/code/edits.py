"""The edit applier: an `AdaptPlan` applied to the working form, or the reasons it cannot be.

Edits apply in order, each to the text the previous ones produced. An edit's `find`
must match exactly once in that text and may not overlap a protected region:

* the `THEME = os.getenv("ANYPLOT_THEME", ...)` assignment,
* every theme token: a module-level assignment that picks a fixed value per theme
  (`PAGE_BG`, `ELEVATED_BG`, `INK*`, `GRID`, `BRAND`, ...; see `regions.py` for the
  exact rule, which leaves a data-dependent `x = INK if THEME == "dark" else ...` to
  the adapter),
* the placeholder line `df = load_user_data()` once it is present, including one an
  earlier edit of the same plan introduced,
* the final savefig statement.

**Matching** goes from strict to tolerant, Aider style, and never fuzzy: the first
tier that finds `find` at all decides, and more than one match there is a failure, so
a looser tier never picks among the candidates of a stricter one.

1. `exact`: `find` as a substring (overlapping occurrences count, so `"aa"` in
   `"aaa"` is two).
2. `trailing_whitespace`: spaces and tabs before each line break ignored on both
   sides, and `\\r\\n` or `\\r` read as `\\n`; a `find` may still start or end inside
   a line.
3. `whitespace`: whole lines whose words agree once indentation and runs of blanks
   outside string literals are ignored. A literal's text must agree exactly, so
   `"North  America"` never matches `"North America"`, and a line that starts inside a
   multi-line literal is never matched this way. The replacement is re-indented by
   the one indentation the code has over `find` (or `find` over the code); when the
   lines do not share one such shift, the tier finds nothing, because Python's
   indentation is meaning.

A `find` that matches nothing now but exactly once in the code before the plan, in
any tier, failed because an earlier edit of the same plan changed that code
(`stale_match`), and its repair line says so.

`AppliedPlan.tolerant` names the tier of every edit a tolerant tier applied, so the
attribution log shows how often they help.

A protected region covers the whole lines of its statement, so an edit that only
appends a comment to such a line is refused too; an edit may end right before one or
start right after one. The `IMPRINT` palette list is not protected: the adapter may
extend it, and the ADAPTATION validator checks that the existing entries keep their
order. A failing edit is skipped and the rest still run, so one round reports every
problem; the plan as a whole then yields no code. `full_code` replaces everything; the
caller decides whether a full file is allowed (from attempt 2 on), the applier only
applies it. After either kind of plan, `protected_drift` compares the result with the
base: the protected statements must keep their meaning (their syntax tree, so a
re-stated token with the same value in other quotes, spacing or comment passes), and
THEME and the theme tokens may not be bound again anywhere (a later `PAGE_BG = ...`
passes the overlap check above but would recolour the plot).

**Restoring drift.** A plan refused only because it changed protected statements
(`drift:theme`, `drift:theme_token`, `drift:savefig`, never `drift:rebind`) keeps its
result in `AppliedPlan.drifted`. `restore_protected` puts the base's text of each
changed statement back over the plan's version of it, by name (the module-level
assignment of THEME or of the token, the final module-level savefig statement). It
restores nothing when a protected statement is gone, shares its lines with another
statement in the plan's code or the base, or the result does not parse or still drifts. The pipeline calls it only
when the round's check retry is spent (owner decision, 2026-10-16), so the adapter
first gets its guided retry.

Failure lines are repair feedback (`Line`): one line each, at most `MAX_LINE_CHARS`
characters, quoting at most `MAX_QUOTE_CHARS` characters of code. Next to them,
`AppliedPlan.kinds` names each failure by a fixed, content-free kind (`FAILURE_KINDS`)
for the attribution log, which never sees the lines because they quote code.

**Languages** (2026-10-29). Matching, the overlap check, drift and restoring are one
language-neutral core; what depends on the language is a `Dialect`, picked by the
library (`dialect_for`). Python's reads the code with `ast` and the regions of
`regions.py`, compares meanings as `ast.dump`, and its literals are `'`, `"` and their
triple forms, each ending with its line unless a backslash continues it. R's
(`ggplot2`) reads it with tree-sitter and `profiles/r/regions.py`, compares meanings as
the token stream with string values decoded (so `'a'` and `"a"` agree, a comment does
not count), its placeholder is `df <- load_user_data()`, its save `ggsave`, and its
literals are `'`, `"` and backtick names, which may span lines, and raw strings
`r"(...)"`. Julia's (`makie`, J2a of 2026-10-29) reads it with tree-sitter and
`profiles/julia/regions.py`, compares meanings as R's does (the token stream with string
values decoded, comments left out, so `const THEME = ...` and `THEME = ...` differ), its
placeholder is `df = load_user_data()` as in Python, its save `save`, and its literals are
`"`, its triple-quoted strings and backtick commands, which may span lines. JavaScript's
(Chart.js, D3, ECharts, Highcharts, and MUI X as TSX; JS-3 of 2026-10-30) reads the code
with tree-sitter and `profiles/javascript/regions.py`: its protected statements are the
token lines that read `window.ANYPLOT_TOKENS`, `_THEME` and `_SIZE`, the placeholder
`const data = loadUserData();` and the `//# anyplot-orientation` directive, which is a
comment and stands as the orientation it picks in the meaning the drift check compares
(the protected `savefig` region: it fixes what the render writes); it has no THEME
statement, so no name but the tokens' counts as a rebind, and only top-level bindings
count (a callback's parameter `t` shadows the token `t` and leaves it alone). Its literals
are `'` and `"`, which end with their line, and templates, which may span lines; `//` and
`/* */` are comments, and a `#` (a CSS colour in a string, a private field) is text. The
Python, R and Julia behaviour is byte for byte what it was (their tests are unchanged).
"""

import ast
import dataclasses
import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal, Protocol

from ..schemas import MAX_FEEDBACK, MAX_LINE_CHARS, AdaptPlan
from . import regions as python_regions
from .profiles.javascript import regions as javascript_regions
from .profiles.julia import regions as julia_regions
from .profiles.r import regions as r_regions
from .regions import PLACEHOLDER, PLACEHOLDER_FUNC, THEME_NAME, SourceIndex, find_regions
from .treesitter import (
    COMMENTS,
    Grammar,
    Source,
    jl_bindings,
    jl_string,
    js_bindings,
    js_string,
    r_assignment,
    r_bindings,
    r_string,
    r_string_value,
    statements,
    syntax_problems,
    walk,
)


MAX_QUOTE_CHARS = 80
MAX_COUNTED_MATCHES = 1000
MAX_NEW_LITERAL_CHARS = 2_000
"""New string-literal text one plan may add (design doc, "Adapt and validate")."""
MAX_CHANGE_LITERAL_CHARS = 300
"""New string-literal text one plan may add on top of a previous version (a change turn): a new title,
a subtitle or a few labels fit, a paragraph of text does not. The first adaptation of the catalogue
code renames many titles and labels at once and keeps `MAX_NEW_LITERAL_CHARS`, which also bounds the
new literals of every version against the catalogue code, so text cannot pile up across turns."""
REWRITE_LITERAL_FACTOR = 1.5
"""On a change that rewrites the plot's text in another language, every character of string-literal text
the plan drops from the base raises the change's budget by this much (up to `MAX_NEW_LITERAL_CHARS`): a
translation may run longer than its source, but the budget grows only by the text the plan replaces, so
switching the language does not let a paragraph of new text in with it."""

# The placeholder statement as a line of text, so one that an earlier edit of the same
# plan introduced is protected before the code parses again.
_PLACEHOLDER_LINE = re.compile(
    rf"^[ \t]*df[ \t]*=[ \t]*{PLACEHOLDER_FUNC}\(\)[ \t]*(?:#[^\r\n]*)?(?:\r\n|\r|\n|$)", re.M
)
_R_PLACEHOLDER_LINE = re.compile(
    rf"^[ \t]*df[ \t]*(?:<-|=)[ \t]*{r_regions.PLACEHOLDER_FUNC}\(\)[ \t]*(?:#[^\r\n]*)?(?:\r\n|\r|\n|$)", re.M
)
_NEWLINE = re.compile(r"\r\n|\r|\n")
_LINE_END_BLANKS = " \t"
_R_RAW_OPENER = re.compile(r"[rR](['\"])(-*)([(\[{])")
_RAW_CLOSERS = {"(": ")", "[": "]", "{": "}"}

_KIND_NAMES = {
    "theme": "THEME assignment",
    "theme_token": "theme token",
    "placeholder": "placeholder line",
    "savefig": "final {save} statement",
}
FAILURE_KINDS: frozenset[str] = frozenset(
    {
        "zero_match",
        "stale_match",
        "multi_match",
        *(f"protected:{kind}" for kind in _KIND_NAMES),
        "drift:theme",
        "drift:theme_token",
        "drift:savefig",
        "drift:rebind",
        "working_unparseable",
    }
)
"""The content-free kind of every failure line: no match, a match only in the code before an
earlier edit of the same plan changed it (`stale_match`), several matches, an overlap with a
protected region (by region kind), a protected statement changed or a theme name bound again
after the plan applied (`drift:*`), or a working form that does not parse."""

MatchTier = Literal["exact", "trailing_whitespace", "whitespace"]
TOLERANT_TIERS: tuple[MatchTier, ...] = ("trailing_whitespace", "whitespace")
"""The tiers after `exact`, in the order they are tried (the module docstring, "Matching")."""


# --- dialects --------------------------------------------------------------------------------


class SpanLike(Protocol):
    """`regions.Span` or `treesitter.Span`: the two have the same fields."""

    @property
    def first_line(self) -> int: ...
    @property
    def last_line(self) -> int: ...
    @property
    def start(self) -> int: ...
    @property
    def end(self) -> int: ...
    def overlaps(self, start: int, end: int) -> bool: ...


class ProtectedRegion(Protocol):
    """A protected statement of either language: `regions.Region` or `profiles.r.regions.Region`."""

    @property
    def kind(self) -> str: ...
    @property
    def name(self) -> str: ...
    @property
    def span(self) -> SpanLike: ...


@dataclass(frozen=True, slots=True)
class CodeView:
    """What the core reads from a parsed source: the protected statements, bindings and top-level assignments.

    `theme` and `save` are the whole lines of the THEME statement and of the protected
    save, `tokens` each theme token's name and lines, `regions` every protected region
    (placeholders included), `bindings` counts how often the code binds each name, and
    `assignments` the lines of each top-level assignment by the names it binds (joined
    as `Region.name` joins them).
    """

    theme: SpanLike | None
    tokens: tuple[tuple[str, SpanLike], ...]
    save: SpanLike | None
    regions: tuple[ProtectedRegion, ...]
    bindings: Callable[[set[str]], Counter[str]]
    assignments: Callable[[], dict[str, list[SpanLike]]]


@dataclass(frozen=True, slots=True)
class LiteralSyntax:
    """How the whitespace tier finds string literals and comments in a line (`_line_words`).

    `comment` opens a comment to the end of the line, `block_comment` is the opener and
    closer of one that may span lines (JavaScript's `/* */`), and `spans_lines` names the
    quotes whose literal may span lines when `multiline` is off (JavaScript's template).
    """

    quotes: str
    triple: bool
    multiline: bool
    raw: bool
    comment: str = "#"
    block_comment: tuple[str, str] | None = None
    spans_lines: str = ""


@dataclass(frozen=True, slots=True)
class Dialect:
    """What the edit core needs from a language (module docstring, "Languages").

    `read` parses the code and raises `SyntaxError` (with `lineno`) when it does not;
    `meaning` gives a protected statement's text a form that ignores spacing, quotes and
    comments; `single_statement` tells whether whole lines hold exactly one statement;
    `string_literals` counts the string values of a parsed source. The labels word the
    failure lines for a language whose protected statements differ from Python's (empty:
    Python's wording with `save_word`), and `theme_name` is the name whose second binding
    is a drift (None for JavaScript, whose theme lives in the token lines).
    """

    placeholder: str
    placeholder_line: re.Pattern[str]
    save_word: str
    literals: LiteralSyntax
    read: Callable[[str], CodeView]
    meaning: Callable[[str], str]
    single_statement: Callable[[str], bool]
    string_literals: Callable[[str], Counter[str]]
    save_label: str = ""
    """The protected save as a failure line names it; empty: `final <save_word> statement`."""
    keep_label: str = ""
    """What stays unchanged, as an overlap's failure line lists it; empty: Python's list."""
    reminder_label: str = ""
    """What the drift reminder asks to keep; empty: Python's list."""
    theme_name: str | None = THEME_NAME

    def saved(self) -> str:
        return self.save_label or f"final {self.save_word} statement"


def _python_read(library: str) -> Callable[[str], CodeView]:
    def read(code: str) -> CodeView:
        tree = ast.parse(code)
        found = find_regions(code, tree, library=library)
        save = found.savefig.statement if found.savefig is not None else None
        index = SourceIndex(code)

        def assignments() -> dict[str, list[SpanLike]]:
            assigned: dict[str, list[SpanLike]] = {}
            for stmt in tree.body:
                names = _module_assignment(stmt)
                if names is not None:
                    assigned.setdefault(names, []).append(index.lines_span(stmt))
            return assigned

        return CodeView(
            theme=found.theme.span if found.theme is not None else None,
            tokens=tuple((region.name, region.span) for region in found.theme_tokens),
            save=save,
            regions=found.protected,
            bindings=lambda names: _bindings(tree, names),
            assignments=assignments,
        )

    return read


def _python_meaning(text: str) -> str:
    try:
        return ast.dump(ast.parse(text))
    except SyntaxError:
        return text.strip()


def _python_single_statement(text: str) -> bool:
    """Whether whole lines hold exactly one statement, so replacing them drops nothing else."""
    try:
        return len(ast.parse(text).body) == 1
    except SyntaxError:
        return False


def _python_string_literals(code: str) -> Counter[str]:
    return _string_literals(ast.parse(code))


def _tree_source(code: str, grammar: Grammar) -> Source:
    """The code parsed as `grammar`; `SyntaxError` with the first problem's line when tree-sitter cannot read it."""
    source = Source(code, grammar)
    problems = syntax_problems(source.tree, limit=1)
    if problems:
        error = SyntaxError(problems[0].message())
        error.lineno = problems[0].line
        raise error
    return source


def _r_read(code: str) -> CodeView:
    source = _tree_source(code, "r")
    found = r_regions.find_regions(source)
    save = found.save.statement if found.save is not None else None

    def bindings(names: set[str]) -> Counter[str]:
        return Counter(name for name, _ in r_bindings(source, source.root) if name in names)

    def assignments() -> dict[str, list[SpanLike]]:
        assigned: dict[str, list[SpanLike]] = {}
        for node in statements(source.root):
            assignment = r_assignment(source, node)
            if assignment is not None and assignment.name is not None and assignment.target.type == "identifier":
                assigned.setdefault(assignment.name, []).append(source.lines_span(node))
        return assigned

    return CodeView(
        theme=found.theme.span if found.theme is not None else None,
        tokens=tuple((region.name, region.span) for region in found.theme_tokens),
        save=save,
        regions=found.protected,
        bindings=bindings,
        assignments=assignments,
    )


def _r_meaning(text: str) -> str:
    """The token stream of an R statement: leaf tokens with string values decoded, comments left out."""
    source = Source(text, "r")
    if syntax_problems(source.tree, limit=1):
        return text.strip()
    tokens: list[str] = []
    stack = [source.root]
    while stack:
        node = stack.pop()
        if node.type == "comment":
            continue
        if node.type == "string":
            tokens.append(f"string:{r_string_value(source, node)!r}")
            continue
        if not node.children:
            tokens.append(f"{node.type}:{source.text(node)}")
            continue
        stack.extend(reversed(node.children))
    return "\x00".join(tokens)


def _r_single_statement(text: str) -> bool:
    source = Source(text, "r")
    return not syntax_problems(source.tree, limit=1) and len(statements(source.root)) == 1


def _r_string_literals(code: str) -> Counter[str]:
    source = _tree_source(code, "r")
    counts: Counter[str] = Counter()
    for node in walk(source.root):
        if node.type == "string":
            value = r_string(source.text(node))
            if value is not None:
                counts[value] += 1
    return counts


def _julia_read(code: str) -> CodeView:
    source = _tree_source(code, "julia")
    found = julia_regions.find_regions(source)
    save = found.save.statement if found.save is not None else None

    def bindings(names: set[str]) -> Counter[str]:
        return Counter(name for name, _ in jl_bindings(source, source.root) if name in names)

    def assignments() -> dict[str, list[SpanLike]]:
        assigned: dict[str, list[SpanLike]] = {}
        for node in statements(source.root):
            top = julia_regions.top_assignment(source, node)
            if top is not None:
                assigned.setdefault(top[1], []).append(source.lines_span(node))
        return assigned

    return CodeView(
        theme=found.theme.span if found.theme is not None else None,
        tokens=tuple((region.name, region.span) for region in found.theme_tokens),
        save=save,
        regions=found.protected,
        bindings=bindings,
        assignments=assignments,
    )


def _julia_meaning(text: str) -> str:
    """The token stream of a Julia statement: leaf tokens with plain string values decoded, comments left out."""
    source = Source(text, "julia")
    if syntax_problems(source.tree, limit=1):
        return text.strip()
    tokens: list[str] = []
    stack = [source.root]
    while stack:
        node = stack.pop()
        if node.type in COMMENTS:
            continue
        if node.type == "string_literal":
            value = jl_string(source, node)
            if value is not None:
                tokens.append(f"string:{value!r}")
                continue
        if not node.children:
            tokens.append(f"{node.type}:{source.text(node)}")
            continue
        stack.extend(reversed(node.children))
    return "\x00".join(tokens)


def _julia_single_statement(text: str) -> bool:
    source = Source(text, "julia")
    return not syntax_problems(source.tree, limit=1) and len(statements(source.root)) == 1


def _julia_string_literals(code: str) -> Counter[str]:
    """The text of every string literal: a plain string's value, else its literal parts (an interpolated string's
    text between the interpolations, a string macro's text such as a `colorant` colour)."""
    source = _tree_source(code, "julia")
    counts: Counter[str] = Counter()
    for node in walk(source.root):
        if node.type == "string_literal":
            value = jl_string(source, node)
            if value is None:
                value = "".join(source.text(child) for child in node.children if child.type == "content")
            counts[value] += 1
        elif node.type == "prefixed_string_literal":
            counts["".join(source.text(child) for child in node.children if child.type == "content")] += 1
    return counts


def _javascript_read(grammar: Grammar) -> Callable[[str], CodeView]:
    def read(code: str) -> CodeView:
        source = _tree_source(code, grammar)
        found = javascript_regions.find_regions(source)
        save = found.save.span if found.save is not None else None
        top = [binding for binding in js_bindings(source, source.root) if binding.scope.type == "program"]

        def bindings(names: set[str]) -> Counter[str]:
            # Top-level bindings only: a parameter `t` in a callback shadows the token `t` and leaves it as it is.
            return Counter(binding.name for binding in top if binding.name in names)

        def assignments() -> dict[str, list[SpanLike]]:
            assigned: dict[str, list[SpanLike]] = {}
            for node in statements(source.root):
                found_declarator = javascript_regions.declarator(node)
                name = found_declarator.child_by_field_name("name") if found_declarator is not None else None
                names = javascript_regions.declared_names(source, name) if name is not None else None
                if names is not None:
                    assigned.setdefault(", ".join(names), []).append(source.lines_span(node))
            return assigned

        return CodeView(
            theme=None,
            tokens=tuple((region.name, region.span) for region in found.theme_tokens),
            save=save,
            regions=found.protected,
            bindings=bindings,
            assignments=assignments,
        )

    return read


def _javascript_meaning(grammar: Grammar) -> Callable[[str], str]:
    def meaning(text: str) -> str:
        """The token stream of a JavaScript statement: leaf tokens with string values decoded, comments left out but
        the orientation directive, which stands as the orientation it picks (`regions.find_directives`)."""
        source = Source(text, grammar)
        if syntax_problems(source.tree, limit=1):
            return text.strip()
        tokens = [
            f"directive:{directive.orientation}"
            for directive in javascript_regions.find_directives(source)
            if directive.comment
        ]
        stack = [source.root]
        while stack:
            node = stack.pop()
            if node.type in COMMENTS:
                continue
            if node.type in ("string", "template_string"):
                value = js_string(source, node)
                if value is not None:
                    tokens.append(f"string:{value!r}")
                    continue
            if not node.children:
                tokens.append(f"{node.type}:{source.text(node)}")
                continue
            stack.extend(reversed(node.children))
        return "\x00".join(tokens)

    return meaning


def _javascript_single_statement(grammar: Grammar) -> Callable[[str], bool]:
    def single_statement(text: str) -> bool:
        """Exactly one statement on the lines, or the orientation directive alone (a comment the drift check keeps)."""
        source = Source(text, grammar)
        if syntax_problems(source.tree, limit=1):
            return False
        found = statements(source.root)
        if found:
            return len(found) == 1
        directives = javascript_regions.find_directives(source)
        comments = [node for node in source.root.children if node.type in COMMENTS]
        return len(directives) == 1 and directives[0].comment and len(comments) == 1

    return single_statement


def _javascript_string_literals(grammar: Grammar) -> Callable[[str], Counter[str]]:
    def string_literals(code: str) -> Counter[str]:
        """The text of every string literal: a string's or template's value, a template's literal parts around its
        substitutions, and JSX text (MUI X's titles and labels), trimmed."""
        source = _tree_source(code, grammar)
        counts: Counter[str] = Counter()
        for node in walk(source.root):
            if node.type in ("string", "template_string"):
                value = js_string(source, node)
                if value is None:
                    value = "".join(source.text(child) for child in node.children if child.type == "string_fragment")
                counts[value] += 1
            elif node.type == "jsx_text" and source.text(node).strip():
                counts[source.text(node).strip()] += 1
        return counts

    return string_literals


_PYTHON_LITERALS = LiteralSyntax(quotes="'\"", triple=True, multiline=False, raw=False)
_R_LITERALS = LiteralSyntax(quotes="'\"`", triple=False, multiline=True, raw=True)
_JULIA_LITERALS = LiteralSyntax(quotes='"`', triple=True, multiline=True, raw=False)
"""Julia's strings (`"..."` and the triple-quoted form) and commands may span lines; `'` is a character or the
adjoint operator (`x'`), so it opens no literal."""
_JAVASCRIPT_LITERALS = LiteralSyntax(
    quotes="'\"`", triple=False, multiline=False, raw=False, comment="//", block_comment=("/*", "*/"), spans_lines="`"
)
"""JavaScript's strings end with their line (a backslash continues one), its templates may span lines, and its
comments are `//` and `/* */`; a `#` is text (a CSS colour inside a string, a private field `#x`)."""
_JAVASCRIPT_PLACEHOLDER_LINE = re.compile(
    rf"^[ \t]*const[ \t]+{javascript_regions.DATA_NAME}[ \t]*=[ \t]*{javascript_regions.PLACEHOLDER_FUNC}\(\)[ \t]*;?"
    r"[ \t]*(?://[^\r\n]*)?(?:\r\n|\r|\n|$)",
    re.M,
)
R_LIBRARIES = frozenset({"ggplot2"})
"""The libraries whose code is R (the R profile, `profiles/r/`)."""
JULIA_LIBRARIES = frozenset({"makie"})
"""The libraries whose code is Julia (the Julia profile, `profiles/julia/`)."""
JAVASCRIPT_LIBRARIES = frozenset(javascript_regions.LIBRARIES)
"""The libraries whose code is JavaScript or TSX (the JavaScript profile, `profiles/javascript/`)."""


def dialect_for(library: str) -> Dialect:
    """The dialect of `library`'s code: R for ggplot2, Julia for Makie, JavaScript for Chart.js, D3, ECharts,
    Highcharts and MUI X (TSX), else Python with the library's save rule."""
    if library in JAVASCRIPT_LIBRARIES:
        grammar = javascript_regions.grammar_for(library)
        directive = "//# anyplot-orientation directive"
        return Dialect(
            placeholder=javascript_regions.PLACEHOLDER,
            placeholder_line=_JAVASCRIPT_PLACEHOLDER_LINE,
            save_word="//# anyplot-orientation",
            literals=_JAVASCRIPT_LITERALS,
            read=_javascript_read(grammar),
            meaning=_javascript_meaning(grammar),
            single_statement=_javascript_single_statement(grammar),
            string_literals=_javascript_string_literals(grammar),
            save_label=directive,
            keep_label=(
                f"the token lines (window.ANYPLOT_TOKENS, _THEME, _SIZE), the {javascript_regions.PLACEHOLDER} line and "
                f"the {directive}"
            ),
            reminder_label=f"the token lines and the {directive}",
            theme_name=None,
        )
    if library in JULIA_LIBRARIES:
        return Dialect(
            placeholder=julia_regions.PLACEHOLDER,
            placeholder_line=_PLACEHOLDER_LINE,
            save_word="save",
            literals=_JULIA_LITERALS,
            read=_julia_read,
            meaning=_julia_meaning,
            single_statement=_julia_single_statement,
            string_literals=_julia_string_literals,
        )
    if library in R_LIBRARIES:
        return Dialect(
            placeholder=r_regions.PLACEHOLDER,
            placeholder_line=_R_PLACEHOLDER_LINE,
            save_word="ggsave",
            literals=_R_LITERALS,
            read=_r_read,
            meaning=_r_meaning,
            single_statement=_r_single_statement,
            string_literals=_r_string_literals,
        )
    python_regions.save_rule(library)  # a library without a profile is a caller bug: ValueError
    return Dialect(
        placeholder=PLACEHOLDER,
        placeholder_line=_PLACEHOLDER_LINE,
        save_word="savefig",
        literals=_PYTHON_LITERALS,
        read=_python_read(library),
        meaning=_python_meaning,
        single_statement=_python_single_statement,
        string_literals=_python_string_literals,
    )


# --- the applier -----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AppliedPlan:
    """The edited working form, or None with one failure line per refused edit.

    `kinds` holds the `FAILURE_KINDS` entry of every failure, the ones past the
    `MAX_FEEDBACK` lines included; trailer lines (the drift reminder, the overflow
    count) have none. `tolerant` names the `TOLERANT_TIERS` entry of every edit that
    applied through a tolerant tier, in plan order, also when another edit of the
    plan failed or the plan drifted, so the log counts every match a tier found.
    """

    code: str | None
    failures: list[str] = field(default_factory=list)
    kinds: tuple[str, ...] = ()
    tolerant: tuple[str, ...] = ()
    drifted: str | None = None
    """The plan's result when only `protected_drift` refused it (every edit applied), for `restore_protected`."""


RESTORABLE_DRIFT: frozenset[str] = frozenset({"drift:theme", "drift:theme_token", "drift:savefig"})
"""The drift kinds `restore_protected` may undo; a theme name bound again (`drift:rebind`) is never restored."""


def apply_plan(working: str, plan: AdaptPlan, *, library: str = "matplotlib") -> AppliedPlan:
    """Apply `plan` to the working form `working`; see the module docstring.

    `library` picks the dialect (`dialect_for`): the language, and for Python the save
    rule (`regions.SAVE_RULES`) that finds the protected final save.
    """
    dialect = dialect_for(library)
    applied = _apply(working, plan, dialect)
    if applied.code is None:
        return applied
    drift = _drift(base=working, code=applied.code, dialect=dialect)
    if not drift:
        return applied
    lines = _with_drift_reminder([line for _, line in drift], dialect)
    kinds = tuple(kind for kind, _ in drift)
    return AppliedPlan(None, lines[:MAX_FEEDBACK], kinds, applied.tolerant, drifted=applied.code)


def restore_protected(base: str, code: str, *, library: str = "matplotlib") -> str | None:
    """`code` with the base's text put back over every protected statement it changed, or None.

    Only when every drift of `code` against `base` is in `RESTORABLE_DRIFT`; a rebind,
    a removed protected statement, one that shares its lines with another statement
    (in the plan's code or in the base),
    a result that does not parse or one that still drifts restores nothing. Each
    replaced region is a whole module-level statement's lines, so the splice keeps
    the code around it as the plan wrote it.
    """
    dialect = dialect_for(library)
    drift = _drift(base, code, dialect)
    if not drift or not {kind for kind, _ in drift} <= RESTORABLE_DRIFT:
        return None
    try:
        before, after = dialect.read(base), dialect.read(code)
    except SyntaxError:
        return None
    assigned = after.assignments()

    def statement(names: str) -> SpanLike | None:
        found = assigned.get(names, [])
        return found[0] if len(found) == 1 else None

    splices: list[tuple[SpanLike, str]] = []
    pairs: list[tuple[SpanLike, SpanLike | None]] = []
    if before.theme is not None:
        pairs.append((before.theme, statement(THEME_NAME)))
    pairs += [(span, statement(name)) for name, span in before.tokens]
    if before.save is not None:
        pairs.append((before.save, after.save))
    for base_span, target in pairs:
        if target is not None and _meaning(dialect, base, base_span) == _meaning(dialect, code, target):
            continue
        text = base[base_span.start : base_span.end]
        # Both sides must be one statement on their lines: a line shared on either side would drop or copy another.
        if (
            target is None
            or not dialect.single_statement(code[target.start : target.end])
            or not dialect.single_statement(text)
        ):
            return None
        if not text.endswith(("\n", "\r")) and target.end < len(code):
            text += "\n"  # the base's statement ended the file; here code follows it
        splices.append((target, text))
    restored = _splice(code, splices)
    if restored is None:
        return None
    try:
        dialect.read(restored)
    except SyntaxError:
        return None
    return None if _drift(base, restored, dialect) else restored


def _module_assignment(stmt: ast.stmt) -> str | None:
    """The names a module-level `Assign` or `AnnAssign` binds, joined as `Region.name` joins them."""
    if isinstance(stmt, ast.Assign):
        targets = stmt.targets
    elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
        targets = [stmt.target]
    else:
        return None
    if not all(isinstance(target, ast.Name) for target in targets):
        return None
    return ", ".join(target.id for target in targets if isinstance(target, ast.Name))


def _splice(code: str, splices: list[tuple[SpanLike, str]]) -> str | None:
    """`code` with each span replaced by its text; None when two spans overlap."""
    cursor, parts = 0, []
    for span, replacement in sorted(splices, key=lambda splice: splice[0].start):
        if span.start < cursor:
            return None
        parts += [code[cursor : span.start], replacement]
        cursor = span.end
    parts.append(code[cursor:])
    return "".join(parts)


def protected_drift(base: str, code: str, *, library: str = "matplotlib") -> list[str]:
    """Failure lines when `code` changed a protected region of `base` or binds a theme name again.

    The text checks per edit cannot see a `full_code` plan, nor an edit that adds
    `PAGE_BG = "#FF00FF"` further down. So after every plan the THEME assignment, each
    theme token assignment and the final savefig statement must keep their meaning,
    compared as syntax trees: a full file that re-states a token with the same value
    in other quotes, spacing, line breaks or comment passes, any other value does not.
    THEME and the token names may be bound no more often than in `base` (assignment,
    augmented assignment, `del`, `global`, import alias, function, class, parameter,
    loop or `with` target, walrus, `except ... as`, match capture; in R an assignment of
    any arrow, a replacement form, a parameter or a `for` variable). A `code` that does
    not parse is left to the validator.
    """
    dialect = dialect_for(library)
    return _with_drift_reminder([line for _, line in _drift(base, code, dialect)], dialect)


def _with_drift_reminder(lines: list[str], dialect: Dialect) -> list[str]:
    if not lines:
        return []
    kept = dialect.reminder_label or f"the THEME assignment, the theme tokens and the final {dialect.save_word}"
    reminder = f"keep {kept} exactly as in the current code"
    return [*lines, _line(reminder)]


def _drift(base: str, code: str, dialect: Dialect) -> list[tuple[str, str]]:
    """`protected_drift` without its closing reminder: one `(kind, failure line)` pair per drift."""
    try:
        before = dialect.read(base)
        after = dialect.read(code)
    except SyntaxError:
        return []
    failures: list[tuple[str, str]] = []

    if before.theme is not None and (
        after.theme is None or _meaning(dialect, base, before.theme) != _meaning(dialect, code, after.theme)
    ):
        failures.append(("drift:theme", "the plan changes or removes the protected THEME assignment"))
    after_tokens = {name: _meaning(dialect, code, span) for name, span in after.tokens}
    for name, span in before.tokens:
        if after_tokens.get(name) != _meaning(dialect, base, span):
            failures.append(
                (
                    "drift:theme_token",
                    f"the plan changes or removes the protected theme token {name}; "
                    "copy its line unchanged from the current code",
                )
            )
    if before.save is not None:
        if after.save is None or _meaning(dialect, base, before.save) != _meaning(dialect, code, after.save):
            line = f"the plan changes or removes the protected {dialect.saved()}"
            failures.append(("drift:savefig", line))

    theme = {dialect.theme_name} if dialect.theme_name is not None else set()
    names = {*theme, *(part for name, _ in before.tokens for part in name.split(", "))}
    counts_before, counts_after = before.bindings(names), after.bindings(names)
    for name in sorted(names):
        if counts_after.get(name, 0) > counts_before.get(name, 0):
            line = f"the plan binds {name} a second time; the theme names are set once, on their protected line"
            failures.append(("drift:rebind", line))
    return [(kind, _line(failure)) for kind, failure in failures]


def _meaning(dialect: Dialect, source: str, span: SpanLike) -> str:
    """A protected statement as its syntax tree without positions: comments, spacing and quotes do not count.

    Every protected region is a whole module-level statement, so its lines parse on
    their own; the stripped text stands in should they ever not.
    """
    return dialect.meaning(source[span.start : span.end])


def _bindings(tree: ast.Module, names: set[str]) -> Counter[str]:
    """How often each of `names` is bound or deleted anywhere in `tree`."""
    counts: Counter[str] = Counter()
    for node in ast.walk(tree):
        bound: list[str] = []
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store | ast.Del):
            bound = [node.id]
        elif isinstance(node, ast.Global | ast.Nonlocal):
            bound = list(node.names)
        elif isinstance(node, ast.alias):
            bound = [node.asname or node.name.split(".")[0]]
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            bound = [node.name]
        elif isinstance(node, ast.arg):
            bound = [node.arg]
        elif isinstance(node, ast.ExceptHandler | ast.MatchAs | ast.MatchStar) and node.name:
            bound = [node.name]
        elif isinstance(node, ast.MatchMapping) and node.rest:
            bound = [node.rest]
        counts.update(name for name in bound if name in names)
    return counts


def new_literals(base: str, code: str, *, library: str = "matplotlib") -> list[str]:
    """The string literals of `code` that `base` does not already hold (as a multiset), each as often as it is new.

    A `code` or `base` that does not parse has none; the validator reports the syntax error.
    """
    dialect = dialect_for(library)
    try:
        before, after = dialect.string_literals(base), dialect.string_literals(code)
    except SyntaxError:
        return []
    return [text for text, count in sorted((after - before).items()) for _ in range(count)]


def new_literal_chars(base: str, code: str, *, library: str = "matplotlib") -> int:
    """Characters of string literals in `code` that `base` does not already hold (as a multiset).

    The plan's literal budget (`MAX_NEW_LITERAL_CHARS`, `MAX_CHANGE_LITERAL_CHARS` on a
    change turn): an adaptation renames titles and labels, it does not write out data
    or long text. A `code` or `base` that does not parse counts as 0.
    """
    return sum(len(text) for text in new_literals(base, code, library=library))


def _string_literals(tree: ast.Module) -> Counter[str]:
    """Every str and bytes constant (bytes as Latin-1 text, as the validator reads them), f-string parts included."""
    counts: Counter[str] = Counter()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            counts[node.value] += 1
        elif isinstance(node, ast.Constant) and isinstance(node.value, bytes):
            counts[node.value.decode("latin-1")] += 1
    return counts


def _apply(working: str, plan: AdaptPlan, dialect: Dialect) -> AppliedPlan:
    if plan.full_code is not None:
        return AppliedPlan(plan.full_code)
    try:
        view = dialect.read(working)
    except SyntaxError as exc:
        line = f"the working form does not parse at line {exc.lineno}; no edit was applied"
        return AppliedPlan(None, [line], ("working_unparseable",))
    # Placeholders are found as text on every step instead (see _PLACEHOLDER_LINE).
    protected = [
        _Protected(region.kind, region.name, region.span.start, region.span.end)
        for region in view.regions
        if region.kind != "placeholder"
    ]

    text = working
    failures: list[str] = []
    kinds: list[str] = []
    tolerant: list[str] = []
    total = len(plan.edits)
    for number, edit in enumerate(plan.edits, start=1):
        label = f"edit {number}/{total}"
        tier, matches = _locate(text, edit.find, edit.replace, dialect.literals)
        if not matches and text != working and len(_locate(working, edit.find, edit.replace, dialect.literals)[1]) == 1:
            failures.append(_stale_failure(label, edit.find))
            kinds.append("stale_match")
            continue
        if len(matches) != 1:
            failures.append(_count_failure(label, len(matches), edit.find))
            kinds.append("zero_match" if not matches else "multi_match")
            continue
        start, end, replace = matches[0]
        hit = next((r for r in [*protected, *_placeholders(text, dialect)] if r.overlaps(start, end)), None)
        if hit is not None:
            failures.append(_protected_failure(label, text, start, end, hit, dialect))
            kinds.append(f"protected:{hit.kind}")
            continue
        text = text[:start] + replace + text[end:]
        protected = _shift(protected, end, len(replace) - (end - start))
        if tier != "exact":
            tolerant.append(tier)

    if len(failures) > MAX_FEEDBACK:
        hidden = len(failures) - (MAX_FEEDBACK - 1)
        failures = [
            *failures[: MAX_FEEDBACK - 1],
            f"{hidden} more edits failed in the same way; fix the ones above first",
        ]
    return AppliedPlan(None if failures else text, failures, tuple(kinds), tuple(tolerant))


Match = tuple[int, int, str]
"""One place `find` matched: its start and end in the text, and the replacement to put there."""


def _locate(
    text: str, find: str, replace: str, literals: LiteralSyntax = _PYTHON_LITERALS
) -> tuple[MatchTier, list[Match]]:
    """The matches of `find` in the first tier that has any (module docstring, "Matching"), with that tier."""
    exact = [(start, start + len(find), replace) for start in _occurrences(text, find)]
    if exact:
        return "exact", exact
    trailing = _trailing_whitespace_matches(text, find, replace)
    if trailing:
        return "trailing_whitespace", trailing
    return "whitespace", _whitespace_matches(text, find, replace, literals)


def _occurrences(text: str, find: str) -> list[int]:
    """Start offsets of every occurrence of `find`, overlapping ones included (capped)."""
    found: list[int] = []
    position = text.find(find)
    while position != -1 and len(found) < MAX_COUNTED_MATCHES:
        found.append(position)
        position = text.find(find, position + 1)
    return found


def _line_spans(source: str) -> list[tuple[int, int, int]]:
    """Each line as `(start, content_end, end)`: `content_end` before its line break, `end` after it."""
    spans: list[tuple[int, int, int]] = []
    start = 0
    for match in _NEWLINE.finditer(source):
        spans.append((start, match.start(), match.end()))
        start = match.end()
    spans.append((start, len(source), len(source)))
    return spans


def _without_line_end_blanks(source: str) -> tuple[str, list[int], list[int]]:
    """`source` without the spaces and tabs before each line break and with every break written `\\n`.

    Also returns, per kept character, its start and end offset in `source`, so a match
    in the result maps back to the exact span it covers there (a `\\r\\n` is one kept
    character two source characters wide).
    """
    kept: list[str] = []
    starts: list[int] = []
    ends: list[int] = []
    for start, content_end, end in _line_spans(source):
        content = source[start:content_end].rstrip(_LINE_END_BLANKS)
        kept.append(content)
        starts.extend(range(start, start + len(content)))
        ends.extend(range(start + 1, start + len(content) + 1))
        if end > content_end:
            kept.append("\n")
            starts.append(content_end)
            ends.append(end)
    return "".join(kept), starts, ends


def _trailing_whitespace_matches(text: str, find: str, replace: str) -> list[Match]:
    """Tier 2: the matches once blanks before line breaks are gone and line breaks are `\\n` on both sides."""
    normal_find = _without_line_end_blanks(find)[0]
    if not normal_find.strip():
        return []
    normal_text, starts, ends = _without_line_end_blanks(text)
    return [
        (starts[position], ends[position + len(normal_find) - 1], replace)
        for position in _occurrences(normal_text, normal_find)
    ]


def _whitespace_matches(text: str, find: str, replace: str, literals: LiteralSyntax) -> list[Match]:
    """Tier 3: whole lines whose words agree, with `replace` moved by the one indentation shift between them."""
    find_lines = _NEWLINE.split(find)
    ends_with_break = len(find_lines) > 1 and find_lines[-1] == ""
    if ends_with_break:
        find_lines.pop()
    find_words, _ = _line_words(find_lines, literals)
    if not any(find_words):
        return []
    text_lines = _line_spans(text)
    text_words, in_literal = _line_words([text[start:content_end] for start, content_end, _ in text_lines], literals)
    count = len(find_lines)
    matches: list[Match] = []
    for first in range(len(text_lines) - count + 1):
        if text_words[first : first + count] != find_words or any(in_literal[first : first + count]):
            continue
        window = text_lines[first : first + count]
        indents = [
            (_indent(text[start:content_end]), _indent(line))
            for (start, content_end, _), line, words in zip(window, find_lines, find_words, strict=True)
            if words
        ]
        moved = _reindent(replace, indents)
        if moved is None:
            continue
        last_start, last_content_end, last_end = window[-1]
        end = last_end if ends_with_break else last_content_end
        if ends_with_break and last_end == last_content_end:
            continue  # find ends with a line break that the code's last line does not have
        matches.append((window[0][0], end, moved))
        if len(matches) >= MAX_COUNTED_MATCHES:
            break
    return matches


def _line_words(lines: list[str], literals: LiteralSyntax = _PYTHON_LITERALS) -> tuple[list[str], list[bool]]:
    """Each line's words for the whitespace tier, and whether the line starts inside a string literal.

    Outside string literals, indentation and trailing blanks go and every run of blanks
    becomes one space, as `" ".join(line.split())` would; a comment collapses the same
    way. A literal's text, quotes included, stays verbatim, so two lines that differ in
    the blanks inside a string do not agree. The scan carries an open literal from one
    line to the next (a triple-quoted one, or a quoted one continued by a backslash; in
    R any quoted one, which may span lines; in JavaScript a template), which marks the
    lines that start inside it. An R raw string (`r"(...)"`) ends only at its own closing
    delimiter and has no escapes. A JavaScript block comment (`/* */`) may span lines too;
    its words collapse like code, and a quote inside it opens no literal.
    """
    words: list[str] = []
    starts_inside: list[bool] = []
    quote: str | None = None  # the open literal's delimiter: ', ", ''' or """ (R: also ` and a raw closer)
    raw = False
    block: str | None = None  # the closer of an open block comment (JavaScript's `*/`), which may span lines
    for line in lines:
        starts_inside.append(quote is not None)
        kept: list[str] = []
        blank = False
        position = 0
        while position < len(line):
            char = line[position]
            if quote is not None:
                if char == "\\" and not raw:
                    kept.append(line[position : position + 2])
                    position += 2
                elif line.startswith(quote, position):
                    kept.append(quote)
                    position += len(quote)
                    quote = None
                    raw = False
                else:
                    kept.append(char)
                    position += 1
                continue
            if char.isspace():
                blank = True
                position += 1
                continue
            if blank and kept:
                kept.append(" ")
            blank = False
            if block is not None:  # inside a block comment: its words collapse like code, and a quote opens nothing
                closed = line.startswith(block, position)
                kept.append(block if closed else char)
                position += len(block) if closed else 1
                block = None if closed else block
                continue
            if literals.block_comment is not None and line.startswith(literals.block_comment[0], position):
                block = literals.block_comment[1]
                kept.append(literals.block_comment[0])
                position += len(literals.block_comment[0])
                continue
            if line.startswith(literals.comment, position):
                kept.append(" ".join(line[position:].split()))
                break
            opener = _R_RAW_OPENER.match(line, position) if literals.raw and char in "rR" else None
            if opener is not None:
                quote = _RAW_CLOSERS[opener.group(3)] + opener.group(2) + opener.group(1)
                raw = True
                kept.append(opener.group(0))
                position = opener.end()
                continue
            if char in literals.quotes:
                quote = char * 3 if literals.triple and line.startswith(char * 3, position) else char
                kept.append(quote)
                position += len(quote)
                continue
            kept.append(char)
            position += 1
        if (
            quote is not None
            and len(quote) == 1
            and not literals.multiline
            and quote not in literals.spans_lines
            and not line.endswith("\\")
        ):
            quote = None  # a one-quote literal ends with its line unless a backslash continues it
        words.append("".join(kept))
    return words, starts_inside


def _indent(line: str) -> str:
    return line[: len(line) - len(line.lstrip(" \t"))]


def _reindent(replace: str, indents: list[tuple[str, str]]) -> str | None:
    """`replace` shifted by the indentation the code has over `find` (or `find` over the code).

    `indents` pairs each non-blank matched line's indentation in the code with its
    indentation in `find`. They must share one shift (the code's indentation is a
    prefix plus `find`'s, or `find`'s a prefix plus the code's, with the same prefix
    on every line); otherwise, or when a line of `replace` lacks the indentation a
    shift would remove, there is no safe placement and the match is not used.
    """
    shifts: set[tuple[str, str]] = set()
    for code_indent, find_indent in indents:
        if code_indent.endswith(find_indent):
            shifts.add(("add", code_indent[: len(code_indent) - len(find_indent)]))
        elif find_indent.endswith(code_indent):
            shifts.add(("remove", find_indent[: len(find_indent) - len(code_indent)]))
        else:
            return None
    if len(shifts) != 1:
        return None
    direction, prefix = shifts.pop()
    if not prefix:
        return replace
    moved: list[str] = []
    for line in (replace[start:end] for start, _, end in _line_spans(replace) if end > start):
        if not line.strip():
            moved.append(line)
        elif direction == "add":
            moved.append(prefix + line)
        elif line.startswith(prefix):
            moved.append(line[len(prefix) :])
        else:
            return None
    return "".join(moved)


@dataclass(frozen=True, slots=True)
class _Protected:
    """A protected region while a plan applies: its kind, name and characters `[start, end)` in the current text."""

    kind: str
    name: str
    start: int
    end: int

    def overlaps(self, start: int, end: int) -> bool:
        """Whether the half-open character range `[start, end)` shares a character with this region."""
        return start < self.end and self.start < end


def _placeholders(text: str, dialect: Dialect) -> list[_Protected]:
    return [
        _Protected("placeholder", dialect.placeholder, match.start(), match.end())
        for match in dialect.placeholder_line.finditer(text)
    ]


def _shift(regions: list[_Protected], after: int, delta: int) -> list[_Protected]:
    """Move the regions that start at or after `after` by `delta` characters (lines are not tracked)."""
    if not delta:
        return regions
    return [
        dataclasses.replace(region, start=region.start + delta, end=region.end + delta)
        if region.start >= after
        else region
        for region in regions
    ]


def _quote(code: str) -> str:
    """At most `MAX_QUOTE_CHARS` characters of code on one line, newlines shown as `\\n`."""
    shown = code[:MAX_QUOTE_CHARS].replace("\\", "\\\\").replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t")
    return f'"{shown}…"' if len(code) > MAX_QUOTE_CHARS else f'"{shown}"'


def _count_failure(label: str, count: int, find: str) -> str:
    if count == 0:
        advice = "copy find verbatim from the current code, including indentation and quotes"
        counted = "0 times"
    else:
        advice = "extend find with a neighbouring line until it is unique"
        counted = f"{count}{'+' if count >= MAX_COUNTED_MATCHES else ''} times"
    return _line(
        f"{label}: find matches {counted} in the current code, it must match exactly once; {advice}. find = {_quote(find)}"
    )


def _stale_failure(label: str, find: str) -> str:
    return _line(
        f"{label}: find matches the code only as it was before an earlier edit of this plan changed it; "
        "write each find against the code after the edits before it, or merge the two edits into one. "
        f"find = {_quote(find)}"
    )


def _protected_failure(label: str, text: str, start: int, end: int, region: _Protected, dialect: Dialect) -> str:
    index = SourceIndex(text)
    first, last = index.line_of(start), index.line_of(max(start, end - 1))
    where = f"line {first}" if first == last else f"lines {first}-{last}"
    region_line = index.line_of(region.start)
    if region.kind == "placeholder":
        return _line(
            f"{label}: find ({where}) overlaps {_placeholder_advice(index, region, dialect)} "
            f"find = {_quote(text[start:end])}"
        )
    what = dialect.saved() if region.kind == "savefig" else _KIND_NAMES[region.kind].format(save=dialect.save_word)
    name = "" if region.kind == "theme" or (region.kind == "savefig" and dialect.save_label) else f" {region.name}"
    kept = (
        dialect.keep_label
        or f"the THEME assignment, the theme tokens, the {dialect.placeholder} line and the final {dialect.save_word}"
    )
    return _line(
        f"{label}: find ({where}) overlaps the protected {what}{name} at line {region_line}; "
        f"{kept} stay unchanged, so anchor the edit on other lines. find = {_quote(text[start:end])}"
    )


def _placeholder_advice(index: SourceIndex, region: _Protected, dialect: Dialect) -> str:
    """How to work around the placeholder: name the line below it, which an insertion anchors on."""
    line = index.line_of(region.start)
    below = next((number for number in range(line + 1, index.line_count + 1) if index.line_text(number).strip()), None)
    head = (
        f"the protected {dialect.placeholder} line at line {line}; keep that line exactly as it is and out of find "
        "and replace"
    )
    if below is None:  # never in a working form, where the final savefig follows
        return f"{head}."
    anchor = _quote(index.line_text(below).rstrip("\r\n"))
    return (
        f"{head}; to change df or add statements after it, set find to line {below} ({anchor}) "
        "and write the new statements in front of that line in replace."
    )


def _line(text: str) -> str:
    """One feedback line of at most `MAX_LINE_CHARS` (quotes already escape their newlines)."""
    text = text.replace("\r", " ").replace("\n", " ")
    return text if len(text) <= MAX_LINE_CHARS else text[: MAX_LINE_CHARS - 1] + "…"
