"""The composer's paste routing and the dataset route's classifier agree on the shared cases.

The page routes pasted text before it reaches the message box (`app/src/sections/agent-chat/routeInput.ts`): a table
becomes an attachment for the dataset route, anything else stays a message. Each case of the shared file names the
page's route and what `classify_paste` answers for the same text, so the two sides are tested against one list in
three directions: text the page sends as data must be what the parser reads (`None`), code the page keeps as a
message must be code here, and the other messages are what the case says (prose `None`, a formula, a data request).
The line cases hold the code veto's copied regexes to the server's.
"""

import json
from pathlib import Path

import pytest

from agents.anyplot.data.classify import _ARROW, _SHAPED, _STRONG, classify_paste
from agents.anyplot.data.layouts import MIN_PAIRS_WITH_DATA, MIN_ROWS, read_layout
from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.data.transcribe import looks_like_free_text


ROOT = Path(__file__).resolve().parents[3]
CASES = ROOT / "app" / "src" / "sections" / "agent-chat" / "routeInput.cases.json"
SHARED = json.loads(CASES.read_text(encoding="utf-8"))


def _text(case: dict) -> str:
    return case["text"] * case.get("repeat", 1)


@pytest.mark.parametrize("case", SHARED["cases"], ids=lambda case: f"case-{case['id']}")
def test_the_server_classifies_each_shared_case_as_it_names(case: dict) -> None:
    assert classify_paste(_text(case)) == case["server"]


@pytest.mark.parametrize(
    "case", [case for case in SHARED["cases"] if case["route"] == "data"], ids=lambda case: f"case-{case['id']}"
)
def test_text_routed_as_data_is_text_the_parser_reads(case: dict) -> None:
    """A table sent as an attachment never meets a classifier refusal: code stays a message at any length."""
    assert case["server"] is None


@pytest.mark.parametrize(
    "case", [case for case in SHARED["cases"] if "parsed" in case], ids=lambda case: f"case-{case['id']}"
)
def test_the_parser_reads_each_layout_case_as_the_case_names(case: dict) -> None:
    """The layouts the page routes as data (`layouts.py`) are read by code, not by the transcriber."""
    parsed = parse_dataset(_text(case), min_pairs=_min_pairs(case))

    assert case["route"] == "data"
    assert parsed.profile.source_format == case["parsed"]["format"]
    assert parsed.profile.rows == case["parsed"]["rows"]
    assert [column.name for column in parsed.profile.columns] == case["parsed"]["columns"]
    assert not looks_like_free_text(parsed)


@pytest.mark.parametrize(
    "case", [case for case in SHARED["cases"] if "layout" in case], ids=lambda case: f"case-{case['id']}"
)
def test_a_change_request_is_no_layout_on_the_server_either(case: dict) -> None:
    """The live regression of 2026-11-09: `x bis 2030, y bis 60` became two `label`/`value` rows over the data."""
    assert case["layout"] is None and case["route"] == "message"
    assert read_layout(_text(case), min_pairs=_min_pairs(case)) is None


def _min_pairs(case: dict) -> int:
    """The pairs a list takes as the dataset route asks them: more while the session holds data."""
    return MIN_PAIRS_WITH_DATA if case.get("has_data") else MIN_ROWS


def test_the_code_veto_cases_are_code_on_both_sides() -> None:
    vetoed = [case for case in SHARED["cases"] if case["rule"] == "5"]

    assert len(vetoed) >= 3
    assert all(case["route"] == "message" and classify_paste(_text(case)) == "code" for case in vetoed)


@pytest.mark.parametrize("item", SHARED["lines"], ids=lambda item: item["line"])
def test_the_code_veto_reads_each_line_as_the_page_does(item: dict) -> None:
    line = item["line"]
    strong = bool(_STRONG.search(line) or _ARROW.search(line))

    assert strong == item["strong"]
    assert (strong or bool(_SHAPED.search(line))) == item["shaped"]
