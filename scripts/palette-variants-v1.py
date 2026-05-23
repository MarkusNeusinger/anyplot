#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "colorspacious>=1.1.2",
#   "numpy>=2.0",
#   "matplotlib>=3.10",
#   "pillow>=11.0",
# ]
# ///
"""Palette variant generator v1 for anyplot (Issue #5817 — second round).

This is the **v1 follow-up** to ``scripts/palette-variants.py``. The first
round (variants A–F) compared candidates against Okabe-Ito. From that round,
**variant D ("balanced")** was adopted as the live ``ANYPLOT_PALETTE`` in
``core/images.py``. v1 therefore changes the baseline — every candidate here
is measured against **live D**, not Okabe-Ito.

Five new candidates explore "refine vs. rethink":

  D1 — d-tight-chroma   (D's max-min but C ∈ [24, 32] — narrower paper-ink)
  D2 — d-wide-spread    (D's max-min with 60° pairwise hue spread target)
  D3 — d-swap-tan       (D's max-min but hue band [50°, 90°] banned at pos 6
                         — forces an alternative to the live tan #BA843E)
  T  — tetradic         (4 anchors 90° apart, brand-green anchored, 3 fillers)
  W  — warm-pole        (D's max-min plus a warm-hue scoring bonus 30°–80°)

For each, the script:

  1. Picks 7 hues respecting the strategy's hue rule, the paper-ink
     chroma/lightness corridor (J' ∈ [45,72], C ∈ [22,50]), and gamut.
  2. Reorders positions 2..4 so the first 4 maximise their internal
     min worst-CVD ΔE — the "most beautiful subset" criterion.
  3. Builds a perceptually-uniform continuous colormap starting at the
     brand green.
  4. Renders a self-contained HTML page with the same diagnostic blocks
     as v0, plus a new CAM02-UCS **color wheel** section that places every
     palette hue at its actual (C, H) coordinates — Adobe Color / Dracula
     Pro style — so the geometry of the palette is visible at a glance.

The live D palette itself is rendered as ``D-baseline.html`` using the same
template, so it sits in the lineup as "the one to beat".

Output: ``docs/reference/palette-variants-v1/{D-baseline,D1..D3,T,W}-…html``
plus ``index.html`` (hero wheel + candidate cards) and ``compare.html``.

Run::

    uv run --script scripts/palette-variants-v1.py
"""

from __future__ import annotations

import argparse
import itertools
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
from colorspacious import cspace_convert


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

# Brand anchor — kept inline so this variant-search script stays decoupled
# from runtime core.images imports.
OK_GREEN = "#009E73"

# Live anyplot palette — mirrored verbatim from core/images.py
# (ANYPLOT_PALETTE, lines 48–63). This is the v1 baseline-to-beat; every
# candidate in this script is measured against ANYPLOT_D_PALETTE. If you
# change one, change the other.
ANYPLOT_D_PALETTE = [
    "#009E73",  # ANYPLOT_GREEN  — brand anchor (also Okabe-Ito green)
    "#9418DB",  # ANYPLOT_PURPLE
    "#B71D27",  # ANYPLOT_RED
    "#16B8F3",  # ANYPLOT_SKY
    "#99B314",  # ANYPLOT_LIME
    "#D359A7",  # ANYPLOT_PINK
    "#BA843E",  # ANYPLOT_TAN
]
from _palette_common import (  # noqa: E402
    CVD_ORDER,
    DARK_THEME_FULL,
    LIGHT_THEME_FULL,
    NEUTRAL_DARK,
    NEUTRAL_LIGHT,
    PAGE_CSS,
    PAGE_JS,
    cell_class,
    hex_to_rgb1,
    pairwise_delta_e,
    _peaks_png_b64,
    render_cmap_demo,
    render_colormap_row,
    render_first_n_summary,
    render_gradient,
    render_hero_mockup_pair,
    render_legend,
    render_matrix_block,
    render_sample_charts,
    render_swatch_table,
    rgb1_to_hex,
    simulate_cvd,
    to_jab,
    worst_cvd_pairwise_delta_e,
)


DEFAULT_OUT_DIR = REPO_ROOT / "docs" / "reference" / "palette-variants-v1"

# ── Paper-ink corridor in CAM02-UCS (J' = lightness, C = chroma, H = hue) ─────
# Lower J' bound: at 45 the colour is dark enough to read against #F5F3EC light bg.
# Upper J' bound: at 72 the colour is still light enough to read against #121210 dark bg.
# Chroma corridor is the paper-ink lever (Caligo sits at C≈60-90, Okabe-Ito at
# C≈40-75). Per-variant overrides below let D be the most muted ("dusty") and
# E honour Okabe-Ito's hotter native chroma.
J_MIN, J_MAX, J_STEP = 45.0, 72.0, 2.0
C_MIN, C_MAX, C_STEP = 22.0, 50.0, 2.0
H_STEP_DEG = 5.0


# Per-variant chroma corridors — tightening C is the single biggest paper-ink lever.
# At hue ≈ 25° (red) the in-gamut max chroma in CAM02-UCS reaches ~70; capping C
# means warm picks stay matte instead of going neon-red. A/B/C sit at "muted",
# D at "dusty" (most restrained), E at "okabe-honest" (slightly hotter to
# respect Okabe-Ito's native saturation).
PER_VARIANT_C_RANGE: dict[str, tuple[float, float]] = {
    # v0 strategies — kept so v1 can still call select_palette("balanced") if needed
    "analogous":      (24.0, 40.0),
    "triadic":        (26.0, 42.0),
    "split-comp":     (26.0, 42.0),
    "balanced":       (22.0, 36.0),
    "harmonic":       (22.0, 60.0),
    "okabe-anchored": (22.0, 42.0),
    # v1 strategies
    "d-tight-chroma": (24.0, 32.0),  # D1 — narrowest paper-ink corridor; cleanest co-existence prediction
    "d-expand-8":     (22.0, 36.0),  # D3 — same C as live D; an 8th slot is greedy-picked in the largest remaining hue gap
    "tetradic":       (24.0, 38.0),  # T  — slight C bump so the 4 forced anchors don't all land at the muted floor
    "warm-pole":      (22.0, 36.0),  # W  — same C as live D; the warm-bonus does the work
}


# Minimum pairwise hue spacing target per strategy (degrees on the colour wheel).
# Every strategy now enforces this via the diversity penalty inside
# ``score_candidates``; without it, max-min ΔE optimisation cheerfully picks
# two near-identical blues or two yellow-greens whenever the chroma corridor
# leaves headroom for only one warm/cool region.
PER_VARIANT_HUE_SPREAD: dict[str, float] = {
    # v0 strategies
    "analogous":      35.0,
    "triadic":        45.0,
    "split-comp":     45.0,
    "balanced":       50.0,  # 360/7 ≈ 51°, the ideal even spacing
    "harmonic":       50.0,
    "okabe-anchored": 45.0,
    # v1 strategies
    "d-tight-chroma": 50.0,  # same as live D — only chroma differs
    "d-expand-8":     50.0,  # same as live D; the 8th pick fills naturally where the wheel gap is biggest
    "tetradic":       50.0,
    "warm-pole":      50.0,  # warm bonus is additive at scoring; spacing target unchanged
}


# -----------------------------------------------------------------------------
# CAM02-UCS / LCh helpers
# -----------------------------------------------------------------------------


def jab_to_rgb1(jab: np.ndarray) -> np.ndarray:
    """Inverse of `to_jab`. Output may go out of gamut — caller clips/checks."""
    return cspace_convert(jab, "CAM02-UCS", "sRGB1")


def jab_batch_to_rgb1(jab_arr: np.ndarray) -> np.ndarray:
    return cspace_convert(jab_arr, "CAM02-UCS", "sRGB1")


def lch_to_jab(L: float, C: float, H_deg: float) -> np.ndarray:
    h = np.deg2rad(H_deg)
    return np.array([L, C * np.cos(h), C * np.sin(h)])


def jab_to_lch(jab: np.ndarray) -> tuple[float, float, float]:
    L, a, b = float(jab[0]), float(jab[1]), float(jab[2])
    C = float(np.hypot(a, b))
    H = float(np.rad2deg(np.arctan2(b, a))) % 360
    return L, C, H


def hue_in_band(hue: float, center: float, half_width: float) -> bool:
    """Circular hue containment, half_width in degrees."""
    d = abs((hue - center + 180) % 360 - 180)
    return d <= half_width


# -----------------------------------------------------------------------------
# Candidate grid — generated once per run, reused across all variants
# -----------------------------------------------------------------------------


@dataclass
class CandidatePool:
    """All candidate colours within the global paper-ink corridor, plus
    precomputed Jab coordinates under each of the 4 conditions. Per-variant
    chroma corridors are applied later as a candidate-mask."""

    rgb1: np.ndarray  # (N, 3) sRGB-1
    hues_deg: np.ndarray  # (N,) circular hue 0-360
    chromas: np.ndarray  # (N,) C in CAM02-UCS
    lightnesses: np.ndarray  # (N,) J' in CAM02-UCS
    jab_per_cond: dict[str, np.ndarray]  # cond → (N, 3)

    @classmethod
    def build(cls, log: logging.Logger) -> "CandidatePool":
        js = np.arange(J_MIN, J_MAX + 0.01, J_STEP)
        cs_ = np.arange(C_MIN, C_MAX + 0.01, C_STEP)
        hs = np.arange(0.0, 360.0, H_STEP_DEG)

        log.info("building candidate grid (J×C×H = %d×%d×%d) …", len(js), len(cs_), len(hs))

        rows = []
        for J in js:
            for C in cs_:
                for H in hs:
                    rows.append((J, C, H))
        grid = np.array(rows)  # (M, 3) where columns are J, C, H

        jab_arr = np.stack(
            [grid[:, 0], grid[:, 1] * np.cos(np.deg2rad(grid[:, 2])), grid[:, 1] * np.sin(np.deg2rad(grid[:, 2]))],
            axis=1,
        )
        rgb_arr = jab_batch_to_rgb1(jab_arr)

        # Strict gamut: tol=0.001. Looser tolerances let near-gamut Jab points
        # clip into oversaturated sRGB (a "muted red" Jab projects to a vivid
        # #F81118 once R clamps to 1.0), which silently breaks the paper-ink
        # intent of the chroma corridor.
        in_gamut = np.all((rgb_arr >= -0.001) & (rgb_arr <= 1.001), axis=1)
        rgb_arr = np.clip(rgb_arr[in_gamut], 0.0, 1.0)
        hues_arr = grid[in_gamut, 2]
        chromas_arr = grid[in_gamut, 1]
        lightnesses_arr = grid[in_gamut, 0]

        # Warm-hue mud filter: warm picks at low J' read as olive/brown, not
        # as the colour name they algorithmically represent. The floor is
        # sub-band specific because the mud zone shifts with hue: deep reds
        # (H ≈ 25-45) still look like reds down to J' ≈ 50, but yellows
        # (H ≈ 65-100) need J' ≥ 62 or they read as olive/khaki. The previous
        # uniform J' ≥ 58 over the full [30, 100] band killed too many useful
        # warm picks in analogous's narrow wedge.
        red_orange = (hues_arr >= 30.0) & (hues_arr < 65.0)
        yellow_lime = (hues_arr >= 65.0) & (hues_arr <= 100.0)
        red_ok = ~red_orange | (lightnesses_arr >= 52.0)
        yellow_ok = ~yellow_lime | (lightnesses_arr >= 62.0)
        no_mud = red_ok & yellow_ok
        rgb_arr = rgb_arr[no_mud]
        hues_arr = hues_arr[no_mud]
        chromas_arr = chromas_arr[no_mud]
        lightnesses_arr = lightnesses_arr[no_mud]

        log.info("kept %d / %d in-gamut, non-muddy candidates", rgb_arr.shape[0], grid.shape[0])

        jab_per_cond: dict[str, np.ndarray] = {}
        for cond in CVD_ORDER:
            sim = simulate_cvd(rgb_arr, cond)
            jab_per_cond[cond] = to_jab(sim)

        return cls(
            rgb1=rgb_arr,
            hues_deg=hues_arr,
            chromas=chromas_arr,
            lightnesses=lightnesses_arr,
            jab_per_cond=jab_per_cond,
        )


# -----------------------------------------------------------------------------
# Greedy selection
# -----------------------------------------------------------------------------


def selected_jabs(selected_rgb: list[np.ndarray]) -> dict[str, np.ndarray]:
    """Pre-compute Jab for the already-selected colours under each condition.
    K is small (≤7) so this is cheap and called every pick."""
    arr = np.array(selected_rgb)
    out: dict[str, np.ndarray] = {}
    for cond in CVD_ORDER:
        out[cond] = to_jab(simulate_cvd(arr, cond))
    return out


def score_candidates(
    pool: CandidatePool, sel_jabs: dict[str, np.ndarray]
) -> np.ndarray:
    """For every candidate, return the min ΔE to any selected colour, taken
    across the 4 conditions. Higher is better (more distinct)."""
    n_cand = pool.rgb1.shape[0]
    best = np.full(n_cand, np.inf)
    for cond in CVD_ORDER:
        # pool.jab_per_cond[cond] is (N, 3); sel_jabs[cond] is (K, 3)
        diff = pool.jab_per_cond[cond][:, None, :] - sel_jabs[cond][None, :, :]
        dist = np.linalg.norm(diff, axis=2)  # (N, K)
        min_per_cand = dist.min(axis=1)
        best = np.minimum(best, min_per_cand)
    return best


def hue_diversity_penalty(
    pool: CandidatePool, sel_hues: list[float], target_spread_deg: float
) -> np.ndarray:
    """Penalty subtracted from the ΔE score: grows as the candidate hue gets
    closer than ``target_spread_deg`` to any already-selected hue. Without
    this, greedy max-min lands on three nearly-identical purples for the
    balanced strategy because the warm/purple corner of CAM02-UCS is where
    "farthest from green" lives for several conditions at once. Weight 1.2 is
    a tiebreaker — the hard min-hue-gap mask in ``select_palette`` does the
    actual no-clash enforcement; this penalty just prefers maximally-spread
    picks among equally-distinct ones.
    """
    if not sel_hues:
        return np.zeros(pool.rgb1.shape[0])
    sel = np.array(sel_hues)
    diff = pool.hues_deg[:, None] - sel[None, :]
    circ = np.abs(((diff + 180) % 360) - 180)
    min_hue_dist = circ.min(axis=1)
    return np.maximum(0.0, target_spread_deg - min_hue_dist) * 1.2


def hue_gap_mask(
    pool: CandidatePool, sel_hues: list[float], min_gap_deg: float
) -> np.ndarray:
    """Hard mask: True for candidates ≥ min_gap_deg away from every selected
    hue on the colour wheel. This is the no-clash guarantee — band fallback
    can drop the per-position bands, but the gap mask still keeps every pick
    distinguishable from its siblings."""
    if not sel_hues:
        return np.ones(pool.rgb1.shape[0], dtype=bool)
    sel = np.array(sel_hues)
    diff = pool.hues_deg[:, None] - sel[None, :]
    circ = np.abs(((diff + 180) % 360) - 180)
    return circ.min(axis=1) >= min_gap_deg


def select_palette(
    strategy: str,
    pool: CandidatePool,
    n_hues: int = 7,
    extra_seeds: tuple[str, ...] = (),
    forbidden_hue_bands: tuple[tuple[float, float], ...] = (),
    warm_bonus: tuple[float, float, float] | None = None,
) -> list[str]:
    """Pick 7 hues for a variant. Greedy max-min ΔE selection under all 4
    CVD conditions, with per-position hue bands and the per-variant chroma
    corridor as candidate masks. If no candidate matches the strictest band,
    the band half-width is widened in 10° steps until something fits.

    ``extra_seeds`` are pinned hex strings that follow brand-green in the
    output. Used by okabe-anchored to keep #D55E00 (vermillion) in the
    palette regardless of where greedy max-min would put it.

    v1 additions:
    - ``forbidden_hue_bands``: a list of (center_deg, half_width_deg) bands
      to EXCLUDE from every position globally. Used by D3 (d-swap-tan) to
      ban the tan band [50°, 90°] so a different 7th hue gets picked.
    - ``warm_bonus``: (center_deg, half_width_deg, weight) — a soft additive
      score bonus for candidates whose hue is within (half-width) of the
      center. Used by W (warm-pole) to bias picks toward 30°–80°.
    """

    brand_rgb = hex_to_rgb1(OK_GREEN)
    _, _, brand_H = jab_to_lch(to_jab(brand_rgb.reshape(1, 3))[0])

    bands_per_pos = _strategy_bands(strategy, brand_H, n_hues)
    c_min, c_max = PER_VARIANT_C_RANGE[strategy]
    chroma_mask = (pool.chromas >= c_min) & (pool.chromas <= c_max)

    # Global hue-exclusion mask (v1 — D3 swap-tan uses this).
    if forbidden_hue_bands:
        forbidden = np.zeros_like(pool.hues_deg, dtype=bool)
        for fc, fhw in forbidden_hue_bands:
            d = np.abs((pool.hues_deg - fc + 180) % 360 - 180)
            forbidden |= d <= fhw
        chroma_mask = chroma_mask & ~forbidden

    # Warm-pole bonus: additive at scoring time. Computed once because hues
    # don't change between picks.
    if warm_bonus is not None:
        wc, whw, ww = warm_bonus
        d_warm = np.abs((pool.hues_deg - wc + 180) % 360 - 180)
        warm_score_bonus = ww * np.maximum(0.0, 1.0 - d_warm / whw)
    else:
        warm_score_bonus = None

    # The hue-diversity penalty is a soft tiebreaker; the hard guarantee that
    # no two picks land within ``min_gap`` of each other on the colour wheel
    # comes from ``hue_gap_mask``. Set to 60% of the target spread — tight
    # enough to forbid the old two-azures / two-blues clashes, loose enough to
    # keep the candidate set non-empty even in cramped variants.
    diversity_target_deg = PER_VARIANT_HUE_SPREAD[strategy]
    min_gap_deg = diversity_target_deg * 0.6

    selected_rgb: list[np.ndarray] = [brand_rgb]
    selected_hues: list[float] = [brand_H]
    for seed_hex in extra_seeds:
        seed_rgb = hex_to_rgb1(seed_hex)
        _, _, seed_H = jab_to_lch(to_jab(seed_rgb.reshape(1, 3))[0])
        selected_rgb.append(seed_rgb)
        selected_hues.append(seed_H)
    start = len(selected_rgb)
    for i in range(start, n_hues):
        sel_jabs = selected_jabs(selected_rgb)
        scores = score_candidates(pool, sel_jabs)
        scores = scores - hue_diversity_penalty(pool, selected_hues, diversity_target_deg)
        if warm_score_bonus is not None:
            scores = scores + warm_score_bonus

        gap_mask = hue_gap_mask(pool, selected_hues, min_gap_deg)
        bands = bands_per_pos[i]
        mask = _bands_mask(pool.hues_deg, bands) & chroma_mask & gap_mask
        # Widen the per-position hue band first (cheap), then loosen the chroma
        # corridor, then finally drop the per-position band — but the gap mask
        # is never relaxed: a near-clash is worse than an off-corridor pick.
        widen = 0
        while not mask.any() and widen < 60:
            widen += 10
            widened = [(c, w + widen) for (c, w) in bands] if bands else None
            mask = _bands_mask(pool.hues_deg, widened) & chroma_mask & gap_mask
        if not mask.any():
            mask = chroma_mask & gap_mask  # drop hue rule, keep gap
        if not mask.any():
            mask = gap_mask  # last-resort: drop chroma too, keep gap

        masked_scores = np.where(mask, scores, -np.inf)
        best_idx = int(np.argmax(masked_scores))
        selected_rgb.append(pool.rgb1[best_idx])
        selected_hues.append(float(pool.hues_deg[best_idx]))

    return [rgb1_to_hex(rgb) for rgb in selected_rgb]


def _bands_mask(hues: np.ndarray, bands: list[tuple[float, float]] | None) -> np.ndarray:
    """Union of (center, half_width) hue bands. None = no constraint."""
    if bands is None:
        return np.ones_like(hues, dtype=bool)
    mask = np.zeros_like(hues, dtype=bool)
    for center, hw in bands:
        d = np.abs((hues - center + 180) % 360 - 180)
        mask |= d <= hw
    return mask


def _strategy_bands(
    strategy: str, brand_hue: float, n_hues: int
) -> list[list[tuple[float, float]] | None]:
    """Return a list of length n_hues; entry i is the acceptable hue bands
    for position i. Each entry is a list of (center_deg, half_width_deg)
    tuples, or None to mean "no hue constraint".

    For strategies with a fixed hue identity (triadic / split-comp / analogous),
    every position has a unique hue target so the palette can't accidentally
    end up with three purples; positions 0-2 carry the scheme's primary
    anchors and 3-6 fill the gaps between them.
    """
    # Default band half-width. Tighter for triadic/split-comp (12°) where the
    # primary anchors differ by only 30° between the two strategies — wider
    # bands would overlap and let both strategies converge on the same hue
    # picks. Analogous keeps 22° because its strategy is intrinsically "stay
    # near brand", not "hit a specific anchor".
    bw = 22

    if strategy == "analogous":
        # ±90° around brand, spread the 7 picks across the band rather than
        # letting greedy max-min cluster them at the band edges.
        targets = [
            brand_hue,
            (brand_hue + 30) % 360,
            (brand_hue - 30) % 360,
            (brand_hue + 60) % 360,
            (brand_hue - 60) % 360,
            (brand_hue + 90) % 360,
            (brand_hue - 90) % 360,
        ]
        return [[(t, bw)] for t in targets][:n_hues]

    if strategy == "triadic":
        # 3 primary anchors at positions 0-2 + 3 midpoints at 3-5 (filling the
        # gaps between primaries). Position 6 is left unconstrained so the
        # algorithm picks the biggest remaining hue gap under the ≥60% diversity
        # mask — the old hardcoded brand+30° filler landed at H=196° (cyan)
        # which was only 29° from brand-green and 35° from the brand+60° azure.
        # Very tight 4° bands at primaries (positions 1-2) so the algorithm
        # cannot drift to ≈305° where split-comp and balanced both land — at
        # H_STEP=5° this snaps to ±1 grid hue. Filler bands stay at 12°.
        targets = [
            brand_hue,
            (brand_hue + 120) % 360,
            (brand_hue + 240) % 360,
            (brand_hue + 60) % 360,
            (brand_hue + 180) % 360,
            (brand_hue + 300) % 360,
        ]
        widths = [12, 4, 4, 12, 12, 12]
        bands: list[list[tuple[float, float]] | None] = [
            [(t, w)] for t, w in zip(targets, widths)
        ]
        bands.append(None)  # position 6: free pick
        return bands[:n_hues]

    if strategy == "split-comp":
        # brand + two split anchors (±150°/210°) at positions 0-2; positions
        # 3-5 fill three of the four non-anchor quadrants. Position 6 is
        # left free for the algorithm to fill the largest remaining hue gap
        # (otherwise the hardcoded brand+300° would land at H=106° = lime,
        # close to brand-green). Very tight 4° bands at primaries to keep
        # them clearly magenta + red rather than the purple+orange-red that
        # triadic and balanced also converge on.
        targets = [
            brand_hue,
            (brand_hue + 150) % 360,
            (brand_hue + 210) % 360,
            (brand_hue + 90) % 360,
            (brand_hue + 270) % 360,
            (brand_hue + 60) % 360,
        ]
        widths = [12, 4, 4, 12, 12, 12]
        bands: list[list[tuple[float, float]] | None] = [
            [(t, w)] for t, w in zip(targets, widths)
        ]
        bands.append(None)  # position 6: free pick
        return bands[:n_hues]

    if strategy == "balanced":
        # No hue rule at any position; the hue-diversity penalty at score time
        # is doing all the work. Most "harmonic but max-distinct" results.
        return [None for _ in range(n_hues)]

    if strategy == "harmonic":
        # Same as balanced (no hue rule) but with a relaxed C corridor — tests
        # whether more chroma headroom yields more pleasing hue choices.
        return [None for _ in range(n_hues)]

    if strategy == "okabe-anchored":
        # Brand-green (pos 0) and vermillion (pos 1) are pinned via
        # extra_seeds; positions 2-6 fill freely under chroma + gap masks.
        return [None for _ in range(n_hues)]

    if strategy in ("d-expand-8", "warm-pole"):
        # v1 D-family expand-8 + warm-pole: no per-position hue rule. The
        # strategy signature lives in PER_VARIANT_C_RANGE / PER_VARIANT_HUE_SPREAD
        # or in select_palette's extra_seeds / warm_bonus knobs.
        return [None for _ in range(n_hues)]

    if strategy == "d-tight-chroma":
        # D1 — pin position 1 to the pure-red band [15°, 35°] so the palette
        # gets a true red inside the tight chroma corridor (C ∈ [24, 32]) —
        # no hard #B71D27 seed needed. Band kept narrow (±10°) so max-min ΔE
        # doesn't drift to the orange edge (which happened at ±20°).
        bands: list[list[tuple[float, float]] | None] = [None, [(25.0, 10.0)]]
        bands.extend([None] * (n_hues - 2))
        return bands[:n_hues]

    if strategy == "tetradic":
        # T — 4 hue anchors 90° apart starting at brand-green, then 3
        # mid-quadrant fillers at +45° offsets. Forces explicit
        # opposite-axis coverage that balanced max-min sometimes skips.
        targets = [
            brand_hue,
            (brand_hue + 90) % 360,
            (brand_hue + 180) % 360,
            (brand_hue + 270) % 360,
            (brand_hue + 45) % 360,
            (brand_hue + 135) % 360,
            (brand_hue + 225) % 360,
        ]
        widths = [12, 8, 8, 8, 16, 16, 16]
        bands: list[list[tuple[float, float]] | None] = [
            [(t, w)] for t, w in zip(targets, widths)
        ]
        return bands[:n_hues]

    raise ValueError(f"unknown strategy: {strategy}")


# -----------------------------------------------------------------------------
# Reorder so the first 4 are the "most beautiful" subset
# -----------------------------------------------------------------------------


def reorder_first_4(
    hexes: list[str], pinned: tuple[int, ...] = ()
) -> list[str]:
    """Position 0 (brand green) stays. ``pinned`` positions (e.g. (1, 2) for
    triadic/split-comp where pos 1-2 are the strategy primaries) also stay
    in their slots; the function only searches the remaining indices for the
    best 4th member. Otherwise: among {1..6}, find the 3-tuple whose
    inclusion in the first-4 maximises the min worst-CVD ΔE inside that
    4-set, subject to a ≥60° pairwise hue-gap constraint (degrades 5° at a
    time if the pool can't satisfy it). Positions 5–7 follow in order of
    decreasing min-distance-to-the-first-4."""
    n = len(hexes)
    assert n >= 7  # v1 allows 8-color palettes (D3 expand-8) — first-4 logic stays the same

    rgb_all = np.array([hex_to_rgb1(hx) for hx in hexes])
    M_worst, _ = worst_cvd_pairwise_delta_e(rgb_all)
    hues_all = np.array(
        [jab_to_lch(to_jab(rgb_all[i:i + 1])[0])[2] for i in range(n)]
    )

    def triple_meets_hue_gap(triple: tuple[int, ...], gap_deg: float) -> bool:
        sub = (0, *triple)
        sub_hues = hues_all[list(sub)]
        diff = sub_hues[:, None] - sub_hues[None, :]
        circ = np.abs(((diff + 180) % 360) - 180)
        np.fill_diagonal(circ, 360.0)
        return bool(circ.min() >= gap_deg)

    # Strategy-anchor preservation: the pinned indices stay; we only search
    # the non-pinned-non-zero positions for the 4th slot. The triple length
    # is still 3 (pinned + 4th slot fillers as needed).
    pinned_set = set(pinned)
    search_pool = [i for i in range(1, n) if i not in pinned_set]
    fill_count = 3 - len(pinned)
    if fill_count < 0:
        raise ValueError(f"too many pinned positions: {pinned}")

    # Try 60° first; if the 7-hue pool can't satisfy that (analogous wedge
    # geometry, mostly), step down in 5° increments. Below 30° we'd be back
    # to the no-clash threshold from select_palette — no improvement.
    best_triple: tuple[int, ...] | None = None
    best_score = -1.0
    for gap in (60.0, 55.0, 50.0, 45.0, 40.0, 35.0, 30.0):
        for extras in itertools.combinations(search_pool, fill_count):
            triple = tuple(pinned) + extras
            if not triple_meets_hue_gap(triple, gap):
                continue
            sub = (0, *triple)
            sub_M = M_worst[np.ix_(sub, sub)]
            triu = np.triu_indices(len(sub), k=1)
            score = float(sub_M[triu].min())
            if score > best_score:
                best_score = score
                best_triple = triple
        if best_triple is not None:
            break

    assert best_triple is not None
    chosen = [0, *best_triple]
    rest = [i for i in range(1, n) if i not in best_triple]

    # Sort remainder by min worst-CVD ΔE to the chosen first-4 (descending)
    rest_scores: list[tuple[float, int]] = []
    for i in rest:
        col = M_worst[i, chosen]
        rest_scores.append((float(col.min()), i))
    rest_scores.sort(reverse=True)

    final_order = chosen + [i for _, i in rest_scores]
    return [hexes[i] for i in final_order]


def measure_first_4(hexes: list[str]) -> float:
    rgb = np.array([hex_to_rgb1(hx) for hx in hexes[:4]])
    M_worst, _ = worst_cvd_pairwise_delta_e(rgb)
    triu = np.triu_indices(4, k=1)
    return float(M_worst[triu].min())


def measure_all_normal_min(hexes: list[str]) -> float:
    rgb = np.array([hex_to_rgb1(hx) for hx in hexes])
    M = pairwise_delta_e(rgb, "normal")
    triu = np.triu_indices(len(hexes), k=1)
    return float(M[triu].min())


# -----------------------------------------------------------------------------
# Naming colours by hue band
# -----------------------------------------------------------------------------


HUE_BANDS = [
    (15, "red"), (35, "orange"), (55, "amber"), (70, "yellow"),
    (95, "lime"), (135, "green"), (165, "teal"), (200, "cyan"),
    (235, "azure"), (255, "blue"), (285, "indigo"), (315, "purple"),
    (345, "magenta"), (360, "pink"),
]


def hue_to_name(hex_str: str) -> str:
    jab = to_jab(hex_to_rgb1(hex_str).reshape(1, 3))[0]
    _, _, h = jab_to_lch(jab)
    for boundary, name in HUE_BANDS:
        if h < boundary:
            return name
    return HUE_BANDS[-1][1]


def names_for_palette(hexes: list[str]) -> list[str]:
    return [hue_to_name(hx) for hx in hexes]


# -----------------------------------------------------------------------------
# Continuous colormap construction (perceptually uniform in CAM02-UCS)
# -----------------------------------------------------------------------------


def _interp_two(start: np.ndarray, end: np.ndarray, n: int) -> np.ndarray:
    ts = np.linspace(0, 1, n).reshape(-1, 1)
    jabs = (1 - ts) * start + ts * end
    return np.clip(jab_batch_to_rgb1(jabs), 0, 1)


def _interp_three(start: np.ndarray, mid: np.ndarray, end: np.ndarray, n: int) -> np.ndarray:
    half = n // 2
    a = _interp_two(start, mid, half)
    b = _interp_two(mid, end, n - half)
    return np.vstack([a, b])


def _find_closest_hue(palette: list[str], target_h: float) -> tuple[str, float]:
    """Return (hex, hue) of the palette member with hue closest to ``target_h``
    on the colour wheel."""
    best_hex, best_h, best_d = palette[0], 0.0, 360.0
    for hx in palette:
        _, _, h = jab_to_lch(to_jab(hex_to_rgb1(hx).reshape(1, 3))[0])
        d = abs(((h - target_h + 180) % 360) - 180)
        if d < best_d:
            best_d, best_hex, best_h = d, hx, h
    return best_hex, best_h


def build_sequential_cmap(palette: list[str], n: int = 256) -> tuple[np.ndarray, str]:
    """Sequential colormap: brand-green → dark version of the palette member
    whose hue sits closest to 240° (blue territory). Hue is palette-derived
    so the cmap shares identity with the categorical; J' and C are tuned
    for monotonic lightness descent (J' 59 → 22) and good chroma headroom
    (C 35) regardless of where the source palette member sits in J/C space."""
    brand_jab = to_jab(hex_to_rgb1(OK_GREEN).reshape(1, 3))[0]
    cool_hex, cool_h = _find_closest_hue(palette[1:], 240.0)
    end = lch_to_jab(22.0, 35.0, cool_h)
    cmap = _interp_two(brand_jab, end, n)
    label = f"green → dark {hue_to_name(cool_hex)}"
    return cmap, label


def build_diverging_cmap(palette: list[str], n: int = 256) -> tuple[np.ndarray, str]:
    """Diverging colormap: warmest palette member ↔ near-neutral ↔ coolest
    palette member. Both poles normalised to J'=45 C=38 for symmetric
    visual weight. Mid-grey uses the average of the two hues so the
    transition reads as continuous rather than two cmaps stitched."""
    warm_hex, warm_h = _find_closest_hue(palette[1:], 30.0)
    cool_hex, cool_h = _find_closest_hue(palette[1:], 240.0)
    warm_jab = lch_to_jab(45.0, 38.0, warm_h)
    cool_jab = lch_to_jab(45.0, 38.0, cool_h)
    mid = lch_to_jab(70.0, 5.0, (warm_h + cool_h) / 2.0)
    cmap = _interp_three(warm_jab, mid, cool_jab, n)
    label = f"{hue_to_name(warm_hex)} ↔ {hue_to_name(cool_hex)} diverging"
    return cmap, label


# -----------------------------------------------------------------------------
# CAM02-UCS color wheel renderer (v1)
# -----------------------------------------------------------------------------
#
# Adobe-Color / Dracula-Pro style: a continuous hue ring rendered at fixed
# (L=60, C=40), with each palette colour placed at its actual (C, H)
# coordinates. The ring shows the colour-space "neighbourhood" each pick
# lives in; the dots show how the picks geometrically relate to each other.
#
# Two modes:
#   - "small" (≈180 px): hue ring + dots only. Slots into index cards.
#   - "large" (≈520 px): hue ring + chroma-corridor rings (toggleable) +
#                        dots + labels + optional overlay of live D dots.


WHEEL_BG_L = 60.0
WHEEL_BG_C = 40.0
# Use 5° slices = 72 segments. Smooth enough visually, ~30× lighter SVG than
# 1° slices and the slice boundaries are invisible at typical view distance.
WHEEL_SLICE_DEG = 5.0


def _polar_xy(cx: float, cy: float, r: float, theta_deg: float) -> tuple[float, float]:
    """Convert polar (r, θ°) into SVG cartesian coords. θ=0 points right
    (east); θ grows counter-clockwise like a math wheel. SVG y is inverted
    so we negate the sin term."""
    t = np.deg2rad(theta_deg)
    return cx + r * float(np.cos(t)), cy - r * float(np.sin(t))


def _arc_slice_path(cx: float, cy: float, r_in: float, r_out: float, a0: float, a1: float) -> str:
    """SVG path for a single annular slice from angle a0 to a1 (degrees)."""
    x0o, y0o = _polar_xy(cx, cy, r_out, a0)
    x1o, y1o = _polar_xy(cx, cy, r_out, a1)
    x0i, y0i = _polar_xy(cx, cy, r_in, a0)
    x1i, y1i = _polar_xy(cx, cy, r_in, a1)
    large_arc = 1 if (a1 - a0) % 360 > 180 else 0
    return (
        f"M{x0o:.2f} {y0o:.2f} "
        f"A{r_out:.2f} {r_out:.2f} 0 {large_arc} 0 {x1o:.2f} {y1o:.2f} "
        f"L{x1i:.2f} {y1i:.2f} "
        f"A{r_in:.2f} {r_in:.2f} 0 {large_arc} 1 {x0i:.2f} {y0i:.2f} "
        f"Z"
    )



def _pie_slice_path(cx: float, cy: float, r_out: float, a0: float, a1: float) -> str:
    """SVG path for a pie slice from centre to angle a0..a1 (degrees).
    Used to draw the filled hue disk — Adobe-Color / Dracula-Pro style — where
    the perceived chroma fade toward the centre is applied by a separate
    radial-gradient overlay rather than per-slice gradients."""
    x0, y0 = _polar_xy(cx, cy, r_out, a0)
    x1, y1 = _polar_xy(cx, cy, r_out, a1)
    large_arc = 1 if (a1 - a0) % 360 > 180 else 0
    return (
        f"M{cx:.2f} {cy:.2f} "
        f"L{x0:.2f} {y0:.2f} "
        f"A{r_out:.2f} {r_out:.2f} 0 {large_arc} 0 {x1:.2f} {y1:.2f} "
        f"Z"
    )


_WHEEL_PNG_CACHE: dict[int, str] = {}


def _wheel_png_b64(disk_size: int) -> str:
    """Render the CAM02-UCS colour disk as a base64 PNG, cached by size.

    Every pixel at radius r and angle θ is coloured (L=60, C=40·r/r_max, H=θ)
    — perceptually honest chroma fade across the whole disk. Pixel-rendered so
    there are no slice seams, no per-position hue jumps, no SVG gradient defs.
    Compared to the 72-slice SVG version: smoother, smaller defs, but a slightly
    larger embedded image (~12 kB for 164 px disks, ~80 kB for 476 px).
    """
    import base64
    import io
    from PIL import Image

    if disk_size in _WHEEL_PNG_CACHE:
        return _WHEEL_PNG_CACHE[disk_size]

    arr = np.zeros((disk_size, disk_size, 4), dtype=np.uint8)
    cx_pix = cy_pix = disk_size / 2.0
    r_out = disk_size / 2.0

    yy, xx = np.mgrid[0:disk_size, 0:disk_size]
    dx = xx + 0.5 - cx_pix
    dy = cy_pix - (yy + 0.5)
    r = np.hypot(dx, dy)
    theta = np.degrees(np.arctan2(dy, dx)) % 360.0

    inside = r <= r_out
    in_idx = np.where(inside)
    n_in = len(in_idx[0])
    L = np.full(n_in, WHEEL_BG_L)
    C = (r[in_idx] / r_out) * WHEEL_BG_C
    H = theta[in_idx]
    H_rad = np.deg2rad(H)
    jab_arr = np.stack([L, C * np.cos(H_rad), C * np.sin(H_rad)], axis=1)
    rgb_arr = jab_batch_to_rgb1(jab_arr)
    rgb_arr = np.clip(rgb_arr, 0.0, 1.0)
    rgb_u8 = (rgb_arr * 255).astype(np.uint8)

    arr[in_idx[0], in_idx[1], 0:3] = rgb_u8
    arr[in_idx[0], in_idx[1], 3] = 255

    img = Image.fromarray(arr, mode="RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    data_url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    _WHEEL_PNG_CACHE[disk_size] = data_url
    return data_url


def _wheel_hue_ring_paths(cx: float, cy: float, r_in: float, r_out: float) -> str:
    """Pre-rendered 72 annular slices coloured by (L=60, C=40, H) sweep."""
    parts: list[str] = []
    n = int(round(360.0 / WHEEL_SLICE_DEG))
    for k in range(n):
        a0 = k * WHEEL_SLICE_DEG
        a1 = (k + 1) * WHEEL_SLICE_DEG
        h_mid = (a0 + a1) / 2.0
        rgb = jab_to_rgb1(lch_to_jab(WHEEL_BG_L, WHEEL_BG_C, h_mid))
        rgb_clipped = np.clip(rgb, 0.0, 1.0)
        hex_str = rgb1_to_hex(rgb_clipped)
        d = _arc_slice_path(cx, cy, r_in, r_out, a0, a1)
        parts.append(f'<path d="{d}" fill="{hex_str}" stroke="none"/>')
    return "\n".join(parts)


def _chroma_corridor_rings(cx: float, cy: float, r_max_wheel: float, c_max_wheel: float,
                           c_lo: float, c_hi: float, klass: str) -> str:
    """Two faint circles marking the per-variant chroma corridor."""
    r_lo = (c_lo / c_max_wheel) * r_max_wheel
    r_hi = (c_hi / c_max_wheel) * r_max_wheel
    return (
        f'<g class="{klass}">'
        f'<circle cx="{cx}" cy="{cy}" r="{r_lo:.2f}" fill="none" stroke="currentColor" '
        f'stroke-width="0.7" stroke-dasharray="3 3" opacity="0.55"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r_hi:.2f}" fill="none" stroke="currentColor" '
        f'stroke-width="0.7" stroke-dasharray="3 3" opacity="0.55"/>'
        f'</g>'
    )


def _palette_dots(cx: float, cy: float, r_max_wheel: float, c_max_wheel: float,
                  hexes: list[str], dot_r: float, show_labels: bool,
                  show_brand_star: bool, klass: str) -> str:
    """Place each hex at its (C, H) coords on the wheel."""
    parts: list[str] = []
    for i, hx in enumerate(hexes):
        rgb = hex_to_rgb1(hx).reshape(1, 3)
        jab = to_jab(rgb)[0]
        _, C_val, H_val = jab_to_lch(jab)
        # Clamp the radius so dots from off-corridor hexes stay inside the wheel.
        r = min(C_val / c_max_wheel, 1.0) * r_max_wheel
        x, y = _polar_xy(cx, cy, r, H_val)
        if show_brand_star and i == 0:
            # 5-point star marker for brand anchor
            star_pts = []
            for k in range(10):
                ang = 90 + k * 36
                rr = dot_r * (1.7 if k % 2 == 0 else 0.75)
                sx, sy = _polar_xy(x, y, rr, ang)
                star_pts.append(f"{sx:.2f},{sy:.2f}")
            parts.append(
                f'<polygon points="{" ".join(star_pts)}" fill="{hx}" '
                f'stroke="var(--ink)" stroke-width="0.8" opacity="0.98">'
                f'<title>{i + 1}·{hx.upper()} (brand anchor)</title>'
                f'</polygon>'
            )
        else:
            parts.append(
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{dot_r:.2f}" '
                f'fill="{hx}" stroke="var(--bg-elevated)" stroke-width="1.4">'
                f'<title>{i + 1}·{hx.upper()}</title>'
                f'</circle>'
            )
        if show_labels:
            # Hex label outside the wheel along the same angle as the dot.
            # Position number is implicit from the dot order (matches the
            # swatch table above the wheel section).
            lx, ly = _polar_xy(cx, cy, r_max_wheel + 14, H_val)
            anchor = "middle"
            if lx > cx + 4:
                anchor = "start"
            elif lx < cx - 4:
                anchor = "end"
            parts.append(
                f'<text x="{lx:.2f}" y="{ly:.2f}" text-anchor="{anchor}" '
                f'dominant-baseline="middle" fill="var(--ink-soft)" '
                f'font-family="var(--mono)" font-size="10">{hx.upper()}</text>'
            )
    return f'<g class="{klass}">{"".join(parts)}</g>'


def render_color_wheel(
    hexes: list[str],
    *,
    size_px: int,
    mode: str,  # "small" | "large"
    chroma_corridor: tuple[float, float] | None = None,
    overlay_hexes: list[str] | None = None,
    dom_id: str | None = None,
) -> str:
    """Render an SVG color wheel placing every hex at its actual (C, H) coords.

    The disk itself is a pre-rendered CAM02-UCS PNG embedded as a base64 data
    URL — pixel-correct chroma fade from neutral grey at the centre to L=60,
    C=40 at the rim, with no slice seams. Dots, corridor rings, labels and
    the overlay live on top as SVG.

    "small" mode: disk + dots only. No labels, no corridor, no overlay.
    "large" mode: disk + dots + labels + optional chroma-corridor rings +
                  optional overlay dots (e.g. live D dots as outlined circles).
                  Includes inline JS toggles for the corridor and overlay.
    """
    cx = cy = size_px / 2.0
    pad = 22 if mode == "large" else 8
    r_out = (size_px / 2.0) - pad
    c_max_wheel = 60.0
    r_max_for_dots = r_out

    wheel_id = dom_id or f"wheel-{abs(hash(tuple(hexes))) & 0xFFFFFF:06x}"

    # Disk = embedded PNG; render at a tight pixel size matching r_out so the
    # rendered pixels = on-screen pixels at typical view sizes. The PNG cache
    # keeps a single image per disk_size across the whole HTML output.
    disk_size = int(round(2 * r_out))
    wheel_png = _wheel_png_b64(disk_size)
    disk = (
        f'<image href="{wheel_png}" x="{pad}" y="{pad}" '
        f'width="{disk_size}" height="{disk_size}" image-rendering="optimizeQuality"/>'
    )
    dot_r = 7.5 if mode == "large" else 4.5

    corridor = ""
    if chroma_corridor is not None and mode == "large":
        c_lo, c_hi = chroma_corridor
        corridor = _chroma_corridor_rings(cx, cy, r_max_for_dots, c_max_wheel,
                                          c_lo, c_hi, klass="wheel-corridor")

    # Cardinal-angle text labels only (no radial tick lines — they visually
    # carved the disk into segments without adding information).
    ticks = ""
    if mode == "large":
        tick_parts: list[str] = []
        for h_deg in (0, 90, 180, 270):
            tx, ty = _polar_xy(cx, cy, r_out + 32, h_deg)
            tick_parts.append(
                f'<text x="{tx:.2f}" y="{ty:.2f}" text-anchor="middle" '
                f'dominant-baseline="middle" fill="var(--ink-muted)" '
                f'font-family="var(--mono)" font-size="9" opacity="0.6">{h_deg}°</text>'
            )
        ticks = "".join(tick_parts)

    dots = _palette_dots(cx, cy, r_max_for_dots, c_max_wheel, hexes, dot_r,
                         show_labels=(mode == "large"),
                         show_brand_star=True, klass="wheel-dots")

    overlay = ""
    if overlay_hexes is not None and mode == "large":
        overlay_parts: list[str] = []
        for i, hx in enumerate(overlay_hexes):
            rgb = hex_to_rgb1(hx).reshape(1, 3)
            jab = to_jab(rgb)[0]
            _, C_val, H_val = jab_to_lch(jab)
            r = min(C_val / c_max_wheel, 1.0) * r_max_for_dots
            x, y = _polar_xy(cx, cy, r, H_val)
            # Each overlay marker = thick coloured ring with a high-contrast
            # ink-coloured halo behind it (so it stays visible no matter which
            # part of the disk it lands on).
            outer_r = dot_r + 8
            overlay_parts.append(
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{outer_r:.2f}" '
                f'fill="none" stroke="var(--ink)" stroke-width="4" opacity="0.5"/>'
            )
            overlay_parts.append(
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{outer_r:.2f}" '
                f'fill="none" stroke="{hx}" stroke-width="2.5" opacity="1"/>'
            )
        overlay = f'<g class="wheel-overlay" style="display:none">{"".join(overlay_parts)}</g>'

    # overflow="visible" so the hex labels can extend past the SVG viewBox
    # without getting clipped — they sit ≈14px outside r_out on each side.
    wheel_svg = (
        f'<svg viewBox="0 0 {size_px} {size_px}" width="{size_px}" height="{size_px}" '
        f'class="color-wheel color-wheel-{mode}" id="{wheel_id}" overflow="visible" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'{disk}{ticks}{corridor}{overlay}{dots}'
        f'</svg>'
    )

    if mode != "large":
        return wheel_svg

    toggles = []
    if chroma_corridor is not None:
        toggles.append(
            f'<label><input type="checkbox" data-wheel-toggle="corridor" data-wheel="{wheel_id}" checked> show chroma corridor</label>'
        )
    if overlay_hexes is not None:
        toggles.append(
            f'<label><input type="checkbox" data-wheel-toggle="overlay" data-wheel="{wheel_id}"> overlay live D</label>'
        )
    toggles_html = ""
    if toggles:
        toggles_html = f'<div class="wheel-toggles">{" ".join(toggles)}</div>'

    return f'<div class="wheel-frame">{wheel_svg}{toggles_html}</div>'


WHEEL_CSS = """
.wheel-frame {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
}
.color-wheel { display: block; }
.color-wheel-large { max-width: 100%; height: auto; }
.color-wheel text { user-select: none; pointer-events: none; }
.wheel-toggles {
    display: flex;
    gap: 14px;
    flex-wrap: wrap;
    font-size: 11px;
    color: var(--ink-soft);
}
.wheel-toggles label {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    cursor: pointer;
}
.wheel-toggles input { accent-color: var(--ok-green); }
"""


WHEEL_JS = """
document.querySelectorAll('[data-wheel-toggle]').forEach(function (cb) {
    cb.addEventListener('change', function () {
        var kind = cb.getAttribute('data-wheel-toggle');
        var wheelId = cb.getAttribute('data-wheel');
        var wheel = document.getElementById(wheelId);
        if (!wheel) return;
        var cls = kind === 'corridor' ? 'wheel-corridor' : 'wheel-overlay';
        var target = wheel.querySelector('.' + cls);
        if (!target) return;
        target.style.display = cb.checked ? '' : 'none';
    });
});
"""


# -----------------------------------------------------------------------------
# Variant definitions
# -----------------------------------------------------------------------------


@dataclass
class Variant:
    key: str  # "A".."E", "D1"..  etc.
    slug: str  # filename-safe
    title: str  # short name
    strategy: str  # algorithm identifier
    one_liner: str  # human description shown on each page + index
    n_hues: int = 7  # override for non-standard palette length (e.g. D3 = 8)


VARIANTS = [
    Variant(
        "D1", "tight-chroma", "d-tight-chroma",
        "d-tight-chroma",
        "live D's max-min ΔE selection but with the paper-ink chroma corridor narrowed to C ∈ [24, 32] — predicts cleaner co-existence in dense charts at the cost of some headroom. live D's semantic red #B71D27 is pinned at position 1 so loss/error/bad can map to the expected colour rather than a tight-corridor brown",
    ),
    Variant(
        "D3", "expand-8", "expand-8",
        "d-expand-8",
        "all 7 of live D's hues are pinned and the algorithm picks one extra 8th hue freely in the largest remaining wheel gap — tan (#BA843E ≈ H70°) and the new pick (indigo ≈ H270°) sit diametrically opposite, filling both remaining slots without forcing a swap",
        n_hues=8,
    ),
    Variant(
        "T", "tetradic", "tetradic",
        "tetradic",
        "four hue anchors 90° apart starting at brand green (the tetradic rule), then three mid-quadrant fillers — forces opposite-axis coverage that balanced max-min sometimes skips",
    ),
    Variant(
        "W", "warm-pole", "warm-pole",
        "warm-pole",
        "live D's max-min ΔE selection plus a warm-pole scoring bonus centred at 55° (half-width 30°) — biases picks toward the red/orange/amber band for plots dominated by warm categorical data. live D's semantic red #B71D27 is pinned at position 1 so the warm pole has a true red anchor rather than only orange-browns",
    ),
]


# -----------------------------------------------------------------------------
# Per-variant HTML rendering
# -----------------------------------------------------------------------------


def render_variant_page(
    variant: Variant,
    hues: list[str],
    seq_rgb: np.ndarray,
    seq_label: str,
    div_rgb: np.ndarray,
    div_label: str,
    *,
    is_baseline: bool = False,
) -> str:
    names = names_for_palette(hues)
    full_hexes = [*hues, NEUTRAL_LIGHT, NEUTRAL_DARK]
    full_labels = [*names, "neutral·light", "neutral·dark"]

    c_min_v, c_max_v = PER_VARIANT_C_RANGE[variant.strategy]

    first_4_score = measure_first_4(hues)
    normal_min = measure_all_normal_min(hues)

    swatches = render_swatch_table(full_hexes, full_labels)
    full_rgb = np.array([hex_to_rgb1(hx) for hx in full_hexes])
    matrix = render_matrix_block(full_rgb, full_labels)
    sample_charts = render_sample_charts(hues, n_series=4)
    first_n = render_first_n_summary(hues, names)
    seq_row = render_colormap_row(seq_label, samples_rgb=seq_rgb)
    seq_demo = render_cmap_demo(seq_rgb, label=f"sequential · {seq_label}")
    div_row = render_colormap_row(div_label, samples_rgb=div_rgb)
    div_demo = render_cmap_demo(div_rgb, label=f"diverging · {div_label}")
    cmap_block = f"{seq_row}\n{seq_demo}\n{div_row}\n{div_demo}"
    hero_pair = render_hero_mockup_pair(hues[0])

    # v1 — baseline is live D, not Okabe-Ito.
    baseline_4 = measure_first_4(ANYPLOT_D_PALETTE)
    if is_baseline:
        score_html = (
            f'<span class="score"><em>first-4 worst-CVD min ΔE</em>{first_4_score:.2f} '
            f'<span class="ink-muted">(this is the bar)</span></span>'
        )
    else:
        delta_vs_baseline = first_4_score - baseline_4
        delta_sign = "+" if delta_vs_baseline >= 0 else ""
        delta_class = 'delta-pos' if delta_vs_baseline >= 0 else 'delta-neg'
        score_html = (
            f'<span class="score"><em>first-4 worst-CVD min ΔE</em>{first_4_score:.2f} '
            f'<span class="{delta_class}">({delta_sign}{delta_vs_baseline:.2f} vs live D {baseline_4:.2f})</span></span>'
        )

    legend = render_legend()

    # Color wheel: large interactive, with chroma-corridor toggle and (for
    # non-baseline pages) an overlay of live D dots so you can compare geometry.
    wheel_overlay = None if is_baseline else ANYPLOT_D_PALETTE
    wheel = render_color_wheel(
        hues, size_px=520, mode="large",
        chroma_corridor=(c_min_v, c_max_v),
        overlay_hexes=wheel_overlay,
        dom_id=f"wheel-{variant.key.lower()}",
    )

    nav_links = [
        f'<a href="D-baseline.html" class="{"current" if is_baseline else ""}">★ D · baseline</a>'
    ]
    for v in VARIANTS:
        nav_links.append(
            f'<a href="{v.key}-{v.slug}.html" class="{"current" if (not is_baseline and v.key == variant.key) else ""}">{v.key} · {v.title}</a>'
        )
    nav = "".join(nav_links)

    page_title = "D · baseline (live anyplot palette)" if is_baseline else f"variant {variant.key}. {variant.title}"
    strategy_text = (
        "the palette currently shipping in core/images.py as ANYPLOT_PALETTE — kept here as the bar every v1 candidate is measured against. all v1 first-4 scores are reported as a delta against this row."
        if is_baseline
        else variant.one_liner + "."
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{page_title} — anyplot palette v1</title>
<style>{PAGE_CSS}
{WHEEL_CSS}
.variant-summary {{
    background: var(--bg-elevated);
    border: 1px solid var(--rule);
    border-radius: 6px;
    padding: 14px 18px;
    margin-bottom: 24px;
    font-size: 12px;
    line-height: 1.7;
}}
.variant-summary .score-row {{
    display: flex;
    gap: 18px;
    margin-top: 10px;
    flex-wrap: wrap;
}}
.variant-summary .score {{
    font-variant-numeric: tabular-nums;
    background: var(--bg-surface);
    border: 1px solid var(--rule);
    border-radius: 3px;
    padding: 4px 10px;
}}
.variant-summary .score em {{
    color: var(--ink-muted);
    font-style: normal;
    margin-right: 6px;
    font-size: 10.5px;
}}
.variant-summary .delta-pos {{ color: var(--ok-green); }}
.variant-summary .delta-neg {{ color: var(--ok-bad); }}
.variant-summary .ink-muted {{ color: var(--ink-muted); font-size: 11px; }}
.wheel-section .wheel-frame {{ margin: 8px auto 0; }}
</style>
</head>
<body>
<header class="masthead">
    <h1>any<span class="dot">.</span>plot() — {page_title}</h1>
    <div class="meta">CAM02-UCS · v1 · #5817</div>
    <button class="theme-toggle">◐ dark</button>
</header>

<nav class="variant-nav">
    <a href="index.html">grid</a>
    <a href="compare.html">compare</a>
    {nav}
</nav>

<div class="variant-summary">
    <strong>strategy:</strong> {strategy_text}<br>
    paper-ink corridor: J' ∈ [{J_MIN:.0f}, {J_MAX:.0f}], C ∈ [{c_min_v:.0f}, {c_max_v:.0f}].
    first-4 reordered to maximise min worst-CVD ΔE within {{1..4}}, pairwise hue gap ≥60°.
    <div class="score-row">
        {score_html}
        <span class="score"><em>all-pairs normal min ΔE</em>{normal_min:.2f}</span>
    </div>
</div>

<section class="domain">
    <h2>palette</h2>
    <p class="lede">{len(hues)} hues + 2 adaptive neutrals. positions 1–4 are the "first-4 most beautiful" subset chosen to maximise min worst-CVD ΔE. positions 5–{len(hues)} follow in descending min-distance-to-the-first-4. neutrals stay theme-adaptive (same as today's design tokens).</p>
    {swatches}
</section>

<section class="domain wheel-section">
    <h2>color wheel</h2>
    <p class="lede">CAM02-UCS hue ring at L=60, C=40. each palette dot sits at its actual (C, H) coordinates — angle is the hue, distance from centre is the chroma. dashed circles mark this variant's chroma corridor. the brand-anchor green is marked with a star. {"" if is_baseline else "toggle the overlay to see live D's dot positions for comparison."}</p>
    {wheel}
</section>

<section class="domain">
    <h2>sample &amp; first-n</h2>
    <p class="lede">first-4 chart on both production bg-page surfaces. the first-n table reads as "if you only use the first n positions, what's the weakest pair under normal vision vs. worst CVD".</p>
    {sample_charts}
    {first_n}
</section>

<section class="domain">
    <h2>ΔE matrix</h2>
    <p class="lede">normal vision left, worst-of-3-cvd right. cells coloured by the 4-step Petroff-2021 scale: ≥15 optimal, 10–15 okay, 5–10 marginal, &lt;5 confusable.</p>
    {matrix}
    {legend}
</section>

<section class="domain">
    <h2>continuous colormaps</h2>
    <p class="lede">two cmaps derived from this variant's palette: a <em>sequential</em> (brand-green → dark blue-zone palette member) and a <em>diverging</em> (warmest palette member ↔ coolest palette member through a near-neutral). hues come from the palette so the cmap reads as the same identity; J' and C are tuned for monotonic lightness descent (sequential) or symmetric weight (diverging). below each gradient: MATLAB's <code>peaks</code> surface rendered with that cmap.</p>
    {cmap_block}
</section>

<section class="domain">
    <h2>on the website</h2>
    <p class="lede">hero mockup pair using this variant's brand position-1 colour as the green-dot anchor. wcag badges live-update against the production bg-page surfaces.</p>
    {hero_pair}
</section>

<script>{PAGE_JS}
{WHEEL_JS}</script>
</body>
</html>
"""


# -----------------------------------------------------------------------------
# Index page (links all 5 variants)
# -----------------------------------------------------------------------------


def render_compare_page(rows: list[tuple[Variant, list[str], float, float]]) -> str:
    """One-page side-by-side comparison. v1 baseline = live D."""
    baseline_first4 = measure_first_4(ANYPLOT_D_PALETTE)

    rendered_rows = []
    # Render the live-D row first as the reference, then each candidate
    baseline_seq_rgb, baseline_seq_label = build_sequential_cmap(ANYPLOT_D_PALETTE)
    baseline_div_rgb, baseline_div_label = build_diverging_cmap(ANYPLOT_D_PALETTE)
    full_rows: list[tuple[str, str, str, list[str], float, float, np.ndarray, str, np.ndarray, str]] = []
    full_rows.append((
        "D", "baseline", "the palette currently shipping in core/images.py — every candidate below is measured against this row",
        ANYPLOT_D_PALETTE, baseline_first4, measure_all_normal_min(ANYPLOT_D_PALETTE),
        baseline_seq_rgb, baseline_seq_label, baseline_div_rgb, baseline_div_label,
    ))
    for variant, hues, first4, normal_min in rows:
        seq_rgb, seq_label = build_sequential_cmap(hues)
        div_rgb, div_label = build_diverging_cmap(hues)
        full_rows.append((
            variant.key, variant.title, variant.one_liner,
            hues, first4, normal_min,
            seq_rgb, seq_label, div_rgb, div_label,
        ))

    for (key, title, one_liner, hues, first4, normal_min,
         seq_rgb, seq_label, div_rgb, div_label) in full_rows:
        chip_all = "".join(
            f'<span class="big" style="background:{hx}" title="{hx}"></span>'
            for hx in hues
        ) + (
            f'<span class="big" style="background:{NEUTRAL_LIGHT};border:1px solid var(--rule)" title="{NEUTRAL_LIGHT} neutral·light"></span>'
            f'<span class="big" style="background:{NEUTRAL_DARK};border:1px solid var(--rule)" title="{NEUTRAL_DARK} neutral·dark"></span>'
        )
        seq_strip = render_gradient(seq_rgb[::4])
        div_strip = render_gradient(div_rgb[::4])
        seq_png = _peaks_png_b64(seq_rgb)
        div_png = _peaks_png_b64(div_rgb)
        seq_demo = f'<img src="{seq_png}" alt="peaks (sequential)" class="peaks-mini">'
        div_demo = f'<img src="{div_png}" alt="peaks (diverging)" class="peaks-mini">'

        is_baseline_row = (key == "D")
        delta = first4 - baseline_first4
        delta_sign = "+" if delta >= 0 else ""
        score_class = cell_class(first4)
        if is_baseline_row:
            delta_html = '<span class="delta">★ baseline</span>'
            link_target = "D-baseline.html"
            card_class = "compare-card compare-card-baseline"
        else:
            delta_class = 'delta-pos' if delta >= 0 else 'delta-neg'
            delta_html = f'<span class="delta {delta_class}">{delta_sign}{delta:.2f} vs live D</span>'
            # Find the variant slug for the link target
            slug_lookup = {v.key: v.slug for v in VARIANTS}
            link_target = f"{key}-{slug_lookup[key]}.html"
            card_class = "compare-card"

        rendered_rows.append(f"""
<section class="{card_class}">
    <header class="compare-head">
        <div class="title">
            <span class="key">{key}</span>
            <h3>{title}</h3>
        </div>
        <div class="metrics">
            <span class="metric {score_class}"><em>first-4 worst-CVD</em>{first4:.2f}</span>
            {delta_html}
            <a class="open-link" href="{link_target}">open full ↗</a>
        </div>
    </header>
    <p class="one-liner">{one_liner}.</p>
    <div class="compare-chips">{chip_all}</div>
    <div class="compare-cmaps">
        <div class="cmap-cell">
            <div class="cmap-cell-label">sequential — {seq_label}</div>
            {seq_strip}
            {seq_demo}
        </div>
        <div class="cmap-cell">
            <div class="cmap-cell-label">diverging — {div_label}</div>
            {div_strip}
            {div_demo}
        </div>
    </div>
</section>
""")

    variant_nav_links = "".join(
        f'<a href="{v.key}-{v.slug}.html">{v.key} · {v.title}</a>'
        for v in VARIANTS
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>palette variants v1 — side-by-side compare (#5817)</title>
<style>{PAGE_CSS}
.compare-card {{
    border: 1px solid var(--rule);
    border-radius: 8px;
    padding: 16px 18px;
    margin: 14px 0;
    background: var(--bg-elevated);
}}
.compare-card-baseline {{
    border-color: var(--ok-green);
    border-width: 1.5px;
}}
.compare-head {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 18px;
    margin-bottom: 8px;
}}
.compare-head .title {{ display: flex; align-items: baseline; gap: 12px; }}
.compare-head .title .key {{
    font-family: var(--mono);
    font-size: 18px;
    color: var(--accent);
    font-weight: 700;
}}
.compare-head h3 {{ margin: 0; font-size: 16px; }}
.compare-head .metrics {{ display: flex; gap: 12px; align-items: baseline; }}
.compare-head .metric {{
    font-family: var(--mono);
    font-size: 12px;
    padding: 3px 8px;
    border-radius: 3px;
    background: var(--bg-page);
    border: 1px solid var(--rule);
}}
.compare-head .metric em {{
    font-style: normal;
    color: var(--muted);
    margin-right: 6px;
}}
.compare-head .delta {{ font-family: var(--mono); font-size: 11px; color: var(--muted); }}
.compare-head .delta.delta-pos {{ color: var(--ok-green); font-weight: 600; }}
.compare-head .delta.delta-neg {{ color: var(--ok-bad); font-weight: 600; }}
.compare-head .open-link {{
    font-size: 11px;
    color: var(--accent);
    text-decoration: none;
}}
.compare-head .open-link:hover {{ text-decoration: underline; }}
.compare-card .one-liner {{ color: var(--muted); font-size: 12px; margin: 4px 0 12px; }}
.compare-chips {{ display: flex; gap: 6px; margin-bottom: 14px; }}
.compare-chips .big {{
    flex: 1;
    height: 28px;
    border-radius: 3px;
    box-shadow: inset 0 0 0 0.5px rgba(0,0,0,0.06);
}}
.compare-cmaps {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
}}
.cmap-cell-label {{
    font-size: 11px;
    color: var(--muted);
    font-style: italic;
    margin-bottom: 4px;
}}
.cmap-cell .gradient {{ height: 14px; margin-bottom: 4px; }}
.peaks-mini {{
    width: 100%;
    height: auto;
    display: block;
    border-radius: 4px;
}}
</style>
</head>
<body>
<header class="masthead">
    <h1>any<span class="dot">.</span>plot() — palette variants v1 · compare</h1>
    <div class="meta">CAM02-UCS · v1 · #5817</div>
    <button class="theme-toggle">◐ dark</button>
</header>
<nav class="variant-nav">
    <a href="index.html">grid</a>
    <a href="compare.html" class="current">compare</a>
    <a href="D-baseline.html">★ D · baseline</a>
    {variant_nav_links}
</nav>
<main class="domain">
    <p class="lede">all candidates side-by-side against live D. each card shows the full 7-hue + 2-neutral palette (left to right), both palette-derived continuous colormaps (sequential green→dark blue-zone, diverging warmest↔coolest), and a peaks-function preview of each cmap. baseline live D first-4 worst-CVD ΔE = {baseline_first4:.2f} — every candidate's Δ is reported against that.</p>
    {"".join(rendered_rows)}
</main>
<script>{PAGE_JS}</script>
</body>
</html>
"""


def render_index_page(rows: list[tuple[Variant, list[str], float, float]]) -> str:
    """v1 index: hero color wheel on top (live D), D-baseline card in the centre,
    candidate cards arrayed around it with Δ-vs-D coloring and per-card small
    wheels."""

    baseline_first4 = measure_first_4(ANYPLOT_D_PALETTE)
    baseline_normal = measure_all_normal_min(ANYPLOT_D_PALETTE)
    baseline_chip_top = "".join(
        f'<span class="big" style="background:{hx}" title="{hx}"></span>'
        for hx in ANYPLOT_D_PALETTE[:4]
    )
    baseline_chip_tail = "".join(
        f'<span class="small" style="background:{hx}" title="{hx}"></span>'
        for hx in ANYPLOT_D_PALETTE[4:]
    )
    baseline_score_class = cell_class(baseline_first4)
    baseline_wheel = render_color_wheel(
        ANYPLOT_D_PALETTE, size_px=180, mode="small",
        dom_id="card-wheel-baseline",
    )
    baseline_card = f"""
<a class="variant-card baseline-card" href="D-baseline.html">
    <div class="card-head">
        <span class="key">★</span>
        <h3>D · baseline <em>(live anyplot palette)</em></h3>
    </div>
    <p class="one-liner">the palette currently shipping in <code>core/images.py</code> — the bar every v1 candidate is measured against. variant D came from the v0 round (Petroff max-min ΔE, paper-ink corridor C ∈ [22, 36]) and has been adopted as the active ANYPLOT_PALETTE.</p>
    <div class="card-body-flex">
        <div class="card-strip-col">
            <div class="strip">
                <div class="chips-big">{baseline_chip_top}</div>
                <div class="chips-tail">{baseline_chip_tail}</div>
            </div>
            <div class="metrics">
                <span class="metric {baseline_score_class}"><em>first-4 worst-CVD</em>{baseline_first4:.2f}</span>
                <span class="metric"><em>all-pairs normal</em>{baseline_normal:.2f}</span>
                <span class="metric"><em>Δ-vs-D</em>0.00</span>
            </div>
        </div>
        <div class="card-wheel-col">{baseline_wheel}</div>
    </div>
    <div class="open">open diagnostic →</div>
</a>
"""

    cards = []
    for variant, hues, first4, normal_min in rows:
        chip_top = "".join(
            f'<span class="big" style="background:{hx}" title="{hx}"></span>' for hx in hues[:4]
        )
        chip_tail = "".join(
            f'<span class="small" style="background:{hx}" title="{hx}"></span>' for hx in hues[4:]
        )
        score_class = cell_class(first4)
        delta = first4 - baseline_first4
        delta_sign = "+" if delta >= 0 else ""
        delta_class = "delta-pos" if delta >= 0 else "delta-neg"
        small_wheel = render_color_wheel(
            hues, size_px=180, mode="small",
            dom_id=f"card-wheel-{variant.key.lower()}",
        )
        cards.append(f"""
<a class="variant-card" href="{variant.key}-{variant.slug}.html">
    <div class="card-head">
        <span class="key">{variant.key}</span>
        <h3>{variant.title}</h3>
    </div>
    <p class="one-liner">{variant.one_liner}.</p>
    <div class="card-body-flex">
        <div class="card-strip-col">
            <div class="strip">
                <div class="chips-big">{chip_top}</div>
                <div class="chips-tail">{chip_tail}</div>
            </div>
            <div class="metrics">
                <span class="metric {score_class}"><em>first-4 worst-CVD</em>{first4:.2f}</span>
                <span class="metric"><em>all-pairs normal</em>{normal_min:.2f}</span>
                <span class="metric {delta_class}"><em>Δ-vs-D</em>{delta_sign}{delta:.2f}</span>
            </div>
        </div>
        <div class="card-wheel-col">{small_wheel}</div>
    </div>
    <div class="open">open →</div>
</a>
""")

    # Hero: large wheel of live D + a toggle row that lets the viewer overlay
    # any candidate's dots on top to compare geometry without leaving the page.
    hero_wheel = render_color_wheel(
        ANYPLOT_D_PALETTE, size_px=420, mode="large",
        chroma_corridor=(22.0, 36.0),
        overlay_hexes=None,  # overlay is dynamically swapped by the candidate-toggle row
        dom_id="hero-wheel",
    )
    candidate_toggle_buttons = "".join(
        f'<button class="hero-toggle-btn" data-candidate="{v.key}" '
        f'data-hexes="{"|".join(h)}">{v.key} · {v.title}</button>'
        for (v, h, _, _) in rows
    )

    # Variant nav (same shape as v0 but using the v1 roster)
    variant_nav_links = "".join(
        f'<a href="{v.key}-{v.slug}.html">{v.key} · {v.title}</a>'
        for v in VARIANTS
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>palette variants v1 — anyplot #5817</title>
<style>{PAGE_CSS}
{WHEEL_CSS}
.intro {{
    max-width: 720px;
    margin-bottom: 32px;
}}
.intro p {{ color: var(--ink-soft); font-size: 13px; line-height: 1.7; }}
.intro code {{ color: var(--ink-soft); }}
.hero-wheel-section {{
    background: var(--bg-surface);
    border: 1px solid var(--rule);
    border-radius: 8px;
    padding: 24px 28px;
    margin-bottom: 28px;
    display: grid;
    grid-template-columns: minmax(360px, 460px) 1fr;
    gap: 28px;
    align-items: center;
}}
.hero-wheel-section .hero-text h2 {{
    margin: 0 0 6px 0;
    font-size: 16px;
    font-weight: 600;
    letter-spacing: -0.01em;
}}
.hero-wheel-section .hero-text h2::before {{
    content: "❯ ";
    color: var(--ink-muted);
    font-weight: 400;
}}
.hero-wheel-section .hero-text p {{
    margin: 0 0 14px 0;
    color: var(--ink-soft);
    font-size: 12px;
    line-height: 1.6;
}}
.hero-toggles {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }}
.hero-toggle-btn {{
    font-family: var(--mono);
    font-size: 11px;
    background: var(--bg-elevated);
    color: var(--ink-soft);
    border: 1px solid var(--rule);
    border-radius: 3px;
    padding: 5px 10px;
    cursor: pointer;
    transition: color 0.15s, border-color 0.15s, background 0.15s;
}}
.hero-toggle-btn:hover {{
    color: var(--ok-green);
    border-color: var(--ok-green);
}}
.hero-toggle-btn.active {{
    background: var(--ok-green);
    color: white;
    border-color: var(--ok-green);
}}
.variants-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
    gap: 18px;
}}
.variant-card {{
    background: var(--bg-surface);
    border: 1px solid var(--rule);
    border-radius: 8px;
    padding: 22px 24px 18px;
    color: var(--ink);
    text-decoration: none;
    display: flex;
    flex-direction: column;
    gap: 12px;
    transition: border-color 0.2s, transform 0.2s;
}}
.variant-card:hover {{
    border-color: var(--ok-green);
    transform: translateY(-2px);
}}
.card-head {{ display: flex; align-items: baseline; gap: 12px; }}
.card-head .key {{
    font-size: 18px;
    font-weight: 700;
    color: var(--ok-green);
    font-variant-numeric: tabular-nums;
}}
.baseline-card {{
    background: var(--bg-elevated);
    border-style: solid;
    border-color: var(--ok-green);
    border-width: 1.5px;
    grid-column: 1 / -1;
}}
.baseline-card .card-head h3 em {{
    font-style: normal;
    font-size: 11px;
    color: var(--ink-muted);
    font-weight: 400;
    margin-left: 4px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}}
.baseline-card .card-head .key {{ color: var(--ok-green); }}
.card-head h3 {{ margin: 0; font-size: 15px; font-weight: 600; letter-spacing: -0.01em; }}
.one-liner {{ margin: 0; font-size: 12px; color: var(--ink-soft); line-height: 1.55; }}
.card-body-flex {{
    display: grid;
    grid-template-columns: 1fr 180px;
    gap: 18px;
    align-items: center;
}}
.card-strip-col {{ display: flex; flex-direction: column; gap: 10px; }}
.card-wheel-col {{ display: flex; justify-content: center; align-items: center; }}
.card-wheel-col .color-wheel-small {{ display: block; }}
.strip {{ display: flex; gap: 6px; align-items: stretch; }}
.chips-big {{ display: flex; gap: 4px; flex: 1; }}
.chips-big .big {{ flex: 1; height: 40px; border-radius: 4px; }}
.chips-tail {{ display: flex; gap: 3px; align-items: stretch; }}
.chips-tail .small {{ width: 14px; height: 40px; border-radius: 3px; opacity: 0.85; }}
.metrics {{ display: flex; gap: 8px; flex-wrap: wrap; }}
.metric {{
    font-size: 10.5px;
    background: var(--bg-elevated);
    border: 1px solid var(--rule);
    border-radius: 3px;
    padding: 3px 8px;
    color: var(--ink-soft);
    font-variant-numeric: tabular-nums;
}}
.metric em {{ font-style: normal; color: var(--ink-muted); margin-right: 6px; }}
.metric.cell-ok   {{ background: rgba(0,158,115,0.22); color: var(--ink); }}
.metric.cell-meh  {{ background: rgba(240,228,66,0.30); color: var(--ink); }}
.metric.cell-warn {{ background: rgba(230,159,0,0.26); color: var(--ink); }}
.metric.cell-bad  {{ background: rgba(213,94,0,0.30); color: var(--ink); }}
.metric.delta-pos {{ background: rgba(0,158,115,0.18); color: var(--ok-green); font-weight: 600; }}
.metric.delta-neg {{ background: rgba(213,94,0,0.18); color: var(--ok-bad); font-weight: 600; }}
.open {{
    margin-top: auto;
    font-size: 11px;
    color: var(--ok-green);
    text-align: right;
    letter-spacing: 0.04em;
}}
</style>
</head>
<body>
<header class="masthead">
    <h1>any<span class="dot">.</span>plot() — palette variants v1 (#5817)</h1>
    <div class="meta">CAM02-UCS · v1 challenges live D · Petroff target ≥ 15</div>
    <button class="theme-toggle">◐ dark</button>
</header>
<nav class="variant-nav">
    <a href="index.html" class="current">grid</a>
    <a href="compare.html">compare</a>
    <a href="D-baseline.html">★ D · baseline</a>
    {variant_nav_links}
</nav>

<section class="intro">
    <p>v0 (<code>palette-variants/</code>) explored 6 candidates against Okabe-Ito and led to
    <strong>variant D</strong> being adopted as the live <code>ANYPLOT_PALETTE</code> in
    <code>core/images.py</code>. v1 reverses the framing: every candidate here is measured against
    <strong>live D</strong>, not Okabe-Ito. the bar is D's own first-4 worst-CVD ΔE
    of <strong>{baseline_first4:.2f}</strong>. a candidate that doesn't measurably beat that is not
    worth the migration cost.</p>
    <p>v1 splits into <em>refine</em> (three D-family tweaks D1/D2/D3) and <em>rethink</em>
    (two fresh strategies T tetradic and W warm-pole). same paper-ink corridor
    (J' ∈ [{J_MIN:.0f}, {J_MAX:.0f}], C ∈ [{C_MIN:.0f}, {C_MAX:.0f}]) and same greedy max-min ΔE under
    normal + 3 CVD conditions. each candidate page includes a CAM02-UCS color wheel
    that places every hue at its actual (C, H) coordinates — toggle the overlay to
    see how the candidate's geometry compares with live D.</p>
</section>

<section class="hero-wheel-section">
    <div>{hero_wheel}</div>
    <div class="hero-text">
        <h2>live D on the color wheel</h2>
        <p>each dot sits at its real (C, H) coordinates in CAM02-UCS — angle is the hue,
        distance from centre is the chroma. dashed rings mark the paper-ink corridor
        (C ∈ [22, 36]). brand anchor is the green star. click a candidate below to
        overlay its dot positions as outlined circles — distance shifts visualise the
        chroma/hue cost of each refinement.</p>
        <div class="hero-toggles">
            <button class="hero-toggle-btn active" data-candidate="" data-hexes="">D only</button>
            {candidate_toggle_buttons}
        </div>
    </div>
</section>

<div class="variants-grid">
{baseline_card}
{"".join(cards)}
</div>

<footer class="notes">
    <p>baseline (live D) first-4 worst-CVD min ΔE = {baseline_first4:.2f}
    — the bar these candidates try to clear. v0 round of variants A–F is preserved at
    <code>../palette-variants/</code>. references: petroff (2021) arXiv:2107.02270,
    okabe &amp; ito (2008), wong (2011), machado et al. (2009).</p>
</footer>

<script>{PAGE_JS}
{WHEEL_JS}
// Hero wheel — candidate overlay swap
(function () {{
    var heroWheel = document.getElementById('hero-wheel');
    if (!heroWheel) return;
    var overlayLayer = heroWheel.querySelector('.wheel-overlay');
    // Create overlay group if missing (live D alone has none by default)
    if (!overlayLayer) {{
        overlayLayer = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        overlayLayer.setAttribute('class', 'wheel-overlay');
        heroWheel.appendChild(overlayLayer);
    }}

    // Wheel geometry must match render_color_wheel's "large" mode at size=420
    var size = 420;
    var pad = 22;
    var cx = size / 2.0;
    var cy = size / 2.0;
    var r_out = (size / 2.0) - pad;
    var c_max_wheel = 60.0;

    function hexToRgb(hex) {{
        hex = hex.replace('#', '');
        return [parseInt(hex.substring(0, 2), 16) / 255,
                parseInt(hex.substring(2, 4), 16) / 255,
                parseInt(hex.substring(4, 6), 16) / 255];
    }}
    // Approximate sRGB → CAM02-UCS C,H using a perceptual proxy: convert to
    // OKLab (which is closely related and fast in JS), then derive C and H.
    // The overlay only needs relative placement, so the small bias vs the
    // server-side CAM02-UCS calc is acceptable here.
    function rgbToOklch(r, g, b) {{
        function lin(c) {{ return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }}
        var R = lin(r), G = lin(g), B = lin(b);
        var l = Math.cbrt(0.4122214708 * R + 0.5363325363 * G + 0.0514459929 * B);
        var m = Math.cbrt(0.2119034982 * R + 0.6806995451 * G + 0.1073969566 * B);
        var s = Math.cbrt(0.0883024619 * R + 0.2817188376 * G + 0.6299787005 * B);
        var L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s;
        var a = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s;
        var bb = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s;
        // Scale chroma to roughly match the CAM02-UCS C∈[0,60] range used server-side.
        var C = Math.sqrt(a * a + bb * bb) * 140.0;
        var H = (Math.atan2(bb, a) * 180.0 / Math.PI + 360.0) % 360.0;
        return [L, C, H];
    }}
    function polar(r, theta_deg) {{
        var t = theta_deg * Math.PI / 180.0;
        return [cx + r * Math.cos(t), cy - r * Math.sin(t)];
    }}
    function overlayMarkers(hx) {{
        var rgb = hexToRgb(hx);
        var lch = rgbToOklch(rgb[0], rgb[1], rgb[2]);
        var r = Math.min(lch[1] / c_max_wheel, 1.0) * r_out;
        var p = polar(r, lch[2]);
        // High-contrast ink halo behind the coloured ring so it stays visible
        // no matter which part of the disk it lands on.
        var halo = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        halo.setAttribute('cx', p[0].toFixed(2));
        halo.setAttribute('cy', p[1].toFixed(2));
        halo.setAttribute('r', '15');
        halo.setAttribute('fill', 'none');
        halo.setAttribute('stroke', 'var(--ink)');
        halo.setAttribute('stroke-width', '4');
        halo.setAttribute('opacity', '0.5');
        var ring = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        ring.setAttribute('cx', p[0].toFixed(2));
        ring.setAttribute('cy', p[1].toFixed(2));
        ring.setAttribute('r', '15');
        ring.setAttribute('fill', 'none');
        ring.setAttribute('stroke', hx);
        ring.setAttribute('stroke-width', '2.5');
        ring.setAttribute('opacity', '1');
        return [halo, ring];
    }}

    document.querySelectorAll('.hero-toggle-btn').forEach(function (btn) {{
        btn.addEventListener('click', function () {{
            document.querySelectorAll('.hero-toggle-btn').forEach(function (b) {{
                b.classList.remove('active');
            }});
            btn.classList.add('active');
            // Clear overlay
            while (overlayLayer.firstChild) overlayLayer.removeChild(overlayLayer.firstChild);
            var hexes = btn.getAttribute('data-hexes');
            if (!hexes) return;
            hexes.split('|').forEach(function (hx) {{
                overlayMarkers(hx).forEach(function (m) {{ overlayLayer.appendChild(m); }});
            }});
            overlayLayer.style.display = '';
        }});
    }});
}})();
</script>
</body>
</html>
"""


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate palette variants v1 for #5817")
    parser.add_argument(
        "--out-dir", type=Path, default=DEFAULT_OUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUT_DIR})",
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(message)s",
    )
    log = logging.getLogger("palette-variants-v1")

    args.out_dir.mkdir(parents=True, exist_ok=True)

    pool = CandidatePool.build(log)

    rows: list[tuple[Variant, list[str], float, float]] = []

    # Pinning: v1 D-family + warm-pole are "no anchors past brand-green"; only
    # tetradic has explicit pos 1-3 anchors that should not be reshuffled.
    PINNED: dict[str, tuple[int, ...]] = {
        "tetradic": (1, 2, 3),
    }

    # Per-strategy select_palette kwargs unique to v1.
    FORBIDDEN_BANDS: dict[str, tuple[tuple[float, float], ...]] = {
        # (currently no global hue exclusions in v1 — D3 was redesigned from
        # "swap-tan" into "expand-8" since tan + the new pick fill opposite
        # wheel gaps, so there's no reason to forbid either.)
    }
    # Semantic-red anchor — pinned for strategies whose natural picks fail to
    # land on a true red, so plots can still map loss/error/bad to the expected
    # colour rather than a tight-corridor brown or warm-bonus orange.
    SEMANTIC_RED = "#B71D27"  # live D's ANYPLOT_RED, same source as ANYPLOT_D_PALETTE[2]
    EXTRA_SEEDS: dict[str, tuple[str, ...]] = {
        # D1 — no extra_seed; a hue-band constraint at position 1 in
        # _strategy_bands keeps the picked red inside the tight chroma corridor
        # (a matte bordeaux ≈ L60·H25·C30 instead of the corridor-violating
        # live D #B71D27 at C≈44).
        "warm-pole":      (SEMANTIC_RED,),
        # D3 — pin every non-brand member of live D as a seed so reorder_first_4
        # works on the full live-D set plus one greedy 8th pick (positions 1-6
        # of live D become extra_seeds; brand-green is the implicit pos-0 seed).
        "d-expand-8":     tuple(ANYPLOT_D_PALETTE[1:]),
    }
    WARM_BONUS: dict[str, tuple[float, float, float]] = {
        # W — additive bonus centred at 55° (warm orange-red), half-width 30°,
        # weight 3.0 ΔE units at the centre. Strong enough to nudge selection
        # toward warms without overriding the no-clash gap mask.
    "warm-pole": (55.0, 30.0, 3.0),
    }

    baseline_4 = measure_first_4(ANYPLOT_D_PALETTE)
    log.info("baseline live D first-4 worst-CVD min ΔE = %.2f", baseline_4)

    for variant in VARIANTS:
        log.info("generating variant %s. %s …", variant.key, variant.title)
        hues = select_palette(
            variant.strategy, pool, n_hues=variant.n_hues,
            extra_seeds=EXTRA_SEEDS.get(variant.strategy, ()),
            forbidden_hue_bands=FORBIDDEN_BANDS.get(variant.strategy, ()),
            warm_bonus=WARM_BONUS.get(variant.strategy),
        )
        hues = reorder_first_4(hues, pinned=PINNED.get(variant.strategy, ()))

        first_4 = measure_first_4(hues)
        normal_min = measure_all_normal_min(hues)
        log.info(
            "  hues: %s",
            " ".join(hues),
        )
        log.info(
            "  first-4 worst-CVD min ΔE = %.2f (baseline live D = %.2f; Δ %+.2f)",
            first_4, baseline_4, first_4 - baseline_4,
        )

        seq_rgb, seq_label = build_sequential_cmap(hues)
        div_rgb, div_label = build_diverging_cmap(hues)
        html = render_variant_page(variant, hues, seq_rgb, seq_label, div_rgb, div_label)

        out_path = args.out_dir / f"{variant.key}-{variant.slug}.html"
        out_path.write_text(html, encoding="utf-8")
        size_kb = out_path.stat().st_size / 1024
        log.info("  wrote %s (%.1f kB)", out_path, size_kb)

        rows.append((variant, hues, first_4, normal_min))

    # Render the baseline (live D) using the same template as candidates so
    # it sits in the lineup as "the one to beat".
    log.info("generating D-baseline (live anyplot palette) diagnostic page …")
    baseline_variant = Variant(
        "D", "baseline", "baseline",
        "balanced",  # so PER_VARIANT_C_RANGE returns live D's corridor (22, 36)
        "the live anyplot palette currently shipping in core/images.py",
    )
    baseline_seq_rgb, baseline_seq_label = build_sequential_cmap(ANYPLOT_D_PALETTE)
    baseline_div_rgb, baseline_div_label = build_diverging_cmap(ANYPLOT_D_PALETTE)
    baseline_html = render_variant_page(
        baseline_variant, ANYPLOT_D_PALETTE,
        baseline_seq_rgb, baseline_seq_label,
        baseline_div_rgb, baseline_div_label,
        is_baseline=True,
    )
    baseline_path = args.out_dir / "D-baseline.html"
    baseline_path.write_text(baseline_html, encoding="utf-8")
    log.info("  wrote %s (%.1f kB)", baseline_path, baseline_path.stat().st_size / 1024)

    index_html = render_index_page(rows)
    index_path = args.out_dir / "index.html"
    index_path.write_text(index_html, encoding="utf-8")
    log.info("wrote %s (%.1f kB)", index_path, index_path.stat().st_size / 1024)

    compare_html = render_compare_page(rows)
    compare_path = args.out_dir / "compare.html"
    compare_path.write_text(compare_html, encoding="utf-8")
    log.info("wrote %s (%.1f kB)", compare_path, compare_path.stat().st_size / 1024)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
