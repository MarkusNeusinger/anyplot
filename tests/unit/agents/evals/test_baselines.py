"""The committed baselines: the pinned model has one, and each is a full report on synthetic cases only.

No baseline is committed yet: the first spike-X run on the Claude arm writes
`agents/evals/baselines/claude-haiku-5-5.json` (`--save-baseline`). Until a baseline
exists this test skips; from then on a model bump must add the new model's baseline.
"""

import pytest

from agents.anyplot.settings import AgentSettings
from agents.evals.matrix import BASELINES_DIR, load_baseline


def test_the_pinned_model_has_a_baseline() -> None:
    committed = sorted(BASELINES_DIR.glob("*.json"))
    if not committed:
        pytest.skip("no baseline committed yet; the first spike-X run creates claude-haiku-5-5.json")
    pinned = AgentSettings.model_fields["model"].default
    assert (BASELINES_DIR / f"{pinned}.json").is_file(), f"add baselines/{pinned}.json for the pinned model"
    for path in committed:
        baseline = load_baseline(path)
        assert baseline["stamp"]["model"] == path.stem
        assert not baseline.get("stopped"), f"{path.name} is a partial run"
        assert {run["origin"] for run in baseline["runs"]} == {"fixtures"}, f"{path.name} holds promoted cases"
