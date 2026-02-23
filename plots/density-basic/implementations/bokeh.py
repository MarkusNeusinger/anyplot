"""pyplots.ai
density-basic: Basic Density Plot
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 88/100 | Updated: 2026-02-23
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, HoverTool, Label, NumeralTickFormatter
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

# Identify peaks for visual storytelling
peak1_idx = np.argmax(density[:250])
peak2_idx = 250 + np.argmax(density[250:])
peak1_x, peak1_y = x_range[peak1_idx], density[peak1_idx]
peak2_x, peak2_y = x_range[peak2_idx], density[peak2_idx]

# Create data source
source = ColumnDataSource(data={"x": x_range, "density": density})

# Highlight regions around each peak (for visual emphasis)
mask1 = (x_range > peak1_x - 60) & (x_range < peak1_x + 60)
mask2 = (x_range > peak2_x - 55) & (x_range < peak2_x + 55)
highlight1 = ColumnDataSource(data={"x": x_range[mask1], "density": density[mask1]})
highlight2 = ColumnDataSource(data={"x": x_range[mask2], "density": density[mask2]})

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

# Emphasize peak regions with darker fill
p.varea(x="x", y1=0, y2="density", source=highlight1, fill_color="#306998", fill_alpha=0.15)
p.varea(x="x", y1=0, y2="density", source=highlight2, fill_color="#306998", fill_alpha=0.15)

# Annotate peaks for data storytelling
p.add_layout(
    Label(
        x=peak1_x,
        y=peak1_y,
        text="Fast Responses",
        text_font_size="22pt",
        text_color="#1a3d5c",
        text_font_style="bold",
        text_align="center",
        y_offset=18,
    )
)
p.add_layout(
    Label(
        x=peak2_x,
        y=peak2_y,
        text="Slower Responses",
        text_font_size="22pt",
        text_color="#1a3d5c",
        text_font_style="bold",
        text_align="center",
        y_offset=18,
    )
)

# Hover tool showing density values at cursor position
hover = HoverTool(
    renderers=[density_line],
    tooltips=[("Response Time", "@x{0.0} ms"), ("Density", "@density{0.00000}")],
    mode="vline",
    line_policy="nearest",
)
p.add_tools(hover)

# Rug plot - vertical segments at bottom
p.segment(x0="x", y0="y0", x1="x", y1="y1", source=rug_source, line_color="#306998", line_width=3, line_alpha=0.65)

# Text sizes for large canvas
p.title.text_font_size = "36pt"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Y-axis tick format
p.yaxis.formatter = NumeralTickFormatter(format="0.0000")

# Axis styling - softened to match minimalist chrome
p.xaxis.axis_line_width = 1
p.yaxis.axis_line_width = 1
p.xaxis.axis_line_alpha = 0.5
p.yaxis.axis_line_alpha = 0.5
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
