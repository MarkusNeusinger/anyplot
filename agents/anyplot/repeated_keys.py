"""The server's data step for a key the rows repeat, before a plot run draws them.

Owner decision of 2026-11-09: the plot draws every row it gets, and a change of the rows goes only through the
data step. A spec that draws one value per key (`data/fidelity.py`, `KEY_ROLES`) cannot draw rows that share a key
as they are, and its plot code, asked by the prompt to draw each of them, still averaged them per key itself in 2 of
2 measured runs, without a count. So a plot run whose data repeats a key first makes the aggregate the root offers
on the repeated-key warning: the same `aggregate` operation of `prepare_data`, applied by the same server code and
stored as the session's next data version (`dataset_versions.push_version`), so it carries a number, shows on the
data card with its change line and `.undo()` brings the rows back. The run then draws every row of that version, and
its result announces the step with its counts (`fidelity.combined_line`, the first line of `changes`).

Which function and when nothing is combined is `fidelity.key_aggregate`'s rule. The step runs only on data the user
confirmed with complete bindings (a run starts only then), and only when the aggregate leaves complete bindings
and no repeated key, so the user's confirmation moves to the new version with the same bindings, as a narrowed
binding moves it (`session_state.narrowed_confirmation`). An earlier data step leaves no repeat, so a run on it
combines nothing more. No ADK import.
"""

import logging
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from .data.bindings import carry_bindings, check_bindings, valid_bindings
from .data.fidelity import KeyAggregate, combined_line, key_aggregate
from .data.parse import ParseError
from .data.prepare import PrepareArgs, PrepareError, apply_and_parse
from .data.store import DatasetStore, StoredDataset, StoreFull
from .dataset_versions import DatasetVersion, push_version
from .session_state import CONFIRMED, SessionView, confirmation_fingerprint


logger = logging.getLogger("anyplot.agents")


@dataclass(frozen=True)
class Combined:
    """A repeated key the server combined: the new version, the aggregate, the line the plot result announces it with
    (`line`) and the version's own change lines (`changes`), as `prepare_data` stores them."""

    version: DatasetVersion
    aggregate: KeyAggregate
    line: str
    changes: list[str]

    def delta(self) -> dict[str, Any]:
        """The state delta that makes the version current and moves the user's confirmation to it."""
        return {
            **self.version.delta,
            CONFIRMED: confirmation_fingerprint(self.version.dataset_id, self.version.bindings),
        }


def combine_repeated_key(
    store: DatasetStore, session_id: str, view: SessionView, dataset: StoredDataset
) -> Combined | None:
    """The aggregate of a repeated key stored as the next data version, or None when there is nothing to combine.

    None also when `fidelity.key_aggregate` combines nothing, when the aggregate fails or would leave bindings that
    do not hold or would move, or when the store is full: the run then draws the data as it is, and the warning
    stands. Nothing is stored in those cases. The caller writes `Combined.delta` into the session state.
    """
    roles = view.snapshot.roles()
    check = check_bindings(view.bindings, roles, dataset.profile)
    if check.repeated_key is None or not view.data_confirmed:
        return None
    aggregate = key_aggregate(valid_bindings(view.bindings, roles, dataset.profile), check.repeated_key, view.spec_id)
    if aggregate is None:
        return None
    try:
        args = PrepareArgs.model_validate({"operations": [aggregate.operation]})
        prepared, parsed = apply_and_parse(dataset.as_parsed(), args.operations, language=view.language)
    except (ValidationError, PrepareError, ParseError) as exc:
        # The operation is built from valid bindings of number columns, so a refusal here is a bug: the run goes on
        # with the data as it is. The class only: a refusal's message names the user's columns.
        logger.warning("repeated key not combined: %s", type(exc).__name__)
        return None
    after = check_bindings(view.bindings, roles, parsed.profile)
    if not after.complete or after.errors or after.repeated_key is not None:
        return None
    # The bindings `push_version` will carry, computed the same way before anything is stored: the confirmation moves
    # only to the bindings the user confirmed, so a table on which they would move is left as it is.
    carried = carry_bindings(
        view.bindings, roles, parsed.profile, dataset.profile, prepared.converted, prepared.row_numbers, prepared.splits
    )
    if carried != view.bindings:
        logger.warning("repeated key not combined: the bindings would move")
        return None
    number = view.next_version
    line = combined_line(aggregate, dataset.profile.rows, parsed.profile.rows, number)
    try:
        version = push_version(
            store,
            session_id,
            view,
            parsed,
            view.snapshot,
            converted=prepared.converted,
            row_numbers=prepared.row_numbers,
            splits=prepared.splits,
            changes=prepared.changes,
        )
    except StoreFull:
        return None
    return Combined(version, aggregate, line, list(prepared.changes))
