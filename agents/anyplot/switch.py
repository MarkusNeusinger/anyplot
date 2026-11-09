"""A switch of the plot's target, the (spec, library) pair, and what carries over to the new one.

Owner decision of 2026-11-02: a plot switched to another library must not start from zero. The
switch route (`POST /v1/sessions/{sid}/library`) keeps the data, the bindings, the confirmation,
the language, the kept first-plot note, the versions and the plot memory (`memory.py`), and writes
the carry (`CARRY`): the theme the user asked for and the texts the plot must show, taken from the
source's latest plot. The first run in the new target consumes it the way a run takes the kept
first-plot note (`pipeline.take_pending_request`): it starts from the new library's catalogue code
(`previous` stays None, so the new-plot literal budget, the new library's hints and no language
rewrite apply), takes its standing decisions from the memory (or, with an empty memory, from the
source lineage's requests in `Carry.requests`), renders in the carried theme when the user asked
for it, and checks the carried texts. A shipped run in the target clears the carry; one that ships
nothing keeps it for the next. A new data version (a paste, a change, `.to_long()`, an undo) drops it,
as it drops the kept first-plot note (owner decision of 2026-11-08): its texts and theme came from a
plot of the data before. A switch after the data changed carries only the asked theme of such a plot,
never its texts or requests (`source_plot`).

The switch answer (`SwitchSummary`) says how much would carry and whether the target already
has a plot. Switching back to a library with an older version would resume a stale lineage,
so `newer` counts the memory entries written after the target's latest version: above zero,
the page offers the carry run (`carry_plot`) instead of resuming silently.

The target is a pair from day one: today the route refuses another spec (`422 invalid`), and the
later plot-type switch (a box plot to a violin) lifts that refusal and reuses everything here.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Any

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, ValidationError

from core.constants import SUPPORTED_LIBRARIES

from .memory import MemoryEntry, decision_lines, expected_texts, newer_than
from .schemas import (
    EXPECTED_TEXT,
    MAX_CHANGE_REQUEST_CHARS,
    MAX_EXPECTED_TEXTS,
    MAX_USER_REQUESTS,
    ExpectedText,
    Theme,
    UserRequest,
)


if TYPE_CHECKING:
    from .services import CodeVersion


def _library(value: str) -> str:
    if value not in SUPPORTED_LIBRARIES:
        raise ValueError("not a supported library")
    return value


CARRY = "anyplot.carry"
"""The carry of the latest switch (`Carry`), or None; written by the switch route, cleared by a shipped run and by
every new data version (`opening.IngestedDataset.state_delta`, `dataset_versions`)."""


class Target(BaseModel):
    """A (spec, library) pair: what the session adapts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    spec_id: str = Field(pattern=r"^[a-z0-9-]{1,100}$")
    library: Annotated[str, AfterValidator(_library)]

    def pair(self) -> tuple[str, str]:
        return (self.spec_id, self.library)


class Carry(BaseModel):
    """What the first run in `target` takes from the plot the user tuned in `source`."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source: Target
    target: Target
    from_plot: bool = False
    """The source had a rendered plot when the user switched (else only the memory carries)."""
    theme: Theme | None = None
    """The source plot's theme when the user asked for it there (`CodeVersion.theme_asked`); None otherwise, so the
    run follows the site theme like any first plot."""
    expected_texts: list[ExpectedText] = Field(default_factory=list, max_length=MAX_EXPECTED_TEXTS)
    """The texts the run checks the render for, unless it brings texts of its own."""
    requests: list[UserRequest] = Field(default_factory=list, max_length=MAX_USER_REQUESTS)
    """The source lineage's standing requests (`CodeVersion.requests`): the decisions of a run whose memory is
    empty, the fallback the raw request list has always been."""


def read_carry(state: Any, target: tuple[str, str]) -> Carry | None:
    """The carry made for `target`, validated; None when there is none, it was made for another pair, or it fails."""
    raw = state.get(CARRY)
    if not isinstance(raw, dict):
        return None
    try:
        carry = Carry.model_validate(raw)
    except ValidationError:
        return None
    return carry if carry.target.pair() == target else None


@dataclass(frozen=True)
class SourcePlot:
    """What the switch reads of the source's latest rendered version (`services.CodeVersion`)."""

    theme: Theme
    theme_asked: bool
    expected_texts: list[str]
    requests: list[str]


def source_plot(version: CodeVersion | None, data_version: int | None = None) -> SourcePlot | None:
    """What a carry reads of the source's latest rendered version, or None without one.

    When the version drew another data version than `data_version`, the session's current one, only its theme
    carries: its texts and requests were written for that data, and a new data version drops them as it drops a
    carry made before it, while the theme the user asked for is no fact of the data, as "plot the new data" keeps it
    too (owner decisions of 2026-11-08). The plot memory, which only the user clears, still carries (`carry_for`).
    """
    if version is None:
        return None
    same_data = data_version is None or version.drew(data_version)
    return SourcePlot(
        theme=version.theme,
        theme_asked=version.theme_asked,
        expected_texts=list(version.expected_texts) if same_data else [],
        requests=list(version.requests) if same_data else [],
    )


def carry_for(
    *, source: Target, target: Target, plot: SourcePlot | None, pending: Carry | None, memory: Sequence[MemoryEntry]
) -> Carry | None:
    """The carry a switch from `source` to `target` writes, or None when nothing would carry.

    The source's latest plot carries its asked-for theme, its texts (the memory's verbatim texts when
    the memory has entries, `memory.expected_texts`, else the version's own) and its lineage's requests.
    Without a plot in the source, a carry the user has not run yet moves on to the new target (a
    switch from A to B and on to C before any run in B carries A's plot to C); without either, a
    memory with entries carries alone.
    """
    if plot is not None:
        texts = expected_texts(memory) if memory else _valid_texts(plot.expected_texts)
        return Carry(
            source=source,
            target=target,
            from_plot=True,
            theme=plot.theme if plot.theme_asked else None,
            expected_texts=texts,
            requests=[r for r in plot.requests if 0 < len(r) <= MAX_CHANGE_REQUEST_CHARS][-MAX_USER_REQUESTS:],
        )
    if pending is not None:
        # Also back to its own source (A to B to A, no run in B): A's plot then counts the memory's newer entries,
        # and a carry run there, offered only for those, keeps the theme the user asked for in A.
        texts = expected_texts(memory) if memory else list(pending.expected_texts)
        return pending.model_copy(update={"target": target, "expected_texts": texts})
    if memory:
        return Carry(source=source, target=target, expected_texts=expected_texts(memory))
    return None


def _valid_texts(texts: Sequence[str]) -> list[str]:
    """The texts that pass `ExpectedText`, each once, at most `MAX_EXPECTED_TEXTS`."""
    kept: list[str] = []
    for text in texts:
        try:
            valid = EXPECTED_TEXT.validate_python(text, strict=True)
        except ValidationError:
            continue
        if valid not in kept:
            kept.append(valid)
    return kept[:MAX_EXPECTED_TEXTS]


@dataclass(frozen=True)
class SwitchSummary:
    """The switch answer's `carry`: what a carry run would hand over, and whether the page should offer it."""

    decisions: int
    """The standing decisions a carry run hands the adapter: the memory's entries, else the carried requests."""
    newer: int
    """Memory entries written after the target's latest version (all of them when the target has none)."""
    target_has_plot: bool
    from_plot: bool
    offer: bool
    """The page offers the carry run: something carries, and the target has no plot or its plot misses newer
    decisions; otherwise the target's own latest plot is current and the switch simply shows it."""

    def body(self) -> dict[str, Any]:
        return {
            "decisions": self.decisions,
            "newer": self.newer,
            "target_has_plot": self.target_has_plot,
            "from_plot": self.from_plot,
            "offer": self.offer,
        }


def summary(
    carry: Carry | None, memory: Sequence[MemoryEntry], target_turn: int | None, *, written: bool = False
) -> SwitchSummary:
    """The switch answer's carry summary; `target_turn` is the turn of the target's latest version, None without one.

    `written` (`memory.memory_written`): once the session's memory ever held an entry, its entries are the decisions
    that travel, also none; the carry's raw requests count only for a session that never remembered anything, as the
    run reads them (`pipeline.Run.raw_requests`).
    """
    raw = len(carry.requests) if carry and not written else 0
    decisions = len(decision_lines(memory)) if memory or written else raw
    newer = newer_than(memory, target_turn)
    has_plot = target_turn is not None
    carries = carry is not None and (decisions > 0 or carry.from_plot)
    offer = carries and (not has_plot or newer > 0)
    return SwitchSummary(
        decisions=decisions,
        newer=newer,
        target_has_plot=has_plot,
        from_plot=bool(carry and carry.from_plot),
        offer=offer,
    )
