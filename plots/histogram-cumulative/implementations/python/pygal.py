""" anyplot.ai
histogram-cumulative: Cumulative Histogram
Library: pygal 3.1.0 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-11
"""

import os

import numpy as np
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"

# Data - Customer satisfaction ratings on 1-5 scale from 1000 customers
np.random.seed(42)
ratings = np.random.normal(loc=3.7, scale=0.8, size=1000)
ratings = np.clip(ratings, 1, 5)

# Compute histogram bins and cumulative counts
bin_count = 20
counts, bin_edges = np.histogram(ratings, bins=bin_count)
cumulative_counts = np.cumsum(counts)
cumulative_proportions = cumulative_counts / len(ratings)

# Create bin labels
bin_labels = [f"{bin_edges[i]:.1f}-{bin_edges[i + 1]:.1f}" for i in range(len(bin_edges) - 1)]

# Style for large canvas (4800x2700)
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(BRAND,),
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
)

# Create bar chart for cumulative histogram
chart = pygal.Bar(
    width=4800,
    height=2700,
    style=custom_style,
    title="histogram-cumulative · pygal · anyplot.ai",
    x_title="Customer Satisfaction Rating",
    y_title="Cumulative Proportion",
    show_legend=False,
    show_y_guides=True,
    show_x_guides=False,
    x_label_rotation=45,
    range=(0, 1.05),
)

# Set x-axis labels
chart.x_labels = bin_labels

# Add cumulative proportion data
chart.add("Cumulative", cumulative_proportions.tolist())

# Save outputs
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
