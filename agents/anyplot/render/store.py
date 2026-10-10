"""The session-scoped, in-memory render store.

Hardened PNGs live here under a random `render_id`, readable only by the session
that produced them, one PNG per rendered theme. A pipeline run stores the one theme
it rendered; the theme toggle adds the other theme to the same render with
`add_theme`, so a version's artifacts are always the PNGs its render holds. The
reviewer's callback loads its image from here by `render_id`, so no image ever passes
through session state, an artifact listing or a tool argument. Like the dataset
store, it is unlocked (one asyncio loop), byte-capped, and emptied by
`delete_session` and the idle sweep.

The PNGs in `pngs` are the raw renders that the gates passed and the reviewer saw.
What a user is shown and downloads is that render with the footer strip
(`watermark.py`); `shown_png` composes it on the first request and caches it in
`shown`, counted against the same byte cap. The cache is disposable: a replaced theme
drops its variant, and a `put` or `add_theme` that would not fit otherwise drops every
cached variant first, so the cache never makes a render fail with `RenderStoreFull`.
`shown_png` is the one coroutine here, and it changes the store only on the event
loop, never in the worker thread the composition runs in.
"""

import secrets
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

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
    """The bytes of `pngs` and `shown` together."""
    shown: dict[Theme, bytes] = field(default_factory=dict)
    """The PNG of each theme as users see it (with the footer strip), cached by `RenderStore.shown_png`."""


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
        if not self._room_for(size):
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
        """Store (or replace) one theme's PNG in an existing render; raises `KeyError` or `RenderStoreFull`.

        The theme's cached shown variant is dropped first, even when the store then
        turns out to be full: it is rebuilt from whichever raw PNG the render holds.
        """
        stored = self.get(render_id, session_id)
        if stored is None:
            raise KeyError("no such render in this session")
        self._drop_shown(stored, theme)
        delta = len(png) - len(stored.pngs.get(theme, b""))
        if not self._room_for(delta):
            raise RenderStoreFull(f"the render store is full ({self._used_bytes} of {self.max_bytes} bytes used)")
        stored.pngs[theme] = png
        stored.size_bytes += delta
        self._used_bytes += delta

    async def shown_png(
        self, render_id: str, session_id: str, theme: Theme, compose: Callable[[bytes], Awaitable[bytes]]
    ) -> bytes | None:
        """The PNG users see of one theme: the cached variant, or `compose(raw)`, cached when it fits.

        None when the session has no such render or the render no such theme. A
        variant that would push the store past its cap is returned uncached. The
        result is cached only when the render still holds the same raw PNG after the
        composition, so a theme the toggle replaced meanwhile never keeps a stale
        variant; two requests that compose at the same time both get their bytes, and
        the first one is kept.
        """
        stored = self.get(render_id, session_id)
        raw = stored.pngs.get(theme) if stored is not None else None
        if stored is None or raw is None:
            return None
        cached = stored.shown.get(theme)
        if cached is not None:
            return cached
        png = await compose(raw)
        still_current = self._renders.get(render_id) is stored and stored.pngs.get(theme) is raw
        if still_current and theme not in stored.shown and self._used_bytes + len(png) <= self.max_bytes:
            stored.shown[theme] = png
            stored.size_bytes += len(png)
            self._used_bytes += len(png)
        return png

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

    def _drop_shown(self, stored: StoredRender, theme: Theme) -> None:
        freed = len(stored.shown.pop(theme, b""))
        stored.size_bytes -= freed
        self._used_bytes -= freed

    def _room_for(self, size: int) -> bool:
        """Whether `size` more bytes fit; when they do not, every cached shown variant is dropped first."""
        if self._used_bytes + size <= self.max_bytes:
            return True
        for stored in self._renders.values():
            for theme in list(stored.shown):
                self._drop_shown(stored, theme)
        return self._used_bytes + size <= self.max_bytes
