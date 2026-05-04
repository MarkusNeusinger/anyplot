"""Pick (or validate) the spec to regen.

Two callers from `regen.md` step 1b:
  - `pick_oldest()`  — bare `/regen`, finds the oldest spec on `origin/main`
  - `validate_spec(id)` — `/regen <spec-id>`, confirms the spec exists

Both read the metadata YAMLs straight out of the `origin/main` git tree
(`git ls-tree`/`git show`), not the working copy, so the result is
independent of which branch is checked out — even on a stale feature
branch the picker reflects the current `main`.

Output format is shared: `<spec_id>\t<latest_iso>` so the markdown can
substitute the two callers interchangeably.
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from typing import Iterable

import yaml


def _git_show(path: str, ref: str = "origin/main") -> str:
    return subprocess.check_output(["git", "show", f"{ref}:{path}"], text=True)


def _list_spec_dirs(ref: str = "origin/main") -> list[str]:
    """Names of every directory directly under `plots/` on the given ref."""
    try:
        out = subprocess.check_output(["git", "ls-tree", "-d", "--name-only", ref, "plots/"], text=True)
    except subprocess.CalledProcessError:
        return []
    names = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        # ls-tree returns "plots/spec-id"; we want just "spec-id"
        leaf = line.rsplit("/", 1)[-1]
        if leaf and not leaf.startswith("."):
            names.append(leaf)
    return names


def _list_metadata_files(spec_id: str, ref: str = "origin/main") -> list[str]:
    """All `metadata/python/*.yaml` paths for a spec on the given ref."""
    try:
        out = subprocess.check_output(
            ["git", "ls-tree", "--name-only", ref, f"plots/{spec_id}/metadata/python/"], text=True
        )
    except subprocess.CalledProcessError:
        return []
    return [line for line in out.splitlines() if line.endswith(".yaml")]


def _parse_iso(ts: str | None) -> datetime:
    if not ts:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _latest_timestamp(meta_paths: Iterable[str], ref: str = "origin/main") -> str | None:
    """Most recent `updated`/`created` ISO timestamp across the given metadata files.

    Compares parsed datetimes, not raw strings — the repo mixes `...Z` and
    `...+00:00` suffixes, which sort differently lexicographically even when
    they represent the same instant.
    """
    latest_dt: datetime | None = None
    latest_ts: str | None = None
    for path in meta_paths:
        try:
            data = yaml.safe_load(_git_show(path, ref)) or {}
        except (subprocess.CalledProcessError, yaml.YAMLError):
            continue
        ts = data.get("updated") or data.get("created")
        if not ts:
            continue
        ts_str = str(ts)
        dt = _parse_iso(ts_str)
        if latest_dt is None or dt > latest_dt:
            latest_dt = dt
            latest_ts = ts_str
    return latest_ts


def pick_oldest(ref: str = "origin/main") -> tuple[str, str]:
    """Return `(spec_id, latest_iso)` of the oldest spec by latest impl update.

    Raises `LookupError` if there are no eligible specs.
    """
    candidates: list[tuple[datetime, str, str]] = []
    for spec_id in sorted(_list_spec_dirs(ref)):
        meta_files = _list_metadata_files(spec_id, ref)
        if not meta_files:
            continue
        latest = _latest_timestamp(meta_files, ref)
        dt = _parse_iso(latest)
        candidates.append((dt, spec_id, latest or dt.isoformat()))
    if not candidates:
        raise LookupError("No eligible specs found on " + ref)
    candidates.sort(key=lambda c: (c[0], c[1]))
    _dt, spec_id, latest_iso = candidates[0]
    return spec_id, latest_iso


def validate_spec(spec_id: str, ref: str = "origin/main") -> tuple[str, str]:
    """Confirm `spec_id` exists on `ref` and return `(spec_id, latest_iso)`.

    Raises `LookupError` with a clear message if the spec is missing.
    Output shape matches `pick_oldest()` so callers are interchangeable.
    """
    if not spec_id or "/" in spec_id or spec_id.startswith("."):
        raise LookupError(f"Invalid spec id: {spec_id!r}")
    if spec_id not in _list_spec_dirs(ref):
        raise LookupError(f"Spec {spec_id!r} does not exist on {ref}")
    meta_files = _list_metadata_files(spec_id, ref)
    latest = _latest_timestamp(meta_files, ref) or _parse_iso(None).isoformat()
    return spec_id, latest
