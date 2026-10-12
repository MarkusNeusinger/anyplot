"""
Tests for api/agent_cases.py — the feedback case files, their upload, and the triage's read back.

The routes' behaviour is in test_agent_router.py (`TestFeedback`, `TestCases`); these cover the
pieces they build on. No test reaches a bucket: the GCS client is a mock.
"""

import json
import re
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from google.api_core.exceptions import Forbidden, NotFound, PreconditionFailed

from api import agent_cases
from api.agent_cases import (
    CASE_ID_PATTERN,
    CASE_MEDIA_TYPES,
    CASE_STATUS_NEW,
    CaseConflict,
    CaseFile,
    FeedbackCase,
    GcsCaseBucket,
    Submission,
    build_case,
    code_diff,
    manifest_detail,
    new_case_id,
    prompt_hash,
    read_manifest,
    session_hash,
    version_library,
    write_case,
)
from core.agent_cases import CASE_FILE_NAMES, row_from_manifest
from core.database import FEEDBACK_STATUSES


def test_case_ids_sort_by_time_and_differ() -> None:
    early = new_case_id(datetime(2026, 10, 12, 9, 5, 7, tzinfo=UTC))
    late = new_case_id(datetime(2026, 10, 12, 14, 30, 5, tzinfo=UTC))
    assert re.fullmatch(r"20261012T090507Z-[0-9a-f]{8}", early)
    assert early < late
    same_second = {new_case_id(datetime(2026, 10, 12, tzinfo=UTC)) for _ in range(50)}
    assert len(same_second) == 50


def test_session_hash_is_the_first_16_hex_digits_of_sha256() -> None:
    assert session_hash("abc") == "ba7816bf8f01cfea"


def test_prompt_hash_is_stable_and_order_free() -> None:
    first = prompt_hash({"root": "a", "reviewer": "b"})
    assert first == prompt_hash({"reviewer": "b", "root": "a"})
    assert first != prompt_hash({"root": "a", "reviewer": "c"})
    assert re.fullmatch(r"[0-9a-f]{16}", first or "")
    assert prompt_hash({}) is None
    assert prompt_hash(None) is None
    assert prompt_hash({"root": 1}) is None


@pytest.mark.parametrize(
    ("version", "session", "expected"),
    [
        ({"library": "plotly"}, {"library": "seaborn"}, "plotly"),
        (
            {"plot_py": "# Adapted by anyplot.ai from bar-grouped (seaborn 0.13.2) for your data.csv;\n"},
            {"library": "matplotlib"},
            "seaborn",
        ),
        (
            {"plot_py": "# Adapted by anyplot.ai from bar-grouped (matplotlib) for your data.csv;\n"},
            {"library": "seaborn"},
            "matplotlib",
        ),
        ({"plot_py": "import pandas as pd\n"}, {"library": "seaborn"}, "seaborn"),
        ({}, {}, None),
    ],
)
def test_version_library(version, session, expected) -> None:
    assert version_library(version, session) == expected


def test_gcs_upload_never_replaces_an_object(monkeypatch) -> None:
    client = MagicMock()
    monkeypatch.setattr(agent_cases, "_storage_client", lambda: client)

    GcsCaseBucket("anyplot-agent-cases").upload("cases/x/plot.py", b"code", "text/x-python; charset=utf-8")

    client.bucket.assert_called_once_with("anyplot-agent-cases")
    client.bucket.return_value.blob.assert_called_once_with("cases/x/plot.py")
    client.bucket.return_value.blob.return_value.upload_from_string.assert_called_once_with(
        b"code", content_type="text/x-python; charset=utf-8", if_generation_match=0
    )


def test_gcs_upload_takes_its_own_retried_object_as_stored(monkeypatch) -> None:
    """A retry whose first attempt stored the object but lost the response meets `412`: stored, the bytes match."""
    client = MagicMock()
    blob = client.bucket.return_value.blob.return_value
    blob.upload_from_string.side_effect = PreconditionFailed("exists")
    blob.md5_hash = "mZFLkyvTelC5g8XnyQrpOw=="  # the MD5 of b"{}" as GCS reports it
    monkeypatch.setattr(agent_cases, "_storage_client", lambda: client)

    GcsCaseBucket("anyplot-agent-cases").upload("cases/x/manifest.json", b"{}", "application/json")

    blob.reload.assert_called_once_with()


def test_gcs_upload_refuses_an_existing_object_with_other_content(monkeypatch) -> None:
    """A `412` on an object whose bytes differ is a collision or a replay, never this upload's own."""
    client = MagicMock()
    blob = client.bucket.return_value.blob.return_value
    blob.upload_from_string.side_effect = PreconditionFailed("exists")
    blob.md5_hash = "eV8yArF8trw9S3cdjGyerw=="  # the MD5 of b"other"
    monkeypatch.setattr(agent_cases, "_storage_client", lambda: client)

    with pytest.raises(CaseConflict, match="cases/x/manifest.json exists with other content"):
        GcsCaseBucket("anyplot-agent-cases").upload("cases/x/manifest.json", b"{}", "application/json")


def test_gcs_upload_raises_any_other_storage_error(monkeypatch) -> None:
    client = MagicMock()
    client.bucket.return_value.blob.return_value.upload_from_string.side_effect = Forbidden("no create right")
    monkeypatch.setattr(agent_cases, "_storage_client", lambda: client)

    with pytest.raises(Forbidden):
        GcsCaseBucket("anyplot-agent-cases").upload("cases/x/manifest.json", b"{}", "application/json")


def test_case_ids_match_the_pattern_a_replaced_case_is_checked_against() -> None:
    assert re.fullmatch(CASE_ID_PATTERN, new_case_id(datetime(2026, 10, 12, 14, 30, 5, tzinfo=UTC)))
    assert not re.fullmatch(CASE_ID_PATTERN, "20261012T143005Z-1A2B3C4D")


def test_write_case_uploads_in_order_and_stops_at_the_first_failure() -> None:
    uploaded: list[str] = []

    class Bucket:
        def upload(self, name: str, data: bytes, content_type: str) -> None:
            if name.endswith("plot.py"):
                raise OSError("refused")
            uploaded.append(name)

    case = FeedbackCase(
        case_id="c1",
        files=(CaseFile("plot-light.png", b"p"), CaseFile("plot.py", b"c"), CaseFile("manifest.json", b"{}")),
        manifest={},
    )
    with pytest.raises(OSError):
        write_case(Bucket(), case)
    assert uploaded == ["cases/c1/plot-light.png"]
    assert case.stored == ["plot-light.png", "plot.py", "manifest.json"]


def test_every_case_file_has_a_content_type() -> None:
    assert set(CASE_MEDIA_TYPES) == {"manifest.json", "plot-light.png", "plot-dark.png", "plot.py", "data.csv"}
    assert set(CASE_MEDIA_TYPES) == set(CASE_FILE_NAMES)
    assert CaseFile("data.csv", b"").content_type == "text/csv; charset=utf-8"


def test_a_fresh_case_has_a_status_of_the_triage() -> None:
    assert CASE_STATUS_NEW in FEEDBACK_STATUSES


PLOT_PY = (
    "# Adapted by anyplot.ai from scatter-basic (matplotlib 3.10.0) for your data.csv;\n"
    "# run: ANYPLOT_THEME=light python plot.py\n"
    "\n"
    "import pandas as pd\n"
)
BUNDLE = {
    "session": {"spec_id": "scatter-basic", "library": "matplotlib", "locale": "de-CH"},
    "snapshot": {"spec_id": "scatter-basic", "library_version": "3.10.0"},
    "transcript": [{"role": "user", "text": "log scale on y"}, {"role": "assistant", "text": "Done."}],
    "versions": [
        {
            "number": 3,
            "plot_py": PLOT_PY,
            "result": {"status": "ok", "attempts": 1, "changes": ["log scale"], "residual_defects": [], "reason": None},
            "images": {},
            "data_csv": "hours,score\n1.5,52\n",
        }
    ],
    "bindings": [{"role": "x", "column": "hours"}, {"role": "y", "column": None}],
    "config": {"model": "claude-haiku-5-5", "prompt_hashes": {"root": "a"}},
}


def _case(**submission) -> FeedbackCase:
    return build_case(
        json.dumps(BUNDLE).encode(),
        Submission(**{"reaction": "bug", "message": None, "include_data": True, "result_version": 3, **submission}),
        case_id="20261012T143005Z-1a2b3c4d",
        created_at=datetime(2026, 10, 12, 14, 30, 5, tzinfo=UTC),
        bucket="anyplot-agent-cases",
        user_hash="adm_0123456789abcdef",
        session_id="S1abcdefgh",
    )


def test_the_case_carries_the_manifest_it_uploads() -> None:
    case = _case()
    assert case.files[-1].name == "manifest.json"
    assert case.manifest == json.loads(case.files[-1].data)


def test_the_bffs_manifest_maps_onto_a_row() -> None:
    """The route inserts `row_from_manifest(case.manifest)`: the BFF's own manifest must pass it."""
    row = row_from_manifest(_case(replaces="20261012T140000Z-00ff00ff").manifest)
    assert row["id"] == "20261012T143005Z-1a2b3c4d"
    assert row["created_at"] == datetime(2026, 10, 12, 14, 30, 5)
    assert row["locale"] == "de-CH"
    assert row["replaces"] == "20261012T140000Z-00ff00ff"
    assert row["files"] == ["plot.py", "data.csv", "manifest.json"]


class MemoryBucket:
    def __init__(self, objects: dict[str, bytes]) -> None:
        self.objects = objects

    def upload(self, name: str, data: bytes, content_type: str) -> None:
        self.objects[name] = data

    def download(self, name: str) -> bytes | None:
        return self.objects.get(name)


def test_read_manifest_returns_the_stored_object() -> None:
    case = _case()
    bucket = MemoryBucket({})
    write_case(bucket, case)
    assert read_manifest(bucket, case.case_id) == case.manifest


def test_read_manifest_is_none_once_the_lifecycle_rule_deleted_it() -> None:
    assert read_manifest(MemoryBucket({}), "20261012T143005Z-1a2b3c4d") is None


@pytest.mark.parametrize("stored", [b"[1, 2]", b"not json"])
def test_read_manifest_refuses_an_object_that_is_no_json_object(stored) -> None:
    bucket = MemoryBucket({"cases/c1/manifest.json": stored})
    with pytest.raises(ValueError):
        read_manifest(bucket, "c1")


def test_manifest_detail_reads_the_bundle() -> None:
    detail = manifest_detail(_case().manifest, 3)
    assert detail.transcript == (("user", "log scale on y"), ("assistant", "Done."))
    assert detail.code == PLOT_PY
    assert detail.snapshot_library_version == "3.10.0"
    assert detail.changes == ("log scale",)
    assert detail.residual_defects == ()
    assert detail.result_reason is None
    assert detail.config == {"model": "claude-haiku-5-5", "prompt_hashes": {"root": "a"}}
    # Unbound roles are left out.
    assert detail.bindings == (("x", "hours"),)


@pytest.mark.parametrize(
    "bundle",
    [
        None,
        "bundle",
        {"versions": "none", "transcript": "none", "bindings": {"x": "a"}, "config": [1]},
        {"versions": [1, None], "transcript": [{"role": "tool", "text": "x"}, {"role": "user", "text": 5}, "turn"]},
    ],
)
def test_manifest_detail_tolerates_any_bundle_shape(bundle) -> None:
    detail = manifest_detail({"bundle": bundle}, 3)
    assert detail.transcript == ()
    assert detail.code is None
    assert (detail.residual_defects, detail.changes, detail.bindings) == ((), (), ())
    assert detail.config is None


def test_manifest_detail_picks_the_rated_version() -> None:
    manifest = {"bundle": {"versions": [{"number": 2, "plot_py": "two"}, {"number": 3, "plot_py": "three"}]}}
    assert manifest_detail(manifest, 3).code == "three"
    assert manifest_detail(manifest, 9).code == "two"


def test_gcs_download_returns_the_objects_bytes(monkeypatch) -> None:
    client = MagicMock()
    client.bucket.return_value.blob.return_value.download_as_bytes.return_value = b"{}"
    monkeypatch.setattr(agent_cases, "_storage_client", lambda: client)

    assert GcsCaseBucket("anyplot-agent-cases").download("cases/x/manifest.json") == b"{}"

    client.bucket.assert_called_once_with("anyplot-agent-cases")
    client.bucket.return_value.blob.assert_called_once_with("cases/x/manifest.json")


def test_gcs_download_of_a_deleted_object_is_none(monkeypatch) -> None:
    client = MagicMock()
    client.bucket.return_value.blob.return_value.download_as_bytes.side_effect = NotFound("gone")
    monkeypatch.setattr(agent_cases, "_storage_client", lambda: client)
    assert GcsCaseBucket("anyplot-agent-cases").download("cases/x/manifest.json") is None


def test_gcs_download_raises_any_other_storage_error(monkeypatch) -> None:
    client = MagicMock()
    client.bucket.return_value.blob.return_value.download_as_bytes.side_effect = Forbidden("no read right")
    monkeypatch.setattr(agent_cases, "_storage_client", lambda: client)
    with pytest.raises(Forbidden):
        GcsCaseBucket("anyplot-agent-cases").download("cases/x/manifest.json")


def test_code_diff_drops_the_export_header() -> None:
    original = "import pandas as pd\n\nx = 1\n"
    adapted = PLOT_PY + "\nx = 2\n"
    diff = code_diff(original, adapted, spec_id="scatter-basic", library_id="matplotlib")
    assert diff.startswith("--- catalogue/scatter-basic/matplotlib.py\n+++ case/plot.py\n")
    assert "-x = 1\n+x = 2\n" in diff
    assert "Adapted by" not in diff
    assert "# run:" not in diff


def test_code_diff_is_empty_when_only_the_header_differs() -> None:
    assert code_diff("import pandas as pd\n", PLOT_PY, spec_id="s", library_id="l") == ""


def test_code_diff_shows_two_hunks_for_two_distant_changes() -> None:
    original = "".join(f"line {number}\n" for number in range(30))
    adapted = original.replace("line 2\n", "line two\n").replace("line 27\n", "line twenty-seven\n")
    diff = code_diff(original, adapted, spec_id="s", library_id="l")
    assert diff.count("\n@@ ") == 2
    assert "-line 2\n+line two\n" in diff


def test_code_diff_keeps_code_without_the_header_whole() -> None:
    """A first line that is not the export's header is code: nothing is dropped."""
    adapted = "# my comment\n\nimport pandas as pd\n"
    diff = code_diff("import pandas as pd\n", adapted, spec_id="s", library_id="l")
    assert "+# my comment\n+\n" in diff


def test_code_diff_never_glues_lines_without_a_final_newline() -> None:
    diff = code_diff("x = 1", "x = 2", spec_id="s", library_id="l")
    assert "-x = 1\n+x = 2\n" in diff
