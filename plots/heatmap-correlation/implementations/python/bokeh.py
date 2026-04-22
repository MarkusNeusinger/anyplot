""" pyplots.ai
heatmap-correlation: Correlation Matrix Heatmap
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import BasicTicker, ColorBar, ColumnDataSource, HoverTool, LabelSet, LinearColorMapper
from bokeh.palettes import RdBu11
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - realistic financial/economic indicators
np.random.seed(42)
variables = ["GDP", "Unemployment", "Inflation", "Interest Rate", "Stock Index", "Consumer Conf.", "Housing", "Exports"]
n_vars = len(variables)

# Generate realistic correlation matrix with known economic relationships
base_corr = np.array(
    [
        [1.00, -0.72, 0.35, 0.28, 0.85, 0.78, 0.65, 0.72],  # GDP
        [-0.72, 1.00, -0.15, -0.22, -0.68, -0.82, -0.55, -0.48],  # Unemployment
        [0.35, -0.15, 1.00, 0.65, 0.12, -0.25, -0.18, 0.22],  # Inflation
        [0.28, -0.22, 0.65, 1.00, -0.08, -0.35, -0.42, 0.15],  # Interest Rate
        [0.85, -0.68, 0.12, -0.08, 1.00, 0.72, 0.58, 0.62],  # Stock Index
        [0.78, -0.82, -0.25, -0.35, 0.72, 1.00, 0.68, 0.55],  # Consumer Confidence
        [0.65, -0.55, -0.18, -0.42, 0.58, 0.68, 1.00, 0.45],  # Housing
        [0.72, -0.48, 0.22, 0.15, 0.62, 0.55, 0.45, 1.00],  # Exports
    ]
)

# Create mask for lower triangle (including diagonal)
mask = np.triu(np.ones_like(base_corr, dtype=bool), k=1)
corr_matrix = np.where(mask, np.nan, base_corr)

# Prepare data for heatmap
x_data = []
y_data = []
values = []
text_values = []
text_colors = []

for i, var_y in enumerate(variables):
    for j, var_x in enumerate(variables):
        if not np.isnan(corr_matrix[i, j]):
            x_data.append(var_x)
            y_data.append(var_y)
            val = corr_matrix[i, j]
            values.append(val)
            text_values.append(f"{val:.2f}")
            # White text for extreme values, dark text for middle range
            text_colors.append("#FFFFFF" if abs(val) > 0.55 else "#333333")

source = ColumnDataSource(
    data={"x": x_data, "y": y_data, "values": values, "text": text_values, "text_color": text_colors}
)

# Create figure with square aspect ratio
p = figure(
    width=3600,
    height=3600,
    x_range=variables,
    y_range=list(reversed(variables)),
    x_axis_location="below",
    title="heatmap-correlation · bokeh · pyplots.ai",
    toolbar_location="right",
    tools="",
)

# Diverging color mapper centered at zero
mapper = LinearColorMapper(palette=list(reversed(RdBu11)), low=-1, high=1, nan_color="white")

# Draw rectangles for heatmap
rects = p.rect(
    x="x",
    y="y",
    width=0.95,
    height=0.95,
    source=source,
    fill_color={"field": "values", "transform": mapper},
    line_color="white",
    line_width=2,
)

# Add HoverTool for interactivity
hover = HoverTool(renderers=[rects], tooltips=[("Row", "@y"), ("Column", "@x"), ("Correlation", "@text")])
p.add_tools(hover)

# Add text annotations with dynamic color based on background
labels = LabelSet(
    x="x",
    y="y",
    text="text",
    text_color="text_color",
    source=source,
    text_align="center",
    text_baseline="middle",
    text_font_size="22pt",
    text_font_style="bold",
)
p.add_layout(labels)

# Add colorbar
color_bar = ColorBar(
    color_mapper=mapper,
    ticker=BasicTicker(desired_num_ticks=11),
    label_standoff=20,
    width=60,
    location=(0, 0),
    title="Correlation",
    title_text_font_size="22pt",
    major_label_text_font_size="18pt",
    title_standoff=15,
)
p.add_layout(color_bar, "right")

# Style the figure
p.title.text_font_size = "32pt"
p.title.align = "center"

# Domain-specific axis labels
p.xaxis.axis_label = "Economic Indicators"
p.yaxis.axis_label = "Economic Indicators"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_orientation = 0.785  # 45 degrees in radians

# Grid styling
p.xgrid.visible = False
p.ygrid.visible = False

# Axis styling
p.outline_line_color = None
p.axis.axis_line_color = None
p.axis.major_tick_line_color = None

# Save as PNG and HTML
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="heatmap-correlation · bokeh · pyplots.ai")
