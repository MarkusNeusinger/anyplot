"""
Tests for api/agent_cases.py — the feedback case files and their upload.

The route's behaviour is in test_agent_router.py (`TestFeedback`); these cover the
pieces it builds on. No test reaches a bucket: the GCS client is a mock.
"""

import re
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from api import agent_cases
from api.agent_cases import (
    CASE_MEDIA_TYPES,
    CaseFile,
    FeedbackCase,
    GcsCaseBucket,
    new_case_id,
    prompt_hash,
    session_hash,
    version_library,
    write_case,
)


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
    )
    with pytest.raises(OSError):
        write_case(Bucket(), case)
    assert uploaded == ["cases/c1/plot-light.png"]
    assert case.stored == ["plot-light.png", "plot.py", "manifest.json"]


def test_every_case_file_has_a_content_type() -> None:
    assert set(CASE_MEDIA_TYPES) == {"manifest.json", "plot-light.png", "plot-dark.png", "plot.py", "data.csv"}
    assert CaseFile("data.csv", b"").content_type == "text/csv; charset=utf-8"
