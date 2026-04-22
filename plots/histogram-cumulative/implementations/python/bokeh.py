""" pyplots.ai
histogram-cumulative: Cumulative Histogram
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


# Data - simulating response times (milliseconds) for a web service
np.random.seed(42)
response_times = np.concatenate(
    [
        np.random.exponential(scale=150, size=400),  # Most requests are fast
        np.random.normal(loc=500, scale=100, size=100),  # Some slower requests
    ]
)
response_times = np.clip(response_times, 10, 1000)  # Realistic bounds

# Calculate cumulative histogram
n_bins = 30
hist_counts, bin_edges = np.histogram(response_times, bins=n_bins)
cumulative_counts = np.cumsum(hist_counts)

# Prepare step data for cumulative histogram
# For step visualization, we need x points at each bin edge
step_x = []
step_y = []
step_x.append(bin_edges[0])
step_y.append(0)
for i in range(len(cumulative_counts)):
    step_x.append(bin_edges[i])
    step_y.append(cumulative_counts[i])
    step_x.append(bin_edges[i + 1])
    step_y.append(cumulative_counts[i])

source = ColumnDataSource(data={"x": step_x, "y": step_y})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="histogram-cumulative · bokeh · pyplots.ai",
    x_axis_label="Response Time (ms)",
    y_axis_label="Cumulative Count",
)

# Plot cumulative histogram as step function
p.line(x="x", y="y", source=source, line_width=5, color="#306998", alpha=0.9)

# Add filled area under the curve
fill_x = step_x + [step_x[-1], step_x[0]]
fill_y = step_y + [0, 0]
fill_source = ColumnDataSource(data={"x": fill_x, "y": fill_y})
p.patch(x="x", y="y", source=fill_source, fill_color="#306998", fill_alpha=0.25, line_width=0)

# Add markers at bin edges for clarity
marker_source = ColumnDataSource(data={"x": bin_edges[1:], "y": cumulative_counts})
p.scatter(x="x", y="y", source=marker_source, size=18, color="#FFD43B", line_color="#306998", line_width=3, alpha=0.95)

# Style text - scaled for 4800x2700
p.title.text_font_size = "36pt"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Axis styling
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "white"

# Outline
p.outline_line_width = 2
p.outline_line_color = "#cccccc"

# Save
export_png(p, filename="plot.png")
