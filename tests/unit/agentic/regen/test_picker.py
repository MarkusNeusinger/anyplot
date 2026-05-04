"""Tests for `agentic.workflows.modules.regen.picker`.

These hit real git via subprocess against the live repo's `origin/main`.
We don't rebuild a fixture repo because the picker's whole point is that
it reads from the existing remote ref — and a synthetic ref is more
expensive than a smoke test that exercises the same paths.
"""

from __future__ import annotations

import pytest

from agentic.workflows.modules.regen.picker import _list_metadata_files, _list_spec_dirs, pick_oldest, validate_spec


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
