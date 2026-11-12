"""Dataset versions of a session: `prepare_data` or `generate_data` stores the next, `undo` restores the previous.

The design is docs/concepts/agent-network.md, "Two steps: data first, then the plot":
the model never writes data rows; the server applies the operations it chose to the
stored canonical CSV, re-parses the result and stores it as the next dataset version
with a change list, and the user can undo. The state keys (`session_state.py`):

* `DATASET_ID` is the current version; `DATASET_HISTORY` holds the ids of the versions
  before it, oldest first, at most `MAX_DATASET_HISTORY` (a version pushed out at the
  front is deleted from the store), and there is a version to undo while it holds one
  (`SessionView.can_undo`). A new paste starts the history over (`IngestedDataset`).
* One numbering per session (owner decision of 2026-11-07): every version the session
  stores gets the next number (`SessionView.next_version`, kept on the version as
  `StoredDataset.number`), a paste, an opened file, a copy or a computed table as much as
  a change, and no number is given twice. An undo makes the version it restores current
  with its own number: paste, change, undo, change is 1, 2, 1, 3. The page's card shows
  this number (`data v3`), the session block lists it and `from_version` takes it, so
  "v2" names the same table to the user and to the root. `DATASET_VERSION` is the current
  version's number, `DATASET_TOP` the highest the session gave.
* The bindings follow the data through `carry_bindings`: the ones still valid for the
  new profile stay, the roles left without one get the defaults. A generated table
  (`generate_data`) replaces the data rather than changing it, so its version starts
  from the defaults (`push_version(rebind=True)`). The confirmation
  (`CONFIRMED`) names the dataset id, so a new version is unconfirmed by itself; an
  undo clears it, because the restored version's id could match a confirmation given
  before the change.
* The notes pasted with the data (`StoredDataset.context_lines`) travel with every version
  made from it (`push_version`); a new paste replaces them, an undo restores the version's own.
  The dropped file's name (`StoredDataset.file_name`) travels with a change of the data
  (`prepare_data`, `.to_long()`) and an undo restores the version's own, but a computed
  table (`generate_data`, `run_data_code`) drops it: it is no longer the file's data.
* The root reads and rebuilds from an earlier version (owner decision of 2026-11-06). The
  persona tests of that day had the chat send users to `.undo()` or a new paste: "the
  first 20 after all" after a top 10, the pace per run after a weekly sum. `prepare_data`
  and `query_data` take `from_version` (`FromVersion`): `current` (the default),
  `original` (the first version of the current data: the paste, the opened file, the copy
  or a table computed in a session without data) or a number the session block lists
  (`kept_versions`, `version_lines`). A rebuild applies its operations to that version
  and stores the result as the next version on top, like any change: the history is
  never rewritten, the user confirms the new data, and `.undo()` steps back one version
  as before. Its change lines say where it started (`rebuilt_changes`: "from your
  original table: kept the first 20 of 487 rows, 467 dropped"). The original stays in
  the store also after the history cap pushed it out of `DATASET_HISTORY`
  (`DATASET_ORIGINAL`), so it can always be read, though undo never reaches it there.
  A number that is gone is refused with a closed code (`resolve_version`): one below
  the original's is a version of earlier data, which a new paste replaced
  (`other_paste`); one from it up was undone, left the history or was never given
  (`version_not_kept`).

`dataset_payload` is the shape every dataset answer shares: the `/dataset/undo`,
`/dataset/to_long` and `/dataset/copy` routes (plus `roles`) and the `done` event's
`dataset` (plus `changes`); the paste route answers the same fields. No ADK import.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any, Literal

from .data.bindings import carry_bindings, default_bindings, filled_bindings
from .data.parse import ParsedDataset
from .data.store import DatasetStore, StoredDataset
from .schemas import MAX_NOTE_CHARS, ORIGINAL_VERSION, Binding, FromVersion
from .session_state import (
    BINDINGS,
    CONFIRMED,
    DATASET_HISTORY,
    DATASET_ID,
    DATASET_ORIGINAL,
    DATASET_TOP,
    DATASET_VERSION,
    PENDING_CLEARED,
    CatalogueSnapshot,
    SessionView,
)
from .switch import CARRY


MAX_DATASET_HISTORY = 5
"""How many earlier versions a session keeps for undo (the design's "last five versions"); the original is kept on
top of them (`DATASET_ORIGINAL`)."""
MAX_VERSION_LINE_CHARS = 240
"""A version's line in the session block at most: its change lines joined, cut with `…`. The list itself holds at most
the original, the `MAX_DATASET_HISTORY` versions of the history and the current one."""
ORIGINAL_WORDS = "from your original table"
"""How the change lines of a version rebuilt from the original start (`rebuilt_changes`)."""
VersionRefusal = Literal["other_paste", "version_not_kept"]
"""Why `from_version` names no version the session keeps: a number below the current data's original belongs to
earlier data, which a paste replaced; one from it up was undone (there is no redo), left the history or was never
given."""


class VersionRefused(Exception):
    """`from_version` names no version the session keeps; `code` says why (`VersionRefusal`)."""

    def __init__(self, code: VersionRefusal) -> None:
        super().__init__(code)
        self.code: VersionRefusal = code


@dataclass(frozen=True)
class KeptVersion:
    """A version of the session's current data that the store still holds, with its number."""

    number: int
    stored: StoredDataset
    current: bool
    original: bool


def _original_id(view: SessionView) -> str | None:
    """The id of the first version of the current data (`DATASET_ORIGINAL`). Every route that stores new data writes
    the key; a view built without it takes the current version while nothing stands before it."""
    if view.dataset_original:
        return view.dataset_original
    return view.dataset_id if not view.dataset_history else None


def original_number(store: DatasetStore, session_id: str, view: SessionView) -> int:
    """The session's number of the current data's original, the version `from_version` `original` reads; the current
    number when the store no longer holds it (it was emptied behind the state)."""
    original = _original_id(view)
    stored = store.get(original, session_id) if original else None
    return stored.number if stored is not None else view.dataset_version


def kept_versions(store: DatasetStore, session_id: str, view: SessionView) -> list[KeptVersion]:
    """Every version of the current data the store still holds, oldest first and the current last: the original,
    the history and the current version, each under its number in the session (`StoredDataset.number`).

    The numbers are the ones the data panel's card shows. They grow in the order the versions were made, so the
    oldest comes first also after an undo; an undone number is missing, and nothing that left the store is listed.
    """
    if not view.dataset_id:
        return []
    original = _original_id(view)
    kept: dict[int, KeptVersion] = {}
    for dataset_id in (*view.earlier_datasets, view.dataset_id):
        stored = store.get(dataset_id, session_id)
        if stored is not None:
            current = dataset_id == view.dataset_id
            kept[stored.number] = KeptVersion(stored.number, stored, current, dataset_id == original)
    return [kept[number] for number in sorted(kept)]


def resolve_version(kept: Sequence[KeptVersion], from_version: FromVersion) -> KeptVersion:
    """The version `from_version` names among `kept`; raises `VersionRefused`.

    `current` is the current version and `original` the current data's first; a number names its version. A number
    the session no longer keeps is `other_paste` below the original's number: it was a version of data a paste
    replaced, which is gone with its versions. From the original's number up it is `version_not_kept`: undone, out
    of the history, or a number the session never gave.
    """
    if isinstance(from_version, int):
        found = next((version for version in kept if version.number == from_version), None)
    elif from_version == ORIGINAL_VERSION:
        found = next((version for version in kept if version.original), None)
    else:  # `CURRENT_VERSION`, the one other value the type admits
        found = next((version for version in kept if version.current), None)
    if found is not None:
        return found
    first = next((version.number for version in kept if version.original), None)
    earlier = isinstance(from_version, int) and first is not None and from_version < first
    raise VersionRefused("other_paste" if earlier else "version_not_kept")


def _count(number: int, noun: str) -> str:
    return f"{number:,} {noun}" if number == 1 else f"{number:,} {noun}s"


def _shape(stored: StoredDataset) -> str:
    return f"{_count(stored.profile.rows, 'row')}, {_count(len(stored.profile.columns), 'column')}"


def _clipped(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def rebuilt_changes(base: KeptVersion, changes: Sequence[str]) -> list[str]:
    """The change lines of a call that started from `base`: as they are from the current version; from another one,
    the first line starts with where ("from your original table: kept the first 20 of 487 rows, 467 dropped"), and a
    call without operations says it took that version as it was, with its shape."""
    if base.current:
        return list(changes)
    where = ORIGINAL_WORDS if base.original else f"from version {base.number}"
    if not changes:
        return [f"{where}, as it was: {_shape(base.stored)}"]
    return [_clipped(f"{where}: {changes[0]}", MAX_NOTE_CHARS), *changes[1:]]


def version_lines(kept: Sequence[KeptVersion]) -> list[str]:
    """The session block's line per kept version: its number, `original` or `current`, the change lines that made it
    (cut to `MAX_VERSION_LINE_CHARS`) and its shape: `2: sorted by 'Revenue', descending; kept the first 10 of 30
    rows, 20 dropped → 10 rows, 3 columns`. The change lines name the user's columns: the caller fences them."""
    lines = []
    for version in kept:
        marks = [mark for mark, holds in (("original", version.original), ("current", version.current)) if holds]
        label = f"{version.number} ({', '.join(marks)})" if marks else str(version.number)
        made = "" if version.original else "; ".join(version.stored.changes)
        what = f"{_clipped(made, MAX_VERSION_LINE_CHARS)} → " if made else ""
        lines.append(f"{label}: {what}{_shape(version.stored)}")
    return lines


@dataclass(frozen=True)
class DatasetVersion:
    """A version that just became the session's current dataset, with the state delta that makes it so."""

    dataset_id: str
    stored: StoredDataset
    bindings: list[Binding]
    version: int
    """Its number in the session (`StoredDataset.number`)."""
    delta: dict[str, Any]
    can_undo: bool
    """Whether an undo can follow it: the history it leaves holds a version."""
    original_version: int
    """The number of the current data's original (`original_number`)."""

    def payload(self) -> dict[str, Any]:
        return dataset_payload(
            self.stored, self.bindings, can_undo=self.can_undo, original_version=self.original_version
        )


def dataset_payload(
    stored: StoredDataset, bindings: list[Binding], *, can_undo: bool, original_version: int
) -> dict[str, Any]:
    """`{preview, profile, bindings, warnings, context_lines, version, can_undo, original_version}`: a dataset as the
    routes and `done` answer it, plus `code` for a version `run_data_code` computed (the Python that ran).

    `version` is the version's number in the session (`StoredDataset.number`), which the page's card shows;
    `can_undo` whether `POST .../dataset/undo` has a version to restore (`SessionView.can_undo`), so no client reads
    it from the number; `original_version` the number of the current data's first version, from which a client can
    count how far an undo went back.
    """
    payload: dict[str, Any] = {
        "preview": [list(row) for row in stored.preview],
        "profile": stored.profile.model_dump(mode="json"),
        "bindings": [binding.model_dump() for binding in bindings],
        "warnings": list(stored.profile.warnings),
        "context_lines": list(stored.context_lines),
        "version": stored.number,
        "can_undo": can_undo,
        "original_version": original_version,
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
    pinned: list[Binding] | None = None,
    code: str | None = None,
    source: str | None = None,
    converted: Mapping[str, str] | None = None,
    row_numbers: Sequence[str] = (),
    splits: Sequence[Sequence[str]] = (),
    changes: Sequence[str] = (),
    made_from: StoredDataset | None = None,
) -> DatasetVersion:
    """Store `parsed` as the session's next dataset version, under the session's next number; raises `StoreFull`
    (nothing changes then).

    The current dataset joins the history; the oldest entries past `MAX_DATASET_HISTORY`
    leave the store, except the original, which stays for `from_version` (`DATASET_ORIGINAL`).
    `changes` are the change lines that made the version, which the session block lists
    (`version_lines`); `made_from` is the earlier version a rebuild started from
    (`from_version`), whose notes, file name and source the new version carries instead of the
    current one's. The bindings are carried over (`carry_bindings`) for a change of the
    data (`prepare_data`), a column `converted` by a `set_type` with a new name (each with its
    source) filling the open required role that takes it, two neighbouring parts of one of
    `splits` filling an open lower and upper bound pair, and a column of `row_numbers` the
    role left for them; `rebind` gives the defaults for the new profile instead
    (`default_bindings`), for a table that replaces the data (`generate_data`), where a
    choice made for the old columns says nothing about the new ones even when a name
    such as `x` returns. `pinned` gives those bindings, keeps the current bindings that
    still hold on the kept columns, and the defaults for the other roles (`filled_bindings`),
    for `.to_long()`, which knows the roles its new columns are made for.

    The notes pasted with the data (`context_lines`) belong to the session's data, not to one
    version: the new version carries the current version's notes, also after `generate_data`.
    `source` says where a computed table comes from (`dataset_context`); without one, a change
    of the data (`prepare_data`) carries the current version's on.
    """
    current = store.get(view.dataset_id, session_id) if view.dataset_id else None
    origin = made_from if made_from is not None else current
    file_name = None
    if origin is not None:
        parsed = replace(parsed, context_lines=list(origin.context_lines))
        # The dropped file's name stays with a change of that file's data (`prepare_data`, `.to_long()`); a
        # computed table (`generate_data`, `run_data_code`, which always say where it comes from) is no longer
        # the file's, so the name would mislabel it.
        file_name = origin.file_name if source is None else None
        if source is None:
            source = origin.source
    version = view.next_version
    # `code` (`run_data_code`'s Python) belongs to this version only, never carried to the next.
    dataset_id = store.put(
        session_id, parsed, code=code, source=source, file_name=file_name, changes=changes, number=version
    )
    original = _original_id(view)
    kept_original = store.get(original, session_id) if original else None
    history = [*view.dataset_history, view.dataset_id] if view.dataset_id else list(view.dataset_history)
    for old in history[:-MAX_DATASET_HISTORY]:
        if old != original:  # past the undo history, but still the version `from_version` `original` reads
            store.delete(old, session_id)
    history = history[-MAX_DATASET_HISTORY:]
    stored = store.get(dataset_id, session_id)
    assert stored is not None  # just stored for this session
    roles = snapshot.roles()
    # The version the carried bindings were made on, the current one also for a rebuild: a date column it did not have
    # fills an open required date role (`carry_bindings`), so a date column a rebuild brings back takes the role the
    # drop left open, as one the change made would.
    previous = current.profile if current is not None else None
    if pinned is not None:
        # The user's bindings on the kept columns stay (review of #12206: `.to_long()` dropped them for the
        # defaults); a role or a column the pinned bindings take is theirs, and a melted column is gone anyway.
        pinned_roles = {binding.role for binding in pinned}
        pinned_columns = {binding.column for binding in pinned}
        carried = [
            binding
            for binding in view.bindings
            if binding.role not in pinned_roles and binding.column not in pinned_columns
        ]
        bindings = filled_bindings([*pinned, *carried], roles, stored.profile)
    elif rebind:
        bindings = default_bindings(roles, stored.profile)
    else:
        bindings = carry_bindings(view.bindings, roles, stored.profile, previous, converted, row_numbers, splits)
    delta = {**_delta(dataset_id, bindings, history, version), DATASET_TOP: version}
    if original is not None:
        delta[DATASET_ORIGINAL] = original
    original_version = kept_original.number if kept_original is not None else version
    return DatasetVersion(dataset_id, stored, bindings, version, delta, bool(history), original_version)


def undo_version(
    store: DatasetStore, session_id: str, view: SessionView, snapshot: CatalogueSnapshot
) -> DatasetVersion | None:
    """Make the newest history entry the current dataset again, or None when there is nothing to undo.

    The current version leaves the store (there is no redo). The idle sweep takes a
    session's history only together with its current version (`DatasetStore.sweep`),
    so an entry missing from the store means the store was emptied behind the state (a
    restart keeps neither): such an entry is skipped. The restored version is current again under its own number
    (`StoredDataset.number`): after paste, change, undo the card reads `data v1` again. It is unconfirmed even when the
    user confirmed it before the change it undoes (the fingerprint would match again): what
    is on the screen changed, so the user confirms what they see, as after a paste. The
    original kept past the history (`DATASET_ORIGINAL`) is no step of the undo, and the
    highest number given (`DATASET_TOP`) stays, so the undone number is never given again and reads as gone.
    """
    history = list(view.dataset_history)
    while history:
        dataset_id = history.pop()
        stored = store.get(dataset_id, session_id)
        if stored is not None:
            break
    else:
        return None
    original = _original_id(view)
    if view.dataset_id and view.dataset_id != original:
        store.delete(view.dataset_id, session_id)
    bindings = carry_bindings(view.bindings, snapshot.roles(), stored.profile)
    delta = {**_delta(dataset_id, bindings, history, stored.number), CONFIRMED: None}
    kept_original = store.get(original, session_id) if original else None
    original_version = kept_original.number if kept_original is not None else stored.number
    return DatasetVersion(dataset_id, stored, bindings, stored.number, delta, bool(history), original_version)


def _delta(dataset_id: str, bindings: list[Binding], history: list[str], version: int) -> dict[str, Any]:
    """The state of a new current version; a kept plot note (`PENDING_REQUEST`) and a switch's carry (`CARRY`, the
    texts, theme and requests of a plot of the data before it) were written for the data before it, so both go
    (owner decision of 2026-11-08: the carry drops with every new data version, as the note does)."""
    return {
        DATASET_ID: dataset_id,
        BINDINGS: [binding.model_dump() for binding in bindings],
        DATASET_HISTORY: history,
        DATASET_VERSION: version,
        **PENDING_CLEARED,
        CARRY: None,
    }
