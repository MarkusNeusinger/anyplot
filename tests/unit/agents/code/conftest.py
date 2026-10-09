"""Shared fixtures for the code-handling tests: a catalogue-style source, the catalogue files, a validator stub."""

import sys
import textwrap
import types
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[4]
CATALOGUE_FILES = sorted(REPO_ROOT.glob("plots/*/implementations/python/matplotlib.py")) + sorted(
    REPO_ROOT.glob("plots/*/implementations/python/seaborn.py")
)
VALIDATE_MODULE = "agents.anyplot.code.validate"


def source(text: str) -> str:
    """Dedent a triple-quoted snippet and drop its leading newline."""
    return textwrap.dedent(text).lstrip("\n")


# A catalogue file in miniature: header, sys.path guard, theme block, palette, synthetic
# data, a literal limit, the catalogue title and a tight savefig at a 16:9 figure.
CATALOGUE = source('''
    """ anyplot.ai
    scatter-demo: Demo Scatter
    Library: matplotlib 3.11.2 | Python 3.13.13
    Quality: 90/100 | Updated: 2026-10-01
    """

    import os
    import sys


    # This file is named matplotlib.py; drop its directory from sys.path.
    _here = os.path.dirname(os.path.abspath(__file__))
    sys.path = [p for p in sys.path if os.path.abspath(p) != _here]

    import matplotlib.pyplot as plt
    import numpy as np


    # Theme tokens
    THEME = os.getenv("ANYPLOT_THEME", "light")
    PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
    INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
    IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

    np.random.seed(42)
    x = np.random.uniform(0, 10, 50)
    y = 2 * x + np.random.normal(0, 1, 50)

    fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
    ax.scatter(x, y, color=IMPRINT[0])
    ax.set_ylim(0, 25)
    ax.set_title("scatter-demo · python · matplotlib · anyplot.ai", color=INK)
    plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
''')

# The same file after normalisation: header and guard gone, dpi 200, no bbox_inches.
CATALOGUE_NORMALISED = source("""
    import os


    import matplotlib.pyplot as plt
    import numpy as np


    # Theme tokens
    THEME = os.getenv("ANYPLOT_THEME", "light")
    PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
    INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
    IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

    np.random.seed(42)
    x = np.random.uniform(0, 10, 50)
    y = 2 * x + np.random.normal(0, 1, 50)

    fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
    ax.scatter(x, y, color=IMPRINT[0])
    ax.set_ylim(0, 25)
    ax.set_title("scatter-demo · python · matplotlib · anyplot.ai", color=INK)
    plt.savefig(f"plot-{THEME}.png", dpi=200, facecolor=PAGE_BG)
""")


@dataclass(frozen=True, slots=True)
class StubFinding:
    """The validator's `Finding` shape."""

    rule: str
    message: str
    line: int | None


@pytest.fixture
def stub_validator(monkeypatch: pytest.MonkeyPatch) -> Callable[..., list[tuple[str, str]]]:
    """Install a stand-in `validate` module; returns a setter for the findings it reports.

    The real `validate.py` is written on a sibling branch; the readiness scan imports
    it at call time, so the stub in `sys.modules` takes its place either way.
    """
    calls: list[tuple[str, str]] = []
    findings: list[StubFinding] = []

    def validate_security(code: str, *, library: str) -> list[StubFinding]:
        calls.append((code, library))
        return list(findings)

    monkeypatch.setitem(sys.modules, VALIDATE_MODULE, types.SimpleNamespace(validate_security=validate_security))

    def set_findings(*items: StubFinding) -> list[tuple[str, str]]:
        findings[:] = items
        return calls

    return set_findings
