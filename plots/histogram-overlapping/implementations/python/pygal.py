""" anyplot.ai
histogram-overlapping: Overlapping Histograms
Library: pygal 3.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-08
"""

import os
import sys

sys.path = [p for p in sys.path if not p.endswith("python")]

import numpy as np
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Data - Height distributions by gender
np.random.seed(42)
heights_male = np.random.normal(175, 7, 200)  # cm
heights_female = np.random.normal(162, 6, 200)  # cm

# Histogram parameters
bin_min = 140
bin_max = 200
n_bins = 20
bin_width = (bin_max - bin_min) / n_bins

# Create bin edges
bin_edges = np.linspace(bin_min, bin_max, n_bins + 1)

# Calculate histogram data for pygal
# Pygal Histogram expects tuples of (height, start, end)
hist_male, _ = np.histogram(heights_male, bins=bin_edges)
hist_female, _ = np.histogram(heights_female, bins=bin_edges)

male_data = [(int(count), float(bin_edges[i]), float(bin_edges[i + 1])) for i, count in enumerate(hist_male)]
female_data = [(int(count), float(bin_edges[i]), float(bin_edges[i + 1])) for i, count in enumerate(hist_female)]

# Style for 4800x2700
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    opacity="0.5",
    opacity_hover="0.7",
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=2,
)

# Create histogram chart
chart = pygal.Histogram(
    width=4800,
    height=2700,
    style=custom_style,
    title="histogram-overlapping · pygal · anyplot.ai",
    x_title="Height (cm)",
    y_title="Frequency",
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=36,
    show_y_guides=True,
    show_x_guides=False,
    x_label_rotation=0,
    margin_bottom=200,
    margin_left=180,
    margin_right=100,
    margin_top=150,
    spacing=0,
)

# Add data series
chart.add("Male", male_data)
chart.add("Female", female_data)

# Save outputs
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
