""" pyplots.ai
histogram-stacked: Stacked Histogram
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
from bokeh.io import export_png
from bokeh.plotting import figure


# Data - Simulating test scores from three different study groups
np.random.seed(42)

# Group A: Regular study group (higher scores, tighter distribution)
group_a = np.random.normal(loc=75, scale=8, size=150)

# Group B: Intensive study group (highest scores)
group_b = np.random.normal(loc=82, scale=10, size=120)

# Group C: Self-study group (lower scores, wider distribution)
group_c = np.random.normal(loc=65, scale=12, size=100)

# Create consistent bin edges for all groups
all_data = np.concatenate([group_a, group_b, group_c])
bin_edges = np.linspace(all_data.min() - 1, all_data.max() + 1, 16)

# Compute histograms with same bins
hist_a, _ = np.histogram(group_a, bins=bin_edges)
hist_b, _ = np.histogram(group_b, bins=bin_edges)
hist_c, _ = np.histogram(group_c, bins=bin_edges)

# Calculate bar positions and widths
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
bin_width = bin_edges[1] - bin_edges[0]

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="histogram-stacked · bokeh · pyplots.ai",
    x_axis_label="Test Score (points)",
    y_axis_label="Frequency (count)",
)

# Plot stacked bars - bottom to top: C, A, B
# Group C at the bottom (Self-study - lower scores)
p.vbar(
    x=bin_centers,
    top=hist_c,
    bottom=0,
    width=bin_width * 0.85,
    fill_color="#306998",
    line_color="white",
    line_width=2,
    alpha=0.9,
    legend_label="Self-study Group",
)

# Group A stacked on top of C (Regular study - middle scores)
p.vbar(
    x=bin_centers,
    top=hist_c + hist_a,
    bottom=hist_c,
    width=bin_width * 0.85,
    fill_color="#FFD43B",
    line_color="white",
    line_width=2,
    alpha=0.9,
    legend_label="Regular Study Group",
)

# Group B stacked on top of A (Intensive study - higher scores)
p.vbar(
    x=bin_centers,
    top=hist_c + hist_a + hist_b,
    bottom=hist_c + hist_a,
    width=bin_width * 0.85,
    fill_color="#4B8BBE",
    line_color="white",
    line_width=2,
    alpha=0.9,
    legend_label="Intensive Study Group",
)

# Styling for large canvas (4800x2700)
p.title.text_font_size = "36pt"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Legend styling - inside plot area
p.legend.location = "top_right"
p.legend.label_text_font_size = "22pt"
p.legend.glyph_width = 50
p.legend.glyph_height = 50
p.legend.spacing = 15
p.legend.padding = 25
p.legend.background_fill_alpha = 0.85
p.legend.border_line_width = 2
p.legend.border_line_color = "#cccccc"

# Axis range padding
p.y_range.start = 0

# Save
export_png(p, filename="plot.png")
