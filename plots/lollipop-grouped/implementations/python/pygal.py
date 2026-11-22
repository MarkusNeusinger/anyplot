"""anyplot.ai
lollipop-grouped: Grouped Lollipop Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-17
"""

import os

import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
REGION = "Region"  # role: category
PRODUCT_LINE = "Product line"  # role: series
REVENUE = "Revenue ($ millions)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("revenue.csv")
df = pd.DataFrame(
    {
        REGION: ["North", "South", "East", "West"] * 3,
        PRODUCT_LINE: ["Electronics"] * 4 + ["Furniture"] * 4 + ["Apparel"] * 4,
        REVENUE: [42, 35, 48, 31, 28, 32, 25, 38, 15, 22, 18, 26],
    }
)

# Plot: reads only df and the constants above
table = df.pivot_table(index=REGION, columns=PRODUCT_LINE, values=REVENUE, sort=False)
n_cat = len(table.index)
n_series = len(table.columns)
top = float(table.max().max())

# Group of lollipops per category: side by side, narrower than the gap between groups
spacing = 0.6 / max(n_series, 1)
offsets = [(i - (n_series - 1) / 2) * spacing for i in range(n_series)]

# One pygal series per lollipop (prevents connecting lines), so the color list repeats per category
series_colors = [IMPRINT_PALETTE[i] for i in range(n_series) for _ in range(n_cat)]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(series_colors),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    opacity="1",
    opacity_hover="1",
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="lollipop-grouped · python · pygal · anyplot.ai",
    x_title=REGION,
    y_title=REVENUE,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=n_series,
    show_y_guides=True,
    show_x_guides=False,
    dots_size=26,
    stroke_style={"width": 6},
    range=(0, top * 1.15),
    xrange=(0.4, n_cat + 0.6),
    show_minor_x_labels=False,
    truncate_legend=-1,
    # pygal's .reactive rule sets stroke-width:1 and stroke-opacity:.8 on every line, which would
    # override the series stroke width, so the stems get their own rule
    css=[
        "file://style.css",
        "file://graph.css",
        "inline:.series .line.reactive{stroke-width:6px !important;stroke-opacity:1 !important}",
    ],
)

for series_idx, line in enumerate(table.columns):
    for cat_idx, val in enumerate(table[line].tolist()):
        x_pos = cat_idx + 1 + offsets[series_idx]
        # One series per lollipop keeps the stems apart: the base point has no dot, the marker sits at the value
        lollipop = [{"value": (x_pos, 0), "node": {"r": 0}}, {"value": (x_pos, val), "node": {"r": 26}}]
        # Only the first lollipop of each series shows in the legend
        chart.add(str(line) if cat_idx == 0 else None, lollipop)

# Category labels at the group centers
label_map = {i + 1: str(name) for i, name in enumerate(table.index)}
chart.x_labels = list(label_map)
chart.x_labels_major = list(label_map)
chart.x_value_formatter = lambda x: label_map.get(round(x), "") if x == round(x) else ""

# Save as PNG and HTML with theme suffix
chart.render_to_png(f"plot-{THEME}.png")
chart.render_to_file(f"plot-{THEME}.html")
