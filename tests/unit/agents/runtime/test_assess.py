"""`opening.assess`: the library's runtime normalises and scans a catalogue pair; a library without one is blocked."""

import pytest

from agents.anyplot.dev_fixture import snapshot_from_repo
from agents.anyplot.opening import assess
from agents.anyplot.render.runtimes import has_runtime
from agents.anyplot.settings import get_settings


def test_a_library_with_a_runtime_is_normalised_and_scanned() -> None:
    snapshot = snapshot_from_repo("scatter-basic", "matplotlib")

    eligibility, normalised = assess(snapshot, "matplotlib", get_settings())

    assert eligibility.eligible and eligibility.status == "coupled"  # its synthetic data couples it, nothing blocks it
    assert all(reason.split(":")[0] in ("statistics", "synthetic-data") for reason in eligibility.reasons)
    assert normalised != snapshot.code and 'THEME = os.getenv("ANYPLOT_THEME", "light")' in normalised


def test_a_library_without_a_runtime_keeps_its_code_and_is_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    """The Python scan blocks the pair as `unsupported-library` and still reports whether it is enabled at all. The
    registry serves all 15 libraries since PB-2a (2026-10-31), so a registry without ggplot2 stands in for one that
    lacks a library."""
    assert has_runtime("plotly") and has_runtime("bokeh")
    monkeypatch.setattr("agents.anyplot.opening.has_runtime", lambda library: library != "ggplot2")
    snapshot = snapshot_from_repo("scatter-basic", "ggplot2")

    eligibility, normalised = assess(snapshot, "ggplot2", get_settings())

    assert normalised == snapshot.code
    assert not eligibility.eligible and eligibility.status == "blocked"
    assert "unsupported-library: no normaliser for ggplot2" in eligibility.reasons
    assert "library-disabled: ggplot2 is not enabled" in eligibility.reasons
