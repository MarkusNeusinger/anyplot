""" pyplots.ai
histogram-overlapping: Overlapping Histograms
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import numpy as np
import pygal
from pygal.style import Style


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
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    opacity=".5",
    opacity_hover=".7",
    colors=("#306998", "#FFD43B"),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=48,
    value_font_size=36,
    stroke_width=2,
)

# Create histogram chart
chart = pygal.Histogram(
    width=4800,
    height=2700,
    style=custom_style,
    title="histogram-overlapping · pygal · pyplots.ai",
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
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
