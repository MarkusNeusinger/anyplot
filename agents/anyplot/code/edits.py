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
3. `whitespace`: whole lines whose words agree once indentation and runs of spaces
   are ignored. The replacement is re-indented by the one indentation the code has
   over `find` (or `find` over the code); when the lines do not share one such shift,
   the tier finds nothing, because Python's indentation is meaning.

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

Failure lines are repair feedback (`Line`): one line each, at most `MAX_LINE_CHARS`
characters, quoting at most `MAX_QUOTE_CHARS` characters of code. Next to them,
`AppliedPlan.kinds` names each failure by a fixed, content-free kind (`FAILURE_KINDS`)
for the attribution log, which never sees the lines because they quote code.
"""

import ast
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Literal

from ..schemas import MAX_FEEDBACK, MAX_LINE_CHARS, AdaptPlan
from .regions import PLACEHOLDER, PLACEHOLDER_FUNC, THEME_NAME, Region, SourceIndex, Span, find_regions


MAX_QUOTE_CHARS = 80
MAX_COUNTED_MATCHES = 1000
MAX_NEW_LITERAL_CHARS = 2_000
"""New string-literal text one plan may add (design doc, "Adapt and validate")."""

# The placeholder statement as a line of text, so one that an earlier edit of the same
# plan introduced is protected before the code parses again.
_PLACEHOLDER_LINE = re.compile(
    rf"^[ \t]*df[ \t]*=[ \t]*{PLACEHOLDER_FUNC}\(\)[ \t]*(?:#[^\r\n]*)?(?:\r\n|\r|\n|$)", re.M
)
_NEWLINE = re.compile(r"\r\n|\r|\n")
_LINE_END_BLANKS = " \t"

_KIND_NAMES = {
    "theme": "THEME assignment",
    "theme_token": "theme token",
    "placeholder": "placeholder line",
    "savefig": "final savefig statement",
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


@dataclass(frozen=True, slots=True)
class AppliedPlan:
    """The edited working form, or None with one failure line per refused edit.

    `kinds` holds the `FAILURE_KINDS` entry of every failure, the ones past the
    `MAX_FEEDBACK` lines included; trailer lines (the drift reminder, the overflow
    count) have none. `tolerant` names the `TOLERANT_TIERS` entry of every edit that
    applied through a tolerant tier, in plan order.
    """

    code: str | None
    failures: list[str] = field(default_factory=list)
    kinds: tuple[str, ...] = ()
    tolerant: tuple[str, ...] = ()


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
    theme token assignment and the final savefig statement must keep their meaning,
    compared as syntax trees: a full file that re-states a token with the same value
    in other quotes, spacing, line breaks or comment passes, any other value does not.
    THEME and the token names may be bound no more often than in `base` (assignment,
    augmented assignment, `del`, `global`, import alias, function, class, parameter,
    loop or `with` target, walrus, `except ... as`, match capture). A `code` that does
    not parse is left to the validator.
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

    if before.theme is not None and (
        after.theme is None or _meaning(base, before.theme.span) != _meaning(code, after.theme.span)
    ):
        failures.append(("drift:theme", "the plan changes or removes the protected THEME assignment"))
    after_tokens = {region.name: _meaning(code, region.span) for region in after.theme_tokens}
    for region in before.theme_tokens:
        if after_tokens.get(region.name) != _meaning(base, region.span):
            failures.append(
                (
                    "drift:theme_token",
                    f"the plan changes or removes the protected theme token {region.name}; "
                    "copy its line unchanged from the current code",
                )
            )
    if before.savefig is not None and before.savefig.statement is not None:
        after_savefig = after.savefig.statement if after.savefig is not None else None
        if after_savefig is None or _meaning(base, before.savefig.statement) != _meaning(code, after_savefig):
            failures.append(("drift:savefig", "the plan changes or removes the protected final savefig statement"))

    names = {THEME_NAME, *(name for region in before.theme_tokens for name in region.name.split(", "))}
    counts_before, counts_after = _bindings(before_tree, names), _bindings(after_tree, names)
    for name in sorted(names):
        if counts_after.get(name, 0) > counts_before.get(name, 0):
            line = f"the plan binds {name} a second time; the theme names are set once, on their protected line"
            failures.append(("drift:rebind", line))
    return [(kind, _line(failure)) for kind, failure in failures]


def _meaning(source: str, span: Span) -> str:
    """A protected statement as its syntax tree without positions: comments, spacing and quotes do not count.

    Every protected region is a whole module-level statement, so its lines parse on
    their own; the stripped text stands in should they ever not.
    """
    text = source[span.start : span.end]
    try:
        return ast.dump(ast.parse(text))
    except SyntaxError:
        return text.strip()


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
    tolerant: list[str] = []
    total = len(plan.edits)
    for number, edit in enumerate(plan.edits, start=1):
        label = f"edit {number}/{total}"
        tier, matches = _locate(text, edit.find, edit.replace)
        if not matches and text != working and len(_occurrences(working, edit.find)) == 1:
            failures.append(_stale_failure(label, edit.find))
            kinds.append("stale_match")
            continue
        if len(matches) != 1:
            failures.append(_count_failure(label, len(matches), edit.find))
            kinds.append("zero_match" if not matches else "multi_match")
            continue
        start, end, replace = matches[0]
        hit = next((r for r in [*protected, *_placeholders(text)] if r.span.overlaps(start, end)), None)
        if hit is not None:
            failures.append(_protected_failure(label, text, start, end, hit))
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


def _locate(text: str, find: str, replace: str) -> tuple[MatchTier, list[Match]]:
    """The matches of `find` in the first tier that has any (module docstring, "Matching"), with that tier."""
    exact = [(start, start + len(find), replace) for start in _occurrences(text, find)]
    if exact:
        return "exact", exact
    trailing = _trailing_whitespace_matches(text, find, replace)
    if trailing:
        return "trailing_whitespace", trailing
    return "whitespace", _whitespace_matches(text, find, replace)


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


def _whitespace_matches(text: str, find: str, replace: str) -> list[Match]:
    """Tier 3: whole lines whose words agree, with `replace` moved by the one indentation shift between them."""
    find_lines = _NEWLINE.split(find)
    ends_with_break = len(find_lines) > 1 and find_lines[-1] == ""
    if ends_with_break:
        find_lines.pop()
    find_words = [" ".join(line.split()) for line in find_lines]
    if not any(find_words):
        return []
    text_lines = _line_spans(text)
    count = len(find_lines)
    matches: list[Match] = []
    for first in range(len(text_lines) - count + 1):
        window = text_lines[first : first + count]
        if [" ".join(text[start:content_end].split()) for start, content_end, _ in window] != find_words:
            continue
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


def _stale_failure(label: str, find: str) -> str:
    return _line(
        f"{label}: find matches the code only as it was before an earlier edit of this plan changed it; "
        "write each find against the code after the edits before it, or merge the two edits into one. "
        f"find = {_quote(find)}"
    )


def _protected_failure(label: str, text: str, start: int, end: int, region: Region) -> str:
    index = SourceIndex(text)
    first, last = index.line_of(start), index.line_of(max(start, end - 1))
    where = f"line {first}" if first == last else f"lines {first}-{last}"
    region_line = index.line_of(region.span.start)
    if region.kind == "placeholder":
        return _line(
            f"{label}: find ({where}) overlaps {_placeholder_advice(index, region)} find = {_quote(text[start:end])}"
        )
    what = _KIND_NAMES[region.kind]
    name = "" if region.kind == "theme" else f" {region.name}"
    return _line(
        f"{label}: find ({where}) overlaps the protected {what}{name} at line {region_line}; "
        "the THEME assignment, the theme tokens, the df = load_user_data() line and the final savefig "
        f"stay unchanged, so anchor the edit on other lines. find = {_quote(text[start:end])}"
    )


def _placeholder_advice(index: SourceIndex, region: Region) -> str:
    """How to work around the placeholder: name the line below it, which an insertion anchors on."""
    line = index.line_of(region.span.start)
    below = next((number for number in range(line + 1, index.line_count + 1) if index.line_text(number).strip()), None)
    head = (
        f"the protected {PLACEHOLDER} line at line {line}; keep that line exactly as it is and out of find and replace"
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
