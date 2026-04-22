""" pyplots.ai
hexbin-basic: Basic Hexbin Plot
Library: pygal 3.1.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-02-21
"""

import math
import re

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


# Data - air quality sensor network with three pollution hotspots
np.random.seed(42)

# Dense downtown core - tight, high concentration
core_x = np.random.randn(2500) * 0.6 + 1.5
core_y = np.random.randn(2500) * 0.6 + 3.0

# Industrial zone - medium density, broader spread
industrial_x = np.random.randn(1200) * 1.1 - 2.5
industrial_y = np.random.randn(1200) * 0.9 - 1.0

# Highway corridor - elongated, moderate density
highway_x = np.random.randn(600) * 0.4 + 5.0
highway_y = np.random.randn(600) * 1.8 + 1.0

# Sparse suburban background (fewer points, tighter bounds)
bg_x = np.random.uniform(-4.0, 6.5, 150)
bg_y = np.random.uniform(-3.0, 5.5, 150)

sensor_x = np.concatenate([core_x, industrial_x, highway_x, bg_x])
sensor_y = np.concatenate([core_y, industrial_y, highway_y, bg_y])

# Hexagonal binning: assign each point to a hex cell, then count per cell
gridsize = 20
pad = 0.2
x_min, x_max = sensor_x.min() - pad, sensor_x.max() + pad
y_min, y_max = sensor_y.min() - pad, sensor_y.max() + pad

hex_width = (x_max - x_min) / gridsize
hex_height = hex_width * 2 / np.sqrt(3)

rows = ((sensor_y - y_min) / hex_height).astype(int)
odd_row_shift = np.where(rows % 2 == 1, 0.5, 0.0)
cols = ((sensor_x - x_min) / hex_width - odd_row_shift).astype(int)

cell_ids = cols * 10000 + rows
unique_cells, counts = np.unique(cell_ids, return_counts=True)

cell_cols = unique_cells // 10000
cell_rows = unique_cells % 10000
cx = x_min + (cell_cols + np.where(cell_rows % 2 == 1, 0.5, 0.0)) * hex_width + hex_width / 2
cy = y_min + cell_rows * hex_height + hex_height / 2

# Refined viridis-derived palette (dark→light = sparse→dense)
viridis_6 = ("#440154", "#414487", "#2a788e", "#22a884", "#7ad151", "#fde725")

custom_style = Style(
    background="#ffffff",
    plot_background="#f7f7f2",
    foreground="#3a3a3a",
    foreground_strong="#1a1a1a",
    foreground_subtle="#e0e0d8",
    colors=viridis_6,
    opacity=0.92,
    opacity_hover=1.0,
    title_font_size=54,
    label_font_size=40,
    major_label_font_size=34,
    legend_font_size=30,
    value_font_size=24,
    tooltip_font_size=24,
    title_font_family="sans-serif",
    label_font_family="sans-serif",
    major_label_font_family="sans-serif",
    legend_font_family="sans-serif",
    value_font_family="sans-serif",
)

# Tight axis range: 2nd/98th percentile with minimal padding
data_x_min = float(np.percentile(sensor_x, 2)) - 0.4
data_x_max = float(np.percentile(sensor_x, 98)) + 0.4
data_y_min = float(np.percentile(sensor_y, 2)) - 0.4
data_y_max = float(np.percentile(sensor_y, 98)) + 0.4

chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="hexbin-basic \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Sensor Grid X (km)",
    y_title="Sensor Grid Y (km)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=6,
    legend_box_size=24,
    stroke=False,
    dots_size=8,
    show_x_guides=False,
    show_y_guides=False,
    xrange=(data_x_min, data_x_max),
    range=(data_y_min, data_y_max),
    truncate_legend=-1,
    tooltip_border_radius=8,
    print_values=False,
    human_readable=True,
    x_labels_major_count=6,
    y_labels_major_count=6,
    show_minor_x_labels=False,
    show_minor_y_labels=False,
    value_formatter=lambda v: f"{v:.1f} km",
)

# Classify hex cells into 6 density levels using log-spaced thresholds
n_levels = 6
c_min, c_max = float(counts.min()), float(counts.max())
edges = np.logspace(np.log10(c_min), np.log10(c_max + 1), n_levels + 1)
edges[0] = c_min
edges[-1] = c_max + 1

level_names = ["Sparse", "Low", "Medium", "Moderate", "Dense", "Hotspot"]
labels = [f"{level_names[i]} ({int(edges[i])}\u2013{int(edges[i + 1])})" for i in range(n_levels)]

series_data = [[] for _ in range(n_levels)]
for x, y, cnt in zip(cx, cy, counts, strict=True):
    level = min(int(np.searchsorted(edges[1:], cnt)), n_levels - 1)
    series_data[level].append({"value": (round(float(x), 2), round(float(y), 2)), "label": f"{int(cnt)} readings"})

# Dot sizes: wider range for stronger visual hierarchy
dot_sizes = [8, 14, 22, 34, 48, 62]
for i in range(n_levels):
    if series_data[i]:
        chart.add(labels[i], series_data[i], dots_size=dot_sizes[i])

# Render SVG, transform circle dots → hexagonal polygon markers, save PNG
svg_raw = chart.render()
svg_text = svg_raw.decode("utf-8") if isinstance(svg_raw, bytes) else svg_raw


def _circle_to_hex(match):
    tag = match.group(0)
    cx_m = re.search(r'cx="([\d.e+-]+)"', tag)
    cy_m = re.search(r'cy="([\d.e+-]+)"', tag)
    r_m = re.search(r'\br="([\d.e+-]+)"', tag)
    if not (cx_m and cy_m and r_m):
        return tag
    r_v = float(r_m.group(1))
    if r_v < 1.0:
        return tag
    xc, yc = float(cx_m.group(1)), float(cy_m.group(1))
    pts = " ".join(
        f"{xc + r_v * math.cos(math.radians(a)):.2f},{yc + r_v * math.sin(math.radians(a)):.2f}"
        for a in range(0, 360, 60)
    )
    result = re.sub(r'\bcx="[\d.e+-]+"', "", tag)
    result = re.sub(r'\bcy="[\d.e+-]+"', "", result)
    result = re.sub(r'\br="[\d.e+-]+"', f'points="{pts}"', result, count=1)
    return result.replace("<circle", "<polygon")


svg_hex = re.sub(r"<circle[^>]*/>", _circle_to_hex, svg_text)

with open("plot.svg", "w", encoding="utf-8") as f:
    f.write(svg_hex)

cairosvg.svg2png(bytestring=svg_hex.encode("utf-8"), write_to="plot.png")
