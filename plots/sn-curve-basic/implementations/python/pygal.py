"""anyplot.ai
sn-curve-basic: S-N Curve (Wöhler Curve)
Library: pygal 3.1.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-20
"""

import math
import os
import re
import sys

import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Remove current dir from sys.path to avoid shadowing the pygal package
_cwd = sys.path[0] if sys.path[0] else "."
if _cwd in sys.path:
    sys.path.remove(_cwd)

import pygal  # noqa: E402
from cairosvg import svg2png  # noqa: E402
from pygal.style import Style  # noqa: E402


sys.path.insert(0, _cwd)

# Constants
ULTIMATE_STRENGTH = 520  # MPa, medium-carbon steel
YIELD_STRENGTH = 350  # MPa
ENDURANCE_LIMIT = 190  # MPa
LCF_END = 1e3  # low-cycle fatigue ends here (cycles)
HCF_END = 1e6  # high-cycle fatigue ends here, infinite life begins (cycles)

# Columns: set these to your table's column names
CYCLES = "Cycles to Failure (N)"  # role: cycles
STRESS = "Stress Amplitude (MPa)"  # role: stress

# Data: replace this block with your own table, for example df = pd.read_csv("fatigue.csv")
np.random.seed(42)
stress_levels = np.array([450, 400, 350, 300, 275, 250, 225, 210, 200, 195])
base_cycles = np.array([1e2, 5e2, 2e3, 1e4, 3e4, 1e5, 4e5, 1e6, 5e6, 1e7])
cycles_data: list[float] = []
stress_data: list[float] = []
for stress, base_n in zip(stress_levels, base_cycles, strict=True):
    n_samples = np.random.randint(3, 6)
    cycles_data.extend(base_n * np.exp(np.random.normal(0, 0.3, n_samples)))
    stress_data.extend([stress] * n_samples)
df = pd.DataFrame({CYCLES: cycles_data, STRESS: stress_data})

# Plot: reads only df and the constants above
valid = df.dropna(subset=[CYCLES, STRESS])
cycles_arr = valid[CYCLES].to_numpy(dtype=float)
stress_arr = valid[STRESS].to_numpy(dtype=float)

# Basquin equation fit: S = A * N^b  (linear in log-log space)
coeffs = np.polyfit(np.log10(cycles_arr), np.log10(stress_arr), 1)
b = coeffs[0]
A = 10 ** coeffs[1]

# Axis extent: whole decades around the data and the reference lines
x_lo_log = math.log10(cycles_arr.min() * 0.9)
x_hi_log = math.log10(cycles_arr.max() * 1.1)
x_lo, x_hi = 10.0**x_lo_log, 10.0**x_hi_log
x_decades = list(range(math.ceil(x_lo_log), math.floor(x_hi_log) + 1))
fit_cycles = np.logspace(x_lo_log, x_hi_log, 100)
fit_stress = A * (fit_cycles**b)

stress_floor = min(stress_arr.min(), ENDURANCE_LIMIT)
stress_top = max(stress_arr.max(), ULTIMATE_STRENGTH)
y_lo, y_hi = stress_floor * 0.87, stress_top * 1.155

# pygal's logarithmic=True only applies to the x-axis in XY mode.
# Log10-transform all stress (y) values for a true log-log plot,
# then map explicit y_labels back to human-readable MPa values.


def _zone(c: float) -> str:
    if c < LCF_END:
        return "Low-Cycle Fatigue"
    return "High-Cycle Fatigue" if c < HCF_END else "Near Endurance Limit"


xy_points = [
    {
        "value": (float(c), math.log10(float(s))),
        "label": f"{_zone(float(c))}: {float(c):.2e} cycles @ {float(s):.0f} MPa",
    }
    for c, s in zip(cycles_arr, stress_arr, strict=True)
]
fit_points = [
    {"value": (float(c), math.log10(float(s))), "label": f"Fit: {float(c):.2e} → {float(s):.0f} MPa"}
    for c, s in zip(fit_cycles, fit_stress, strict=True)
]

ult_log = math.log10(ULTIMATE_STRENGTH)
yld_log = math.log10(YIELD_STRENGTH)
end_log = math.log10(ENDURANCE_LIMIT)

# ── Style ─────────────────────────────────────────────────────────────────────
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=3,
    opacity=0.75,
    opacity_hover=1.0,
)

# ── Chart ─────────────────────────────────────────────────────────────────────
chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="Steel Fatigue · sn-curve-basic · python · pygal · anyplot.ai",
    x_title=CYCLES,
    y_title=STRESS,
    logarithmic=True,
    show_dots=True,
    dots_size=12,
    stroke=True,
    show_x_guides=False,
    show_y_guides=True,
    x_label_rotation=0,
    legend_at_bottom=True,
    legend_box_size=44,
    margin=100,
    # Tighter y-range: start just below endurance limit to reduce empty bottom space
    range=(math.log10(y_lo), math.log10(y_hi)),
    xrange=(x_lo, x_hi),
    value_formatter=lambda xy: f"{xy[0]:.2e} cycles, {10 ** xy[1]:.0f} MPa" if isinstance(xy, tuple) else str(xy),
)

# X-axis: major log decades
chart.x_labels = [10.0**d for d in x_decades]

# Y-axis: stress labels within the tightened range
y_tick_vals = [v for v in range(0, int(y_hi) + 1, 50) if y_lo < v < y_hi]
chart.y_labels = [{"value": math.log10(v), "label": str(v)} for v in y_tick_vals]

# Series: Test Data first (most prominent), then derived/reference
chart.add("Test Data", xy_points, dots_size=16, stroke=False, show_dots=True)
chart.add(
    "Basquin Fit (S = A·N^b)",
    fit_points,
    stroke=True,
    show_dots=False,
    stroke_style={"width": 9, "dasharray": "20, 10"},
)
# Distinct stroke styles per reference line: solid / long-dash / short-dash
chart.add(
    f"Ultimate Strength, Su = {ULTIMATE_STRENGTH} MPa",
    [(x_lo, ult_log), (x_hi, ult_log)],
    stroke=True,
    show_dots=False,
    stroke_style={"width": 7, "opacity": 0.80},
)
chart.add(
    f"Yield Strength, Sy = {YIELD_STRENGTH} MPa",
    [(x_lo, yld_log), (x_hi, yld_log)],
    stroke=True,
    show_dots=False,
    stroke_style={"width": 7, "dasharray": "30, 8", "opacity": 0.80},
)
# Endurance limit: thicker + shorter dashes for better visibility on light bg
chart.add(
    f"Endurance Limit, Se = {ENDURANCE_LIMIT} MPa",
    [(x_lo, end_log), (x_hi, end_log)],
    stroke=True,
    show_dots=False,
    stroke_style={"width": 12, "dasharray": "14, 5", "opacity": 0.90},
)


# ── SVG injection: fatigue region bands ───────────────────────────────────────


def _get_plot_dims(svg: str) -> tuple[float, float]:
    """Return (width, height) of the plot area from its inner background rect."""
    # Find the opening tag of <g class="plot"> (exact class, not "plot overlay")
    plot_tag = re.search(r'<g[^>]*\bclass="plot"[^>]*>', svg)
    if plot_tag:
        # Find the first <rect> after the plot group tag (that's the background rect)
        rect_m = re.search(r"<rect\b[^>]+>", svg[plot_tag.end() :])
        if rect_m:
            attrs: dict[str, float] = {}
            for attr in ("width", "height"):
                am = re.search(rf'\b{attr}="([0-9.]+)"', rect_m.group(0))
                if am:
                    attrs[attr] = float(am.group(1))
            if "width" in attrs and "height" in attrs:
                return attrs["width"], attrs["height"]
    # Fallback for width=3200, height=1800, margin=100 with our font sizes
    return 2760.0, 1290.0


def _inject_region_bands(svg: str, theme: str) -> str:
    """Inject fatigue-region bands and labels into the SVG, in plot-local coordinates."""
    pw, ph = _get_plot_dims(svg)

    # X-axis: log10(x_lo) → log10(x_hi) mapped to [0, pw]
    def log_to_x(n: float) -> float:
        return (math.log10(n) - x_lo_log) / (x_hi_log - x_lo_log) * pw

    x_lcf = log_to_x(LCF_END)  # LCF | HCF boundary
    x_hcf = log_to_x(HCF_END)  # HCF | Infinite Life boundary

    # Semi-transparent fills (fill + fill-opacity for cairosvg compatibility)
    if theme == "light":
        region_fills = [("#CC8888", "0.10"), ("#88AA88", "0.10"), ("#8888BB", "0.10")]
        div_stroke = "#6B6A63"
        lbl_fill = "#6B6A63"
    else:
        region_fills = [("#BB5555", "0.09"), ("#55994A", "0.09"), ("#5577BB", "0.09")]
        div_stroke = "#A8A79F"
        lbl_fill = "#A8A79F"

    # Labels near the top of the plot area (above all data points)
    lbl_y = 55.0
    lbl_sz = 38

    parts = ['<g class="fatigue-regions">']

    # Three region fills
    for rx, rw, (rfill, rop) in [
        (0.0, x_lcf, region_fills[0]),
        (x_lcf, x_hcf - x_lcf, region_fills[1]),
        (x_hcf, pw - x_hcf, region_fills[2]),
    ]:
        parts.append(
            f'<rect x="{rx:.1f}" y="0" width="{rw:.1f}" height="{ph:.1f}" '
            f'fill="{rfill}" fill-opacity="{rop}" stroke="none"/>'
        )

    # Subtle vertical dividers at region boundaries
    for xd in (x_lcf, x_hcf):
        parts.append(
            f'<line x1="{xd:.1f}" y1="0" x2="{xd:.1f}" y2="{ph:.1f}" '
            f'stroke="{div_stroke}" stroke-width="2" stroke-dasharray="8,4" opacity="0.30"/>'
        )

    # Region labels centered in each band
    for lx, lbl in [
        (x_lcf / 2, "Low-Cycle"),
        ((x_lcf + x_hcf) / 2, "High-Cycle Fatigue"),
        ((x_hcf + pw) / 2, "Infinite Life"),
    ]:
        parts.append(
            f'<text x="{lx:.1f}" y="{lbl_y:.1f}" text-anchor="middle" '
            f'fill="{lbl_fill}" font-size="{lbl_sz}" font-family="sans-serif" '
            f'opacity="0.55">{lbl}</text>'
        )

    parts.append("</g>")
    region_block = "".join(parts)

    # Insert immediately after the plot background rect so bands appear above bg,
    # but behind grid guides and data series.
    plot_tag = re.search(r'<g[^>]*\bclass="plot"[^>]*>', svg)
    if plot_tag:
        after_tag = svg[plot_tag.end() :]
        bg_rect = re.search(r"<rect\b[^>]+>", after_tag)
        if bg_rect:
            insert_pos = plot_tag.end() + bg_rect.end()
            return svg[:insert_pos] + region_block + svg[insert_pos:]

    # Fallback: insert just before </svg>
    return svg.replace("</svg>", region_block + "</svg>")


# ── Render & save ─────────────────────────────────────────────────────────────
svg_raw = chart.render()

# Inject region bands into a copy of the SVG, then convert to PNG via cairosvg
svg_enhanced = _inject_region_bands(svg_raw.decode("utf-8"), THEME).encode("utf-8")
svg2png(bytestring=svg_enhanced, write_to=f"plot-{THEME}.png")

# HTML export uses the original SVG (preserves full pygal interactivity)
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(svg_raw)
