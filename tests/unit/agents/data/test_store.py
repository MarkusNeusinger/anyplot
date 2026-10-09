"""Tests for agents/anyplot/data/store.py: ownership, idle sweep, byte accounting and the cap."""

import re

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
        assert DatasetStore().max_bytes == DEFAULT_MAX_BYTES == 64 * 1024 * 1024
