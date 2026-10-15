"""Dataset versions of a session: `prepare_data` or `generate_data` stores the next, `undo` restores the previous.

The design is docs/concepts/agent-network.md, "Two steps: data first, then the plot":
the model never writes data rows; the server applies the operations it chose to the
stored canonical CSV, re-parses the result and stores it as the next dataset version
with a change list, and the user can undo. The state keys (`session_state.py`):

* `DATASET_ID` is the current version; `DATASET_HISTORY` holds the ids of the versions
  before it, oldest first, at most `MAX_DATASET_HISTORY` (a version pushed out at the
  front is deleted from the store); `DATASET_VERSION` numbers the current version
  (1 for a paste, one more per `prepare_data`, one less per undo), so a number above
  1 means there is a version to undo. A new paste starts over (`IngestedDataset`).
* The bindings follow the data through `carry_bindings`: the ones still valid for the
  new profile stay, the roles left without one get the defaults. A generated table
  (`generate_data`) replaces the data rather than changing it, so its version starts
  from the defaults (`push_version(rebind=True)`). The confirmation
  (`CONFIRMED`) names the dataset id, so a new version is unconfirmed by itself; an
  undo clears it, because the restored version's id could match a confirmation given
  before the change.
* The notes pasted with the data (`StoredDataset.context_lines`) travel with every version
  made from it (`push_version`); a new paste replaces them, an undo restores the version's own.
  The dropped file's name (`StoredDataset.file_name`) travels the same way.

`dataset_payload` is the shape every dataset answer shares: the `/dataset` and
`/dataset/undo` routes (plus `roles`) and the `done` event's `dataset` (plus
`changes`). No ADK import.
"""

from dataclasses import dataclass, replace
from typing import Any

from .data.bindings import carry_bindings, default_bindings
from .data.parse import ParsedDataset
from .data.store import DatasetStore, StoredDataset
from .schemas import Binding
from .session_state import (
    BINDINGS,
    CONFIRMED,
    DATASET_HISTORY,
    DATASET_ID,
    DATASET_VERSION,
    PENDING_CLEARED,
    CatalogueSnapshot,
    SessionView,
)


MAX_DATASET_HISTORY = 5
"""How many earlier versions a session keeps for undo (the design's "last five versions")."""


@dataclass(frozen=True)
class DatasetVersion:
    """A version that just became the session's current dataset, with the state delta that makes it so."""

    dataset_id: str
    stored: StoredDataset
    bindings: list[Binding]
    version: int
    delta: dict[str, Any]

    def payload(self) -> dict[str, Any]:
        return dataset_payload(self.stored, self.bindings, self.version)


def dataset_payload(stored: StoredDataset, bindings: list[Binding], version: int) -> dict[str, Any]:
    """`{preview, profile, bindings, warnings, context_lines, version}`: a dataset as the routes and `done` answer it,
    plus `code` for a version `run_data_code` computed (the Python that ran)."""
    payload: dict[str, Any] = {
        "preview": [list(row) for row in stored.preview],
        "profile": stored.profile.model_dump(mode="json"),
        "bindings": [binding.model_dump() for binding in bindings],
        "warnings": list(stored.profile.warnings),
        "context_lines": list(stored.context_lines),
        "version": version,
    }
    if stored.code is not None:
        payload["code"] = stored.code
    if stored.file_name is not None:
        payload["file_name"] = stored.file_name
    return payload


def push_version(
    store: DatasetStore,
    session_id: str,
    view: SessionView,
    parsed: ParsedDataset,
    snapshot: CatalogueSnapshot,
    *,
    rebind: bool = False,
    code: str | None = None,
    source: str | None = None,
) -> DatasetVersion:
    """Store `parsed` as the session's next dataset version; raises `StoreFull` (nothing changes then).

    The current dataset joins the history; the oldest entries past `MAX_DATASET_HISTORY`
    leave the store. The bindings are carried over (`carry_bindings`) for a change of the
    data (`prepare_data`); `rebind` gives the defaults for the new profile instead
    (`default_bindings`), for a table that replaces the data (`generate_data`), where a
    choice made for the old columns says nothing about the new ones even when a name
    such as `x` returns.

    The notes pasted with the data (`context_lines`) belong to the session's data, not to one
    version: the new version carries the current version's notes, also after `generate_data`.
    `source` says where a computed table comes from (`dataset_context`); without one, a change
    of the data (`prepare_data`) carries the current version's on.
    """
    current = store.get(view.dataset_id, session_id) if view.dataset_id else None
    file_name = None
    if current is not None:
        parsed = replace(parsed, context_lines=list(current.context_lines))
        file_name = current.file_name
        if source is None:
            source = current.source
    # `code` (`run_data_code`'s Python) belongs to this version only, never carried to the next.
    dataset_id = store.put(session_id, parsed, code=code, source=source, file_name=file_name)
    history = [*view.dataset_history, view.dataset_id] if view.dataset_id else list(view.dataset_history)
    for old in history[:-MAX_DATASET_HISTORY]:
        store.delete(old, session_id)
    history = history[-MAX_DATASET_HISTORY:]
    stored = store.get(dataset_id, session_id)
    assert stored is not None  # just stored for this session
    roles = snapshot.roles()
    bindings = (
        default_bindings(roles, stored.profile) if rebind else carry_bindings(view.bindings, roles, stored.profile)
    )
    version = view.dataset_version + 1
    return DatasetVersion(dataset_id, stored, bindings, version, _delta(dataset_id, bindings, history, version))


def undo_version(
    store: DatasetStore, session_id: str, view: SessionView, snapshot: CatalogueSnapshot
) -> DatasetVersion | None:
    """Make the newest history entry the current dataset again, or None when there is nothing to undo.

    The current version leaves the store (there is no redo). The idle sweep takes a
    session's history only together with its current version (`DatasetStore.sweep`),
    so an entry missing from the store means the store was emptied behind the state (a
    restart keeps neither): such an entry is skipped, and the version number drops once
    more for it, so the numbers stay one apart. The restored version is unconfirmed even when the user
    confirmed it before the change it undoes (the fingerprint would match again): what
    is on the screen changed, so the user confirms what they see, as after a paste.
    """
    history = list(view.dataset_history)
    skipped = 0
    while history:
        dataset_id = history.pop()
        stored = store.get(dataset_id, session_id)
        if stored is not None:
            break
        skipped += 1
    else:
        return None
    if view.dataset_id:
        store.delete(view.dataset_id, session_id)
    bindings = carry_bindings(view.bindings, snapshot.roles(), stored.profile)
    version = max(1, view.dataset_version - 1 - skipped)
    delta = {**_delta(dataset_id, bindings, history, version), CONFIRMED: None}
    return DatasetVersion(dataset_id, stored, bindings, version, delta)


def _delta(dataset_id: str, bindings: list[Binding], history: list[str], version: int) -> dict[str, Any]:
    """The state of a new current version; a kept plot note (`PENDING_REQUEST`) was written for the data before it."""
    return {
        DATASET_ID: dataset_id,
        BINDINGS: [binding.model_dump() for binding in bindings],
        DATASET_HISTORY: history,
        DATASET_VERSION: version,
        **PENDING_CLEARED,
    }
