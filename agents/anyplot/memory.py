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
kind and target; an entry of a multi-valued kind (`MULTI_KINDS`) is added beside the others and
goes only by its id (`forget`). The caps (`MAX_ENTRIES`, `MAX_TEXT_CHARS`, `MAX_TOTAL_CHARS`)
refuse a new entry (`MemoryRefused("memory_full")`) rather than dropping an old one silently.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Literal, get_args

from pydantic import BaseModel, ConfigDict, Field, ValidationError

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


def read_memory(state: Any) -> list[MemoryEntry]:
    """The entries in `state`, oldest first; an item that fails validation is dropped, never passed on."""
    raw = state.get(MEMORY)
    entries: list[MemoryEntry] = []
    for item in raw if isinstance(raw, list) else []:
        try:
            entry = MemoryEntry.model_validate(item)
        except ValidationError:
            continue
        if all(entry.id != kept.id for kept in entries):
            entries.append(entry)
    return entries[:MAX_ENTRIES]


def next_seq(state: Any, entries: Sequence[MemoryEntry]) -> int:
    """The number of the next id: the stored counter, never below one past the highest id in use."""
    stored = state.get(MEMORY_SEQ)
    floor = max((int(entry.id[1:]) for entry in entries), default=0) + 1
    return max(stored, floor) if isinstance(stored, int) and not isinstance(stored, bool) else floor


def remember(entries: Sequence[MemoryEntry], item: RememberItem, *, seq: int, turn: int) -> list[MemoryEntry]:
    """The entries with `item` added as entry `m{seq}`; a single-valued kind replaces the entry of the same kind and
    target. Raises `MemoryRefused("memory_full")` past a cap.

    The same text under the same kind and target is no new decision: the entries stay as they are, so a
    decision handed over twice never fills the memory with copies.
    """
    for entry in entries:
        same = (entry.kind, entry.target, entry.text, entry.expect)
        if same == (item.kind, item.target, item.text, item.expected_text):
            return list(entries)
    # A correction names the entry it corrects; one that is gone already (the user removed it) corrects nothing.
    kept = [entry for entry in entries if entry.id != item.replaces]
    if item.kind in SINGLE_KINDS:
        kept = [entry for entry in kept if (entry.kind, entry.target) != (item.kind, item.target)]
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
