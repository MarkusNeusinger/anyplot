"""Tests for agents/anyplot/code/letsplot_names.py: the static `lets_plot.__all__` against the installed package."""

import pytest

from agents.anyplot.code.letsplot_names import LETS_PLOT_NAMES
from agents.anyplot.code.normalise import normalise


def test_209_distinct_names_and_the_save_among_them() -> None:
    assert len(LETS_PLOT_NAMES) == 209
    assert "ggsave" in LETS_PLOT_NAMES and "LetsPlot" in LETS_PLOT_NAMES
    assert all(name.isidentifier() for name in LETS_PLOT_NAMES)


def test_the_names_are_the_installed_lets_plot_all() -> None:
    """A lets-plot upgrade that changes `__all__` fails here until the data is refreshed (module docstring)."""
    lets_plot = pytest.importorskip("lets_plot")

    assert set(lets_plot.__all__) == LETS_PLOT_NAMES


def test_the_expanded_star_import_binds_what_the_star_import_bound() -> None:
    """Code that reads every name of `__all__`: the normaliser's explicit import binds the same objects."""
    lets_plot = pytest.importorskip("lets_plot")
    names = sorted(set(lets_plot.__all__))
    code = "from lets_plot import *\n\n" + "".join(f"_ = {name}\n" for name in names)
    expanded = normalise(code, library="letsplot")

    assert "import *" not in expanded and expanded.startswith("from lets_plot import (\n    GGBunch,\n    LetsPlot,\n")
    star: dict[str, object] = {}
    explicit: dict[str, object] = {}
    exec(compile(code, "star.py", "exec"), star)
    exec(compile(expanded, "explicit.py", "exec"), explicit)
    assert all(explicit[name] is star[name] for name in names)
