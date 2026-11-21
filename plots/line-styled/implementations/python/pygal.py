"""anyplot.ai
line-styled: Styled Line Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-12
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

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
LINE_WIDTH = 7  # one width for every style, so no series looks heavier
# Standard styles in series order: solid, dashed, dotted, dash-dot (SVG dasharray, in px)
DASH_PATTERNS = [None, "56, 28", "6, 24", "56, 22, 6, 22"]
STYLE_NAMES = ["Solid", "Dashed", "Dotted", "Dash-dot"]

# Columns: set these to your table's column names
MONTH = "Month"  # role: x
SENSORS = ["Sensor A", "Sensor B", "Sensor C", "Sensor D"]  # role: y_
TEMPERATURE = "Temperature (°C)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("sensors.csv")
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
base_temp = np.array([5, 7, 12, 16, 20, 24, 26, 25, 21, 15, 9, 6])
offsets = [0, 3, -2, 1.5]
df = pd.DataFrame(
    {MONTH: months}
    | {sensor: base_temp + off + np.random.randn(12) * 1.5 for sensor, off in zip(SENSORS, offsets, strict=True)}
)

# Plot: reads only df and the constants above
title = "line-styled · python · pygal · anyplot.ai"
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    tooltip_font_size=36,
    stroke_width=LINE_WIDTH,
)

chart = pygal.Line(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    x_title=MONTH,
    y_title=TEMPERATURE,
    show_x_guides=False,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_box_size=40,
    dots_size=11,
    show_dots=True,
    truncate_legend=-1,
    margin=60,
)
chart.x_labels = df[MONTH].tolist()

# One series per sensor, each with its own dash pattern at the same width
for i, sensor in enumerate(SENSORS):
    stroke = {"width": LINE_WIDTH}
    if DASH_PATTERNS[i % len(DASH_PATTERNS)]:
        stroke["dasharray"] = DASH_PATTERNS[i % len(DASH_PATTERNS)]
    chart.add(f"{sensor} ({STYLE_NAMES[i % len(STYLE_NAMES)]})", df[sensor].tolist(), stroke_style=stroke)

# Save as PNG and HTML
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
