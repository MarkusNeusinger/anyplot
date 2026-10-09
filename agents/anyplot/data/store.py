"""The session-scoped, in-memory dataset store.

Parsed datasets live here, never in ADK state and never as a `user:` artifact,
which would outlive the session and be listable by the model. Nothing is
persisted: a restart or scale-to-zero empties the store, and the session then
answers `session_expired`. Entries leave through `delete` (a replaced dataset),
`delete_session` (the DELETE route) and `sweep` (the idle sweeper).

Every method is synchronous and never awaits, so a call runs to completion on the
one asyncio loop that serves the app; there are no threads and no locks. Times
come from `time.monotonic` unless a clock is injected, so they measure idleness,
not wall-clock dates.
"""

import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass

from ..schemas import ColumnDtype, DatasetProfile
from .parse import ParsedDataset


DEFAULT_MAX_BYTES = 64 * 1024 * 1024


class StoreFull(Exception):
    """A put would push the store past its byte cap; nothing was stored."""


@dataclass
class StoredDataset:
    """One parsed dataset, owned by the session that uploaded it."""

    dataset_id: str
    session_id: str
    csv: str
    profile: DatasetProfile
    column_dtypes: dict[str, ColumnDtype]
    parse_dates: list[str]
    preview: list[list[str]]
    created_at: float
    last_used_at: float
    size_bytes: int


def dataset_size(parsed: ParsedDataset) -> int:
    """The bytes a dataset is accounted at: `data.csv`, the profile as JSON and the preview cells, as UTF-8."""
    preview = sum(len(cell.encode("utf-8")) for row in parsed.preview for cell in row)
    return len(parsed.csv.encode("utf-8")) + len(parsed.profile.model_dump_json().encode("utf-8")) + preview


class DatasetStore:
    """Datasets keyed by a random url-safe `dataset_id`, readable only by their own session."""

    def __init__(self, max_bytes: int = DEFAULT_MAX_BYTES, clock: Callable[[], float] = time.monotonic) -> None:
        self.max_bytes = max_bytes
        self._clock = clock
        self._datasets: dict[str, StoredDataset] = {}
        self._used_bytes = 0

    @property
    def used_bytes(self) -> int:
        return self._used_bytes

    def __len__(self) -> int:
        return len(self._datasets)

    def put(self, session_id: str, parsed: ParsedDataset) -> str:
        """Store a parsed dataset for `session_id` and return its new id; raises `StoreFull` past the cap."""
        size = dataset_size(parsed)
        if self._used_bytes + size > self.max_bytes:
            raise StoreFull(f"the dataset store is full ({self._used_bytes} of {self.max_bytes} bytes used)")
        dataset_id = secrets.token_urlsafe(16)
        while dataset_id in self._datasets:  # 128 random bits; the loop only guards the impossible
            dataset_id = secrets.token_urlsafe(16)
        now = self._clock()
        self._datasets[dataset_id] = StoredDataset(
            dataset_id=dataset_id,
            session_id=session_id,
            csv=parsed.csv,
            profile=parsed.profile,
            column_dtypes=dict(parsed.column_dtypes),
            parse_dates=list(parsed.parse_dates),
            preview=[list(row) for row in parsed.preview],
            created_at=now,
            last_used_at=now,
            size_bytes=size,
        )
        self._used_bytes += size
        return dataset_id

    def get(self, dataset_id: str, session_id: str) -> StoredDataset | None:
        """The dataset if it exists and belongs to `session_id`, else None; a hit counts as use."""
        stored = self._datasets.get(dataset_id)
        if stored is None or stored.session_id != session_id:
            return None
        stored.last_used_at = self._clock()
        return stored

    def delete(self, dataset_id: str, session_id: str) -> bool:
        """Remove one dataset of `session_id`; False when it does not exist or belongs to another session."""
        stored = self._datasets.get(dataset_id)
        if stored is None or stored.session_id != session_id:
            return False
        self._remove(dataset_id)
        return True

    def delete_session(self, session_id: str) -> list[str]:
        """Remove every dataset of `session_id` and return their ids."""
        removed = [dataset_id for dataset_id, stored in self._datasets.items() if stored.session_id == session_id]
        for dataset_id in removed:
            self._remove(dataset_id)
        return removed

    def sweep(self, idle_seconds: float, now: float | None = None) -> list[str]:
        """Remove every dataset unused for more than `idle_seconds` and return their ids."""
        current = self._clock() if now is None else now
        removed = [
            dataset_id for dataset_id, stored in self._datasets.items() if current - stored.last_used_at > idle_seconds
        ]
        for dataset_id in removed:
            self._remove(dataset_id)
        return removed

    def _remove(self, dataset_id: str) -> None:
        stored = self._datasets.pop(dataset_id)
        self._used_bytes -= stored.size_bytes
