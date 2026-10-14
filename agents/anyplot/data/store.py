"""The session-scoped, in-memory dataset store.

Parsed datasets live here, never in ADK state and never as a `user:` artifact,
which would outlive the session and be listable by the model. Nothing is
persisted: a restart or scale-to-zero empties the store, and the session then
answers `session_expired`. Entries leave through `delete` (a replaced dataset),
`delete_session` (the DELETE route) and `sweep` (the idle sweeper). The sweep
counts idleness per session, not per entry: a session's datasets are its current
version and the versions its undo history keeps (`dataset_versions.py`), and only
the current one is read by the routes and the tools, so the history lives exactly as
long as the current version does.

Every method is synchronous and never awaits, so a call runs to completion on the
one asyncio loop that serves the app; there are no threads and no locks. Times
come from `time.monotonic` unless a clock is injected, so they measure idleness,
not wall-clock dates.
"""

import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass, field

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
    text_columns: list[str]
    preview: list[list[str]]
    created_at: float
    last_used_at: float
    size_bytes: int
    context_lines: list[str] = field(default_factory=list)
    """The notes the user pasted around the table (`ParsedDataset.context_lines`), as the route kept
    them after the pre-filter and the scope judge; a version made from this one carries them on."""
    code: str | None = None
    """The Python that computed this version (`run_data_code`, the validated snippet as it ran), for the data
    panel's collapsed "code that made this data" block; None for every other version."""

    def as_parsed(self) -> ParsedDataset:
        """The dataset as `parse_dataset` returned it (the profile's warnings are the parse's), for `apply_operations`."""
        return ParsedDataset(
            profile=self.profile.model_copy(deep=True),
            csv=self.csv,
            preview=[list(row) for row in self.preview],
            column_dtypes=dict(self.column_dtypes),
            parse_dates=list(self.parse_dates),
            warnings=list(self.profile.warnings),
            text_columns=list(self.text_columns),
            context_lines=list(self.context_lines),
        )


def dataset_size(parsed: ParsedDataset) -> int:
    """The bytes a dataset is accounted at: `data.csv`, the profile as JSON, the preview cells and the notes, as UTF-8."""
    preview = sum(len(cell.encode("utf-8")) for row in parsed.preview for cell in row)
    notes = sum(len(line.encode("utf-8")) for line in parsed.context_lines)
    return len(parsed.csv.encode("utf-8")) + len(parsed.profile.model_dump_json().encode("utf-8")) + preview + notes


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

    def put(self, session_id: str, parsed: ParsedDataset, *, code: str | None = None) -> str:
        """Store a parsed dataset (and the code that computed it) for `session_id` and return its new id;
        raises `StoreFull` past the cap."""
        size = dataset_size(parsed) + (len(code.encode("utf-8", errors="surrogatepass")) if code else 0)
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
            profile=parsed.profile.model_copy(deep=True),
            column_dtypes=dict(parsed.column_dtypes),
            parse_dates=list(parsed.parse_dates),
            text_columns=list(parsed.text_columns),
            preview=[list(row) for row in parsed.preview],
            created_at=now,
            last_used_at=now,
            size_bytes=size,
            context_lines=list(parsed.context_lines),
            code=code,
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
        """Remove the datasets of every session none of whose datasets was used within `idle_seconds`; their ids.

        A session's history entries are never read while they wait for an undo, so a
        session counts as idle only when its most recently used dataset is: the history
        then leaves together with the current version, never before it.
        """
        current = self._clock() if now is None else now
        latest: dict[str, float] = {}
        for stored in self._datasets.values():
            latest[stored.session_id] = max(latest.get(stored.session_id, stored.last_used_at), stored.last_used_at)
        removed = [
            dataset_id
            for dataset_id, stored in self._datasets.items()
            if current - latest[stored.session_id] > idle_seconds
        ]
        for dataset_id in removed:
            self._remove(dataset_id)
        return removed

    def _remove(self, dataset_id: str) -> None:
        stored = self._datasets.pop(dataset_id)
        self._used_bytes -= stored.size_bytes
