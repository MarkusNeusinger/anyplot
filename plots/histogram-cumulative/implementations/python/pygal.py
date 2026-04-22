""" pyplots.ai
histogram-cumulative: Cumulative Histogram
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Test scores from 500 students
np.random.seed(42)
scores = np.random.normal(loc=72, scale=12, size=500)
scores = np.clip(scores, 0, 100)  # Ensure valid score range

# Compute histogram bins and cumulative counts
bin_count = 20
counts, bin_edges = np.histogram(scores, bins=bin_count)
cumulative_counts = np.cumsum(counts)
cumulative_proportions = cumulative_counts / len(scores)

# Create bin labels (bin ranges)
bin_labels = [f"{int(bin_edges[i])}-{int(bin_edges[i + 1])}" for i in range(len(bin_edges) - 1)]

# Style for large canvas (4800x2700)
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333",
    foreground_strong="#333",
    foreground_subtle="#666",
    colors=("#306998",),  # Python Blue
    title_font_size=60,
    label_font_size=42,
    major_label_font_size=38,
    legend_font_size=36,
    value_font_size=32,
)

# Create bar chart for cumulative histogram
chart = pygal.Bar(
    width=4800,
    height=2700,
    style=custom_style,
    title="histogram-cumulative · pygal · pyplots.ai",
    x_title="Test Score Range",
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
chart.add("Cumulative Proportion", cumulative_proportions.tolist())

# Save outputs
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
