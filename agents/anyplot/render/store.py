"""The session-scoped, in-memory render store.

Hardened PNGs live here under a random `render_id`, readable only by the session
that produced them, one PNG per rendered theme. A pipeline run stores the one theme
it rendered; the theme toggle adds the other theme to the same render with
`add_theme`, so a version's artifacts are always the PNGs its render holds. The
reviewer's callback loads its image from here by `render_id`, so no image ever passes
through session state, an artifact listing or a tool argument. Like the dataset
store, it is synchronous, unlocked (one asyncio loop), byte-capped, and emptied by
`delete_session` and the idle sweep.
"""

import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass

from .contract import Theme


DEFAULT_MAX_BYTES = 256 * 1024 * 1024


class RenderStoreFull(Exception):
    """A put would push the store past its byte cap; nothing was stored."""


@dataclass
class StoredRender:
    """The PNG of every theme rendered for one code version, owned by one session."""

    render_id: str
    session_id: str
    pngs: dict[Theme, bytes]
    created_at: float
    last_used_at: float
    size_bytes: int


class RenderStore:
    """Renders keyed by a random url-safe id."""

    def __init__(self, max_bytes: int = DEFAULT_MAX_BYTES, clock: Callable[[], float] = time.monotonic) -> None:
        self.max_bytes = max_bytes
        self._clock = clock
        self._renders: dict[str, StoredRender] = {}
        self._used_bytes = 0

    @property
    def used_bytes(self) -> int:
        return self._used_bytes

    def __len__(self) -> int:
        return len(self._renders)

    def put(self, session_id: str, pngs: dict[Theme, bytes]) -> str:
        size = sum(len(data) for data in pngs.values())
        if self._used_bytes + size > self.max_bytes:
            raise RenderStoreFull(f"the render store is full ({self._used_bytes} of {self.max_bytes} bytes used)")
        render_id = secrets.token_urlsafe(12)
        while render_id in self._renders:
            render_id = secrets.token_urlsafe(12)
        now = self._clock()
        self._renders[render_id] = StoredRender(render_id, session_id, dict(pngs), now, now, size)
        self._used_bytes += size
        return render_id

    def get(self, render_id: str, session_id: str) -> StoredRender | None:
        stored = self._renders.get(render_id)
        if stored is None or stored.session_id != session_id:
            return None
        stored.last_used_at = self._clock()
        return stored

    def add_theme(self, render_id: str, session_id: str, theme: Theme, png: bytes) -> None:
        """Store (or replace) one theme's PNG in an existing render; raises `KeyError` or `RenderStoreFull`."""
        stored = self.get(render_id, session_id)
        if stored is None:
            raise KeyError("no such render in this session")
        delta = len(png) - len(stored.pngs.get(theme, b""))
        if self._used_bytes + delta > self.max_bytes:
            raise RenderStoreFull(f"the render store is full ({self._used_bytes} of {self.max_bytes} bytes used)")
        stored.pngs[theme] = png
        stored.size_bytes += delta
        self._used_bytes += delta

    def delete_session(self, session_id: str) -> list[str]:
        removed = [render_id for render_id, stored in self._renders.items() if stored.session_id == session_id]
        for render_id in removed:
            self._remove(render_id)
        return removed

    def sweep(self, idle_seconds: float, now: float | None = None) -> list[str]:
        current = self._clock() if now is None else now
        removed = [rid for rid, stored in self._renders.items() if current - stored.last_used_at > idle_seconds]
        for render_id in removed:
            self._remove(render_id)
        return removed

    def _remove(self, render_id: str) -> None:
        stored = self._renders.pop(render_id)
        self._used_bytes -= stored.size_bytes
