""" pyplots.ai
area-stacked-percent: 100% Stacked Area Chart
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure, output_file, save


# Data - Market share evolution over time
np.random.seed(42)
years = np.arange(2015, 2025)

# Generate market share data for 4 product categories
product_a = 40 + np.cumsum(np.random.randn(len(years)) * 2)
product_b = 30 + np.cumsum(np.random.randn(len(years)) * 1.5)
product_c = 20 + np.cumsum(np.random.randn(len(years)) * 1.2)
product_d = 10 + np.cumsum(np.random.randn(len(years)) * 0.8)

# Ensure all values are positive
product_a = np.maximum(product_a, 5)
product_b = np.maximum(product_b, 5)
product_c = np.maximum(product_c, 5)
product_d = np.maximum(product_d, 5)

# Normalize to 100%
totals = product_a + product_b + product_c + product_d
pct_a = (product_a / totals) * 100
pct_b = (product_b / totals) * 100
pct_c = (product_c / totals) * 100
pct_d = (product_d / totals) * 100

# Calculate stacked positions
stack_0 = np.zeros(len(years))
stack_a = pct_a
stack_ab = pct_a + pct_b
stack_abc = pct_a + pct_b + pct_c
stack_abcd = pct_a + pct_b + pct_c + pct_d  # Should be 100

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="area-stacked-percent · bokeh · pyplots.ai",
    x_axis_label="Year",
    y_axis_label="Market Share (%)",
    x_range=(2014.5, 2024.5),
    y_range=(0, 105),
)

# Colors - Python Blue primary, colorblind-safe palette
colors = ["#306998", "#FFD43B", "#2E8B57", "#E07B53"]
categories = ["Product A", "Product B", "Product C", "Product D"]

# Create patches for stacked areas (bottom to top)
# Product D (top layer)
source_d = ColumnDataSource(
    data={"x": np.concatenate([years, years[::-1]]), "y": np.concatenate([stack_abcd, stack_abc[::-1]])}
)
p.patch(
    x="x",
    y="y",
    source=source_d,
    fill_color=colors[3],
    fill_alpha=0.85,
    line_color=colors[3],
    line_width=2,
    legend_label=categories[3],
)

# Product C
source_c = ColumnDataSource(
    data={"x": np.concatenate([years, years[::-1]]), "y": np.concatenate([stack_abc, stack_ab[::-1]])}
)
p.patch(
    x="x",
    y="y",
    source=source_c,
    fill_color=colors[2],
    fill_alpha=0.85,
    line_color=colors[2],
    line_width=2,
    legend_label=categories[2],
)

# Product B
source_b = ColumnDataSource(
    data={"x": np.concatenate([years, years[::-1]]), "y": np.concatenate([stack_ab, stack_a[::-1]])}
)
p.patch(
    x="x",
    y="y",
    source=source_b,
    fill_color=colors[1],
    fill_alpha=0.85,
    line_color=colors[1],
    line_width=2,
    legend_label=categories[1],
)

# Product A (bottom layer)
source_a = ColumnDataSource(
    data={"x": np.concatenate([years, years[::-1]]), "y": np.concatenate([stack_a, stack_0[::-1]])}
)
p.patch(
    x="x",
    y="y",
    source=source_a,
    fill_color=colors[0],
    fill_alpha=0.85,
    line_color=colors[0],
    line_width=2,
    legend_label=categories[0],
)

# Styling for large canvas (scaled for 4800x2700 px)
p.title.text_font_size = "72pt"
p.xaxis.axis_label_text_font_size = "48pt"
p.yaxis.axis_label_text_font_size = "48pt"
p.xaxis.major_label_text_font_size = "36pt"
p.yaxis.major_label_text_font_size = "36pt"

# Grid styling (subtle, per quality criteria VQ-07: alpha 0.2-0.4)
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = [6, 4]
p.ygrid.grid_line_dash = [6, 4]
p.grid.grid_line_width = 2

# Legend styling
p.legend.label_text_font_size = "36pt"
p.legend.location = "top_right"
p.legend.background_fill_alpha = 0.85
p.legend.border_line_alpha = 0.5

# Axis styling
p.xaxis.ticker = list(years)
p.yaxis.ticker = [0, 20, 40, 60, 80, 100]

# Background
p.background_fill_color = "#fafafa"

# Save as PNG
export_png(p, filename="plot.png")

# Save as HTML (interactive)
output_file("plot.html")
save(p)
