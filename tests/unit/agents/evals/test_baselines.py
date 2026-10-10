"""The committed baselines: the pinned model has one, and each is a full report on synthetic cases only.

`agents/evals/baselines/claude-haiku-5-5.json` is the first spike-X run on the Claude
arm (2026-10-10, written with `--save-baseline`). A model bump adds the new model's
baseline in the same PR, or this test fails on the new default.
"""

from agents.anyplot.settings import AgentSettings
from agents.evals.matrix import BASELINES_DIR, is_error, load_baseline


def test_the_pinned_model_has_a_baseline() -> None:
    committed = sorted(BASELINES_DIR.glob("*.json"))
    assert committed, "no baseline is committed; the spike-X run of the pinned model writes it with --save-baseline"
    pinned = AgentSettings.model_fields["model"].default
    assert (BASELINES_DIR / f"{pinned}.json").is_file(), f"add baselines/{pinned}.json for the pinned model"
    for path in committed:
        baseline = load_baseline(path)
        assert baseline["stamp"]["model"] == path.stem
        assert not baseline.get("stopped"), f"{path.name} is a partial run"
        assert {run["origin"] for run in baseline["runs"]} == {"fixtures"}, f"{path.name} holds promoted cases"
        assert not any(is_error(run) for run in baseline["runs"]), f"{path.name} has runs that ended in an error"
