""" anyplot.ai
line-styled: Styled Line Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-12
"""

import os

import numpy as np
import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Data - Temperature measurements from 4 different sensors over 12 months
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
base_temp = np.array([5, 7, 12, 16, 20, 24, 26, 25, 21, 15, 9, 6])

sensor_a = base_temp + np.random.randn(12) * 1.5
sensor_b = base_temp + 3 + np.random.randn(12) * 1.5
sensor_c = base_temp - 2 + np.random.randn(12) * 1.5
sensor_d = base_temp + 1.5 + np.random.randn(12) * 1.5

# Custom style for large canvas (4800x2700)
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    tooltip_font_size=14,
    stroke_width=3,
)

# Create line chart with different stroke styles
chart = pygal.Line(
    width=4800,
    height=2700,
    style=custom_style,
    title="line-styled · pygal · anyplot.ai",
    x_title="Month",
    y_title="Temperature (°C)",
    show_x_guides=False,
    show_y_guides=True,
    legend_at_bottom=False,
    legend_box_size=20,
    dots_size=6,
    stroke_style={"width": 3},
    show_dots=True,
    truncate_legend=-1,
    margin=50,
    margin_top=120,
    margin_bottom=100,
)

# Set x-axis labels
chart.x_labels = months

# Add series with different stroke dash arrays for line styles
chart.add("Sensor A (Solid)", sensor_a.tolist(), stroke_style={"width": 3, "dasharray": "0"})
chart.add("Sensor B (Dashed)", sensor_b.tolist(), stroke_style={"width": 3, "dasharray": "30, 15"})
chart.add("Sensor C (Dotted)", sensor_c.tolist(), stroke_style={"width": 3, "dasharray": "8, 12"})
chart.add("Sensor D (Dash-Dot)", sensor_d.tolist(), stroke_style={"width": 3, "dasharray": "30, 10, 8, 10"})

# Save as PNG and HTML
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
