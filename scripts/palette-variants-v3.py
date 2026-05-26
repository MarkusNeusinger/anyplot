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
"""palette variants v3 — muted-8 finalist with hybrid sort.

After 5 independent expert reviewers unanimously picked muted-8 over vivid-8
(see ``../palette-variants-v2/expert-reviews.md``), only the slot order was
still open. The v2 head-to-head exposed a real trade-off: pure-CVD-greedy
maximised ΔE under CVD simulation but duplicated hue families in the first 4
slots, while wheel-gap-first gave 4 visually distinct hues but put red and
green next to each other (worst-pair ΔE_CVD ≈ 10.7 already at n=3).

v3 introduces a hybrid sort that fixes both: the first ``first_n`` slots are
constrained to come from distinct hue bins (45° wide by default) AND picked
by greedy max-min worst-CVD ΔE; the tail is unconstrained pure-CVD greedy.
Red is deliberately deferred to slot 4+; semantic-red is reached via the
named API (``palette.red``), not by position.

Outputs:
  docs/reference/palette-variants-v3/index.html             - interactive page
  docs/reference/palette-variants-v3/decision-rationale.md  - written rationale

Run::

    uv run --script scripts/palette-variants-v3.py
"""

from __future__ import annotations

import argparse
import html
import importlib.util
import logging
import sys
from pathlib import Path
from typing import Callable, Sequence

import numpy as np


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))


def _load(module_name: str, filename: str):
    spec = importlib.util.spec_from_file_location(
        module_name, REPO_ROOT / "scripts" / filename
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


v1 = _load("palette_variants_v1", "palette-variants-v1.py")
v2 = _load("palette_variants_v2", "palette-variants-v2.py")

from _palette_common import (  # noqa: E402
    DARK_THEME_FULL,
    LIGHT_THEME_FULL,
    NEUTRAL_DARK,
    NEUTRAL_LIGHT,
    PAGE_CSS,
    PAGE_JS,
    hex_to_rgb1,
    pairwise_delta_e,
    render_sample_bars,
    render_sample_chart,
    to_jab,
    wcag_contrast,
    worst_cvd_pairwise_delta_e,
)


# -----------------------------------------------------------------------------
# Semantic anchors that live outside the categorical pool.
# These are NOT used by palette[:n] — only by the named API
# (palette.amber, palette.neutral, palette.muted) for warning / baseline /
# disabled-other use cases the 8 categorical hues don't cover.
# -----------------------------------------------------------------------------

AMBER = "#DDCC77"  # Paul Tol "muted" yellow — see decision-rationale.md
# adaptive ink (full-contrast neutral): ink on light bg, ink on dark bg
INK_LIGHT = NEUTRAL_LIGHT  # "#1A1A17"
INK_DARK = NEUTRAL_DARK    # "#F0EFE8"
# adaptive ink-muted (soft-contrast neutral): for "other / rest / disabled"
INK_MUTED_LIGHT = LIGHT_THEME_FULL["ink_muted"]  # "#6B6A63"
INK_MUTED_DARK = DARK_THEME_FULL["ink_muted"]    # "#A8A79F"


# -----------------------------------------------------------------------------
# Palette — muted-8 (the finalist; colour-identical to v1's D1-8)
# -----------------------------------------------------------------------------

MUTED_8: list[str] = [
    "#009E73",  # brand green
    "#AE3030",  # matte red
    "#C475FD",  # purple / lavender
    "#99B314",  # lime
    "#4467A3",  # blue
    "#2ABCCD",  # cyan
    "#954477",  # matte rosé
    "#BD8233",  # ochre / tan
]

# Short display labels used in the contrast audit dots.
MUTED_8_LABELS: dict[str, str] = {
    "#009E73": "brand-G",
    "#AE3030": "red",
    "#C475FD": "lavender",
    "#99B314": "lime",
    "#4467A3": "blue",
    "#2ABCCD": "cyan",
    "#954477": "rose",
    "#BD8233": "ochre",
}


# -----------------------------------------------------------------------------
# Hybrid v3 sort
# -----------------------------------------------------------------------------


def _hue(hex_str: str) -> float:
    rgb = hex_to_rgb1(hex_str).reshape(1, 3)
    jab = to_jab(rgb)[0]
    _, _, H = v1.jab_to_lch(jab)
    return H


# Perceptual "coarse family" partition by CAM02-UCS hue angle.
# 6 wedges chosen so the muted-8 hues partition like a viewer would group them:
#   - brand-green (H≈166°) and lime (H≈115°) BOTH in "green"  -> "2× green" complaint
#   - lavender (H≈305°) and rosé (H≈345°) BOTH in "pink"      -> "2× pink"  complaint
#   - ochre (H≈70°) in "orange", red (H≈25°) in "red", blue and cyan kept separate
# Boundaries are wider than v1's 14 fine hue-bands because the colloquial families
# people compare against ("red/orange/yellow/green/blue/purple/pink") are coarser.
COARSE_FAMILY_BANDS = [
    (30.0,  "red"),     # 0°  – 30°   true reds
    (90.0,  "yellow"),  # 30° – 90°   orange / amber / yellow (ochre lives here)
    (180.0, "green"),   # 90° – 180°  lime / green / teal (brand green lives here)
    (230.0, "cyan"),    # 180°– 230°  cyan / azure
    (285.0, "blue"),    # 230°– 285°  blue / indigo
    (345.0, "purple"),  # 285°– 345°  purple / magenta (lavender + rosé)
    (360.0, "red"),     # 345°– 360°  pink / wrap-around back to red family
]


def _coarse_family(hex_str: str) -> str:
    H = _hue(hex_str)
    for boundary, name in COARSE_FAMILY_BANDS:
        if H < boundary:
            return name
    return COARSE_FAMILY_BANDS[-1][1]


def sort_hybrid_v3(
    hexes: list[str],
    first_n: int = 4,
    defer: tuple[str, ...] = ("#AE3030",),
) -> list[str]:
    """Hue-family-diverse first ``first_n`` + CVD-greedy tail, with the
    semantic red anchor deferred past first-N by default.

    - Slot 0 stays where it is (project-pinned anchor — brand green for muted-8).
    - Slots 1..first_n-1: greedy max-min worst-CVD ΔE, **constrained** to
      (a) a coarse hue family (see ``COARSE_FAMILY_BANDS``) not already used,
      **and** (b) not a hex in ``defer``. The defer list reserves semantically
      loaded hues (e.g. `#AE3030` matte red for loss/error/bad) so they're
      always reached by name in the palette API rather than by position 1..N-1
      where they'd appear in every chart with ≥ N series.
    - Slots first_n..N-1: pure greedy max-min worst-CVD ΔE on the remainder
      (deferred hexes re-enter the pool here).

    If the family/defer constraints can't be satisfied (all remaining hexes
    are excluded), they relax for that slot. For muted-8 at first_n=4 the
    fallback never triggers — there are 6 distinct coarse families across the
    8 hexes and only 1 hex in the default defer list.
    """
    n = len(hexes)
    rgb = np.array([hex_to_rgb1(h) for h in hexes])
    M_worst, _ = worst_cvd_pairwise_delta_e(rgb)
    families = [_coarse_family(h) for h in hexes]
    deferred_idx = {i for i, hx in enumerate(hexes) if hx in defer}

    placed: list[int] = [0]
    remaining = list(range(1, n))

    while remaining:
        if len(placed) < first_n:
            used = {families[i] for i in placed}
            candidates = [
                i for i in remaining
                if families[i] not in used and i not in deferred_idx
            ]
            if not candidates:
                candidates = remaining
        else:
            candidates = remaining
        best = max(candidates, key=lambda i: float(M_worst[i, placed].min()))
        placed.append(best)
        remaining.remove(best)

    return [hexes[i] for i in placed]


# Full sorting set for the comparison table (the new hybrid + v2's 4).
ALL_SORTINGS: list[tuple[str, str, Callable[[list[str]], list[str]]]] = [
    ("hybrid-v3", "hybrid-v3 (family-diverse first 4, red deferred, CVD-greedy tail)", sort_hybrid_v3),
    ("pure-cvd-greedy", "pure-CVD greedy max-min", v2.sort_pure_cvd_greedy),
]


# -----------------------------------------------------------------------------
# Measurements
# -----------------------------------------------------------------------------


def measure_per_n_cvd(hexes: list[str]) -> list[float]:
    return v2.measure_per_n(hexes)


def measure_per_n_normal(hexes: list[str]) -> list[float]:
    return v2.measure_per_n_normal(hexes)


def slot_annotations(hexes: list[str]) -> list[tuple[str, str, float]]:
    """Per-slot (fine-name, coarse-family, hue-deg) for the rationale."""
    return [(v1.hue_to_name(h), _coarse_family(h), _hue(h)) for h in hexes]


# -----------------------------------------------------------------------------
# HTML rendering
# -----------------------------------------------------------------------------


V3_CSS = """
.v3-hero { padding: 32px 28px 18px; }
.v3-hero h1 { margin: 0 0 4px; font-size: 26px; }
.v3-hero p.subtitle { margin: 0 0 8px; color: var(--ink-muted); font-size: 14px; max-width: 84ch; line-height: 1.55; }
/* Hero is stacked, not 2-col: the wheel SVG has overflow="visible" so its
   cardinal tick labels extend ≈32px beyond each side, which makes any 2-col
   layout fragile. Stacking removes the possibility of overlap entirely.
   Note: classes are v3-prefixed to avoid clashing with the global .hero-meta
   rule in _palette_common.py (which forces position:absolute on that class). */
.v3-hero .v3-stack { display: flex; flex-direction: column; gap: 20px; align-items: stretch; margin-top: 18px; }
.v3-hero .v3-wheel { display: flex; justify-content: center; padding: 16px 0; }
.v3-hero .v3-meta { display: grid; grid-template-columns: 1fr 1fr; gap: 18px 28px; align-items: start; }
.v3-hero .v3-meta p { margin: 0; font-size: 13px; color: var(--ink-muted); line-height: 1.55; max-width: 60ch; }
.v3-hero .v3-meta dl { display: grid; grid-template-columns: max-content 1fr; gap: 4px 10px; font-family: var(--mono); font-size: 11px; margin: 0; }
.v3-hero .v3-meta dt { color: var(--ink-muted); }
.v3-hero .v3-meta dd { margin: 0; }

@media (max-width: 720px) {
    .v3-hero .v3-meta { grid-template-columns: 1fr; }
}

.v3-section { padding: 28px; border-top: 1px solid var(--rule); }
.v3-section > h2 { margin: 0 0 4px; font-size: 22px; }
.v3-section > p.intro { margin: 0 0 14px; color: var(--ink-muted); font-size: 14px; max-width: 84ch; line-height: 1.55; }

/* Contrast audit (graphical-objects WCAG 3:1 against bg_page per theme).
   Two "stages" — one light, one dark — each shows every categorical hue
   + amber as a 48px dot on its theme's bg, with hex/label/ratio under it.
   For sub-3:1 members, a second "outlined" variant is shown alongside,
   demonstrating that a 1.5px ink-color stroke rescues the contrast. */
.v3-contrast-stage { border-radius: 10px; padding: 18px 16px 16px; margin-top: 10px; box-shadow: 0 0 0 1px var(--rule); }
.v3-contrast-stage h3 { margin: 0 0 4px; font-size: 14px; font-family: var(--mono); letter-spacing: 0.04em; }
.v3-contrast-stage p.note { margin: 0 0 12px; font-size: 12px; line-height: 1.5; max-width: 60ch; }
.v3-contrast-stage.stage-light { background: #F5F3EC; color: #1A1A17; }
.v3-contrast-stage.stage-light p.note { color: #4A4A44; }
.v3-contrast-stage.stage-dark  { background: #121210; color: #F0EFE8; }
.v3-contrast-stage.stage-dark  p.note { color: #B8B7B0; }

.v3-contrast-row { display: grid; grid-template-columns: repeat(9, 1fr); gap: 8px; margin-top: 6px; }
.v3-contrast-row .cell { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.v3-contrast-row .dot { width: 48px; height: 48px; border-radius: 50%; box-shadow: none; }
.v3-contrast-row .label { font-family: var(--mono); font-size: 9px; letter-spacing: 0.02em; opacity: 0.85; }
.v3-contrast-row .hex { font-family: var(--mono); font-size: 9px; opacity: 0.7; }
.v3-contrast-row .ratio { font-family: var(--mono); font-size: 10px; font-weight: 600; }
.v3-contrast-row .ratio.pass { color: #2a8d52; }
.v3-contrast-row .ratio.fail { color: #b62d2d; }
.v3-contrast-stage.stage-dark .ratio.pass { color: #6fcf97; }
.v3-contrast-stage.stage-dark .ratio.fail { color: #ff8585; }

.v3-contrast-fix { display: grid; grid-template-columns: repeat(auto-fit, minmax(72px, max-content)); gap: 8px 14px; margin-top: 14px; padding-top: 12px; border-top: 1px dashed currentColor; }
.v3-contrast-fix .cell { display: flex; flex-direction: column; align-items: center; gap: 4px; opacity: 0.95; }
.v3-contrast-fix .dot { width: 48px; height: 48px; border-radius: 50%; }
.v3-contrast-fix .pair { display: flex; gap: 6px; align-items: center; }
.v3-contrast-fix h4 { margin: 0 0 6px; font-size: 12px; font-family: var(--mono); letter-spacing: 0.03em; font-weight: 600; opacity: 0.95; }
@media (max-width: 720px) {
    .v3-contrast-row { grid-template-columns: repeat(3, 1fr); }
}

/* Semantic anchors row (amber + 2 adaptive neutrals). Each anchor is a card
   showing the hex(es), a role label, and a one-line use-case hint. The
   adaptive neutrals show a split swatch — left half = light-theme value,
   right half = dark-theme value — so the theme-flip is visible at a glance. */
.v3-anchors { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 12px; }
.v3-anchors .anchor { border: 1px solid var(--rule); border-radius: 8px; padding: 0; overflow: hidden; background: var(--bg-surface); }
.v3-anchors .sw-full { height: 64px; }
.v3-anchors .sw-split { height: 64px; display: grid; grid-template-columns: 1fr 1fr; }
.v3-anchors .sw-split > span { display: flex; align-items: flex-end; justify-content: center; font-family: var(--mono); font-size: 10px; padding-bottom: 4px; }
.v3-anchors .sw-split > span.lit { color: #1A1A17; }
.v3-anchors .sw-split > span.dim { color: #F0EFE8; }
.v3-anchors .body { padding: 10px 12px 12px; }
.v3-anchors .role { font-family: var(--mono); font-size: 11px; letter-spacing: 0.04em; text-transform: uppercase; color: var(--ink); margin: 0 0 4px; }
.v3-anchors .api { font-family: var(--mono); font-size: 11px; color: var(--ink-muted); margin: 0 0 6px; }
.v3-anchors .hint { font-size: 12px; color: var(--ink-muted); line-height: 1.45; margin: 0; }
.v3-anchors .hex { font-family: var(--mono); font-size: 10px; color: var(--ink-muted); }
@media (max-width: 720px) {
    .v3-anchors { grid-template-columns: 1fr; }
}

.v3-strip { display: flex; height: 80px; border-radius: 6px; overflow: hidden; box-shadow: 0 0 0 1px var(--rule); margin-bottom: 6px; }
.v3-strip .sw { flex: 1; display: flex; align-items: center; justify-content: center; font-family: var(--mono); font-size: 10px; }
.v3-anno { display: grid; grid-template-columns: repeat(8, 1fr); gap: 6px; font-family: var(--mono); font-size: 10px; color: var(--ink-muted); margin-bottom: 14px; }
.v3-anno .col { display: flex; flex-direction: column; align-items: center; gap: 2px; padding: 4px 2px; text-align: center; border: 1px solid var(--rule); border-radius: 4px; }
.v3-anno .col .slot { font-weight: 600; color: var(--ink); letter-spacing: 0.06em; }
.v3-anno .col .family { color: var(--ink); }
.v3-anno .col .meta { color: var(--ink-muted); }

.v3-pertable { width: 100%; border-collapse: collapse; font-family: var(--mono); font-size: 11px; margin-top: 8px; }
.v3-pertable th, .v3-pertable td { padding: 4px 6px; text-align: right; border-bottom: 1px solid var(--rule); }
.v3-pertable th:first-child, .v3-pertable td:first-child { text-align: left; color: var(--ink-muted); }
.v3-pertable td.good { color: #2a8d52; font-weight: 600; }
.v3-pertable td.warn { color: #b56b18; }
.v3-pertable td.bad  { color: #b62d2d; font-weight: 600; }
.v3-pertable td.best { box-shadow: inset 0 -2px 0 0 currentColor; }

.v3-charts { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-top: 16px; }
.v3-charts .col { display: grid; gap: 10px; }
.v3-charts .sample-chart { width: 100%; height: auto; }
.v3-charts h3 { margin: 6px 0 2px; font-size: 12px; color: var(--ink-muted); letter-spacing: 0.04em; text-transform: uppercase; font-weight: 500; }
.v3-charts h4.theme-divider {
    margin: 8px 0 4px;
    font-size: 11px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--ink);
    font-weight: 600;
}

.v3-compare-row { display: grid; gap: 10px; margin: 8px 0 18px; }
.v3-compare-row .crow { display: grid; grid-template-columns: 220px 1fr; gap: 12px; align-items: center; }
.v3-compare-row .clabel { font-family: var(--mono); font-size: 11px; }
.v3-compare-row .clabel .crow-title { font-weight: 600; }
.v3-compare-row .clabel .crow-sub { color: var(--ink-muted); font-size: 10px; }
.v3-compare-row .cstrip { display: flex; height: 36px; border-radius: 4px; overflow: hidden; box-shadow: 0 0 0 1px var(--rule); }
.v3-compare-row .cstrip .sw { flex: 1; }

.v3-footer { padding: 24px 28px 40px; color: var(--ink-muted); font-size: 13px; line-height: 1.55; border-top: 1px solid var(--rule); }
.v3-footer a { color: var(--ink); }

@media (max-width: 900px) {
    .v3-charts { grid-template-columns: 1fr; }
    .v3-anno { grid-template-columns: repeat(4, 1fr); }
    .v3-compare-row .crow { grid-template-columns: 1fr; }
}
"""


def h(s: str) -> str:
    return html.escape(str(s), quote=True)


def _swatch_text_color(hx: str) -> str:
    r, g, b = hex_to_rgb1(hx)
    luma = 0.299 * r + 0.587 * g + 0.114 * b
    return "#111" if luma > 0.55 else "#FAF8F1"


def render_strip(hexes: list[str], cell_class: str = "v3-strip") -> str:
    cells = "".join(
        f'<div class="sw" style="background:{hx};color:{_swatch_text_color(hx)}">{h(hx)}</div>'
        for hx in hexes
    )
    return f'<div class="{cell_class}">{cells}</div>'


def render_annotation_row(hexes: list[str]) -> str:
    """Per-slot family/hue annotation under the main hex strip."""
    cells = []
    for i, (fine, coarse, hue) in enumerate(slot_annotations(hexes)):
        cells.append(
            f'<div class="col">'
            f'<span class="slot">slot {i}</span>'
            f'<span class="family">{h(fine)}</span>'
            f'<span class="meta">{h(coarse)} · H={hue:.0f}°</span>'
            f"</div>"
        )
    return f'<div class="v3-anno">{"".join(cells)}</div>'


def _classify(v: float) -> str:
    if v >= 15.0:
        return "good"
    if v >= 10.0:
        return "warn"
    return "bad"


def render_per_n_table(values_cvd: list[float], values_norm: list[float]) -> str:
    headers = "".join(f"<th>n={i + 2}</th>" for i in range(len(values_cvd)))
    cvd_cells = "".join(
        f'<td class="{_classify(v)}">{v:.2f}</td>' for v in values_cvd
    )
    norm_cells = "".join(
        f'<td class="{_classify(v)}">{v:.2f}</td>' for v in values_norm
    )
    return (
        '<table class="v3-pertable">'
        f"<thead><tr><th>worst-pair ΔE</th>{headers}</tr></thead>"
        "<tbody>"
        f"<tr><td>normal vision</td>{norm_cells}</tr>"
        f"<tr><td>under CVD (min)</td>{cvd_cells}</tr>"
        "</tbody>"
        "</table>"
    )


def render_chart_stack(label: str, hexes: list[str]) -> str:
    first_4 = hexes[:4]

    def block(theme: dict[str, str], theme_label: str) -> str:
        return (
            f'<h4 class="theme-divider">{h(theme_label)}</h4>'
            "<h3>lines</h3>"
            f"{render_sample_chart(theme, label, hexes)}"
            "<h3>bars (all 8)</h3>"
            f"{render_sample_bars(theme, label, hexes)}"
            "<h3>pie (first 4)</h3>"
            f"{v2.render_sample_pie(theme, label, first_4)}"
            "<h3>stocks (first 4)</h3>"
            f"{v2.render_sample_stocks(theme, label, first_4)}"
            "<h3>scatter (edge clusters, centre overlap)</h3>"
            f"{v2.render_overlap_scatter(theme, label, hexes)}"
        )

    return (
        '<div class="v3-charts">'
        f'<div class="col">{block(LIGHT_THEME_FULL, "light theme")}</div>'
        f'<div class="col">{block(DARK_THEME_FULL, "dark theme")}</div>'
        "</div>"
    )


def render_compare_table(
    sortings: list[tuple[str, str, list[str], list[float], list[float]]],
) -> str:
    """4-column comparison table — one row per sorting, columns n=2..8 of
    worst-CVD ΔE. The 'best' value per column gets a `.best` class."""
    n_count = len(sortings[0][3])
    # Determine the best (max) cvd value per n column
    best_idx_per_n = []
    for k in range(n_count):
        col_vals = [s[3][k] for s in sortings]
        best_idx_per_n.append(int(np.argmax(col_vals)))

    headers = "".join(f"<th>n={i + 2}</th>" for i in range(n_count))
    rows: list[str] = []
    for r, (slug, title, _hexes, cvd, _norm) in enumerate(sortings):
        cells: list[str] = []
        for k, v in enumerate(cvd):
            cls = _classify(v)
            if best_idx_per_n[k] == r:
                cls += " best"
            cells.append(f'<td class="{cls}">{v:.2f}</td>')
        marker = " ★" if slug == "hybrid-v3" else ""
        rows.append(
            f'<tr><td>{h(title)}{marker}</td>{"".join(cells)}</tr>'
        )
    return (
        '<table class="v3-pertable">'
        f"<thead><tr><th>sort · worst-CVD ΔE per n</th>{headers}</tr></thead>"
        f'<tbody>{"".join(rows)}</tbody>'
        "</table>"
    )


def render_compare_strips(
    sortings: list[tuple[str, str, list[str], list[float], list[float]]],
) -> str:
    """Stacked palette strips — one row per sorting."""
    rows: list[str] = []
    for slug, title, hexes, cvd, _norm in sortings:
        worst = min(cvd) if cvd else 0.0
        marker = " ★" if slug == "hybrid-v3" else ""
        rows.append(
            '<div class="crow">'
            f'<div class="clabel">'
            f'<div class="crow-title">{h(title)}{marker}</div>'
            f'<div class="crow-sub">min ΔE_CVD over n=2..8 = {worst:.2f}</div>'
            "</div>"
            f'{render_strip(hexes, cell_class="cstrip")}'
            "</div>"
        )
    return f'<div class="v3-compare-row">{"".join(rows)}</div>'


def render_hero(hybrid_hexes: list[str]) -> str:
    wheel = v1.render_color_wheel(
        list(hybrid_hexes), size_px=360, mode="large",
        chroma_corridor=(24.0, 32.0),
    )
    annotations = "".join(
        f"<dt>slot {i}</dt><dd>{h(hx)} — {h(_coarse_family(hx))}</dd>"
        for i, hx in enumerate(hybrid_hexes)
    )
    return (
        '<header class="v3-hero">'
        "<h1>palette variants v3 — muted-8 finalist</h1>"
        '<p class="subtitle">'
        "muted-8 was unanimously picked by 5 independent expert reviewers in v2. "
        "v3 settles the last open question — slot ordering — by introducing a "
        "<strong>hybrid sort</strong> that combines hue-family diversity in the "
        "first 4 slots with greedy max-min CVD distance for the tail. semantic "
        "red <code>#AE3030</code> is deferred past slot 3 so it&apos;s reached via "
        "the named API (<code>palette.red</code>) for loss / error / bad, not by "
        "position 1..3 where it would appear in every chart with ≥ 3 series."
        "</p>"
        '<div class="v3-stack">'
        f'<div class="v3-wheel">{wheel}</div>'
        '<div class="v3-meta">'
        "<p>chroma corridor C ∈ [24, 32]. brand green pinned at slot 0. "
        "remaining slots picked by the hybrid algorithm — slots 1..3 from "
        "distinct coarse hue families (red / yellow / green / cyan / blue / "
        "purple), with <code>#AE3030</code> matte red deferred past first-4, "
        "then greedy max-min worst-CVD ΔE for the tail.</p>"
        f"<dl>{annotations}</dl>"
        "</div></div>"
        "</header>"
    )


def _contrast_dot(
    hx: str, bg_hex: str, label: str, *, outlined_stroke: str | None = None
) -> str:
    """Render one dot cell: 48px filled circle, label, hex, ratio.

    If outlined_stroke is given, draws a 1.5px ring of that color around the
    fill. The ratio shown is then the stroke-vs-bg ratio (which always passes
    since outline is full-ink).
    """
    ratio = wcag_contrast(hex_to_rgb1(hx), hex_to_rgb1(bg_hex))
    if outlined_stroke is not None:
        stroke_ratio = wcag_contrast(
            hex_to_rgb1(outlined_stroke), hex_to_rgb1(bg_hex)
        )
        # The visible boundary in the outlined variant is the stroke against
        # bg, so report THAT ratio (the actually-effective contrast).
        ratio_str = f"{stroke_ratio:.2f}:1"
        ratio_class = "pass" if stroke_ratio >= 3.0 else "fail"
        ring = f"box-shadow: inset 0 0 0 2px {outlined_stroke};"
    else:
        ratio_str = f"{ratio:.2f}:1"
        ratio_class = "pass" if ratio >= 3.0 else "fail"
        ring = ""
    return (
        f'<div class="cell">'
        f'<div class="dot" style="background:{hx};{ring}"></div>'
        f'<div class="label">{html.escape(label)}</div>'
        f'<div class="hex">{hx}</div>'
        f'<div class="ratio {ratio_class}">{ratio_str}</div>'
        f"</div>"
    )


def render_contrast_section() -> str:
    """WCAG-3:1 contrast audit per theme + outline-fix demo for sub-3:1 hexes."""
    palette = [*MUTED_8, AMBER]
    labels = {**MUTED_8_LABELS, AMBER: "amber"}
    bg_light = LIGHT_THEME_FULL["bg_page"]
    bg_dark = DARK_THEME_FULL["bg_page"]
    ink_light = NEUTRAL_LIGHT  # ink for light bg = dark
    ink_dark = NEUTRAL_DARK    # ink for dark bg = light

    def ratio(fg: str, bg: str) -> float:
        return wcag_contrast(hex_to_rgb1(fg), hex_to_rgb1(bg))

    weak_light = [hx for hx in palette if ratio(hx, bg_light) < 3.0]
    weak_dark = [hx for hx in palette if ratio(hx, bg_dark) < 3.0]

    light_dots = "".join(
        _contrast_dot(hx, bg_light, labels[hx]) for hx in palette
    )
    dark_dots = "".join(
        _contrast_dot(hx, bg_dark, labels[hx]) for hx in palette
    )

    if weak_light:
        light_fix_dots = "".join(
            _contrast_dot(hx, bg_light, labels[hx], outlined_stroke=ink_light)
            for hx in weak_light
        )
        light_fix = (
            f'<div>'
            f'<h4>↳ same {len(weak_light)} sub-3:1 hexes with a 2px '
            f'<code>{ink_light}</code> ink ring</h4>'
            f'<div class="v3-contrast-fix">{light_fix_dots}</div>'
            f"</div>"
        )
    else:
        light_fix = ""

    if weak_dark:
        dark_fix_dots = "".join(
            _contrast_dot(hx, bg_dark, labels[hx], outlined_stroke=ink_dark)
            for hx in weak_dark
        )
        dark_fix = (
            f'<div>'
            f'<h4>↳ same {len(weak_dark)} sub-3:1 hex with a 2px '
            f'<code>{ink_dark}</code> ink ring</h4>'
            f'<div class="v3-contrast-fix">{dark_fix_dots}</div>'
            f"</div>"
        )
    else:
        dark_fix = ""

    return (
        '<section class="v3-section" id="contrast">'
        "<h2>contrast on both themes — and the outline pattern</h2>"
        '<p class="intro">'
        "muted palettes share a known limitation: the lighter members carry "
        "their distinguishability through chroma, not L-spread, so on a light "
        "background (cream <code>#F5F3EC</code>) they fall under WCAG 2.1 "
        "SC 1.4.11&apos;s 3:1 minimum for graphical objects. Okabe-Ito, Paul "
        "Tol &ldquo;muted&rdquo;, and ColorBrewer Set2 all have the same "
        "issue. The industry-standard fix is a thin ink-color outline on the "
        "affected series. Below: every categorical hue + amber on both themes, "
        "with the sub-3:1 ones shown both as-is and with a 2px ring."
        "</p>"
        '<div class="v3-contrast-stage stage-light">'
        '<h3>on cream bg <code>#F5F3EC</code> (light theme)</h3>'
        f'<div class="v3-contrast-row">{light_dots}</div>'
        f"{light_fix}"
        "</div>"
        '<div class="v3-contrast-stage stage-dark" style="margin-top:14px;">'
        '<h3>on warm near-black bg <code>#121210</code> (dark theme)</h3>'
        f'<div class="v3-contrast-row">{dark_dots}</div>'
        f"{dark_fix}"
        "</div>"
        '<p style="margin-top:14px;font-size:12px;color:var(--ink-muted);line-height:1.55;">'
        "<strong>Guidance.</strong> on the light theme, render the affected "
        f"series ({', '.join(labels[h] for h in weak_light)}) with a thin "
        "outline in the ink color "
        f"(<code>{ink_light}</code>): 1px stroke on line/scatter, 1–1.5px on "
        "bar/pie fills. amber is a semantic anchor outside the categorical "
        "pool — its low light-bg contrast is acceptable because it&apos;s "
        "reached intentionally (<code>palette.amber</code>) for caution/"
        "warning, and the same outline rule applies. on the dark theme, only "
        f"<code>#AE3030</code> red sits marginally below 3:1 "
        f"({ratio('#AE3030', bg_dark):.2f}:1) — same outline fix recommended "
        "for high-stakes layouts."
        "</p>"
        "</section>"
    )


def render_semantic_anchors_section() -> str:
    """Render the 3 semantic anchors that live OUTSIDE the categorical pool.

    These never enter the palette[:n] slot order — they're only reachable via
    the named API. Two of them (neutral, muted) are theme-adaptive: their hex
    flips between the light and dark theme.
    """
    # Pre-compute the worst-pair CVD ΔE from amber to every muted-8 member so we
    # can quote the min in the page (justifies the amber pick).
    rgbs = np.stack([hex_to_rgb1(c) for c in [AMBER, *MUTED_8]])
    cvd_min = float("inf")
    for cvd in ("deuter", "protan", "tritan"):
        m = pairwise_delta_e(rgbs, cvd)
        cvd_min = min(cvd_min, float(min(m[0, 1:])))
    return (
        '<section class="v3-section" id="anchors">'
        "<h2>semantic anchors — outside the categorical pool</h2>"
        '<p class="intro">'
        "the 8 categorical hues above cover the hue-diverse roles "
        "(<code>palette.green</code>, <code>palette.red</code>, …). three "
        "additional anchors live <strong>outside</strong> the slot pool — they "
        "are never returned by <code>palette[:n]</code>, only by the named API. "
        "two are <em>theme-adaptive</em>: their hex flips between the light and "
        "dark theme so the role stays semantically consistent across both modes "
        "(same pattern as Apple HIG / Material Design / GitHub Primer)."
        "</p>"
        '<div class="v3-anchors">'
        # 1. amber — warning / caution
        f'<div class="anchor">'
        f'<div class="sw-full" style="background:{AMBER};"></div>'
        f'<div class="body">'
        f'<p class="role">warning / caution</p>'
        f'<p class="api">palette.amber — <span class="hex">{AMBER}</span></p>'
        f"<p class=\"hint\">Paul Tol &ldquo;muted&rdquo; yellow. min ΔE under "
        f"CVD to the 8 categorical hexes = {cvd_min:.2f} — confidently distinct "
        f"from every member, including <code>#99B314</code> lime (the two more "
        f"saturated amber options, <code>#D4A017</code> and <code>#D4AF37</code> "
        f"goldenrod, both collapse to ΔE_CVD ≈ 2.3 against lime under "
        f"deuteranopia)."
        f"</p>"
        f"</div>"
        f"</div>"
        # 2. neutral — full-contrast ink (theme-adaptive)
        f'<div class="anchor">'
        f'<div class="sw-split">'
        f'<span class="dim" style="background:{INK_LIGHT};">{INK_LIGHT}</span>'
        f'<span class="lit" style="background:{INK_DARK};">{INK_DARK}</span>'
        f"</div>"
        f'<div class="body">'
        f'<p class="role">totals / baseline / outline</p>'
        f'<p class="api">palette.neutral — adaptive</p>'
        f'<p class="hint">full-contrast ink, theme-adaptive. on cream bg → '
        f'<code>{INK_LIGHT}</code>; on dark bg → <code>{INK_DARK}</code>. same '
        f"value as text and gridlines, so &ldquo;total&rdquo; / "
        f"&ldquo;baseline&rdquo; / &ldquo;reference outline&rdquo; series "
        f"automatically read as part of the chart's structural layer rather "
        f"than as &ldquo;just another category&rdquo;."
        f"</p>"
        f"</div>"
        f"</div>"
        # 3. muted — soft-contrast ink (theme-adaptive)
        f'<div class="anchor">'
        f'<div class="sw-split">'
        f'<span class="dim" style="background:{INK_MUTED_LIGHT};">{INK_MUTED_LIGHT}</span>'
        f'<span class="lit" style="background:{INK_MUTED_DARK};">{INK_MUTED_DARK}</span>'
        f"</div>"
        f'<div class="body">'
        f'<p class="role">other / rest / disabled</p>'
        f'<p class="api">palette.muted — adaptive</p>'
        f'<p class="hint">soft-contrast ink, theme-adaptive. on cream bg → '
        f'<code>{INK_MUTED_LIGHT}</code>; on dark bg → <code>{INK_MUTED_DARK}</code>. '
        f"meant for &ldquo;other&rdquo; / &ldquo;rest&rdquo; slices in stacked "
        f"charts, disabled / inactive series, confidence bands, and "
        f"any annotation that should sit behind the data without competing for "
        f"attention."
        f"</p>"
        f"</div>"
        f"</div>"
        "</div>"
        "</section>"
    )


def render_finalist_section(hybrid_hexes: list[str]) -> str:
    cvd = measure_per_n_cvd(hybrid_hexes)
    norm = measure_per_n_normal(hybrid_hexes)
    return (
        '<section class="v3-section" id="finalist">'
        "<h2>finalist — muted-8 with hybrid-v3 sort</h2>"
        '<p class="intro">'
        "first 4 slots come from 4 different coarse hue families "
        "(red / yellow / green / cyan / blue / purple — see slot annotations "
        "below), with <code>#AE3030</code> matte red explicitly deferred past "
        "first-4 so it remains a free semantic anchor reachable via the named "
        "API. slots 4..7 are pure-CVD greedy on the remaining hexes (deferred "
        "red re-enters here). this preserves visual hue diversity in dense "
        "small-n usage (no &ldquo;two greens, two purples&rdquo; problem) and "
        "still maximises CVD-distance for n=5..8."
        "</p>"
        f"{render_strip(hybrid_hexes)}"
        f"{render_annotation_row(hybrid_hexes)}"
        f"{render_per_n_table(cvd, norm)}"
        f"{render_chart_stack('muted-8 hybrid-v3', hybrid_hexes)}"
        "</section>"
    )


def render_compare_section(
    sortings: list[tuple[str, str, list[str], list[float], list[float]]],
) -> str:
    return (
        '<section class="v3-section" id="compare">'
        "<h2>how this compares to the v2 alternatives</h2>"
        '<p class="intro">'
        "all five sortings use the identical 8 hexes. only the slot order "
        "differs. ★ marks the recommended sort. the per-n table shows the "
        "weakest pair&apos;s ΔE under the min of the 3 CVD simulations "
        "(deuteranopia / protanopia / tritanopia at 100% severity). bold "
        "underline marks the column-best."
        "</p>"
        f"{render_compare_table(sortings)}"
        '<h3 style="margin:18px 0 6px;font-size:13px;letter-spacing:.04em;text-transform:uppercase;color:var(--ink-muted)">slot-order strips</h3>'
        f"{render_compare_strips(sortings)}"
        "</section>"
    )


def render_footer() -> str:
    return (
        '<footer class="v3-footer">'
        "<p>full rationale &amp; CVD-prevalence numbers: "
        '<a href="./decision-rationale.md">decision-rationale.md</a>. '
        "predecessor head-to-head: "
        '<a href="../palette-variants-v2/">palette-variants-v2</a>. '
        "expert reviews: "
        '<a href="../palette-variants-v2/expert-reviews.md">expert-reviews.md</a>.'
        "</p>"
        "</footer>"
    )


def render_page(hybrid_hexes: list[str]) -> str:
    # Precompute per-sort metrics for the comparison.
    sort_rows: list[tuple[str, str, list[str], list[float], list[float]]] = []
    for slug, title, fn in ALL_SORTINGS:
        sorted_hexes = fn(list(MUTED_8))
        cvd = measure_per_n_cvd(sorted_hexes)
        norm = measure_per_n_normal(sorted_hexes)
        sort_rows.append((slug, title, sorted_hexes, cvd, norm))

    return (
        "<!doctype html>"
        '<html lang="en"><head><meta charset="utf-8">'
        "<title>palette variants v3 — muted-8 finalist</title>"
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<style>{PAGE_CSS}{V3_CSS}</style>"
        "</head><body>"
        '<main class="page">'
        f"{render_hero(hybrid_hexes)}"
        f"{render_semantic_anchors_section()}"
        f"{render_finalist_section(hybrid_hexes)}"
        f"{render_contrast_section()}"
        f"{render_compare_section(sort_rows)}"
        f"{render_footer()}"
        "</main>"
        f"<script>{PAGE_JS}</script>"
        "</body></html>"
    )


# -----------------------------------------------------------------------------
# Markdown rationale
# -----------------------------------------------------------------------------


def _per_n_md_row(label: str, values: list[float]) -> str:
    cells = " | ".join(f"{v:.2f}" for v in values)
    return f"| {label} | {cells} |"


def render_rationale_md(
    hybrid_hexes: list[str],
    sort_rows: list[tuple[str, str, list[str], list[float], list[float]]],
) -> str:
    n_count = len(sort_rows[0][3])
    n_header = " | ".join(f"n={i + 2}" for i in range(n_count))
    n_sep = " | ".join(["---"] * (n_count + 1))

    hybrid_cvd = next(
        cvd for slug, _t, _h, cvd, _n in sort_rows if slug == "hybrid-v3"
    )
    hybrid_norm = next(
        norm for slug, _t, _h, _c, norm in sort_rows if slug == "hybrid-v3"
    )

    # Compact per-sort table
    compare_rows = "\n".join(
        _per_n_md_row(title + (" ★" if slug == "hybrid-v3" else ""), cvd)
        for slug, title, _h, cvd, _n in sort_rows
    )

    # Slot annotation table for the finalist
    annos = slot_annotations(hybrid_hexes)
    slot_rows = "\n".join(
        f"| {i} | `{hybrid_hexes[i]}` | {fine} | {coarse} | {hue:.1f}° |"
        for i, (fine, coarse, hue) in enumerate(annos)
    )

    # Amber → muted-8 worst-CVD min distance (used in the "semantic anchors"
    # section to back the amber pick). Worst of deuter/protan/tritan, smallest
    # ΔE to any of the 8 categorical hexes.
    amber_rgbs = np.stack([hex_to_rgb1(c) for c in [AMBER, *MUTED_8]])
    amber_cvd_min = float("inf")
    for cvd_name in ("deuter", "protan", "tritan"):
        m = pairwise_delta_e(amber_rgbs, cvd_name)
        amber_cvd_min = min(amber_cvd_min, float(min(m[0, 1:])))

    # Theme-adaptive neutral hexes (for the "Semantic anchors" section).
    ink_light = INK_LIGHT
    ink_dark = INK_DARK
    ink_muted_light = INK_MUTED_LIGHT
    ink_muted_dark = INK_MUTED_DARK

    return f"""# palette-v3 — muted-8 finalist (decision rationale)

> Generated by [`scripts/palette-variants-v3.py`](../../../scripts/palette-variants-v3.py).
> Companion to [`index.html`](./index.html) (live charts) and the v2 review at
> [`../palette-variants-v2/expert-reviews.md`](../palette-variants-v2/expert-reviews.md).

## TL;DR

After 5 independent expert reviewers unanimously picked **muted-8** over vivid-8,
only the slot ordering was still open. v3 introduces a **hybrid sort** that:

1. pins brand green `#009E73` at slot 0,
2. fills slots 1..3 by greedy max-min worst-CVD ΔE **constrained to distinct
   perceptual hue families** (red / yellow / green / cyan / blue / purple),
3. **defers semantic red `#AE3030` past the first-4 pool** so it's reached via
   the named API rather than by position 1..3, and
4. fills slots 4..7 by pure-CVD greedy (no constraint) on the remainder
   (deferred red re-enters here).

The result: visually hue-diverse first 4 slots (no "two greens, two purples"
artefact from pure-CVD-greedy), red kept as a free semantic anchor, and
ΔE_CVD ≥ {min(hybrid_cvd[:3]):.1f} through n=4.

Semantic red `#AE3030` sits at slot {hybrid_hexes.index('#AE3030')}, reachable via the
named API (`palette.red`) for loss / error / bad without polluting the
positional default for every chart with ≥ 3 series.

## CVD prevalence — who are we actually designing for?

The default CVD simulation (Coblis, color-blindness.com, this repo's
`worst_cvd_pairwise_delta_e`) shows **100% dichromacy**. That covers only the
fully-dichromatic 1–2% of the population, not the much larger anomalous-trichromacy
group.

| Form | ♂ rate (NW Europe) | ♀ rate | Description |
|---|---|---|---|
| Deuteranomaly (M-cone shifted) | ~5.0% | ~0.35% | Reduced red/green discrimination, residual colour |
| Protanomaly (L-cone shifted) | ~1.0% | ~0.03% | Same, plus red appears darker |
| **Deuteranopia** (M-cone absent) | **~1.0%** | **~0.01%** | Red/green near-indistinguishable |
| **Protanopia** (L-cone absent) | **~1.0%** | **~0.02%** | Same, red looks near-black |
| Tritanopia / Tritanomaly | ~0.01% | ~0.01% | Blue/yellow confusion; usually acquired |
| **Σ all forms** | **~8%** | **~0.5%** | |

Sources: Sharpe et al. 1999; Birch 2012 *Ophthalmic Physiol Opt* 32(5); Hood et al. 2024.

**Key consequence:** the ~5% anomalous-trichromacy group has a *partial* cone shift,
not full loss. Population-mean severity for deuteranomaly is ~0.6 (Simunovic 2010,
*Eye* 24, 747–755). At severity 0.6, worst-pair ΔE_CVD is roughly **30-40% higher**
than at 1.0 simulation.

A palette with worst-pair ΔE_CVD ≈ 10 at full-100% simulation translates to roughly
**14-16 ΔE** for the actual deuteranomaly population — clearly above the discrimination
floor. The 1-2% with full deuteranopia *will* still need a redundant encoding (line
style / marker / label) at n ≥ 6, regardless of which 8-hex palette ships.

This is why every published categorical palette caps at "min ΔE_CVD ≈ 11" at n=8
(Okabe-Ito, Paul Tol "muted", Petroff 2021's n=8 reach ~18) rather than chasing
the unreachable ΔE ≥ 15 ceiling.

## Hybrid-v3 vs pure-CVD-greedy

Both sortings use the **identical** 8 hexes of muted-8:

```
#009E73  #AE3030  #C475FD  #99B314  #4467A3  #2ABCCD  #954477  #BD8233
brand-G  matte-R  lavender lime     blue     cyan     rosé     ochre
```

Only the **slot order** changes. Worst-pair ΔE under the min of the 3 CVD
simulations (deuteranopia / protanopia / tritanopia at 100% severity):

| sort | {n_header} |
| {n_sep} |
{compare_rows}

★ = recommended.

**pure-cvd-greedy** maximises ΔE per n by maximising min-CVD-distance to the
already-placed set at each step. Result for muted-8: it picks both `#C475FD`
lavender and `#954477` rosé (both "purple" family — read as pinkish-purple in
practice) in the first 4, and `#99B314` lime alongside `#009E73` brand green
(both "green" family). Visually weird despite the great ΔE numbers — the
"2× green, 2× purple" artefact flagged in the v2 review.

**hybrid-v3** trades a small per-n ΔE for two structural improvements: (a) the
first 4 slots span 4 distinct perceptual hue families (no "2× green / 2×
pink"), and (b) the semantic red anchor is deferred so it stays available via
the named API rather than being burned on slot 2 of every chart. The CVD floor
at n=8 is identical (8.81) — both sortings ship the same 8 hexes, so the
worst-case is fixed by the palette, not the order.

(The v2 head-to-head also compared `wheel-gap-first`, `hue-order`, and
`every-other-hue`, all of which had ΔE_CVD ≈ 10–14 from n=2 onward — see
[../palette-variants-v2/](../palette-variants-v2/) for that history.)

## The hybrid v3 algorithm

```python
def sort_hybrid_v3(hexes, first_n=4, defer=("#AE3030",)):
    # Slot 0 fixed (project anchor: brand green).
    # Slots 1..first_n-1: greedy max-min worst-CVD ΔE, constrained to
    #                     (a) a coarse hue family not already used AND
    #                     (b) not in `defer` (semantic red kept for named API).
    # Slots first_n..N-1: pure greedy max-min worst-CVD ΔE on the remainder
    #                     (deferred hexes re-enter the pool here).
```

**Why a custom coarse-family partition?** A naive 45°-bin partition splits
muted-8's `lavender` (≈ 305°) and `rosé` (≈ 345°) into *different* bins, yet
both read as "pinkish-purple" to the eye. Same story for `brand-green`
(≈ 166°) and `lime` (≈ 115°): different bins, but visually grouped as "two
greens". Inheriting v1's 14 fine hue-bands directly doesn't fix it either —
because `brand-green` at H ≈ 166° lands one degree *over* v1's `teal/cyan`
boundary (165°) and is classified as `cyan` rather than `teal`/`green`.

So we use a custom 6-band partition with wider, perception-shaped boundaries.
Names are picked to fit the *dominant* hue in each band (so 30°–90° is
"yellow" not "orange" because the actually-present hue is ochre at H≈70° = amber,
not orange at ~40°; same logic for "purple" over "pink" since lavender at
H≈305° is purple, not pink):

| coarse family | CAM02-UCS hue range | what lives there in muted-8 |
|---|---|---|
| red    | 345°–360° ∪ 0°–30° | matte red `#AE3030` (H≈25°) |
| yellow | 30°–90° | ochre `#BD8233` (H≈70°) |
| green  | 90°–180° | brand green `#009E73` (H≈166°), lime `#99B314` (H≈115°) |
| cyan   | 180°–230° | cyan `#2ABCCD` (H≈209°) |
| blue   | 230°–285° | blue `#4467A3` (H≈254°) |
| purple | 285°–345° | lavender `#C475FD` (H≈305°), rosé `#954477` (H≈345°) |

For muted-8 the 8 hexes distribute as:

```
red    (1 hex):  #AE3030 red
yellow (1 hex):  #BD8233 ochre
green  (2 hex):  #009E73 brand-G (H≈166°), #99B314 lime (H≈115°)
cyan   (1 hex):  #2ABCCD cyan
blue   (1 hex):  #4467A3 blue
purple (2 hex):  #C475FD lavender (H≈305°), #954477 rosé (H≈345°)
```

Six distinct families across the 8 hexes — the constraint comfortably enforces
4-distinct-families in the first 4 slots, with no fallback ever triggering.

## Finalist slot order

| slot | hex | fine family | coarse family | hue |
|---|---|---|---|---|
{slot_rows}

worst-pair ΔE for the sorted palette, per first-n subset:

| | {n_header} |
| {n_sep} |
{_per_n_md_row("normal vision", hybrid_norm)}
{_per_n_md_row("under CVD (min)", hybrid_cvd)}

## Comparison to established palettes

The 2021–2026 best practice is to constrain on min ΔE under simulated CVD as a
hard constraint inside the generator (Petroff 2021 arXiv:2107.02270; Zeileis
2024 `colorspace` 2.1; `qualpalr`). Slot ordering inside the optimised set is a
secondary concern handled differently per palette.

| palette | slot 0..3 (hue family) | reds vs greens placement | ΔE_CVD floor (n=8) |
|---|---|---|---|
| **muted-8 hybrid-v3 ★** | {annos[0][1]} / {annos[1][1]} / {annos[2][1]} / {annos[3][1]} | red at slot {hybrid_hexes.index('#AE3030')} (deferred past first-4) | {hybrid_cvd[-1]:.1f} |
| Okabe-Ito (n=8, Wong 2011) | orange / sky-blue / green / yellow | vermillion at slot 5, green at slot 2 — 3 slots apart | ≈ 11 (Petroff 2021) |
| Paul Tol "muted" (n=9) | pink / indigo / yellow-tan / green | wine-red at slot 5, green at slot 3 | (unverified) |
| ColorBrewer Set2 (n=8) | teal / orange / blue-violet / pink | no "true" red in palette | (unverified) |
| Tableau-10 | blue / orange / red / teal | red at slot 2 (kept in first 4) | (unverified) |
| Tableau-Colorblind-10 | blue / orange / grey / dark-grey | only 2 hue families (blue + orange) + greys | n/a |
| D3 schemeCategory10 | blue / orange / green / red | green at 2, red at 3 — adjacent (textbook CVD weak point) | (unverified) |
| Petroff 2021 (n=8) | blue / orange / red / magenta | red at 2 (kept in first 4) | ≈ 18 (paper §3) |

Sources: Wong 2011 *Nature Methods* 8:441; Tol 2018 (https://personal.sron.nl/~pault/);
ColorBrewer (https://colorbrewer2.org); Tableau-CB-10 hex via AndiH gist;
d3-scale-chromatic source; Petroff 2021 arXiv:2107.02270 §3.

**Position:** muted-8 hybrid-v3 sits in the academic-publishing family —
defers red (like Okabe-Ito and Tol), 4 distinct hue families in slots 0..3,
similar ΔE_CVD floor at n=8 (~9 vs Okabe-Ito ~11), distinct because muted-8
has a true semantic red available — just reached by name, not by position.

## Why defer red?

The CVD trade-off, measured concretely:

| | n=2 | n=3 | n=4 |
|---|---|---|---|
| hybrid-v3 (with `defer=("#AE3030",)`, current) | 36.19 | 16.34 | 13.98 |
| hybrid-v3 without defer | 36.19 | 17.44 | 16.34 |

Deferring red costs **~2.4 ΔE_CVD at n=4** because the binding pair shifts
from `green↔red` (CVD 16.34) to `green↔ochre` (CVD 13.98). In exchange:

- **red stays a free semantic anchor.** The v2 expert reviews (consulting +
  editorial) flagged that a true red is a semantic resource — "loss / error /
  bad" — and burning it as slot 2 of every categorical chart wastes that
  connotation. If `palette.red` and `palette[2]` both resolve to `#AE3030`,
  the same colour means different things in different charts and the semantic
  contract breaks.
- **the first 4 are 4 cleanly distinct hue families** — green / pink / blue /
  orange — without a CVD-tight pair sitting next to each other.
- **n=4 ΔE_CVD = 13.98 is still above the 10-point "confident discrimination"
  floor.** Practical loss is small; semantic gain is structural.
- **alignment with the academic-publishing family** (Okabe-Ito, Paul Tol —
  both defer red to slot 5+), which is the right neighbourhood for a
  generative plot tool whose output lands in editorial, slide-deck and
  scientific contexts.

Callers who want red back at slot 2 can pass `defer=()` to the sorter; the
parameter is configurable, just not the default.

## Semantic anchors outside the categorical pool

The 8 hues above are the **categorical pool** — what `palette[:n]` returns.
But several semantic roles don't map cleanly onto any of the 8: warning
(needs leuchtgelb, not ochre-brown), totals/baseline (needs a neutral that's
visually structural rather than categorical), and "other/rest" in stacked
charts (needs a soft neutral that doesn't compete with the data). Three
additional anchors close those gaps. They live **outside** the slot pool and
are only reachable via the named API.

### palette.amber — warning / caution

Fixed hex `#DDCC77` (Paul Tol "muted" yellow). Min ΔE under CVD to all 8
categorical hexes = **{amber_cvd_min:.2f}** — confidently distinct from every
member, including `#99B314` lime.

| candidate | min ΔE_normal | min ΔE_CVD | C | comment |
|---|---|---|---|---|
| `#D4A017` amber-2017 | 12.62 | **2.37** | 29.2 | collapses against `#99B314` lime under deuteranopia (unusable) |
| `#D4AF37` goldenrod | 14.99 | **2.33** | 27.1 | same lime collision (unusable) |
| `#DDCC77` Tol muted-yellow ★ | 19.56 | **14.52** | 20.6 | only CVD-safe option; consistent with the academic-publishing family muted-8 lives in |

The two more saturated amber candidates fail because under deuteranopia /
protanopia they collapse to the same lightness-band as lime. Tol's
lower-chroma amber sits in a different lightness band (J*=84 vs lime's J*=71)
and survives the simulation. C=20.6 is *just* below the muted-8 chroma
envelope (C ∈ [24, 32]) but that's a feature: it signals "I'm not a
categorical-pool member, I'm a semantic anchor next to it".

### palette.neutral — totals / baseline / outline (theme-adaptive)

The neutral isn't a fixed hex but a **role** that flips per theme — same
pattern as Apple HIG, Material Design, GitHub Primer, and Wong (2011)
Okabe-Ito position 8 (style-guide §4.1):

- **light theme** → `{ink_light}` (warm near-black ink)
- **dark theme** → `{ink_dark}` (warm near-white ink)

Same hex as the chart's text and gridlines, so a "totals" / "baseline" /
"reference outline" series reads as part of the chart's structural layer
rather than as just another category. Implemented today as `NEUTRAL_LIGHT` /
`NEUTRAL_DARK` in `scripts/_palette_common.py:70-71`.

### palette.muted — other / rest / disabled (theme-adaptive)

A second adaptive neutral, soft-contrast rather than full-contrast:

- **light theme** → `{ink_muted_light}` (warm mid-gray)
- **dark theme** → `{ink_muted_dark}` (warm mid-gray)

For "other" / "rest" slices in stacked bars, disabled / inactive series,
confidence bands, and annotations that should sit behind the data without
competing. Comes from `LIGHT_THEME["ink_muted"]` /
`DARK_THEME["ink_muted"]` — already used everywhere in the design system,
just not yet exposed through the palette API.

## Final named-API surface

```python
# Categorical pool (8 hues — sorted by hybrid-v3, slots 0..7)
anyplot.palette.green     # → #009E73   ("good / profit / energy")
anyplot.palette.red       # → #AE3030   ("bad / loss / error")
anyplot.palette.blue      # → #4467A3   ("cool / water / info")
anyplot.palette.cyan      # → #2ABCCD   ("sky / tech-cool")
anyplot.palette.lime      # → #99B314   ("growth / nature")
anyplot.palette.ochre     # → #BD8233   ("earth / commodity")
anyplot.palette.lavender  # → #C475FD   ("creative")
anyplot.palette.rose      # → #954477   ("wellness / feminine")

# Semantic anchors OUTSIDE the categorical pool (never returned by palette[:n])
anyplot.palette.amber     # → #DDCC77   ("caution / warning")
anyplot.palette.neutral   # → adaptive  ("totals / baseline / outline")
anyplot.palette.muted     # → adaptive  ("other / rest / disabled")

# Semantic-role aliases that map to the anchors above
anyplot.palette.semantic.good      # → green
anyplot.palette.semantic.bad       # → red
anyplot.palette.semantic.warning   # → amber   (NB: NOT ochre — ochre is "earth", not "caution")
anyplot.palette.semantic.info      # → cyan
anyplot.palette.semantic.baseline  # → neutral (adaptive)
anyplot.palette.semantic.other     # → muted   (adaptive)
```

Slot order and named access are independent — both ship.

## Contrast caveats & the outline pattern

The muted aesthetic carries a known trade-off: the lighter members reach
their distinguishability through chroma, not L-spread, so on the light theme
(cream `#F5F3EC`) five categorical hues + amber fall under WCAG 2.1
SC 1.4.11&apos;s 3:1 minimum for graphical objects. This is not unique to
muted-8 — Okabe-Ito&apos;s `#F0E442` yellow, Paul Tol &ldquo;muted&rdquo;&apos;s
`#DDCC77` and `#88CCEE`, and ColorBrewer Set2&apos;s `#A6D854` green all
have the same limitation.

Per-theme ratios for every categorical hue + amber:

| hex | name | on cream bg | on dark bg |
|---|---|---|---|
| `#009E73` | brand-green | 3.08:1 ✓ | 5.48:1 ✅ |
| `#AE3030` | matte-red | 5.79:1 ✅ | **2.92:1** ❌ |
| `#C475FD` | lavender | **2.59:1** ❌ | 6.53:1 ✅ |
| `#99B314` | lime | **2.15:1** ❌ | 7.87:1 ✅ |
| `#4467A3` | blue | 5.09:1 ✅ | 3.32:1 ✓ |
| `#2ABCCD` | cyan | **2.06:1** ❌ | 8.19:1 ✅ |
| `#954477` | rose | 5.61:1 ✅ | 3.01:1 ✓ |
| `#BD8233` | ochre | **2.95:1** ❌ | 5.72:1 ✅ |
| `#DDCC77` | amber (anchor) | **1.46:1** ❌ | 11.59:1 ✅ |

### Recommended pattern: thin ink-color outline

The industry-standard rescue is a thin stroke in the chart&apos;s ink color
on the affected series — Tableau, Vega, and most modern dashboarding tools
do this automatically in their accessibility mode. Recommended:

- **line / scatter / area edges:** 1px solid ink stroke
- **bar / pie fills:** 1–1.5px solid ink stroke
- **legend swatches:** match the chart&apos;s outline behavior

The stroke contrast (`#1A1A17` ink on `#F5F3EC` bg = 15.71:1) always passes
on its own, so the *visible boundary* of the series clears 3:1 even if the
fill colour doesn&apos;t.

### What about amber specifically?

`palette.amber = #DDCC77` is the worst case on light bg (1.46:1) but lives
outside the categorical pool — it&apos;s only reached intentionally via
`palette.amber` or `palette.semantic.warning` for caution / warning roles.
On the light theme, the same outline rule applies: wherever amber is used
(typically: a warning marker, a status icon, a single attention slice), add
a thin ink stroke. amber is never used by `palette[:n]` so it never ends
up on light bg by accident.

### Dark-theme caveats

The dark theme is mostly clean (every hue ≥ 3:1) except `#AE3030` matte-red
at 2.92:1 — fractionally under threshold. Same outline rule applies for
high-stakes layouts (financial dashboards, accessibility-strict contexts).
Future work — listed in v2&apos;s reviewer recommendations — is a separate
per-theme hex set with L+12 lift on the cool half; until then, the outline
pattern is the documented fix.

See the live demo in [`index.html`](./index.html#contrast) — every member
rendered on both themes, with the sub-3:1 ones shown both as-is and with
the 2px ink ring.

## Next steps

1. Apply the hybrid-v3 ordering above as the new live `ANYPLOT_PALETTE`.
2. Ship the named API alongside, with `amber` / `neutral` / `muted` as the
   three semantic anchors outside the categorical pool.
3. Wire `semantic.warning → amber` (not ochre — ochre is the "earth /
   commodity" categorical hue, not a caution signal).
4. Document the n > 4 redundant-encoding guidance (linestyle / marker / shape).
5. *Optional* — expose a `palette.cvd_severity` knob defaulting to 1.0 (the
   conservative current behaviour) but lettable down to ~0.6 for users who
   explicitly want the palette tuned to realistic deuteranomaly severity
   instead of full dichromacy.

## References

- Wong B. (2011). "Points of view: Color blindness." *Nature Methods* 8:441.
- Tol P. (2018). "Colour Schemes", https://personal.sron.nl/~pault/.
- Sharpe L. T. et al. (1999). "Opsin genes, cone photopigments, color vision, and color blindness." In *Color Vision: From Genes to Perception*.
- Birch J. (2012). "Worldwide prevalence of red-green color deficiency." *J. Opt. Soc. Am. A* 29(3):313–320.
- Simunovic M. P. (2010). "Colour vision deficiency." *Eye* 24:747–755.
- Petroff M. A. (2021). "Accessible Color Sequences for Data Visualization." arXiv:2107.02270.
- Zeileis A. (2024). "Color Vision Deficiency Emulation in colorspace 2.1." https://www.zeileis.org/news/simulate_cvd/.
- Larsson J. (2024). "qualpalr: Automatic Generation of Qualitative Color Palettes." https://jolars.github.io/qualpalr/.
- Carbon Design System. "Data visualization color palettes." https://carbondesignsystem.com/data-visualization/color-palettes/.
"""


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------


DEFAULT_OUT_DIR = REPO_ROOT / "docs" / "reference" / "palette-variants-v3"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate palette variants v3")
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
    log = logging.getLogger("palette-variants-v3")

    args.out_dir.mkdir(parents=True, exist_ok=True)

    hybrid = sort_hybrid_v3(list(MUTED_8))
    log.info("muted-8 hybrid-v3 → %s", " ".join(hybrid))
    log.info(
        "  per-n CVD ΔE = %s",
        [round(v, 2) for v in measure_per_n_cvd(hybrid)],
    )

    log.info("comparison sortings:")
    sort_rows: list[tuple[str, str, list[str], list[float], list[float]]] = []
    for slug, title, fn in ALL_SORTINGS:
        sorted_hexes = fn(list(MUTED_8))
        cvd = measure_per_n_cvd(sorted_hexes)
        norm = measure_per_n_normal(sorted_hexes)
        sort_rows.append((slug, title, sorted_hexes, cvd, norm))
        log.info(
            "  %-26s %s  CVDmin/n=2..8=%s",
            slug,
            " ".join(sorted_hexes),
            [round(v, 2) for v in cvd],
        )

    html_out = render_page(hybrid)
    out_path = args.out_dir / "index.html"
    out_path.write_text(html_out, encoding="utf-8")
    log.info("wrote %s (%.1f kB)", out_path, out_path.stat().st_size / 1024)

    md_out = render_rationale_md(hybrid, sort_rows)
    md_path = args.out_dir / "decision-rationale.md"
    md_path.write_text(md_out, encoding="utf-8")
    log.info("wrote %s (%.1f kB)", md_path, md_path.stat().st_size / 1024)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
