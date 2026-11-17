"""The plot memory: the user's standing decisions about the plot, visible on the page, kept across a switch.

Owner decision of 2026-11-02: a library switch must not start from zero. The root hands a run the
lasting decisions of its change (`PipelineArgs.remember`, `KeepRequestArgs.remember`), the pipeline
stores them once the run has shipped (`pipeline.settle_memory`), the page lists the entries under
"Gemerkt" and removes one on request (`GET`/`DELETE /v1/sessions/{sid}/memory`), the root removes one
with `forget`, and every later run of the plot hands them to the adapter and the reviewer as the
user's standing decisions (`pipeline._requests_lines`), in whatever library and, later, plot type
the run adapts. The owner's own examples are a horizontal line at 7, an annotation with a LaTeX
formula, outliers as red stars, an axis label given verbatim and the x limits, so an entry is a
closed `kind`, an optional closed `target` and free, library-neutral text, never a fixed key with
a value. The decisions travel with the run because the root cannot call a tool after a shipped
plot: the Budget plugin strips the tools of that closing call (`plugins/budget.py`).

The memory lives in session state only (`MEMORY`, `MEMORY_SEQ`) and dies with the session: nothing
durable, no telemetry beyond counts by kind (`kind_counts`). Every read validates every entry again
(`read_memory`), so a corrupt value never reaches a prompt; the text is model-written from the
user's words, so every prompt gets it fenced as user text.

Replace rule: a new entry of a single-valued kind (`SINGLE_KINDS`) replaces the entry of the same
kind and target (`replace_key`: the target `plot` is the same as none); an entry of a multi-valued kind
(`MULTI_KINDS`) is added beside the others and goes only by its id (`forget`). The caps (`MAX_ENTRIES`,
`MAX_TEXT_CHARS`, `MAX_TOTAL_CHARS`) refuse a new entry (`MemoryRefused("memory_full")`) rather than
dropping an old one silently.

Besides the root's items, one server-side step keeps a standing title, subtitle or x or y axis label in
step with the plot (`replace_drawn`): when a shipped render no longer draws the entry's verbatim text as
the whole of any drawn text, and draws a text the user wrote as that part's whole text instead, the new
text replaces the entry. It never creates an entry, and it reads the parts the library's probe reports.
An entry whose verbatim text a shipped render does not draw anywhere stays, and the plot's card lists it
as not used (`not_drawn`).
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal, get_args

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .grounding import DrawnTexts, draws, format_unit, whole_text_as, whole_text_in
from .language import same_language
from .schemas import (
    MAX_DECISION_CHARS,
    MAX_DECISIONS,
    MAX_EXPECTED_TEXTS,
    MEMORY_ENTRY_ID_PATTERN,
    ExpectedText,
    MemoryKind,
    MemoryTarget,
    MemoryText,
    RememberItem,
    ShownGroup,
)


PREFIX = "anyplot."
MEMORY = PREFIX + "memory"
"""The entries, oldest first, as dicts of `MemoryEntry`."""
MEMORY_SEQ = PREFIX + "memory_seq"
"""The number the next entry's id takes (`m1`, `m2`, ...): ids are never reused within a session, so a page that
removes an entry by an id it listed earlier never removes a newer one."""

KINDS: tuple[str, ...] = get_args(MemoryKind)
TARGETS: tuple[str, ...] = get_args(MemoryTarget)
MULTI_KINDS: frozenset[str] = frozenset({"reference_line", "annotation", "marker", "other"})
"""Kinds that hold several entries side by side (two reference lines, three annotations): a new one is added."""
SINGLE_KINDS: frozenset[str] = frozenset(KINDS) - MULTI_KINDS
"""Kinds that hold one entry per target (one title, one x-axis label, one y scale): a new one replaces it."""

MAX_ENTRIES = MAX_DECISIONS
MAX_TEXT_CHARS = MAX_DECISION_CHARS
MAX_TOTAL_CHARS = 3_000
"""The texts of all entries together: 30 entries of 100 characters, or 15 at the text cap."""
ENTRY_ID_PATTERN = MEMORY_ENTRY_ID_PATTERN

SLOT_GROUPS: dict[tuple[str, str | None], ShownGroup] = {
    ("title", None): "title",
    ("subtitle", None): "subtitle",
    ("axis_label", "x"): "x axis label",
    ("axis_label", "y"): "y axis label",
}
"""The single-valued text entries `replace_drawn` keeps in step with the render, by `replace_key`, and the drawn texts'
role that holds each one: the plot's title and subtitle, and the x and y axis labels. A title filed under another
target (a legend's, under `color`) is no plot title and stays out."""
SLOT_TEXTS: dict[ShownGroup, str] = {
    "title": "title: '{text}'",
    "subtitle": "subtitle: '{text}'",
    "x axis label": "x-axis label: '{text}'",
    "y axis label": "y-axis label: '{text}'",
}
"""The instruction of a replacing entry whose old instruction cannot simply take the new text (`_replacing_text`), in the
form the root writes them."""


class MemoryEntry(BaseModel):
    """One standing decision: what kind of thing it sets, on which part of the plot, in the user's terms."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=ENTRY_ID_PATTERN)
    kind: MemoryKind
    target: MemoryTarget | None = None
    text: MemoryText
    """A short, library-neutral instruction ("horizontal reference line at y = 7", "x-axis label: 'Zeit (h)'")."""
    expect: ExpectedText | None = None
    """The text the decision puts in the plot, verbatim as the user wrote it (a title, an axis label), so a run that
    carries the memory into another library checks the render for it (`grounding`); None for a decision without one."""
    turn: int = Field(ge=0, le=100_000)
    """The session's user turn the entry was written in: an entry newer than a plot's version is not in it yet."""


class ForgetArgs(BaseModel):
    """The `forget` tool's input."""

    model_config = ConfigDict(extra="forbid")

    entry_id: str = Field(pattern=ENTRY_ID_PATTERN)


class MemoryRefused(Exception):
    """A write the memory refuses: `memory_full` (a cap) or `unknown_entry` (`forget` of an id it does not hold)."""

    def __init__(self, code: Literal["memory_full", "unknown_entry"]) -> None:
        super().__init__(code)
        self.code = code


def replace_key(kind: str, target: str | None) -> tuple[str, str | None]:
    """The key a single-valued entry is replaced by: its kind and target, the target `plot` read as none, so a title
    filed with `plot` and one filed without are one title. Only this synonym is folded: a legend's title filed under
    `color` stays apart from the plot's."""
    return (kind, None if target == "plot" else target)


def read_memory(state: Any) -> list[MemoryEntry]:
    """The entries in `state`, oldest first; an item that fails validation is dropped, never passed on.

    A single-valued kind holds one entry per `replace_key`: of two stored under one key (a title with the target
    `plot` and one without, written before the synonym was folded), the newer one stands.
    """
    raw = state.get(MEMORY)
    entries: list[MemoryEntry] = []
    for item in raw if isinstance(raw, list) else []:
        try:
            entry = MemoryEntry.model_validate(item)
        except ValidationError:
            continue
        if all(entry.id != kept.id for kept in entries):
            entries.append(entry)
    newest = {replace_key(entry.kind, entry.target): entry.id for entry in entries if entry.kind in SINGLE_KINDS}
    entries = [
        entry
        for entry in entries
        if entry.kind not in SINGLE_KINDS or newest[replace_key(entry.kind, entry.target)] == entry.id
    ]
    return entries[:MAX_ENTRIES]


def memory_written(state: Any) -> bool:
    """Whether the session's memory ever held an entry: the id counter moved past 1 (ids are never reused).

    From then on the visible memory is what stands and travels: the raw lineage requests, the fallback of a
    session that never remembered anything, never come back, also after the user removed every entry (owner
    decision of 2026-11-02: what the user removed must not come back through the back door).
    """
    stored = state.get(MEMORY_SEQ)
    return isinstance(stored, int) and not isinstance(stored, bool) and stored > 1


def next_seq(state: Any, entries: Sequence[MemoryEntry]) -> int:
    """The number of the next id: the stored counter, never below one past the highest id in use."""
    stored = state.get(MEMORY_SEQ)
    floor = max((int(entry.id[1:]) for entry in entries), default=0) + 1
    return max(stored, floor) if isinstance(stored, int) and not isinstance(stored, bool) else floor


_CLOSING_PUNCTUATION = ".,;:!?…"


def same_wording(text: str) -> str:
    """An instruction as `remember` compares it: case folded, spacing collapsed, closing punctuation set aside."""
    return " ".join(text.split()).rstrip(_CLOSING_PUNCTUATION + " ").casefold()


def remember(entries: Sequence[MemoryEntry], item: RememberItem, *, seq: int, turn: int) -> list[MemoryEntry]:
    """The entries with `item` added as entry `m{seq}`; a single-valued kind replaces the entry of the same kind and
    target (`replace_key`). Raises `MemoryRefused("memory_full")` past a cap.

    The same decision under the same kind and target is no new one: the entries stay as they are, so a
    decision handed over twice never fills the memory with copies. The instruction counts as the same when
    it differs only in case, spacing or a closing punctuation mark (`same_wording`: "Red star markers." and
    "red  star markers"), which the root's words for one wish vary in from turn to turn. The verbatim text
    the plot shows (`expect`) must match exactly: a title written in other capitals is another title.
    """
    key = replace_key(item.kind, item.target)
    for entry in entries:
        if (replace_key(entry.kind, entry.target), entry.expect) == (key, item.expected_text) and same_wording(
            entry.text
        ) == same_wording(item.text):
            return list(entries)
    # A correction names the entry it corrects; one that is gone already (the user removed it) corrects nothing.
    kept = [entry for entry in entries if entry.id != item.replaces]
    if item.kind in SINGLE_KINDS:
        kept = [entry for entry in kept if replace_key(entry.kind, entry.target) != key]
    entry = MemoryEntry(
        id=f"m{seq}", kind=item.kind, target=item.target, text=item.text, expect=item.expected_text, turn=turn
    )
    after = [*kept, entry]
    if len(after) > MAX_ENTRIES or sum(len(each.text) for each in after) > MAX_TOTAL_CHARS:
        raise MemoryRefused("memory_full")
    return after


@dataclass(frozen=True)
class Planned:
    """The memory after a run's `remember` items: the entries, the next id's number, and how many items found no room."""

    entries: list[MemoryEntry]
    seq: int
    refused: int


def plan(entries: Sequence[MemoryEntry], items: Sequence[RememberItem], *, seq: int, turn: int) -> Planned:
    """`entries` with every item applied in order (`remember`); an item past a cap is left out and counted."""
    after = list(entries)
    refused = 0
    for item in items:
        try:
            updated = remember(after, item, seq=seq, turn=turn)
        except MemoryRefused:
            refused += 1
            continue
        if updated != after:
            seq += 1
        after = updated
    return Planned(after, seq, refused)


def _standing(entry: MemoryEntry, below: int) -> bool:
    """Whether the entry was there before the run whose first new id is `m{below}` (ids are never reused)."""
    return int(entry.id[1:]) < below


def _words(text: str) -> set[str]:
    """The words of a text, case folded, by Unicode word characters: no list of any language's words."""
    return set(re.findall(r"\w+", text.casefold()))


def _replacing_text(entry: MemoryEntry, expect: str, new: str, group: ShownGroup) -> str:
    """The instruction of the entry that replaces `entry`: its own with the new verbatim text in place of the old, so
    the rest of the decision stands ("bold title: ..."), when the old text stands in it exactly once, the rest of the
    instruction shares no word with the old text, and the result fits; else the plain form of that part
    (`SLOT_TEXTS`). A rest that shares a word may point into the old text ("with 2030 in bold" under a title that
    held 2030), which the new text may not have, so the plain form stands then, at the cost of a modifier such as
    "bold"."""
    if entry.text.count(expect) == 1 and not _words(entry.text.replace(expect, " ")) & _words(expect):
        text = entry.text.replace(expect, new)
        if len(text) <= MAX_TEXT_CHARS:
            return text
    return SLOT_TEXTS[group].format(text=new)


def _still_drawn(drawn: DrawnTexts, expect: str) -> bool:
    """Whether the render still draws an entry's verbatim text as the whole of one drawn text, in its part or in any
    other (`grounding.whole_text_as`): a title drawn as a free text above the axes is no title to matplotlib's probe,
    yet still the plot's title, while a text that only stands inside a longer one (an old title the user lengthened)
    is no longer drawn."""
    return whole_text_as(drawn, None, expect)


def replace_drawn(
    planned: Planned, expected: Sequence[str], drawn: DrawnTexts | None, *, standing_below: int, turn: int
) -> Planned:
    """The memory a shipped run leaves once its render replaced a standing title, subtitle or x or y axis label.

    An entry from before the run (numbered below `standing_below`) of a part `SLOT_GROUPS` names, with a verbatim
    text, is replaced when the render no longer draws that text as the whole of any drawn text (`_still_drawn`), and
    draws exactly one of `expected`, the texts the user wrote for this run, as the whole text of that part
    (`grounding.whole_text_in`) and as the part's only text, or, for the title, as the figure title (`suptitle`). The
    new entry has the same kind and target and the drawn text, through `remember`, so a cap refuses it and the old entry
    stands. The root's `remember` items replace only when they come, and a title that arrived in the request alone left
    the old title standing, to be drawn again by a later change. A title the user lengthened ("Q3 sales" to "Q3 sales
    2031") no longer draws the old text whole, so it replaces the entry too. An entry whose text is a number-format
    example (`grounding.format_unit`, "12,5 %") stands for tick labels, never for a part's whole text, so it is never
    replaced.

    The roles are the probe's: where a library's probe reports no subtitle role (matplotlib's) a subtitle entry is
    never replaced, and where it reports the title and the axis labels as other texts (plotnine's) no entry is.

    Nothing here creates an entry: an empty memory stays empty, so whether the memory was ever written
    (`memory_written`) never changes. A render without a complete report of its drawn texts changes nothing.
    """
    if drawn is None or not drawn.complete or not expected:
        return planned
    items: list[RememberItem] = []
    for entry in planned.entries:
        group = SLOT_GROUPS.get(replace_key(entry.kind, entry.target))
        if group is None or entry.expect is None or not _standing(entry, standing_below):
            continue
        if format_unit(entry.expect) is not None or _still_drawn(drawn, entry.expect):
            continue
        filling = list(dict.fromkeys(text for text in expected if whole_text_in(drawn, group, text)))
        if len(filling) != 1:
            continue
        new = filling[0]
        # A role can hold several texts: matplotlib reports a figure title (`suptitle`) and an axes title both as
        # `title`, a figure of several panels draws a title or an axis label per panel, and a second y axis (`twinx`) a
        # second y label. Which of them is the entry's part is not known then, so only the figure title stands for the
        # plot's title, and no other part of such a role is replaced.
        if len(drawn.groups.get(group, [])) > 1 and not (group == "title" and whole_text_as(drawn, "suptitle", new)):
            continue
        try:
            items.append(
                RememberItem(
                    kind=entry.kind,
                    target=entry.target,
                    text=_replacing_text(entry, entry.expect, new, group),
                    expected_text=new,
                )
            )
        except ValidationError:
            continue
    if not items:
        return planned
    after = plan(planned.entries, items, seq=planned.seq, turn=turn)
    return Planned(after.entries, after.seq, planned.refused)


def not_drawn(
    entries: Sequence[MemoryEntry],
    drawn: DrawnTexts | None,
    *,
    standing_below: int,
    language: str,
    written_in: Mapping[int, str],
) -> list[str]:
    """The ids of the entries from before the run (numbered below `standing_below`) whose verbatim text a complete
    report of the shipped render does not draw (`grounding.draws`), in the memory's order: they stay in the memory,
    and the plot's card lists them as not used rather than kept.

    An entry without a verbatim text counts as kept, as does every entry when the report is missing or left texts
    out. So does an entry written while the plot had another language than `language`, the run's, or one whose
    language is unknown: `written_in` maps each turn to the plot language of the version it shipped, and a language
    change rewrites the title and labels, so the old verbatim text is gone for a reason the user chose.
    """
    if drawn is None or not drawn.complete:
        return []
    ids: list[str] = []
    for entry in entries:
        if entry.expect is None or not _standing(entry, standing_below):
            continue
        written = written_in.get(entry.turn)
        if written is None or not same_language(written, language):
            continue
        if not draws(drawn, entry.expect):
            ids.append(entry.id)
    return ids


def forget(entries: Sequence[MemoryEntry], entry_id: str) -> list[MemoryEntry]:
    """The entries without `entry_id`; raises `MemoryRefused("unknown_entry")` when no entry has it."""
    if all(entry.id != entry_id for entry in entries):
        raise MemoryRefused("unknown_entry")
    return [entry for entry in entries if entry.id != entry_id]


def memory_delta(entries: Sequence[MemoryEntry], seq: int | None = None) -> dict[str, Any]:
    """The state delta that stores `entries` (and the next id's number, when given)."""
    delta: dict[str, Any] = {MEMORY: [entry.model_dump(mode="json") for entry in entries]}
    if seq is not None:
        delta[MEMORY_SEQ] = seq
    return delta


def decision_lines(entries: Sequence[MemoryEntry]) -> list[str]:
    """The entries as the adapter and the reviewer read them, oldest first: the text alone, which names the part of
    the plot it is about ("x-axis label: ...")."""
    return [entry.text for entry in entries]


def expected_texts(entries: Sequence[MemoryEntry]) -> list[str]:
    """The verbatim texts the entries put in the plot, at most `MAX_EXPECTED_TEXTS`: the newest when there are more,
    in the entries' order, each once."""
    texts: list[str] = []
    for entry in reversed(entries):
        if entry.expect is not None and entry.expect not in texts:
            texts.append(entry.expect)
    return texts[:MAX_EXPECTED_TEXTS][::-1]


def newer_than(entries: Sequence[MemoryEntry], turn: int | None) -> int:
    """How many entries were written after `turn`, the turn of a plot's latest version; all of them without one."""
    if turn is None:
        return len(entries)
    return sum(1 for entry in entries if entry.turn > turn)


def kind_counts(entries: Sequence[MemoryEntry]) -> dict[str, int]:
    """The number of entries of each kind, for the usage telemetry: never a text."""
    return dict(sorted(Counter(entry.kind for entry in entries).items()))


def public_entries(entries: Sequence[MemoryEntry]) -> list[dict[str, Any]]:
    """The entries as the page lists them (`GET /v1/sessions/{sid}/memory`)."""
    return [entry.model_dump(mode="json") for entry in entries]
