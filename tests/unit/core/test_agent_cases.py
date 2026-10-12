"""
Tests for core/agent_cases.py — the manifest-to-row mapping of the agent chat's feedback cases.

The BFF's own manifest goes through the same mapping in tests/unit/api/test_agent_cases.py;
here a literal manifest of schema 1 pins every key.
"""

import re
from datetime import datetime

import pytest

from core.agent_cases import (
    CASE_FILE_NAMES,
    CASE_ID_PATTERN,
    EXPECTED_BY_REACTION,
    MAX_TAGS,
    TAG_PATTERN,
    ManifestError,
    case_object,
    row_from_manifest,
)
from core.database import AGENT_CASE_EXPECTED, CASE_ID_LENGTH, FEEDBACK_REACTIONS, AgentFeedback


CASE_ID = "20261012T143005Z-1a2b3c4d"
TRIAGE_COLUMNS = {"tags", "expected", "promoted_at", "superseded_by", "updated_at"}


def _manifest(**overrides) -> dict:
    """A manifest of schema 1 as `api.agent_cases.build_case` writes it."""
    manifest = {
        "schema": 1,
        "id": CASE_ID,
        "created_at": "2026-10-12T14:30:05Z",
        "case_uri": f"gs://anyplot-agent-cases/cases/{CASE_ID}/",
        "user_hash": "adm_0123456789abcdef",
        "session_hash": "fedcba9876543210",
        "spec_id": "scatter-basic",
        "library_id": "matplotlib",
        "language": "de-CH",
        "reaction": "thumbs_down",
        "message": "the legend hides the points",
        "include_data": True,
        "status": "new",
        "result_version": 3,
        "replaces": None,
        "model": "claude-haiku-5-5",
        "model_version": None,
        "judge_model": "claude-haiku-5-5",
        "prompt_hash": "0123456789abcdef",
        "pipeline_status": "needs_attention",
        "attempts": 2,
        "tokens": None,
        "cost_estimate": None,
        "files": ["plot-light.png", "plot-dark.png", "plot.py", "data.csv", "manifest.json"],
        "bundle": {"transcript": [{"role": "user", "text": "secret content"}]},
    }
    return {**manifest, **overrides}


def test_every_manifest_key_maps_to_its_column() -> None:
    row = row_from_manifest(_manifest())

    assert row == {
        "id": CASE_ID,
        "manifest_schema": 1,
        "created_at": datetime(2026, 10, 12, 14, 30, 5),
        "case_uri": f"gs://anyplot-agent-cases/cases/{CASE_ID}/",
        "user_hash": "adm_0123456789abcdef",
        "session_hash": "fedcba9876543210",
        "spec_id": "scatter-basic",
        "library_id": "matplotlib",
        "locale": "de-CH",
        "reaction": "thumbs_down",
        "message": "the legend hides the points",
        "include_data": True,
        "status": "new",
        "result_version": 3,
        "replaces": None,
        "model": "claude-haiku-5-5",
        "model_version": None,
        "judge_model": "claude-haiku-5-5",
        "prompt_hash": "0123456789abcdef",
        "pipeline_status": "needs_attention",
        "attempts": 2,
        "tokens": None,
        "cost_estimate": None,
        "files": ["plot-light.png", "plot-dark.png", "plot.py", "data.csv", "manifest.json"],
    }
    # Naive UTC, like every timestamp column of the schema.
    assert row["created_at"].tzinfo is None


def test_the_row_fills_every_column_but_the_triage_state_and_never_the_content() -> None:
    row = row_from_manifest(_manifest())
    columns = {column.name for column in AgentFeedback.__table__.columns}
    assert set(row) == columns - TRIAGE_COLUMNS
    assert "bundle" not in row
    assert "secret content" not in repr(row)


def test_the_row_builds_a_model_instance() -> None:
    entity = AgentFeedback(**row_from_manifest(_manifest()))
    assert entity.id == CASE_ID
    assert entity.locale == "de-CH"


@pytest.mark.parametrize("replaces", [None, "absent"])
def test_replaces_null_or_absent_is_none(replaces) -> None:
    manifest = _manifest()
    if replaces == "absent":
        del manifest["replaces"]
    assert row_from_manifest(manifest)["replaces"] is None


def test_replaces_keeps_a_case_id() -> None:
    earlier = "20261012T140000Z-00ff00ff"
    assert row_from_manifest(_manifest(replaces=earlier))["replaces"] == earlier


@pytest.mark.parametrize(
    ("overrides", "field"),
    [
        ({"schema": 2}, "schema"),
        ({"schema": True}, "schema"),
        ({"schema": "1"}, "schema"),
        ({"id": "20261012T143005Z-1A2B3C4D"}, "id"),
        ({"id": "case-1"}, "id"),
        ({"id": None}, "id"),
        ({"created_at": "2026-10-12T14:30:05+00:00"}, "created_at"),
        ({"created_at": "2026-10-12 14:30:05"}, "created_at"),
        ({"created_at": 1760279405}, "created_at"),
        ({"reaction": "love"}, "reaction"),
        ({"reaction": None}, "reaction"),
        ({"status": "retired"}, "status"),
        ({"include_data": "true"}, "include_data"),
        ({"include_data": 1}, "include_data"),
        ({"result_version": 0}, "result_version"),
        ({"result_version": 1000}, "result_version"),
        ({"result_version": True}, "result_version"),
        ({"result_version": "3"}, "result_version"),
        ({"files": "plot.py"}, "files"),
        ({"files": ["plot.py", "secrets.txt"]}, "files"),
        ({"replaces": "abc"}, "replaces"),
        ({"replaces": "20261012T143005Z-1a2b3c4d0"}, "replaces"),
        ({"replaces": 20261012}, "replaces"),
        ({"case_uri": ""}, "case_uri"),
        ({"user_hash": None}, "user_hash"),
        ({"session_hash": 12}, "session_hash"),
        # Longer than its column: refused, never cut, and never a database error.
        ({"user_hash": "adm_" + "0" * 17}, "user_hash"),
        ({"spec_id": "s" * 101}, "spec_id"),
        ({"language": "de-CH-x-" + "a" * 20}, "language"),
    ],
)
def test_a_malformed_manifest_is_refused_with_the_field_named(overrides, field) -> None:
    with pytest.raises(ManifestError, match=field):
        row_from_manifest(_manifest(**overrides))


@pytest.mark.parametrize("manifest", [None, [], "manifest", 1])
def test_a_manifest_that_is_no_object_is_refused(manifest) -> None:
    with pytest.raises(ManifestError):
        row_from_manifest(manifest)


def test_a_missing_required_field_is_refused() -> None:
    for field in ("schema", "id", "created_at", "case_uri", "user_hash", "session_hash", "reaction", "status"):
        manifest = _manifest()
        del manifest[field]
        with pytest.raises(ManifestError, match=field):
            row_from_manifest(manifest)


@pytest.mark.parametrize(
    ("overrides", "column", "expected"),
    [
        ({"message": ""}, "message", None),
        ({"model": 5}, "model", None),
        ({"language": ["de"]}, "locale", None),
        ({"attempts": "2"}, "attempts", None),
        ({"attempts": True}, "attempts", None),
        ({"attempts": -1}, "attempts", None),
        ({"tokens": 2**31}, "tokens", None),
        ({"tokens": 1200}, "tokens", 1200),
        ({"cost_estimate": "0.1"}, "cost_estimate", None),
        ({"cost_estimate": True}, "cost_estimate", None),
        ({"cost_estimate": 2}, "cost_estimate", 2.0),
        ({"cost_estimate": 0.0042}, "cost_estimate", 0.0042),
    ],
)
def test_an_optional_field_of_another_type_is_none(overrides, column, expected) -> None:
    assert row_from_manifest(_manifest(**overrides))[column] == expected


def test_an_absent_optional_field_is_none() -> None:
    manifest = _manifest()
    for key in ("spec_id", "library_id", "language", "message", "model", "attempts", "cost_estimate"):
        del manifest[key]
    row = row_from_manifest(manifest)
    assert [row[column] for column in ("spec_id", "library_id", "locale", "message", "model")] == [None] * 5
    assert row["attempts"] is None
    assert row["cost_estimate"] is None


def test_case_object_names_a_file_under_the_case_prefix() -> None:
    assert case_object(CASE_ID, "plot.py") == f"cases/{CASE_ID}/plot.py"


def test_the_case_id_pattern_fits_the_id_column() -> None:
    assert re.fullmatch(CASE_ID_PATTERN, CASE_ID)
    assert len(CASE_ID) == CASE_ID_LENGTH
    assert CASE_FILE_NAMES[-1] == "manifest.json"


@pytest.mark.parametrize(("tag", "valid"), [("legend-overlap", True), ("a" * 40, True), ("a" * 41, False)])
def test_tags_are_lowercase_slugs(tag, valid) -> None:
    assert bool(re.fullmatch(TAG_PATTERN, tag)) is valid
    for bad in ("Legend", "legend overlap", "legend_overlap", ""):
        assert not re.fullmatch(TAG_PATTERN, bad)
    assert MAX_TAGS == 10


def test_the_reaction_rule_maps_thumbs_onto_an_expected_outcome() -> None:
    assert EXPECTED_BY_REACTION == {"thumbs_up": "accepted", "thumbs_down": "rejected"}
    assert set(EXPECTED_BY_REACTION) <= set(FEEDBACK_REACTIONS)
    assert set(EXPECTED_BY_REACTION.values()) == set(AGENT_CASE_EXPECTED)
