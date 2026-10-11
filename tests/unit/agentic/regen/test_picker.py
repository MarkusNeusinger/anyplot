"""Tests for `agentic.workflows.modules.regen.picker`.

Two kinds. The live tests hit real git against the repo's `origin/main`,
because the picker's whole point is that it reads the remote ref; the
slowest, `test_pick_oldest_returns_real_spec`, reads the whole catalogue.
The fake-git tests swap `picker._git` for an in-memory tree and pin the
listing, batch-parsing and picking rules without touching a repository.
"""

from __future__ import annotations

import hashlib
import subprocess

import pytest

from agentic.workflows.modules.regen import picker
from agentic.workflows.modules.regen.picker import (
    _group_listing,
    _list_metadata_files,
    _list_spec_dirs,
    _parse_batch,
    _timestamp,
    pick_oldest,
    validate_spec,
)


# --- live tests against origin/main ---


def test_list_spec_dirs_returns_known_specs():
    specs = _list_spec_dirs()
    # Specs known to be on main at the time of writing this test
    assert "scatter-basic" in specs
    assert "sparkline-basic" in specs
    # No path separators or hidden entries
    assert all("/" not in s for s in specs)
    assert all(not s.startswith(".") for s in specs)


def test_list_metadata_files_for_known_spec():
    files = _list_metadata_files("sparkline-basic")
    assert any(p.endswith("altair.yaml") for p in files)


def test_pick_oldest_returns_real_spec():
    spec_id, latest = pick_oldest()
    assert spec_id  # non-empty
    assert latest  # non-empty ISO


def test_validate_spec_known_id():
    spec_id, latest = validate_spec("sparkline-basic")
    assert spec_id == "sparkline-basic"
    assert latest


def test_validate_spec_unknown_raises():
    with pytest.raises(LookupError):
        validate_spec("definitely-not-a-real-spec-id-xyz")


def test_validate_spec_rejects_path_traversal():
    with pytest.raises(LookupError):
        validate_spec("../etc/passwd")


# --- fake-git tests ---


def _oid(content: bytes) -> str:
    """The blob id git gives `content`."""
    return hashlib.sha1(b"blob %d\0" % len(content) + content).hexdigest()


def _blob_record(content: bytes) -> bytes:
    """One found object as `git cat-file --batch` prints it."""
    return b"%s blob %d\n%s\n" % (_oid(content).encode(), len(content), content)


class FakeGit:
    """Serves `files` (path to content) as the tree of every ref.

    Answers the two calls the picker makes, `ls-tree -r -z <ref> plots/` and
    `cat-file --batch`, in git's output format. The blobs of the paths in
    `missing` are listed but reported missing, as in a repository that lost
    them. Every call is recorded in `calls`.
    """

    def __init__(self, files: dict[str, bytes], missing: tuple[str, ...] = ()) -> None:
        self.files = files
        self.missing = {_oid(files[path]) for path in missing}
        self.calls: list[list[str]] = []

    def __call__(self, args: list[str], stdin: bytes | None = None) -> bytes:
        self.calls.append(args)
        if args[:3] == ["ls-tree", "-r", "-z"] and args[4:] == ["plots/"]:
            return b"".join(
                b"100644 blob %s\t%s\0" % (_oid(content).encode(), path.encode())
                for path, content in sorted(self.files.items())
            )
        if args == ["cat-file", "--batch"] and stdin is not None:
            blobs = {_oid(content): content for content in self.files.values()}
            return b"".join(
                _blob_record(blobs[oid]) if oid in blobs and oid not in self.missing else b"%s missing\n" % oid.encode()
                for oid in stdin.decode().splitlines()
            )
        raise AssertionError(f"unexpected git call: {args}")


def _meta(spec_id: str, lib: str) -> str:
    return f"plots/{spec_id}/metadata/python/{lib}.yaml"


# One catalogue that exercises every rule pick_oldest applies.
TREE = {
    "plots/README.md": b"# not a spec\n",
    # Hidden directory: never a spec, however old its metadata.
    _meta(".archive", "matplotlib"): b"created: '2020-01-01T00:00:00Z'\n",
    # No python metadata: not eligible, although it has no timestamp at all.
    "plots/bar-basic/specification.md": b"# bar-basic\n",
    "plots/bar-basic/metadata/r/ggplot2.yaml": b"updated: '2020-01-01T00:00:00Z'\n",
    # Latest of two files.
    _meta("line-basic", "altair"): b"updated: '2026-03-01T00:00:00Z'\n",
    _meta("line-basic", "plotly"): b"updated: '2026-01-10T00:00:00Z'\n",
    # Datetimes, not strings: `.5+00:00` is later although it sorts before `Z`.
    _meta("scatter-basic", "bokeh"): b"updated: '2026-02-01T00:00:00Z'\n",
    _meta("scatter-basic", "pygal"): b"updated: '2026-02-01T00:00:00.500000+00:00'\n",
    # `created` stands in for a missing `updated`.
    _meta("pie-basic", "seaborn"): b"created: '2026-01-15T00:00:00+00:00'\n",
    # Same instant as pie-basic, written differently: the tie goes to the
    # alphabetically first id. A missing blob and a file that is not valid
    # YAML both carry later timestamps and must be skipped.
    _meta("heatmap-basic", "altair"): b"updated: '2026-01-15T00:00:00Z'\nlibrary: altair\n",
    _meta("heatmap-basic", "broken"): b"updated: '2027-01-01T00:00:00Z\n",
    _meta("heatmap-basic", "lost"): b"updated: '2027-06-01T00:00:00Z'\n",
    "plots/heatmap-basic/metadata/python/README.md": b"updated: '2010-01-01T00:00:00Z'\n",
    "plots/heatmap-basic/metadata/python/old/plotly.yaml": b"updated: '2010-01-01T00:00:00Z'\n",
}
MISSING = (_meta("heatmap-basic", "lost"),)


@pytest.fixture
def fake_git(monkeypatch):
    def install(files: dict[str, bytes] = TREE, missing: tuple[str, ...] = MISSING) -> FakeGit:
        fake = FakeGit(files, missing)
        monkeypatch.setattr(picker, "_git", fake)
        return fake

    return install


def test_parse_batch_cuts_objects_by_announced_size():
    first = b"updated: '2026-01-02T00:00:00Z'\n"
    broken = b"updated: '2027-01-01T00:00:00Z\n"
    # Lines that look like batch headers, and no final newline of its own.
    tricky = b"created: '2026-01-03T00:00:00Z'\nnote: \"one\n%s blob 3\nabc missing\"" % (b"0" * 40)
    stream = (
        _blob_record(first)
        + b"%s missing\n" % (b"f" * 40)
        + _blob_record(broken)
        + _blob_record(tricky)
        + b"%s tree 0\n\n" % (b"e" * 40)
    )

    blobs = _parse_batch(stream, 5)

    assert blobs == [first, None, broken, tricky, None]
    assert [_timestamp(blob) for blob in blobs] == [
        "2026-01-02T00:00:00Z",
        None,  # missing object
        None,  # YAML error
        "2026-01-03T00:00:00Z",
        None,  # not a blob
    ]


@pytest.mark.parametrize(
    "stream",
    [
        pytest.param(_blob_record(b"a: 1\n")[:-3], id="content cut short"),
        pytest.param(_blob_record(b"a: 1\n") + b"extra", id="bytes past the last object"),
        pytest.param(b"fatal: something else\n", id="unknown header"),
        pytest.param(b"", id="fewer objects than requested"),
    ],
)
def test_parse_batch_rejects_a_malformed_stream(stream):
    with pytest.raises(ValueError):
        _parse_batch(stream, 1)


@pytest.mark.parametrize(
    ("blob", "expected"),
    [
        pytest.param(
            b"updated: '2026-01-02T00:00:00Z'\ncreated: '2025-01-01T00:00:00Z'\n",
            "2026-01-02T00:00:00Z",
            id="updated wins",
        ),
        pytest.param(b"updated:\ncreated: '2025-01-01T00:00:00Z'\n", "2025-01-01T00:00:00Z", id="empty updated"),
        pytest.param(b"updated: 2026-01-02T00:00:00Z\n", "2026-01-02 00:00:00+00:00", id="unquoted timestamp"),
        pytest.param(b"", None, id="empty document"),
        pytest.param(b"- a list, not a mapping\n", None, id="not a mapping"),
        pytest.param(b"updated: '\xff'\n", None, id="not UTF-8"),
    ],
)
def test_timestamp_reads_updated_then_created(blob, expected):
    assert _timestamp(blob) == expected


def test_group_listing_maps_each_spec_to_its_metadata_blobs():
    records = [
        (b"100644 blob " + b"1" * 40, b"plots/README.md"),
        (b"100644 blob " + b"2" * 40, b"plots/.archive/metadata/python/matplotlib.yaml"),
        (b"100644 blob " + b"3" * 40, b"plots/area-basic/metadata/python/altair.yaml"),
        (b"100644 blob " + b"4" * 40, b"plots/area-basic/metadata/python/notes.md"),
        (b"100644 blob " + b"5" * 40, b"plots/area-basic/metadata/python/old/plotly.yaml"),
        (b"160000 commit " + b"6" * 40, b"plots/area-basic/metadata/python/submodule.yaml"),
        (b"100644 blob " + b"7" * 40, b"plots/area-basic/metadata/python/seaborn.yaml"),
        (b"100644 blob " + b"8" * 40, b"plots/area-basic/metadata/r/ggplot2.yaml"),
        (b"100644 blob " + b"9" * 40, b"plots/bar-basic/specification.md"),
    ]
    listing = b"".join(b"%s\t%s\0" % record for record in records)

    assert _group_listing(listing) == {
        "area-basic": [
            ("plots/area-basic/metadata/python/altair.yaml", "3" * 40),
            ("plots/area-basic/metadata/python/seaborn.yaml", "7" * 40),
        ],
        "bar-basic": [],
    }


def test_listing_helpers_read_the_fake_tree(fake_git):
    fake_git()

    assert _list_spec_dirs("main") == ["bar-basic", "heatmap-basic", "line-basic", "pie-basic", "scatter-basic"]
    assert _list_metadata_files("heatmap-basic", "main") == [
        _meta("heatmap-basic", name) for name in ("altair", "broken", "lost")
    ]
    assert _list_metadata_files("bar-basic", "main") == []


def test_pick_oldest_on_a_fixed_tree(fake_git):
    fake = fake_git()

    assert pick_oldest("main") == ("heatmap-basic", "2026-01-15T00:00:00Z")
    # The whole catalogue costs one listing and one batch read.
    assert [call[0] for call in fake.calls] == ["ls-tree", "cat-file"]


def test_pick_oldest_prefers_a_spec_without_any_timestamp(fake_git):
    fake_git({**TREE, _meta("violin-basic", "altair"): b"library: altair\n"})

    assert pick_oldest("main") == ("violin-basic", "0001-01-01T00:00:00+00:00")


def test_validate_spec_on_a_fixed_tree(fake_git):
    fake = fake_git()

    assert validate_spec("scatter-basic", "main") == ("scatter-basic", "2026-02-01T00:00:00.500000+00:00")
    assert validate_spec("line-basic", "main") == ("line-basic", "2026-03-01T00:00:00Z")
    # A spec without python metadata exists, with the floor timestamp and no batch read.
    fake.calls.clear()
    assert validate_spec("bar-basic", "main") == ("bar-basic", "0001-01-01T00:00:00+00:00")
    assert [call[0] for call in fake.calls] == ["ls-tree"]


@pytest.mark.parametrize("spec_id", ["", "../etc/passwd", "plots/line-basic", ".archive"])
def test_validate_spec_rejects_an_invalid_id_before_calling_git(fake_git, spec_id):
    fake = fake_git()

    with pytest.raises(LookupError, match="Invalid spec id"):
        validate_spec(spec_id, "main")
    assert fake.calls == []


def test_validate_spec_unknown_id_on_a_fixed_tree(fake_git):
    fake_git()

    with pytest.raises(LookupError, match="does not exist"):
        validate_spec("area-basic", "main")


def test_unlistable_ref_finds_no_specs(monkeypatch):
    def failing_git(args, stdin=None):
        raise subprocess.CalledProcessError(128, ["git", *args])

    monkeypatch.setattr(picker, "_git", failing_git)

    with pytest.raises(LookupError, match="No eligible specs"):
        pick_oldest("no-such-ref")
    with pytest.raises(LookupError, match="does not exist"):
        validate_spec("line-basic", "no-such-ref")


def test_failed_batch_read_raises_instead_of_picking_blind(monkeypatch, fake_git):
    fake = fake_git()

    def git(args, stdin=None):
        if args[0] == "cat-file":
            raise subprocess.CalledProcessError(128, ["git", *args])
        return fake(args, stdin)

    monkeypatch.setattr(picker, "_git", git)

    with pytest.raises(subprocess.CalledProcessError):
        pick_oldest("main")
