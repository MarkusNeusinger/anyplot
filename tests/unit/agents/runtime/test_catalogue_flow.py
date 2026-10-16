"""The live flow since 2026-10-13: self-review in every round, the catalogue reviewer, ship-best, the ship bar.

The other flow tests script the checklist reviewer (`conftest.CHECKLIST_FLOW`); these run the defaults.
"""

import json
import logging
from typing import Any

import httpx
import pytest

from agents.anyplot.grounding import UNVERIFIED_LINE
from agents.anyplot.pipeline import EARLIER_REQUESTS_HEADING, SELF_REVIEW_LINE
from agents.anyplot.render.backends.fake import FakeBackend, FakeOutcome
from agents.anyplot.scoring import DE_DEFAULTS, SCORED
from agents.anyplot.services import get_services
from agents.anyplot.settings import get_settings

from .conftest import CHECKLIST_FLOW
from .fakes import ROOT_REPLY, SCATTER_PLAN, default_script
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
    # Round 1 loses one point (below the review bar, above the ship bar); the repair loses four.
    script["reviewer"] = [{"json": score(**{"VQ-05": 1})}, {"json": score(**{"VQ-02": 4})}]
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


@pytest.mark.parametrize("visible", ["VQ-05", "VQ-02"])
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


async def test_a_visible_defect_no_round_fixes_ships_above_the_ship_bar_without_notes(
    client: httpx.AsyncClient, swap_models
) -> None:
    """The ship bar is untouched: the repair round is spent, the better-scored render ships without notes."""
    script = default_script(plans=[SCATTER_PLAN, EMPTY_PLAN, SECOND_PLAN])
    script["reviewer"] = [{"json": score(**{"VQ-05": 1})}, {"json": score(**{"VQ-05": 2})}]
    swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert (plot["status"], plot["attempts"], plot["residual_defects"]) == ("ok", 2, [])
    assert [r["attempt"] for r in plot["rounds"] if r["shipped"]] == [1]


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
    swap_models("gemini", script)
    sid = await open_session(client)

    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert (plot["status"], plot["residual_defects"]) == ("needs_attention", [UNVERIFIED_LINE.format(theme="light")])
    assert len(plot["rounds"]) == 1
