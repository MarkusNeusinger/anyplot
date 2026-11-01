"""The live flow since 2026-10-13: self-review in every round, the catalogue reviewer, ship-best, the ship bar.

The other flow tests script the checklist reviewer (`conftest.CHECKLIST_FLOW`); these run the defaults.
"""

import io
import json
import logging
from typing import Any

import httpx
import pytest

from agents.anyplot.grounding import UNVERIFIED_LINE
from agents.anyplot.pipeline import EARLIER_REQUESTS_HEADING, REVIEW_EXPECTED_HEADING, SELF_REVIEW_LINE
from agents.anyplot.render.backends.fake import FakeBackend, FakeOutcome
from agents.anyplot.render.runtimes import PythonRuntime
from agents.anyplot.scoring import DE_DEFAULTS, SCORED
from agents.anyplot.services import get_services
from agents.anyplot.settings import get_settings

from .conftest import CHECKLIST_FLOW
from .fakes import ROOT_REPLY, SCATTER_PLAN, VERDICT_OK, default_script
from .test_service_flow import (
    HEADERS,
    adapter_inputs,
    attribution_lines,
    client,
    create_plot,
    open_session,
    parse_sse,
    runtime,
)


__all__ = ["client", "runtime"]  # fixtures used by name

SECOND_PLAN: dict[str, Any] = {"edits": [{"find": "s=130", "replace": "s=200"}], "changes": ["Larger markers"]}
EMPTY_PLAN: dict[str, Any] = {"edits": [], "changes": []}
DEFECT_LINE = "VQ-03 (light): 24 sparse markers at s=130 look small → s=250 (+120). Likely cause: the marker size."


@pytest.fixture(autouse=True)
def live_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    """The settings defaults: undo the checklist flow the runtime conftest sets for the other tests."""
    for name in CHECKLIST_FLOW:
        monkeypatch.delenv(name, raising=False)
    get_settings.cache_clear()


def score(**lost: int) -> dict[str, Any]:
    """A catalogue review answer: every technical item at its maximum minus `lost`, DE at its defaults."""
    points = {**SCORED, **DE_DEFAULTS}
    lines = []
    for item, minus in lost.items():
        points[item] = SCORED[item] - minus
        lines.append(DEFECT_LINE.replace("VQ-03", item))
    return {
        "items": [{"id": item, "points": value} for item, value in points.items()],
        "defects": lines,
        "suggestions": [],
        "description": "A scatter of the user's two columns.",
    }


def statuses(events: list[tuple[str, dict[str, Any]]]) -> list[tuple[str, int]]:
    return [(data["step"], data["attempt"]) for name, data in events if name == "status"]


async def test_the_first_version_is_proofread_then_reviewed_in_one_round(
    client: httpx.AsyncClient, swap_models, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO, logger="anyplot.agents.attribution")
    script = default_script(plans=[SCATTER_PLAN, EMPTY_PLAN])
    script["reviewer"] = [{"json": score()}]
    fake = swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert (plot["status"], plot["attempts"], plot["residual_defects"]) == ("ok", 1, [])
    assert [(r["attempt"], r["outcome"], r["shipped"]) for r in plot["rounds"]] == [(1, "ok", True)]
    # Both adapter calls belong to round 1 on the page; the second is the self-review.
    assert statuses(events)[:6] == [
        ("adapting", 1), ("checking", 1), ("rendering", 1), ("adapting", 1), ("checking", 1), ("rendering", 1)
    ]  # fmt: skip
    inputs = adapter_inputs(fake)
    assert len(inputs) == 2 and SELF_REVIEW_LINE[:40] in inputs[1]
    # The self-review sees the render: an image part in the adapter's second request.
    adapter_requests = [r for r in fake.requests if (r.config.labels or {}).get("agent_kind") == "adapter"]
    assert any(part.inline_data for part in adapter_requests[1].contents[-1].parts)
    (review,) = attribution_lines(caplog, "pipeline_review")
    assert (review["verdict"], review["score"], review["technical"]) == ("ok", 84, 1.0)


async def test_the_attribution_lines_reach_stdout_without_content(client: httpx.AsyncClient, swap_models) -> None:
    """Owner decision of 2026-10-16: the attribution logger writes to stdout at INFO (Cloud Logging had none of
    round 7's lines), and a whole plot run writes no column name, cell, message or plot text there."""
    from agents.main import ATTRIBUTION_LOGGER, enable_attribution_log

    enable_attribution_log()
    enable_attribution_log()  # idempotent: one handler
    handlers = [h for h in logging.getLogger(ATTRIBUTION_LOGGER).handlers if type(h).__name__ == "_AttributionHandler"]
    assert len(handlers) == 1 and logging.getLogger(ATTRIBUTION_LOGGER).level == logging.INFO
    stream = io.StringIO()
    previous = handlers[0].setStream(stream)
    try:
        script = default_script(plans=[SCATTER_PLAN, EMPTY_PLAN])
        script["reviewer"] = [{"json": score(**{"VQ-03": 3})}, {"json": score()}]
        swap_models("gemini", script)
        sid = await open_session(client)
        await create_plot(client, sid)
    finally:
        handlers[0].setStream(previous)

    lines = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert {"pipeline_review", "pipeline_result"} <= {line["hook"] for line in lines}
    written = stream.getvalue()
    for content in ("Study Hours", "Exam Score", "S01", "sparse markers", "Larger markers", ROOT_REPLY[:20]):
        assert content not in written, content


async def test_a_repair_goes_to_the_review_without_a_proofread(client: httpx.AsyncClient, swap_models) -> None:
    """`AGENT_REPAIR_SELF_REVIEW` is off: the review re-checks the repair, so only round 1 proofreads."""
    script = default_script(plans=[SCATTER_PLAN, EMPTY_PLAN, SECOND_PLAN])
    script["reviewer"] = [{"json": score(**{"VQ-03": 3})}, {"json": score()}]
    fake = swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert (plot["status"], plot["attempts"]) == ("ok", 2)
    assert [(r["attempt"], r["outcome"]) for r in plot["rounds"]] == [(1, "review"), (2, "ok")]
    inputs = adapter_inputs(fake)
    assert len(inputs) == 3  # adapt, proofread, repair
    assert "24 sparse markers" in inputs[2] and SELF_REVIEW_LINE[:40] not in inputs[2]


async def test_a_repair_is_proofread_with_its_findings_before_the_second_review(
    client: httpx.AsyncClient, swap_models, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AGENT_REPAIR_SELF_REVIEW", "true")
    get_settings.cache_clear()
    script = default_script(plans=[SCATTER_PLAN, EMPTY_PLAN, SECOND_PLAN, EMPTY_PLAN])
    script["reviewer"] = [{"json": score(**{"VQ-03": 3})}, {"json": score()}]
    fake = swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert (plot["status"], plot["attempts"]) == ("ok", 2)
    assert [(r["attempt"], r["outcome"]) for r in plot["rounds"]] == [(1, "review"), (2, "ok")]
    inputs = adapter_inputs(fake)
    assert len(inputs) == 4  # adapt, proofread, repair, proofread the repair
    assert "24 sparse markers" in inputs[2] and "24 sparse markers" in inputs[3]
    assert SELF_REVIEW_LINE[:40] in inputs[3]


async def test_with_repair_sees_render_the_repair_sees_before_and_its_proofread_both(
    client: httpx.AsyncClient, swap_models, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AGENT_REPAIR_SEES_RENDER", "true")
    monkeypatch.setenv("AGENT_REPAIR_SELF_REVIEW", "true")
    get_settings.cache_clear()
    script = default_script(plans=[SCATTER_PLAN, EMPTY_PLAN, SECOND_PLAN, EMPTY_PLAN])
    script["reviewer"] = [{"json": score(**{"VQ-03": 3})}, {"json": score()}]
    fake = swap_models("gemini", script)
    sid = await open_session(client)

    await create_plot(client, sid)

    adapter_requests = [r for r in fake.requests if (r.config.labels or {}).get("agent_kind") == "adapter"]

    def images(index: int) -> int:
        return sum(1 for part in adapter_requests[index].contents[-1].parts if part.inline_data)

    # adapt (none), proofread (current), repair (the reviewed render), proofread the repair (before and after)
    assert [images(i) for i in range(4)] == [0, 1, 1, 2]


async def test_a_repair_whose_edits_do_not_apply_gets_a_retry_in_the_same_round(
    client: httpx.AsyncClient, swap_models
) -> None:
    """The c5 incident of 2026-10-13: a repair's edits missed, the round ended and an unreviewed render shipped."""
    missing = {"edits": [{"find": "this text is not in the code", "replace": "x"}], "changes": []}
    script = default_script(plans=[SCATTER_PLAN, EMPTY_PLAN, missing, SECOND_PLAN])
    script["reviewer"] = [{"json": score(**{"VQ-03": 3})}, {"json": score()}]
    fake = swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert (plot["status"], plot["attempts"]) == ("ok", 2)
    # Two rounds on the page: the missed repair and its retry are one round, which the review passed.
    assert [(r["attempt"], r["outcome"], r["shipped"]) for r in plot["rounds"]] == [
        (1, "review", False),
        (2, "ok", True),
    ]
    inputs = adapter_inputs(fake)
    assert len(inputs) == 4  # adapt, proofread, repair (missed), retry
    assert "this text is not in the code" in inputs[3]  # the retry is told which edit missed


async def test_an_unreadable_review_is_asked_once_more(client: httpx.AsyncClient, swap_models) -> None:
    """The Vertex check of 2026-10-14: one review answer failed its schema and the render shipped unreviewed."""
    script = default_script(plans=[SCATTER_PLAN, EMPTY_PLAN])
    script["reviewer"] = [{"text": "not a score"}, {"json": score()}]
    swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert (plot["status"], plot["residual_defects"]) == ("ok", [])
    assert [(r["attempt"], r["outcome"]) for r in plot["rounds"]] == [(1, "ok")]


async def test_a_proofread_whose_edits_miss_is_retried_and_stays_the_proofread(
    client: httpx.AsyncClient, swap_models
) -> None:
    """A retry of the proofread answer must not start a second proofread in the same round."""
    missing = {"edits": [{"find": "this text is not in the code", "replace": "x"}], "changes": []}
    script = default_script(plans=[SCATTER_PLAN, missing, EMPTY_PLAN])
    script["reviewer"] = [{"json": score()}]
    fake = swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert (plot["status"], plot["attempts"]) == ("ok", 1)
    assert [(r["attempt"], r["outcome"], r["shipped"]) for r in plot["rounds"]] == [(1, "ok", True)]
    assert len(adapter_inputs(fake)) == 3  # adapt, proofread (missed), its retry


async def test_a_review_bar_below_the_ship_bar_keeps_the_notes(
    client: httpx.AsyncClient, swap_models, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The bars are independent: no repair above the review bar, but notes below the ship bar."""
    monkeypatch.setenv("AGENT_REVIEW_BAR", "0.9")
    get_settings.cache_clear()
    script = default_script(plans=[SCATTER_PLAN, EMPTY_PLAN])
    script["reviewer"] = [{"json": score(**{"VQ-03": 4})}]  # 51 of 55 technical points: 93 %
    swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert plot["status"] == "needs_attention"
    assert any("sparse markers" in line for line in plot["residual_defects"])


@pytest.mark.parametrize(
    "unreadable",
    [
        # Points lost without a defect line: no notes for the ship bar and nothing to repair.
        {**score(**{"VQ-03": 4}), "defects": []},
        # A technical criterion left unscored is not a perfect one.
        {**score(), "items": [item for item in score()["items"] if item["id"] != "VQ-03"]},
    ],
    ids=["silent-deduction", "missing-technical-item"],
)
async def test_a_review_that_cannot_back_its_score_is_asked_once_more(
    client: httpx.AsyncClient, swap_models, unreadable: dict[str, Any]
) -> None:
    script = default_script(plans=[SCATTER_PLAN, EMPTY_PLAN])
    script["reviewer"] = [{"json": unreadable}, {"json": score()}]
    fake = swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert (plot["status"], plot["residual_defects"]) == ("ok", [])
    assert [(r["attempt"], r["outcome"]) for r in plot["rounds"]] == [(1, "ok")]
    reviewer_calls = [r for r in fake.requests if (r.config.labels or {}).get("agent_kind") == "reviewer"]
    assert len(reviewer_calls) == 2


async def test_the_best_scored_version_ships_when_the_repair_scores_lower(
    client: httpx.AsyncClient, swap_models, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO, logger="anyplot.agents.attribution")
    monkeypatch.setenv("AGENT_REVIEW_BAR", "1.0")
    get_settings.cache_clear()
    script = default_script(plans=[SCATTER_PLAN, EMPTY_PLAN, SECOND_PLAN])
    # Round 1 loses one point (below the review bar, above the ship bar); the repair loses four. No visible-defect
    # ids (`VISIBLE_DEFECT_IDS`), which would leave round 1 a note.
    script["reviewer"] = [{"json": score(**{"VQ-03": 1})}, {"json": score(**{"VQ-03": 4})}]
    swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    shipped = [r["attempt"] for r in plot["rounds"] if r["shipped"]]
    assert shipped == [1]
    # Round 1 meets the ship bar (54 of 55 technical points), so it shows without notes.
    assert (plot["status"], plot["residual_defects"]) == ("ok", [])
    # The attribution line names the render that shipped (round 1's proofread, attempt 2), not the
    # last one rendered (the repair, attempt 3).
    (result,) = attribution_lines(caplog, "pipeline_result")
    assert result["shipped_attempt"] == 2


async def test_two_lost_technical_points_need_no_repair(client: httpx.AsyncClient, swap_models) -> None:
    """`AGENT_REVIEW_BAR` 0.95: 53 of 55 technical points (96 %) ship from round 1 without notes."""
    script = default_script(plans=[SCATTER_PLAN, EMPTY_PLAN])
    script["reviewer"] = [{"json": score(**{"VQ-03": 2})}]
    fake = swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert (plot["status"], plot["attempts"], plot["residual_defects"]) == ("ok", 1, [])
    assert len(adapter_inputs(fake)) == 2  # adapt, proofread


@pytest.mark.parametrize("visible", ["VQ-05", "VQ-02", "VQ-01"])
async def test_a_visible_defect_above_the_review_bar_still_gets_the_repair(
    client: httpx.AsyncClient, swap_models, visible: str
) -> None:
    """Live test round 7 of 2026-10-16: a heatmap shipped after the first try with its axis label cut at the edge.

    Two lost points pass the review bar, but a clipped, overlapping or crammed layout (`VISIBLE_DEFECT_IDS`) is
    what the user sees first: the round goes to the repair with the review's lines."""
    script = default_script(plans=[SCATTER_PLAN, EMPTY_PLAN, SECOND_PLAN])
    script["reviewer"] = [{"json": score(**{visible: 2})}, {"json": score()}]
    fake = swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert (plot["status"], plot["attempts"], plot["residual_defects"]) == ("ok", 2, [])
    inputs = adapter_inputs(fake)
    assert len(inputs) == 3 and "24 sparse markers" in inputs[2]


async def test_an_auto_reject_line_for_clipped_text_gets_the_repair(client: httpx.AsyncClient, swap_models) -> None:
    """AR-09 carries no points of its own: a review with every point and a clipping line used to pass as is."""
    clipped = score()
    clipped["defects"] = ["AR-09 (light): the y axis label 'Wochentag' is cut at the right edge → keep it inside."]
    script = default_script(plans=[SCATTER_PLAN, EMPTY_PLAN, SECOND_PLAN])
    script["reviewer"] = [{"json": clipped}, {"json": score()}]
    fake = swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert (plot["status"], plot["attempts"]) == ("ok", 2)
    assert "Wochentag" in adapter_inputs(fake)[2]


async def test_a_visible_defect_no_round_fixes_ships_with_its_note(client: httpx.AsyncClient, swap_models) -> None:
    """Review of #12204: the better-scored render ships, and the visible defect it still shows is a note."""
    script = default_script(plans=[SCATTER_PLAN, EMPTY_PLAN, SECOND_PLAN])
    script["reviewer"] = [{"json": score(**{"VQ-05": 1})}, {"json": score(**{"VQ-05": 2})}]
    swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert (plot["status"], plot["attempts"]) == ("needs_attention", 2)
    assert [r["attempt"] for r in plot["rounds"] if r["shipped"]] == [1]
    assert [line[:5] for line in plot["residual_defects"]] == ["VQ-05"]


async def test_a_clean_repair_ships_over_a_higher_score_with_a_clipped_label(
    client: httpx.AsyncClient, swap_models
) -> None:
    """Review of #12204: a 96 with an AR-09 line against a clean 94 shipped the clipped plot without a note."""
    clipped = score(**{"VQ-03": 1})
    clipped["defects"] = [*clipped["defects"], "AR-09 (light): the y axis label is cut at the right edge → inside."]
    script = default_script(plans=[SCATTER_PLAN, EMPTY_PLAN, SECOND_PLAN])
    script["reviewer"] = [{"json": clipped}, {"json": score(**{"VQ-03": 2})}]
    swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert [r["attempt"] for r in plot["rounds"] if r["shipped"]] == [2]
    assert (plot["status"], plot["residual_defects"]) == ("ok", [])


async def test_below_the_ship_bar_the_review_lines_are_the_notes(client: httpx.AsyncClient, swap_models) -> None:
    script = default_script(plans=[SCATTER_PLAN, EMPTY_PLAN, SECOND_PLAN, EMPTY_PLAN])
    below = score(**{"VQ-03": 4})  # 51 of 55 technical points: 93 %
    script["reviewer"] = [{"json": below}, {"json": below}]
    swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert plot["status"] == "needs_attention"
    assert any("sparse markers" in line for line in plot["residual_defects"])


# --- What a run reports it changed (the live test of 2026-10-14) ---------------------------

NOTHING_TO_FIX: dict[str, Any] = {"edits": [], "changes": ["Red line and axis titles already present"]}
"""A proofread that changes nothing but writes notes about the code the adaptation wrote."""


async def test_a_proofread_that_changes_nothing_keeps_the_rounds_changes(
    client: httpx.AsyncClient, swap_models
) -> None:
    script = default_script(plans=[SCATTER_PLAN, NOTHING_TO_FIX])
    script["reviewer"] = [{"json": score()}]
    swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert plot["status"] == "ok"
    assert plot["changes"] == SCATTER_PLAN["changes"]


async def test_a_proofread_with_edits_adds_its_changes(client: httpx.AsyncClient, swap_models) -> None:
    script = default_script(plans=[SCATTER_PLAN, SECOND_PLAN])
    script["reviewer"] = [{"json": score()}]
    swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert plot["changes"] == [*SCATTER_PLAN["changes"], "Larger markers"]


async def test_a_shipped_repair_reports_the_changes_its_code_carries(client: httpx.AsyncClient, swap_models) -> None:
    """The repair builds on round 1's code, so the user's request stays among the changes it reports."""
    script = default_script(plans=[SCATTER_PLAN, EMPTY_PLAN, SECOND_PLAN, NOTHING_TO_FIX])
    script["reviewer"] = [{"json": score(**{"VQ-03": 3})}, {"json": score()}]
    swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert [r["attempt"] for r in plot["rounds"] if r["shipped"]] == [2]
    assert plot["changes"] == [*SCATTER_PLAN["changes"], "Larger markers"]


async def test_ship_best_of_round_1_reports_round_1s_changes(client: httpx.AsyncClient, swap_models) -> None:
    script = default_script(plans=[SCATTER_PLAN, EMPTY_PLAN, SECOND_PLAN, EMPTY_PLAN])
    script["reviewer"] = [{"json": score(**{"VQ-05": 1})}, {"json": score(**{"VQ-02": 4})}]
    swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert [r["attempt"] for r in plot["rounds"] if r["shipped"]] == [1]
    assert plot["changes"] == SCATTER_PLAN["changes"]  # not round 2's "Larger markers"


# --- An earlier request stands (the live test of 2026-10-14) -------------------------------

TITLE_REQUEST = "set the title to Vienna 2025"
MARKER_REQUEST = "make the markers bigger"
TITLE_PLAN: dict[str, Any] = {
    "edits": [{"find": 'title = "Exam Score by Study Hours"', "replace": 'title = "Vienna 2025"'}],
    "title": "Vienna 2025",
    "changes": ["Set the title to Vienna 2025"],
}


def reviewer_inputs(fake: Any) -> list[str]:
    requests = [request for request in fake.requests if (request.config.labels or {}).get("agent_kind") == "reviewer"]
    return ["".join(part.text or "" for part in request.contents[-1].parts or []) for request in requests]


async def test_a_later_change_carries_the_earlier_request_to_every_call(client: httpx.AsyncClient, swap_models) -> None:
    script = {
        "root": [
            {"call": "plot_pipeline", "args": {}},
            {"text": ROOT_REPLY},
            {"call": "plot_pipeline", "args": {"change_request": TITLE_REQUEST, "base": "previous"}},
            {"text": "Done: new title."},
            {"call": "plot_pipeline", "args": {"change_request": MARKER_REQUEST, "base": "previous"}},
            {"text": "Done: bigger markers."},
        ],
        "adapter": [{"json": plan} for plan in (SCATTER_PLAN, EMPTY_PLAN, TITLE_PLAN, EMPTY_PLAN)]
        + [{"json": plan} for plan in (SECOND_PLAN, EMPTY_PLAN)],
        "reviewer": [{"json": score()}, {"json": score()}, {"json": score()}],
    }
    fake = swap_models("gemini", script)
    sid = await open_session(client)
    await create_plot(client, sid)
    for text in (TITLE_REQUEST, MARKER_REQUEST):
        response = await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": text})
        plot = next(data for name, data in parse_sse(response.text) if name == "plot")
        assert plot["status"] == "ok"

    adapter = adapter_inputs(fake)
    reviewer = reviewer_inputs(fake)
    assert len(adapter) == 6 and len(reviewer) == 3
    # The first change has no earlier request; the second carries the first to its adaptation, its
    # proofread and its review, fenced as user text.
    earlier = f"{EARLIER_REQUESTS_HEADING}\n\n<user_message>\n1. {TITLE_REQUEST}\n</user_message>"
    assert not any(EARLIER_REQUESTS_HEADING in text for text in [*adapter[:4], *reviewer[:2]])
    assert all(earlier.replace("\n\n", "\n") in text for text in adapter[4:])
    assert earlier in reviewer[2]  # the catalogue reviewer's blocks stand a blank line apart
    assert all(f"<user_message>\n{MARKER_REQUEST}\n</user_message>" in text for text in [*adapter[4:], reviewer[2]])
    shipped = get_services().versions.get(sid)
    assert shipped is not None and shipped.requests == [TITLE_REQUEST, MARKER_REQUEST]
    assert 'title = "Vienna 2025"' in shipped.working


def millions_probe(*ticks: str) -> dict[str, Any]:
    """A probe whose drawn texts are a title and the y tick labels `ticks` (live case Q1 of 2026-10-14)."""
    entries = [("title", "Wohnbevölkerung der Schweiz"), *(("y tick label", tick) for tick in ticks)]
    return {"texts": [], "labels": [{"kind": kind, "text": text} for kind, text in entries]}


def root_inputs(fake: Any) -> list[str]:
    requests = [request for request in fake.requests if (request.config.labels or {}).get("agent_kind") == "root"]
    return [
        json.dumps([content.model_dump(mode="json") for content in request.contents], ensure_ascii=False)
        for request in requests
    ]


async def test_a_requested_format_the_render_misses_goes_to_the_repair(
    client: httpx.AsyncClient, swap_models, backend: FakeBackend
) -> None:
    """`AGENT_EXPECT_CHECK=repair`: the miss is measured like a gate line, the repair fixes it, the reply sees it."""
    script = default_script(plans=[SCATTER_PLAN, EMPTY_PLAN, SECOND_PLAN])
    script["root"] = [{"call": "plot_pipeline", "args": {"expected_texts": ["6,5 Mio."]}}, {"text": ROOT_REPLY}]
    script["reviewer"] = [{"json": score()}, {"json": score()}]
    fixed = millions_probe("6,0 Mio.", "6,5 Mio.")
    backend.script = lambda job, theme: FakeOutcome(
        probe=fixed if len(backend.jobs) >= 3 else millions_probe("6.0 M", "6.5 M")
    )
    fake = swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert (plot["status"], plot["residual_defects"]) == ("ok", [])
    assert [(r["attempt"], r["outcome"], r["shipped"]) for r in plot["rounds"]] == [
        (1, "measured", False),
        (2, "ok", True),
    ]
    assert "shows" not in plot  # the page's plot event carries no drawn texts
    inputs = adapter_inputs(fake)
    miss = 'the plot does not show the requested number format \\"6,5 Mio.\\"'  # quoted inside the notes' JSON
    assert "<user_message>\n6,5 Mio.\n</user_message>" in inputs[0]
    assert miss in inputs[1] and miss in inputs[2]  # the proofread and the repair
    closing = root_inputs(fake)[-1]
    assert "6,0 Mio." in closing and "requested_not_found" in closing
    # With the probe the review request is as before 2026-10-29: the texts are checked against the drawn ones.
    assert not any(REVIEW_TASK in text for text in reviewer_inputs(fake))


@pytest.mark.parametrize("mode", ["repair", "note"])
async def test_a_miss_no_round_fixes_ships_as_a_residual_line(
    client: httpx.AsyncClient, swap_models, backend: FakeBackend, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    monkeypatch.setenv("AGENT_EXPECT_CHECK", mode)
    get_settings.cache_clear()
    plans = [SCATTER_PLAN, EMPTY_PLAN, SECOND_PLAN] if mode == "repair" else [SCATTER_PLAN, EMPTY_PLAN]
    script = default_script(plans=plans)
    script["root"] = [{"call": "plot_pipeline", "args": {"expected_texts": ["6,5 Mio."]}}, {"text": ROOT_REPLY}]
    script["reviewer"] = [{"json": score()}, {"json": score()}]
    backend.script = lambda job, theme: FakeOutcome(probe=millions_probe("6.0 M", "6.5 M"))
    fake = swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert plot["status"] == "needs_attention"
    (line,) = plot["residual_defects"]
    assert line.startswith('SC-02 (light): the plot does not show the requested number format "6,5 Mio."')
    assert len(plot["rounds"]) == (2 if mode == "repair" else 1)
    # `note`: the proofread sees no miss line, since only `repair` measures it.
    assert ("requested number format" in adapter_inputs(fake)[1]) is (mode == "repair")
    closing = root_inputs(fake)[-1]
    assert "requested_not_found" in closing and "6.0 M" in closing


async def test_a_renderer_without_drawn_texts_leaves_a_note_and_no_repair(
    client: httpx.AsyncClient, swap_models, backend: FakeBackend
) -> None:
    """Until the renderer reports `labels`, requested texts are not verifiable: a note, never a pass or a repair."""
    script = default_script(plans=[SCATTER_PLAN, EMPTY_PLAN])
    script["root"] = [{"call": "plot_pipeline", "args": {"expected_texts": ["6,5 Mio."]}}, {"text": ROOT_REPLY}]
    script["reviewer"] = [{"json": score()}]
    backend.script = lambda job, theme: FakeOutcome(probe={"texts": [], "tick_overlaps": 0, "points": 0})
    fake = swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert (plot["status"], plot["residual_defects"]) == ("needs_attention", [UNVERIFIED_LINE.format(theme="light")])
    assert len(plot["rounds"]) == 1
    # The Python runtime keeps the old path: its review request carries no requested texts.
    assert REVIEW_TASK not in reviewer_inputs(fake)[0]


TEMPERATURE = "Temperatur (°C)"
MISS_LINE = (
    f'SC-04 (light): the plot does not show the requested text "{TEMPERATURE}" (the y axis reads "Exam Score") '
    "→ write it exactly as the user asked. Likely cause: the y axis label."
)
REVIEW_TASK = "look for each one in the attached render yourself"
"""A phrase of `REVIEW_EXPECTED_HEADING`: the review request carries the requested texts."""


def missing(line: str = MISS_LINE) -> dict[str, Any]:
    """A catalogue review that cannot find the requested text: one SC-04 point lost, so the points still pass."""
    return {**score(**{"SC-04": 1}), "defects": [line]}


@pytest.fixture
def reviewer_checks_texts(monkeypatch: pytest.MonkeyPatch) -> None:
    """The fixture session's matplotlib runtime as R's (`RRuntime.review_texts`): no drawn texts (the fake's probe
    has no `labels`, as R writes no probe), so the review finds the requested texts in the image."""
    monkeypatch.setattr(PythonRuntime, "review_texts", True)


def ask_for(script: dict[str, list[Any]], *texts: str) -> None:
    script["root"] = [{"call": "plot_pipeline", "args": {"expected_texts": list(texts)}}, {"text": ROOT_REPLY}]


@pytest.mark.usefixtures("reviewer_checks_texts")
async def test_without_drawn_texts_a_text_the_review_confirms_needs_no_note(
    client: httpx.AsyncClient, swap_models
) -> None:
    """Live test of 2026-10-29: ggplot2 drew the requested y axis label, and the plot still needed attention."""
    script = default_script(plans=[SCATTER_PLAN, EMPTY_PLAN])
    ask_for(script, TEMPERATURE)
    script["reviewer"] = [{"json": score()}]
    fake = swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert (plot["status"], plot["residual_defects"]) == ("ok", [])
    assert [(r["attempt"], r["outcome"]) for r in plot["rounds"]] == [(1, "ok")]
    (review,) = reviewer_inputs(fake)
    heading = REVIEW_EXPECTED_HEADING.format(ids="SC-04 (SC-02 for a number format)")
    assert f"{heading}\n\n<user_message>\n{TEMPERATURE}\n</user_message>" in review


@pytest.mark.usefixtures("reviewer_checks_texts")
async def test_without_drawn_texts_a_text_the_review_misses_goes_to_the_repair(
    client: httpx.AsyncClient, swap_models
) -> None:
    """A miss the review reports is repaired as the probe's is, although its points pass the review bar."""
    script = default_script(plans=[SCATTER_PLAN, EMPTY_PLAN, SECOND_PLAN])
    ask_for(script, TEMPERATURE)
    script["reviewer"] = [{"json": missing()}, {"json": score()}]
    fake = swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert (plot["status"], plot["residual_defects"]) == ("ok", [])
    assert [(r["attempt"], r["outcome"], r["shipped"]) for r in plot["rounds"]] == [
        (1, "review", False),
        (2, "ok", True),
    ]
    assert "does not show the requested text" in adapter_inputs(fake)[2]  # the repair gets the review's line
    assert all(REVIEW_TASK in text for text in reviewer_inputs(fake))  # the repaired render's review checks again


@pytest.mark.usefixtures("reviewer_checks_texts")
@pytest.mark.parametrize("mode", ["repair", "note"])
async def test_without_drawn_texts_a_miss_no_round_fixes_ships_as_the_reviewers_line(
    client: httpx.AsyncClient, swap_models, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    monkeypatch.setenv("AGENT_EXPECT_CHECK", mode)
    get_settings.cache_clear()
    plans = [SCATTER_PLAN, EMPTY_PLAN, SECOND_PLAN] if mode == "repair" else [SCATTER_PLAN, EMPTY_PLAN]
    script = default_script(plans=plans)
    ask_for(script, TEMPERATURE, "12 %")
    script["reviewer"] = [{"json": missing()}, {"json": missing()}]
    fake = swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert (plot["status"], plot["residual_defects"]) == ("needs_attention", [MISS_LINE])
    assert len(plot["rounds"]) == (2 if mode == "repair" else 1)
    # The review named only the label: the format it found is no miss.
    shipped = get_services().versions.get(sid)
    assert shipped is not None and shipped.result.shows is not None
    assert (shipped.result.shows.texts, shipped.result.shows.requested_not_found) == (None, [TEMPERATURE])
    assert "requested_not_found" in root_inputs(fake)[-1]


@pytest.mark.usefixtures("reviewer_checks_texts")
async def test_without_drawn_texts_an_unread_review_keeps_the_note(client: httpx.AsyncClient, swap_models) -> None:
    """Never a silent pass: no readable review answered for the requested texts."""
    script = default_script(plans=[SCATTER_PLAN, EMPTY_PLAN])
    ask_for(script, TEMPERATURE)
    unreadable = {"items": [], "defects": [], "suggestions": [], "description": ""}
    script["reviewer"] = [{"json": unreadable}, {"json": unreadable}]
    swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert plot["status"] == "needs_attention"
    assert UNVERIFIED_LINE.format(theme="light") in plot["residual_defects"]


@pytest.mark.usefixtures("reviewer_checks_texts")
async def test_a_text_probe_grounds_the_reply_and_the_review_checks_the_requested_texts(
    client: httpx.AsyncClient, swap_models, backend: FakeBackend, caplog: pytest.LogCaptureFixture
) -> None:
    """User test of 2026-11-01 (Chart.js, bokeh, pygal): the probe of a library without matplotlib reports its drawn
    texts, which reach the root, while the requested texts stay the review's to find, never the probe's to miss."""
    caplog.set_level(logging.INFO, logger="anyplot.agents.attribution")
    script = default_script(plans=[SCATTER_PLAN, EMPTY_PLAN])
    ask_for(script, TEMPERATURE)
    script["reviewer"] = [{"json": score()}]
    probe = {"labels": [{"kind": "title", "text": "Prüfungen"}, {"kind": "y axis label", "text": "Punkte"}]}
    backend.script = lambda job, theme: FakeOutcome(probe=probe)
    fake = swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert (plot["status"], plot["residual_defects"]) == ("ok", [])  # the probe's texts claim no miss
    (review,) = reviewer_inputs(fake)
    assert REVIEW_TASK in review
    shipped = get_services().versions.get(sid)
    assert shipped is not None and shipped.result.shows is not None
    assert shipped.result.shows.texts == {"title": ["Prüfungen"], "y axis label": ["Punkte"]}
    assert "Prüfungen" in root_inputs(fake)[-1]
    (result,) = attribution_lines(caplog, "pipeline_result")
    assert (result["texts"], result["texts_expected"]) == (["title", "y axis label"], True)  # roles, never texts


async def test_a_failed_text_probe_drops_the_texts_and_is_logged(
    client: httpx.AsyncClient, swap_models, backend: FakeBackend, caplog: pytest.LogCaptureFixture
) -> None:
    """A probe that failed (`{"error": <class>}`) is best-effort: the plot ships, the root gets no `texts` and no
    null, and the render's attribution line names the class; a value outside the closed vocabulary reads `other`."""
    caplog.set_level(logging.INFO, logger="anyplot.agents.attribution")
    script = default_script(plans=[SCATTER_PLAN, EMPTY_PLAN])
    script["reviewer"] = [{"json": score()}]
    probes = iter([{"error": "TimeoutError"}, {"error": "Kanton Zürich"}])
    backend.script = lambda job, theme: FakeOutcome(probe=next(probes, None))
    fake = swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert plot["status"] == "ok"
    errors = [line["probe_error"] for line in attribution_lines(caplog, "pipeline_render")]
    assert errors[0] == "TimeoutError" and set(errors) <= {"TimeoutError", "other"}
    closing = root_inputs(fake)[-1]
    assert '\\"texts\\"' not in closing and "Kanton" not in closing


CHECKLIST_MISS: dict[str, Any] = {
    "ok": False,
    "defects": [
        {
            "id": "SC-04",
            "theme": "light",
            "observed": f'the plot does not show the requested text "{TEMPERATURE}" (the y axis reads "Exam Score")',
            "target": "write it exactly as the user asked",
            "likely_cause": "the y axis label",
        }
    ],
}
"""A checklist verdict that cannot find the requested text: its own `Verdict` schema, rendered into a defect line."""


@pytest.fixture
def checklist_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    """The checklist reviewer (`AGENT_REVIEWER_MODE=checklist`) with the rest of the runtime conftest's flow."""
    for name, value in CHECKLIST_FLOW.items():
        monkeypatch.setenv(name, value)
    get_settings.cache_clear()


@pytest.mark.usefixtures("reviewer_checks_texts", "checklist_flow")
@pytest.mark.parametrize(
    ("answers", "plans", "status", "rounds"),
    [
        pytest.param([VERDICT_OK], [SCATTER_PLAN], "ok", 1, id="confirmed"),
        pytest.param([CHECKLIST_MISS, VERDICT_OK], [SCATTER_PLAN, SECOND_PLAN], "ok", 2, id="miss-repaired"),
        # A rejection without defects is no verdict (`Verdict._ok_matches_defects`).
        pytest.param([{"ok": False}, {"ok": False}], [SCATTER_PLAN], "needs_attention", 1, id="unreadable"),
    ],
)
async def test_without_drawn_texts_the_checklist_reviewer_answers_for_the_texts(
    client: httpx.AsyncClient,
    swap_models,
    answers: list[dict[str, Any]],
    plans: list[dict[str, Any]],
    status: str,
    rounds: int,
) -> None:
    """The checklist path end to end (Copilot's review of #12454): its `Verdict` defects are read as the catalogue
    reviewer's lines, a miss goes to the repair, and an answer that is not a verdict keeps the note."""
    script = default_script(plans=plans)
    ask_for(script, TEMPERATURE)
    script["reviewer"] = [{"json": answer} for answer in answers]
    fake = swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert (plot["status"], len(plot["rounds"])) == (status, rounds)
    reviews = reviewer_inputs(fake)
    assert reviews and all(f"{REVIEW_EXPECTED_HEADING.format(ids='SC-04')}\n<user_message>" in text for text in reviews)
    if rounds == 2:
        assert "does not show the requested text" in adapter_inputs(fake)[1]  # the repair gets the reviewer's line
    unverified = UNVERIFIED_LINE.format(theme="light")
    assert (unverified in plot["residual_defects"]) is (status == "needs_attention")
