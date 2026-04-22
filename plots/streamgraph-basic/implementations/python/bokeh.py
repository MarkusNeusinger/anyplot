""" pyplots.ai
streamgraph-basic: Basic Stream Graph
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Legend
from bokeh.plotting import figure


# Data: monthly streaming hours by music genre over two years
np.random.seed(42)

months = pd.date_range(start="2022-01-01", periods=24, freq="ME")
categories = ["Pop", "Rock", "Hip-Hop", "Electronic", "Jazz", "Classical"]

# Generate streaming data for each genre with natural variations
n_points = len(months)
base = np.linspace(0, 4 * np.pi, n_points)

data = {
    "Pop": 45 + 18 * np.sin(base) + np.random.randn(n_points) * 3,
    "Rock": 38 + 12 * np.sin(base + 0.8) + np.random.randn(n_points) * 2.5,
    "Hip-Hop": 35 + 22 * np.sin(base + 1.6) + np.random.randn(n_points) * 4,
    "Electronic": 28 + 14 * np.sin(base + 2.4) + np.random.randn(n_points) * 2.5,
    "Jazz": 18 + 10 * np.sin(base + 3.2) + np.random.randn(n_points) * 2,
    "Classical": 14 + 6 * np.sin(base + 4.0) + np.random.randn(n_points) * 1.5,
}

# Ensure all values are positive
for cat in categories:
    data[cat] = np.maximum(data[cat], 5)

# Convert to DataFrame
df = pd.DataFrame(data)
df["month"] = months

# Calculate stacked values with symmetric baseline (centered around 0)
values = df[categories].values
cumulative = np.cumsum(values, axis=1)
total = cumulative[:, -1]

# Center the baseline: offset so the middle is at 0
baseline_offset = total / 2
y_bottom = np.zeros_like(values)
y_top = np.zeros_like(values)

for i in range(len(categories)):
    if i == 0:
        y_bottom[:, i] = -baseline_offset
        y_top[:, i] = y_bottom[:, i] + values[:, i]
    else:
        y_bottom[:, i] = y_top[:, i - 1]
        y_top[:, i] = y_bottom[:, i] + values[:, i]

# Create smooth interpolated curves for flowing appearance using numpy
x_numeric = np.arange(n_points)
n_smooth = n_points * 10
x_smooth = np.linspace(0, n_points - 1, n_smooth)

# Convert smooth indices back to datetime
date_min = months.min()
date_max = months.max()
months_smooth = pd.date_range(start=date_min, end=date_max, periods=n_smooth)

y_bottom_smooth = np.zeros((n_smooth, len(categories)))
y_top_smooth = np.zeros((n_smooth, len(categories)))

# Use polynomial interpolation for smooth curves
for i in range(len(categories)):
    # Fit polynomial and interpolate for smooth curves
    poly_bottom = np.polyfit(x_numeric, y_bottom[:, i], deg=min(10, n_points - 1))
    poly_top = np.polyfit(x_numeric, y_top[:, i], deg=min(10, n_points - 1))
    y_bottom_smooth[:, i] = np.polyval(poly_bottom, x_smooth)
    y_top_smooth[:, i] = np.polyval(poly_top, x_smooth)

# Colors - Python Blue first, then harmonious colorblind-safe palette
colors = ["#306998", "#FFD43B", "#E07A5F", "#81B29A", "#F2CC8F", "#3D405B"]

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="streamgraph-basic · bokeh · pyplots.ai",
    x_axis_label="Time",
    y_axis_label="Streaming Hours (relative)",
    x_axis_type="datetime",
)

# Style title and axes for large canvas
p.title.text_font_size = "32pt"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Create patches for each category (streamgraph layers) with smooth curves
legend_items = []
x_values = months_smooth.values

for i, cat in enumerate(categories):
    # Create polygon coordinates for smooth stacked area
    # Go forward along top, then backward along bottom
    xs = np.concatenate([x_values, x_values[::-1]])
    ys = np.concatenate([y_top_smooth[:, i], y_bottom_smooth[:, i][::-1]])

    source = ColumnDataSource(data={"x": xs, "y": ys})

    renderer = p.patch(
        x="x", y="y", source=source, fill_color=colors[i], fill_alpha=0.85, line_color=colors[i], line_width=2
    )
    legend_items.append((cat, [renderer]))

# Add legend outside the plot
legend = Legend(items=legend_items, location="center")
legend.label_text_font_size = "20pt"
legend.glyph_height = 35
legend.glyph_width = 35
legend.spacing = 12
p.add_layout(legend, "right")

# Grid styling - subtle
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = [6, 4]

# Keep y-axis visible but subtle
p.yaxis.visible = True
p.outline_line_color = None

# Toolbar placement
p.toolbar_location = "above"

# Save as PNG
export_png(p, filename="plot.png")

# Also save interactive HTML
output_file("plot.html")
save(p)
