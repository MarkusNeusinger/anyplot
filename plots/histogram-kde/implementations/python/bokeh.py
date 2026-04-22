""" pyplots.ai
histogram-kde: Histogram with KDE Overlay
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


# Data - Simulating stock returns distribution (realistic financial data)
np.random.seed(42)
# Mix of normal market conditions and some fat-tail events
main_returns = np.random.normal(0.05, 2.5, 800)  # Daily returns in %
tail_events = np.concatenate(
    [
        np.random.normal(-8, 1.5, 50),  # Negative tail events
        np.random.normal(10, 2, 50),  # Positive tail events
    ]
)
values = np.concatenate([main_returns, tail_events])

# Histogram computation (density-normalized)
bin_count = 40
hist, bin_edges = np.histogram(values, bins=bin_count, density=True)

# KDE computation using Gaussian kernel (Scott's rule bandwidth)
x_kde = np.linspace(values.min() - 2, values.max() + 2, 500)
bandwidth = 1.06 * np.std(values) * len(values) ** (-1 / 5)
y_kde = np.zeros_like(x_kde)
for xi in values:
    y_kde += np.exp(-0.5 * ((x_kde - xi) / bandwidth) ** 2)
y_kde /= len(values) * bandwidth * np.sqrt(2 * np.pi)

# Create figure (4800 x 2700 px)
p = figure(
    width=4800,
    height=2700,
    title="histogram-kde · bokeh · pyplots.ai",
    x_axis_label="Daily Return (%)",
    y_axis_label="Density",
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

# Create histogram using quad glyphs
hist_source = ColumnDataSource(
    data={"left": bin_edges[:-1], "right": bin_edges[1:], "top": hist, "bottom": [0] * len(hist)}
)

p.quad(
    left="left",
    right="right",
    top="top",
    bottom="bottom",
    source=hist_source,
    fill_color="#306998",
    fill_alpha=0.5,
    line_color="#306998",
    line_alpha=0.8,
    line_width=2,
    legend_label="Histogram",
)

# Add KDE curve
kde_source = ColumnDataSource(data={"x": x_kde, "y": y_kde})
p.line(x="x", y="y", source=kde_source, line_color="#FFD43B", line_width=5, legend_label="KDE")

# Styling for large canvas
p.title.text_font_size = "32pt"
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Legend styling
p.legend.label_text_font_size = "20pt"
p.legend.location = "top_right"
p.legend.background_fill_alpha = 0.8
p.legend.border_line_alpha = 0.5

# Axis styling
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "#ffffff"

# Save as PNG
export_png(p, filename="plot.png")

# Also save as HTML for interactive version
output_file("plot.html")
save(p)
