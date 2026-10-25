"""`opening.assess`: the library's runtime normalises and scans a catalogue pair; a library without one is blocked."""

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


def test_a_library_without_a_runtime_keeps_its_code_and_is_blocked() -> None:
    """The Python scan blocks the pair as `unsupported-library` and still reports whether it is enabled at all."""
    assert not has_runtime("plotly")
    snapshot = snapshot_from_repo("scatter-basic", "plotly")

    eligibility, normalised = assess(snapshot, "plotly", get_settings())

    assert normalised == snapshot.code
    assert not eligibility.eligible and eligibility.status == "blocked"
    assert "unsupported-library: no normaliser for plotly" in eligibility.reasons
    assert "library-disabled: plotly is not enabled" in eligibility.reasons
