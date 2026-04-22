""" pyplots.ai
line-multi: Multi-Line Comparison Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, Legend
from bokeh.plotting import figure, save
from bokeh.resources import CDN


# Data: Monthly sales (thousands) for 4 product lines over 12 months
np.random.seed(42)
months = np.arange(1, 13)

# Generate realistic sales trends for different products
electronics = 45 + np.cumsum(np.random.randn(12) * 3) + months * 2
clothing = 35 + np.cumsum(np.random.randn(12) * 2.5) + np.sin(months * np.pi / 6) * 8
furniture = 25 + np.cumsum(np.random.randn(12) * 2) + months * 0.5
groceries = 55 + np.cumsum(np.random.randn(12) * 1.5)

# Create figure (4800 x 2700 px for 16:9)
p = figure(
    width=4800,
    height=2700,
    title="line-multi · bokeh · pyplots.ai",
    x_axis_label="Month",
    y_axis_label="Sales (thousands $)",
)

# Colors: Python Blue first, then additional colorblind-safe colors
colors = ["#306998", "#FFD43B", "#E24A33", "#348ABD"]
line_dashes = ["solid", "solid", "dashed", "dashed"]
series_names = ["Electronics", "Clothing", "Furniture", "Groceries"]
series_data = [electronics, clothing, furniture, groceries]

# Plot each series with lines and markers
renderers = []
for name, data, color, dash in zip(series_names, series_data, colors, line_dashes, strict=True):
    source = ColumnDataSource(data={"x": months, "y": data})

    # Line
    line = p.line(x="x", y="y", source=source, line_width=5, line_color=color, line_dash=dash, line_alpha=0.9)

    # Markers for better readability
    scatter = p.scatter(x="x", y="y", source=source, size=18, color=color, alpha=0.9)

    renderers.append((name, [line, scatter]))

# Create legend
legend = Legend(items=renderers, location="top_left")
legend.label_text_font_size = "20pt"
legend.glyph_height = 30
legend.glyph_width = 30
legend.spacing = 10
legend.padding = 20
legend.background_fill_alpha = 0.7
p.add_layout(legend, "right")

# Title styling
p.title.text_font_size = "28pt"
p.title.align = "center"

# Axis label styling
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = [6, 4]
p.ygrid.grid_line_dash = [6, 4]

# Axis ticks
p.xaxis.ticker = list(range(1, 13))
p.xaxis.major_label_overrides = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec",
}

# Outline
p.outline_line_color = "#333333"
p.outline_line_width = 2

# Save as PNG
export_png(p, filename="plot.png")

# Save as HTML for interactive version
save(p, filename="plot.html", title="line-multi · bokeh · pyplots.ai", resources=CDN)
