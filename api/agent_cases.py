"""Feedback cases of the agent chat: what `POST /debug/agent/sessions/{sid}/feedback` stores, and where.

A case is the agents service's bundle of one result version (`GET /v1/sessions/{sid}/bundle
?version=<n>`), split into files under `cases/<case_id>/` in the private bucket
`AGENT_CASES_BUCKET` (`settings.agent_cases_bucket`):

* `plot-light.png`, `plot-dark.png`: the version's PNGs as the user saw them, footer strip
  included, decoded from the bundle's base64; a theme the version never rendered has none;
* `plot.py`: the exported code;
* `data.csv`: the version's data, only when the user ticked `# include data.csv`;
* `manifest.json`: the case's row (every field the design names for the later
  `agent_feedback` table, so a table can be filled from the manifests) plus the whole
  bundle without the PNGs and the data, which are the sibling files. Written LAST: a case
  directory without a manifest is an aborted write and never a case.

The case id is the UTC time in ISO 8601 basic format plus 8 random hex digits
(`20261012T143005Z-1a2b3c4d`), so ids sort by time. Every upload carries
`if_generation_match=0`: a write never replaces an object, so no case can overwrite
another. Nothing here deletes: a later submission for the same result version is a new
case whose manifest names the earlier one in `replaces` (the id the page got for it), and
the triage counts the newest case of a `session_hash` and `result_version`. The bucket's
lifecycle rule (delete after 180 days) is the retention, also for a replaced case and its
`data.csv`, and it removes the files of an aborted write. Design:
`docs/concepts/agent-network.md` ("Feedback capture").

Everything in this module is blocking (JSON, base64, the GCS client); the route runs it
in a worker thread.
"""

from __future__ import annotations

import base64
import binascii
import functools
import hashlib
import json
import math
import re
import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol


CASE_PREFIX = "cases"
CASE_ID_PATTERN = r"^[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$"
"""What `new_case_id` makes, and what a submission's `replaces` must look like."""
MANIFEST_NAME = "manifest.json"
MANIFEST_SCHEMA = 1
CASE_STATUS_NEW = "new"
"""The status of a fresh case; the triage moves it to `in_progress`, `done` or `wont_solve`."""

CASE_MEDIA_TYPES: dict[str, str] = {
    MANIFEST_NAME: "application/json",
    "plot-light.png": "image/png",
    "plot-dark.png": "image/png",
    "plot.py": "text/x-python; charset=utf-8",
    "data.csv": "text/csv; charset=utf-8",
}
"""Every file a case can hold, with the content type it is stored under."""

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_THEMES = ("light", "dark")
_FILE_KEYS = frozenset({"images", "data_csv"})
"""The version fields that become files of their own and stay out of the manifest's `bundle`."""
# The first line of an exported `plot.py` (agents/anyplot/code/export.py, `attribution`):
# `# Adapted by anyplot.ai from <spec> (<library>[ <version>]) for your data.csv;`.
_EXPORT_LIBRARY = re.compile(r"\A# Adapted by anyplot\.ai from [a-z0-9-]+ \(([a-z][a-z0-9]*)[ )]")


class BundleError(ValueError):
    """The agents service's bundle is not what its route documents; the BFF answers `502 upstream`."""


class CaseBucket(Protocol):
    """Where the case files go: the private case bucket in production, a fake in the tests."""

    def upload(self, name: str, data: bytes, content_type: str) -> None:
        """Store `data` as the object `name`; raise when it is not stored, and never replace an object."""


@functools.cache
def _storage_client() -> Any:
    """One GCS client per process, created on first use (Application Default Credentials)."""
    from google.cloud.storage import Client

    return Client()


class GcsCaseBucket:
    """The case bucket through `google-cloud-storage`, the library `core/images.py` uses too."""

    def __init__(self, bucket: str) -> None:
        self.bucket = bucket

    def upload(self, name: str, data: bytes, content_type: str) -> None:
        from google.api_core.exceptions import PreconditionFailed

        blob = _storage_client().bucket(self.bucket).blob(name)
        try:
            # `if_generation_match=0` creates the object only when none exists under that name.
            blob.upload_from_string(data, content_type=content_type, if_generation_match=0)
        except PreconditionFailed:
            # The object exists. Every case id is new and its object names are written once,
            # so this is the upload's own object: the library retried a request whose first
            # attempt stored it but lost the response, and the retry met the stored object.
            return


@dataclass(frozen=True)
class Submission:
    """What the user sent with the feedback control."""

    reaction: str
    message: str | None
    include_data: bool
    result_version: int
    replaces: str | None = None
    """The case id of the earlier submission for the same version that this one replaces."""


@dataclass(frozen=True)
class CaseFile:
    name: str
    data: bytes

    @property
    def content_type(self) -> str:
        return CASE_MEDIA_TYPES[self.name]


@dataclass(frozen=True)
class FeedbackCase:
    """One case, its files in upload order: the manifest is the last one."""

    case_id: str
    files: tuple[CaseFile, ...]

    @property
    def stored(self) -> list[str]:
        """The file names, as the route answers them."""
        return [item.name for item in self.files]


def new_case_id(now: datetime) -> str:
    """`<UTC time, ISO 8601 basic>-<8 random hex digits>`, such as `20261012T143005Z-1a2b3c4d`."""
    return f"{now:%Y%m%dT%H%M%SZ}-{secrets.token_hex(4)}"


def session_hash(session_id: str) -> str:
    """The first 16 hex digits of the session id's SHA-256: groups a session's cases without naming it."""
    return hashlib.sha256(session_id.encode()).hexdigest()[:16]


def prompt_hash(prompt_hashes: Any) -> str | None:
    """One hash over the config stamp's per-prompt hashes (the table's single `prompt_hash` column).

    The first 16 hex digits of the SHA-256 of the sorted, compact JSON of the map, so two
    cases share it exactly when every prompt is the same; None without a usable map. The
    map itself stays in the manifest's `bundle.config`.
    """
    if not isinstance(prompt_hashes, dict) or not prompt_hashes:
        return None
    if not all(isinstance(key, str) and isinstance(value, str) for key, value in prompt_hashes.items()):
        return None
    canonical = json.dumps(prompt_hashes, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def _text(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _count(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value) if math.isfinite(value) and value >= 0 else None


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def version_library(version: dict[str, Any], session: dict[str, Any]) -> str | None:
    """The library the version was adapted for.

    The bundle's version items carry no `library` yet, and the session's library is the
    one at submission time, which differs after a library switch. So: the version's own
    `library` when a newer agents service sends one, else the library the exported
    `plot.py` names in its first line, else the session's.
    """
    own = _text(version.get("library"))
    if own:
        return own
    code = version.get("plot_py")
    match = _EXPORT_LIBRARY.match(code) if isinstance(code, str) else None
    if match:
        return match.group(1)
    return _text(session.get("library"))


def _png(encoded: Any, theme: str) -> bytes:
    if not isinstance(encoded, str):
        raise BundleError(f"the {theme} image is not base64 text")
    try:
        data = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise BundleError(f"the {theme} image is not valid base64") from exc
    if not data.startswith(_PNG_SIGNATURE):
        raise BundleError(f"the {theme} image is not a PNG")
    return data


def _utf8(text: str, name: str) -> bytes:
    try:
        return text.encode("utf-8")
    except UnicodeEncodeError as exc:  # a lone surrogate, which UTF-8 cannot carry
        raise BundleError(f"{name} is not valid text") from exc


def build_case(
    content: bytes,
    submission: Submission,
    *,
    case_id: str,
    created_at: datetime,
    bucket: str,
    user_hash: str,
    session_id: str,
) -> FeedbackCase:
    """Split the bundle of one result version into the case's files; raises `BundleError` for a malformed one.

    The bundle must be a JSON object whose `versions` hold the submitted version: the
    BFF asks the agents service for exactly that one, which answers `404 not_found`
    when the session has no such version.
    """
    try:
        bundle = json.loads(content)
    except (ValueError, RecursionError) as exc:
        raise BundleError("the bundle is not JSON") from exc
    if not isinstance(bundle, dict):
        raise BundleError("the bundle is not a JSON object")
    versions = bundle.get("versions")
    if not isinstance(versions, list):
        raise BundleError("the bundle has no version list")
    version = next(
        (item for item in versions if isinstance(item, dict) and item.get("number") == submission.result_version), None
    )
    if version is None:
        raise BundleError("the bundle lacks the submitted version")

    files: list[CaseFile] = []
    images = _dict(version.get("images"))
    for theme in _THEMES:
        if theme in images:
            files.append(CaseFile(f"plot-{theme}.png", _png(images[theme], theme)))
    code = version.get("plot_py")
    if isinstance(code, str) and code:
        files.append(CaseFile("plot.py", _utf8(code, "plot.py")))
    data_csv = version.get("data_csv")
    if submission.include_data and isinstance(data_csv, str) and data_csv:
        files.append(CaseFile("data.csv", _utf8(data_csv, "data.csv")))

    # The bundle as the manifest keeps it: without the PNGs and the data, which are files of their own.
    kept = {
        **bundle,
        "versions": [
            {key: value for key, value in item.items() if key not in _FILE_KEYS} if isinstance(item, dict) else item
            for item in versions
        ],
    }

    session = _dict(bundle.get("session"))
    config = _dict(bundle.get("config"))
    result = _dict(version.get("result"))
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "id": case_id,
        "created_at": created_at.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "case_uri": f"gs://{bucket}/{CASE_PREFIX}/{case_id}/",
        "user_hash": user_hash,
        "session_hash": session_hash(session_id),
        "spec_id": _text(session.get("spec_id")),
        "library_id": version_library(version, session),
        "language": _text(session.get("locale")),
        "reaction": submission.reaction,
        "message": submission.message,
        "include_data": submission.include_data,
        "status": CASE_STATUS_NEW,
        "result_version": submission.result_version,
        # As the page sent it, unchecked: the triage is to honour it only for a case of the same session and version.
        "replaces": submission.replaces,
        "model": _text(config.get("model")),
        # Not in the agents service's config stamp yet: null until it sends them.
        "model_version": _text(config.get("model_version")),
        "judge_model": _text(config.get("judge_model")),
        "prompt_hash": prompt_hash(config.get("prompt_hashes")),
        "pipeline_status": _text(result.get("status")),
        "attempts": _count(result.get("attempts")),
        "tokens": _count(config.get("tokens")),
        "cost_estimate": _number(config.get("cost_estimate")),
        "files": [item.name for item in files] + [MANIFEST_NAME],
        "bundle": kept,
    }
    try:
        text = json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False)
    except ValueError as exc:  # NaN or Infinity, which the agents service's JSON never holds
        raise BundleError("the bundle holds a number JSON cannot carry") from exc
    files.append(CaseFile(MANIFEST_NAME, _utf8(text, MANIFEST_NAME)))
    return FeedbackCase(case_id=case_id, files=tuple(files))


def case_object(case_id: str, name: str) -> str:
    """The object name of one case file: `cases/<case_id>/<name>`."""
    return f"{CASE_PREFIX}/{case_id}/{name}"


def write_case(bucket: CaseBucket, case: FeedbackCase) -> None:
    """Upload the case's files in order, the manifest last; the first failure stops the rest."""
    for item in case.files:
        bucket.upload(case_object(case.case_id, item.name), item.data, item.content_type)
