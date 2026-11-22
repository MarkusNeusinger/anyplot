"""anyplot.ai
area-stacked-confidence: Stacked Area Chart with Confidence Bands
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-18
"""

import os
import re

import cairosvg
import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BAND_TINT = 0.45  # share of white mixed into a series color to get its lighter band shade
BAND_OPACITY = 0.4  # semi-transparent bands keep the layers behind them visible
LAYER_OPACITY = 0.85

# Columns: set these to your table's column names
QUARTER = "Quarter"  # role: x
REVENUE = ["Product A", "Product B", "Product C"]  # role: y
LOWER = ["Product A lower", "Product B lower", "Product C lower"]  # role: y_lower
UPPER = ["Product A upper", "Product B upper", "Product C upper"]  # role: y_upper
UNIT = "Revenue ($M)"

# Data: replace this block with your own table, for example df = pd.read_csv("forecast.csv")
half_width = [
    [8.0, 9.0, 8.5, 10.0, 9.5, 11.0, 10.5, 12.0],
    [6.0, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0],
    [12.0, 15.0, 18.0, 20.0, 22.0, 24.0, 25.0, 26.0],
]
revenue = [
    [120.0, 125.0, 130.0, 140.0, 145.0, 150.0, 158.0, 165.0],
    [80.0, 85.0, 88.0, 92.0, 95.0, 100.0, 105.0, 110.0],
    [30.0, 40.0, 55.0, 70.0, 85.0, 95.0, 105.0, 115.0],
]
df = pd.DataFrame(
    {
        QUARTER: ["Q1'24", "Q2'24", "Q3'24", "Q4'24", "Q1'25", "Q2'25", "Q3'25", "Q4'25"],
        **dict(zip(REVENUE, revenue, strict=True)),
        **{c: np.array(v) - np.array(h) for c, v, h in zip(LOWER, revenue, half_width, strict=True)},
        **{c: np.array(v) + np.array(h) for c, v, h in zip(UPPER, revenue, half_width, strict=True)},
    }
)

# Plot: reads only df and the constants above
# pygal cannot draw a gap inside a filled layer, so a missing value is bridged from its neighbors
table = df.set_index(QUARTER).astype(float).interpolate(limit_direction="both")
centers = table[REVENUE]
below = table[LOWER].set_axis(REVENUE, axis=1)
above = table[UPPER].set_axis(REVENUE, axis=1)
products = list(REVENUE)

# Stacked edge of every series, and its band moved onto that edge
edge = centers.cumsum(axis=1)
band_low = edge - (centers - below)
band_high = edge + (above - centers)
top = np.nanmax(band_high.to_numpy())


def lighter(color, share):
    channels = [int(color[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(c + (255 - c) * share):02X}" for c in channels)


layer_colors = [IMPRINT_PALETTE[i] for i in range(len(products))]
band_colors = [lighter(c, BAND_TINT) for c in layer_colors]

# Series in drawing order, back to front: layers (top series first), band edges, then the central edges.
# pygal's Style hands out colors by series index, so the color list follows that order.
n = len(products)
order = list(range(n))[::-1]
series_colors = (
    [layer_colors[i] for i in order] + [band_colors[i] for i in order for _ in range(2)] + [INK for _ in order]
)

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    guide_stroke_color=INK_SOFT,
    major_guide_stroke_color=INK_SOFT,
    colors=tuple(series_colors),
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=40,
    value_font_size=36,
    stroke_width=4,
)

chart = pygal.Line(
    fill=True,
    width=3200,
    height=1800,
    style=custom_style,
    title="area-stacked-confidence · python · pygal · anyplot.ai",
    x_title=QUARTER,
    y_title=UNIT,
    show_dots=False,
    show_x_guides=False,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=n,
    range=(0, top * 1.06),
    margin=60,
    truncate_legend=-1,
)
chart.x_labels = centers.index.tolist()

for i in order:
    chart.add(products[i], edge[products[i]].tolist(), fill=True)
for i in order:
    chart.add(f"{products[i]} 90% interval", band_high[products[i]].tolist(), fill=True)
    chart.add(None, band_low[products[i]].tolist(), fill=True)
for i in order:
    chart.add(None, edge[products[i]].tolist(), fill=False)

svg = chart.render().decode()

# Each band is the region between its upper and lower edge, so the two fill-to-zero paths of a
# series become one closed polygon; layers and bands get their own opacity.
paths = list(re.finditer(r'<path d="(M[^"]*)" class="line reactive[^"]*"\s*/>', svg))
series_paths = paths[: 3 * n]
patched = svg
for k in reversed(range(n)):
    up, lo = series_paths[n + 2 * k], series_paths[n + 2 * k + 1]
    pts_up = re.findall(r"(-?[\d.]+) (-?[\d.]+)", up.group(1).replace("M", "L"))[1:-1]
    pts_lo = re.findall(r"(-?[\d.]+) (-?[\d.]+)", lo.group(1).replace("M", "L"))[1:-1]
    polygon = "M" + " L".join(f"{x} {y}" for x, y in pts_up + pts_lo[::-1]) + " Z"
    patched = patched.replace(lo.group(0), "").replace(
        up.group(0),
        up.group(0).replace(up.group(1), polygon).replace("/>", f'style="fill-opacity:{BAND_OPACITY};stroke:none" />'),
    )
for k in range(n):
    m = series_paths[k]
    patched = patched.replace(
        m.group(0), m.group(0).replace("/>", f'style="fill-opacity:{LAYER_OPACITY};stroke:none" />')
    )

with open(f"plot-{THEME}.html", "wb") as f:
    f.write(patched.encode())
cairosvg.svg2png(bytestring=patched.encode(), write_to=f"plot-{THEME}.png")
