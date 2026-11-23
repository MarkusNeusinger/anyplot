"""
Tests for core/palette.py.

Covers the categorical pool, semantic anchors, theme-adaptive helpers,
the named ``palette`` namespace, and the lazily constructed cmaps.
"""

import re
from itertools import pairwise
from pathlib import Path
from typing import cast

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
    RAMP_STOPS,
    RED,
    ROSE,
    Theme,
    Use,
    diverging_stops,
    muted_for,
    neutral_for,
    palette,
    ramp_color,
    sequential_stops,
)
from tests.libraries import import_library


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
        matplotlib = import_library("matplotlib")
        import core.palette as pal

        assert pal.imprint_seq.name == "imprint_seq"
        assert pal.imprint_div_light.name == "imprint_div_light"
        assert pal.imprint_div_dark.name == "imprint_div_dark"
        assert isinstance(pal.imprint_seq, matplotlib.colors.LinearSegmentedColormap)

    def test_diverging_factory_flips_midpoint(self) -> None:
        import_library("matplotlib")
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
        matplotlib = import_library("matplotlib")
        from core.palette import register_with_matplotlib

        register_with_matplotlib()
        register_with_matplotlib()  # second call must not raise
        assert "imprint_seq" in matplotlib.colormaps

    def test_register_with_matplotlib_names_every_ramp(self) -> None:
        matplotlib = import_library("matplotlib")
        from core.palette import register_with_matplotlib

        register_with_matplotlib()
        for theme in ("light", "dark"):
            for name in ("imprint_seq", "imprint_seq_marks", "imprint_div", "imprint_div_marks"):
                assert f"{name}_{theme}" in matplotlib.colormaps

    def test_cmaps_follow_the_stops(self) -> None:
        """Each cmap returns its stops at their positions and blends like ``ramp_color`` in between."""
        import_library("matplotlib")
        import core.palette as pal

        for theme, use in RAMPS:
            for factory, stops in (
                (pal.sequential, sequential_stops(theme, use)),
                (pal.diverging, diverging_stops(theme, use)),
            ):
                cmap = factory(theme, use)
                for value in (*(position for position, _ in stops), 0.1, 0.45, 0.8):
                    assert _channels(_hex_of(cmap(value))) == pytest.approx(
                        _channels(ramp_color(stops, value)), abs=2
                    ), (cmap.name, value)

    def test_cmap_names(self) -> None:
        import_library("matplotlib")
        import core.palette as pal

        assert pal.sequential("dark").name == "imprint_seq_dark"
        assert pal.sequential("light", "marks").name == "imprint_seq_marks_light"
        assert pal.diverging("dark").name == "imprint_div_dark"
        assert pal.diverging("light", "marks").name == "imprint_div_marks_light"

    def test_old_names_are_the_fields_ramps(self) -> None:
        """``imprint_seq`` keeps its name as the light fields ramp; ``imprint_div_{theme}`` are the fields ramps."""
        import_library("matplotlib")
        import core.palette as pal

        for value in (0.0, 0.3, 0.7, 1.0):
            assert pal.imprint_seq(value) == pal.sequential("light")(value)
            assert pal.imprint_div_light(value) == pal.diverging("light")(value)
            assert pal.imprint_div_dark(value) == pal.diverging("dark")(value)


# --- continuous ramps --------------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[3]
THEMES: list[Theme] = ["light", "dark"]
RAMPS: list[tuple[Theme, Use]] = [("light", "fields"), ("dark", "fields"), ("light", "marks"), ("dark", "marks")]
PAGE = {"light": "#FAF8F1", "dark": "#1A1A17"}
SAMPLES = [i / 255 for i in range(256)]


def _channels(hex_color: str) -> tuple[int, int, int]:
    return int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)


def _hex_of(rgba: tuple[float, ...]) -> str:
    return "#" + "".join(f"{round(channel * 255):02X}" for channel in rgba[:3])


def _luminance(color: str | tuple[float, float, float]) -> float:
    """WCAG 2.x relative luminance of a hex or of sRGB channels in 0..255."""
    channels = _channels(color) if isinstance(color, str) else color
    linear = [c / 255 / 12.92 if c / 255 <= 0.03928 else ((c / 255 + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _unrounded(stops: tuple[tuple[float, str], ...], value: float) -> tuple[float, float, float]:
    """The ramp at ``value`` before rounding to 8 bits, so a test of its shape does not read rounding noise."""
    for (p0, c0), (p1, c1) in pairwise(stops):
        if value <= p1:
            share = (value - p0) / (p1 - p0)
            a, b = _channels(c0), _channels(c1)
            return a[0] + (b[0] - a[0]) * share, a[1] + (b[1] - a[1]) * share, a[2] + (b[2] - a[2]) * share
    raise AssertionError(value)


def _contrast(a: str, b: str) -> float:
    high, low = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


class TestContinuousRamps:
    """imprint_seq and imprint_div per theme and per use (owner's decision of 2026-11-23)."""

    def test_sequential_stops_are_the_chosen_ones(self) -> None:
        """The owner picked these stops and positions from renders; any change is a new decision."""
        assert sequential_stops("light", "fields") == (
            (0.0, "#66E2B2"),
            (0.368, "#009E73"),
            (0.582, "#4467A3"),
            (1.0, "#002850"),
        )
        assert sequential_stops("dark", "fields") == ((0.0, "#00573D"), (0.467, "#009E73"), (1.0, "#CDD9FF"))
        assert sequential_stops("light", "marks") == ((0.0, "#009E73"), (0.338, "#4467A3"), (1.0, "#002850"))
        assert sequential_stops("dark", "marks") == ((0.0, "#007755"), (0.32, "#009E73"), (1.0, "#CDD9FF"))

    def test_defaults_are_light_fields(self) -> None:
        assert sequential_stops() == sequential_stops("light", "fields")
        assert diverging_stops() == diverging_stops("light", "fields")

    @pytest.mark.parametrize(("theme", "use"), RAMPS)
    def test_stops_run_from_zero_to_one(self, theme: Theme, use: Use) -> None:
        for stops in (sequential_stops(theme, use), diverging_stops(theme, use)):
            positions = [position for position, _ in stops]
            assert positions[0] == 0.0 and positions[-1] == 1.0
            assert positions == sorted(set(positions))
            assert all(HEX_RE.match(color) for _, color in stops)

    @pytest.mark.parametrize(("theme", "use"), RAMPS)
    def test_every_sequential_ramp_passes_through_brand_green(self, theme: Theme, use: Use) -> None:
        assert GREEN in [color for _, color in sequential_stops(theme, use)]

    @pytest.mark.parametrize(("theme", "use"), RAMPS)
    def test_high_values_stand_out_and_low_values_recede(self, theme: Theme, use: Use) -> None:
        """Contrast against the page rises along the whole ramp: light → dark on light, dark → bright on dark."""
        stops = sequential_stops(theme, use)
        page = PAGE[theme]
        luminance = [_luminance(_unrounded(stops, value)) for value in SAMPLES]
        if theme == "light":
            assert all(value < _luminance(page) for value in luminance)
            assert all(b < a for a, b in pairwise(luminance))
        else:
            assert all(value > _luminance(page) for value in luminance)
            assert all(b > a for a, b in pairwise(luminance))
        assert _contrast(stops[-1][1], page) > 12

    @pytest.mark.parametrize("theme", THEMES)
    def test_marks_ramp_keeps_three_to_one_on_its_page(self, theme: Theme) -> None:
        """WCAG 2.1 SC 1.4.11: every colour of the marks ramp, not only its stops, reaches 3:1 on its own page."""
        stops = sequential_stops(theme, "marks")
        assert min(_contrast(ramp_color(stops, value), PAGE[theme]) for value in SAMPLES) >= 3.0

    @pytest.mark.parametrize("theme", THEMES)
    def test_fields_ramp_starts_closer_to_the_page_than_the_marks_ramp(self, theme: Theme) -> None:
        """The fields ramp buys its range with a low end near the page, which is why marks get their own ramp."""
        fields, marks = sequential_stops(theme, "fields"), sequential_stops(theme, "marks")
        assert _contrast(fields[0][1], PAGE[theme]) < 3.0 <= _contrast(marks[0][1], PAGE[theme])

    @pytest.mark.parametrize("theme", THEMES)
    def test_diverging_midpoint_is_the_page_for_fields_and_muted_for_marks(self, theme: Theme) -> None:
        assert diverging_stops(theme, "fields") == ((0.0, RED), (0.5, PAGE[theme]), (1.0, BLUE))
        assert diverging_stops(theme, "marks") == ((0.0, RED), (0.5, muted_for(theme)), (1.0, BLUE))

    def test_ramp_color(self) -> None:
        stops = sequential_stops("light", "marks")
        assert ramp_color(stops, 0.0) == "#009E73"
        assert ramp_color(stops, 0.338) == "#4467A3"
        assert ramp_color(stops, 1.0) == "#002850"
        assert ramp_color(stops, -1.0) == "#009E73"  # clamped
        assert ramp_color(stops, 2.0) == "#002850"
        assert ramp_color(((0.0, "#000000"), (1.0, "#FFFFFF")), 0.5) == "#808080"

    @pytest.mark.parametrize(("theme", "use"), [("Light", "fields"), ("dark", "lines"), ("", "")])
    def test_unknown_theme_or_use_raises(self, theme: str, use: str) -> None:
        for factory in (sequential_stops, diverging_stops):
            with pytest.raises(ValueError):
                factory(*cast(tuple[Theme, Use], (theme, use)))

    @pytest.mark.parametrize(("theme", "use"), RAMPS)
    def test_every_written_copy_of_the_sequential_stops_is_these(self, theme: Theme, use: Use) -> None:
        """The stops are written out where code cannot import this module; each copy must carry them, positions too."""
        stops = sequential_stops(theme, use)
        hexes, positions = [c for _, c in stops], [p for p, _ in stops]
        python = "[" + ", ".join(f'({p:.1f}, "{c}")' if p in (0, 1) else f'({p}, "{c}")' for p, c in stops) + "]"
        plotly = python.replace("(", "[").replace(")", "]")
        javascript = "[" + ", ".join(f'[{p:g}, "{c}"]' for p, c in stops) + "]"
        r = f"colours = c({', '.join(map(repr, hexes))}), values = c({', '.join(f'{p:g}' for p in positions)})"
        julia = (
            "cgrad(["
            + ", ".join(f'colorant"{c}"' for c in hexes)
            + f"], [{', '.join(f'{p:.1f}' if p in (0, 1) else str(p) for p in positions)}])"
        )
        app = f"{{ at: [{', '.join(f'{p:g}' for p in positions)}], hex: [{', '.join(map(repr, hexes))}] }}"
        copies = {
            "automation/js-render/render.mjs": [javascript],
            "prompts/default-style-guide.md": [python],
            "app/src/sections/palette/paletteHelpers.ts": [app],
            "prompts/library/ggplot2.md": [r.replace("'", '"')],
            "prompts/library/makie.md": [julia],
            "prompts/library/plotly.md": [plotly],
            **{
                f"prompts/library/{library}.md": [python, python.replace('"', "'")]
                for library in ("matplotlib", "seaborn", "bokeh", "pygal", "altair", "plotnine", "letsplot")
            },
        }
        for path, forms in copies.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            assert any(form in text for form in forms), (path, forms[0])

    def test_every_written_copy_of_the_diverging_midpoint_matches_its_use(self) -> None:
        """Each copy pairs the page midpoint with fields and the muted midpoint with marks, both themes."""
        page = {t: diverging_stops(t, "fields")[1][1] for t in THEMES}
        muted = {t: diverging_stops(t, "marks")[1][1] for t in THEMES}
        names = {
            "prompts/default-style-guide.md": ("DIV_FIELDS =", "DIV_MARKS  ="),
            "automation/js-render/render.mjs": ("divFields:", "divMarks:"),
            "prompts/library/altair.md": ("DIV_FIELDS_RANGE =", "DIV_MARKS_RANGE ="),
            "prompts/library/ggplot2.md": ("DIV_MID_FIELDS <-", "DIV_MID_MARKS  <-"),
            "prompts/library/letsplot.md": ("DIV_MID_FIELDS =", "DIV_MID_MARKS ="),
            "prompts/library/plotnine.md": ("DIV_MID_FIELDS =", "DIV_MID_MARKS ="),
            "prompts/library/makie.md": ("const ANYPLOT_DIV_FIELDS =", "const ANYPLOT_DIV_MARKS ="),
            **{
                f"prompts/library/{library}.md": ("DIV_FIELDS =", "DIV_MARKS =")
                for library in ("matplotlib", "seaborn", "bokeh", "pygal", "plotly")
            },
        }
        # A copy may name the theme token instead of writing the two hexes out.
        page_tokens, muted_tokens = ("PAGE_BG", "pageBg"), ("INK_MUTED",)
        for path, (fields_name, marks_name) in names.items():
            lines = [line.strip() for line in (ROOT / path).read_text(encoding="utf-8").splitlines()]
            fields = next(line for line in lines if line.startswith(fields_name))
            marks = next(line for line in lines if line.startswith(marks_name))
            assert any(t in fields for t in page_tokens) or all(page[t] in fields for t in THEMES), (path, fields)
            assert any(t in marks for t in muted_tokens) or all(muted[t] in marks for t in THEMES), (path, marks)
            assert not any(muted[t] in fields for t in THEMES), (path, fields)
            assert not any(page[t] in marks for t in THEMES), (path, marks)

    def test_ramp_stops_lists_every_new_hex(self) -> None:
        """RAMP_STOPS is what a hex allow-list adds to the palette and the theme tokens."""
        known = {*IMPRINT, AMBER, *PAGE.values(), *(muted_for(t) for t in THEMES), *(neutral_for(t) for t in THEMES)}
        ramp_hexes = {
            color for theme, use in RAMPS for _, color in (*sequential_stops(theme, use), *diverging_stops(theme, use))
        }
        assert set(RAMP_STOPS) == ramp_hexes - known
