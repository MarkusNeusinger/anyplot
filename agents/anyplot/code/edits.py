"""The edit applier: an `AdaptPlan` applied to the working form, or the reasons it cannot be.

Edits apply in order, each to the text the previous ones produced. An edit's `find`
must occur exactly once in that text (overlapping occurrences count, so `"aa"` in
`"aaa"` is two) and may not overlap a protected region:

* the `THEME = os.getenv("ANYPLOT_THEME", ...)` assignment,
* every module-level assignment whose value tests `THEME == ...` or `THEME != ...`
  (`PAGE_BG`, `ELEVATED_BG`, `INK*`, `GRID`, `BRAND`, ...),
* the placeholder line `df = load_user_data()` once it is present, including one an
  earlier edit of the same plan introduced,
* the final savefig statement.

A protected region covers the whole lines of its statement, so an edit that only
appends a comment to such a line is refused too; an edit may end right before one or
start right after one. The `IMPRINT` palette list is not protected: the adapter may
extend it, and the ADAPTATION validator checks that the existing entries keep their
order. A failing edit is skipped and the rest still run, so one round reports every
problem; the plan as a whole then yields no code. `full_code` replaces everything; the
caller decides whether a full file is allowed (attempt 2 only), the applier only
applies it. After either kind of plan, `protected_drift` compares the result with the
base: the protected statements must keep their exact text, and THEME and the theme
tokens may not be bound again anywhere (a later `PAGE_BG = ...` passes the overlap
check above but would recolour the plot).

Failure lines are repair feedback (`Line`): one line each, at most `MAX_LINE_CHARS`
characters, quoting at most `MAX_QUOTE_CHARS` characters of code. Next to them,
`AppliedPlan.kinds` names each failure by a fixed, content-free kind (`FAILURE_KINDS`)
for the attribution log, which never sees the lines because they quote code.
"""

import ast
import re
from collections import Counter
from dataclasses import dataclass, field

from ..schemas import MAX_FEEDBACK, MAX_LINE_CHARS, AdaptPlan
from .regions import PLACEHOLDER_FUNC, THEME_NAME, Region, SourceIndex, Span, find_regions


MAX_QUOTE_CHARS = 80
MAX_COUNTED_MATCHES = 1000
MAX_NEW_LITERAL_CHARS = 2_000
"""New string-literal text one plan may add (design doc, "Adapt and validate")."""

# The placeholder statement as a line of text, so one that an earlier edit of the same
# plan introduced is protected before the code parses again.
_PLACEHOLDER_LINE = re.compile(
    rf"^[ \t]*df[ \t]*=[ \t]*{PLACEHOLDER_FUNC}\(\)[ \t]*(?:#[^\r\n]*)?(?:\r\n|\r|\n|$)", re.M
)

_KIND_NAMES = {
    "theme": "THEME assignment",
    "theme_token": "theme token",
    "placeholder": "placeholder line",
    "savefig": "final savefig statement",
}
FAILURE_KINDS: frozenset[str] = frozenset(
    {
        "zero_match",
        "multi_match",
        *(f"protected:{kind}" for kind in _KIND_NAMES),
        "drift:theme",
        "drift:theme_token",
        "drift:savefig",
        "drift:rebind",
        "working_unparseable",
    }
)
"""The content-free kind of every failure line: no match, several matches, an overlap with
a protected region (by region kind), a protected statement changed or a theme name bound
again after the plan applied (`drift:*`), or a working form that does not parse."""


@dataclass(frozen=True, slots=True)
class AppliedPlan:
    """The edited working form, or None with one failure line per refused edit.

    `kinds` holds the `FAILURE_KINDS` entry of every failure, the ones past the
    `MAX_FEEDBACK` lines included; trailer lines (the drift reminder, the overflow
    count) have none.
    """

    code: str | None
    failures: list[str] = field(default_factory=list)
    kinds: tuple[str, ...] = ()


def apply_plan(working: str, plan: AdaptPlan) -> AppliedPlan:
    """Apply `plan` to the working form `working`; see the module docstring."""
    applied = _apply(working, plan)
    if applied.code is None:
        return applied
    drift = _drift(working, applied.code)
    if not drift:
        return applied
    lines = _with_drift_reminder([line for _, line in drift])
    return AppliedPlan(None, lines[:MAX_FEEDBACK], tuple(kind for kind, _ in drift))


def protected_drift(base: str, code: str) -> list[str]:
    """Failure lines when `code` changed a protected region of `base` or binds a theme name again.

    The text checks per edit cannot see a `full_code` plan, nor an edit that adds
    `PAGE_BG = "#FF00FF"` further down. So after every plan the THEME assignment, each
    theme token assignment and the final savefig statement must keep their exact
    source text, and THEME and the token names may be bound no more often than in
    `base` (assignment, augmented assignment, `del`, `global`, import alias, function,
    class, parameter, loop or `with` target, walrus, `except ... as`, match capture).
    A `code` that does not parse is left to the validator.
    """
    return _with_drift_reminder([line for _, line in _drift(base, code)])


def _with_drift_reminder(lines: list[str]) -> list[str]:
    if not lines:
        return []
    reminder = "keep the THEME assignment, the theme tokens and the final savefig exactly as in the current code"
    return [*lines, _line(reminder)]


def _drift(base: str, code: str) -> list[tuple[str, str]]:
    """`protected_drift` without its closing reminder: one `(kind, failure line)` pair per drift."""
    try:
        before_tree = ast.parse(base)
        after_tree = ast.parse(code)
    except SyntaxError:
        return []
    before, after = find_regions(base, before_tree), find_regions(code, after_tree)
    failures: list[tuple[str, str]] = []

    def text(source: str, span: Span) -> str:
        return source[span.start : span.end].strip()

    if before.theme is not None and (
        after.theme is None or text(base, before.theme.span) != text(code, after.theme.span)
    ):
        failures.append(("drift:theme", "the plan changes or removes the protected THEME assignment"))
    after_tokens = {region.name: text(code, region.span) for region in after.theme_tokens}
    for region in before.theme_tokens:
        if after_tokens.get(region.name) != text(base, region.span):
            failures.append(
                ("drift:theme_token", f"the plan changes or removes the protected theme token {region.name}")
            )
    if before.savefig is not None and before.savefig.statement is not None:
        after_savefig = after.savefig.statement if after.savefig is not None else None
        if after_savefig is None or text(base, before.savefig.statement) != text(code, after_savefig):
            failures.append(("drift:savefig", "the plan changes or removes the protected final savefig statement"))

    names = {THEME_NAME, *(name for region in before.theme_tokens for name in region.name.split(", "))}
    counts_before, counts_after = _bindings(before_tree, names), _bindings(after_tree, names)
    for name in sorted(names):
        if counts_after.get(name, 0) > counts_before.get(name, 0):
            line = f"the plan binds {name} a second time; the theme names are set once, on their protected line"
            failures.append(("drift:rebind", line))
    return [(kind, _line(failure)) for kind, failure in failures]


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


def new_literal_chars(base: str, code: str) -> int:
    """Characters of string literals in `code` that `base` does not already hold (as a multiset).

    The plan's literal budget (`MAX_NEW_LITERAL_CHARS`): an adaptation renames titles
    and labels, it does not write out data or long text. A `code` or `base` that does
    not parse counts as 0; the validator reports the syntax error.
    """
    try:
        before, after = _string_literals(ast.parse(base)), _string_literals(ast.parse(code))
    except SyntaxError:
        return 0
    return sum(len(text) * count for text, count in (after - before).items())


def _string_literals(tree: ast.Module) -> Counter[str]:
    return Counter(
        node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)
    )


def _apply(working: str, plan: AdaptPlan) -> AppliedPlan:
    if plan.full_code is not None:
        return AppliedPlan(plan.full_code)
    try:
        regions = find_regions(working)
    except SyntaxError as exc:
        line = f"the working form does not parse at line {exc.lineno}; no edit was applied"
        return AppliedPlan(None, [line], ("working_unparseable",))
    # Placeholders are found as text on every step instead (see _PLACEHOLDER_LINE).
    protected = [region for region in regions.protected if region.kind != "placeholder"]

    text = working
    failures: list[str] = []
    kinds: list[str] = []
    total = len(plan.edits)
    for number, edit in enumerate(plan.edits, start=1):
        label = f"edit {number}/{total}"
        matches = _occurrences(text, edit.find)
        if len(matches) != 1:
            failures.append(_count_failure(label, len(matches), edit.find))
            kinds.append("zero_match" if not matches else "multi_match")
            continue
        start = matches[0]
        end = start + len(edit.find)
        hit = next((r for r in [*protected, *_placeholders(text)] if r.span.overlaps(start, end)), None)
        if hit is not None:
            failures.append(_protected_failure(label, text, start, end, hit))
            kinds.append(f"protected:{hit.kind}")
            continue
        text = text[:start] + edit.replace + text[end:]
        protected = _shift(protected, end, len(edit.replace) - (end - start))

    if len(failures) > MAX_FEEDBACK:
        hidden = len(failures) - (MAX_FEEDBACK - 1)
        failures = [
            *failures[: MAX_FEEDBACK - 1],
            f"{hidden} more edits failed in the same way; fix the ones above first",
        ]
    return AppliedPlan(None if failures else text, failures, tuple(kinds))


def _occurrences(text: str, find: str) -> list[int]:
    """Start offsets of every occurrence of `find`, overlapping ones included (capped)."""
    found: list[int] = []
    position = text.find(find)
    while position != -1 and len(found) < MAX_COUNTED_MATCHES:
        found.append(position)
        position = text.find(find, position + 1)
    return found


def _placeholders(text: str) -> list[Region]:
    index = SourceIndex(text)
    regions = []
    for match in _PLACEHOLDER_LINE.finditer(text):
        first = index.line_of(match.start())
        regions.append(Region("placeholder", "df = load_user_data()", Span(first, first, match.start(), match.end())))
    return regions


def _shift(regions: list[Region], after: int, delta: int) -> list[Region]:
    """Move the regions that start at or after `after` by `delta` characters (lines are not tracked)."""
    if not delta:
        return regions
    shifted = []
    for region in regions:
        span = region.span
        if span.start >= after:
            span = Span(span.first_line, span.last_line, span.start + delta, span.end + delta)
        shifted.append(Region(region.kind, region.name, span))
    return shifted


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


def _protected_failure(label: str, text: str, start: int, end: int, region: Region) -> str:
    index = SourceIndex(text)
    first, last = index.line_of(start), index.line_of(max(start, end - 1))
    where = f"line {first}" if first == last else f"lines {first}-{last}"
    what = _KIND_NAMES[region.kind]
    name = "" if region.kind in ("placeholder", "theme") else f" {region.name}"
    region_line = index.line_of(region.span.start)
    return _line(
        f"{label}: find ({where}) overlaps the protected {what}{name} at line {region_line}; "
        "the THEME assignment, the theme tokens, the df = load_user_data() line and the final savefig "
        f"stay unchanged, so anchor the edit on other lines. find = {_quote(text[start:end])}"
    )


def _line(text: str) -> str:
    """One feedback line of at most `MAX_LINE_CHARS` (quotes already escape their newlines)."""
    text = text.replace("\r", " ").replace("\n", " ")
    return text if len(text) <= MAX_LINE_CHARS else text[: MAX_LINE_CHARS - 1] + "…"
