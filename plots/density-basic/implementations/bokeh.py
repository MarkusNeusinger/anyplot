""" pyplots.ai
density-basic: Basic Density Plot
Library: bokeh 3.8.2 | Python 3.14
Quality: /100 | Updated: 2026-02-23
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, HoverTool, NumeralTickFormatter
from bokeh.plotting import figure


# Data - Response times (ms) for a web service
np.random.seed(42)
response_times = np.concatenate(
    [
        np.random.normal(150, 30, 300),  # Fast responses
        np.random.normal(280, 40, 100),  # Slower responses (shows bimodality)
    ]
)

# Calculate kernel density estimation (Silverman's rule for bandwidth)
n = len(response_times)
std = np.std(response_times)
iqr = np.percentile(response_times, 75) - np.percentile(response_times, 25)
bandwidth = 0.9 * min(std, iqr / 1.34) * n ** (-0.2)

# Evaluate density on a grid
x_range = np.linspace(response_times.min() - 40, response_times.max() + 40, 500)
density = np.zeros_like(x_range)
for xi in response_times:
    density += np.exp(-0.5 * ((x_range - xi) / bandwidth) ** 2)
density /= n * bandwidth * np.sqrt(2 * np.pi)

# Create data source
source = ColumnDataSource(data={"x": x_range, "density": density})

# Rug plot data (individual observations)
rug_y_pos = -0.0006
rug_source = ColumnDataSource(
    data={
        "x": response_times,
        "y0": np.full_like(response_times, rug_y_pos),
        "y1": np.full_like(response_times, rug_y_pos + 0.0008),
    }
)

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="density-basic · bokeh · pyplots.ai",
    x_axis_label="Response Time (ms)",
    y_axis_label="Density",
)

# Fill under the curve
p.varea(x="x", y1=0, y2="density", source=source, fill_color="#306998", fill_alpha=0.25)

# Density curve
density_line = p.line(x="x", y="density", source=source, line_color="#306998", line_width=6, line_alpha=0.9)

# Hover tool showing density values at cursor position
hover = HoverTool(
    renderers=[density_line],
    tooltips=[("Response Time", "@x{0.0} ms"), ("Density", "@density{0.00000}")],
    mode="vline",
    line_policy="nearest",
)
p.add_tools(hover)

# Rug plot - vertical segments at bottom
p.segment(x0="x", y0="y0", x1="x", y1="y1", source=rug_source, line_color="#306998", line_width=3, line_alpha=0.5)

# Text sizes for large canvas
p.title.text_font_size = "36pt"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Y-axis tick format
p.yaxis.formatter = NumeralTickFormatter(format="0.0000")

# Axis styling
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None

# Grid - y-axis only, subtle
p.xgrid.grid_line_color = None
p.ygrid.grid_line_alpha = 0.15
p.ygrid.grid_line_width = 1

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "#ffffff"
p.outline_line_color = None

# Remove toolbar
p.toolbar_location = None

# Save
export_png(p, filename="plot.png")
