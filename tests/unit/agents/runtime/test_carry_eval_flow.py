"""The switch eval's own flow (`agents/evals/carry.py`), run against scripted models and the fake renderer.

The live run checks the code models write; this runs the same steps in process with fakes, so the eval
itself is known to drive the route sequence the page uses: the first plot, the tuning turn whose run
hands the owner's five decisions over, the switch asked for in the chat, the switch route with
`source: chat` and the carry run in the new library.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest

import agents.main as agents_main
from agents.anyplot.services import Services
from agents.evals.carry import OWNER_EXAMPLES, TUNE_MESSAGE, _Lines, run_target
from agents.main import Runtime, app

from .fakes import SCATTER_PLAN, VERDICT_OK
from .test_plot_memory import KEEP_PLAN, seaborn_plan
from .test_service_flow import adapter_inputs, permissive_queue


@pytest.fixture
def runtime(monkeypatch: pytest.MonkeyPatch) -> Iterator[Runtime]:
    """The eval reads the runtime through `get_runtime()` itself, so both it and the routes get this one."""
    fresh = Runtime(queue=permissive_queue())
    app.dependency_overrides[agents_main.get_runtime] = lambda: fresh
    monkeypatch.setattr(agents_main, "get_runtime", lambda: fresh)
    yield fresh
    app.dependency_overrides.clear()


@pytest.mark.usefixtures("runtime", "services")
async def test_the_chat_path_tunes_switches_and_carries(swap_models, tmp_path: Path, services: Services) -> None:
    tune = {"change_request": TUNE_MESSAGE, "base": "previous", "remember": OWNER_EXAMPLES}
    swap_models(
        "gemini",
        {
            "root": [
                {"call": "plot_pipeline", "args": {}},
                {"text": "Here."},
                {"call": "plot_pipeline", "args": tune},
                {"text": "All five are in."},
                {"call": "switch_plot", "args": {"library": "seaborn"}},
                {"text": "The plot comes in seaborn with your decisions."},
                {"call": "plot_pipeline", "args": {}},
                {"text": "In seaborn."},
            ],
            "adapter": [{"json": SCATTER_PLAN}, {"json": KEEP_PLAN}, {"json": seaborn_plan()}],
            "reviewer": [{"json": VERDICT_OK}] * 3,
        },
    )

    outcome = await run_target("seaborn", "matplotlib", tmp_path, _Lines(), via="chat")

    assert outcome.remembered == 5
    assert outcome.switch == {"library": "seaborn", "plot": True}
    assert outcome.status in ("ok", "needs_attention") and outcome.version == 3
    # The scripted seaborn code carries none of the five intents: the checks say so, and the target fails.
    assert set(outcome.checks) == {"reference_line", "latex_annotation", "star_markers", "label_text", "x_limits"}
    assert not outcome.passed
    assert (tmp_path / "seaborn" / "plot.py").is_file()


@pytest.mark.usefixtures("runtime", "services")
async def test_the_chat_path_stops_when_no_switch_was_asked_for(swap_models, tmp_path: Path) -> None:
    swap_models(
        "gemini",
        {
            "root": [
                {"call": "plot_pipeline", "args": {}},
                {"text": "Here."},
                {"text": "Which change do you mean?"},
                {"text": "Which library?"},
            ],
            "adapter": [{"json": SCATTER_PLAN}],
            "reviewer": [{"json": VERDICT_OK}],
        },
    )

    outcome = await run_target("seaborn", "matplotlib", tmp_path, _Lines(), via="chat")

    assert outcome.switch is None and outcome.note == "the switch turn asked for no switch to this library"
    assert not outcome.passed


@pytest.mark.usefixtures("runtime", "services")
async def test_the_memory_path_seeds_the_examples_and_runs_the_carry(swap_models, tmp_path: Path) -> None:
    fake = swap_models(
        "gemini",
        {
            "root": [{"call": "plot_pipeline", "args": {}}, {"text": "In seaborn."}],
            "adapter": [{"json": seaborn_plan()}],
            "reviewer": [{"json": VERDICT_OK}],
        },
    )

    outcome = await run_target("seaborn", "matplotlib", tmp_path, _Lines())

    assert outcome.via == "memory" and outcome.status in ("ok", "needs_attention") and outcome.version == 1
    carried = adapter_inputs(fake)[0]
    assert all(item["text"] in carried for item in OWNER_EXAMPLES)  # the seeded memory reached the adapter
