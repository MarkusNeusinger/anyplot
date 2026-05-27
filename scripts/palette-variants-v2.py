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
"""Palette variants v2 — head-to-head: vivid-8 (D3) vs muted-8 (D1-8).

v1 produced five candidate variants (D-baseline, D1, D1-8, D3, T, W). Two
emerged as the realistic contenders for the next live ANYPLOT_PALETTE:

  vivid-8  (was D3 / d-expand-8)        — chroma corridor C ∈ [22, 36],
                                          live D's 7 hues + 1 indigo greedy
                                          pick in the largest wheel gap;
                                          max CVD-distance headroom.

  muted-8  (was D1-8 / d-tight-chroma-8) — chroma corridor C ∈ [24, 32],
                                          live D's max-min selection inside
                                          a tighter paper-ink band + 1 matte
                                          rosé in the back-gap; cleaner
                                          co-existence in dense charts.

The two palettes are colour-identical to v1's D3 / D1-8; only the slot
**order** of the 8 hues can vary, and the order matters because the
review-loop picks colours in order from positions 0..n. v2 explores
**different sort orderings** for the same two palettes and shows them
side-by-side per sorting in a single HTML page so a human can pick which
combination of palette × sorting feels best.

Layout per sorting section
--------------------------
   ┌──────────────────────┬──────────────────────┐
   │ vivid-8 strip + n→ΔE │ muted-8 strip + n→ΔE │
   ├──────────────────────┼──────────────────────┤
   │ vivid-8 light chart  │ muted-8 light chart  │
   ├──────────────────────┼──────────────────────┤
   │ vivid-8 dark chart   │ muted-8 dark chart   │
   └──────────────────────┴──────────────────────┘

Sortings included
-----------------
  1. pure-CVD greedy max-min   (slowest possible per-n ΔE degradation;
                                pos 0 fixed brand-green; pos 1 fixed at
                                muted-8's semantic red for stability)
  2. wheel-gap-first           (v1's reorder_first_4 — first-4 picked by
                                widest pairwise hue-gap at ≥60° then rest
                                by descending distance to first-4)
  3. hue-order                 (pos 0 = brand green; rest by hue angle
                                clockwise — natural rainbow, ignores CVD)
  4. every-other-hue           (hue-order, then interleave: first-4 = every
                                other wedge for maximally even wheel
                                coverage; rest are the in-between wedges)

Run::

    uv run --script scripts/palette-variants-v2.py
"""

from __future__ import annotations

import argparse
import html
import importlib.util
import logging
import math
import random
import sys
from pathlib import Path
from typing import Callable, Sequence

import numpy as np


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

# Import v1 utilities (hyphenated filename → importlib).
_V1_SPEC = importlib.util.spec_from_file_location(
    "palette_variants_v1", REPO_ROOT / "scripts" / "palette-variants-v1.py"
)
assert _V1_SPEC is not None and _V1_SPEC.loader is not None
v1 = importlib.util.module_from_spec(_V1_SPEC)
# Register before exec_module so @dataclass can resolve cls.__module__ during
# class construction (otherwise dataclasses.py raises NoneType.__dict__).
sys.modules["palette_variants_v1"] = v1
_V1_SPEC.loader.exec_module(v1)

from _palette_common import (  # noqa: E402
    DARK_THEME_FULL,
    LIGHT_THEME_FULL,
    PAGE_CSS,
    PAGE_JS,
    hex_to_rgb1,
    pairwise_delta_e,
    render_sample_bars,
    render_sample_chart,
    to_jab,
    worst_cvd_pairwise_delta_e,
)


# -----------------------------------------------------------------------------
# Palette definitions — colour-identical to v1's D3 / D1-8 picks
# -----------------------------------------------------------------------------

VIVID_8: list[str] = [
    "#009E73",  # brand green
    "#9418DB",  # purple    — live D pos 1
    "#B71D27",  # red       — live D pos 2
    "#16B8F3",  # cyan      — live D pos 3
    "#99B314",  # lime      — live D pos 4
    "#D359A7",  # pink      — live D pos 5
    "#7981FD",  # indigo    — v1 D3 8th-slot pick
    "#BA843E",  # tan       — live D pos 6
]

MUTED_8: list[str] = [
    "#009E73",  # brand green
    "#AE3030",  # matte red   — pinned via hue-band [25°±10°] in tight corridor
    "#C475FD",  # purple
    "#99B314",  # lime
    "#4467A3",  # blue
    "#2ABCCD",  # cyan
    "#954477",  # matte rosé  — v1 D1-8 8th-slot pick (back-gap bridge)
    "#BD8233",  # tan
]


PALETTES: list[tuple[str, str, list[str], str]] = [
    (
        "vivid-8",
        "wide chroma corridor C ∈ [22, 36] — live D's 7 hues plus a greedy 8th indigo pick that fills the wheel gap opposite tan. max CVD-headroom, the best worst-pair ΔE at small n.",
        VIVID_8,
        "rgb(72, 158, 116)",  # accent for section headings
    ),
    (
        "muted-8",
        "tight chroma corridor C ∈ [24, 32] — D1's max-min selection plus a matte rosé filling the 75° back-gap between purple and red. lower per-pair ΔE ceiling but flatter co-existence inside dense small-multiple charts.",
        MUTED_8,
        "rgb(86, 132, 191)",
    ),
]


# -----------------------------------------------------------------------------
# Sorting functions
# -----------------------------------------------------------------------------


def _hue(hex_str: str) -> float:
    rgb = hex_to_rgb1(hex_str).reshape(1, 3)
    jab = to_jab(rgb)[0]
    _, _, H = v1.jab_to_lch(jab)
    return H


def _lightness(hex_str: str) -> float:
    rgb = hex_to_rgb1(hex_str).reshape(1, 3)
    jab = to_jab(rgb)[0]
    L, _, _ = v1.jab_to_lch(jab)
    return L


def sort_pure_cvd_greedy(hexes: list[str]) -> list[str]:
    """Only pos 0 (brand green) fixed; positions 1..n picked iteratively to
    maximise min worst-CVD ΔE against the already-placed set. No semantic
    anchors — pure algorithmic CVD optimisation."""
    return v1.reorder_pure_cvd_greedy(hexes, pinned=())


def sort_wheel_gap_first(hexes: list[str]) -> list[str]:
    """v1's reorder_first_4: widest-gap first-4 then rest by descending distance."""
    return v1.reorder_first_4(hexes)


def sort_hue_order(hexes: list[str]) -> list[str]:
    """pos 0 = brand green; rest sorted by hue angle clockwise from green."""
    brand_hue = _hue(hexes[0])
    rest = sorted(hexes[1:], key=lambda hx: (_hue(hx) - brand_hue) % 360)
    return [hexes[0], *rest]


def sort_every_other_hue(hexes: list[str]) -> list[str]:
    """Hue-ordered then interleaved: first-4 = every-other wedge for maximally
    even wheel coverage; the in-between wedges follow as the second-4."""
    full = sort_hue_order(hexes)
    n = len(full)
    even = [full[i] for i in range(0, n, 2)]
    odd = [full[i] for i in range(1, n, 2)]
    return [*even, *odd]


SORTINGS: list[tuple[str, str, str, Callable[[list[str]], list[str]]]] = [
    (
        "pure-cvd-greedy",
        "pure-CVD greedy max-min",
        "only pos 0 (brand green) fixed; positions 1..n picked iteratively to maximise min worst-CVD ΔE against the already-placed set. No semantic anchors — pure algorithmic CVD optimisation. Designed to keep the per-n worst-pair curve as high as possible for chart series-count growth.",
        sort_pure_cvd_greedy,
    ),
    (
        "wheel-gap-first",
        "wheel-gap-first (v1 reorder_first_4)",
        "v1 algorithm: among 3-tuples joining brand green, pick the one whose 4-set has the widest pairwise hue-gap at ≥60° (degrades in 5° steps if no quadruple satisfies); rest by descending min-distance to first-4. Trades CVD distinctness for visual wheel symmetry.",
        sort_wheel_gap_first,
    ),
    (
        "hue-order",
        "hue-order (rainbow)",
        "pos 0 = brand green; remaining 7 hues sorted by hue angle going clockwise around the wheel. Pure “natural rainbow” order — ignores CVD distance entirely. Useful when the chart's series correspond to an ordered category (time, magnitude bins) and the rainbow conveys that order.",
        sort_hue_order,
    ),
    (
        "every-other-hue",
        "every-other-hue (interleaved)",
        "Hue-order full set, then interleave: first-4 = every other wedge for maximally even wheel coverage; the in-between wedges follow as the second-4. The first-4 still spans the whole wheel symmetrically — like wheel-gap-first but constructed via interleaving instead of search.",
        sort_every_other_hue,
    ),
]


# -----------------------------------------------------------------------------
# Measurements
# -----------------------------------------------------------------------------


def measure_per_n(hexes: list[str]) -> list[float]:
    """Worst-CVD ΔE of the weakest pair inside the first-n subset, for n=2..N.
    Takes the min across normal + 3 CVD simulations."""
    rgb = np.array([hex_to_rgb1(h) for h in hexes])
    M, _ = worst_cvd_pairwise_delta_e(rgb)
    return _weakest_pair_per_n(M, len(hexes))


def measure_per_n_normal(hexes: list[str]) -> list[float]:
    """Normal-vision pairwise ΔE of the weakest pair in first-n, no CVD sim."""
    rgb = np.array([hex_to_rgb1(h) for h in hexes])
    M = pairwise_delta_e(rgb, "normal")
    return _weakest_pair_per_n(M, len(hexes))


def _weakest_pair_per_n(M: np.ndarray, n: int) -> list[float]:
    out: list[float] = []
    for k in range(2, n + 1):
        sub = M[:k, :k].copy()
        np.fill_diagonal(sub, np.inf)
        out.append(round(float(sub.min()), 2))
    return out


# -----------------------------------------------------------------------------
# HTML rendering
# -----------------------------------------------------------------------------


V2_CSS = """
.v2-hero { padding: 32px 28px 18px; }
.v2-hero h1 { margin: 0 0 4px; font-size: 26px; }
.v2-hero p.subtitle { margin: 0 0 8px; color: var(--ink-muted); font-size: 14px; }
.v2-pair-row {
    display: grid; grid-template-columns: 1fr 1fr; gap: 24px;
    margin: 20px 0;
}
.v2-pair-cell { min-width: 0; }
.v2-pair-cell h2 { margin: 0 0 8px; font-size: 18px; }
.v2-pair-cell h3 { margin: 14px 0 6px; font-size: 13px; color: var(--ink-muted); font-weight: 500; letter-spacing: 0.04em; text-transform: uppercase; }
.v2-pair-cell p { margin: 0 0 8px; font-size: 13px; color: var(--ink-muted); line-height: 1.5; }

/* Strips row uses a column-major grid so corresponding rows (heading, intro,
   strip, table) line up between left and right cells even if the intro
   paragraph wraps to a different number of lines on each side. */
.v2-pair-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    column-gap: 24px;
    row-gap: 6px;
    margin: 20px 0;
}
.v2-pair-grid .pg-head { margin: 0 0 4px; font-size: 18px; }
.v2-pair-grid .pg-intro { margin: 0; font-size: 13px; color: var(--ink-muted); line-height: 1.5; align-self: end; }
.v2-pair-grid .pg-wheel { display: flex; justify-content: center; padding: 8px 0; }
.v2-pair-grid .pg-wheel svg { max-width: 100%; height: auto; }
/* corridor ring is always visible in v2; drop the toggle UI from v1's wheel. */
.v2-pair-grid .wheel-toggles { display: none; }

.v2-palette-strip { display: flex; height: 70px; border-radius: 6px; overflow: hidden; box-shadow: 0 0 0 1px var(--rule); }
.v2-palette-strip .swatch { flex: 1; display: flex; align-items: center; justify-content: center; font-family: var(--mono); font-size: 10px; }
.v2-pertable { width: 100%; border-collapse: collapse; font-family: var(--mono); font-size: 11px; margin-top: 8px; }
.v2-pertable th, .v2-pertable td { padding: 4px 6px; text-align: right; border-bottom: 1px solid var(--rule); }
.v2-pertable th:first-child, .v2-pertable td:first-child { text-align: left; color: var(--ink-muted); }
.v2-pertable td.good { color: #2a8d52; font-weight: 600; }
.v2-pertable td.warn { color: #b56b18; }
.v2-pertable td.bad  { color: #b62d2d; font-weight: 600; }

.v2-section { padding: 28px; border-top: 1px solid var(--rule); scroll-margin-top: 60px; }
.v2-section > h2 { margin: 0 0 4px; font-size: 22px; }
.v2-section > p.intro { margin: 0 0 18px; color: var(--ink-muted); font-size: 14px; max-width: 80ch; line-height: 1.55; }

.v2-scorecard {
    display: flex; flex-direction: column; gap: 4px;
    margin: 0 0 16px;
    padding: 10px 12px;
    border: 1px solid var(--rule); border-radius: 6px;
    background: color-mix(in srgb, var(--bg-page) 60%, transparent);
    font-family: var(--mono); font-size: 12px;
}
.v2-scorecard .sc-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.v2-scorecard .sc-label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--ink-muted); width: 52px; flex-shrink: 0; }
.v2-scorecard .sc-strip { display: flex; gap: 3px; }
.v2-scorecard .sc-cell { padding: 2px 5px; border-radius: 3px; font-size: 10px; }
.v2-scorecard .sc-cell.win-l { background: rgba(72, 158, 116, 0.30); color: var(--ink); }
.v2-scorecard .sc-cell.win-r { background: rgba(86, 132, 191, 0.32); color: var(--ink); }
.v2-scorecard .sc-cell.win-tie { background: rgba(120, 120, 120, 0.25); color: var(--ink-muted); }

.v2-charts-stack { display: grid; gap: 12px; }
.v2-charts-stack .sample-chart { width: 100%; height: auto; }
.v2-charts-stack .theme-divider {
    margin: 16px 0 4px;
    padding-top: 12px;
    border-top: 1px solid var(--rule);
    font-size: 12px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--ink);
    font-weight: 600;
}
.v2-charts-stack .theme-divider:first-child {
    margin-top: 0; padding-top: 0; border-top: none;
}

.v2-toc {
    position: sticky; top: 0; z-index: 50;
    padding: 10px 28px; border-bottom: 1px solid var(--rule);
    background: color-mix(in srgb, var(--bg-page) 92%, transparent);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    display: flex; align-items: center; gap: 16px;
}
.v2-toc h2 { margin: 0; font-size: 11px; color: var(--ink-muted); text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; flex-shrink: 0; }
.v2-toc ol { margin: 0; padding: 0; list-style: none; display: flex; gap: 14px; flex-wrap: wrap; font-size: 12px; }
.v2-toc a { color: var(--ink); text-decoration: none; border-bottom: 1px dashed var(--ink-muted); }
.v2-toc a:hover { border-bottom-style: solid; }

@media (max-width: 900px) {
    .v2-pair-row { grid-template-columns: 1fr; }
}
"""


def h(s: str) -> str:
    return html.escape(str(s), quote=True)


def _swatch_text_color(hx: str) -> str:
    r, g, b = hex_to_rgb1(hx)
    luma = 0.299 * r + 0.587 * g + 0.114 * b
    return "#111" if luma > 0.55 else "#FAF8F1"


def render_palette_strip(hexes: list[str]) -> str:
    cells = "".join(
        f'<div class="swatch" style="background:{hx};color:{_swatch_text_color(hx)}">{h(hx)}</div>'
        for hx in hexes
    )
    return f'<div class="v2-palette-strip">{cells}</div>'


def _classify_per_n(val: float) -> str:
    if val >= 15.0:
        return "good"
    if val >= 10.0:
        return "warn"
    return "bad"


def render_scorecard(
    left_name: str, left_cvd: list[float], left_norm: list[float],
    right_name: str, right_cvd: list[float], right_norm: list[float],
) -> str:
    """Compact win-per-n strip for one sorting. Two rows: CVD and
    normal-vision, each showing per-n winner as a coloured n=k chip."""
    def winners(a: list[float], b: list[float]) -> list[str]:
        out: list[str] = []
        for av, bv in zip(a, b):
            if abs(av - bv) < 0.05:  # treat ≤0.05 ΔE as a tie
                out.append("=")
            elif av > bv:
                out.append("L")
            else:
                out.append("R")
        return out

    def strip(labels: list[str]) -> str:
        cells = []
        for i, lab in enumerate(labels):
            cls = {"L": "win-l", "R": "win-r", "=": "win-tie"}[lab]
            cells.append(f'<span class="sc-cell {cls}">n={i + 2}</span>')
        return "".join(cells)

    return (
        '<div class="v2-scorecard">'
        '<div class="sc-row">'
        '<span class="sc-label">CVD</span>'
        f'<div class="sc-strip">{strip(winners(left_cvd, right_cvd))}</div>'
        '</div>'
        '<div class="sc-row">'
        '<span class="sc-label">normal</span>'
        f'<div class="sc-strip">{strip(winners(left_norm, right_norm))}</div>'
        '</div>'
        '</div>'
    )


def render_per_n_table(values_cvd: list[float], values_normal: list[float]) -> str:
    headers = "".join(f"<th>n={i + 2}</th>" for i in range(len(values_cvd)))
    cvd_cells = "".join(
        f'<td class="{_classify_per_n(v)}">{v:.2f}</td>' for v in values_cvd
    )
    normal_cells = "".join(
        f'<td class="{_classify_per_n(v)}">{v:.2f}</td>' for v in values_normal
    )
    return (
        '<table class="v2-pertable">'
        f"<thead><tr><th>worst-pair ΔE</th>{headers}</tr></thead>"
        "<tbody>"
        f"<tr><td>normal vision</td>{normal_cells}</tr>"
        f"<tr><td>under CVD (min)</td>{cvd_cells}</tr>"
        "</tbody>"
        "</table>"
    )


def render_pair_grid(
    items: list[tuple[str, list[str], list[float], list[float], str]]
) -> str:
    """Column-major grid: row 1 = headings, row 2 = intros, row 3 = strips,
    row 4 = tables. Each row is filled left-then-right so corresponding items
    share the same grid-row and align vertically regardless of intro length."""
    headings = "".join(f'<h2 class="pg-head">{h(name)}</h2>' for name, *_ in items)
    intros = "".join(
        f'<p class="pg-intro">{h(blurb)}</p>' for _, _, _, _, blurb in items
    )
    strips = "".join(
        f"<div>{render_palette_strip(hx)}</div>" for _, hx, _, _, _ in items
    )
    tables = "".join(
        f"<div>{render_per_n_table(per_n_cvd, per_n_norm)}</div>"
        for _, _, per_n_cvd, per_n_norm, _ in items
    )
    return f'<div class="v2-pair-grid">{headings}{intros}{strips}{tables}</div>'


def render_sample_stocks(
    theme: dict[str, str], theme_label: str, series_hexes: Sequence[str]
) -> str:
    """Inline SVG stock-style time series — 4 random-walk paths normalised
    around a 100 baseline, each with a distinct drift. Tests how the first-4
    sorted picks read in a dense overlapping line context (typical financial
    visualisation: noisy daily ticks, all four crossing each other often)."""
    width, height = 460, 240
    margin_l, margin_r, margin_t, margin_b = 38, 22, 22, 26
    plot_w = width - margin_l - margin_r
    plot_h = height - margin_t - margin_b

    bg = theme["bg_page"]
    ink_muted = theme["ink_muted"]
    rule = theme.get("rule", "#DFDDD6")
    is_light = bg.upper().startswith("#F")
    grid = "rgba(26,26,23,0.15)" if is_light else "rgba(240,239,232,0.15)"

    n_points = 90
    # Per-series annualised-style drift + per-step vol. Picked deterministically
    # so the chart looks the same across runs and across the two palettes.
    series_specs = [
        (+0.18, 1.5),   # series 0 — moderate uptrend
        (-0.10, 1.2),   # series 1 — gentle decline
        (+0.05, 2.4),   # series 2 — flat-ish but volatile
        (-0.02, 1.0),   # series 3 — slightly down
    ]
    rnd = random.Random(7)
    series_values: list[list[float]] = []
    for drift, vol in series_specs[: len(series_hexes)]:
        v = 100.0
        path = [v]
        for _ in range(n_points - 1):
            step = drift + rnd.gauss(0, vol)
            v = max(40.0, v + step)  # floor so prices stay positive-ish
            path.append(v)
        series_values.append(path)

    # Normalise y to the combined min/max range, padded slightly.
    all_vals = [v for s in series_values for v in s]
    v_min, v_max = min(all_vals), max(all_vals)
    pad = (v_max - v_min) * 0.08 or 1.0
    y_lo = v_min - pad
    y_hi = v_max + pad

    grid_lines = "".join(
        f'<line x1="{margin_l}" y1="{margin_t + plot_h * f:.1f}" '
        f'x2="{margin_l + plot_w}" y2="{margin_t + plot_h * f:.1f}" '
        f'stroke="{grid}" stroke-width="1" />'
        for f in (0.25, 0.5, 0.75)
    )

    polylines: list[str] = []
    for i, path in enumerate(series_values):
        pts = []
        for j, val in enumerate(path):
            x = j / (n_points - 1)
            y = (val - y_lo) / (y_hi - y_lo)
            px = margin_l + x * plot_w
            py = margin_t + (1 - y) * plot_h
            pts.append(f"{px:.1f},{py:.1f}")
        polylines.append(
            f'<polyline points="{" ".join(pts)}" stroke="{series_hexes[i]}" '
            f'stroke-width="1.6" fill="none" stroke-linecap="round" '
            f'stroke-linejoin="round" />'
        )

    axes = (
        f'<line x1="{margin_l}" y1="{margin_t}" '
        f'x2="{margin_l}" y2="{margin_t + plot_h}" stroke="{rule}" stroke-width="1" />'
        f'<line x1="{margin_l}" y1="{margin_t + plot_h}" '
        f'x2="{margin_l + plot_w}" y2="{margin_t + plot_h}" stroke="{rule}" stroke-width="1" />'
    )

    # Price-axis ticks (a couple of round values inside the range)
    tick_count = 4
    tick_labels: list[str] = []
    for k in range(tick_count + 1):
        f = k / tick_count
        val = y_lo + (y_hi - y_lo) * (1 - f)
        ty = margin_t + plot_h * f + 3
        tick_labels.append(
            f'<text x="{margin_l - 4}" y="{ty:.1f}" fill="{ink_muted}" '
            f'font-size="9" text-anchor="end">{val:.0f}</text>'
        )

    label = (
        f'<text x="{margin_l}" y="{margin_t - 6}" fill="{ink_muted}" '
        f'font-size="10" text-anchor="start">{h(theme_label)} — stocks (first 4)</text>'
    )

    return (
        f'<svg viewBox="0 0 {width} {height}" class="sample-chart" '
        f'preserveAspectRatio="xMidYMid meet" '
        f'style="background:{bg};border:1px solid {rule};border-radius:6px">'
        f"{label}{grid_lines}{axes}{''.join(polylines)}{''.join(tick_labels)}"
        "</svg>"
    )


def render_sample_pie(
    theme: dict[str, str], theme_label: str, series_hexes: Sequence[str]
) -> str:
    """Inline SVG pie chart — 4 wedges with deliberately uneven sizes so each
    colour shows at a different arc length. Tests how the first-4 sorted
    picks read when they share boundaries directly (no axes, no whitespace
    between wedges other than a hair-thin bg-coloured stroke)."""
    width, height = 460, 240
    margin_l, margin_t = 36, 22

    bg = theme["bg_page"]
    ink_muted = theme["ink_muted"]
    rule = theme.get("rule", "#DFDDD6")

    series = list(series_hexes)
    fractions = [0.35, 0.27, 0.22, 0.16][: len(series)]
    total = sum(fractions) or 1.0
    fractions = [f / total for f in fractions]

    # Pie centred vertically below the title strip; radius bounded by the
    # smaller plot dimension so it stays within the SVG even on the
    # 460-wide / 240-tall canvas.
    cx = width / 2
    cy = margin_t + (height - margin_t - 12) / 2
    r = min((height - margin_t - 12) / 2 - 6, 92)

    wedges: list[str] = []
    start = -math.pi / 2  # start at 12 o'clock
    for i, frac in enumerate(fractions):
        end = start + frac * 2 * math.pi
        x1 = cx + r * math.cos(start)
        y1 = cy + r * math.sin(start)
        x2 = cx + r * math.cos(end)
        y2 = cy + r * math.sin(end)
        large_arc = 1 if frac > 0.5 else 0
        d = (
            f"M {cx:.2f} {cy:.2f} "
            f"L {x1:.2f} {y1:.2f} "
            f"A {r:.2f} {r:.2f} 0 {large_arc} 1 {x2:.2f} {y2:.2f} Z"
        )
        wedges.append(
            f'<path d="{d}" fill="{series[i]}" stroke="{bg}" stroke-width="1.5" />'
        )
        start = end

    label = (
        f'<text x="{margin_l}" y="{margin_t - 6}" fill="{ink_muted}" '
        f'font-size="10" text-anchor="start">{h(theme_label)} — pie (first 4)</text>'
    )

    return (
        f'<svg viewBox="0 0 {width} {height}" class="sample-chart" '
        f'preserveAspectRatio="xMidYMid meet" '
        f'style="background:{bg};border:1px solid {rule};border-radius:6px">'
        f"{label}{''.join(wedges)}"
        "</svg>"
    )


def render_overlap_scatter(
    theme: dict[str, str], theme_label: str, series_hexes: Sequence[str]
) -> str:
    """Scatter chart where each series has its own cluster near the plot
    perimeter, but with a wide enough Gaussian tail that the inner edges of
    all clusters meet and overlap in the middle. Tests how the palette reads
    at the edges (single colour visible cleanly) AND in the middle (multiple
    colours collide pixel-by-pixel). Z-order shuffled so no colour stays on
    top."""
    width, height = 460, 240
    margin_l, margin_r, margin_t, margin_b = 36, 18, 22, 26
    plot_w = width - margin_l - margin_r
    plot_h = height - margin_t - margin_b

    bg = theme["bg_page"]
    ink_muted = theme["ink_muted"]
    rule = theme.get("rule", "#DFDDD6")
    is_light = bg.upper().startswith("#F")
    grid = "rgba(26,26,23,0.15)" if is_light else "rgba(240,239,232,0.15)"

    rnd = random.Random(42)
    n_series = len(series_hexes)
    # Each colour contributes two Gaussian blobs:
    #   1. EDGE blob — its own dedicated cluster on the perimeter (tight σ so
    #      adjacent colours don't bleed into each other much).
    #   2. CENTER blob — a small mass at (0.5, 0.5) so all 8 colours mix in
    #      the middle (otherwise opposite colours never meet — only adjacent
    #      ones overlap, and the centre stays empty).
    # Cluster centres ring around an ellipse — radii sized to roughly account
    # for the chart's ~2:1 aspect so the visual ring looks circular on screen.
    r_x = 0.35
    r_y = 0.37
    sigma_edge_x = 0.060
    sigma_edge_y = 0.070
    sigma_center = 0.105
    n_edge = 16
    n_center = 12

    grid_lines = "".join(
        f'<line x1="{margin_l}" y1="{margin_t + plot_h * f:.1f}" '
        f'x2="{margin_l + plot_w}" y2="{margin_t + plot_h * f:.1f}" '
        f'stroke="{grid}" stroke-width="1" />'
        for f in (0.25, 0.5, 0.75)
    )

    dots: list[tuple[float, float, float, str]] = []
    for i, color in enumerate(series_hexes):
        # Start the ring at 12 o'clock so brand-green sits at the top in both
        # palettes — the eye can compare same-screen-position swatches across
        # vivid-8 and muted-8.
        theta = -math.pi / 2 + i * (2 * math.pi / n_series)
        edge_x = 0.5 + r_x * math.cos(theta)
        edge_y = 0.5 + r_y * math.sin(theta)

        # Edge blob
        for _ in range(n_edge):
            x = max(0.04, min(0.96, edge_x + rnd.gauss(0, sigma_edge_x)))
            y = max(0.04, min(0.96, edge_y + rnd.gauss(0, sigma_edge_y)))
            px = margin_l + x * plot_w
            py = margin_t + (1 - y) * plot_h
            dots.append((px, py, 3.4, color))

        # Center mix blob — same σ on both axes (ellipse not needed; we want a
        # round mass exactly at the middle).
        for _ in range(n_center):
            x = max(0.04, min(0.96, 0.5 + rnd.gauss(0, sigma_center)))
            y = max(0.04, min(0.96, 0.5 + rnd.gauss(0, sigma_center)))
            px = margin_l + x * plot_w
            py = margin_t + (1 - y) * plot_h
            dots.append((px, py, 3.4, color))

    # Shuffle so the z-order across colours is randomised — no single colour
    # permanently sits on top of the stack.
    rnd.shuffle(dots)
    dots_svg = "".join(
        f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r:.1f}" '
        f'fill="{color}" fill-opacity="0.78" />'
        for (px, py, r, color) in dots
    )

    axes = (
        f'<line x1="{margin_l}" y1="{margin_t}" '
        f'x2="{margin_l}" y2="{margin_t + plot_h}" stroke="{rule}" stroke-width="1" />'
        f'<line x1="{margin_l}" y1="{margin_t + plot_h}" '
        f'x2="{margin_l + plot_w}" y2="{margin_t + plot_h}" stroke="{rule}" stroke-width="1" />'
    )

    label = (
        f'<text x="{margin_l}" y="{margin_t - 6}" fill="{ink_muted}" '
        f'font-size="10" text-anchor="start">{h(theme_label)} — scatter (edge-clusters, centre-overlap)</text>'
    )

    return (
        f'<svg viewBox="0 0 {width} {height}" class="sample-chart" '
        f'preserveAspectRatio="xMidYMid meet" '
        f'style="background:{bg};border:1px solid {rule};border-radius:6px">'
        f"{label}{grid_lines}{axes}{dots_svg}"
        "</svg>"
    )


def _charts_stack(label: str, hexes: list[str]) -> str:
    """Per-cell vertical stack — first ALL light-theme charts, then ALL
    dark-theme charts (each block: lines / bars all-8 / pie first-4 /
    stocks first-4 / scatter centre-overlap)."""
    first_4 = hexes[:4]

    def block(theme: dict[str, str], theme_label: str) -> str:
        return (
            f'<h3 class="theme-divider">{h(theme_label)}</h3>'
            '<h3>lines</h3>'
            f'{render_sample_chart(theme, label, hexes)}'
            '<h3>bars (all 8)</h3>'
            f'{render_sample_bars(theme, label, hexes)}'
            '<h3>pie (first 4)</h3>'
            f'{render_sample_pie(theme, label, first_4)}'
            '<h3>stocks (first 4)</h3>'
            f'{render_sample_stocks(theme, label, first_4)}'
            '<h3>scatter (edge clusters, centre overlap)</h3>'
            f'{render_overlap_scatter(theme, label, hexes)}'
        )

    return (
        '<div class="v2-pair-cell v2-charts-stack">'
        f"{block(LIGHT_THEME_FULL, 'light theme')}"
        f"{block(DARK_THEME_FULL, 'dark theme')}"
        "</div>"
    )


def render_charts_pair(
    label_left: str, hexes_left: list[str], label_right: str, hexes_right: list[str]
) -> str:
    """2-col grid with the full chart-stack per palette."""
    return (
        '<div class="v2-pair-row">'
        f"{_charts_stack(label_left, hexes_left)}"
        f"{_charts_stack(label_right, hexes_right)}"
        "</div>"
    )


def render_sorting_section(
    section_id: str,
    title: str,
    intro: str,
    sorted_palettes: list[tuple[str, list[str], str]],
) -> str:
    # Top: column-major grid so headings/intros/strips/tables align by row
    # even when intros differ in line count.
    pair_items = [
        (name, hexes, measure_per_n(hexes), measure_per_n_normal(hexes), blurb)
        for name, hexes, blurb in sorted_palettes
    ]
    strips_row = render_pair_grid(pair_items)

    # Scorecard: per-n winner strips for CVD and normal vision.
    name_l, hexes_l, _ = sorted_palettes[0]
    name_r, hexes_r, _ = sorted_palettes[1]
    cvd_l = measure_per_n(hexes_l)
    cvd_r = measure_per_n(hexes_r)
    norm_l = measure_per_n_normal(hexes_l)
    norm_r = measure_per_n_normal(hexes_r)
    scorecard = render_scorecard(name_l, cvd_l, norm_l, name_r, cvd_r, norm_r)

    # Charts row: 2 columns, light stacked above dark per column.
    charts_row = render_charts_pair(name_l, hexes_l, name_r, hexes_r)

    return (
        f'<section class="v2-section" id="{h(section_id)}">'
        f"<h2>{h(title)}</h2>"
        f'<p class="intro">{h(intro)}</p>'
        f"{scorecard}"
        f"{strips_row}"
        f"{charts_row}"
        "</section>"
    )


def render_hero(palettes: list[tuple[str, str, list[str], str]]) -> str:
    # Column-major grid so head/intro/wheel/strip line up between palettes
    # even if intros differ in line count.
    heads = "".join(f'<h2 class="pg-head">{h(name)}</h2>' for name, *_ in palettes)
    intros = "".join(
        f'<p class="pg-intro">{h(blurb)}</p>' for _, blurb, _, _ in palettes
    )
    # Per-palette C corridor — kept light-touch so the wheel ring shows where
    # the algorithm's paper-ink band sat without dominating the disk.
    corridors = {"vivid-8": (22.0, 36.0), "muted-8": (24.0, 32.0)}
    wheels = "".join(
        '<div class="pg-wheel">'
        f'{v1.render_color_wheel(list(hexes), size_px=360, mode="large", chroma_corridor=corridors.get(name))}'
        "</div>"
        for name, _b, hexes, _a in palettes
    )
    # Hero strips sorted by hue (rainbow) — easiest side-by-side comparison
    # of which hue each palette places where.
    strips = "".join(
        f'<div>{render_palette_strip(sort_hue_order(list(hexes)))}</div>'
        for _n, _b, hexes, _a in palettes
    )
    return (
        '<header class="v2-hero">'
        "<h1>palette variants v2 — head-to-head</h1>"
        '<p class="subtitle">vivid-8 (was D3) vs muted-8 (was D1-8) under 4 different slot orderings. '
        "colours are identical between rows; only the position changes. each section is one sorting; "
        "compare per-n worst-pair ΔE under CVD against the live sample charts below it.</p>"
        '<div class="v2-pair-grid">'
        f"{heads}{intros}{wheels}{strips}"
        "</div>"
        "</header>"
    )


def render_toc(sortings: list[tuple[str, str, str, Callable]]) -> str:
    items = "".join(
        f'<li><a href="#{h(slug)}">{h(title)}</a></li>'
        for slug, title, _desc, _fn in sortings
    )
    return (
        '<nav class="v2-toc">'
        "<h2>sortings</h2>"
        f"<ol>{items}</ol>"
        "</nav>"
    )


def render_page(
    palettes: list[tuple[str, str, list[str], str]],
    sortings: list[tuple[str, str, str, Callable[[list[str]], list[str]]]],
) -> str:
    hero = render_hero(palettes)
    toc = render_toc(sortings)

    sections: list[str] = []
    for slug, title, desc, fn in sortings:
        sorted_pair: list[tuple[str, list[str], str]] = []
        for name, _blurb, hexes, _accent in palettes:
            sorted_hexes = fn(list(hexes))
            short = f"{name} after {title}"
            sorted_pair.append((name, sorted_hexes, short))
        sections.append(render_sorting_section(slug, title, desc, sorted_pair))

    return (
        "<!doctype html>"
        '<html lang="en"><head><meta charset="utf-8">'
        "<title>palette variants v2 — vivid-8 vs muted-8</title>"
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<style>{PAGE_CSS}{V2_CSS}</style>"
        "</head><body>"
        '<main class="page">'
        f"{hero}{toc}{''.join(sections)}"
        "</main>"
        f"<script>{PAGE_JS}</script>"
        "</body></html>"
    )


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------


DEFAULT_OUT_DIR = REPO_ROOT / "docs" / "reference" / "palette-variants-v2"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate palette variants v2")
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
    log = logging.getLogger("palette-variants-v2")

    args.out_dir.mkdir(parents=True, exist_ok=True)

    for name, _blurb, hexes, _accent in PALETTES:
        log.info("palette %s (%d hues)", name, len(hexes))
    for slug, title, _desc, fn in SORTINGS:
        log.info("sorting %s → %s", slug, title)
        for name, _blurb, hexes, _accent in PALETTES:
            sorted_h = fn(list(hexes))
            per_n = measure_per_n(sorted_h)
            log.info("  %s: %s  per-n=%s", name, " ".join(sorted_h), per_n)

    html_out = render_page(PALETTES, SORTINGS)
    out_path = args.out_dir / "index.html"
    out_path.write_text(html_out, encoding="utf-8")
    log.info("wrote %s (%.1f kB)", out_path, out_path.stat().st_size / 1024)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
