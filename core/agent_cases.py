"""Feedback cases of the agent chat as the `agent_feedback` table sees them.

A case is a directory `cases/<case_id>/` in the private case bucket, written by the BFF's
feedback route (`api/agent_cases.py`), whose `manifest.json` carries one value for every
column of the case's row. This module holds what more than one side needs: the case id
and object names, the triage rules for tags and the expected outcome, and
`row_from_manifest`, which turns a manifest into the row. The route inserts that row right
after the upload, and the dev machine's sync CLI (`agents/evals/sync_cases.py`) indexes a
case that reached the bucket without one; both read the mapping from here, so it has one
home. Design: docs/concepts/agent-network.md ("Feedback capture").
"""

from __future__ import annotations

import math
import re
from datetime import datetime
from typing import Any, TypeIs

from sqlalchemy import String

from core.database.models import FEEDBACK_REACTIONS, FEEDBACK_STATUSES, AgentFeedback


CASE_PREFIX = "cases"
CASE_ID_PATTERN = r"^[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$"
"""What `api.agent_cases.new_case_id` makes, and what a submission's `replaces` must look like."""
MANIFEST_NAME = "manifest.json"
MANIFEST_SCHEMA = 1
CASE_FILE_NAMES = ("plot-light.png", "plot-dark.png", "plot.py", "data.csv", MANIFEST_NAME)
"""Every file a case can hold; a case's manifest lists the ones it has."""
TAG_PATTERN = r"^[a-z0-9-]{1,40}$"
"""A triage tag: a lowercase slug, such as `legend-overlap`."""
MAX_TAGS = 10
EXPECTED_BY_REACTION = {"thumbs_up": "accepted", "thumbs_down": "rejected"}
"""The outcome a promoted case expects when the owner names none: the reaction rule.

`bug` and `idea` do not map to an outcome, so promoting one needs an explicit choice.
The importer (`agents/evals/import_case.py`) applies the same rule to a case without one.
"""

_CASE_ID = re.compile(CASE_ID_PATTERN)
_CREATED_AT_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
_MAX_INTEGER = 2**31 - 1
"""The largest value of a PostgreSQL `INTEGER` column."""
_MAX_LENGTH: dict[str, int] = {
    column.name: column.type.length
    for column in AgentFeedback.__table__.columns
    if isinstance(column.type, String) and column.type.length is not None
}
"""The `VARCHAR` length of every bounded text column, read from the model."""


class ManifestError(ValueError):
    """A manifest that is not schema 1 or lacks a required field; the message names the field."""


def case_object(case_id: str, name: str) -> str:
    """The object name of one case file: `cases/<case_id>/<name>`."""
    return f"{CASE_PREFIX}/{case_id}/{name}"


def _required_text(manifest: dict[str, Any], key: str, column: str | None = None) -> str:
    value = manifest.get(key)
    if not isinstance(value, str) or not value:
        raise ManifestError(f"{key} is not a non-empty string")
    return _bounded(value, key, column or key)


def _optional_text(manifest: dict[str, Any], key: str, column: str | None = None) -> str | None:
    value = manifest.get(key)
    if not isinstance(value, str) or not value:
        return None
    return _bounded(value, key, column or key)


def _bounded(value: str, key: str, column: str) -> str:
    # Over the column's length is refused here, not truncated: a cut value would misstate the
    # case, and a database error would count as a failed insert instead of a malformed manifest.
    limit = _MAX_LENGTH.get(column)
    if limit is not None and len(value) > limit:
        raise ManifestError(f"{key} is longer than {limit} characters")
    return value


def _is_int(value: Any) -> TypeIs[int]:
    """An integer that is not a boolean (`True == 1` would pass for schema 1 otherwise)."""
    return isinstance(value, int) and not isinstance(value, bool)


def _optional_count(value: Any) -> int | None:
    return value if _is_int(value) and 0 <= value <= _MAX_INTEGER else None


def _optional_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value) if math.isfinite(value) else None


def row_from_manifest(manifest: Any) -> dict[str, Any]:
    """The `agent_feedback` columns a manifest fills; raises `ManifestError` on a malformed one.

    Required: `schema == 1`, `id` matching CASE_ID_PATTERN, `created_at` as `YYYY-MM-DDTHH:MM:SSZ`,
    `case_uri`, `user_hash`, `session_hash` (non-empty str), `reaction` in FEEDBACK_REACTIONS,
    `status` in FEEDBACK_STATUSES, `include_data` bool, `result_version` int from 0 to 999
    (0: the chat's case, of a session that made no plot),
    `files` a list of CASE_FILE_NAMES. Optional (None when absent or null): spec_id, library_id,
    language -> locale, message, model, model_version, judge_model, prompt_hash,
    pipeline_status, attempts, tokens, cost_estimate; a value of another type is None too.
    `replaces` is the exception: None when absent or null, the string when it matches
    CASE_ID_PATTERN, and ManifestError otherwise (a stray value must never reach the
    VARCHAR(25) column as a database error, which the backfill would count as `failed`
    instead of `skipped`). A text longer than its column is a ManifestError for the same reason.
    Never sets tags, expected, promoted_at, superseded_by, updated_at.
    """
    if not isinstance(manifest, dict):
        raise ManifestError("the manifest is not a JSON object")
    schema = manifest.get("schema")
    if not _is_int(schema) or schema != MANIFEST_SCHEMA:
        raise ManifestError(f"schema is not {MANIFEST_SCHEMA}")
    case_id = manifest.get("id")
    if not isinstance(case_id, str) or not _CASE_ID.fullmatch(case_id):
        raise ManifestError("id is not a case id")
    created_at = manifest.get("created_at")
    try:
        created = datetime.strptime(created_at, _CREATED_AT_FORMAT) if isinstance(created_at, str) else None
    except ValueError:
        created = None
    if created is None:
        raise ManifestError("created_at is not YYYY-MM-DDTHH:MM:SSZ")
    reaction = manifest.get("reaction")
    if reaction not in FEEDBACK_REACTIONS:
        raise ManifestError("reaction is not one of the feedback reactions")
    status = manifest.get("status")
    if status not in FEEDBACK_STATUSES:
        raise ManifestError("status is not one of the triage states")
    include_data = manifest.get("include_data")
    if not isinstance(include_data, bool):
        raise ManifestError("include_data is not a boolean")
    result_version = manifest.get("result_version")
    if not _is_int(result_version) or not 0 <= result_version <= 999:
        raise ManifestError("result_version is not an integer from 0 to 999")
    files = manifest.get("files")
    if not isinstance(files, list) or not all(isinstance(name, str) and name in CASE_FILE_NAMES for name in files):
        raise ManifestError("files is not a list of case file names")
    replaces = manifest.get("replaces")
    if replaces is not None and (not isinstance(replaces, str) or not _CASE_ID.fullmatch(replaces)):
        raise ManifestError("replaces is not a case id")

    return {
        "id": case_id,
        "manifest_schema": schema,
        "created_at": created,
        "case_uri": _required_text(manifest, "case_uri"),
        "user_hash": _required_text(manifest, "user_hash"),
        "session_hash": _required_text(manifest, "session_hash"),
        "spec_id": _optional_text(manifest, "spec_id"),
        "library_id": _optional_text(manifest, "library_id"),
        "locale": _optional_text(manifest, "language", "locale"),
        "reaction": reaction,
        "message": _optional_text(manifest, "message"),
        "include_data": include_data,
        "status": status,
        "result_version": result_version,
        "replaces": replaces,
        "model": _optional_text(manifest, "model"),
        "model_version": _optional_text(manifest, "model_version"),
        "judge_model": _optional_text(manifest, "judge_model"),
        "prompt_hash": _optional_text(manifest, "prompt_hash"),
        "pipeline_status": _optional_text(manifest, "pipeline_status"),
        "attempts": _optional_count(manifest.get("attempts")),
        "tokens": _optional_count(manifest.get("tokens")),
        "cost_estimate": _optional_number(manifest.get("cost_estimate")),
        "files": list(files),
    }
