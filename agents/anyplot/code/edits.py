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
applies it.

Failure lines are repair feedback (`Line`): one line each, at most `MAX_LINE_CHARS`
characters, quoting at most `MAX_QUOTE_CHARS` characters of code.
"""

import re
from dataclasses import dataclass, field

from ..schemas import MAX_FEEDBACK, MAX_LINE_CHARS, AdaptPlan
from .regions import PLACEHOLDER_FUNC, Region, SourceIndex, Span, find_regions


MAX_QUOTE_CHARS = 80
MAX_COUNTED_MATCHES = 1000

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


@dataclass(frozen=True, slots=True)
class AppliedPlan:
    """The edited working form, or None with one failure line per refused edit."""

    code: str | None
    failures: list[str] = field(default_factory=list)


def apply_plan(working: str, plan: AdaptPlan) -> AppliedPlan:
    """Apply `plan` to the working form `working`; see the module docstring."""
    if plan.full_code is not None:
        return AppliedPlan(plan.full_code)
    try:
        regions = find_regions(working)
    except SyntaxError as exc:
        return AppliedPlan(None, [f"the working form does not parse at line {exc.lineno}; no edit was applied"])
    # Placeholders are found as text on every step instead (see _PLACEHOLDER_LINE).
    protected = [region for region in regions.protected if region.kind != "placeholder"]

    text = working
    failures: list[str] = []
    total = len(plan.edits)
    for number, edit in enumerate(plan.edits, start=1):
        label = f"edit {number}/{total}"
        matches = _occurrences(text, edit.find)
        if len(matches) != 1:
            failures.append(_count_failure(label, len(matches), edit.find))
            continue
        start = matches[0]
        end = start + len(edit.find)
        hit = next((r for r in [*protected, *_placeholders(text)] if r.span.overlaps(start, end)), None)
        if hit is not None:
            failures.append(_protected_failure(label, text, start, end, hit))
            continue
        text = text[:start] + edit.replace + text[end:]
        protected = _shift(protected, end, len(edit.replace) - (end - start))

    if len(failures) > MAX_FEEDBACK:
        hidden = len(failures) - (MAX_FEEDBACK - 1)
        failures = [
            *failures[: MAX_FEEDBACK - 1],
            f"{hidden} more edits failed in the same way; fix the ones above first",
        ]
    return AppliedPlan(None if failures else text, failures)


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
