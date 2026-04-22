""" pyplots.ai
histogram-density: Density Histogram
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-29
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


# Data - Test scores with normal-like distribution
np.random.seed(42)
mu, sigma = 75, 12
scores = np.random.normal(loc=mu, scale=sigma, size=500)

# Calculate histogram with density normalization
bin_edges = np.linspace(scores.min() - 5, scores.max() + 5, 31)
hist_counts, edges = np.histogram(scores, bins=bin_edges, density=True)
left_edges = edges[:-1]
right_edges = edges[1:]

# Theoretical normal PDF for overlay (calculated manually)
x_pdf = np.linspace(scores.min() - 10, scores.max() + 10, 200)
pdf_values = (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_pdf - mu) / sigma) ** 2)

# Sources
hist_source = ColumnDataSource(
    data={"left": left_edges, "right": right_edges, "top": hist_counts, "bottom": [0] * len(hist_counts)}
)

pdf_source = ColumnDataSource(data={"x": x_pdf, "y": pdf_values})

# Create figure (4800 x 2700 px)
p = figure(
    width=4800,
    height=2700,
    title="histogram-density · bokeh · pyplots.ai",
    x_axis_label="Test Score",
    y_axis_label="Density (Probability per Unit)",
)

# Plot histogram bars
p.quad(
    left="left",
    right="right",
    top="top",
    bottom="bottom",
    source=hist_source,
    fill_color="#306998",
    fill_alpha=0.7,
    line_color="white",
    line_width=2,
    legend_label="Empirical Distribution",
)

# Plot theoretical PDF overlay
p.line(x="x", y="y", source=pdf_source, line_color="#FFD43B", line_width=5, legend_label="Normal PDF (μ=75, σ=12)")

# Styling for 4800x2700 px
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Legend styling
p.legend.label_text_font_size = "16pt"
p.legend.location = "top_left"
p.legend.background_fill_alpha = 0.8

# Y-axis starts at zero
p.y_range.start = 0

# Save outputs
export_png(p, filename="plot.png")
save(p, filename="plot.html")
