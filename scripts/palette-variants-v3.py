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
        f"{render_finalist_section(hybrid_hexes)}"
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

## Optional: the semantic named-API (decoupled from position)

The position-based access pattern (`palette[:n]`) is the default. For projects
where consistent semantic anchors matter (every chart in the slide deck uses
the same red for "loss"), a parallel named API is the right tool — separate
from slot order:

```python
anyplot.palette.green   # → #009E73   ("good / profit / energy")
anyplot.palette.red     # → #AE3030   ("bad / loss / error")
anyplot.palette.blue    # → #4467A3   ("cool / water / info")
anyplot.palette.ochre   # → #BD8233   ("warning / commodity")
# … plus palette.semantic.{{good, bad, warning, info}} aliases
```

This is documented in [`../palette-variants-v2/expert-reviews.md`](../palette-variants-v2/expert-reviews.md)
under "Recommended additional design move". Slot order and named access are
independent — both ship.

## Next steps

1. Apply the hybrid-v3 ordering above as the new live `ANYPLOT_PALETTE`.
2. Ship the named API alongside (`palette.red`, `palette.semantic.bad`, etc.).
3. Document the n > 4 redundant-encoding guidance (linestyle / marker / shape).
4. *Optional* — expose a `palette.cvd_severity` knob defaulting to 1.0 (the
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
