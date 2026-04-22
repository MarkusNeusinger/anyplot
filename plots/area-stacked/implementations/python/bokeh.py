""" pyplots.ai
area-stacked: Stacked Area Chart
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, FixedTicker, Legend
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Monthly revenue by product category over 2 years
np.random.seed(42)
months = pd.date_range("2023-01-01", periods=24, freq="MS")

# Generate realistic revenue data with trends
base_electronics = 150 + np.arange(24) * 3 + np.random.randn(24) * 15
base_clothing = 100 + np.sin(np.linspace(0, 4 * np.pi, 24)) * 20 + np.random.randn(24) * 10
base_home = 80 + np.arange(24) * 1.5 + np.random.randn(24) * 8
base_sports = 50 + np.cos(np.linspace(0, 4 * np.pi, 24)) * 15 + np.random.randn(24) * 5

# Ensure all values are positive
electronics = np.maximum(base_electronics, 20)
clothing = np.maximum(base_clothing, 15)
home_garden = np.maximum(base_home, 10)
sports = np.maximum(base_sports, 8)

# Calculate stacked values (cumulative sums for stacking)
stack_sports = sports
stack_home = stack_sports + home_garden
stack_clothing = stack_home + clothing
stack_electronics = stack_clothing + electronics

# Convert dates to strings for bokeh x-axis
x_labels = [d.strftime("%b %Y") for d in months]
x_values = list(range(len(months)))

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="area-stacked · bokeh · pyplots.ai",
    x_axis_label="Month",
    y_axis_label="Revenue ($K)",
    x_range=(-0.5, 23.5),
    y_range=(0, max(stack_electronics) * 1.1),
)

# Colors - Python Blue primary, then harmonious colors
colors = ["#306998", "#FFD43B", "#4B8BBE", "#FFE873"]

# Create stacked areas using varea_stack (areas stacked from bottom)
# We need to draw from top to bottom to layer correctly
legend_items = []

# Electronics (top layer)
source_electronics = ColumnDataSource(data={"x": x_values, "y1": stack_clothing, "y2": stack_electronics})
r_electronics = p.varea(x="x", y1="y1", y2="y2", source=source_electronics, fill_color=colors[0], fill_alpha=0.85)
legend_items.append(("Electronics", [r_electronics]))

# Clothing
source_clothing = ColumnDataSource(data={"x": x_values, "y1": stack_home, "y2": stack_clothing})
r_clothing = p.varea(x="x", y1="y1", y2="y2", source=source_clothing, fill_color=colors[1], fill_alpha=0.85)
legend_items.append(("Clothing", [r_clothing]))

# Home & Garden
source_home = ColumnDataSource(data={"x": x_values, "y1": stack_sports, "y2": stack_home})
r_home = p.varea(x="x", y1="y1", y2="y2", source=source_home, fill_color=colors[2], fill_alpha=0.85)
legend_items.append(("Home & Garden", [r_home]))

# Sports (bottom layer)
source_sports = ColumnDataSource(data={"x": x_values, "y1": np.zeros(len(x_values)), "y2": stack_sports})
r_sports = p.varea(x="x", y1="y1", y2="y2", source=source_sports, fill_color=colors[3], fill_alpha=0.85)
legend_items.append(("Sports", [r_sports]))

# Add legend
legend = Legend(items=legend_items, location="top_left")
legend.label_text_font_size = "24pt"
legend.glyph_height = 40
legend.glyph_width = 40
legend.spacing = 15
legend.padding = 20
legend.background_fill_alpha = 0.8
legend.border_line_color = "#cccccc"
p.add_layout(legend, "right")

# Style text sizes for large canvas
p.title.text_font_size = "36pt"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "20pt"
p.yaxis.major_label_text_font_size = "20pt"

# Custom x-axis tick labels (show every 3 months)
p.xaxis.ticker = FixedTicker(ticks=[0, 3, 6, 9, 12, 15, 18, 21, 23])
p.xaxis.major_label_overrides = {i: x_labels[i] for i in range(len(x_labels))}
p.xaxis.major_label_orientation = 0.6

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "white"

# Outline
p.outline_line_color = "#cccccc"

# Save outputs
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="area-stacked · bokeh · pyplots.ai")
