"""The live flow since 2026-10-13: self-review in every round, the catalogue reviewer, ship-best, the ship bar.

The other flow tests script the checklist reviewer (`conftest.CHECKLIST_FLOW`); these run the defaults.
"""

import logging
from typing import Any

import httpx
import pytest

from agents.anyplot.pipeline import SELF_REVIEW_LINE
from agents.anyplot.scoring import DE_DEFAULTS, SCORED
from agents.anyplot.settings import get_settings

from .fakes import SCATTER_PLAN, default_script
from .test_service_flow import adapter_inputs, attribution_lines, client, create_plot, open_session, runtime


__all__ = ["client", "runtime"]  # fixtures used by name

SECOND_PLAN: dict[str, Any] = {"edits": [{"find": "s=130", "replace": "s=200"}], "changes": ["Larger markers"]}
EMPTY_PLAN: dict[str, Any] = {"edits": [], "changes": []}
DEFECT_LINE = "VQ-03 (light): 24 sparse markers at s=130 look small → s=250 (+120). Likely cause: the marker size."


@pytest.fixture(autouse=True)
def live_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    """The settings defaults: undo the checklist flow the runtime conftest sets for the other tests."""
    for name in ("AGENT_REVIEWER_MODE", "AGENT_SELF_REVIEW", "AGENT_SHIP_BEST"):
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


async def test_a_repair_is_proofread_with_its_findings_before_the_second_review(
    client: httpx.AsyncClient, swap_models
) -> None:
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


async def test_the_best_scored_version_ships_when_the_repair_scores_lower(
    client: httpx.AsyncClient, swap_models
) -> None:
    script = default_script(plans=[SCATTER_PLAN, EMPTY_PLAN, SECOND_PLAN, EMPTY_PLAN])
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
