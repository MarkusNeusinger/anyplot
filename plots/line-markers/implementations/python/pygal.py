"""anyplot.ai
line-markers: Line Plot with Markers
Library: pygal 3.1.3 | Python 3.14
Quality: pending | Updated: 2026-11-09
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per sensor in order
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Constants: marker treatments cycled per series (filled, hollow ring, segmented ring)
MARKER_STYLES = (
    {"fill": None, "stroke": PAGE_BG, "stroke-width": 4, "stroke-dasharray": "none"},
    {"fill": PAGE_BG, "stroke": None, "stroke-width": 7, "stroke-dasharray": "none"},
    {"fill": PAGE_BG, "stroke": None, "stroke-width": 10, "stroke-dasharray": "8 10"},
)
MARKER_RADIUS = 15
LINE_WIDTH = 5

# Columns: set these to your table's column names
MONTH = "Month"  # role: x
SENSORS = ["Sensor A", "Sensor B", "Sensor C"]  # role: y
Y_TITLE = "Temperature (°C)"  # shared unit of the SENSORS columns

# Data: replace this block with your own table, for example df = pd.read_csv("sensors.csv")
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
x_values = np.arange(len(months))
df = pd.DataFrame(
    {
        MONTH: months,
        SENSORS[0]: 20 + 5 * np.sin(x_values * np.pi / 6) + np.random.randn(12) * 1.5,
        SENSORS[1]: 18 + 4 * np.sin(x_values * np.pi / 6 + 1) + np.random.randn(12) * 1.2,
        SENSORS[2]: 22 + 3 * np.sin(x_values * np.pi / 6 + 2) + np.random.randn(12) * 1.0,
    }
)

# Plot: reads only df and the constants above
table = df.set_index(MONTH)[SENSORS]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
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
    legend_box_size=36,
    margin=60,
    spacing=40,
    truncate_legend=-1,
    value_formatter=lambda v: f"{v:.1f}",
)

chart.x_labels = table.index.astype(str).tolist()

for i, sensor in enumerate(table.columns):
    color = IMPRINT_PALETTE[i]
    marker = MARKER_STYLES[i % len(MARKER_STYLES)]
    style = (
        f"fill:{marker['fill'] or color};stroke:{marker['stroke'] or color};"
        f"stroke-width:{marker['stroke-width']};stroke-dasharray:{marker['stroke-dasharray']}"
    )
    values = [
        None if pd.isna(v) else {"value": float(v), "node": {"style": style, "r": MARKER_RADIUS}} for v in table[sensor]
    ]
    chart.add(str(sensor), values)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
