"""Tests for agents/anyplot/data/store.py: ownership, idle sweep, byte accounting and the cap."""

import re
from dataclasses import asdict, replace

import pytest

from agents.anyplot.data.parse import ParsedDataset, parse_dataset
from agents.anyplot.data.store import DEFAULT_MAX_BYTES, DatasetStore, StoreFull, dataset_size


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def parsed() -> ParsedDataset:
    return parse_dataset("when,value\n2024-01-01,1.5\n2024-01-02,2.5\n")


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def store(clock: Clock) -> DatasetStore:
    return DatasetStore(clock=clock)


class TestOwnership:
    def test_put_and_get(self, store: DatasetStore, parsed: ParsedDataset) -> None:
        dataset_id = store.put("s1", parsed)
        stored = store.get(dataset_id, "s1")

        assert stored is not None
        assert stored.dataset_id == dataset_id
        assert stored.session_id == "s1"
        assert stored.csv == parsed.csv
        assert stored.profile == parsed.profile
        assert stored.column_dtypes == {"when": "datetime", "value": "number"}
        assert stored.parse_dates == ["when"]
        assert stored.preview == parsed.preview

    def test_ids_are_random_url_safe_tokens(self, store: DatasetStore, parsed: ParsedDataset) -> None:
        ids = {store.put("s1", parsed) for _ in range(20)}

        assert len(ids) == 20
        assert all(re.fullmatch(r"[A-Za-z0-9_-]{20,}", dataset_id) for dataset_id in ids)

    def test_another_session_gets_nothing(self, store: DatasetStore, parsed: ParsedDataset) -> None:
        dataset_id = store.put("s1", parsed)

        assert store.get(dataset_id, "s2") is None
        assert store.get("unknown", "s1") is None
        assert store.get(dataset_id, "s1") is not None

    def test_the_stored_copy_is_independent_of_the_parse_result(
        self, store: DatasetStore, parsed: ParsedDataset
    ) -> None:
        dataset_id = store.put("s1", parsed)
        profile_before = parsed.profile.model_copy(deep=True)
        parsed.parse_dates.append("value")
        parsed.preview[0][0] = "changed"
        parsed.profile.warnings.append("changed")
        parsed.profile.columns[0].missing = 99

        stored = store.get(dataset_id, "s1")
        assert stored is not None
        assert stored.parse_dates == ["when"]
        assert stored.preview[0][0] == "2024-01-01"
        assert stored.profile == profile_before

    def test_delete_checks_ownership(self, store: DatasetStore, parsed: ParsedDataset) -> None:
        dataset_id = store.put("s1", parsed)

        assert store.delete(dataset_id, "s2") is False
        assert store.delete(dataset_id, "s1") is True
        assert store.delete(dataset_id, "s1") is False
        assert len(store) == 0

    def test_delete_session_removes_only_that_session(self, store: DatasetStore, parsed: ParsedDataset) -> None:
        first = store.put("s1", parsed)
        second = store.put("s1", parsed)
        other = store.put("s2", parsed)

        assert sorted(store.delete_session("s1")) == sorted([first, second])
        assert store.get(first, "s1") is None
        assert store.get(other, "s2") is not None
        assert store.delete_session("s1") == []


class TestCopy:
    """The admin fan-out's copy into another session (`DatasetStore.copy`): every field as it is, own ids and times."""

    def test_a_copy_is_the_same_dataset_under_its_own_id_and_session(self, store: DatasetStore, clock: Clock) -> None:
        noted = parse_dataset("Grüße aus Wien\nx,y,n\n0.12345678901234568,NaN,\n2.5,1.25,7\n3,4,8\n")
        source_id = store.put("s1", noted, code="df = make()", source="computed from a formula", file_name="a.csv")
        clock.now += 30

        copy_id = store.copy(source_id, "s1", "s2")

        assert copy_id is not None and copy_id != source_id
        original, copied = store.get(source_id, "s1"), store.get(copy_id, "s2")
        assert original is not None and copied is not None
        assert asdict(copied) == {
            **asdict(original),
            "dataset_id": copy_id,
            "session_id": "s2",
            "created_at": 1030.0,
            "last_used_at": 1030.0,
        }
        assert copied.csv is original.csv  # the very string: nothing was written or read again
        assert store.get(copy_id, "s1") is None  # the copy is the other session's only

    def test_the_copy_is_independent_of_the_original(self, store: DatasetStore, parsed: ParsedDataset) -> None:
        source_id = store.put("s1", parsed)
        copy_id = store.copy(source_id, "s1", "s2")
        original = store.get(source_id, "s1")
        assert copy_id is not None and original is not None
        original.preview[0][0] = "changed"
        original.parse_dates.append("value")
        original.profile.columns[0].missing = 99

        copied = store.get(copy_id, "s2")
        assert copied is not None
        assert copied.preview[0][0] == "2024-01-01"
        assert copied.parse_dates == ["when"]
        assert copied.profile.columns[0].missing == 0

    def test_only_the_owner_copies_and_the_cap_holds(self, parsed: ParsedDataset) -> None:
        size = dataset_size(parsed)
        store = DatasetStore(max_bytes=2 * size)
        source_id = store.put("s1", parsed)

        assert store.copy(source_id, "s2", "s3") is None  # another session's dataset, as for `get`
        assert store.copy("unknown", "s1", "s3") is None
        assert store.copy(source_id, "s1", "s2") is not None
        assert store.used_bytes == 2 * size
        with pytest.raises(StoreFull):
            store.copy(source_id, "s1", "s3")
        assert len(store) == 2 and store.used_bytes == 2 * size


class TestSweep:
    def test_idle_datasets_are_swept(self, store: DatasetStore, parsed: ParsedDataset, clock: Clock) -> None:
        old = store.put("s1", parsed)
        clock.now += 50
        fresh = store.put("s2", parsed)
        clock.now += 20

        assert store.sweep(60) == [old]
        assert store.get(old, "s1") is None
        assert store.get(fresh, "s2") is not None

    def test_a_get_counts_as_use(self, store: DatasetStore, parsed: ParsedDataset, clock: Clock) -> None:
        dataset_id = store.put("s1", parsed)
        clock.now += 50
        assert store.get(dataset_id, "s1") is not None
        clock.now += 50

        assert store.sweep(60) == []
        stored = store.get(dataset_id, "s1")
        assert stored is not None
        assert stored.created_at == 1000.0
        assert stored.last_used_at == 1100.0

    def test_a_foreign_get_does_not_count_as_use(
        self, store: DatasetStore, parsed: ParsedDataset, clock: Clock
    ) -> None:
        dataset_id = store.put("s1", parsed)
        clock.now += 50
        store.get(dataset_id, "s2")

        assert store.sweep(30) == [dataset_id]

    def test_sweep_takes_an_explicit_now(self, store: DatasetStore, parsed: ParsedDataset) -> None:
        dataset_id = store.put("s1", parsed)

        assert store.sweep(60, now=1060.0) == []
        assert store.sweep(60, now=1060.5) == [dataset_id]

    def test_a_sessions_undo_history_lives_as_long_as_its_current_dataset(
        self, store: DatasetStore, parsed: ParsedDataset, clock: Clock
    ) -> None:
        """Only the current version is read during a session; the history waits for an undo, so idleness is the session's."""
        history = store.put("s1", parsed)
        current = store.put("s1", parsed)
        other = store.put("s2", parsed)
        clock.now += 50
        assert store.get(current, "s1") is not None  # a turn reads the current version only
        clock.now += 50

        assert store.sweep(60) == [other]
        assert store.get(history, "s1") is not None and store.get(current, "s1") is not None

        clock.now += 100
        assert sorted(store.sweep(60)) == sorted([history, current])
        assert len(store) == 0

    def test_the_stored_copy_keeps_the_columns_kept_text(self, store: DatasetStore) -> None:
        parsed = parse_dataset("year,v\n2023,1\n", text_columns=["year"])
        stored = store.get(store.put("s1", parsed), "s1")

        assert stored is not None and stored.text_columns == ["year"]
        assert stored.as_parsed().text_columns == ["year"] and stored.as_parsed().column_dtypes["year"] == "text"

    def test_the_stored_copy_keeps_the_notes_and_counts_their_bytes(self, store: DatasetStore) -> None:
        noted = parse_dataset("Grüße aus Wien\nx,y\n1,2\n3,4\n5,6\n")
        plain = replace(noted, context_lines=[])
        stored = store.get(store.put("s1", noted), "s1")

        assert stored is not None and stored.context_lines == ["Grüße aus Wien"]
        assert stored.as_parsed().context_lines == ["Grüße aus Wien"]
        assert dataset_size(noted) == dataset_size(plain) + len("Grüße aus Wien".encode())


class TestCap:
    def test_byte_accounting(self, store: DatasetStore, parsed: ParsedDataset) -> None:
        size = dataset_size(parsed)
        first = store.put("s1", parsed)
        store.put("s2", parsed)

        assert size > len(parsed.csv)
        assert store.used_bytes == 2 * size
        store.delete(first, "s1")
        assert store.used_bytes == size
        store.delete_session("s2")
        assert store.used_bytes == 0

    def test_a_put_beyond_the_cap_raises_and_stores_nothing(self, parsed: ParsedDataset) -> None:
        size = dataset_size(parsed)
        store = DatasetStore(max_bytes=2 * size)
        store.put("s1", parsed)
        store.put("s1", parsed)

        with pytest.raises(StoreFull):
            store.put("s2", parsed)
        assert len(store) == 2
        assert store.used_bytes == 2 * size

        store.delete_session("s1")
        store.put("s2", parsed)
        assert len(store) == 1

    def test_the_default_cap_is_64_mib(self) -> None:
        assert DatasetStore().max_bytes == DEFAULT_MAX_BYTES == 256 * 1024 * 1024
