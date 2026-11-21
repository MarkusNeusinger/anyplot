"""anyplot.ai
facet-grid: Faceted Grid Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-13
"""

import os

import cairosvg
import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, first series is brand green
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Columns: set these to your table's column names
DAYS = "Days"  # role: x
HEIGHT = "Height (cm)"  # role: y
SOIL = "Soil"  # role: row_facet
LIGHT = "Light"  # role: col_facet

# Data: replace this block with your own table, for example df = pd.read_csv("growth.csv")
np.random.seed(42)
soils = ["Sandy Soil", "Clay Soil"]
light_levels = ["Low Light", "Medium Light", "High Light"]
growth_rates = {
    ("Sandy Soil", "Low Light"): 0.4,
    ("Sandy Soil", "Medium Light"): 0.8,
    ("Sandy Soil", "High Light"): 1.0,
    ("Clay Soil", "Low Light"): 0.5,
    ("Clay Soil", "Medium Light"): 1.2,
    ("Clay Soil", "High Light"): 0.9,
}
sample_days = [0, 5, 10, 15, 20, 25, 30]
records = []
for soil in soils:
    for light in light_levels:
        for d in sample_days:
            h = d * growth_rates[(soil, light)] + np.random.normal(0, 1)
            records.append({SOIL: soil, LIGHT: light, DAYS: d, HEIGHT: max(0, h)})
df = pd.DataFrame(records)

# Plot: reads only df and the constants above
row_cats = df[SOIL].drop_duplicates().tolist()
col_cats = df[LIGHT].drop_duplicates().tolist()
day_values = df[DAYS].drop_duplicates().tolist()
y_top = float(df[HEIGHT].max()) * 1.15  # one shared y scale for every panel

TITLE = "facet-grid · python · pygal · anyplot.ai"
CANVAS_W, CANVAS_H = 3200, 1800
title_height = 140
row_label_width = 180
cell_width = (CANVAS_W - row_label_width) // len(col_cats)
cell_height = (CANVAS_H - title_height) // len(row_cats)

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    font_family="sans-serif",
    title_font_size=44,
    label_font_size=32,
    major_label_font_size=28,
    legend_font_size=28,
    value_font_size=24,
    stroke_width=3,
)

# One pygal chart per facet: pygal has no facet support, so the panels are composed afterwards
charts = []
for row_idx, soil in enumerate(row_cats):
    row_charts = []
    for col_idx, light in enumerate(col_cats):
        panel = df[(df[SOIL] == soil) & (df[LIGHT] == light)].set_index(DAYS)[HEIGHT].reindex(day_values)
        chart = pygal.Line(
            width=cell_width,
            height=cell_height,
            style=custom_style,
            show_legend=False,
            show_y_guides=True,
            show_x_guides=False,
            x_title=DAYS if row_idx == len(row_cats) - 1 else "",
            y_title=HEIGHT if col_idx == 0 else "",
            title=light if row_idx == 0 else "",
            show_dots=True,
            dots_size=8,
            stroke_style={"width": 4},
            range=(0, y_top),
            truncate_label=-1,
        )
        chart.x_labels = [str(d) for d in day_values]
        chart.add(soil, [None if pd.isna(v) else float(v) for v in panel])
        row_charts.append(chart)
    charts.append(row_charts)

# Compose the panels, facet labels and title into one SVG, then rasterize it
parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}">',
    f'<rect width="{CANVAS_W}" height="{CANVAS_H}" fill="{PAGE_BG}"/>',
    f'<text x="{CANVAS_W // 2}" y="95" text-anchor="middle" font-family="sans-serif" font-weight="bold" '
    f'font-size="64" fill="{INK}">{TITLE}</text>',
]
for row_idx, row_charts in enumerate(charts):
    row_y = title_height + row_idx * cell_height
    label_x, label_y = 90, row_y + cell_height // 2
    parts.append(
        f'<text transform="translate({label_x},{label_y}) rotate(-90)" text-anchor="middle" '
        f'font-family="sans-serif" font-size="46" fill="{INK}">{row_cats[row_idx]}</text>'
    )
    for col_idx, chart in enumerate(row_charts):
        svg = chart.render().decode("utf-8")
        svg = svg[svg.index("<svg") :].replace("<svg ", f'<svg width="{cell_width}" height="{cell_height}" ', 1)
        parts.append(f'<g transform="translate({row_label_width + col_idx * cell_width},{row_y})">{svg}</g>')
parts.append("</svg>")
cairosvg.svg2png(bytestring="".join(parts).encode("utf-8"), write_to=f"plot-{THEME}.png")

# Interactive HTML: the composed figure as live SVG
page = f'<!DOCTYPE html><html><head><title>{TITLE}</title></head><body style="margin:0;background:{PAGE_BG}">'
with open(f"plot-{THEME}.html", "w") as f:
    f.write(page + "".join(parts) + "</body></html>")
