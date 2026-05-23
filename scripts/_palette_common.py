"""Shared helpers for palette analysis & variant generation scripts.

Imported by ``scripts/palette-analysis.py`` (baseline diagnostic) and
``scripts/palette-variants.py`` (candidate replacement palettes). Both
consumers are PEP-723 inline-dep scripts; this module deliberately has
no inline metadata because it is not run directly.

Public surface area:

- Color math: ``hex_to_rgb1``, ``rgb1_to_hex``, ``simulate_cvd``, ``to_jab``,
  ``pairwise_delta_e``, ``worst_cvd_pairwise_delta_e``, ``adjacent_delta_e``,
  ``worst_adjacent_jump``, ``wcag_relative_luminance``, ``wcag_contrast``,
  ``cmap_samples``.
- Thresholding: ``cell_class`` (4-step CAM02-UCS scale; see Petroff 2021).
- HTML rendering: ``render_swatch_table``, ``render_matrix_block``,
  ``render_first_n_summary``, ``render_sample_charts``, ``render_gradient``,
  ``render_colormap_row``, ``render_hero_mockup_pair``,
  ``render_surface_section``, ``render_legend``.
- Constants: ``CVD_SPECS``, ``CVD_LABELS``, ``CVD_ORDER``, ``NEUTRAL_LIGHT``,
  ``NEUTRAL_DARK``, ``SURFACE_KEYS``, ``SURFACE_LABELS``, ``LIGHT_THEME_FULL``,
  ``DARK_THEME_FULL``, ``PAGE_CSS``, ``PAGE_JS``.

CAM02-UCS is the chosen perceptual space because it underpins Petroff (2021)
and is the same one ``colorspacious.cspace_convert(..., "CAM02-UCS")`` exposes.
"""

from __future__ import annotations

import math
import sys
from html import escape as h
from pathlib import Path
from typing import Callable, Sequence

import matplotlib as mpl
import numpy as np
from colorspacious import cspace_convert


# -----------------------------------------------------------------------------
# Path bootstrap — so consumers can `from core.images import ...`
# -----------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.images import DARK_THEME, LIGHT_THEME  # noqa: E402


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

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
CVD_ONLY = ["deuter", "protan", "tritan"]

NEUTRAL_LIGHT = "#1A1A17"
NEUTRAL_DARK = "#F0EFE8"

SURFACE_KEYS = ["bg_page", "bg_surface", "bg_elevated", "ink", "ink_soft", "ink_muted"]
SURFACE_LABELS = ["bg-page", "bg-surface", "bg-elevated", "ink", "ink-soft", "ink-muted"]

# bg_elevated is in style-guide.md §4.2 but not in core.images themes — bridge.
LIGHT_THEME_FULL = {**LIGHT_THEME, "bg_elevated": "#FFFDF6"}
DARK_THEME_FULL = {**DARK_THEME, "bg_elevated": "#242420"}


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
    if cvd == "normal":
        return rgbs
    out = cspace_convert(rgbs, CVD_SPECS[cvd], "sRGB1")
    return np.clip(out, 0.0, 1.0)


def to_jab(rgbs: np.ndarray) -> np.ndarray:
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
    - breakdown[i, j, k] = ΔE under CVD_ONLY[k]
    """
    matrices = np.stack(
        [pairwise_delta_e(colors_rgb, cvd) for cvd in CVD_ONLY], axis=-1
    )
    return matrices.min(axis=-1), matrices


def adjacent_delta_e(samples_rgb: np.ndarray, cvd: str) -> np.ndarray:
    sim = simulate_cvd(samples_rgb, cvd)
    jab = to_jab(sim)
    return np.linalg.norm(np.diff(jab, axis=0), axis=1)


def worst_adjacent_jump(samples_rgb: np.ndarray) -> tuple[float, str]:
    worst_v = -1.0
    worst_cvd = "normal"
    for cvd in CVD_ORDER:
        v = float(adjacent_delta_e(samples_rgb, cvd).max())
        if v > worst_v:
            worst_v, worst_cvd = v, cvd
    return worst_v, CVD_LABELS[worst_cvd]


def cmap_samples(name: str, n: int = 256) -> np.ndarray:
    cmap = mpl.colormaps[name]
    return cmap(np.linspace(0.0, 1.0, n))[:, :3]


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


# -----------------------------------------------------------------------------
# Thresholding (Petroff 2021)
# -----------------------------------------------------------------------------


def cell_class(delta_e: float) -> str:
    """4-step CAM02-UCS threshold. Petroff (2021) uses 15 as the minimum
    target for comfortable categorical distinguishability."""
    if delta_e < 5:
        return "cell-bad"
    if delta_e < 10:
        return "cell-warn"
    if delta_e < 15:
        return "cell-meh"
    return "cell-ok"


def swatch_text_color(rgb1: np.ndarray) -> str:
    return "#1A1A17" if wcag_relative_luminance(rgb1) > 0.45 else "#F0EFE8"


# -----------------------------------------------------------------------------
# HTML rendering — domain helpers
# -----------------------------------------------------------------------------


def render_swatch_row(hex_str: str, label: str) -> str:
    rgb1 = hex_to_rgb1(hex_str)
    txt = swatch_text_color(rgb1)
    return (
        f'<div class="sw" style="background:{hex_str};color:{txt}">'
        f"<code>{hex_str}</code>"
        f"<span>{h(label)}</span>"
        "</div>"
    )


def render_swatch_table(hexes: Sequence[str], labels: Sequence[str]) -> str:
    items = "".join(render_swatch_row(hx, lab) for hx, lab in zip(hexes, labels))
    return f'<div class="swatch-row">{items}</div>'


def _render_one_matrix(
    M: np.ndarray,
    labels: Sequence[str],
    caption: str,
    tooltip_for: Callable[[int, int, float], str],
) -> str:
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


def render_matrix_block(colors_rgb: np.ndarray, labels: Sequence[str]) -> str:
    """Two ΔE matrices side-by-side: normal vision on the left, worst of the
    3 CVD conditions on the right. A pair fine normally but collapsing under
    CVD is visible as a left/right delta."""
    M_normal = pairwise_delta_e(colors_rgb, "normal")
    M_worst, M_breakdown = worst_cvd_pairwise_delta_e(colors_rgb)

    def _normal_tip(i: int, j: int, v: float) -> str:
        return f"{labels[i]} × {labels[j]} · normal ΔE={v:.2f}"

    def _worst_tip(i: int, j: int, v: float) -> str:
        breakdown = " · ".join(
            f"{CVD_LABELS[cvd]}={float(M_breakdown[i, j, k]):.1f}"
            for k, cvd in enumerate(CVD_ONLY)
        )
        return f"{labels[i]} × {labels[j]} · worst-cvd ΔE={v:.2f} ({breakdown})"

    left = _render_one_matrix(M_normal, labels, "normal vision", _normal_tip)
    right = _render_one_matrix(
        M_worst, labels, "worst of 3 cvd (deuter · protan · tritan)", _worst_tip
    )
    return f'<div class="matrix-pair">{left}{right}</div>'


def render_first_n_summary(
    palette_hexes: Sequence[str], palette_names: Sequence[str]
) -> str:
    """If you only use the first N colours (in the given order), what's the
    weakest pair under normal vision vs worst CVD? Answers the practical
    question more directly than the full matrix."""
    hues_rgb = np.array([hex_to_rgb1(hx) for hx in palette_hexes])
    M_normal_full = pairwise_delta_e(hues_rgb, "normal")
    cvd_full = np.stack(
        [pairwise_delta_e(hues_rgb, c) for c in CVD_ONLY], axis=-1
    ).min(axis=-1)

    rows = []
    n_total = len(palette_hexes)
    for n in range(2, n_total + 1):
        triu = np.triu_indices(n, k=1)
        v_norm = float(M_normal_full[:n, :n][triu].min())
        v_worst = float(cvd_full[:n, :n][triu].min())
        added = palette_names[n - 1]
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


def render_sample_chart(
    theme: dict[str, str], theme_label: str, series_hexes: Sequence[str]
) -> str:
    """Inline SVG mini line-chart on the theme's bg-page. Series count and
    colours are explicit so this works for any palette."""
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

    grid_lines = "".join(
        f'<line x1="{margin_l}" y1="{margin_t + plot_h * f:.1f}" '
        f'x2="{margin_l + plot_w}" y2="{margin_t + plot_h * f:.1f}" '
        f'stroke="{grid}" stroke-width="1" />'
        for f in (0.25, 0.5, 0.75)
    )

    polylines: list[str] = []
    for i, color in enumerate(series_hexes):
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


def render_sample_bars(
    theme: dict[str, str], theme_label: str, series_hexes: Sequence[str]
) -> str:
    """Inline SVG bar chart: one group per series, 4 categories per group.
    Lets the palette show its identity in a categorical (not continuous)
    context — a common case for the picker not covered by the line chart."""
    width, height = 460, 240
    margin_l, margin_r, margin_t, margin_b = 36, 18, 22, 26
    plot_w = width - margin_l - margin_r
    plot_h = height - margin_t - margin_b

    bg = theme["bg_page"]
    ink_muted = theme["ink_muted"]
    rule = theme.get("rule", "#DFDDD6")
    is_light = bg.upper().startswith("#F")
    grid = "rgba(26,26,23,0.06)" if is_light else "rgba(240,239,232,0.06)"

    n_groups = 4
    n_series = len(series_hexes)
    # Heights per (group, series) — fabricated but visually believable
    rng = [(0.42, 0.78, 0.55, 0.66),  # series 0
           (0.58, 0.45, 0.71, 0.49),  # series 1
           (0.66, 0.60, 0.38, 0.74),  # series 2
           (0.36, 0.55, 0.62, 0.41)]  # series 3
    group_gap = plot_w / n_groups
    bar_w = (group_gap * 0.78) / max(n_series, 1)
    bar_gap = (group_gap - bar_w * n_series) / 2

    grid_lines = "".join(
        f'<line x1="{margin_l}" y1="{margin_t + plot_h * f:.1f}" '
        f'x2="{margin_l + plot_w}" y2="{margin_t + plot_h * f:.1f}" '
        f'stroke="{grid}" stroke-width="1" />'
        for f in (0.25, 0.5, 0.75)
    )

    bars: list[str] = []
    for g in range(n_groups):
        for i, color in enumerate(series_hexes):
            val = rng[i % len(rng)][g]
            bx = margin_l + g * group_gap + bar_gap + i * bar_w
            bh = val * plot_h
            by = margin_t + plot_h - bh
            bars.append(
                f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w - 1.5:.1f}" '
                f'height="{bh:.1f}" fill="{color}" rx="1.5" />'
            )

    axes = (
        f'<line x1="{margin_l}" y1="{margin_t}" '
        f'x2="{margin_l}" y2="{margin_t + plot_h}" stroke="{rule}" stroke-width="1" />'
        f'<line x1="{margin_l}" y1="{margin_t + plot_h}" '
        f'x2="{margin_l + plot_w}" y2="{margin_t + plot_h}" stroke="{rule}" stroke-width="1" />'
    )

    tick_y = margin_t + plot_h + 14
    ticks = "".join(
        f'<text x="{margin_l + (g + 0.5) * group_gap:.1f}" y="{tick_y}" '
        f'fill="{ink_muted}" font-size="9" text-anchor="middle">Q{g + 1}</text>'
        for g in range(n_groups)
    )

    label = (
        f'<text x="{margin_l}" y="{margin_t - 6}" fill="{ink_muted}" '
        f'font-size="10" text-anchor="start">{h(theme_label)} — bars</text>'
    )

    return (
        f'<svg viewBox="0 0 {width} {height}" class="sample-chart" '
        f'preserveAspectRatio="xMidYMid meet" '
        f'style="background:{bg};border:1px solid {rule};border-radius:6px">'
        f"{label}{grid_lines}{axes}{''.join(bars)}{ticks}"
        "</svg>"
    )


def render_sample_scatter(
    theme: dict[str, str], theme_label: str, series_hexes: Sequence[str]
) -> str:
    """Inline SVG scatter chart: 4 clusters, ~20 points each. Tests how the
    palette reads when colours appear in dense small marks rather than long
    lines or wide bars."""
    width, height = 460, 240
    margin_l, margin_r, margin_t, margin_b = 36, 18, 22, 26
    plot_w = width - margin_l - margin_r
    plot_h = height - margin_t - margin_b

    bg = theme["bg_page"]
    ink_muted = theme["ink_muted"]
    rule = theme.get("rule", "#DFDDD6")
    is_light = bg.upper().startswith("#F")
    grid = "rgba(26,26,23,0.06)" if is_light else "rgba(240,239,232,0.06)"

    # Reproducible "random" jitter via a fixed sequence
    import random as _r
    rnd = _r.Random(42)

    centres = [(0.25, 0.30), (0.70, 0.25), (0.30, 0.70), (0.75, 0.72)]
    grid_lines = "".join(
        f'<line x1="{margin_l}" y1="{margin_t + plot_h * f:.1f}" '
        f'x2="{margin_l + plot_w}" y2="{margin_t + plot_h * f:.1f}" '
        f'stroke="{grid}" stroke-width="1" />'
        for f in (0.25, 0.5, 0.75)
    )

    dots: list[str] = []
    for i, color in enumerate(series_hexes):
        cx_frac, cy_frac = centres[i % len(centres)]
        for _ in range(22):
            jx = rnd.gauss(0, 0.08)
            jy = rnd.gauss(0, 0.08)
            x = max(0.02, min(0.98, cx_frac + jx))
            y = max(0.02, min(0.98, cy_frac + jy))
            px = margin_l + x * plot_w
            py = margin_t + (1 - y) * plot_h
            dots.append(
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.2" '
                f'fill="{color}" fill-opacity="0.75" />'
            )

    axes = (
        f'<line x1="{margin_l}" y1="{margin_t}" '
        f'x2="{margin_l}" y2="{margin_t + plot_h}" stroke="{rule}" stroke-width="1" />'
        f'<line x1="{margin_l}" y1="{margin_t + plot_h}" '
        f'x2="{margin_l + plot_w}" y2="{margin_t + plot_h}" stroke="{rule}" stroke-width="1" />'
    )

    label = (
        f'<text x="{margin_l}" y="{margin_t - 6}" fill="{ink_muted}" '
        f'font-size="10" text-anchor="start">{h(theme_label)} — scatter</text>'
    )

    return (
        f'<svg viewBox="0 0 {width} {height}" class="sample-chart" '
        f'preserveAspectRatio="xMidYMid meet" '
        f'style="background:{bg};border:1px solid {rule};border-radius:6px">'
        f"{label}{grid_lines}{axes}{''.join(dots)}"
        "</svg>"
    )


def render_sample_charts(palette_hexes: Sequence[str], n_series: int = 3) -> str:
    """Render a 3×2 grid of sample charts (line / bar / scatter × light / dark
    bg) using the first ``n_series`` colours from the given palette. Default
    3 matches the style-guide ideal; pass n_series=4 for variant pages that
    showcase the "first-4 most beautiful" subset."""
    series = list(palette_hexes[:n_series])
    return (
        '<div class="sample-charts">'
        f"{render_sample_chart(LIGHT_THEME_FULL, 'light · lines', series)}"
        f"{render_sample_chart(DARK_THEME_FULL, 'dark · lines', series)}"
        f"{render_sample_bars(LIGHT_THEME_FULL, 'light', series)}"
        f"{render_sample_bars(DARK_THEME_FULL, 'dark', series)}"
        f"{render_sample_scatter(LIGHT_THEME_FULL, 'light', series)}"
        f"{render_sample_scatter(DARK_THEME_FULL, 'dark', series)}"
        "</div>"
    )


def render_gradient(samples_rgb: np.ndarray) -> str:
    spans = "".join(
        f'<span style="background:{rgb1_to_hex(s)}"></span>' for s in samples_rgb
    )
    return f'<div class="gradient">{spans}</div>'


def render_colormap_row(name: str, samples_rgb: np.ndarray | None = None) -> str:
    """Single-row compact colormap display. If ``samples_rgb`` is provided,
    use it directly (custom colormap); otherwise sample from matplotlib by
    ``name`` (e.g. 'viridis', 'cividis', 'BrBG')."""
    if samples_rgb is None:
        samples_rgb = cmap_samples(name, 256)
    worst, worst_cond = worst_adjacent_jump(samples_rgb)
    return (
        f'<div class="cmap-row">'
        f'<span class="cmap-name">{h(name)}</span>'
        f"{render_gradient(samples_rgb)}"
        f'<span class="badge">worst Δ: {worst:.2f} <em>({h(worst_cond)})</em></span>'
        "</div>"
    )


def _peaks_png_b64(samples_rgb: np.ndarray) -> str:
    """Render the classic peaks function to a small PNG with the given
    colormap and return a base64 data URI."""
    import base64
    import io

    from PIL import Image

    w, h_px = 240, 144
    x = np.linspace(-2.2, 2.2, w)
    y = np.linspace(-1.3, 1.3, h_px)
    X, Y = np.meshgrid(x, y)
    Z = (
        3 * (1 - X) ** 2 * np.exp(-X ** 2 - (Y + 1) ** 2)
        - 10 * (X / 5 - X ** 3 - Y ** 5) * np.exp(-X ** 2 - Y ** 2)
        - (1.0 / 3) * np.exp(-(X + 1) ** 2 - Y ** 2)
    )
    Zn = (Z - Z.min()) / (Z.max() - Z.min())
    idx = np.clip((Zn * (len(samples_rgb) - 1)).round().astype(int), 0, len(samples_rgb) - 1)
    rgb = (samples_rgb[idx] * 255).astype(np.uint8)
    img = Image.fromarray(rgb, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def render_cmap_demo(samples_rgb: np.ndarray, label: str = "") -> str:
    """Apply the 256-step colormap to MATLAB's peaks bivariate function and
    return an HTML figure with the rendered PNG inlined as a data URI,
    framed on BOTH the production light-bg and dark-bg surfaces side by
    side. The peaks pixels are identical in each frame; the surrounding
    chrome (frame colour, axis/caption text) changes so the user can see
    how the cmap reads against each surface without toggling the theme.
    """
    src = _peaks_png_b64(samples_rgb)
    caption = f'<figcaption>{h(label)}</figcaption>' if label else ""
    light = LIGHT_THEME_FULL
    dark = DARK_THEME_FULL
    frame = (
        '<div class="cmap-demo-frame" style="background:{bg};color:{ink};'
        'border:1px solid {rule};border-radius:6px;padding:8px">'
        '<div style="font-size:10px;color:{muted};margin-bottom:6px">'
        '{theme} — bg-page {bg}</div>'
        '<img src="{src}" '
        'alt="continuous palette applied to the peaks bivariate function" '
        'style="width:100%;height:auto;display:block;border-radius:4px">'
        '</div>'
    )
    pair = (
        '<div class="cmap-demo-pair">'
        + frame.format(
            theme="light", bg=light["bg_page"], ink=light["ink"],
            muted=light["ink_muted"], rule=light.get("rule", "#DFDDD6"), src=src,
        )
        + frame.format(
            theme="dark", bg=dark["bg_page"], ink=dark["ink"],
            muted=dark["ink_muted"], rule=dark.get("rule", "#1E1E1B"), src=src,
        )
        + "</div>"
    )
    return f'<figure class="cmap-demo">{pair}{caption}</figure>'


def _wcag_badge(fg_hex: str, bg_hex: str, large: bool = False) -> str:
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


def render_hero_mockup(
    theme: dict[str, str], theme_label: str, brand_hex: str
) -> str:
    """Tiny rendition of the anyplot.ai hero (style-guide §5.3). Every visible
    text/UI element carries its WCAG ratio so a colour change instantly shows
    whether everything is still in the green-zone for Lighthouse."""
    bg = theme["bg_page"]
    bg_elev = theme["bg_elevated"]
    ink = theme["ink"]
    ink_soft = theme["ink_soft"]
    ink_muted = theme["ink_muted"]
    rule = theme.get("rule", "#DFDDD6")
    green = brand_hex

    badge_text = ink_muted

    eyebrow_badge = _wcag_badge(ink_muted, bg)
    h1_badge = _wcag_badge(ink, bg, large=True)
    dot_badge = _wcag_badge(green, bg, large=True)
    accent_badge = _wcag_badge(ink, bg, large=True)
    subtitle_badge = _wcag_badge(ink, bg)
    prose_badge = _wcag_badge(ink_soft, bg)
    tagline_badge = _wcag_badge(ink, bg, large=True)
    cta_badge = _wcag_badge(bg, ink)
    cta_hover_badge = _wcag_badge("#FFFFFF", green, large=True)
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


def render_hero_mockup_pair(brand_hex: str) -> str:
    return (
        '<div class="hero-mockup-stack">'
        f"{render_hero_mockup(LIGHT_THEME_FULL, 'light', brand_hex)}"
        f"{render_hero_mockup(DARK_THEME_FULL, 'dark', brand_hex)}"
        "</div>"
    )


def render_wcag_table(theme: dict[str, str]) -> str:
    bgs = ["bg_page", "bg_surface", "bg_elevated"]
    inks = ["ink", "ink_soft", "ink_muted"]
    head = "<tr><th></th>" + "".join(
        f"<th>{h(k.replace('_', '-'))}</th>" for k in bgs
    ) + "</tr>"
    rows = []
    for ink_key in inks:
        cells = []
        for bg_key in bgs:
            ratio = wcag_contrast(hex_to_rgb1(theme[ink_key]), hex_to_rgb1(theme[bg_key]))
            grade = "AAA" if ratio >= 7 else "AA" if ratio >= 4.5 else "FAIL"
            cls = (
                "cell-ok"
                if grade == "AAA"
                else "cell-warn"
                if grade == "AA"
                else "cell-bad"
            )
            cells.append(f'<td class="{cls}">{ratio:.2f}<small>{grade}</small></td>')
        rows.append(
            f'<tr><th>{h(ink_key.replace("_", "-"))}</th>{"".join(cells)}</tr>'
        )
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


def render_legend() -> str:
    return (
        '<div class="legend">'
        '<span><i style="background:rgba(0,158,115,0.45)"></i>ΔE ≥ 15 — optimal (Petroff 2021 target)</span>'
        '<span><i style="background:rgba(240,228,66,0.60)"></i>10 ≤ ΔE &lt; 15 — okay, below comfort threshold</span>'
        '<span><i style="background:rgba(230,159,0,0.50)"></i>5 ≤ ΔE &lt; 10 — marginal</span>'
        '<span><i style="background:rgba(213,94,0,0.55)"></i>ΔE &lt; 5 — confusable</span>'
        "</div>"
    )


# -----------------------------------------------------------------------------
# Shared CSS + JS — load once per page
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

/* sample charts */
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
.cell-ok   { background: rgba(0,158,115,0.22); }
.cell-meh  { background: rgba(240,228,66,0.30); }
.cell-warn { background: rgba(230,159,0,0.26); }
.cell-bad  { background: rgba(213,94,0,0.30); }
.diag      { background: var(--rule); }
.wcag table.delta td { font-size: 10px; }
.wcag table.delta td small {
    display: block;
    font-size: 9px;
    opacity: 0.65;
    font-weight: 600;
    letter-spacing: 0.04em;
}

.matrix-pair {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-top: 8px;
}
@media (max-width: 1100px) { .matrix-pair { grid-template-columns: 1fr; } }

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
.first-n td.add { text-align: left; color: var(--ink-soft); }

/* legend */
.legend {
    display: flex;
    gap: 16px;
    align-items: center;
    font-size: 10px;
    color: var(--ink-muted);
    margin-top: 12px;
    flex-wrap: wrap;
}
.legend i {
    display: inline-block;
    width: 14px;
    height: 14px;
    margin-right: 4px;
    border-radius: 2px;
    vertical-align: -2px;
}

/* compact colormap rows */
.cmap-row {
    display: grid;
    grid-template-columns: 130px 1fr 220px;
    align-items: center;
    gap: 14px;
    padding: 8px 0;
    border-bottom: 1px solid var(--rule);
}
.cmap-row:last-child { border-bottom: none; }

/* 2D cmap demo: peaks function rendered with the variant's colormap */
.cmap-demo {
    margin: 14px 0 4px;
    padding: 0;
}
.cmap-demo figcaption {
    font-size: 11px;
    color: var(--muted);
    margin-top: 6px;
    font-style: italic;
}
.cmap-demo-pair {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}
.cmap-demo-frame {
    overflow: hidden;
}
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

/* hero mockups */
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

/* surface section layout */
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

/* Shared top nav used on baseline, grid, compare, and every variant page */
.variant-nav {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin: 4px 0 24px;
}
.variant-nav a {
    font-size: 11px;
    padding: 5px 10px;
    border-radius: 4px;
    border: 1px solid var(--rule);
    background: var(--bg-elevated);
    color: var(--ink-soft);
    text-decoration: none;
    transition: color 60ms, border-color 60ms;
}
.variant-nav a.current {
    background: var(--ok-green);
    color: #ffffff;
    border-color: var(--ok-green);
    font-weight: 600;
}
.variant-nav a:hover:not(.current) {
    color: var(--ok-green);
    border-color: var(--ok-green);
}
"""

PAGE_JS = """
(function () {
    var t = document.querySelector('button.theme-toggle');
    if (!t) return;
    t.addEventListener('click', function () {
        document.body.classList.toggle('theme-dark');
        t.textContent = document.body.classList.contains('theme-dark')
            ? '☀ light'
            : '◐ dark';
    });
})();
"""
