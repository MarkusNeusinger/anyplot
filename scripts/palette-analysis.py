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
"""Palette baseline diagnostic for anyplot.

Generates a single self-contained HTML page that visualises the current anyplot
palette across three domains, each evaluated for normal vision and three
100%-severity CVD simulations (deuteranopia, protanopia, tritanopia):

  A. Categorical plot palette (Okabe-Ito 7 + 2 adaptive neutrals)
  B. Continuous plot colormaps (viridis, cividis, BrBG, Reds, Blues, Greens)
  C. Website surface & chrome tokens (light + dark themes)

For each domain the page renders swatches, pairwise CAM02-UCS ΔE matrices,
L* monotonicity profiles for colormaps, and WCAG contrast cross-checks for
website tokens. Output is one file with inline CSS and inline SVG, no
external assets, no JS beyond a tiny theme-toggle.

Method:
    - ΔE = Euclidean distance in CAM02-UCS (Luo et al. 2006)
    - CVD simulation = Machado et al. (2009) model via colorspacious
    - Severity = 100% (i.e. the "anopia" endpoint for each cone type)

The script reads palette constants directly from ``core.images`` so there is
a single source of truth.

Usage::

    uv run --script scripts/palette-analysis.py
    uv run --script scripts/palette-analysis.py --out /tmp/palette.html

Default output is ``docs/reference/palette-analysis.html`` so the artefact
lives next to ``docs/reference/style-guide.md`` and ``anyplot-landing-mockup.html``.
"""

from __future__ import annotations

import argparse
import logging
import sys
from html import escape as h
from pathlib import Path

import matplotlib as mpl
import numpy as np
from colorspacious import cspace_convert


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from core.images import DARK_THEME, LIGHT_THEME, OK_GREEN, OKABE_PALETTE  # noqa: E402


DEFAULT_OUTPUT = REPO_ROOT / "docs" / "reference" / "palette-analysis.html"

# CVD condition spec consumed by colorspacious. "normal" is handled as a
# no-op branch so the rest of the code can iterate uniformly over all four.
CVD_SPECS: dict[str, dict | None] = {
    "normal": None,
    "deuter": {"name": "sRGB1+CVD", "cvd_type": "deuteranomaly", "severity": 100},
    "protan": {"name": "sRGB1+CVD", "cvd_type": "protanomaly", "severity": 100},
    "tritan": {"name": "sRGB1+CVD", "cvd_type": "tritanomaly", "severity": 100},
}
CVD_LABELS = {
    "normal": "normal",
    "deuter": "deuteranopia",
    "protan": "protanopia",
    "tritan": "tritanopia",
}
CVD_ORDER = ["normal", "deuter", "protan", "tritan"]

OKABE_NAMES = ["green", "vermillion", "blue", "purple", "orange", "sky", "yellow"]
NEUTRAL_LIGHT = "#1A1A17"
NEUTRAL_DARK = "#F0EFE8"

COLORMAPS = ["viridis", "cividis", "BrBG"]


# -----------------------------------------------------------------------------
# Color math
# -----------------------------------------------------------------------------


def hex_to_rgb1(hex_str: str) -> np.ndarray:
    s = hex_str.lstrip("#")
    return np.array([int(s[i : i + 2], 16) / 255.0 for i in (0, 2, 4)])


def rgb1_to_hex(rgb1: np.ndarray) -> str:
    r, g, b = (int(round(float(np.clip(c, 0, 1)) * 255)) for c in rgb1)
    return f"#{r:02X}{g:02X}{b:02X}"


def simulate_cvd(rgbs: np.ndarray, cvd: str) -> np.ndarray:
    """Simulate CVD on an (..., 3) sRGB-1 array. Returns clipped sRGB-1."""
    if cvd == "normal":
        return rgbs
    out = cspace_convert(rgbs, CVD_SPECS[cvd], "sRGB1")
    return np.clip(out, 0.0, 1.0)


def to_jab(rgbs: np.ndarray) -> np.ndarray:
    """sRGB-1 (..., 3) → CAM02-UCS (..., 3) = (J', a', b')."""
    return cspace_convert(rgbs, "sRGB1", "CAM02-UCS")


def pairwise_delta_e(colors_rgb: np.ndarray, cvd: str) -> np.ndarray:
    sim = simulate_cvd(colors_rgb, cvd)
    jab = to_jab(sim)
    diff = jab[:, None, :] - jab[None, :, :]
    return np.linalg.norm(diff, axis=2)


def worst_cvd_pairwise_delta_e(
    colors_rgb: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Returns (worst_matrix, breakdown) for the 3 CVD conditions only.

    - worst_matrix[i, j] = min ΔE across {deuter, protan, tritan}
                           (i.e. the worst-case CVD for that pair)
    - breakdown[i, j, k] = ΔE under CVD_TYPES[k] for k in (deuter, protan, tritan)

    Normal vision is handled separately because the diagnostic question
    "how distinct under CVD?" is a different one from "how distinct
    overall?", and conflating both blurs the answer.
    """
    cvds = ["deuter", "protan", "tritan"]
    matrices = np.stack(
        [pairwise_delta_e(colors_rgb, cvd) for cvd in cvds], axis=-1
    )
    return matrices.min(axis=-1), matrices


def adjacent_delta_e(samples_rgb: np.ndarray, cvd: str) -> np.ndarray:
    sim = simulate_cvd(samples_rgb, cvd)
    jab = to_jab(sim)
    return np.linalg.norm(np.diff(jab, axis=0), axis=1)


def wcag_relative_luminance(rgb1: np.ndarray) -> float:
    def _f(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (_f(float(c)) for c in rgb1)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def wcag_contrast(rgb1_a: np.ndarray, rgb1_b: np.ndarray) -> float:
    la = wcag_relative_luminance(rgb1_a)
    lb = wcag_relative_luminance(rgb1_b)
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


def cmap_samples(name: str, n: int = 256) -> np.ndarray:
    cmap = mpl.colormaps[name]
    return cmap(np.linspace(0.0, 1.0, n))[:, :3]


# -----------------------------------------------------------------------------
# Domain inputs
# -----------------------------------------------------------------------------


CATEGORICAL_HEX = [*OKABE_PALETTE, NEUTRAL_LIGHT, NEUTRAL_DARK]
CATEGORICAL_LABELS = [*OKABE_NAMES, "neutral·light", "neutral·dark"]

SURFACE_KEYS = ["bg_page", "bg_surface", "bg_elevated", "ink", "ink_soft", "ink_muted"]
SURFACE_LABELS = ["bg-page", "bg-surface", "bg-elevated", "ink", "ink-soft", "ink-muted"]

# bg_elevated is documented in style-guide.md §4.2 but not (yet) carried in
# core.images.{LIGHT,DARK}_THEME — bridge it here so the diagnostic covers the
# full chrome layer.
LIGHT_THEME_FULL = {**LIGHT_THEME, "bg_elevated": "#FFFDF6"}
DARK_THEME_FULL = {**DARK_THEME, "bg_elevated": "#242420"}


# -----------------------------------------------------------------------------
# HTML rendering
# -----------------------------------------------------------------------------


def cell_class(delta_e: float) -> str:
    """4-step CAM02-UCS threshold for categorical distinguishability.

    Petroff (2021) "Accessible Color Sequences for Data Visualization"
    (arXiv:2107.02270) optimises palettes in CAM02-UCS and uses 15 as the
    minimum target for comfortable categorical distinguishability. Below 15
    pairs are distinct but uncomfortably so; below 10 they're marginal;
    below 5 they're effectively confusable.
    """
    if delta_e < 5:
        return "cell-bad"
    if delta_e < 10:
        return "cell-warn"
    if delta_e < 15:
        return "cell-meh"
    return "cell-ok"


def swatch_text_color(rgb1: np.ndarray) -> str:
    return "#1A1A17" if wcag_relative_luminance(rgb1) > 0.45 else "#F0EFE8"


def render_sample_chart(theme: dict[str, str], theme_label: str) -> str:
    """Inline SVG mini line-chart with 3 series on the theme's bg-page —
    the real-world typical case (style-guide §4: "2–3 colours is ideal for
    most categorical plots").
    """
    import math

    width, height = 460, 240
    margin_l, margin_r, margin_t, margin_b = 36, 18, 22, 26
    plot_w = width - margin_l - margin_r
    plot_h = height - margin_t - margin_b

    bg = theme["bg_page"]
    ink_muted = theme["ink_muted"]
    rule = theme.get("rule", "#DFDDD6")
    is_light = bg.upper().startswith("#F")
    grid = "rgba(26,26,23,0.06)" if is_light else "rgba(240,239,232,0.06)"

    n_points = 48
    series = OKABE_PALETTE[:3]  # green · vermillion · blue — positions 1–3

    grid_lines = "".join(
        f'<line x1="{margin_l}" y1="{margin_t + plot_h * f:.1f}" '
        f'x2="{margin_l + plot_w}" y2="{margin_t + plot_h * f:.1f}" '
        f'stroke="{grid}" stroke-width="1" />'
        for f in (0.25, 0.5, 0.75)
    )

    polylines: list[str] = []
    for i, color in enumerate(series):
        amp = 0.38 - i * 0.04
        phase = i * math.pi / 4.5
        freq = 1.4 + i * 0.18
        decay = 0.25 + i * 0.05
        pts = []
        for j in range(n_points):
            x = j / (n_points - 1)
            y = 0.5 + amp * math.sin(2 * math.pi * freq * x + phase) * (1 - decay * x)
            px = margin_l + x * plot_w
            py = margin_t + (1 - y) * plot_h
            pts.append(f"{px:.1f},{py:.1f}")
        polylines.append(
            f'<polyline points="{" ".join(pts)}" stroke="{color}" '
            f'stroke-width="2.4" fill="none" stroke-linecap="round" '
            f'stroke-linejoin="round" />'
        )

    axes = (
        f'<line x1="{margin_l}" y1="{margin_t}" '
        f'x2="{margin_l}" y2="{margin_t + plot_h}" stroke="{rule}" stroke-width="1" />'
        f'<line x1="{margin_l}" y1="{margin_t + plot_h}" '
        f'x2="{margin_l + plot_w}" y2="{margin_t + plot_h}" stroke="{rule}" stroke-width="1" />'
    )

    tick_x_y = margin_t + plot_h + 14
    ticks = "".join(
        f'<text x="{margin_l + plot_w * f:.1f}" y="{tick_x_y}" fill="{ink_muted}" '
        f'font-size="9" text-anchor="middle">{int(f * 100)}</text>'
        for f in (0.0, 0.25, 0.5, 0.75, 1.0)
    )

    label = (
        f'<text x="{margin_l}" y="{margin_t - 6}" fill="{ink_muted}" '
        f'font-size="10" text-anchor="start">{h(theme_label)} — bg-page {bg}</text>'
    )

    return (
        f'<svg viewBox="0 0 {width} {height}" class="sample-chart" '
        f'preserveAspectRatio="xMidYMid meet" '
        f'style="background:{bg};border:1px solid {rule};border-radius:6px">'
        f"{label}{grid_lines}{axes}{''.join(polylines)}{ticks}"
        "</svg>"
    )


def render_first_n_summary() -> str:
    """Compact "if you only use the first N colours" table.

    Answers the real-world question: at what palette size does the weakest
    pair drop below comfortable distinguishability? The 9×9 matrix shows
    everything, but most plots are 2–4 series — so the prioritisation matters.
    """
    hues_rgb = np.array([hex_to_rgb1(hx) for hx in OKABE_PALETTE])
    M_normal_full = pairwise_delta_e(hues_rgb, "normal")
    cvd_full = np.stack(
        [pairwise_delta_e(hues_rgb, c) for c in ("deuter", "protan", "tritan")],
        axis=-1,
    ).min(axis=-1)

    rows = []
    for n in range(2, 8):
        sub_normal = M_normal_full[:n, :n]
        sub_worst = cvd_full[:n, :n]
        # min over off-diagonal entries (upper triangle is enough by symmetry)
        triu = np.triu_indices(n, k=1)
        v_norm = float(sub_normal[triu].min())
        v_worst = float(sub_worst[triu].min())
        added = OKABE_NAMES[n - 1]
        rows.append(
            f'<tr><th>n={n}</th>'
            f'<td class="add">+ {h(added)}</td>'
            f'<td class="{cell_class(v_norm)}">{v_norm:.1f}</td>'
            f'<td class="{cell_class(v_worst)}">{v_worst:.1f}</td></tr>'
        )
    return (
        '<figure class="first-n">'
        '<figcaption>worst pair if you use only positions 1..n</figcaption>'
        '<table>'
        '<tr><th></th><th>added</th><th>normal</th><th>worst-cvd</th></tr>'
        f'{"".join(rows)}'
        '</table>'
        "</figure>"
    )


def render_sample_charts() -> str:
    return (
        '<div class="sample-charts">'
        f"{render_sample_chart(LIGHT_THEME_FULL, 'light')}"
        f"{render_sample_chart(DARK_THEME_FULL, 'dark')}"
        "</div>"
    )


def _wcag_badge(fg_hex: str, bg_hex: str, large: bool = False) -> str:
    """Inline contrast badge using WCAG 2.1 thresholds.

    Normal text: AA ≥ 4.5, AAA ≥ 7. Large text / non-text UI: AA ≥ 3, AAA ≥ 4.5.
    """
    ratio = wcag_contrast(hex_to_rgb1(fg_hex), hex_to_rgb1(bg_hex))
    aa = 3.0 if large else 4.5
    aaa = 4.5 if large else 7.0
    if ratio >= aaa:
        cls, grade = "ok", "AAA"
    elif ratio >= aa:
        cls, grade = "warn", "AA"
    else:
        cls, grade = "bad", "FAIL"
    return f'<span class="cbadge cb-{cls}">{ratio:.2f}:1 {grade}</span>'


def render_hero_mockup(theme: dict[str, str], theme_label: str) -> str:
    """Tiny rendition of the anyplot.ai hero (style-guide §5.3) for the current
    theme, with every visible text element annotated with its WCAG contrast
    ratio. The annotations turn red as soon as a colour change drops a pair
    below AA — that is the "Lighthouse green" check the user can eyeball."""
    bg = theme["bg_page"]
    bg_elev = theme["bg_elevated"]
    ink = theme["ink"]
    ink_soft = theme["ink_soft"]
    ink_muted = theme["ink_muted"]
    rule = theme.get("rule", "#DFDDD6")
    green = OK_GREEN

    badge_text = ink_muted  # readable on both light and bg-elevated overlays

    eyebrow_badge = _wcag_badge(ink_muted, bg)
    h1_badge = _wcag_badge(ink, bg, large=True)
    dot_badge = _wcag_badge(green, bg, large=True)
    accent_badge = _wcag_badge(ink, bg, large=True)
    subtitle_badge = _wcag_badge(ink, bg)
    prose_badge = _wcag_badge(ink_soft, bg)
    tagline_badge = _wcag_badge(ink, bg, large=True)
    cta_badge = _wcag_badge(bg, ink)  # button text on filled ink
    cta_hover_badge = _wcag_badge("#FFFFFF", green, large=True)  # hover-state, green fill
    link_badge = _wcag_badge(ink_soft, bg)

    return f"""
<div class="hero-mockup" style="background:{bg};border:1px solid {rule};color:{ink};--badge-color:{badge_text}">
    <div class="hero-meta">{h(theme_label)} — bg-page {bg}</div>

    <div class="hero-eyebrow" style="color:{ink_muted}">
        <span class="rule-line" style="background:{green}"></span>
        — the open plot catalogue {eyebrow_badge}
    </div>

    <div class="hero-h1">
        <span class="word">any<span class="dot" style="background:{green}"></span>plot()</span>
        <span class="paren">{dot_badge}</span>
    </div>
    <div class="hero-accent">— any library. {accent_badge} {h1_badge}</div>

    <div class="hero-subtitle">one spec · every library · always current. {subtitle_badge}</div>

    <p class="hero-prose" style="color:{ink_soft}">
        every plot begins as a library-agnostic spec. {prose_badge}
    </p>

    <div class="hero-tagline">
        steal like an artist.<span class="cursor" style="background:{green}"></span>
        {tagline_badge}
    </div>

    <div class="hero-ctas">
        <span class="cta-primary" style="background:{ink};color:{bg}">.browse()</span>
        <span class="cta-hover" style="background:{green};color:#FFFFFF">.browse() <em>hover</em></span>
        <a class="cta-secondary" style="color:{ink_soft}">or connect via mcp →</a>
    </div>
    <div class="hero-cta-badges">
        <span>filled cta: {cta_badge}</span>
        <span>hover green: {cta_hover_badge}</span>
        <span>secondary link: {link_badge}</span>
    </div>

    <div class="hero-surfaces" style="border-top:1px solid {rule}">
        <div class="surface-chip" style="background:{bg};color:{ink_muted}">bg-page {bg}</div>
        <div class="surface-chip" style="background:{theme['bg_surface']};color:{ink_muted}">bg-surface {theme['bg_surface']}</div>
        <div class="surface-chip" style="background:{bg_elev};color:{ink_muted}">bg-elevated {bg_elev}</div>
    </div>
</div>
"""


def render_hero_mockup_pair() -> str:
    return (
        '<div class="hero-mockup-stack">'
        f"{render_hero_mockup(LIGHT_THEME_FULL, 'light')}"
        f"{render_hero_mockup(DARK_THEME_FULL, 'dark')}"
        "</div>"
    )


def render_swatch_row(hex_str: str, label: str) -> str:
    rgb1 = hex_to_rgb1(hex_str)
    txt = swatch_text_color(rgb1)
    return (
        f'<div class="sw" style="background:{hex_str};color:{txt}">'
        f"<code>{hex_str}</code>"
        f"<span>{h(label)}</span>"
        "</div>"
    )


def render_swatch_table(hexes: list[str], labels: list[str]) -> str:
    items = "".join(render_swatch_row(hx, lab) for hx, lab in zip(hexes, labels))
    return f'<div class="swatch-row">{items}</div>'


def _render_one_matrix(
    M: np.ndarray,
    labels: list[str],
    caption: str,
    tooltip_for: callable,
) -> str:
    """Render a single ΔE matrix table. ``tooltip_for(i, j, value)`` returns
    the title-attribute text for the cell (so the caller controls how the
    underlying conditions are summarised on hover)."""
    n = M.shape[0]
    head = (
        "<tr><th></th>"
        + "".join(f'<th class="rot"><span>{h(lab)}</span></th>' for lab in labels)
        + "</tr>"
    )
    rows = []
    for i in range(n):
        cells = []
        for j in range(n):
            if i == j:
                cells.append('<td class="diag"></td>')
            else:
                v = float(M[i, j])
                cells.append(
                    f'<td class="{cell_class(v)}" title="{h(tooltip_for(i, j, v))}">{v:.1f}</td>'
                )
        rows.append(
            f'<tr><th class="rowlab">{h(labels[i])}</th>{"".join(cells)}</tr>'
        )
    return (
        f'<figure class="matrix">'
        f'<figcaption>{h(caption)}</figcaption>'
        f'<table class="delta">{head}{"".join(rows)}</table>'
        "</figure>"
    )


def render_matrix_block(colors_rgb: np.ndarray, labels: list[str]) -> str:
    """Two ΔE matrices side-by-side:

    1. Normal vision — the baseline.
    2. Worst across the 3 cvd conditions — for each pair, the cell shows the
       minimum ΔE produced by deuteranopia / protanopia / tritanopia (i.e.
       the worst case among them).

    Splitting normal and cvd answers two different diagnostic questions:
    a pair may be fine under normal vision but collapse under cvd, which only
    shows up clearly when the two matrices live side-by-side.
    """
    M_normal = pairwise_delta_e(colors_rgb, "normal")
    M_worst, M_breakdown = worst_cvd_pairwise_delta_e(colors_rgb)
    cvds = ["deuter", "protan", "tritan"]

    def _normal_tip(i: int, j: int, v: float) -> str:
        return f"{labels[i]} × {labels[j]} · normal ΔE={v:.2f}"

    def _worst_tip(i: int, j: int, v: float) -> str:
        breakdown = " · ".join(
            f"{CVD_LABELS[cvd]}={float(M_breakdown[i, j, k]):.1f}"
            for k, cvd in enumerate(cvds)
        )
        return f"{labels[i]} × {labels[j]} · worst-cvd ΔE={v:.2f} ({breakdown})"

    left = _render_one_matrix(M_normal, labels, "normal vision", _normal_tip)
    right = _render_one_matrix(
        M_worst, labels, "worst of 3 cvd (deuter · protan · tritan)", _worst_tip
    )
    return f'<div class="matrix-pair">{left}{right}</div>'


def render_gradient(samples_rgb: np.ndarray) -> str:
    spans = "".join(
        f'<span style="background:{rgb1_to_hex(s)}"></span>' for s in samples_rgb
    )
    return f'<div class="gradient">{spans}</div>'


def worst_adjacent_jump(samples_rgb: np.ndarray) -> tuple[float, str]:
    """Returns (max adjacent ΔE across all 4 conditions, condition label)."""
    worst_v = -1.0
    worst_cvd = "normal"
    for cvd in CVD_ORDER:
        v = float(adjacent_delta_e(samples_rgb, cvd).max())
        if v > worst_v:
            worst_v, worst_cvd = v, cvd
    return worst_v, CVD_LABELS[worst_cvd]


def render_colormap_row(name: str) -> str:
    samples = cmap_samples(name, 256)
    worst, worst_cond = worst_adjacent_jump(samples)
    return (
        f'<div class="cmap-row">'
        f'<span class="cmap-name">{h(name)}</span>'
        f"{render_gradient(samples)}"
        f'<span class="badge">worst Δ: {worst:.2f} <em>({h(worst_cond)})</em></span>'
        "</div>"
    )


def render_wcag_table(theme: dict[str, str]) -> str:
    bgs = ["bg_page", "bg_surface", "bg_elevated"]
    inks = ["ink", "ink_soft", "ink_muted"]
    head = "<tr><th></th>" + "".join(f"<th>{h(k.replace('_', '-'))}</th>" for k in bgs) + "</tr>"
    rows = []
    for ink_key in inks:
        cells = []
        for bg_key in bgs:
            ratio = wcag_contrast(hex_to_rgb1(theme[ink_key]), hex_to_rgb1(theme[bg_key]))
            grade = "AAA" if ratio >= 7 else "AA" if ratio >= 4.5 else "FAIL"
            cls = "cell-ok" if grade == "AAA" else "cell-warn" if grade == "AA" else "cell-bad"
            cells.append(f'<td class="{cls}">{ratio:.2f}<small>{grade}</small></td>')
        rows.append(f'<tr><th>{h(ink_key.replace("_", "-"))}</th>{"".join(cells)}</tr>')
    return (
        f'<figure class="matrix wcag">'
        f"<figcaption>WCAG contrast</figcaption>"
        f'<table class="delta">{head}{"".join(rows)}</table>'
        "</figure>"
    )


def render_surface_section(theme: dict[str, str], title: str) -> str:
    hexes = [theme[k] for k in SURFACE_KEYS]
    rgb_arr = np.array([hex_to_rgb1(hx) for hx in hexes])
    matrix = render_matrix_block(rgb_arr, SURFACE_LABELS)
    swatches = render_swatch_table(hexes, SURFACE_LABELS)
    wcag = render_wcag_table(theme)
    return (
        f'<section class="surface">'
        f"<h3>{h(title)}</h3>"
        f"{swatches}"
        f'<div class="surface-grid">'
        f'<div class="surface-col">{matrix}</div>'
        f'<div class="surface-col">{wcag}</div>'
        "</div>"
        "</section>"
    )


# -----------------------------------------------------------------------------
# Page assembly
# -----------------------------------------------------------------------------


PAGE_CSS = """
:root {
    --bg-page:     #F5F3EC;
    --bg-surface:  #FAF8F1;
    --bg-elevated: #FFFDF6;
    --ink:         #1A1A17;
    --ink-soft:    #4A4A44;
    --ink-muted:   #6B6A63;
    --rule:        rgba(26, 26, 23, 0.10);
    --ok-green:    #009E73;
    --ok-amber:    #E69F00;
    --ok-bad:      #D55E00;
    --mono: 'MonoLisa', 'MonoLisa Fallback', 'JetBrains Mono', Consolas, Menlo, Monaco, monospace;
}
body.theme-dark {
    --bg-page:     #121210;
    --bg-surface:  #1A1A17;
    --bg-elevated: #242420;
    --ink:         #F0EFE8;
    --ink-soft:    #B8B7B0;
    --ink-muted:   #A8A79F;
    --rule:        rgba(240, 239, 232, 0.10);
}
* { box-sizing: border-box; }
body {
    font-family: var(--mono);
    background: var(--bg-page);
    color: var(--ink);
    margin: 0;
    padding: 32px 48px 80px;
    font-size: 13px;
    line-height: 1.5;
    transition: background 0.3s, color 0.3s;
}
header.masthead {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    border-bottom: 1px solid var(--rule);
    padding-bottom: 18px;
    margin-bottom: 32px;
}
header.masthead h1 {
    font-size: 18px;
    margin: 0;
    font-weight: 600;
    letter-spacing: -0.01em;
}
header.masthead h1 .dot {
    color: var(--ok-green);
    font-size: 1.5em;
    line-height: 0;
    vertical-align: -0.05em;
    margin: 0 2px;
}
header.masthead .meta {
    color: var(--ink-muted);
    font-size: 11px;
}
button.theme-toggle {
    font-family: var(--mono);
    font-size: 12px;
    background: transparent;
    color: var(--ink-soft);
    border: 1px solid var(--rule);
    border-radius: 4px;
    padding: 6px 12px;
    cursor: pointer;
    transition: color 0.2s, border-color 0.2s;
}
button.theme-toggle:hover { color: var(--ok-green); border-color: var(--ok-green); }

section.domain {
    background: var(--bg-surface);
    border: 1px solid var(--rule);
    border-radius: 8px;
    padding: 24px 28px 28px;
    margin-bottom: 28px;
}
section.domain > h2 {
    font-size: 16px;
    font-weight: 600;
    margin: 0 0 6px 0;
    letter-spacing: -0.01em;
}
section.domain > h2::before {
    content: "❯ ";
    color: var(--ink-muted);
    font-weight: 400;
}
section.domain > p.lede {
    margin: 0 0 24px 0;
    color: var(--ink-soft);
    font-size: 12px;
}

/* sample charts (real-bg multi-line preview) */
.sample-charts {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
    margin-bottom: 18px;
}
.sample-charts svg { width: 100%; height: auto; display: block; }

/* swatch row */
.swatch-row {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 8px;
    margin-bottom: 20px;
}
.swatch-row .sw {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 60px;
    padding: 8px 12px;
    border-radius: 4px;
    border: 1px solid var(--rule);
    font-size: 11px;
}
.swatch-row .sw code { font-size: 12px; font-weight: 600; letter-spacing: -0.01em; }
.swatch-row .sw span { font-size: 10px; opacity: 0.85; }

/* delta E matrix */
.matrix {
    margin: 0;
    background: var(--bg-elevated);
    border: 1px solid var(--rule);
    border-radius: 6px;
    padding: 14px 16px 16px;
}
.matrix figcaption {
    font-size: 11px;
    color: var(--ink-muted);
    margin-bottom: 8px;
    text-transform: lowercase;
}
.matrix table.delta {
    border-collapse: collapse;
    width: 100%;
    font-size: 10px;
}
.matrix table.delta th {
    font-weight: 400;
    color: var(--ink-muted);
    padding: 2px 4px;
    text-align: center;
    vertical-align: bottom;
    font-size: 9.5px;
}
.matrix table.delta th.rowlab {
    text-align: right;
    padding-right: 6px;
    color: var(--ink-soft);
}
.matrix table.delta th.rot { white-space: nowrap; }
.matrix table.delta th.rot span {
    display: inline-block;
    transform: rotate(-45deg) translateX(6px);
    transform-origin: bottom left;
}
.matrix table.delta td {
    padding: 4px 6px;
    text-align: center;
    font-size: 10px;
    border: 1px solid rgba(26,26,23,0.04);
    font-variant-numeric: tabular-nums;
    color: var(--ink);
}
body.theme-dark .matrix table.delta td {
    border-color: rgba(240,239,232,0.06);
}
.cell-ok   { background: rgba(0,158,115,0.22); }      /* ≥ 15 — distinct (Petroff target) */
.cell-meh  { background: rgba(240,228,66,0.30); }     /* 10–15 — okay-ish */
.cell-warn { background: rgba(230,159,0,0.26); }      /* 5–10 — marginal */
.cell-bad  { background: rgba(213,94,0,0.30); }       /* < 5 — confusable */
.diag      { background: var(--rule); }

/* side-by-side matrix layout (normal + worst-cvd) */
.matrix-pair {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-top: 8px;
}
@media (max-width: 1100px) {
    .matrix-pair { grid-template-columns: 1fr; }
}

/* first-n summary */
.first-n {
    margin: 0 0 22px;
    max-width: 460px;
    background: var(--bg-elevated);
    border: 1px solid var(--rule);
    border-radius: 6px;
    padding: 12px 16px 14px;
}
.first-n figcaption {
    font-size: 11px;
    color: var(--ink-muted);
    margin-bottom: 8px;
}
.first-n table {
    border-collapse: collapse;
    width: 100%;
    font-size: 11px;
    font-variant-numeric: tabular-nums;
}
.first-n th {
    text-align: left;
    color: var(--ink-muted);
    font-weight: 400;
    padding: 3px 8px;
    font-size: 10.5px;
}
.first-n td {
    padding: 4px 8px;
    text-align: center;
}
.first-n td.add {
    text-align: left;
    color: var(--ink-soft);
}
.wcag table.delta td { font-size: 10px; }
.wcag table.delta td small {
    display: block;
    font-size: 9px;
    opacity: 0.65;
    font-weight: 600;
    letter-spacing: 0.04em;
}

/* legend */
.legend {
    display: flex;
    gap: 16px;
    align-items: center;
    font-size: 10px;
    color: var(--ink-muted);
    margin-top: 12px;
}
.legend i {
    display: inline-block;
    width: 14px;
    height: 14px;
    margin-right: 4px;
    border-radius: 2px;
    vertical-align: -2px;
}

/* colormaps */
section.cmap {
    background: var(--bg-elevated);
    border: 1px solid var(--rule);
    border-radius: 6px;
    padding: 16px 18px 20px;
    margin-bottom: 16px;
}
section.cmap h3 {
    margin: 0 0 12px;
    font-size: 13px;
    font-weight: 600;
    color: var(--ink);
}
/* compact colormap rows */
.cmap-row {
    display: grid;
    grid-template-columns: 90px 1fr 220px;
    align-items: center;
    gap: 14px;
    padding: 8px 0;
    border-bottom: 1px solid var(--rule);
}
.cmap-row:last-child { border-bottom: none; }
.cmap-name {
    font-size: 12px;
    font-weight: 600;
    color: var(--ink);
}
.badge {
    font-size: 10.5px;
    background: var(--bg-elevated);
    border: 1px solid var(--rule);
    border-radius: 3px;
    padding: 2px 8px;
    color: var(--ink-soft);
    font-variant-numeric: tabular-nums;
}
.badge em {
    font-style: normal;
    color: var(--ink-muted);
    font-size: 9.5px;
}
.gradient {
    display: flex;
    height: 22px;
    border-radius: 3px;
    overflow: hidden;
    border: 1px solid var(--rule);
}
.gradient span { flex: 1; display: block; }

/* hero mockups (homepage preview with live wcag badges) */
.hero-mockup-stack {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 22px;
}
.hero-mockup {
    border-radius: 8px;
    padding: 24px 26px 18px;
    font-family: var(--mono);
    line-height: 1.4;
    position: relative;
}
.hero-meta {
    position: absolute;
    top: 8px;
    right: 12px;
    font-size: 9px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    opacity: 0.55;
    color: var(--badge-color);
}
.hero-eyebrow {
    font-size: 10px;
    letter-spacing: 0.06em;
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 4px 0 14px;
}
.hero-eyebrow .rule-line {
    display: inline-block;
    width: 18px;
    height: 1.5px;
}
.hero-h1 {
    font-size: 34px;
    font-weight: 700;
    letter-spacing: -0.03em;
    line-height: 0.95;
    margin: 6px 0 0;
    display: flex;
    align-items: baseline;
    gap: 12px;
    flex-wrap: wrap;
}
.hero-h1 .word { white-space: nowrap; }
.hero-h1 .dot {
    display: inline-block;
    width: 0.28em;
    height: 0.28em;
    border-radius: 50%;
    vertical-align: 0.15em;
    margin: 0 1px;
}
.hero-accent {
    font-size: 22px;
    font-style: italic;
    margin: 2px 0 18px;
    display: flex;
    gap: 8px;
    align-items: baseline;
    flex-wrap: wrap;
}
.hero-subtitle {
    font-size: 13px;
    font-weight: 500;
    margin-bottom: 12px;
    display: flex;
    gap: 8px;
    align-items: baseline;
    flex-wrap: wrap;
}
.hero-prose {
    font-size: 12px;
    margin: 0 0 16px;
}
.hero-tagline {
    font-size: 16px;
    font-style: italic;
    margin-bottom: 18px;
    display: flex;
    gap: 8px;
    align-items: baseline;
    flex-wrap: wrap;
}
.hero-tagline .cursor {
    display: inline-block;
    width: 7px;
    height: 16px;
    vertical-align: -3px;
    margin: 0 4px 0 2px;
}
.hero-ctas {
    display: flex;
    gap: 12px;
    align-items: center;
    margin-bottom: 8px;
    flex-wrap: wrap;
}
.cta-primary, .cta-hover {
    font-size: 12px;
    font-family: inherit;
    border-radius: 4px;
    padding: 7px 13px;
    display: inline-block;
}
.cta-hover em { font-style: italic; opacity: 0.7; font-size: 10px; margin-left: 4px; }
.cta-secondary { font-size: 11px; }
.hero-cta-badges {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 10px;
    color: var(--badge-color);
    margin-bottom: 14px;
}
.hero-cta-badges span { display: flex; gap: 6px; align-items: center; }
.hero-surfaces {
    display: flex;
    gap: 6px;
    padding-top: 12px;
    margin-top: 4px;
}
.surface-chip {
    flex: 1;
    border: 1px solid;
    border-color: var(--badge-color);
    border-radius: 3px;
    padding: 6px 8px;
    font-size: 9.5px;
    letter-spacing: 0.02em;
    opacity: 0.7;
}

/* wcag contrast badges (live, inline next to text) */
.cbadge {
    display: inline-block;
    padding: 1px 6px;
    border-radius: 2px;
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 0.04em;
    font-style: normal;
    color: var(--badge-color);
    font-variant-numeric: tabular-nums;
    vertical-align: 1px;
}
.cb-ok   { background: rgba(0, 158, 115, 0.28); }
.cb-warn { background: rgba(230, 159, 0, 0.34); }
.cb-bad  { background: rgba(213, 94, 0, 0.42); }

/* surface sections */
section.surface {
    background: var(--bg-elevated);
    border: 1px solid var(--rule);
    border-radius: 6px;
    padding: 18px 20px;
    margin-bottom: 16px;
}
section.surface h3 {
    margin: 0 0 14px;
    font-size: 13px;
    font-weight: 600;
}
.surface-grid {
    display: grid;
    grid-template-columns: 1.6fr 1fr;
    gap: 24px;
    margin-bottom: 18px;
}

/* notes footer */
.notes {
    color: var(--ink-muted);
    font-size: 11px;
    line-height: 1.7;
    border-top: 1px solid var(--rule);
    padding-top: 20px;
}
.notes code { color: var(--ink-soft); }
"""

PAGE_JS = """
(function () {
    var t = document.querySelector('button.theme-toggle');
    t.addEventListener('click', function () {
        document.body.classList.toggle('theme-dark');
        t.textContent = document.body.classList.contains('theme-dark')
            ? '☀ light'
            : '◐ dark';
    });
})();
"""


def render_legend() -> str:
    return (
        '<div class="legend">'
        '<span><i style="background:rgba(0,158,115,0.45)"></i>ΔE ≥ 15 — optimal (Petroff 2021 target)</span>'
        '<span><i style="background:rgba(240,228,66,0.60)"></i>10 ≤ ΔE &lt; 15 — okay, below comfort threshold</span>'
        '<span><i style="background:rgba(230,159,0,0.50)"></i>5 ≤ ΔE &lt; 10 — marginal</span>'
        '<span><i style="background:rgba(213,94,0,0.55)"></i>ΔE &lt; 5 — confusable</span>'
        "</div>"
    )


def render_page() -> str:
    cat_rgb = np.array([hex_to_rgb1(hx) for hx in CATEGORICAL_HEX])
    cat_swatches = render_swatch_table(CATEGORICAL_HEX, CATEGORICAL_LABELS)
    cat_matrix = render_matrix_block(cat_rgb, CATEGORICAL_LABELS)
    sample_charts = render_sample_charts()
    first_n = render_first_n_summary()

    cmap_rows = "\n".join(render_colormap_row(name) for name in COLORMAPS)

    hero_pair = render_hero_mockup_pair()
    surface_light = render_surface_section(LIGHT_THEME_FULL, "light theme")
    surface_dark = render_surface_section(DARK_THEME_FULL, "dark theme")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>anyplot palette — baseline diagnostic</title>
<style>{PAGE_CSS}</style>
</head>
<body>
<header class="masthead">
    <h1>any<span class="dot">.</span>plot() — palette baseline</h1>
    <div class="meta">CAM02-UCS · colorspacious · severity 100%</div>
    <button class="theme-toggle">◐ dark</button>
</header>

<section class="domain">
    <h2>A. categorical plot palette</h2>
    <p class="lede">okabe-ito (positions 1–7) plus the two adaptive neutrals.
    sample charts render the typical 3-series case on the production bg-page surfaces.
    matrices side-by-side: <em>normal vision</em> left, <em>worst of the 3 cvd
    conditions</em> right. the "first-n" table below answers the practical question —
    at what palette size does the weakest pair drop below comfortable distinguishability?</p>
    {sample_charts}
    {first_n}
    {cat_swatches}
    {cat_matrix}
    {render_legend()}
</section>

<section class="domain">
    <h2>B. continuous plot colormaps</h2>
    <p class="lede">256-step samples of the three sequential / diverging colormaps named in
    style-guide §9.2. badge reports the worst-case adjacent-sample ΔE across normal + 3 cvd —
    a value above ~2.5 indicates visible banding under at least one condition.</p>
    {cmap_rows}
</section>

<section class="domain">
    <h2>C. website chrome — homepage hero &amp; surface tokens</h2>
    <p class="lede">tiny renditions of the anyplot.ai hero (style-guide §5.3) for both themes,
    with every visible text/UI element tagged with its live wcag contrast ratio. badges turn
    red the moment a colour change drops a pair below aa — that is the lighthouse-green
    check at a glance. surface tokens, ΔE matrices and wcag tables drill down below.</p>
    {hero_pair}
    {surface_light}
    {surface_dark}
    {render_legend()}
</section>

<footer class="notes">
    <p>method: ΔE is euclidean distance in CAM02-UCS (Luo et al. 2006), computed via
    <code>colorspacious.cspace_convert(rgb, "sRGB1", "CAM02-UCS")</code>.
    cvd simulation uses the machado et al. (2009) model exposed by
    <code>colorspacious</code>'s <code>sRGB1+CVD</code> space at <code>severity=100</code>
    for deuteranomaly, protanomaly, and tritanomaly.</p>
    <p>palette source: <code>core/images.py</code> · spec: <code>docs/reference/style-guide.md §4, §9</code>.
    references: okabe &amp; ito (2008), wong (2011), machado et al. (2009), petroff (2021).</p>
</footer>

<script>{PAGE_JS}</script>
</body>
</html>
"""


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT, help=f"Output HTML path (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(message)s",
    )
    log = logging.getLogger("palette-analysis")

    log.info("computing palette diagnostic …")
    html = render_page()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html, encoding="utf-8")
    size_kb = args.out.stat().st_size / 1024
    log.info("wrote %s (%.1f kB)", args.out, size_kb)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
