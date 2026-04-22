""" pyplots.ai
histogram-density: Density Histogram
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-29
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Test scores with a realistic bimodal distribution
np.random.seed(42)
# Create bimodal distribution (two groups of students)
scores_group1 = np.random.normal(loc=65, scale=10, size=150)
scores_group2 = np.random.normal(loc=82, scale=8, size=100)
scores = np.concatenate([scores_group1, scores_group2])
scores = np.clip(scores, 0, 100)  # Clip to valid score range

# Calculate histogram bins and density values
n_bins = 25
counts, bin_edges = np.histogram(scores, bins=n_bins, density=True)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

# Custom style for pyplots
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998",),  # Python Blue
    title_font_size=48,
    label_font_size=36,
    major_label_font_size=32,
    legend_font_size=32,
    value_font_size=28,
    stroke_width=0,
    opacity=0.85,
)

# Create histogram chart
chart = pygal.Bar(
    width=4800,
    height=2700,
    style=custom_style,
    title="histogram-density · pygal · pyplots.ai",
    x_title="Test Score",
    y_title="Density (Probability per Unit)",
    show_legend=False,
    show_x_guides=False,
    show_y_guides=True,
    x_label_rotation=0,
    margin=60,
    spacing=1,
    print_values=False,
)

# Create bar labels from bin centers (show every 5th label for clarity)
chart.x_labels = [f"{int(bc)}" if i % 5 == 0 else "" for i, bc in enumerate(bin_centers)]

# Add density histogram data
chart.add("Density", [{"value": float(c), "label": f"Score: {int(bin_centers[i])}"} for i, c in enumerate(counts)])

# Save outputs
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
