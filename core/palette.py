"""anyplot imprint palette — v3 hybrid-v3 ordering.

Single source of truth for the 8 categorical hues, 3 semantic anchors,
sequential cmap, and diverging cmap used across the project.

Design rationale: docs/reference/palette-variants-v3/decision-rationale.md

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
- Sequential cmap (``imprint_seq``): brand-green → blue.
- Diverging cmap (``imprint_div_light`` / ``imprint_div_dark``): matte-red
  ↔ near-neutral ↔ blue. Theme-adaptive via ``diverging(theme)`` factory.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING


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
# Sequential + diverging cmaps
# ─────────────────────────────────────────────────────────────────────────────

# Sequential + diverging cmaps. Constructed lazily on attribute access via
# ``__getattr__`` below — keeps ``import core.palette`` matplotlib-free for
# callers that only need the hex constants. Public names preserved:
#   core.palette.imprint_seq, .imprint_div_light, .imprint_div_dark


def diverging(theme: str = "light") -> LinearSegmentedColormap:
    """Diverging cmap: matte-red ↔ near-neutral ↔ blue.

    The midpoint flips per theme to keep the diverging "zero" reading as
    part of the chart bg rather than as an opaque grey blob.

    Parameters
    ----------
    theme : "light" | "dark", default "light"
        On light bg, midpoint = warm cream #FAF8F1; on dark bg, midpoint
        = warm near-black #1A1A17.
    """
    from matplotlib.colors import LinearSegmentedColormap

    midpoint = "#FAF8F1" if theme == "light" else "#1A1A17"
    return LinearSegmentedColormap.from_list(f"imprint_div_{theme}", [RED, midpoint, BLUE])


def __getattr__(name: str) -> LinearSegmentedColormap:
    # Lazy-construct the cmap module attributes on first access so importing
    # this module does not require matplotlib. The return annotation is a
    # forward reference under `from __future__ import annotations`, so it
    # does not trigger a runtime matplotlib import.
    if name == "imprint_seq":
        from matplotlib.colors import LinearSegmentedColormap

        cm = LinearSegmentedColormap.from_list("imprint_seq", [GREEN, BLUE])
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
    """Register imprint_seq + both diverging cmap variants with matplotlib.

    Idempotent — re-registering an existing cmap is silently skipped.
    """
    # Resolve via module globals so the lazy ``__getattr__`` builds each cmap
    # on first access (avoids a top-level matplotlib import here too).
    import sys

    import matplotlib

    mod = sys.modules[__name__]
    for cm in (mod.imprint_seq, mod.imprint_div_light, mod.imprint_div_dark):
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
    # cmaps — resolved lazily via module __getattr__ (avoids module-level
    # matplotlib import; see explanation at top of file)
    "imprint_seq",  # noqa: F822
    "imprint_div_light",  # noqa: F822
    "imprint_div_dark",  # noqa: F822
    "diverging",
    # mpl integration
    "register_with_matplotlib",
]
