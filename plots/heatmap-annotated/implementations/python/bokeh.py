""" pyplots.ai
heatmap-annotated: Annotated Heatmap
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import BasicTicker, ColorBar, ColumnDataSource, LinearColorMapper
from bokeh.plotting import figure
from bokeh.transform import transform


# Data: Correlation matrix for financial metrics
np.random.seed(42)
variables = ["Revenue", "Profit", "Assets", "Debt", "Growth", "ROI", "Market Cap", "Volume"]
n = len(variables)

# Generate realistic correlation matrix
base = np.random.randn(100, n)
base[:, 1] = base[:, 0] * 0.8 + np.random.randn(100) * 0.5  # Profit correlates with Revenue
base[:, 5] = base[:, 1] * 0.7 + np.random.randn(100) * 0.6  # ROI correlates with Profit
base[:, 6] = base[:, 0] * 0.6 + np.random.randn(100) * 0.7  # Market Cap correlates with Revenue
base[:, 3] = -base[:, 5] * 0.5 + np.random.randn(100) * 0.8  # Debt negatively correlates with ROI
corr_matrix = np.corrcoef(base.T)
np.fill_diagonal(corr_matrix, 1.0)

# Prepare data for bokeh
x_coords = []
y_coords = []
values = []
text_values = []
text_colors = []

for i, row_var in enumerate(variables):
    for j, col_var in enumerate(variables):
        x_coords.append(col_var)
        y_coords.append(row_var)
        val = corr_matrix[i, j]
        values.append(val)
        text_values.append(f"{val:.2f}")
        # White text for dark cells, black text for light cells
        text_colors.append("white" if abs(val) > 0.5 else "black")

source = ColumnDataSource(
    data={"x": x_coords, "y": y_coords, "value": values, "text": text_values, "text_color": text_colors}
)

# Create color mapper with diverging palette (blue-white-red)
colors = ["#2166AC", "#4393C3", "#92C5DE", "#D1E5F0", "#F7F7F7", "#FDDBC7", "#F4A582", "#D6604D", "#B2182B"]
mapper = LinearColorMapper(palette=colors, low=-1, high=1)

# Create figure
p = figure(
    width=3600,
    height=3600,
    x_range=variables,
    y_range=list(reversed(variables)),
    title="heatmap-annotated · bokeh · pyplots.ai",
    x_axis_location="above",
    toolbar_location=None,
)

# Add heatmap rectangles
p.rect(
    x="x",
    y="y",
    width=1,
    height=1,
    source=source,
    fill_color=transform("value", mapper),
    line_color="white",
    line_width=2,
)

# Add text annotations
p.text(
    x="x",
    y="y",
    text="text",
    source=source,
    text_align="center",
    text_baseline="middle",
    text_font_size="24pt",
    text_color="text_color",
)

# Style the figure
p.title.text_font_size = "32pt"
p.title.align = "center"
p.xaxis.axis_label = "Variable"
p.yaxis.axis_label = "Variable"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_orientation = 0.7
p.axis.axis_line_color = None
p.axis.major_tick_line_color = None
p.grid.grid_line_color = None

# Add colorbar
color_bar = ColorBar(
    color_mapper=mapper,
    ticker=BasicTicker(desired_num_ticks=9),
    label_standoff=12,
    major_label_text_font_size="16pt",
    title="Correlation",
    title_text_font_size="20pt",
    width=40,
    location=(0, 0),
)
p.add_layout(color_bar, "right")

# Save
export_png(p, filename="plot.png")
