"""Feedback cases of the agent chat: what `POST /debug/agent/sessions/{sid}/feedback` stores, and where.

A case is the agents service's bundle of one result version (`GET /v1/sessions/{sid}/bundle
?version=<n>`), split into files under `cases/<case_id>/` in the private bucket
`AGENT_CASES_BUCKET` (`settings.agent_cases_bucket`):

* `plot-light.png`, `plot-dark.png`: the version's PNGs as the user saw them, footer strip
  included, decoded from the bundle's base64; a theme the version never rendered has none;
* `plot.py`: the exported code;
* `data.csv`: the version's data, only when the user ticked `# include data.csv`;
* `manifest.json`: the case's row (`core.agent_cases.row_from_manifest` turns it into the
  `agent_feedback` row the route inserts, and the backfill of `sync_cases.py` into one for
  a case that reached the bucket first) plus the whole bundle without the PNGs and the
  data, which are the sibling files. Written LAST: a case directory without a manifest is
  an aborted write and never a case.

The case id is the UTC time in ISO 8601 basic format plus 8 random hex digits
(`20261012T143005Z-1a2b3c4d`), so ids sort by time. Every upload carries
`if_generation_match=0`: a write never replaces an object, so no case can overwrite
another; an upload that meets an object under its name (the library retried a request
whose first attempt stored it) counts as stored only when the stored bytes match, and
anything else is a `CaseConflict`. Nothing here deletes: a later submission for the same result version is a new
case whose manifest names the earlier one in `replaces` (the id the page got for it), and
the row of the earlier case is marked superseded by the new one when `replaces` names it
for the same `session_hash` and `result_version`; nothing is implicit. The bucket's
lifecycle rule (delete after 180 days) is the retention, also for a replaced case and its
`data.csv`, and it removes the files of an aborted write. The triage reads a case back
(`CaseBucket.download`) and compares its code with the catalogue's (`code_diff`). Design:
`docs/concepts/agent-network.md` ("Feedback capture").

Everything in this module is blocking (JSON, base64, the GCS client); the routes run it
in a worker thread.
"""

from __future__ import annotations

import base64
import binascii
import difflib
import functools
import hashlib
import json
import math
import re
import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal, Protocol

# The case id, object names and manifest schema are shared with the table and the sync CLI;
# `CASE_ID_PATTERN` is re-exported for the routes, which validate ids against it.
from core.agent_cases import CASE_ID_PATTERN as CASE_ID_PATTERN
from core.agent_cases import CASE_PREFIX, CODE_FILE_NAMES, MANIFEST_NAME, MANIFEST_SCHEMA, case_object


CASE_STATUS_NEW = "new"
"""The status of a fresh case; the triage moves it to `in_progress`, `done` or `wont_solve`."""

CASE_MEDIA_TYPES: dict[str, str] = {
    MANIFEST_NAME: "application/json",
    "plot-light.png": "image/png",
    "plot-dark.png": "image/png",
    "plot.py": "text/x-python; charset=utf-8",
    "plot.R": "text/plain; charset=utf-8",
    "plot.jl": "text/plain; charset=utf-8",
    "plot.js": "text/javascript; charset=utf-8",
    "plot.tsx": "text/plain; charset=utf-8",
    "data.csv": "text/csv; charset=utf-8",
}
"""Every file a case can hold, with the content type it is stored under. The exported code is stored under its
language's name (`core.agent_cases.CODE_FILE_NAMES`: the bundle's `code_artifact`, `plot.py` for Python and for
bundles from before 2026-10-24)."""

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_THEMES = ("light", "dark")
_FILE_KEYS = frozenset({"images", "data_csv"})
"""The version fields that become files of their own and stay out of the manifest's `bundle`."""
# The first line of an exported `plot.py` (agents/anyplot/code/export.py, `attribution`):
# `# Adapted by anyplot.ai from <spec> (<library>[ <version>]) for your data.csv;`.
_EXPORT_LIBRARY = re.compile(r"\A# Adapted by anyplot\.ai from [a-z0-9-]+ \(([a-z][a-z0-9]*)[ )]")


class BundleError(ValueError):
    """The agents service's bundle is not what its route documents; the BFF answers `502 upstream`."""


class NoChatData(ValueError):
    """The chat's case asked for its data, but the session has none yet; the BFF answers `422 no_data`."""


class CaseConflict(RuntimeError):
    """An object exists under a case file's name with other content; the BFF answers `502 storage`."""


def _md5_base64(data: bytes) -> str:
    """The MD5 of `data` as GCS reports an object's `md5_hash`: the digest in base64."""
    return base64.b64encode(hashlib.md5(data, usedforsecurity=False).digest()).decode("ascii")


class CaseBucket(Protocol):
    """Where the case files go: the private case bucket in production, a fake in the tests."""

    def upload(self, name: str, data: bytes, content_type: str) -> None:
        """Store `data` as the object `name`; raise when it is not stored, and never replace an object."""

    def download(self, name: str) -> bytes | None:
        """The bytes of the object `name`; None when it does not exist (the lifecycle rule deleted it), raise otherwise."""


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
        except PreconditionFailed as exc:
            # An object exists under the name. Every case id is new and each name is written
            # once, so it should be this upload's own first attempt, whose response was lost
            # before the library retried; only identical bytes prove that, so the stored
            # object's MD5 decides, and anything else (a replay, an id collision) is a conflict.
            blob.reload()
            if blob.md5_hash != _md5_base64(data):
                raise CaseConflict(f"{name} exists with other content") from exc

    def download(self, name: str) -> bytes | None:
        from google.api_core.exceptions import NotFound

        try:
            data: bytes = _storage_client().bucket(self.bucket).blob(name).download_as_bytes()
        except NotFound:
            return None
        return data


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
    manifest: dict[str, Any]
    """The manifest as a dict, the same one `manifest.json` holds: the route derives the case's row from it.

    Required on purpose: a case without its manifest is not a case, and a default would turn a
    forgotten assignment into a missing row in production instead of a `TypeError` in the tests.
    """

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


def _code_file_name(version: dict[str, Any]) -> str:
    """The name the version's exported code is stored under: the bundle's `code_artifact` when it is one of the
    known code names, else `plot.py` (bundles from before the agents service sent one)."""
    name = version.get("code_artifact")
    return name if isinstance(name, str) and name in CODE_FILE_NAMES else "plot.py"


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
    when the session has no such version. `result_version` 0 is the chat's case, of a
    session that made no plot: its bundle (`version=0`) holds no version, and the data,
    when asked for, is the bundle's top-level `data_csv`; such a case has no image and no
    `plot.py`.
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
    chat = submission.result_version == 0
    if chat:
        version: dict[str, Any] | None = {"data_csv": bundle.get("data_csv")}
    else:
        version = next(
            (item for item in versions if isinstance(item, dict) and item.get("number") == submission.result_version),
            None,
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
        code_name = _code_file_name(version)
        files.append(CaseFile(code_name, _utf8(code, code_name)))
    if submission.include_data:
        data_csv = version.get("data_csv")
        # Asked for and absent is a malformed bundle: a manifest must never claim data the case lacks.
        if chat and data_csv is None and "data_csv" in bundle:
            # The service said so: no data pasted or computed yet. The user's choice, not a malformed bundle.
            raise NoChatData("the session has no data yet")
        if not isinstance(data_csv, str) or not data_csv:
            what = "the chat has" if chat else "the version has"
            raise BundleError(f"{what} no data.csv although the data was asked for")
        files.append(CaseFile("data.csv", _utf8(data_csv, "data.csv")))

    # The bundle as the manifest keeps it: without the PNGs and the data, which are files of their own.
    kept = {
        **{key: value for key, value in bundle.items() if key != "data_csv"},
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
        # As the page sent it: the row insert supersedes the named case only for the same session and version.
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
    return FeedbackCase(case_id=case_id, files=tuple(files), manifest=manifest)


def write_case(bucket: CaseBucket, case: FeedbackCase) -> None:
    """Upload the case's files in order, the manifest last; the first failure stops the rest."""
    for item in case.files:
        bucket.upload(case_object(case.case_id, item.name), item.data, item.content_type)


def read_manifest(bucket: CaseBucket, case_id: str) -> dict[str, Any] | None:
    """The case's `manifest.json` from the bucket; None when the lifecycle rule deleted it.

    Raises the storage library's error when the bucket cannot be read, and `ValueError` when
    the object is not a JSON object.
    """
    data = bucket.download(case_object(case_id, MANIFEST_NAME))
    if data is None:
        return None
    manifest = json.loads(data)
    if not isinstance(manifest, dict):
        raise ValueError("the manifest is not a JSON object")
    return manifest


@dataclass(frozen=True)
class ManifestDetail:
    """What the triage's case detail shows from a manifest's `bundle`: everything but the row's own columns."""

    transcript: tuple[tuple[Literal["user", "assistant"], str], ...]
    code: str | None
    snapshot_library_version: str | None
    residual_defects: tuple[str, ...]
    changes: tuple[str, ...]
    result_reason: str | None
    config: dict[str, Any] | None
    bindings: tuple[tuple[str, str], ...]
    """The session's bound roles as `(role, column)`; unbound roles are left out."""


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _strings(value: Any) -> tuple[str, ...]:
    return tuple(item for item in _list(value) if isinstance(item, str))


def manifest_detail(manifest: dict[str, Any], result_version: int) -> ManifestDetail:
    """Read the bundle a manifest keeps, defensively: it is the agents service's shape, not this module's.

    The version is the one numbered `result_version` (the manifest keeps only that one), else
    the first; the transcript keeps only `{role, text}` turns of the user and the assistant.
    """
    bundle = _dict(manifest.get("bundle"))
    versions = [item for item in _list(bundle.get("versions")) if isinstance(item, dict)]
    version = next((item for item in versions if item.get("number") == result_version), versions[0] if versions else {})
    result = _dict(version.get("result"))
    config = bundle.get("config")
    code = version.get("plot_py")
    return ManifestDetail(
        transcript=tuple(
            (turn["role"], turn["text"])
            for turn in _list(bundle.get("transcript"))
            if isinstance(turn, dict)
            and turn.get("role") in ("user", "assistant")
            and isinstance(turn.get("text"), str)
        ),
        code=code if isinstance(code, str) and code else None,
        snapshot_library_version=_text(_dict(bundle.get("snapshot")).get("library_version")),
        residual_defects=_strings(result.get("residual_defects")),
        changes=_strings(result.get("changes")),
        result_reason=_text(result.get("reason")),
        config=config if isinstance(config, dict) else None,
        bindings=tuple(
            (binding["role"], binding["column"])
            for binding in _list(bundle.get("bindings"))
            if isinstance(binding, dict) and _text(binding.get("role")) and _text(binding.get("column"))
        ),
    )


def _without_export_header(code: str) -> str:
    """The exported code without its attribution header (agents/anyplot/code/export.py, `attribution`).

    Only when the first line is the header's: then the leading comment lines up to the
    first blank line, and that blank line, which the export adds after its two lines.
    """
    if not _EXPORT_LIBRARY.match(code):
        return code
    lines = code.split("\n")
    start = 0
    while start < len(lines) and lines[start].startswith("#"):
        start += 1
    if start < len(lines) and not lines[start].strip():
        start += 1
    return "\n".join(lines[start:])


def _diff_lines(text: str) -> list[str]:
    """`text` as lines for `difflib`, each ending in a newline (the last one too), split on `\\n` only."""
    lines = text.split("\n")
    if lines[-1] == "":
        lines.pop()
    return [f"{line}\n" for line in lines]


def code_diff(original: str, adapted: str, *, spec_id: str, library_id: str) -> str:
    """A unified diff from the catalogue's code to a case's exported `plot.py`; empty when they agree.

    The export's attribution header is dropped first, so its two comment lines do not read as
    a change. Each line counts as newline-terminated, so a missing final newline on either
    side does not glue two diff lines together.
    """
    return "".join(
        difflib.unified_diff(
            _diff_lines(original),
            _diff_lines(_without_export_header(adapted)),
            fromfile=f"catalogue/{spec_id}/{library_id}.py",
            tofile="case/plot.py",
            n=3,
        )
    )
