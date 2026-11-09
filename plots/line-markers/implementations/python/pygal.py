""" anyplot.ai
line-markers: Line Plot with Markers
Library: pygal 3.1.3 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-09
"""

import os
import re

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions, one per site in order
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Constants: marker shape + fill treatment cycled per series (filled circle, hollow square, filled triangle, hollow diamond)
MARKER_SHAPES = ("circle", "square", "triangle", "diamond")
MARKER_FILLED = (True, False, True, False)
MARKER_RADIUS = 19
MARKER_OUTLINE = 5
LINE_WIDTH = 5
LEGEND_BOX = 44

# Columns: set these to your table's column names
MONTH = "Month"  # role: x
SITES = ["Greenhouse", "Warehouse", "Server Room"]  # role: y
Y_TITLE = "Temperature (°C)"  # shared unit of the SITES columns

# Data: replace this block with your own table, for example df = pd.read_csv("temperatures.csv")
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
x_values = np.arange(len(months))
df = pd.DataFrame(
    {
        MONTH: months,
        SITES[0]: 20 + 5 * np.sin(x_values * np.pi / 6) + np.random.randn(12) * 1.5,
        SITES[1]: 18 + 4 * np.sin(x_values * np.pi / 6 + 1) + np.random.randn(12) * 1.2,
        SITES[2]: 22 + 3 * np.sin(x_values * np.pi / 6 + 2) + np.random.randn(12) * 1.0,
    }
)

# Plot: reads only df and the constants above
table = df.set_index(MONTH)[SITES]


def shape_markers(root):
    """pygal xml filter: redraw each series' dots and legend box as that series' marker shape."""
    targets = []
    for group in root.iter("g"):
        serie = re.search(r"\bserie-(\d+)\b", group.get("class", ""))
        if serie:
            for dot in group.iter("circle"):
                targets.append((dot, int(serie.group(1)), float(dot.get("cx")), float(dot.get("cy")), MARKER_RADIUS))
        elif group.get("id", "").startswith("activate-serie-"):
            for box in group.findall("rect"):
                half = LEGEND_BOX / 2
                cx, cy = float(box.get("x")) + half, float(box.get("y")) + half
                targets.append((box, int(group.get("id").rsplit("-", 1)[1]), cx, cy, half - MARKER_OUTLINE / 2))
    for node, i, cx, cy, r in targets:
        shape = MARKER_SHAPES[i % len(MARKER_SHAPES)]
        color = IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)]
        keep = {k: node.get(k) for k in ("class",) if node.get(k)}
        node.attrib.clear()
        node.attrib.update(keep)
        if shape == "circle":
            node.tag = "circle"
            node.attrib.update(cx=f"{cx}", cy=f"{cy}", r=f"{r}")
        elif shape == "square":
            side = r * 1.75
            node.tag = "rect"
            node.attrib.update(x=f"{cx - side / 2}", y=f"{cy - side / 2}", width=f"{side}", height=f"{side}")
        else:
            k = r * 1.45
            if shape == "triangle":
                pts = [(cx, cy - k), (cx + k * 0.866, cy + k * 0.5), (cx - k * 0.866, cy + k * 0.5)]
            else:
                pts = [(cx, cy - k), (cx + k, cy), (cx, cy + k), (cx - k, cy)]
            node.tag = "polygon"
            node.set("points", " ".join(f"{px},{py}" for px, py in pts))
        fill = color if MARKER_FILLED[i % len(MARKER_FILLED)] else PAGE_BG
        outline = PAGE_BG if MARKER_FILLED[i % len(MARKER_FILLED)] else color
        node.set("style", f"fill:{fill};stroke:{outline};stroke-width:{MARKER_OUTLINE};stroke-linejoin:round")
    return root


custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=GRID,
    guide_stroke_color=GRID,
    major_guide_stroke_color=GRID,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=LINE_WIDTH,
    opacity=1.0,
    opacity_hover=1.0,
    font_family="sans-serif",
)

chart = pygal.Line(
    width=3200,
    height=1800,
    explicit_size=True,
    style=custom_style,
    title="line-markers · python · pygal · anyplot.ai",
    x_title=MONTH,
    y_title=Y_TITLE,
    show_dots=True,
    dots_size=MARKER_RADIUS,
    stroke_style={"width": LINE_WIDTH, "linecap": "round", "linejoin": "round"},
    show_x_guides=False,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=len(table.columns),
    legend_box_size=LEGEND_BOX,
    margin=60,
    spacing=40,
    truncate_legend=-1,
    value_formatter=lambda v: f"{v:.1f}",
)
chart.add_xml_filter(shape_markers)

chart.x_labels = table.index.astype(str).tolist()

for site in table.columns:
    chart.add(str(site), [None if pd.isna(v) else float(v) for v in table[site]])

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
