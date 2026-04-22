""" pyplots.ai
histogram-overlapping: Overlapping Histograms
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import numpy as np
from bokeh.io import export_png
from bokeh.plotting import figure, output_file, save


# Data - Employee response times (ms) by department
np.random.seed(42)
engineering = np.random.normal(250, 50, 150)  # Faster responses
sales = np.random.normal(320, 70, 150)  # Moderate, more varied
support = np.random.normal(280, 40, 150)  # Consistent responses

# Compute histogram bins (aligned across all groups)
all_data = np.concatenate([engineering, sales, support])
bins = np.linspace(all_data.min() - 10, all_data.max() + 10, 30)

# Compute histogram values
eng_hist, eng_edges = np.histogram(engineering, bins=bins)
sales_hist, _ = np.histogram(sales, bins=bins)
support_hist, _ = np.histogram(support, bins=bins)

# Create figure (4800 x 2700 px)
p = figure(
    width=4800,
    height=2700,
    title="histogram-overlapping · bokeh · pyplots.ai",
    x_axis_label="Response Time (ms)",
    y_axis_label="Frequency",
    tools="pan,wheel_zoom,box_zoom,reset,hover",
    toolbar_location="above",
)

# Plot overlapping histograms using quad (true overlapping, not stacking)
eng_render = p.quad(
    top=eng_hist,
    bottom=0,
    left=eng_edges[:-1],
    right=eng_edges[1:],
    fill_color="#306998",
    fill_alpha=0.5,
    line_color="#306998",
    line_width=2,
    line_alpha=0.8,
    legend_label="Engineering",
)

sales_render = p.quad(
    top=sales_hist,
    bottom=0,
    left=eng_edges[:-1],
    right=eng_edges[1:],
    fill_color="#FFD43B",
    fill_alpha=0.5,
    line_color="#B8860B",
    line_width=2,
    line_alpha=0.8,
    legend_label="Sales",
)

support_render = p.quad(
    top=support_hist,
    bottom=0,
    left=eng_edges[:-1],
    right=eng_edges[1:],
    fill_color="#4CAF50",
    fill_alpha=0.5,
    line_color="#2E7D32",
    line_width=2,
    line_alpha=0.8,
    legend_label="Support",
)

# Configure text sizes for large canvas
p.title.text_font_size = "42pt"
p.xaxis.axis_label_text_font_size = "32pt"
p.yaxis.axis_label_text_font_size = "32pt"
p.xaxis.major_label_text_font_size = "24pt"
p.yaxis.major_label_text_font_size = "24pt"

# Configure grid
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Configure legend
p.legend.location = "top_right"
p.legend.label_text_font_size = "26pt"
p.legend.spacing = 15
p.legend.padding = 20
p.legend.background_fill_alpha = 0.85
p.legend.border_line_width = 2
p.legend.glyph_height = 30
p.legend.glyph_width = 30

# Configure axes
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.outline_line_width = 2

# Save outputs
export_png(p, filename="plot.png")
output_file("plot.html", title="Overlapping Histograms")
save(p)
