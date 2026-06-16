""" anyplot.ai
polar-line: Polar Line Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-12
"""

import os

import numpy as np
import pygal
from pygal.style import Style


# Theme-adaptive colors
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette (first series is always #009E73)
IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Data - Hourly wind speed variation (cyclical data)
np.random.seed(42)
hours = [f"{h:02d}:00" for h in range(24)]

# Day 1 - Typical breezy day pattern
day_1 = [
    3.2,
    2.8,
    2.5,
    2.1,
    2.0,
    2.3,
    3.1,
    4.5,
    6.2,
    7.8,
    8.9,
    9.5,
    10.2,
    10.8,
    10.5,
    9.8,
    8.6,
    7.2,
    5.8,
    4.2,
    3.8,
    3.5,
    3.3,
    3.2,
]

# Day 2 - Calmer day pattern
day_2 = [
    2.1,
    1.9,
    1.8,
    1.7,
    1.6,
    1.8,
    2.4,
    3.2,
    4.1,
    4.8,
    5.2,
    5.6,
    5.8,
    5.9,
    5.7,
    5.2,
    4.6,
    3.8,
    3.1,
    2.5,
    2.3,
    2.2,
    2.1,
    2.0,
]

# Custom style for 4800x2700
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=18,
    major_label_font_size=16,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
    opacity=0.9,
    opacity_hover=1.0,
)

# Create Radar chart (polar line visualization)
chart = pygal.Radar(
    width=4800,
    height=2700,
    style=custom_style,
    title="polar-line · pygal · anyplot.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=24,
    dots_size=16,
    stroke_style={"width": 3},
    fill=False,
    show_dots=True,
    inner_radius=0.15,
    margin=50,
    margin_top=100,
    margin_bottom=150,
)

# Set angular labels (hours)
chart.x_labels = hours

# Add wind speed series
chart.add("Breezy Day", day_1)
chart.add("Calm Day", day_2)

# Render to files
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
