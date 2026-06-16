""" anyplot.ai
density-rug: Density Plot with Rug Marks
Library: pygal 3.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-18
"""

import os

import numpy as np
import pygal
from pygal.style import Style
from scipy.stats import gaussian_kde


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette (first series = brand green)
IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Data - bimodal distribution to show interesting density shape
np.random.seed(42)
values = np.concatenate(
    [
        np.random.normal(loc=35, scale=8, size=60),  # First mode
        np.random.normal(loc=65, scale=10, size=90),  # Second mode
    ]
)

# Calculate KDE
kde = gaussian_kde(values)
x_range = np.linspace(values.min() - 10, values.max() + 10, 200)
density = kde(x_range)

# Scale density for visibility
density_scaled = density / density.max()

# Custom style (scaled for 4800x2700 canvas)
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
    stroke_width=3,
)

# Create XY chart for continuous data
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="density-rug · Python · pygal · anyplot.ai",
    x_title="Measurement Value",
    y_title="Density (normalized)",
    show_legend=True,
    legend_at_bottom=True,
    stroke=True,
    fill=True,
    show_dots=False,
    show_x_guides=True,
    show_y_guides=True,
    range=(0, 1.15),
    include_x_axis=True,
    truncate_legend=-1,
)

# Add KDE curve as line with fill
kde_points = [(float(x), float(y)) for x, y in zip(x_range, density_scaled, strict=True)]
chart.add("KDE Density Curve", kde_points, stroke_style={"width": 5})

# Add rug marks as dots along the x-axis at y=0
sorted_values = np.sort(values)
rug_points = [(float(v), 0.0) for v in sorted_values]
chart.add("Rug Marks", rug_points, stroke=False, show_dots=True, fill=False, dots_size=10)

# Save as PNG and HTML with theme-suffixed names
chart.render_to_png(f"plot-{THEME}.png")
chart.render_to_file(f"plot-{THEME}.html")
