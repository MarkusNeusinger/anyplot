"""anyplot.ai
heatmap-rainflow: Rainflow Counting Matrix for Fatigue Analysis
Library: pygal 3.1.3 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-28
"""

import math
import os
from itertools import pairwise

import cairosvg
import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens — Imprint palette chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
AMBER = "#DDCC77"  # Imprint amber anchor, outside the categorical pool

# Imprint sequential ramp for filled cells (fields stops, per theme)
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.369, "#009E73"), (0.803, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#404C02"), (0.487, "#009E73"), (1.0, "#CDD9FF")]
)


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


# Columns: set these to your table's column names
AMPLITUDE = "Stress Amplitude (MPa)"  # role: amplitude
MEAN = "Mean Stress (MPa)"  # role: mean
COUNT = "Cycle Count"  # role: count

# Data: replace this block with your own table, for example df = pd.read_csv("rainflow.csv")
# Wind turbine blade root fatigue loading (variable-amplitude spectrum), one row per bin
np.random.seed(42)
n_bins = 20
amp_edges = np.linspace(0, 200, n_bins + 1)
mean_edges = np.linspace(-50, 250, n_bins + 1)
amp_centers = (amp_edges[:-1] + amp_edges[1:]) / 2
mean_centers = (mean_edges[:-1] + mean_edges[1:]) / 2

rows = []
for amp in amp_centers:
    for mean_val in mean_centers:
        primary = np.exp(-amp / 28) * np.exp(-((mean_val - 100) ** 2) / (2 * 55**2))
        vibration = 0.5 * np.exp(-amp / 10) * np.exp(-((mean_val - 55) ** 2) / (2 * 20**2))
        base = 9000 * (primary + vibration) * (1 + 0.2 * np.random.randn())
        empty = amp + abs(mean_val - 100) > 220 or base < 2
        rows.append((float(amp), float(mean_val), 0 if empty else int(round(max(0, base)))))
df = pd.DataFrame(rows, columns=[AMPLITUDE, MEAN, COUNT])

# Plot: reads only df and the constants above
table = df.pivot_table(index=AMPLITUDE, columns=MEAN, values=COUNT, sort=False, dropna=False)
table = table.iloc[::-1]  # high amplitude at the top, the fatigue-matrix convention
values = table.to_numpy(dtype=float)
nr, nc = values.shape
counted = values[values > 0]
lo, hi = float(counted.min()), float(counted.max())

# Bin edges from the bin centers: ticks name the edges the cells share
amp_step = float(np.diff(np.sort(df[AMPLITUDE].unique())).min())
mean_step = float(np.diff(np.sort(df[MEAN].unique())).min())
amp_lo = float(df[AMPLITUDE].min()) - amp_step / 2
mean_lo = float(df[MEAN].min()) - mean_step / 2
TICK_EVERY = 4

# pygal draws title, background and the SVG root; the matrix is added as plain SVG nodes
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
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

chart = pygal.XY(
    width=2400,
    height=2400,
    style=custom_style,
    title="heatmap-rainflow · python · pygal · anyplot.ai",
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    margin=80,
    explicit_size=True,
    pretty_print=True,
)
chart.add("", [(0, 0)], show_dots=False, stroke=False)
chart.setup()  # builds the SVG tree, which the nodes below are added to
svg, root = chart.svg, chart.svg.root


def svg_text(x, y, label, size, fill=INK, anchor="middle", weight="normal", rotation=None):
    node = svg.node(root, "text", x=x, y=y)
    node.set("text-anchor", anchor)
    node.set("fill", fill)
    node.set("style", f"font-size:{size}px;font-weight:{weight};font-family:sans-serif")
    if rotation is not None:
        node.set("transform", f"rotate({rotation}, {x}, {y})")
    node.text = label


# Grid geometry
x0, y0 = 300, 330
cell_w, cell_h = 1600 / nc, 1640 / nr
gap = 2
gw, gh = nc * cell_w, nr * cell_h

svg_text(
    x0 + gw / 2,
    y0 - 50,
    "Wind Turbine Blade Root — Variable Amplitude Fatigue Spectrum",
    44,
    fill=INK_MUTED,
    weight="300",
)

pad = 14
panel = svg.node(root, "rect", x=x0 - pad, y=y0 - pad, width=gw + 2 * pad, height=gh + 2 * pad, rx=6, ry=6)
panel.set("fill", ELEVATED_BG)
panel.set("stroke", INK_MUTED)
panel.set("stroke-width", "0.8")
panel.set("stroke-opacity", "0.4")

# Cells: log color from the lowest counted value; empty bins take the page color with an outline
peak = np.unravel_index(np.nanargmax(values), values.shape)
for i, j in np.ndindex(nr, nc):
    val = values[i, j]
    if np.isnan(val):
        continue
    cx, cy = x0 + j * cell_w + gap / 2, y0 + i * cell_h + gap / 2
    fill, stroke, sw = PAGE_BG, INK_MUTED, "0.5"
    if val > 0:
        fill, stroke, sw = ramp_color(SEQ_FIELDS, math.log(val / lo) / math.log(hi / lo)), "none", "0.5"
    if (i, j) == peak:
        glow = svg.node(root, "rect", x=cx - 4, y=cy - 4, width=cell_w - gap + 8, height=cell_h - gap + 8, rx=5, ry=5)
        glow.set("fill", "none")
        glow.set("stroke", AMBER)
        glow.set("stroke-width", "5")
        glow.set("opacity", "0.7")
        stroke, sw = INK, "2.5"
    rect = svg.node(root, "rect", x=cx, y=cy, width=cell_w - gap, height=cell_h - gap, rx=3, ry=3)
    rect.set("fill", fill)
    rect.set("stroke", stroke)
    rect.set("stroke-width", sw)

# Peak value on a page-colored pill so it reads on any cell color
txt = f"{int(hi):,}"
size = 34
pill_w, pill_h = len(txt) * size * 0.62 + 16, size + 12
pcx, pcy = x0 + peak[1] * cell_w + cell_w / 2, y0 + peak[0] * cell_h + cell_h / 2
pill = svg.node(
    root, "rect", x=pcx - pill_w / 2, y=pcy - pill_h / 2, width=pill_w, height=pill_h, rx=pill_h / 2, ry=pill_h / 2
)
pill.set("fill", PAGE_BG)
pill.set("fill-opacity", "0.9")
svg_text(pcx, pcy + size * 0.35, txt, size, weight="bold")

# Axis ticks at bin edges, evenly stepped
for j in range(0, nc + 1, TICK_EVERY):
    svg_text(x0 + j * cell_w, y0 + gh + 62, f"{mean_lo + j * mean_step:g}", 44, fill=INK_SOFT)
for i in range(0, nr + 1, TICK_EVERY):
    svg_text(x0 - 22, y0 + gh - i * cell_h + 15, f"{amp_lo + i * amp_step:g}", 44, fill=INK_SOFT, anchor="end")

svg_text(x0 + gw / 2, y0 + gh + 150, MEAN, 46, weight="bold")
svg_text(x0 - 180, y0 + gh / 2, AMPLITUDE, 46, weight="bold", rotation=-90)

# Color bar: log scale from the lowest counted value to the peak
cb_w, cb_h = 44, int(gh * 0.8)
cb_x, cb_y = x0 + gw + 70, y0 + 50
n_seg = 120
for k in range(n_seg):
    shade = ramp_color(SEQ_FIELDS, 1 - k / (n_seg - 1))
    svg.node(root, "rect", x=cb_x, y=cb_y + k * cb_h / n_seg, width=cb_w, height=cb_h / n_seg + 1, fill=shade)
border = svg.node(root, "rect", x=cb_x, y=cb_y, width=cb_w, height=cb_h, rx=3, ry=3)
border.set("fill", "none")
border.set("stroke", INK_SOFT)
border.set("stroke-width", "1.5")

cb_ticks = [lo] + [
    10.0**p
    for p in range(math.floor(math.log10(lo)) + 1, math.floor(math.log10(hi)) + 1)
    if math.log(10.0**p / lo) / math.log(hi / lo) > 0.12
]
for tv in cb_ticks:
    ty = cb_y + cb_h * (1 - math.log(tv / lo) / math.log(hi / lo))
    svg.node(root, "line", x1=cb_x + cb_w, y1=ty, x2=cb_x + cb_w + 12, y2=ty, stroke=INK_SOFT)
    svg_text(cb_x + cb_w + 20, ty + 15, f"{int(tv):,}", 44, fill=INK_SOFT, anchor="start")
svg_text(cb_x, cb_y - 36, COUNT, 40, weight="bold", anchor="start")

# Separate key for empty bins: a page-colored swatch
sw_y = cb_y + cb_h + 60
swatch = svg.node(root, "rect", x=cb_x, y=sw_y, width=cb_w, height=cb_w, rx=3, ry=3)
swatch.set("fill", PAGE_BG)
swatch.set("stroke", INK_MUTED)
swatch.set("stroke-width", "1.5")
svg_text(cb_x + cb_w + 20, sw_y + cb_w / 2 + 15, "0 (empty)", 44, fill=INK_SOFT, anchor="start")

svg_bytes = svg.render(is_unicode=False, pretty_print=True)
html_svg = svg.render(is_unicode=True)
chart.teardown()
cairosvg.svg2png(bytestring=svg_bytes, write_to=f"plot-{THEME}.png", dpi=72)

# Interactive HTML export: pygal's native SVG inside a page
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>heatmap-rainflow · python · pygal · anyplot.ai</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center;
               align-items: center; min-height: 100vh; background: {PAGE_BG}; }}
        .chart {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <figure class="chart">{html_svg}</figure>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)
