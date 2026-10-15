"""Tests for agents/anyplot/dataset_versions.py: the next version, the history cap, undo, the carried bindings."""

from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.data.store import DatasetStore
from agents.anyplot.dataset_versions import MAX_DATASET_HISTORY, dataset_payload, push_version, undo_version
from agents.anyplot.dev_fixture import snapshot_from_repo
from agents.anyplot.opening import store_dataset
from agents.anyplot.session_state import (
    BINDINGS,
    CONFIRMED,
    DATASET_HISTORY,
    DATASET_ID,
    DATASET_VERSION,
    SessionView,
    confirmation_fingerprint,
    initial_state,
    read_session,
)


SID = "s1"
SNAPSHOT = snapshot_from_repo("scatter-basic", "matplotlib")


def view_of(state: dict) -> SessionView:
    view = read_session(state)
    assert view is not None
    return view


def opened(store: DatasetStore, text: str = "a,b\n1,2\n3,4\n") -> dict:
    """A session state with a stored paste, as the dataset route leaves it (its notes screened)."""
    state = initial_state(
        spec_id="scatter-basic", library="matplotlib", locale="en", snapshot=SNAPSHOT, normalised="x = 1", readiness={}
    )
    ingested = store_dataset(store, SID, parse_dataset(text), SNAPSHOT, notes_screened=True)
    state.update(ingested.state_delta())
    return state


def test_push_keeps_the_previous_version_and_carries_the_bindings() -> None:
    store = DatasetStore()
    state = opened(store)
    first = state[DATASET_ID]
    state[CONFIRMED] = confirmation_fingerprint(first, view_of(state).bindings)

    version = push_version(store, SID, view_of(state), parse_dataset("hours,b\n1,2\n3,4\n"), SNAPSHOT)
    state.update(version.delta)

    assert version.version == 2 and version.delta[DATASET_VERSION] == 2
    assert version.delta[DATASET_HISTORY] == [first] and state[DATASET_ID] == version.dataset_id != first
    assert store.get(first, SID) is not None and store.get(version.dataset_id, SID) is not None
    assert version.delta[BINDINGS] == [{"role": "x", "column": "hours"}, {"role": "y", "column": "b"}]  # x carried over
    assert not view_of(state).data_confirmed  # the fingerprint names the old dataset id
    assert version.payload() == dataset_payload(version.stored, version.bindings, 2)
    assert set(version.payload()) == {"preview", "profile", "bindings", "warnings", "context_lines", "version"}
    assert version.payload()["profile"]["columns"][0]["name"] == "hours"


def test_a_dropped_files_name_travels_with_every_version() -> None:
    store = DatasetStore()
    state = initial_state(
        spec_id="scatter-basic", library="matplotlib", locale="en", snapshot=SNAPSHOT, normalised="x = 1", readiness={}
    )
    ingested = store_dataset(store, SID, parse_dataset("a,b\n1,2\n3,4\n"), SNAPSHOT, file_name="sales.csv")
    state.update(ingested.state_delta())

    version = push_version(store, SID, view_of(state), parse_dataset("hours,b\n1,2\n3,4\n"), SNAPSHOT)

    assert version.stored.file_name == "sales.csv" and version.payload()["file_name"] == "sales.csv"
    assert version.stored.context_lines == []  # a name is never a note
    state.update(version.delta)

    # `.to_long()` rebinds but is still the file's data.
    long = push_version(store, SID, view_of(state), parse_dataset("k,v\na,1\nb,2\n"), SNAPSHOT, rebind=True)
    assert long.stored.file_name == "sales.csv"
    state.update(long.delta)

    # A computed table is no longer the file's: no name, in the payload either.
    computed = push_version(
        store, SID, view_of(state), parse_dataset("x,y\n0,0\n1,0.84\n"), SNAPSHOT, rebind=True, source="formulas"
    )
    assert computed.stored.file_name is None and "file_name" not in computed.payload()
    state.update(computed.delta)

    # The undo restores the version's own name.
    undone = undo_version(store, SID, view_of(state), SNAPSHOT)
    assert undone is not None and undone.stored.file_name == "sales.csv"


def test_a_replacing_table_gets_the_default_bindings_where_a_change_carries_them() -> None:
    """`rebind` (a generated table) starts from the defaults even where the old columns' names return."""
    store = DatasetStore()
    state = opened(store, "x,y\n1,2\n3,4\n")
    state[BINDINGS] = [{"role": "x", "column": "y"}, {"role": "y", "column": "x"}]  # the user swapped them

    carried = push_version(store, SID, view_of(state), parse_dataset("x,y\n5,6\n7,8\n"), SNAPSHOT)
    fresh = push_version(store, SID, view_of(state), parse_dataset("x,y\n5,6\n7,8\n"), SNAPSHOT, rebind=True)

    assert carried.delta[BINDINGS] == [{"role": "x", "column": "y"}, {"role": "y", "column": "x"}]
    assert fresh.delta[BINDINGS] == [{"role": "x", "column": "x"}, {"role": "y", "column": "y"}]


def test_the_history_keeps_five_versions_and_deletes_the_oldest() -> None:
    store = DatasetStore()
    state = opened(store)
    ids = [state[DATASET_ID]]
    for number in range(2, 9):
        version = push_version(store, SID, view_of(state), parse_dataset(f"a,b\n{number},2\n"), SNAPSHOT)
        state.update(version.delta)
        ids.append(version.dataset_id)

    assert state[DATASET_VERSION] == 8
    assert state[DATASET_HISTORY] == ids[2:7] and len(state[DATASET_HISTORY]) == MAX_DATASET_HISTORY
    assert [store.get(dataset_id, SID) is not None for dataset_id in ids] == [False, False] + [True] * 6
    assert len(store) == 6


def test_undo_restores_the_newest_entry_and_drops_the_current_one() -> None:
    store = DatasetStore()
    state = opened(store)
    first = state[DATASET_ID]
    state[CONFIRMED] = confirmation_fingerprint(first, view_of(state).bindings)  # the paste was confirmed
    pushed = push_version(store, SID, view_of(state), parse_dataset("hours,b\n1,2\n"), SNAPSHOT)
    state.update(pushed.delta)

    restored = undo_version(store, SID, view_of(state), SNAPSHOT)
    assert restored is not None
    state.update(restored.delta)

    assert (restored.dataset_id, restored.version) == (first, 1)
    assert state[DATASET_HISTORY] == [] and state[DATASET_ID] == first
    assert restored.delta[CONFIRMED] is None and not view_of(state).data_confirmed  # confirmed again by the user
    assert store.get(pushed.dataset_id, SID) is None and store.get(first, SID) is not None
    assert restored.delta[BINDINGS] == [{"role": "x", "column": "a"}, {"role": "y", "column": "b"}]
    assert undo_version(store, SID, view_of(state), SNAPSHOT) is None  # nothing left to undo


def test_undo_skips_an_entry_the_store_lost() -> None:
    """The sweep takes a session's history only with its current version; a lost entry (the store emptied) is skipped."""
    store = DatasetStore()
    state = opened(store)
    first = state[DATASET_ID]
    second = push_version(store, SID, view_of(state), parse_dataset("a,b\n5,6\n"), SNAPSHOT)
    state.update(second.delta)
    third = push_version(store, SID, view_of(state), parse_dataset("a,b\n7,8\n"), SNAPSHOT)
    state.update(third.delta)
    store.delete(second.dataset_id, SID)  # the store lost the entry behind the state

    restored = undo_version(store, SID, view_of(state), SNAPSHOT)

    assert restored is not None and restored.dataset_id == first and restored.version == 1
    assert restored.delta[DATASET_HISTORY] == []


def test_a_new_paste_forgets_the_history() -> None:
    store = DatasetStore()
    state = opened(store)
    first = state[DATASET_ID]
    pushed = push_version(store, SID, view_of(state), parse_dataset("a,b\n5,6\n"), SNAPSHOT)
    state.update(pushed.delta)
    view = view_of(state)

    ingested = store_dataset(store, SID, parse_dataset("c,d\n1,2\n"), SNAPSHOT, view.dataset_id, view.dataset_history)
    state.update(ingested.state_delta())

    assert state[DATASET_HISTORY] == [] and state[DATASET_VERSION] == 1
    assert store.get(first, SID) is None and store.get(pushed.dataset_id, SID) is None and len(store) == 1


NOTED = "Rainfall per month\nx,y\n1,2\n3,4\n5,6\nSource: own measurements\n"
"""A paste with a title above and a source line below the table: two notes for the root."""


def test_notes_that_did_not_pass_the_screen_are_never_stored() -> None:
    """A fixture seed or an eval ingest stores the table without its notes (#12168 review)."""
    store = DatasetStore()
    ingested = store_dataset(store, SID, parse_dataset(NOTED), SNAPSHOT)

    stored = store.get(ingested.dataset_id, SID)
    assert ingested.parsed.context_lines == [] and stored is not None and stored.context_lines == []


def test_the_notes_travel_with_every_version_and_a_new_paste_replaces_them() -> None:
    """prepare_data and generate_data re-parse a CSV without notes; the session's notes stay all the same."""
    store = DatasetStore()
    state = opened(store, NOTED)
    first = state[DATASET_ID]
    notes = ["Rainfall per month", "Source: own measurements"]
    first_stored = store.get(first, SID)
    assert first_stored is not None and first_stored.context_lines == notes

    prepared = push_version(store, SID, view_of(state), parse_dataset("x,y\n1,2\n", find_table=False), SNAPSHOT)
    state.update(prepared.delta)
    generated = push_version(
        store, SID, view_of(state), parse_dataset("t,v\n0,1\n", find_table=False), SNAPSHOT, rebind=True
    )
    state.update(generated.delta)

    assert prepared.stored.context_lines == notes and generated.stored.context_lines == notes
    assert generated.payload()["context_lines"] == notes
    restored = undo_version(store, SID, view_of(state), SNAPSHOT)
    assert restored is not None and restored.stored.context_lines == notes  # the version's own

    view = view_of(state)
    pasted = store_dataset(
        store, SID, parse_dataset("c,d\n1,2\n3,4\n5,6\n"), SNAPSHOT, view.dataset_id, view.dataset_history
    )
    stored = store.get(pasted.dataset_id, SID)
    assert pasted.parsed.context_lines == [] and stored is not None and stored.context_lines == []
