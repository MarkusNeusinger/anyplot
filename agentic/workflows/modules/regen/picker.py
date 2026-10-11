"""Pick (or validate) the spec to regen.

Two callers from `regen.md` step 1b:
  - `pick_oldest()`  — bare `/regen`, finds the oldest spec on `origin/main`
  - `validate_spec(id)` — `/regen <spec-id>`, confirms the spec exists

Both read the metadata YAMLs straight out of the `origin/main` git tree, not
the working copy, so the result is independent of which branch is checked
out — even on a stale feature branch the picker reflects the current `main`.

A call starts at most two git processes, however large the catalogue: one
recursive `git ls-tree` lists every file under `plots/` with its blob id, and
one `git cat-file --batch` streams the `metadata/python/*.yaml` blobs that the
listing named. Both reads come from the same tree, so a fetch between them
cannot mix two states of `main`. The YAML goes through libyaml's `CSafeLoader`
when PyYAML was built with it — the C twin of the `SafeLoader` behind
`yaml.safe_load`, accepting the same documents — and through `SafeLoader`
otherwise. Until October 2026 the picker ran one `git ls-tree` per spec and one
`git show` per file, about 2,900 processes, and parsed in pure Python: about
30 s per call instead of about 2.5 s.

Output format is shared: `<spec_id>\t<latest_iso>` so the markdown can
substitute the two callers interchangeably.
"""

from __future__ import annotations

import re
import subprocess
from datetime import datetime, timezone
from typing import Iterable

import yaml


# libyaml's loader when PyYAML was built with it, the pure-Python one otherwise.
_YAML_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)

# `git cat-file --batch` announces each object it found as `<oid> <type> <size>`.
_BATCH_HEADER = re.compile(rb"([0-9a-f]{40}|[0-9a-f]{64}) ([a-z]+) ([0-9]+)")

# A spec's metadata file per library: `plots/<spec>/metadata/python/<lib>.yaml`.
_METADATA_DIR = ["metadata", "python"]


def _git(args: list[str], stdin: bytes | None = None) -> bytes:
    """Run `git <args>` and return its stdout; stderr goes to the terminal.

    The only place this module starts a process, so a test can swap in a fake.
    Raises `subprocess.CalledProcessError` when git exits non-zero.
    """
    return subprocess.run(["git", *args], input=stdin, stdout=subprocess.PIPE, check=True).stdout


def _group_listing(listing: bytes) -> dict[str, list[tuple[str, str]]]:
    """Group a `git ls-tree -r -z <ref> plots/` listing by spec.

    Maps every directory directly under `plots/` whose name does not start
    with a dot to the `(path, blob id)` pairs of its `metadata/python/*.yaml`
    files, in the listing's (git's) order. A spec without such files maps to
    an empty list; files directly under `plots/` belong to no spec.
    """
    specs: dict[str, list[tuple[str, str]]] = {}
    for record in listing.split(b"\0"):
        if not record:
            continue
        # `<mode> <type> <oid>\t<path>`; only the path can contain a tab.
        info, _tab, raw_path = record.partition(b"\t")
        _mode, obj_type, oid = info.split(b" ")
        parts = raw_path.decode("utf-8", "surrogateescape").split("/")
        if len(parts) < 3 or parts[0] != "plots" or not parts[1] or parts[1].startswith("."):
            continue
        files = specs.setdefault(parts[1], [])
        if len(parts) == 5 and parts[2:4] == _METADATA_DIR and parts[4].endswith(".yaml") and obj_type == b"blob":
            files.append(("/".join(parts), oid.decode("ascii")))
    return specs


def _list_tree(ref: str = "origin/main") -> dict[str, list[tuple[str, str]]]:
    """Every spec on `ref` with its metadata blobs (see `_group_listing`).

    One `git ls-tree` for the whole catalogue; `{}` when git cannot list `ref`.
    """
    try:
        listing = _git(["ls-tree", "-r", "-z", ref, "plots/"])
    except subprocess.CalledProcessError:
        return {}
    return _group_listing(listing)


def _list_spec_dirs(ref: str = "origin/main") -> list[str]:
    """Names of every directory directly under `plots/` on the given ref."""
    return list(_list_tree(ref))


def _list_metadata_files(spec_id: str, ref: str = "origin/main") -> list[str]:
    """All `metadata/python/*.yaml` paths for a spec on the given ref."""
    return [path for path, _oid in _list_tree(ref).get(spec_id, [])]


def _parse_batch(stream: bytes, count: int) -> list[bytes | None]:
    """Split the stdout of `git cat-file --batch` into `count` objects.

    git answers each requested name, in order, with `<oid> <type> <size>\\n`
    followed by exactly `<size>` bytes of content and a `\\n`, or with a single
    `<name> missing` (or `ambiguous`) line. Content is cut by the announced
    size, never by searching for a separator: a blob can hold anything,
    including lines that look like a header. A missing object, or one that is
    not a blob, comes back as `None`. Raises `ValueError` when the stream does
    not follow this format, since every object after a framing error would be
    misread.
    """
    blobs: list[bytes | None] = []
    pos = 0
    for _ in range(count):
        eol = stream.find(b"\n", pos)
        if eol < 0:
            raise ValueError(f"git cat-file --batch output ends after {len(blobs)} of {count} objects")
        header = stream[pos:eol]
        pos = eol + 1
        found = _BATCH_HEADER.fullmatch(header)
        if found is None:
            if not header.endswith((b" missing", b" ambiguous")):
                raise ValueError(f"unexpected git cat-file --batch header: {header[:200]!r}")
            blobs.append(None)
            continue
        end = pos + int(found.group(3))
        if stream[end : end + 1] != b"\n":
            raise ValueError(f"git cat-file --batch object {found.group(1).decode()} is cut short")
        blobs.append(stream[pos:end] if found.group(2) == b"blob" else None)
        pos = end + 1
    if pos != len(stream):
        raise ValueError(f"git cat-file --batch output has {len(stream) - pos} bytes past the last object")
    return blobs


def _read_blobs(oids: list[str]) -> list[bytes | None]:
    """Contents of the given blobs, read by one `git cat-file --batch` process.

    `None` marks an object git does not have; the caller skips it as it would
    an unreadable file. Raises `subprocess.CalledProcessError` when git itself
    fails, rather than treating every file as unreadable and picking a spec
    from nothing.
    """
    if not oids:
        return []
    stream = _git(["cat-file", "--batch"], stdin="".join(f"{oid}\n" for oid in oids).encode("ascii"))
    return _parse_batch(stream, len(oids))


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


def _timestamp(blob: bytes | None) -> str | None:
    """The `updated` (else `created`) value of one metadata file, as a string.

    `None` when the file is missing, is not UTF-8 or valid YAML, is not a
    mapping, or has neither key.
    """
    if blob is None:
        return None
    try:
        data = yaml.load(blob.decode("utf-8"), Loader=_YAML_LOADER) or {}
    except (UnicodeDecodeError, yaml.YAMLError):
        return None
    if not isinstance(data, dict):
        return None
    ts = data.get("updated") or data.get("created")
    return str(ts) if ts else None


def _latest(timestamps: Iterable[str | None]) -> str | None:
    """The most recent of the given ISO timestamps, as written.

    Compares parsed datetimes, not raw strings — the repo mixes `...Z` and
    `...+00:00` suffixes, which sort differently lexicographically even when
    they represent the same instant. Of equal instants the first one wins.
    """
    latest_dt: datetime | None = None
    latest_ts: str | None = None
    for ts in timestamps:
        if not ts:
            continue
        dt = _parse_iso(ts)
        if latest_dt is None or dt > latest_dt:
            latest_dt = dt
            latest_ts = ts
    return latest_ts


def _latest_per_spec(specs: dict[str, list[tuple[str, str]]]) -> dict[str, str | None]:
    """The latest `updated`/`created` timestamp of each spec's metadata files.

    Reads every file of every given spec with one `git cat-file --batch`.
    """
    oids = list(dict.fromkeys(oid for files in specs.values() for _path, oid in files))
    blobs = dict(zip(oids, _read_blobs(oids), strict=True))
    return {spec_id: _latest(_timestamp(blobs[oid]) for _path, oid in files) for spec_id, files in specs.items()}


def pick_oldest(ref: str = "origin/main") -> tuple[str, str]:
    """Return `(spec_id, latest_iso)` of the oldest spec by latest impl update.

    Specs without `metadata/python/*.yaml` files are not eligible; a spec
    whose files carry no readable timestamp counts as the oldest of all. Ties
    go to the alphabetically first spec id. Raises `LookupError` if there are
    no eligible specs.
    """
    specs = {spec_id: files for spec_id, files in sorted(_list_tree(ref).items()) if files}
    candidates: list[tuple[datetime, str, str]] = []
    for spec_id, latest in _latest_per_spec(specs).items():
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
    tree = _list_tree(ref)
    if spec_id not in tree:
        raise LookupError(f"Spec {spec_id!r} does not exist on {ref}")
    latest = _latest_per_spec({spec_id: tree[spec_id]})[spec_id] or _parse_iso(None).isoformat()
    return spec_id, latest
