"""Tests for agents/anyplot/code/readiness.py: blocked, coupled and clean, with a stubbed validator."""

import sys
import types
from collections.abc import Callable
from pathlib import Path

import pytest

from agents.anyplot.code.normalise import normalise
from agents.anyplot.code.readiness import MAP_SPECS, Readiness, scan
from agents.anyplot.schemas import MAX_NOTE_CHARS

from .conftest import CATALOGUE_FILES, CATALOGUE_NORMALISED, VALIDATE_MODULE, StubFinding, source


ENABLED = ("matplotlib", "seaborn")
HEAD = source("""
    import os

    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd

    THEME = os.getenv("ANYPLOT_THEME", "light")
    PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
    df = load_user_data()
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
""")
SAVE = 'plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)\n'

StubSetter = Callable[..., list[tuple[str, str]]]


def check(body: str, *, spec_id: str = "scatter-basic", library: str = "matplotlib") -> Readiness:
    code = HEAD + source(body).rstrip("\n") + "\n" + SAVE
    result = scan(code, spec_id=spec_id, library=library, enabled_libraries=ENABLED)
    assert all(len(hint) <= MAX_NOTE_CHARS for hint in result.hints)
    assert all(len(reason) <= MAX_NOTE_CHARS for reason in result.reasons)
    return result


def categories(result: Readiness) -> list[str]:
    return [reason.split(":")[0] for reason in result.reasons]


def test_clean(stub_validator: StubSetter) -> None:
    calls = stub_validator()
    result = check('ax.plot(df["x"], df["y"], color=PAGE_BG)\nax.set_ylim(bottom=0)\nax.axhline(0)\n')

    assert result == Readiness("clean", [], [])
    assert calls and calls[0][1] == "matplotlib"


def test_normalised_catalogue_file_is_coupled(stub_validator: StubSetter) -> None:
    stub_validator()
    result = scan(CATALOGUE_NORMALISED, spec_id="scatter-demo", library="matplotlib", enabled_libraries=ENABLED)

    assert result.status == "coupled"
    assert categories(result) == ["limits", "palette", "synthetic-data"]
    assert result.hints[0].startswith("Literal axis limits or ticks at line 20 `ax.set_ylim(0, 25)`")
    assert "IMPRINT (3 entries)" in result.hints[1]
    assert "line 14 `np.random.seed(42)`" in result.hints[2]


@pytest.mark.parametrize(
    ("body", "category"),
    [
        ("ax.set_xlim(0, 100)", "limits"),
        ("ax.set_xticks([0, 5, 10])", "limits"),
        ("ax.set_yticks(np.arange(0, 101, 20))", "limits"),
        ('ax.set_xlim(pd.Timestamp("2024-01-01"), df["d"].max())', "limits"),
        ("plt.ylim(-1.05, 1.05)", "limits"),
        ('ax.annotate("Peak", xy=(5, 92.3))', "annotations"),
        ('ax.annotate("Peak", (df["x"][3], 92.3), xytext=(10, 10), textcoords="offset points")', "annotations"),
        ('ax.text(2.5, 40, "label")', "annotations"),
        ("ax.axvline(x=1990)", "annotations"),
        ("ax.axhspan(10, 20, xmin=0, xmax=1)", "annotations"),
        ("ax.hlines(50, 0, df['x'].max())", "annotations"),
        ('ax.legend(title="r = 0.87")', "statistics"),
        ('ax.text(0.5, 0.5, "p < 0.001", transform=ax.transAxes)', "statistics"),
        ('label = "n = 180 students"', "statistics"),
        ("upper = mean + 1.96 * se", "statistics"),
        ('IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]', "palette"),
        ('COLORS = ["#009E73", "#AE3030"]', "palette"),
        ("ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))", "date-locators"),
        ('ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))', "date-locators"),
        ("x = np.random.default_rng(1).normal(size=10)", "synthetic-data"),
        ("rng = np.random.default_rng(1)\ny = rng.normal(size=10)", "synthetic-data"),
        ("import random\nvalue = random.uniform(0, 1)", "synthetic-data"),
        ("from scipy import stats\nsample = stats.norm.rvs(size=50)", "synthetic-data"),
    ],
)
def test_each_coupling_rule(stub_validator: StubSetter, body: str, category: str) -> None:
    stub_validator()
    result = check(body)

    assert result.status == "coupled"
    assert categories(result) == [category]
    assert len(result.hints) == 1 and "line " in result.hints[0]


@pytest.mark.parametrize(
    "body",
    [
        "ax.set_ylim(0, None)",
        'ax.set_xlim(df["x"].min(), df["x"].max() * 1.15)',
        "ax.set_xticks([])",
        'ax.text(0.02, 0.95, "note", transform=ax.transAxes)',
        'fig.text(0.98, 0.02, "source", ha="right")',
        'ax.annotate("top", xy=(0.5, 1.02), xycoords="axes fraction")',
        'r = 0.5\nax.set_title(f"r = {r:.2f}")',
        "ax.xaxis.set_major_locator(mdates.AutoDateLocator())",
        'IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]',
        'GRAYS = ["#111111", "#222222"]',
    ],
)
def test_not_coupled(stub_validator: StubSetter, body: str) -> None:
    stub_validator()
    assert check(body).status == "clean"


def test_one_hint_per_category_names_lines_and_counts(stub_validator: StubSetter) -> None:
    stub_validator()
    body = "\n".join(
        f"ax.axvline({year}, color=PAGE_BG, linestyle='--', linewidth=0.8, alpha=0.5)" for year in range(1990, 2020)
    )
    result = check(body)

    assert result.reasons == ["annotations: 30 lines"]
    hint = result.hints[0]
    assert hint.startswith("Annotations at literal data coordinates at line 12 `ax.axvline(1990")
    assert " more: place them from df values or drop them." in hint
    assert len(hint) <= MAX_NOTE_CHARS


def test_canvas_note_does_not_change_status(stub_validator: StubSetter) -> None:
    stub_validator()
    code = HEAD.replace("figsize=(8, 4.5), dpi=400", "figsize=(16, 12)") + SAVE.replace("dpi=400", "dpi=200")
    result = scan(normalise(code, library="matplotlib"), spec_id="x", library="matplotlib", enabled_libraries=ENABLED)

    assert result.status == "clean"
    assert result.reasons[0].startswith("canvas: figsize (16, 12) at dpi 200 renders 3200x2400")


# --- blocked -------------------------------------------------------------------------------


@pytest.mark.parametrize("spec_id", sorted(MAP_SPECS))
def test_map_specs_are_blocked(stub_validator: StubSetter, spec_id: str) -> None:
    stub_validator()
    result = check("", spec_id=spec_id)

    assert result.status == "blocked" and categories(result) == ["map-spec"] and result.hints == []


def test_thirteen_map_specs() -> None:
    assert len(MAP_SPECS) == 13
    assert "scatter-pitch-events" not in MAP_SPECS and "hexbin-map-geographic" not in MAP_SPECS


def test_library_not_enabled_or_unsupported(stub_validator: StubSetter) -> None:
    stub_validator()
    code = HEAD + SAVE

    disabled = scan(code, spec_id="scatter-basic", library="seaborn", enabled_libraries=["matplotlib"])
    assert disabled.status == "blocked" and categories(disabled) == ["library-disabled"]
    unsupported = scan(code, spec_id="scatter-basic", library="plotly", enabled_libraries=["plotly"])
    assert categories(unsupported) == ["unsupported-library"]


def test_security_findings_block(stub_validator: StubSetter) -> None:
    stub_validator(
        StubFinding("banned-import", "import of 'subprocess' is not allowed", 3),
        StubFinding("size", "the code exceeds 48 KB", None),
        *(StubFinding("dunder", f"dunder {i}", i) for i in range(5)),
    )
    result = check("")

    assert result.status == "blocked"
    assert result.reasons[0] == "security: banned-import at line 3: import of 'subprocess' is not allowed"
    assert result.reasons[1] == "security: size: the code exceeds 48 KB"
    assert result.reasons[-1] == "security: 2 more findings"


def test_unavailable_validator_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, VALIDATE_MODULE, None)  # makes the import raise ImportError
    result = check("")

    assert result.status == "blocked"
    assert result.reasons == ["security: the validator failed (ModuleNotFoundError)"]


def test_crashing_validator_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    def explode(code: str, *, library: str) -> list[StubFinding]:
        raise RuntimeError("boom")

    monkeypatch.setitem(sys.modules, VALIDATE_MODULE, types.SimpleNamespace(validate_security=explode))
    assert check("").reasons == ["security: the validator failed (RuntimeError)"]


@pytest.mark.parametrize(
    ("code", "reason"),
    [
        (HEAD.replace('THEME = os.getenv("ANYPLOT_THEME", "light")', 'THEME = "light"') + SAVE, "no-theme"),
        (HEAD + 'plt.savefig("plot.png", dpi=400)\n', "savefig-target: single-theme savefig target 'plot.png'"),
        (HEAD + 'plt.savefig(os.path.join(d, f"plot-{THEME}.png"))\n', "savefig-target: saves to os.path.join"),
        (HEAD + "if True:\n    " + SAVE, "savefig-target: the last savefig is not a module-level statement"),
        (HEAD, "savefig-target: no savefig call"),
        (HEAD + 'fig.savefig("draft.png")\n' + SAVE, "savefig-target: single-theme savefig target 'draft.png'"),
    ],
)
def test_structure_blocks(stub_validator: StubSetter, code: str, reason: str) -> None:
    stub_validator()
    result = scan(code, spec_id="scatter-basic", library="matplotlib", enabled_libraries=ENABLED)

    assert result.status == "blocked"
    assert any(r.startswith(reason) for r in result.reasons), result.reasons


def test_syntax_error_blocks_without_calling_the_validator(stub_validator: StubSetter) -> None:
    calls = stub_validator()
    result = scan("def broken(:\n", spec_id="x", library="matplotlib", enabled_libraries=ENABLED)

    assert result == Readiness("blocked", ["syntax: line 1 does not parse"], [])
    assert calls == []


# --- catalogue sweep ------------------------------------------------------------------------


@pytest.mark.skipif(not CATALOGUE_FILES, reason="plots/ is not checked out")
@pytest.mark.parametrize("path", CATALOGUE_FILES, ids=lambda p: f"{p.parts[-4]}-{p.stem}")
def test_catalogue_scan_never_raises(stub_validator: StubSetter, path: Path) -> None:
    stub_validator()
    code = normalise(path.read_text(encoding="utf-8"), library=path.stem)
    result = scan(code, spec_id=path.parts[-4], library=path.stem, enabled_libraries=ENABLED)

    assert result.status in ("blocked", "coupled", "clean")
    assert all(len(text) <= MAX_NOTE_CHARS for text in [*result.reasons, *result.hints])
    assert (result.status == "coupled") == bool(result.hints)
