""" pyplots.ai
lollipop-grouped: Grouped Lollipop Chart
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, Legend, LegendItem
from bokeh.plotting import figure


# Data - Quarterly Revenue by Product Line across Regions
np.random.seed(42)

categories = ["North", "South", "East", "West"]
series_names = ["Electronics", "Clothing", "Food", "Home"]
series_colors = ["#306998", "#FFD43B", "#2E8B57", "#9467BD"]

# Generate revenue data (in millions)
data = {
    "Electronics": [85, 72, 91, 68],
    "Clothing": [62, 78, 55, 71],
    "Food": [45, 52, 48, 58],
    "Home": [38, 41, 35, 47],
}

# Create the figure
p = figure(
    width=4800,
    height=2700,
    title="lollipop-grouped · bokeh · pyplots.ai",
    x_axis_label="Region",
    y_axis_label="Revenue ($ Million)",
    x_range=(-1, len(categories) * (len(series_names) + 1)),
    y_range=(0, 105),
)

# Plot lollipops for each series
legend_items = []

for series_idx, (series_name, color) in enumerate(zip(series_names, series_colors, strict=True)):
    # Calculate x positions for this series
    x_pos = [i * (len(series_names) + 1) + series_idx for i in range(len(categories))]
    y_vals = data[series_name]

    # Create source for stems (vertical lines from 0 to value)
    for x, y in zip(x_pos, y_vals, strict=True):
        stem_source = ColumnDataSource(data={"x": [x, x], "y": [0, y]})
        p.line(x="x", y="y", source=stem_source, line_width=8, color=color, alpha=0.85)

    # Create source for markers
    marker_source = ColumnDataSource(data={"x": x_pos, "y": y_vals})
    circle = p.scatter(
        x="x", y="y", source=marker_source, size=45, color=color, alpha=0.95, line_color="white", line_width=4
    )
    legend_items.append(LegendItem(label=series_name, renderers=[circle]))

# Add legend inside the plot area
legend = Legend(items=legend_items, location="top_right")
legend.label_text_font_size = "32pt"
legend.glyph_height = 45
legend.glyph_width = 45
legend.spacing = 20
legend.padding = 30
legend.background_fill_alpha = 0.9
legend.border_line_width = 3
legend.border_line_color = "#cccccc"
p.add_layout(legend)

# Set custom x-axis tick labels (category names at group centers)
group_centers = [(i * (len(series_names) + 1) + 1.5) for i in range(len(categories))]
p.xaxis.ticker = group_centers
p.xaxis.major_label_overrides = dict(zip(group_centers, categories, strict=True))

# Styling - Large text for 4800x2700 canvas
p.title.text_font_size = "48pt"
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "36pt"
p.yaxis.axis_label_text_font_size = "36pt"
p.xaxis.major_label_text_font_size = "32pt"
p.yaxis.major_label_text_font_size = "28pt"

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "white"

# Axis styling
p.xaxis.axis_line_width = 3
p.yaxis.axis_line_width = 3
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.major_tick_line_width = 3
p.yaxis.major_tick_line_width = 3

# Outline
p.outline_line_width = 2
p.outline_line_color = "#cccccc"

# Save
export_png(p, filename="plot.png")
