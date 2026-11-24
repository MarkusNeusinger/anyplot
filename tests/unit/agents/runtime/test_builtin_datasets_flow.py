"""Nothing in the chat renders a catalogue original (owner decision of 2026-11-23, built-in datasets).

The eligibility scan accepts an original that loads a built-in example dataset, because the chat never runs the
original: a session's opening only normalises and scans it (`opening.assess`), and the pipeline renders a run form
only after `_check` passed the adapted working form under the strict SECURITY profile (`pipeline.py`, the render
call). These tests pin that order on the real service with a fake renderer: a plan that keeps the loader never
reaches the renderer, and the render job of a plan that drops it holds no loader.
"""

import logging
from typing import Any

import httpx
import pytest

from agents.anyplot.code.validate import PLACEHOLDER
from agents.anyplot.dev_fixture import snapshot_from_repo
from agents.anyplot.pipeline import _check
from agents.anyplot.render.backends.fake import FakeBackend
from agents.anyplot.render.runtimes import runtime_for
from agents.main import Runtime

from . import test_service_flow
from .fakes import SCATTER_PLAN, default_script
from .test_service_flow import adapter_inputs, attribution_lines, client, create_plot, open_session, runtime


__all__ = ["client", "runtime"]  # fixtures used by name

DATASET_IMPORT = "from sklearn.datasets import make_regression\n"
DATASET_CALL = "_features, _target = make_regression(n_samples=180, n_features=1, random_state=42)\n"
DROPS_THE_LOADER: dict[str, Any] = {
    **SCATTER_PLAN,
    "edits": [*SCATTER_PLAN["edits"], {"find": DATASET_IMPORT, "replace": ""}, {"find": DATASET_CALL, "replace": ""}],
}


def with_a_dataset(code: str) -> str:
    """scatter-basic's matplotlib file with a scikit-learn generator beside its own data, as an ML spec's file has."""
    assert "import numpy as np\n" in code and "np.random.seed(42)\n" in code
    code = code.replace("import numpy as np\n", "import numpy as np\n" + DATASET_IMPORT, 1)
    return code.replace("np.random.seed(42)\n", DATASET_CALL + "np.random.seed(42)\n", 1)


@pytest.fixture
def dataset_original(monkeypatch: pytest.MonkeyPatch) -> None:
    """`open_session` opens scatter-basic in matplotlib on that file instead of the catalogue's."""
    real = test_service_flow.snapshot_body

    def body(spec_id: str = "scatter-basic", library: str = "matplotlib") -> dict[str, Any]:
        snapshot = real(spec_id, library)
        return {**snapshot, "code": with_a_dataset(snapshot["code"])}

    monkeypatch.setattr(test_service_flow, "snapshot_body", body)


def test_check_refuses_the_unedited_original_with_a_built_in_dataset() -> None:
    """The working form the adapter starts from is the normalised original; left as it is (with the placeholder the
    adaptation adds), `_check` refuses it for the loader's import, so the pipeline never renders it."""
    runtime = runtime_for("matplotlib")
    normalised = runtime.normalise(with_a_dataset(snapshot_from_repo("scatter-basic", "matplotlib").code), "matplotlib")
    working = normalised.replace("np.random.seed(42)\n", f"{PLACEHOLDER}\nnp.random.seed(42)\n", 1)

    check = _check(working, library="matplotlib", palette=[], base=working)

    assert not check.may_render
    assert "banned-import" in check.blocking_rules
    assert any("sklearn.datasets.make_regression" in line for line in check.blocking)


@pytest.mark.usefixtures("dataset_original")
async def test_a_plan_that_keeps_the_loader_never_reaches_the_renderer(
    client: httpx.AsyncClient, swap_models, backend: FakeBackend, runtime: Runtime, caplog: pytest.LogCaptureFixture
) -> None:
    """The session opens (the original is eligible, with the hint), and two plans that leave the generator in place are
    refused by the check before any render: the renderer gets no job at all."""
    caplog.set_level(logging.INFO, logger="anyplot.agents.attribution")
    fake = swap_models("gemini", default_script(plans=[SCATTER_PLAN, SCATTER_PLAN]))
    sid = await open_session(client)
    eligibility = runtime.eligibility_cache[("scatter-basic", "matplotlib")]
    assert eligibility.eligible and eligibility.status == "coupled"
    assert "built-in-dataset: 2 lines" in eligibility.reasons

    plot = next(data for name, data in await create_plot(client, sid) if name == "plot")

    assert backend.jobs == []
    assert plot["status"] != "ok"
    assert "Built-in example dataset at" in adapter_inputs(fake)[0]  # the hint reached the adapter
    checks = attribution_lines(caplog, "pipeline_check")
    assert [line["outcome"] for line in checks] == ["rejected", "rejected"]
    assert all("banned-import" in line["validator"] for line in checks)


@pytest.mark.usefixtures("dataset_original")
async def test_the_render_job_of_a_plan_that_drops_the_loader_holds_none(
    client: httpx.AsyncClient, swap_models, backend: FakeBackend
) -> None:
    """The repair that removes the import and the call passes the check, and only then does a job reach the renderer:
    its source is the run form of the adapted code, which loads nothing built in."""
    swap_models("gemini", default_script(plans=[SCATTER_PLAN, DROPS_THE_LOADER]))
    sid = await open_session(client)

    plot = next(data for name, data in await create_plot(client, sid) if name == "plot")

    assert (plot["status"], plot["attempts"]) == ("ok", 2)
    assert len(backend.jobs) == 1
    (job,) = backend.jobs
    assert "sklearn" not in job.source and "make_regression" not in job.source
