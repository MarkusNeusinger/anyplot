"""anyplot imprint palette — v3 hybrid-v3 ordering.

Single source of truth for the 8 categorical hues, 3 semantic anchors,
sequential cmap, and diverging cmap used across the project.

Design rationale: docs/reference/palette-variants/v3/decision-rationale.md

Why "imprint": the palette is tuned for warm-cream paper backgrounds with
matte ink-like categorical hues — the academic-publishing-imprint mood
(Penguin Classics, FT Books, Nature Methods). It deliberately sits in the
Okabe-Ito / Paul Tol "muted" / ColorBrewer Set2 family.

Why 8 (not 7): closes the cyan-or-lavender gap in the previous 7-hue
palette; matches the academic-publishing-family pool size; sits at the
ΔE_CVD discrimination sweet spot before n=9+ breaks down.

Layout
------
- 8 categorical hexes in slot order 0..7 (hybrid-v3 sort: brand anchor,
  then hue-family-diverse first 4, then pure-CVD-greedy tail). Reached
  by position via ``IMPRINT[:n]`` or by name via ``palette.green`` etc.
- 3 semantic anchors OUTSIDE the categorical pool. Never returned by
  ``IMPRINT[:n]``. Reached only by name: ``palette.amber``,
  ``palette.neutral(theme)``, ``palette.muted(theme)``. The neutrals are
  theme-adaptive — they flip between light and dark themes by design,
  same pattern as Apple HIG / Material Design / GitHub Primer.
- Continuous ramps, per theme and per use (``fields`` or ``marks``), as
  ``(position, hex)`` stops: ``sequential_stops(theme, use)`` (``imprint_seq``,
  brand green and blue, light → dark on the light page and dark → bright on
  the dark one) and ``diverging_stops(theme, use)`` (``imprint_div``, matte
  red ↔ midpoint ↔ blue). Matplotlib cmaps via ``sequential(theme, use)`` and
  ``diverging(theme, use)``. Categorical colours stay identical across themes;
  the continuous ramps do not.
"""

from __future__ import annotations

import math
from itertools import pairwise
from types import SimpleNamespace
from typing import TYPE_CHECKING, Literal


# matplotlib is a heavy optional dep — import lazily inside the cmap helpers so
# that callers who only need the hex constants (core/images.py, R/Julia helper
# scripts, etc.) don't pay for it. Type-check imports still get the real type.
if TYPE_CHECKING:
    from matplotlib.colors import LinearSegmentedColormap


# ─────────────────────────────────────────────────────────────────────────────
# Identity
# ─────────────────────────────────────────────────────────────────────────────

NAME: str = "imprint"

# ─────────────────────────────────────────────────────────────────────────────
# Categorical hues — slot order from hybrid-v3 sort
# ─────────────────────────────────────────────────────────────────────────────

GREEN: str = "#009E73"  # slot 0 — brand anchor (Okabe-Ito's bluish green)
LAVENDER: str = "#C475FD"  # slot 1
BLUE: str = "#4467A3"  # slot 2
OCHRE: str = "#BD8233"  # slot 3
RED: str = "#AE3030"  # slot 4 — semantic anchor for bad/loss/error (deferred past first-4)
CYAN: str = "#2ABCCD"  # slot 5
ROSE: str = "#954477"  # slot 6
LIME: str = "#99B314"  # slot 7

IMPRINT: list[str] = [GREEN, LAVENDER, BLUE, OCHRE, RED, CYAN, ROSE, LIME]

# ─────────────────────────────────────────────────────────────────────────────
# Semantic anchors OUTSIDE the categorical pool
# ─────────────────────────────────────────────────────────────────────────────

# Fixed hex — never theme-adaptive. Chosen for max ΔE_CVD against the 8
# categorical members (min ΔE_CVD = 14.52 to lime — the two more saturated
# amber candidates #D4A017 and #D4AF37 both collapse to ΔE_CVD ≈ 2.3 against
# lime under deuteranopia).
AMBER: str = "#DDCC77"  # warning / caution

# Theme-adaptive neutrals. Same hex pair as LIGHT_THEME["ink"] / DARK_THEME["ink"]
# and LIGHT_THEME["ink_muted"] / DARK_THEME["ink_muted"] in scripts/_palette_common.py
# (kept duplicated here so this module doesn't depend on the scripts/ tree).
_INK_LIGHT: str = "#1A1A17"  # full-contrast neutral on cream bg
_INK_DARK: str = "#F0EFE8"  # full-contrast neutral on warm near-black bg
_INK_MUTED_LIGHT: str = "#6B6A63"  # soft-contrast neutral on cream bg
_INK_MUTED_DARK: str = "#A8A79F"  # soft-contrast neutral on warm near-black bg
_PAGE_LIGHT: str = "#FAF8F1"  # plot surface, light theme
_PAGE_DARK: str = "#1A1A17"  # plot surface, dark theme (same hex as the light theme's ink)


def neutral_for(theme: str = "light") -> str:
    """Theme-adaptive ink: totals / baseline / outline.

    Same hex as the chart's text and gridlines, so "totals" / "baseline"
    series read as part of the chart's structural layer rather than as
    "just another category".

    Parameters
    ----------
    theme : "light" | "dark", default "light"
    """
    return _INK_LIGHT if theme == "light" else _INK_DARK


def muted_for(theme: str = "light") -> str:
    """Theme-adaptive ink-muted: other / rest / disabled.

    Soft-contrast rather than full-contrast. Meant for "other" / "rest"
    slices in stacked charts, disabled / inactive series, confidence
    bands, and annotations that should sit behind the data.

    Parameters
    ----------
    theme : "light" | "dark", default "light"
    """
    return _INK_MUTED_LIGHT if theme == "light" else _INK_MUTED_DARK


# ─────────────────────────────────────────────────────────────────────────────
# Named API — by hue, by semantic role
# ─────────────────────────────────────────────────────────────────────────────

# Slot order and named access are independent. Callers who want
# "the loss colour" reach for ``palette.red`` or ``palette.semantic.bad``;
# callers who just need n distinct series reach for ``palette.as_list[:n]``.
palette = SimpleNamespace(
    name=NAME,
    as_list=IMPRINT,
    # by hue
    green=GREEN,
    red=RED,
    blue=BLUE,
    cyan=CYAN,
    lime=LIME,
    ochre=OCHRE,
    lavender=LAVENDER,
    rose=ROSE,
    # semantic anchors outside the categorical pool
    amber=AMBER,
    neutral=neutral_for,  # call with "light" / "dark"
    muted=muted_for,
    # role-based aliases — semantic.warning maps to amber (NOT ochre — ochre
    # is the "earth / commodity" categorical hue, not a caution signal)
    semantic=SimpleNamespace(good=GREEN, bad=RED, warning=AMBER, info=CYAN, baseline=neutral_for, other=muted_for),
)


# ─────────────────────────────────────────────────────────────────────────────
# Continuous ramps: imprint_seq (sequential) and imprint_div (diverging)
# ─────────────────────────────────────────────────────────────────────────────

# A ramp is a tuple of (position, hex) stops from the lowest value (0.0) to the
# highest (1.0); colours between two stops blend linearly in sRGB, as
# matplotlib's ``from_list`` does (Vega-Lite and ggplot2 blend in HCL and
# CIELAB by default, which moves the colours between the stops a little,
# never the stops). Each ramp exists per theme and per use:
#
# - "fields": coloured areas whose cells touch and fill the plot (heatmaps,
#   spectrograms, filled contours, maps, tiles). Wide lightness range; the low
#   end sits close to the page.
# - "marks": coloured marks that sit on the page themselves (points, lines,
#   outlines). Every colour of the sequential marks ramp keeps WCAG 3:1 against
#   its page (WCAG 2.1 SC 1.4.11), so no mark fades into the page.
#
# In both themes the high values stand out from the page and the low values
# recede into it: the light ramps run light → dark, the dark ramps dark →
# bright. Stop positions are proportional to CIELAB L*, so lightness runs
# linearly along each sequential ramp. Design and numbers:
# docs/decisions/2026-11-23-continuous-ramps-per-theme.md.

Theme = Literal["light", "dark"]
Use = Literal["fields", "marks"]
Stops = tuple[tuple[float, str], ...]

_SEQUENTIAL: dict[tuple[str, str], Stops] = {
    # pale mint → brand green → blue → navy (L* 82 → 16)
    ("fields", "light"): ((0.0, "#66E2B2"), (0.368, GREEN), (0.582, BLUE), (1.0, "#002850")),
    # deep green → brand green → pale blue (L* 32 → 87)
    ("fields", "dark"): ((0.0, "#00573D"), (0.467, GREEN), (1.0, "#CDD9FF")),
    # brand green → blue → navy (L* 58 → 16)
    ("marks", "light"): ((0.0, GREEN), (0.338, BLUE), (1.0, "#002850")),
    # dark green → brand green → pale blue (L* 44 → 87)
    ("marks", "dark"): ((0.0, "#007755"), (0.32, GREEN), (1.0, "#CDD9FF")),
}

# The midpoint of ``imprint_div`` for marks on the dark page. The ``muted`` ink
# (#A8A79F, 7.2:1 on #1A1A17) would outshine the poles (matte red 2.7:1, blue
# 3.1:1), so the marks near zero would lead the plot. This darker grey keeps a
# mark at zero visible at about 3:1 (3.08:1), level with the poles, so the
# extremes lead. It is deliberately not a palette colour. The light page keeps
# the ``muted`` ink, which already sits level with its poles there.
_DIV_MARKS_MID_DARK: str = "#686762"

#: Every hex of the continuous ramps that is not already a palette colour or a
#: theme token. ``automation/scripts/contract_check.py`` allows these too.
RAMP_STOPS: tuple[str, ...] = ("#66E2B2", "#002850", "#00573D", "#CDD9FF", "#007755", _DIV_MARKS_MID_DARK)


def _key(theme: str, use: str) -> tuple[str, str]:
    if theme not in ("light", "dark"):
        raise ValueError(f"theme must be 'light' or 'dark', not {theme!r}")
    if use not in ("fields", "marks"):
        raise ValueError(f"use must be 'fields' or 'marks', not {use!r}")
    return use, theme


def sequential_stops(theme: Theme = "light", use: Use = "fields") -> Stops:
    """``imprint_seq`` stops for one theme and one use, low value → high value.

    Parameters
    ----------
    theme : "light" | "dark", default "light"
    use : "fields" | "marks", default "fields"
        "fields" for areas whose cells touch (heatmaps, spectrograms, filled
        contours, maps, tiles); "marks" for points, lines and outlines that sit
        on the page, where every colour keeps 3:1 against it.
    """
    return _SEQUENTIAL[_key(theme, use)]


def diverging_stops(theme: Theme = "light", use: Use = "fields") -> Stops:
    """``imprint_div`` stops: matte red ↔ midpoint ↔ blue.

    The midpoint is the page colour for fields, so a cell at the midpoint
    reads as part of the page. For marks it is a grey that keeps at least 3:1
    against the page, because a page-coloured mark would vanish against it:
    the ``muted`` ink #6B6A63 on light and #686762 on dark, where the
    ``muted`` ink would outshine the poles (the rule ordered categories follow
    too).
    """
    use_, theme_ = _key(theme, use)
    if use_ == "fields":
        midpoint = _PAGE_LIGHT if theme_ == "light" else _PAGE_DARK
    else:
        midpoint = muted_for("light") if theme_ == "light" else _DIV_MARKS_MID_DARK
    return ((0.0, RED), (0.5, midpoint), (1.0, BLUE))


def ramp_color(stops: Stops, value: float) -> str:
    """The hex at ``value`` (0.0 to 1.0, clamped) of a ramp, blended linearly in sRGB between its stops.

    A missing value (NaN or infinite) returns ``"none"``, which matplotlib and
    SVG read as no colour, so it draws nothing rather than the low end.
    """
    if not math.isfinite(value):
        return "none"
    value = min(1.0, max(0.0, value))
    for (p0, c0), (p1, c1) in pairwise(stops):
        if value <= p1:
            share = (value - p0) / (p1 - p0) if p1 > p0 else 0.0
            channels = (
                round(int(c0[i : i + 2], 16) + (int(c1[i : i + 2], 16) - int(c0[i : i + 2], 16)) * share)
                for i in (1, 3, 5)
            )
            return "#" + "".join(f"{channel:02X}" for channel in channels)
    return stops[-1][1]


def _cmap_name(base: str, theme: str, use: str) -> str:
    return f"{base}_{theme}" if use == "fields" else f"{base}_marks_{theme}"


def sequential(theme: Theme = "light", use: Use = "fields") -> LinearSegmentedColormap:
    """``imprint_seq`` as a matplotlib cmap, named ``imprint_seq_{theme}`` or ``imprint_seq_marks_{theme}``."""
    from matplotlib.colors import LinearSegmentedColormap

    stops = sequential_stops(theme, use)
    return LinearSegmentedColormap.from_list(_cmap_name("imprint_seq", theme, use), list(stops))


def diverging(theme: Theme = "light", use: Use = "fields") -> LinearSegmentedColormap:
    """``imprint_div`` as a matplotlib cmap, named ``imprint_div_{theme}`` or ``imprint_div_marks_{theme}``.

    Parameters
    ----------
    theme : "light" | "dark", default "light"
        For fields the midpoint is the page: warm cream #FAF8F1 on light,
        warm near-black #1A1A17 on dark.
    use : "fields" | "marks", default "fields"
        For marks the midpoint is #6B6A63 on light (the ``muted`` anchor) and
        #686762 on dark.
    """
    from matplotlib.colors import LinearSegmentedColormap

    stops = diverging_stops(theme, use)
    return LinearSegmentedColormap.from_list(_cmap_name("imprint_div", theme, use), list(stops))


# The three cmap module attributes of the first Imprint release stay, built
# lazily on first access via ``__getattr__`` below, which keeps
# ``import core.palette`` matplotlib-free: ``imprint_div_light`` and
# ``imprint_div_dark`` are the fields ramps of their theme, and
# ``imprint_seq`` is the light theme's fields ramp under its old name.
# Theme-aware callers use ``sequential(theme, use)`` and ``diverging(theme, use)``.


def __getattr__(name: str) -> LinearSegmentedColormap:
    # Lazy-construct the cmap module attributes on first access so importing
    # this module does not require matplotlib. The return annotation is a
    # forward reference under `from __future__ import annotations`, so it
    # does not trigger a runtime matplotlib import.
    if name == "imprint_seq":
        from matplotlib.colors import LinearSegmentedColormap

        cm = LinearSegmentedColormap.from_list("imprint_seq", list(sequential_stops("light", "fields")))
        globals()[name] = cm
        return cm
    if name == "imprint_div_light":
        cm = diverging("light")
        globals()[name] = cm
        return cm
    if name == "imprint_div_dark":
        cm = diverging("dark")
        globals()[name] = cm
        return cm
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# ─────────────────────────────────────────────────────────────────────────────
# Matplotlib registration — opt-in side effect, called by core.images
# ─────────────────────────────────────────────────────────────────────────────


def register_with_matplotlib() -> None:
    """Register every Imprint ramp with matplotlib.

    Registers ``imprint_seq`` and ``imprint_div`` for both themes and both
    uses (``imprint_seq_light``, ``imprint_seq_marks_dark``, …) plus the old
    name ``imprint_seq``. Idempotent — re-registering an existing cmap is
    silently skipped.
    """
    # Resolve via module globals so the lazy ``__getattr__`` builds each cmap
    # on first access (avoids a top-level matplotlib import here too).
    import sys

    import matplotlib

    mod = sys.modules[__name__]
    cmaps = [mod.imprint_seq, mod.imprint_div_light, mod.imprint_div_dark]
    themes: tuple[Theme, ...] = ("light", "dark")
    for theme in themes:
        cmaps.append(sequential(theme, "fields"))
        cmaps.extend(factory(theme, "marks") for factory in (sequential, diverging))
    for cm in cmaps:
        try:
            matplotlib.colormaps.register(cm)
        except ValueError:
            # Already registered (e.g. when this module is re-imported in
            # the same Python process).
            pass


__all__ = [
    # identity
    "NAME",
    # categorical pool
    "IMPRINT",
    "GREEN",
    "LAVENDER",
    "BLUE",
    "OCHRE",
    "RED",
    "CYAN",
    "ROSE",
    "LIME",
    # semantic anchors
    "AMBER",
    "neutral_for",
    "muted_for",
    # named API
    "palette",
    # continuous ramps
    "RAMP_STOPS",
    "sequential_stops",
    "diverging_stops",
    "ramp_color",
    "sequential",
    "diverging",
    # cmaps — resolved lazily via module __getattr__ (avoids module-level
    # matplotlib import; see explanation at top of file)
    "imprint_seq",  # noqa: F822
    "imprint_div_light",  # noqa: F822
    "imprint_div_dark",  # noqa: F822
    # mpl integration
    "register_with_matplotlib",
]
