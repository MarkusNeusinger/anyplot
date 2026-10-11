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
    """A session state with a stored paste, as the dataset route leaves it."""
    state = initial_state(
        spec_id="scatter-basic", library="matplotlib", locale="en", snapshot=SNAPSHOT, normalised="x = 1", readiness={}
    )
    ingested = store_dataset(store, SID, parse_dataset(text), SNAPSHOT)
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
    assert set(version.payload()) == {"preview", "profile", "bindings", "warnings", "version"}
    assert version.payload()["profile"]["columns"][0]["name"] == "hours"


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
