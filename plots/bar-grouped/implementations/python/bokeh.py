""" pyplots.ai
bar-grouped: Grouped Bar Chart
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

from bokeh.io import export_png
from bokeh.models import ColumnDataSource, FactorRange, Legend, LegendItem
from bokeh.plotting import figure
from bokeh.transform import factor_cmap


# Data - Quarterly revenue by product line (in thousands)
categories = ["Q1", "Q2", "Q3", "Q4"]
groups = ["Electronics", "Clothing", "Home & Garden"]

data = {"Electronics": [245, 278, 312, 385], "Clothing": [180, 165, 210, 295], "Home & Garden": [125, 198, 245, 178]}

# Create factors for grouped bars
x = [(cat, group) for cat in categories for group in groups]
values = [data[group][i] for i, cat in enumerate(categories) for group in groups]

source = ColumnDataSource(data={"x": x, "values": values})

# Create figure with categorical axis
p = figure(
    x_range=FactorRange(*x, group_padding=0.3),
    width=4800,
    height=2700,
    title="Quarterly Revenue by Product · bar-grouped · bokeh · pyplots.ai",
)

# Create grouped bars with colors
colors = ["#306998", "#FFD43B", "#4CAF50"]
bars = p.vbar(
    x="x",
    top="values",
    width=0.85,
    source=source,
    line_color="white",
    line_width=3,
    fill_color=factor_cmap("x", palette=colors, factors=groups, start=1, end=2),
)

# Add value labels on top of bars
for factor, value in zip(x, values, strict=True):
    p.text(
        x=[factor],
        y=[value + 5],
        text=[f"${value}K"],
        text_align="center",
        text_baseline="bottom",
        text_font_size="16pt",
        text_color="#333333",
    )

# Title styling - larger for 4800x2700
p.title.text_font_size = "36pt"
p.title.text_color = "#333333"

# X-axis styling
p.xaxis.axis_label = "Quarter"
p.xaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "1pt"  # Hide individual bar labels (minimal)
p.xaxis.major_label_text_color = "#fafafa"  # Match background to hide
p.xaxis.group_text_font_size = "24pt"
p.xaxis.major_label_orientation = 0
p.xaxis.separator_line_color = None

# Y-axis styling
p.yaxis.axis_label = "Revenue ($ Thousands)"
p.yaxis.axis_label_text_font_size = "28pt"
p.yaxis.major_label_text_font_size = "20pt"

# Grid styling
p.xgrid.grid_line_color = None
p.ygrid.grid_line_alpha = 0.3
p.ygrid.grid_line_dash = "dashed"

# Add legend manually with correct colors
legend_items = [
    LegendItem(label=groups[0], renderers=[bars], index=0),
    LegendItem(label=groups[1], renderers=[bars], index=1),
    LegendItem(label=groups[2], renderers=[bars], index=2),
]
legend = Legend(items=legend_items, location="top_right", orientation="vertical")
legend.label_text_font_size = "22pt"
legend.glyph_height = 30
legend.glyph_width = 30
legend.spacing = 15
legend.padding = 25
legend.background_fill_alpha = 0.8
p.add_layout(legend)

# Set y-axis range to accommodate labels
p.y_range.start = 0
p.y_range.end = 430

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "#ffffff"

# Outline
p.outline_line_color = None

# Save output
export_png(p, filename="plot.png")
