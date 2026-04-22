""" pyplots.ai
horizon-basic: Horizon Chart
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import numpy as np
from bokeh.io import export_png
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, HoverTool, Label, Range1d, Title
from bokeh.plotting import figure, output_file, save


# Data - Server metrics over 24 hours for 6 servers
np.random.seed(42)

n_points = 200
n_series = 6
server_names = ["Web Server 1", "Web Server 2", "Database", "Cache Server", "API Gateway", "Load Balancer"]

# Create time series data with different patterns
hours = np.linspace(0, 24, n_points)

# Each server has a different pattern
series_data = []
for i, name in enumerate(server_names):
    # Base pattern with some periodicity
    base = np.sin(hours * np.pi / 6 + i * 0.5) * 20
    # Add some noise and trends
    noise = np.random.randn(n_points) * 10
    trend = np.sin(hours * np.pi / 12) * 15 * (1 + i * 0.2)
    # Add some spikes for realism
    spikes = np.zeros(n_points)
    spike_locations = np.random.choice(n_points, size=5, replace=False)
    spikes[spike_locations] = np.random.randn(5) * 30

    values = base + noise + trend + spikes
    series_data.append({"name": name, "hours": hours, "values": values})

# Horizon chart parameters
n_bands = 3  # Number of positive/negative bands
chart_width = 4800
total_height = 2700
individual_height = total_height // n_series  # ~450px per series

# Define colors - blue for positive, orange for negative (colorblind-friendly)
pos_colors = ["#a6cee3", "#306998", "#08306b"]  # Light to dark blue (using Python Blue)
neg_colors = ["#fdd0a2", "#f16913", "#8c2d04"]  # Light to dark orange (colorblind-safe)

# Create individual horizon plots
plots = []

for idx, data in enumerate(series_data):
    values = data["values"]
    x = data["hours"]
    name = data["name"]

    # Normalize values to fit in bands
    max_abs = np.max(np.abs(values))
    band_size = max_abs / n_bands

    # Create figure for this series
    p = figure(
        width=chart_width,
        height=individual_height,
        x_range=Range1d(0, 24),
        y_range=Range1d(0, band_size),
        tools="pan,wheel_zoom,box_zoom,reset,hover",
        toolbar_location="right" if idx == 0 else None,
    )

    # Configure axes
    if idx < len(series_data) - 1:
        p.xaxis.visible = False
    else:
        p.xaxis.axis_label = "Hour of Day"
        p.xaxis.axis_label_text_font_size = "24pt"
        p.xaxis.major_label_text_font_size = "20pt"

    p.yaxis.visible = False
    p.grid.visible = False
    p.outline_line_color = "#cccccc"
    p.outline_line_width = 1

    # Add series name as label on the left (larger for better readability)
    label = Label(
        x=0.3,
        y=band_size * 0.5,
        text=name,
        text_font_size="26pt",
        text_font_style="bold",
        text_align="left",
        text_baseline="middle",
        text_color="#333333",
    )
    p.add_layout(label)

    # Add customized HoverTool showing actual values
    hover = HoverTool(tooltips=[("Server", name), ("Hour", "@x{0.1}"), ("Value", "@original{0.1}")], mode="vline")
    p.add_tools(hover)

    # Draw horizon bands (folded areas)
    for band_idx in range(n_bands):
        band_min = band_idx * band_size

        # Positive values for this band
        pos_vals = np.clip(values - band_min, 0, band_size)
        pos_vals = np.where(values > band_min, pos_vals, 0)

        # Negative values for this band (mirrored)
        neg_vals = np.clip(-values - band_min, 0, band_size)
        neg_vals = np.where(values < -band_min, neg_vals, 0)

        # Create patches for positive band
        if np.any(pos_vals > 0):
            source_pos = ColumnDataSource(data={"x": x, "y": pos_vals, "original": values})
            p.varea(x="x", y1=0, y2="y", source=source_pos, fill_color=pos_colors[band_idx], fill_alpha=0.9)

        # Create patches for negative band
        if np.any(neg_vals > 0):
            source_neg = ColumnDataSource(data={"x": x, "y": neg_vals, "original": values})
            p.varea(x="x", y1=0, y2="y", source=source_neg, fill_color=neg_colors[band_idx], fill_alpha=0.9)

    plots.append(p)

# Add main title to the first plot
plots[0].add_layout(Title(text="horizon-basic · bokeh · pyplots.ai", text_font_size="32pt", align="center"), "above")

# Create legend figure explaining color bands
legend_height = 150
legend_fig = figure(
    width=chart_width,
    height=legend_height,
    x_range=Range1d(0, 100),
    y_range=Range1d(0, 10),
    tools="",
    toolbar_location=None,
)
legend_fig.xaxis.visible = False
legend_fig.yaxis.visible = False
legend_fig.grid.visible = False
legend_fig.outline_line_color = None

# Add legend title
legend_fig.add_layout(
    Label(x=2, y=7, text="Color Legend:", text_font_size="22pt", text_font_style="bold", text_color="#333333")
)

# Positive bands legend (left side)
legend_fig.add_layout(
    Label(x=20, y=7, text="Positive Values (above baseline):", text_font_size="18pt", text_color="#333333")
)
for i, (color, label_text) in enumerate(zip(pos_colors, ["Low (+)", "Medium (+)", "High (+)"], strict=True)):
    legend_fig.rect(x=22 + i * 8, y=3, width=6, height=4, fill_color=color, line_color=None)
    legend_fig.add_layout(
        Label(x=22 + i * 8, y=0.5, text=label_text, text_font_size="14pt", text_align="center", text_color="#333333")
    )

# Negative bands legend (right side)
legend_fig.add_layout(
    Label(x=55, y=7, text="Negative Values (below baseline):", text_font_size="18pt", text_color="#333333")
)
for i, (color, label_text) in enumerate(zip(neg_colors, ["Low (−)", "Medium (−)", "High (−)"], strict=True)):
    legend_fig.rect(x=57 + i * 8, y=3, width=6, height=4, fill_color=color, line_color=None)
    legend_fig.add_layout(
        Label(x=57 + i * 8, y=0.5, text=label_text, text_font_size="14pt", text_align="center", text_color="#333333")
    )

# Combine all plots vertically with legend at top
layout = column(legend_fig, *plots)

# Save as HTML (interactive)
output_file("plot.html", title="Horizon Chart - pyplots.ai")
save(layout)

# Save as PNG
export_png(layout, filename="plot.png")
