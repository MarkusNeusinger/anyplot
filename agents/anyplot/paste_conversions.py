"""The `certain` conversions for open roles, made by the server on the summary turn of a paste.

When the bindings of a paste leave a required role open, `data/conversions.py` lists what
would fill it, and a `certain` line reads every cell and guesses nothing. The root used to
make such a line with its own `prepare_data` call in the summary turn, and in the prep eval
it did not: it skipped the owed date column, or made it and dropped it again as one the user
had not asked for (`en-note-rename-year-column`, 3 of 3 runs under two prompt wordings). A
column that reads without a guess is the code's to convert ("convert, don't stall"), so the
root's before-agent callback (`agent.make_paste_conversions`) makes the lines here, before
the root's first model call, and the root only names them.

* Only on the summary turn of a fresh paste (the summary action, or the note sent with the
  paste), after the scope guard: a refused note changes nothing, and the new columns are
  named in the session language the note may just have set. A later turn never makes a line
  by itself, also after an undo.
* Only `certain` lines: an `uncertain` one is still the root's one question, a `date_number`
  offer still waits for the user's request (it is never `certain`), and the dry runs keep
  ids, codes and spans of years text and leave a guessed day and month order or decimal mark
  `uncertain` (`conversions.candidates`).
* Their operations go through the same path as the root's (`prepare.apply_and_parse`), all
  into one new data version, so one `.undo()` takes back exactly these conversions; the
  originals stay beside the new columns, and `carry_bindings` binds the new columns to the
  open roles. The change lines join the turn's (`RequestLedger.dataset_changes`), so the
  `done` event shows them as it shows the root's.
* The version is still the paste the root has not summarized (`SUMMARY_PENDING` moves to
  it), and `CONVERSIONS_MADE` keeps the lines for the session block (`Candidate.made`): the
  root names each in the summary, with its count and the new column's name.

No ADK import.
"""

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from pydantic import TypeAdapter

from .data.bindings import check_bindings
from .data.conversions import Candidate, DateNumbers, RangeSplit, RowNumbers, candidates
from .data.parse import ParseError
from .data.prepare import MAX_OPERATIONS, Operation, PrepareError, apply_and_parse
from .data.store import DatasetStore, StoreFull
from .dataset_versions import DatasetVersion, push_version
from .session_state import CONVERSIONS_MADE, SUMMARY_PENDING, CatalogueSnapshot, ConversionsMade, SessionView
from .telemetry import ConversionOutcome


logger = logging.getLogger(__name__)

_OPERATIONS = TypeAdapter(list[Operation])

Line = Candidate | RangeSplit | RowNumbers


@dataclass(frozen=True)
class MadeConversions:
    """The conversions the server made on a paste: the new version, its state delta and what the turn reports."""

    version: DatasetVersion
    record: ConversionsMade
    changes: list[str]
    """The change lines of the operations, as `prepare_data` returns them, for the `done` event."""
    outcome: ConversionOutcome
    """What the turn made for an open role, for the `chat_turn` telemetry line (`outcome`)."""

    def delta(self) -> dict[str, Any]:
        """The new version, still the paste the root summarizes now, with the record for the session block."""
        return {
            **self.version.delta,
            SUMMARY_PENDING: self.version.dataset_id,
            CONVERSIONS_MADE: self.record.model_dump(),
        }


def certain_lines(found: Sequence[Line | DateNumbers]) -> list[Line]:
    """The lines the server makes: every `certain` one, in the order listed (a `DateNumbers` offer never is)."""
    return [line for line in found if not isinstance(line, DateNumbers) and line.certain]


def batches(lines: Sequence[Line]) -> list[list[dict[str, Any]]]:
    """The lines' operations in calls of at most `MAX_OPERATIONS`, a line never split across two calls."""
    out: list[list[dict[str, Any]]] = []
    for line in lines:
        operations = line.operations()
        if not out or len(out[-1]) + len(operations) > MAX_OPERATIONS:
            out.append([])
        out[-1].extend(operations)
    return out


def make_conversions(
    store: DatasetStore, session_id: str, view: SessionView, snapshot: CatalogueSnapshot
) -> MadeConversions | None:
    """Make every `certain` conversion line of the current data as one new version, or None when none is due.

    The caller decides that this is the summary turn of a paste and writes `MadeConversions.delta`. The lines are
    the ones the session block would list for this data, language and bindings (`conversions.candidates`, with the
    stored dry runs), so they are made exactly as listed. A refusal of the operations or a full store makes
    nothing: the lines stay listed, and the root asks about them as about an `uncertain` one.
    """
    stored = store.get(view.dataset_id, session_id) if view.dataset_id else None
    if stored is None:
        return None
    roles = snapshot.roles()
    if not check_bindings(view.bindings, roles, stored.profile).missing_roles:
        return None
    found = candidates(
        view.bindings,
        roles,
        stored.profile,
        stored.as_parsed(),
        language=view.language,
        keep_text=stored.text_columns,
        cache=stored.dry_runs,
    )
    lines = certain_lines(found)
    if not lines:
        return None
    parsed = stored.as_parsed()
    operations: list[dict[str, Any]] = []
    changes: list[str] = []
    converted: dict[str, str] = {}
    row_numbers: list[str] = []
    splits: list[list[str]] = []
    try:
        # More than `MAX_OPERATIONS` take two calls in a row, as two `prepare_data` calls would, into one version.
        for batch in batches(lines):
            prepared, parsed = apply_and_parse(parsed, _OPERATIONS.validate_python(batch), language=view.language)
            operations += batch
            changes += prepared.changes
            converted.update(prepared.converted)
            row_numbers += prepared.row_numbers
            splits += prepared.splits
        version = push_version(
            store, session_id, view, parsed, snapshot, converted=converted, row_numbers=row_numbers, splits=splits
        )
    except (PrepareError, ParseError, StoreFull) as exc:
        # A dry run said every cell reads, so a refusal here is a bug, and a full store a capacity limit: the turn
        # goes on with the lines listed. The class only: a refusal's message names the user's columns.
        logger.warning("paste conversions not made: %s", type(exc).__name__)
        return None
    record = ConversionsMade(
        dataset_id=version.dataset_id, lines=[line.made() for line in lines], operations=operations
    )
    return MadeConversions(version, record, changes, outcome(lines))


def outcome(lines: Sequence[Line]) -> ConversionOutcome:
    """The turn's one conversion outcome for the telemetry, ranked as `prepare_data` ranks it: row numbers, then
    dates, then numbers."""
    made = {line.outcome for line in lines}
    return "index" if "index" in made else "date" if "date" in made else "number"
