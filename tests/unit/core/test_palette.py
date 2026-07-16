"""
Tests for core/palette.py.

Covers the categorical pool, semantic anchors, theme-adaptive helpers,
the named ``palette`` namespace, and the lazily constructed cmaps.
"""

import re

import pytest

from core.palette import (
    AMBER,
    BLUE,
    CYAN,
    GREEN,
    IMPRINT,
    LAVENDER,
    LIME,
    NAME,
    OCHRE,
    RED,
    ROSE,
    muted_for,
    neutral_for,
    palette,
)


HEX_RE = re.compile(r"^#[0-9A-F]{6}$")


class TestCategoricalPool:
    """Tests for the IMPRINT categorical hues."""

    def test_has_eight_slots(self) -> None:
        """The pool is exactly 8 hues (see module docstring for why 8)."""
        assert len(IMPRINT) == 8

    def test_slot_order_is_hybrid_v3(self) -> None:
        """Slot order is part of the public contract — plots rely on it."""
        assert IMPRINT == [GREEN, LAVENDER, BLUE, OCHRE, RED, CYAN, ROSE, LIME]

    def test_all_unique(self) -> None:
        assert len(set(IMPRINT)) == len(IMPRINT)

    def test_all_valid_uppercase_hex(self) -> None:
        for color in IMPRINT:
            assert HEX_RE.match(color), f"not a normalized hex color: {color}"

    def test_green_is_brand_anchor(self) -> None:
        """Slot 0 is the Okabe-Ito bluish green brand anchor."""
        assert IMPRINT[0] == GREEN == "#009E73"

    def test_amber_outside_categorical_pool(self) -> None:
        """AMBER is a semantic anchor — never returned by IMPRINT[:n]."""
        assert AMBER not in IMPRINT


class TestThemeAdaptiveNeutrals:
    """Tests for neutral_for / muted_for."""

    def test_neutral_flips_with_theme(self) -> None:
        assert neutral_for("light") != neutral_for("dark")

    def test_muted_flips_with_theme(self) -> None:
        assert muted_for("light") != muted_for("dark")

    def test_defaults_to_light(self) -> None:
        assert neutral_for() == neutral_for("light")
        assert muted_for() == muted_for("light")

    def test_neutrals_are_valid_hex(self) -> None:
        for theme in ("light", "dark"):
            assert HEX_RE.match(neutral_for(theme))
            assert HEX_RE.match(muted_for(theme))

    def test_neutrals_outside_categorical_pool(self) -> None:
        for theme in ("light", "dark"):
            assert neutral_for(theme) not in IMPRINT
            assert muted_for(theme) not in IMPRINT


class TestNamedPalette:
    """Tests for the ``palette`` SimpleNamespace API."""

    def test_identity(self) -> None:
        assert palette.name == NAME == "imprint"

    def test_as_list_is_the_pool(self) -> None:
        assert palette.as_list == IMPRINT

    def test_hue_names_match_constants(self) -> None:
        assert palette.green == GREEN
        assert palette.red == RED
        assert palette.blue == BLUE
        assert palette.cyan == CYAN
        assert palette.lime == LIME
        assert palette.ochre == OCHRE
        assert palette.lavender == LAVENDER
        assert palette.rose == ROSE
        assert palette.amber == AMBER

    def test_semantic_roles(self) -> None:
        """warning maps to AMBER, not ochre (ochre is a categorical hue)."""
        assert palette.semantic.good == GREEN
        assert palette.semantic.bad == RED
        assert palette.semantic.warning == AMBER
        assert palette.semantic.info == CYAN

    def test_theme_adaptive_roles_are_callables(self) -> None:
        assert palette.neutral("dark") == neutral_for("dark")
        assert palette.muted("light") == muted_for("light")
        assert palette.semantic.baseline("light") == neutral_for("light")
        assert palette.semantic.other("dark") == muted_for("dark")


class TestCmaps:
    """Tests for the lazily constructed matplotlib cmaps."""

    def test_import_does_not_require_matplotlib(self) -> None:
        """``import core.palette`` must stay matplotlib-free (lazy cmaps)."""
        import subprocess
        import sys

        # A fresh interpreter that blocks matplotlib must still import the
        # module and read the hex constants.
        code = "import sys; sys.modules['matplotlib'] = None; import core.palette; print(core.palette.GREEN)"
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
        assert result.stdout.strip() == "#009E73"

    def test_lazy_cmap_attributes(self) -> None:
        matplotlib = pytest.importorskip("matplotlib")
        import core.palette as pal

        assert pal.imprint_seq.name == "imprint_seq"
        assert pal.imprint_div_light.name == "imprint_div_light"
        assert pal.imprint_div_dark.name == "imprint_div_dark"
        assert isinstance(pal.imprint_seq, matplotlib.colors.LinearSegmentedColormap)

    def test_diverging_factory_flips_midpoint(self) -> None:
        pytest.importorskip("matplotlib")
        from core.palette import diverging

        light = diverging("light")
        dark = diverging("dark")
        # Midpoint (0.5) differs per theme: cream on light, near-black on dark.
        assert light(0.5) != dark(0.5)

    def test_unknown_attribute_raises(self) -> None:
        import core.palette as pal

        name = "no_such_cmap"
        with pytest.raises(AttributeError):
            getattr(pal, name)

    def test_register_with_matplotlib_idempotent(self) -> None:
        matplotlib = pytest.importorskip("matplotlib")
        from core.palette import register_with_matplotlib

        register_with_matplotlib()
        register_with_matplotlib()  # second call must not raise
        assert "imprint_seq" in matplotlib.colormaps
