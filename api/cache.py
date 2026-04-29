"""
Caching utilities for anyplot API.

Centralized cache management with consistent key patterns.
Includes stampede protection (per-key asyncio.Lock) and
stale-while-revalidate (background refresh before TTL expiry).
"""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar, cast

from cachetools import TTLCache

from core.config import settings


T = TypeVar("T")

logger = logging.getLogger(__name__)


class _LockPruningTTLCache(TTLCache):
    """TTLCache that prunes the per-key asyncio.Lock when an entry is evicted.

    Binding lock lifecycle to cache-entry lifecycle gives us two guarantees
    a separate bounded `_locks` collection cannot:

    1. **No unbounded growth** — every lock that gets created either ends up
       in the cache (and is later pruned via TTL/LRU/explicit-delete) or is
       cleaned up by clear_cache().
    2. **No race between lock-eviction and lock-holder** — a lock can only
       disappear once its cache entry has been written, which means any
       in-flight `factory()` will have called `set_cache(key, ...)` before
       the lock entry can be reaped. New callers either find the cached
       value (no factory re-run) or take a fresh lock (which is fine,
       because at that point nobody else is in the critical section).
    """

    def __delitem__(self, key, *args, **kwargs):
        try:
            super().__delitem__(key, *args, **kwargs)
        finally:
            _locks.pop(key, None)


# Global cache instance. Stores `(value, monotonic_set_at)` tuples — folding
# the timestamp into the entry keeps cache age + payload on a single lifecycle
# (was a separate _timestamps dict that grew unbounded under high-cardinality
# traffic such as /plots/filter or /og/* keys).
_cache: _LockPruningTTLCache = _LockPruningTTLCache(maxsize=settings.cache_maxsize, ttl=settings.cache_ttl)

# Per-key locks for stampede protection. Plain dict; lifecycle is bound to
# `_cache` via `_LockPruningTTLCache.__delitem__`. Refresh-locks stored under
# `_refresh:<key>` never have a corresponding cache entry and are pruned by
# `_background_refresh` on completion.
_locks: dict[str, asyncio.Lock] = {}


def _get_lock(key: str) -> asyncio.Lock:
    """Get or create a lock for a specific cache key.

    Safe because asyncio is single-threaded — no race on dict access.
    """
    if key not in _locks:
        _locks[key] = asyncio.Lock()
    return _locks[key]


def cache_key(*parts: str) -> str:
    """
    Build consistent cache key from parts.

    Args:
        *parts: Key components to join.

    Returns:
        Cache key string.

    Example:
        >>> cache_key("spec", "scatter-basic")
        "spec:scatter-basic"
    """
    return ":".join(str(p) for p in parts if p)


def get_cache(key: str) -> Any | None:
    """
    Get value from cache.

    Args:
        key: Cache key.

    Returns:
        Cached value or None if not found.
    """
    entry = _cache.get(key)
    return entry[0] if entry is not None else None


def set_cache(key: str, value: Any) -> None:
    """
    Set value in cache.

    Args:
        key: Cache key.
        value: Value to cache.
    """
    _cache[key] = (value, time.monotonic())


def cache_age(key: str) -> float | None:
    """Seconds since key was last set, or None if not tracked."""
    entry = _cache.get(key)
    return time.monotonic() - entry[1] if entry is not None else None


def clear_cache() -> None:
    """
    Clear entire cache.

    Use this when you want to invalidate all cached data.
    Called automatically after database synchronization.

    Example:
        >>> clear_cache()  # Invalidates all cached responses
    """
    _cache.clear()
    # Per-entry locks are pruned by _LockPruningTTLCache.__delitem__, but
    # also clear refresh-locks (`_refresh:*`) that have no cache entry and
    # any locks for cold-miss attempts whose factory never called set_cache.
    _locks.clear()


def clear_cache_by_pattern(pattern: str) -> int:
    """
    Clear cache entries matching a pattern.

    Args:
        pattern: String pattern to match (substring match)

    Returns:
        Number of cache entries cleared

    Example:
        >>> clear_cache_by_pattern("spec:")  # Clears all spec-related cache
        15
        >>> clear_cache_by_pattern("filter:")  # Clears all filter cache
        42
    """
    keys_to_delete = [key for key in _cache.keys() if pattern in key]
    # _LockPruningTTLCache.__delitem__ also prunes _locks[key].
    for key in keys_to_delete:
        del _cache[key]
    return len(keys_to_delete)


def clear_spec_cache(spec_id: str) -> int:
    """
    Clear all cache entries related to a specific spec.

    Clears spec detail, spec images, spec list, filters, and stats caches.

    Args:
        spec_id: The specification ID

    Returns:
        Total count across all cleared patterns (may count overlapping keys multiple times)

    Example:
        >>> clear_spec_cache("scatter-basic")
        5
    """
    # Clear spec detail, spec images, and spec list cache
    count = 0
    count += clear_cache_by_pattern(f"spec:{spec_id}")
    count += clear_cache_by_pattern(f"spec_images:{spec_id}")
    count += clear_cache_by_pattern("specs_list")  # List might have changed
    count += clear_cache_by_pattern("filter:")  # Filters might be affected
    count += clear_cache_by_pattern("stats")  # Stats might have changed
    count += clear_cache_by_pattern("sitemap")  # Sitemap includes spec URLs
    count += clear_cache_by_pattern(f"seo:{spec_id}")  # SEO proxy pages for this spec
    count += clear_cache_by_pattern(f"og:{spec_id}")  # OG images for this spec
    return count


def clear_library_cache(library_id: str) -> int:
    """
    Clear all cache entries for a specific library.

    Args:
        library_id: The library ID

    Returns:
        Number of cache entries cleared

    Example:
        >>> clear_library_cache("matplotlib")
        3
    """
    # Clear library images and lists
    count = 0
    count += clear_cache_by_pattern(f"lib_images:{library_id}")
    count += clear_cache_by_pattern("libraries")  # List might have changed
    count += clear_cache_by_pattern("filter:")  # Filters might be affected
    count += clear_cache_by_pattern("stats")  # Stats might have changed
    count += clear_cache_by_pattern("sitemap")  # Sitemap includes library URLs
    return count


def get_cache_stats() -> dict:
    """
    Get cache statistics.

    Returns:
        Dict with cache size, maxsize, and TTL

    Example:
        >>> get_cache_stats()
        {"size": 42, "maxsize": 1000, "ttl": 600}
    """
    return {"size": len(_cache), "maxsize": _cache.maxsize, "ttl": _cache.ttl}


# ---------------------------------------------------------------------------
# Stampede protection + stale-while-revalidate
# ---------------------------------------------------------------------------


async def get_or_set_cache(
    key: str,
    factory: Callable[[], Awaitable[T]],
    *,
    refresh_after: float | None = None,
    refresh_factory: Callable[[], Awaitable[T]] | None = None,
) -> T:
    """Get cached value or compute it. Prevents stampede via per-key lock.

    If *refresh_after* is set and the cached entry is older than that many
    seconds, a background refresh is scheduled and the stale value is
    returned immediately (stale-while-revalidate).

    Args:
        key: Cache key.
        factory: Async callable that produces the value (e.g. DB query).
            Used for cold-miss (inline). May capture a request-scoped DB session.
        refresh_after: Seconds after which to trigger background refresh.
        refresh_factory: Standalone async callable for background refresh.
            Must create its own DB session (via get_db_context). Only used
            when refresh_after is set. Falls back to *factory* if not provided.
    """
    cached = get_cache(key)
    if cached is not None:
        # Stale-while-revalidate: schedule background refresh if stale
        if refresh_after is not None:
            age = cache_age(key)
            if age is not None and age > refresh_after:
                _schedule_refresh(key, refresh_factory or factory)
        return cast(T, cached)

    # Cold miss — must await. Lock prevents stampede.
    async with _get_lock(key):
        # Double-check after acquiring lock
        cached = get_cache(key)
        if cached is not None:
            return cast(T, cached)
        result = await factory()
        set_cache(key, result)
        return result


def _schedule_refresh(key: str, factory: Callable[[], Awaitable[Any]]) -> None:
    """Schedule a background cache refresh if one isn't already running."""
    refresh_key = f"_refresh:{key}"
    lock = _get_lock(refresh_key)
    if lock.locked():
        return  # refresh already in progress
    asyncio.create_task(_background_refresh(key, refresh_key, factory, lock))


async def _background_refresh(
    key: str, refresh_key: str, factory: Callable[[], Awaitable[Any]], lock: asyncio.Lock
) -> None:
    """Run factory in background and update cache. Errors are logged, not raised.

    Refresh-locks (`_refresh:<key>`) have no corresponding cache entry, so the
    `_LockPruningTTLCache.__delitem__` hook never reaps them — they would
    accumulate one-per-refreshed-key indefinitely. Pop in `finally` to bound
    `_locks` growth. A duplicate-task race (a second caller taking the same
    released lock before pop runs) only costs duplicated factory work, not
    correctness, since `set_cache` is last-write-wins.
    """
    try:
        async with lock:
            try:
                result = await factory()
                set_cache(key, result)
            except Exception:
                logger.warning("Background cache refresh failed for key: %s", key, exc_info=True)
    finally:
        _locks.pop(refresh_key, None)
