""" pyplots.ai
bar-stacked-labeled: Stacked Bar Chart with Total Labels
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, LabelSet
from bokeh.plotting import figure


# Data - Quarterly revenue by product category
np.random.seed(42)
categories = ["Q1", "Q2", "Q3", "Q4"]
components = ["Electronics", "Clothing", "Home & Garden", "Sports"]
colors = ["#306998", "#FFD43B", "#4ECDC4", "#FF6B6B"]

# Generate realistic quarterly revenue data (in millions)
data = {
    "Electronics": [45, 52, 48, 68],
    "Clothing": [32, 38, 55, 72],
    "Home & Garden": [28, 42, 38, 35],
    "Sports": [18, 25, 32, 45],
}

# Calculate totals for labels
totals = [sum(data[comp][i] for comp in components) for i in range(len(categories))]

# Create figure with categorical x-axis
p = figure(
    x_range=categories,
    width=4800,
    height=2700,
    title="bar-stacked-labeled · bokeh · pyplots.ai",
    x_axis_label="Quarter",
    y_axis_label="Revenue ($M)",
    toolbar_location=None,
)

# Track bottom positions for stacking
bottoms = [0] * len(categories)

# Plot stacked bars
for comp, color in zip(components, colors, strict=True):
    tops = [b + v for b, v in zip(bottoms, data[comp], strict=True)]
    source = ColumnDataSource(
        data={"categories": categories, "values": data[comp], "bottoms": bottoms.copy(), "tops": tops}
    )

    p.vbar(
        x="categories",
        top="tops",
        bottom="bottoms",
        width=0.7,
        source=source,
        color=color,
        legend_label=comp,
        line_color="white",
        line_width=2,
    )

    # Update bottoms for next stack
    bottoms = tops.copy()

# Add total labels above each bar stack
label_source = ColumnDataSource(
    data={
        "x": categories,
        "y": [t + 5 for t in totals],  # Offset above bars
        "text": [f"${t}M" for t in totals],
    }
)

labels = LabelSet(
    x="x",
    y="y",
    text="text",
    source=label_source,
    text_font_size="36pt",
    text_font_style="bold",
    text_color="#333333",
    text_align="center",
    text_baseline="bottom",
)
p.add_layout(labels)

# Styling for large canvas (4800x2700)
p.title.text_font_size = "42pt"
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "32pt"
p.yaxis.axis_label_text_font_size = "32pt"
p.xaxis.major_label_text_font_size = "28pt"
p.yaxis.major_label_text_font_size = "24pt"

# Grid styling
p.xgrid.grid_line_color = None
p.ygrid.grid_line_alpha = 0.3
p.ygrid.grid_line_dash = "dashed"

# Legend styling - position in top right to avoid covering bars
p.legend.location = "top_right"
p.legend.label_text_font_size = "24pt"
p.legend.glyph_height = 35
p.legend.glyph_width = 35
p.legend.spacing = 12
p.legend.padding = 20
p.legend.background_fill_alpha = 0.9
p.legend.border_line_color = "#cccccc"

# Set y-axis range to accommodate labels
p.y_range.end = max(totals) + 30

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "white"

# Axis line styling
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2

# Save
export_png(p, filename="plot.png")
