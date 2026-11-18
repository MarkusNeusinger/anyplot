"""
Tests for api/agent_cases.py — the feedback case files, their upload, and the triage's read back.

The routes' behaviour is in test_agent_router.py (`TestFeedback`, `TestCases`); these cover the
pieces they build on. No test reaches a bucket: the GCS client is a mock.
"""

import hashlib
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
    BundleError,
    CaseCallShape,
    CaseCondition,
    CaseConflict,
    CaseFile,
    CaseGuardLine,
    CaseLastRun,
    CaseOperation,
    CaseRound,
    CaseToolCall,
    CaseTurn,
    CaseTurns,
    FeedbackCase,
    GcsCaseBucket,
    NoChatData,
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
from core.agent_cases import CASE_FILE_NAMES, CODE_FILE_NAMES, row_from_manifest
from core.constants import LIBRARY_LANGUAGES, library_file_extension
from core.database import FEEDBACK_STATUSES


def test_case_ids_sort_by_time_and_differ() -> None:
    early = new_case_id(datetime(2026, 10, 12, 9, 5, 7, tzinfo=UTC))
    late = new_case_id(datetime(2026, 10, 12, 14, 30, 5, tzinfo=UTC))
    assert re.fullmatch(r"20261012T090507Z-[0-9a-f]{8}", early)
    assert early < late
    same_second = {new_case_id(datetime(2026, 10, 12, tzinfo=UTC)) for _ in range(50)}
    assert len(same_second) == 50


def test_the_session_hash_is_the_key_the_agents_service_made() -> None:
    assert session_hash("abc", "0123456789abcdef") == "0123456789abcdef"


def test_without_a_key_the_session_hash_is_salted_here_and_never_the_plain_hash() -> None:
    """A plain hash of the session id could be made again from a log that holds the id."""
    plain = hashlib.sha256(b"abc").hexdigest()
    own = session_hash("abc")
    assert re.fullmatch(r"[0-9a-f]{16}", own)
    assert own == session_hash("abc"), "one session, one value, so a correction finds the case it replaces"
    assert own != session_hash("abd")
    assert own not in (plain[:16], hashlib.sha256(b"case:abc").hexdigest()[:16])


def test_a_bundle_without_a_key_is_logged_without_the_session_id(caplog: pytest.LogCaptureFixture) -> None:
    """Once both services send the key, a bundle without one means the field got lost: that must show in the log,
    and the line must not hold the id the salt keeps out of the stored case."""
    with caplog.at_level("WARNING", logger="api.agent_cases"):
        session_hash("S1abcdefgh", "0123456789abcdef")
        assert caplog.records == []
        own = session_hash("S1abcdefgh")
    (record,) = caplog.records
    assert "no usable case key" in record.getMessage()
    assert "S1abcdefgh" not in record.getMessage() and own not in record.getMessage()


@pytest.mark.parametrize(
    "unusable",
    [None, "", 12, "0123456789ABCDEF", "0123456789abcde", "0123456789abcdef0", "g123456789abcdef", ["0" * 16]],
)
def test_a_key_of_another_form_is_not_stored(unusable: object) -> None:
    """The column takes 16 characters and the value groups rows: only the form the agents service writes is kept."""
    assert session_hash("abc", unusable) == session_hash("abc")


def test_a_case_records_the_bundles_key_and_not_a_hash_of_the_session_id() -> None:
    keyed = json.loads(json.dumps(BUNDLE))
    keyed["session"]["case_key"] = "fedcba9876543210"
    case = build_case(
        json.dumps(keyed).encode(),
        Submission(reaction="bug", message=None, include_data=False, result_version=3),
        case_id="20261012T143005Z-1a2b3c4d",
        created_at=datetime(2026, 10, 12, 14, 30, 5, tzinfo=UTC),
        bucket="anyplot-agent-cases",
        user_hash="adm_0123456789abcdef",
        session_id="S1abcdefgh",
    )
    assert case.manifest["session_hash"] == "fedcba9876543210"
    # A bundle from before the field: this process's salted hash, the same for every case of the session.
    assert _case().manifest["session_hash"] == session_hash("S1abcdefgh")
    assert _case().manifest["session_hash"] != hashlib.sha256(b"S1abcdefgh").hexdigest()[:16]


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
        (
            {"plot_py": "// Adapted by anyplot.ai from scatter-basic (chartjs 4.4.7) for your data.csv;\n"},
            {"library": "d3"},
            "chartjs",
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
    code_files = {"plot.py", "plot.R", "plot.jl", "plot.js", "plot.tsx"}
    assert set(CASE_MEDIA_TYPES) == {"manifest.json", "plot-light.png", "plot-dark.png", "data.csv", *code_files}
    assert set(CASE_MEDIA_TYPES) == set(CASE_FILE_NAMES)
    assert set(agent_cases.CODE_FILE_NAMES) == code_files
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


def test_the_code_file_takes_the_bundles_artifact_name() -> None:
    """An R version's code is stored as `plot.R`; a bundle without the name, or with an unknown one, keeps `plot.py`."""
    names = [file.name for file in _case().files]
    assert "plot.py" in names and not any(name.endswith((".R", ".js")) for name in names)
    bundle = json.loads(json.dumps(BUNDLE))
    bundle["versions"][0]["code_artifact"] = "plot.R"
    case = build_case(
        json.dumps(bundle).encode(),
        Submission(reaction="bug", message=None, include_data=False, result_version=3),
        case_id="20261012T143005Z-1a2b3c4d",
        created_at=datetime(2026, 10, 12, 14, 30, 5, tzinfo=UTC),
        bucket="anyplot-agent-cases",
        user_hash="adm_0123456789abcdef",
        session_id="S1abcdefgh",
    )
    assert [file.name for file in case.files if file.name.startswith("plot.")] == ["plot.R"]
    assert next(file for file in case.files if file.name == "plot.R").content_type == "text/plain; charset=utf-8"
    bundle["versions"][0]["code_artifact"] = "plot.exe"
    case = build_case(
        json.dumps(bundle).encode(),
        Submission(reaction="bug", message=None, include_data=False, result_version=3),
        case_id="20261012T143005Z-1a2b3c4d",
        created_at=datetime(2026, 10, 12, 14, 30, 5, tzinfo=UTC),
        bucket="anyplot-agent-cases",
        user_hash="adm_0123456789abcdef",
        session_id="S1abcdefgh",
    )
    assert [file.name for file in case.files if file.name.startswith("plot.")] == ["plot.py"]


def test_the_bffs_manifest_maps_onto_a_row() -> None:
    """The route inserts `row_from_manifest(case.manifest)`: the BFF's own manifest must pass it."""
    row = row_from_manifest(_case(replaces="20261012T140000Z-00ff00ff").manifest)
    assert row["id"] == "20261012T143005Z-1a2b3c4d"
    assert row["created_at"] == datetime(2026, 10, 12, 14, 30, 5)
    assert row["locale"] == "de-CH"
    assert row["replaces"] == "20261012T140000Z-00ff00ff"
    assert row["files"] == ["plot.py", "data.csv", "manifest.json"]


def _chat_case(bundle: dict[str, object], include_data: bool = True) -> FeedbackCase:
    """The chat's case (version 0) of a session without a plot, from the `version=0` bundle."""
    return build_case(
        json.dumps(bundle).encode(),
        Submission(reaction="idea", message="sin x as a feature", include_data=include_data, result_version=0),
        case_id="20261012T150000Z-0a0b0c0d",
        created_at=datetime(2026, 10, 12, 15, 0, 0, tzinfo=UTC),
        bucket="anyplot-agent-cases",
        user_hash="adm_0123456789abcdef",
        session_id="S1abcdefgh",
    )


CHAT_BUNDLE = {**BUNDLE, "versions": [], "data_csv": "x,y\n-3.14,0\n0,0\n"}


def test_the_chat_case_has_its_data_but_no_image_or_code() -> None:
    case = _chat_case(CHAT_BUNDLE)

    assert case.stored == ["data.csv", "manifest.json"]
    assert case.files[0].data == b"x,y\n-3.14,0\n0,0\n"
    # The data is a file of its own, never inside the manifest's bundle.
    assert "data_csv" not in case.manifest["bundle"]
    row = row_from_manifest(case.manifest)
    assert (row["result_version"], row["library_id"], row["pipeline_status"], row["attempts"]) == (
        0,
        "matplotlib",
        None,
        None,
    )
    assert manifest_detail(case.manifest, 0).transcript[0] == ("user", "log scale on y")


def test_the_chat_case_without_data_asked() -> None:
    case = _chat_case({**BUNDLE, "versions": []}, include_data=False)
    assert case.stored == ["manifest.json"]


def test_the_chat_case_of_a_session_without_data_is_the_users_problem_not_a_bad_bundle() -> None:
    with pytest.raises(NoChatData):
        _chat_case({**BUNDLE, "versions": [], "data_csv": None})
    # A bundle that omits the field entirely did not come from a version-0 request: malformed.
    with pytest.raises(BundleError):
        _chat_case({**BUNDLE, "versions": []})


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


FAILED_ROUND = {
    "attempt": 1,
    "outcome": "render_failed",
    "findings": 1,
    "step": "rendering",
    "shipped": False,
    "defects": [],
    "gates_failed": ["R1"],
    "sandbox_failures": ["key"],
}


def test_manifest_detail_reads_the_rounds_and_the_latest_run() -> None:
    """A chat case holds no version: the session's count and its latest run say what happened."""
    manifest = {
        "bundle": {
            "versions": [],
            "session": {
                "versions": 0,
                "last_run": {
                    "status": "failed",
                    "reason": "render",
                    "version": None,
                    "turn": 2,
                    "rounds": [FAILED_ROUND],
                },
            },
        }
    }

    detail = manifest_detail(manifest, 0)

    failed = CaseRound(
        attempt=1,
        outcome="render_failed",
        findings=1,
        step="rendering",
        shipped=False,
        defects=(),
        gates_failed=("R1",),
        sandbox_failures=("key",),
    )
    assert detail.rounds == ()
    assert detail.session_versions == 0
    assert detail.last_run == CaseLastRun(status="failed", reason="render", version=None, turn=2, rounds=(failed,))
    # A plot case reads its own version's rounds.
    shipped = {
        **FAILED_ROUND,
        "attempt": 2,
        "outcome": "ok",
        "shipped": True,
        "gates_failed": [],
        "sandbox_failures": [],
    }
    plot = {"bundle": {"versions": [{"number": 1, "result": {"rounds": [FAILED_ROUND, shipped]}}]}}
    assert [item.outcome for item in manifest_detail(plot, 1).rounds] == ["render_failed", "ok"]


def test_manifest_detail_shows_only_closed_codes() -> None:
    """Whatever the bundle holds, only codes of the closed vocabularies reach the triage view, never text."""
    noisy = {
        **FAILED_ROUND,
        "gates_failed": ["R1", "KeyError: 'Zürich'", 7],
        # A lowercase word is no code either: only the closed vocabulary passes.
        "sandbox_failures": ["key", "Zürich has 3 rows", "zurich"],
        "defects": ["VQ-05", "the title says Zürich"],
        "step": "zurich",
    }
    manifest = {
        "bundle": {
            "versions": [{"number": 1, "result": {"rounds": [noisy, {"attempt": 0, "outcome": "ok"}, "round"]}}],
            "session": {"versions": "two", "last_run": {"status": "zurich", "rounds": [noisy]}},
        }
    }

    detail = manifest_detail(manifest, 1)

    (only,) = detail.rounds
    assert (only.gates_failed, only.sandbox_failures, only.defects, only.step) == (("R1",), ("key",), ("VQ-05",), None)
    assert detail.session_versions is None and detail.last_run is None


def test_manifest_detail_of_an_older_manifest_has_no_rounds_or_run() -> None:
    detail = manifest_detail(_case().manifest, 3)

    assert (detail.rounds, detail.session_versions, detail.last_run, detail.turns) == ((), None, None, None)


PREP_TURN = {
    "turn": 2,
    "action": "text",
    "kind": "prep",
    "refusal": None,
    "error": None,
    "tools": [
        {"tool": "prepare_data", "verdict": "allowed", "outcome": "error", "code": "invalid_operations"},
        {"tool": "plot_pipeline", "verdict": "plot_as_confirmed", "outcome": "refused", "code": None},
    ],
    "tools_dropped": 0,
    "guards": [{"guard": "scope_guard", "verdict": "in_scope"}, {"guard": "output_guard", "verdict": "reply_cut"}],
    "guards_dropped": 1,
    "prep_ops": ["derive"],
    "prep_ops_dropped": 0,
}


def test_manifest_detail_reads_the_turn_record() -> None:
    manifest = {"bundle": {"turns": {"records": [PREP_TURN], "dropped": 4}}}

    turns = manifest_detail(manifest, 0).turns

    assert turns == CaseTurns(
        records=(
            CaseTurn(
                turn=2,
                action="text",
                kind="prep",
                refusal=None,
                error=None,
                tools=(
                    CaseToolCall("prepare_data", "allowed", "error", "invalid_operations"),
                    CaseToolCall("plot_pipeline", "plot_as_confirmed", "refused", None),
                ),
                tools_dropped=0,
                guards=(CaseGuardLine("scope_guard", "in_scope"), CaseGuardLine("output_guard", "reply_cut")),
                guards_dropped=1,
                prep_ops=("derive",),
                prep_ops_dropped=0,
            ),
        ),
        dropped=4,
    )
    # A session whose turns all left the ring, or that ran none, still has a record.
    assert manifest_detail({"bundle": {"turns": {"records": []}}}, 0).turns == CaseTurns(records=(), dropped=0)


def test_manifest_detail_keeps_the_latest_turns_of_a_longer_record() -> None:
    """The record's own bound again: of 55 turns the latest 50 stay, and the 5 older ones count with the record's own."""
    records = [{**PREP_TURN, "turn": number} for number in range(1, 56)]
    manifest = {"bundle": {"turns": {"records": records, "dropped": 2}}}

    turns = manifest_detail(manifest, 0).turns

    assert turns is not None
    assert [record.turn for record in turns.records] == list(range(6, 56))
    assert turns.dropped == 2 + 5


def test_manifest_detail_closes_the_turn_record_to_its_vocabularies() -> None:
    """Whatever the bundle holds, a value outside the record's vocabularies reads `other`, never as text."""
    noisy = {
        **PREP_TURN,
        "action": "Zürich",
        "kind": None,
        "refusal": "the column Zürich",
        "tools": [{"tool": "zurich", "verdict": 3, "code": "KeyError: 'Zürich'"}, "call"],
        "guards": [{"guard": "scope_guard", "verdict": "zurich"}] * 30,
        "prep_ops": ["derive", "Zürich"],
        "tools_dropped": "two",
    }
    manifest = {"bundle": {"turns": {"records": [noisy, {"action": "text"}, "turn"], "dropped": None}}}

    turns = manifest_detail(manifest, 0).turns

    assert turns is not None and turns.dropped == 0
    (only,) = turns.records
    assert (only.action, only.kind, only.refusal, only.error) == ("other", "other", "other", None)
    assert only.tools == (CaseToolCall("other", "other", "other", "other"),)
    assert only.tools_dropped == 0
    # The latest 24 verdicts, the earlier ones counted with the record's own.
    assert only.guards == (CaseGuardLine("scope_guard", "other"),) * 24
    assert only.guards_dropped == 1 + 6
    assert only.prep_ops == ("derive", "other")
    assert manifest_detail({"bundle": {"turns": "none"}}, 0).turns is None


NULL_OPERATION = dict.fromkeys(
    ("mode", "target", "order", "conditions", "how", "period", "keys", "type", "date_format", "decimal", "unit")
    + ("keep", "family")
)
NULL_SHAPE = dict.fromkeys(
    ("operations", "from_version", "limit", "base", "theme", "combine", "change_request", "expected_texts")
    + ("remember", "applies_to", "plot")
)


def _shaped_turn(*calls: tuple[str, object]) -> dict[str, object]:
    return {
        **PREP_TURN,
        "tools": [
            {"tool": tool, "verdict": "allowed", "outcome": "ok", "code": None, "shape": shape} for tool, shape in calls
        ],
    }


def test_manifest_detail_reads_a_calls_shape() -> None:
    """An invented data change's shape and a plot run's, field by field; a call without a shape key (a case from
    before the record kept it) has none, not `other`."""
    condition = {"test": "ge", "value_shape": "iso_date", "column_kind": "datetime"}
    selection = {**NULL_OPERATION, "op": "keep_rows", "mode": "where", "target": "plot", "conditions": [condition]}
    dropped = {**NULL_OPERATION, "op": "drop_rows", "conditions": [{**condition, "test": "is_missing"}]}
    change = {**NULL_SHAPE, "operations": [dropped, selection, {**NULL_OPERATION, "op": "sort", "order": "descending"}]}
    plot = {**NULL_SHAPE, "base": "previous", "change_request": True, "expected_texts": 2, "remember": ["title"]}
    manifest = {
        "bundle": {
            "turns": {"records": [_shaped_turn(("prepare_data", change), ("plot_pipeline", plot), ("forget", None))]}
        }
    }
    manifest["bundle"]["turns"]["records"][0]["tools"].append({"tool": "get_spec_brief", "verdict": "allowed"})

    turns = manifest_detail(manifest, 0).turns

    assert turns is not None
    changed, run, bare, older = (call.shape for call in turns.records[0].tools)
    assert changed == CaseCallShape(
        **{
            **NULL_SHAPE,
            "operations": (
                CaseOperation(
                    **{
                        **dropped,
                        "conditions": (
                            CaseCondition(test="is_missing", value_shape="iso_date", column_kind="datetime"),
                        ),
                    }
                ),
                CaseOperation(
                    **{
                        **selection,
                        "conditions": (CaseCondition(test="ge", value_shape="iso_date", column_kind="datetime"),),
                    }
                ),
                CaseOperation(**{**NULL_OPERATION, "op": "sort", "order": "descending"}),
            ),
        }
    )
    assert run == CaseCallShape(**{**plot, "remember": ("title",)})
    assert bare is None and older is None


def test_manifest_detail_reads_a_questions_total_and_fit() -> None:
    """A question's aggregate over every row keeps its `keys` of 0, and a `fit` reads by its own name."""
    total = {**NULL_OPERATION, "op": "aggregate", "how": "sum", "keys": 0}
    question = {**NULL_SHAPE, "operations": [total, {**NULL_OPERATION, "op": "fit"}], "from_version": "current"}
    manifest = {"bundle": {"turns": {"records": [_shaped_turn(("query_data", question))]}}}

    turns = manifest_detail(manifest, 0).turns

    assert turns is not None
    shape = turns.records[0].tools[0].shape
    assert shape is not None and shape.operations == (CaseOperation(**total), CaseOperation(**NULL_OPERATION, op="fit"))


def test_manifest_detail_closes_a_shape_to_each_fields_own_vocabulary() -> None:
    """A value outside its field's set reads `other`, a code of another field too; a count past its bound, a
    non-boolean flag and a list past the tools' own bounds are dropped, never shown."""
    noisy_operation = {
        "op": "Zürich",
        "mode": "first_n",
        "target": "descending",
        "conditions": [{"test": "eq", "value_shape": "Zürich", "column_kind": 7}] * 5,
        "keys": 9,
        "decimal": ";",
    }
    noisy = {
        "operations": [noisy_operation] * 8,
        "from_version": "3",
        "limit": "yes",
        "expected_texts": 99,
        "remember": ["title", "Zürich"] * 4,
        "plot": 1,
    }
    manifest = {"bundle": {"turns": {"records": [_shaped_turn(("query_data", noisy), ("query_data", "shape"))]}}}

    turns = manifest_detail(manifest, 0).turns

    assert turns is not None
    shape, text = (call.shape for call in turns.records[0].tools)
    assert text is None and shape is not None and shape.operations is not None
    assert len(shape.operations) == 5
    operation = shape.operations[0]
    assert (operation.op, operation.mode, operation.target, operation.keys, operation.decimal) == (
        "other",
        "first_n",
        "other",
        None,
        "other",
    )
    assert operation.conditions == (CaseCondition(test="eq", value_shape="other", column_kind="other"),) * 3
    assert (shape.from_version, shape.limit, shape.expected_texts, shape.plot) == ("other", None, None, None)
    assert shape.remember == ("title", "other", "title", "other", "title")


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


def test_code_diff_drops_a_script_export_header() -> None:
    """A JavaScript export's two header lines are `//` comments; they do not read as a change either."""
    adapted = (
        "// Adapted by anyplot.ai from scatter-basic (chartjs 4.4.7) for your data.csv;\n"
        "// run: open plot.html in a browser, which runs this code with the chart library, the light theme and your data\n"
        "\nconst chart = new Chart(ctx, config);\n"
    )
    original = "const chart = new Chart(ctx, config);\nchart.update();\n"
    diff = code_diff(original, adapted, spec_id="scatter-basic", library_id="chartjs")
    assert diff.startswith("--- catalogue/scatter-basic/chartjs.js\n+++ case/plot.js\n")
    assert "-chart.update();\n" in diff
    assert "Adapted by" not in diff
    assert "// run:" not in diff


@pytest.mark.parametrize(
    ("library_id", "extension"), [("matplotlib", ".py"), ("ggplot2", ".R"), ("makie", ".jl"), ("muix", ".tsx")]
)
def test_code_diff_names_both_sides_with_the_library_s_extension(library_id, extension) -> None:
    diff = code_diff("x\n", "y\n", spec_id="s", library_id=library_id)
    assert diff.startswith(f"--- catalogue/s/{library_id}{extension}\n+++ case/plot{extension}\n")


def test_every_library_s_case_label_is_a_case_code_file_name() -> None:
    """The diff's `case/plot<ext>` label names a file a case stores, for every library of the registry."""
    assert {f"plot{library_file_extension(library)}" for library in LIBRARY_LANGUAGES} <= set(CODE_FILE_NAMES)


def test_code_diff_is_empty_when_only_the_header_differs() -> None:
    assert code_diff("import pandas as pd\n", PLOT_PY, spec_id="s", library_id="l") == ""


def test_code_diff_is_empty_when_only_a_script_header_differs() -> None:
    original = "const chart = new Chart(ctx, config);\n"
    adapted = (
        "// Adapted by anyplot.ai from scatter-basic (chartjs 4.4.7) for your data.csv;\n"
        "// run: open plot.html in a browser, which runs this code with the chart library, the light theme and your data\n"
        "\n" + original
    )
    assert code_diff(original, adapted, spec_id="scatter-basic", library_id="chartjs") == ""


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
