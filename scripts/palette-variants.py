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
"""Palette variant generator for anyplot (Issue #5817).

Generates 6 candidate replacement palettes inspired by Anselmoo's
``dracula-palette`` generator (https://anselmoo.github.io/dracula-palette/),
all anchored at the brand green ``#009E73`` and selected by max-min ΔE in
CAM02-UCS under normal vision + 3 CVD conditions (deuteranomaly,
protanomaly, tritanomaly, each at 100% severity).

Variants differ in their hue-selection strategy:

  A — analogous            (harmony over distinctness; hues clustered)
  B — triadic              (three hue anchors 120° apart)
  C — split-complementary  (green plus two flanking complements)
  D — balanced             (Petroff-style max-min, paper-ink chroma)
  E — harmonic             (balanced rule but relaxed C corridor)
  F — okabe-anchored       (forces Okabe-Ito green + vermillion, fills 5)

For each, the script:

  1. Picks 7 hues respecting the strategy's hue rule, the paper-ink
     chroma/lightness corridor (J' ∈ [45,72], C ∈ [25,55]), and gamut.
  2. Reorders positions 2..4 so the first 4 maximise their internal
     min worst-CVD ΔE — the "most beautiful subset" criterion.
  3. Builds a perceptually-uniform continuous colormap starting at the
     brand green.
  4. Renders a self-contained HTML using the same rendering pipeline as
     ``palette-analysis.py``, so the variant pages are directly comparable
     to the baseline diagnostic.

Output: ``docs/reference/palette-variants/{A..F}-<name>.html`` plus an
``index.html`` linking the six.

Run::

    uv run --script scripts/palette-variants.py
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

# Okabe-Ito hex constants — kept inline so this variant-search script
# continues to compare new variants against the original Okabe-Ito palette
# even after core.images was migrated to the anyplot palette (variant D).
OK_GREEN = "#009E73"
OKABE_PALETTE = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]
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


DEFAULT_OUT_DIR = REPO_ROOT / "docs" / "reference" / "palette-variants"

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
    "analogous":      (24.0, 40.0),
    "triadic":        (26.0, 42.0),
    "split-comp":     (26.0, 42.0),
    "balanced":       (22.0, 36.0),
    "harmonic":       (22.0, 60.0),  # F: relaxed paper-ink — wider C headroom for more harmonious hue picks
    "okabe-anchored": (22.0, 42.0),  # room for both brand-green (C=25) and vermillion (C=34) + 5 fillers
}


# Minimum pairwise hue spacing target per strategy (degrees on the colour wheel).
# Every strategy now enforces this via the diversity penalty inside
# ``score_candidates``; without it, max-min ΔE optimisation cheerfully picks
# two near-identical blues or two yellow-greens whenever the chroma corridor
# leaves headroom for only one warm/cool region.
PER_VARIANT_HUE_SPREAD: dict[str, float] = {
    "analogous":      35.0,  # narrow wedge ±90° around green → smaller target
    "triadic":        45.0,
    "split-comp":     45.0,
    "balanced":       50.0,  # 360/7 ≈ 51°, the ideal even spacing
    "harmonic":       50.0,
    "okabe-anchored": 45.0,  # two anchors already at 166° and 51° → 115° apart, 5 fillers to spread
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
) -> list[str]:
    """Pick 7 hues for a variant. Greedy max-min ΔE selection under all 4
    CVD conditions, with per-position hue bands and the per-variant chroma
    corridor as candidate masks. If no candidate matches the strictest band,
    the band half-width is widened in 10° steps until something fits.

    ``extra_seeds`` are pinned hex strings that follow brand-green in the
    output. Used by okabe-anchored to keep #D55E00 (vermillion) in the
    palette regardless of where greedy max-min would put it.
    """

    brand_rgb = hex_to_rgb1(OK_GREEN)
    _, _, brand_H = jab_to_lch(to_jab(brand_rgb.reshape(1, 3))[0])

    bands_per_pos = _strategy_bands(strategy, brand_H, n_hues)
    c_min, c_max = PER_VARIANT_C_RANGE[strategy]
    chroma_mask = (pool.chromas >= c_min) & (pool.chromas <= c_max)

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
    assert n == 7

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
# Variant definitions
# -----------------------------------------------------------------------------


@dataclass
class Variant:
    key: str  # "A".."E"
    slug: str  # filename-safe
    title: str  # short name
    strategy: str  # algorithm identifier
    one_liner: str  # human description shown on each page + index


VARIANTS = [
    Variant(
        "A", "analogous", "analogous",
        "analogous",
        "harmony over distinctness — hues cluster within ±90° of brand green",
    ),
    Variant(
        "B", "triadic", "triadic",
        "triadic",
        "three primaries 120° apart (green · purple · amber-red), plus four harmonic fillers (azure, magenta, lime, cyan)",
    ),
    Variant(
        "C", "split-complementary", "split-complementary",
        "split-comp",
        "green + the two flanking complements at +150° (magenta) and +210° (red), then four-quadrant fillers",
    ),
    Variant(
        "D", "balanced", "balanced",
        "balanced",
        "Petroff-style max-min ΔE optimisation under the paper-ink corridor — no hue rule",
    ),
    Variant(
        "E", "harmonic", "harmonic",
        "harmonic",
        "same max-min ΔE selection as balanced, but with the paper-ink chroma corridor widened (C∈[22,60]) for more harmonic headroom",
    ),
    Variant(
        "F", "okabe-anchored", "okabe-anchored",
        "okabe-anchored",
        "Okabe-Ito's vermillion (#D55E00) seeded into the 7-hue pool alongside brand-green — both already paper-ink-compliant. reorder_first_4 then chooses top-4 freely; vermillion stays in if it earns the spot.",
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

    # Methodology summary block
    okabe_hex_lower = [h.lower() for h in OKABE_PALETTE]
    baseline_4 = measure_first_4(OKABE_PALETTE)
    delta_vs_baseline = first_4_score - baseline_4
    delta_sign = "+" if delta_vs_baseline >= 0 else ""

    legend = render_legend()

    nav = '<a href="../palette-analysis.html">★ baseline</a>' + "".join(
        f'<a href="{v.key}-{v.slug}.html" class="{"current" if v.key == variant.key else ""}">{v.key} · {v.title}</a>'
        for v in VARIANTS
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>variant {variant.key}. {variant.title} — anyplot palette</title>
<style>{PAGE_CSS}
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
</style>
</head>
<body>
<header class="masthead">
    <h1>any<span class="dot">.</span>plot() — variant {variant.key}. {variant.title}</h1>
    <div class="meta">CAM02-UCS · #5817</div>
    <button class="theme-toggle">◐ dark</button>
</header>

<nav class="variant-nav">
    <a href="index.html">grid</a>
    <a href="compare.html">compare</a>
    {nav}
</nav>

<div class="variant-summary">
    <strong>strategy:</strong> {variant.one_liner}.<br>
    paper-ink corridor: J' ∈ [{J_MIN:.0f}, {J_MAX:.0f}], C ∈ [{c_min_v:.0f}, {c_max_v:.0f}].
    first-4 reordered to maximise min worst-CVD ΔE within {{1..4}}, pairwise hue gap ≥60°.
    <div class="score-row">
        <span class="score"><em>first-4 worst-CVD min ΔE</em>{first_4_score:.2f}
        <span class="{ 'delta-pos' if delta_vs_baseline >= 0 else 'delta-neg'}">({delta_sign}{delta_vs_baseline:.2f} vs Okabe-Ito {baseline_4:.2f})</span></span>
        <span class="score"><em>all-pairs normal min ΔE</em>{normal_min:.2f}</span>
    </div>
</div>

<section class="domain">
    <h2>palette</h2>
    <p class="lede">7 hues + 2 adaptive neutrals. positions 1–4 are the "first-4 most beautiful" subset chosen to maximise min worst-CVD ΔE. positions 5–7 follow in descending min-distance-to-the-first-4. neutrals stay theme-adaptive (same as today's design tokens).</p>
    {swatches}
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

<script>{PAGE_JS}</script>
</body>
</html>
"""


# -----------------------------------------------------------------------------
# Index page (links all 5 variants)
# -----------------------------------------------------------------------------


def render_compare_page(rows: list[tuple[Variant, list[str], float, float]]) -> str:
    """One-page side-by-side comparison of all variants for decision making.
    Each row shows: header + score · all 9 swatches · sequential cmap strip
    with mini peaks demo · diverging cmap strip with mini peaks demo · link
    to full variant page. Heavier than index.html (~250 kB with embedded
    PNGs) but everything you need to choose a variant lives in one viewport.
    """
    baseline_first4 = measure_first_4(OKABE_PALETTE)

    rendered_rows = []
    for variant, hues, first4, normal_min in rows:
        chip_all = "".join(
            f'<span class="big" style="background:{hx}" title="{hx}"></span>'
            for hx in hues
        ) + (
            f'<span class="big" style="background:{NEUTRAL_LIGHT};border:1px solid var(--rule)" title="{NEUTRAL_LIGHT} neutral·light"></span>'
            f'<span class="big" style="background:{NEUTRAL_DARK};border:1px solid var(--rule)" title="{NEUTRAL_DARK} neutral·dark"></span>'
        )

        seq_rgb, seq_label = build_sequential_cmap(hues)
        div_rgb, div_label = build_diverging_cmap(hues)
        seq_strip = render_gradient(seq_rgb[::4])  # downsample for compare-page strip width
        div_strip = render_gradient(div_rgb[::4])
        # Single-frame peaks demos (no light/dark pair) to keep page weight down
        seq_png = _peaks_png_b64(seq_rgb)
        div_png = _peaks_png_b64(div_rgb)
        seq_demo = f'<img src="{seq_png}" alt="peaks (sequential)" class="peaks-mini">'
        div_demo = f'<img src="{div_png}" alt="peaks (diverging)" class="peaks-mini">'

        delta = first4 - baseline_first4
        delta_sign = "+" if delta >= 0 else ""
        score_class = cell_class(first4)

        rendered_rows.append(f"""
<section class="compare-card">
    <header class="compare-head">
        <div class="title">
            <span class="key">{variant.key}</span>
            <h3>{variant.title}</h3>
        </div>
        <div class="metrics">
            <span class="metric {score_class}"><em>first-4 worst-CVD</em>{first4:.2f}</span>
            <span class="delta {'delta-pos' if delta >= 0 else 'delta-neg'}">{delta_sign}{delta:.2f} vs Okabe-Ito</span>
            <a class="open-link" href="{variant.key}-{variant.slug}.html">open full ↗</a>
        </div>
    </header>
    <p class="one-liner">{variant.one_liner}.</p>
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

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>palette variants — side-by-side compare (#5817)</title>
<style>{PAGE_CSS}
.compare-card {{
    border: 1px solid var(--rule);
    border-radius: 8px;
    padding: 16px 18px;
    margin: 14px 0;
    background: var(--bg-elevated);
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
    <h1>any<span class="dot">.</span>plot() — palette variants · compare</h1>
    <div class="meta">CAM02-UCS · #5817</div>
    <button class="theme-toggle">◐ dark</button>
</header>
<nav class="variant-nav">
    <a href="index.html">grid</a>
    <a href="compare.html" class="current">compare</a>
    <a href="../palette-analysis.html">★ baseline</a>
    <a href="A-analogous.html">A · analogous</a>
    <a href="B-triadic.html">B · triadic</a>
    <a href="C-split-complementary.html">C · split-complementary</a>
    <a href="D-balanced.html">D · balanced</a>
    <a href="E-harmonic.html">E · harmonic</a>
    <a href="F-okabe-anchored.html">F · okabe-anchored</a>
</nav>
<main class="domain">
    <p class="lede">all variants side-by-side for decision making. each card shows the full 7-hue + 2-neutral palette (left to right), both palette-derived continuous colormaps (sequential green→dark blue-zone, diverging warmest↔coolest), and a peaks-function preview of each cmap. baseline Okabe-Ito first-4 worst-CVD ΔE = {baseline_first4:.2f} for reference.</p>
    {"".join(rendered_rows)}
</main>
<script>{PAGE_JS}</script>
</body>
</html>
"""


def render_index_page(rows: list[tuple[Variant, list[str], float, float]]) -> str:
    # Baseline card — current Okabe-Ito palette as the reference everyone
    # compares against. Linked to the full diagnostic for drill-down.
    baseline_first4 = measure_first_4(OKABE_PALETTE)
    baseline_normal = measure_all_normal_min(OKABE_PALETTE)
    baseline_chip_top = "".join(
        f'<span class="big" style="background:{hx}" title="{hx}"></span>'
        for hx in OKABE_PALETTE[:4]
    )
    baseline_chip_tail = "".join(
        f'<span class="small" style="background:{hx}" title="{hx}"></span>'
        for hx in OKABE_PALETTE[4:]
    )
    baseline_score_class = cell_class(baseline_first4)
    baseline_card = f"""
<a class="variant-card baseline-card" href="../palette-analysis.html">
    <div class="card-head">
        <span class="key">★</span>
        <h3>baseline — okabe-ito <em>(legacy)</em></h3>
    </div>
    <p class="one-liner">the previous plot palette, kept here as the bar every variant below tried to clear — the bar is the green×blue tritanopia collapse at ΔE 11.73. variant D has since been adopted as the active anyplot palette.</p>
    <div class="strip">
        <div class="chips-big">{baseline_chip_top}</div>
        <div class="chips-tail">{baseline_chip_tail}</div>
    </div>
    <div class="metrics">
        <span class="metric {baseline_score_class}"><em>first-4 worst-CVD</em>{baseline_first4:.2f}</span>
        <span class="metric"><em>all-pairs normal</em>{baseline_normal:.2f}</span>
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
        cards.append(f"""
<a class="variant-card" href="{variant.key}-{variant.slug}.html">
    <div class="card-head">
        <span class="key">{variant.key}</span>
        <h3>{variant.title}</h3>
    </div>
    <p class="one-liner">{variant.one_liner}.</p>
    <div class="strip">
        <div class="chips-big">{chip_top}</div>
        <div class="chips-tail">{chip_tail}</div>
    </div>
    <div class="metrics">
        <span class="metric {score_class}"><em>first-4 worst-CVD</em>{first4:.2f}</span>
        <span class="metric"><em>all-pairs normal</em>{normal_min:.2f}</span>
    </div>
    <div class="open">open →</div>
</a>
""")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>palette variants — anyplot #5817</title>
<style>{PAGE_CSS}
.intro {{
    max-width: 720px;
    margin-bottom: 32px;
}}
.intro p {{ color: var(--ink-soft); font-size: 13px; line-height: 1.7; }}
.intro code {{ color: var(--ink-soft); }}
.variants-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
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
    border-style: dashed;
    border-color: var(--ink-muted);
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
.baseline-card .card-head .key {{ color: var(--ink-muted); }}
.card-head h3 {{ margin: 0; font-size: 15px; font-weight: 600; letter-spacing: -0.01em; }}
.one-liner {{ margin: 0; font-size: 12px; color: var(--ink-soft); line-height: 1.55; }}
.strip {{ display: flex; gap: 6px; align-items: stretch; }}
.chips-big {{ display: flex; gap: 4px; flex: 1; }}
.chips-big .big {{ flex: 1; height: 56px; border-radius: 4px; }}
.chips-tail {{ display: flex; gap: 3px; align-items: stretch; }}
.chips-tail .small {{ width: 18px; height: 56px; border-radius: 3px; opacity: 0.85; }}
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
    <h1>any<span class="dot">.</span>plot() — palette variants (#5817)</h1>
    <div class="meta">CAM02-UCS · Petroff target ≥ 15</div>
    <button class="theme-toggle">◐ dark</button>
</header>
<nav class="variant-nav">
    <a href="index.html" class="current">grid</a>
    <a href="compare.html">compare</a>
    <a href="../palette-analysis.html">★ baseline</a>
    <a href="A-analogous.html">A · analogous</a>
    <a href="B-triadic.html">B · triadic</a>
    <a href="C-split-complementary.html">C · split-complementary</a>
    <a href="D-balanced.html">D · balanced</a>
    <a href="E-harmonic.html">E · harmonic</a>
    <a href="F-okabe-anchored.html">F · okabe-anchored</a>
</nav>

<section class="intro">
    <p>five candidate palettes inspired by Anselmoo's <code>dracula-palette</code> generator —
    all anchored at brand green <code>{OK_GREEN}</code>, generated by greedy max-min ΔE
    selection in CAM02-UCS under normal vision + 3 CVD conditions (deuteranopia, protanopia,
    tritanopia at 100% severity). all colours sit inside a paper-ink corridor
    (J' ∈ [{J_MIN:.0f}, {J_MAX:.0f}], C ∈ [{C_MIN:.0f}, {C_MAX:.0f}]) — that's the lever that
    keeps the palette away from caligo-style neon while staying perceptually uniform.</p>
    <p>positions 1–4 in each variant are the "first-4 most beautiful" subset: the 3 colours
    out of 6 that, together with brand green, maximise their internal min worst-CVD ΔE.
    most plots use 2–3 series so this subset is in 95% of the visual surface.</p>
</section>

<div class="variants-grid">
{baseline_card}
{"".join(cards)}
</div>

<footer class="notes">
    <p>baseline (Okabe-Ito) first-4 worst-CVD min ΔE = {measure_first_4(OKABE_PALETTE):.2f}
    — the bar these variants try to clear. references: petroff (2021) arXiv:2107.02270,
    okabe &amp; ito (2008), wong (2011), machado et al. (2009), dracula-palette generator
    (anselmoo.github.io/dracula-palette).</p>
</footer>

<script>{PAGE_JS}</script>
</body>
</html>
"""


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate palette variants for #5817")
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
    log = logging.getLogger("palette-variants")

    args.out_dir.mkdir(parents=True, exist_ok=True)

    pool = CandidatePool.build(log)

    rows: list[tuple[Variant, list[str], float, float]] = []

    # Strategies whose pos 1 and 2 ARE the strategy signature — pinning these
    # keeps triadic visibly different from split-comp (otherwise the reorder
    # picks max-min ΔE positions that happen to coincide). Okabe-anchored
    # additionally pins pos 1 to vermillion.
    PINNED: dict[str, tuple[int, ...]] = {
        "triadic":         (1, 2),
        "split-comp":      (1, 2),
        # okabe-anchored: vermillion is seeded into the 7-hue pool but NOT
        # pinned — reorder_first_4 may move it out of top-4 if a different
        # pick gives more CVD distance to brand-green.
    }

    EXTRA_SEEDS: dict[str, tuple[str, ...]] = {
        "okabe-anchored": ("#D55E00",),  # vermillion — Okabe-Ito's warm pillar
    }

    for variant in VARIANTS:
        log.info("generating variant %s. %s …", variant.key, variant.title)
        hues = select_palette(
            variant.strategy, pool, n_hues=7,
            extra_seeds=EXTRA_SEEDS.get(variant.strategy, ()),
        )
        hues = reorder_first_4(hues, pinned=PINNED.get(variant.strategy, ()))

        first_4 = measure_first_4(hues)
        normal_min = measure_all_normal_min(hues)
        baseline_4 = measure_first_4(OKABE_PALETTE)
        log.info(
            "  hues: %s",
            " ".join(hues),
        )
        log.info(
            "  first-4 worst-CVD min ΔE = %.2f (baseline Okabe-Ito = %.2f; Δ %+.2f)",
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
