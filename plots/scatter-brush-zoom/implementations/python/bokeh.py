""" pyplots.ai
scatter-brush-zoom: Interactive Scatter Plot with Brush Selection and Zoom
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-08
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import (
    BoxSelectTool,
    ColumnDataSource,
    HoverTool,
    Legend,
    LegendItem,
    PanTool,
    ResetTool,
    WheelZoomTool,
)
from bokeh.plotting import figure
from bokeh.transform import factor_cmap


# Data - Generate clustered data for demonstrating brush selection
np.random.seed(42)

# Create 4 clusters with different characteristics
n_per_cluster = 75
clusters = []
labels = ["Cluster A", "Cluster B", "Cluster C", "Cluster D"]
centers = [(20, 30), (60, 70), (25, 75), (70, 25)]
spreads = [8, 10, 6, 9]

for i, (cx, cy) in enumerate(centers):
    x_vals = np.random.normal(cx, spreads[i], n_per_cluster)
    y_vals = np.random.normal(cy, spreads[i], n_per_cluster)
    cluster = np.full(n_per_cluster, labels[i])
    clusters.append((x_vals, y_vals, cluster))

x = np.concatenate([c[0] for c in clusters])
y = np.concatenate([c[1] for c in clusters])
category = np.concatenate([c[2] for c in clusters])

# Create ColumnDataSource
source = ColumnDataSource(data={"x": x, "y": y, "category": category})

# Create figure with interactive tools
# BoxSelectTool for brush selection, WheelZoomTool for zoom, PanTool for panning
p = figure(
    width=4800,
    height=2700,
    title="scatter-brush-zoom · bokeh · pyplots.ai",
    x_axis_label="X Value",
    y_axis_label="Y Value",
    tools="",  # Clear default tools, we'll add custom ones
    output_backend="webgl",  # Better performance for many points
)

# Add specific tools for brush and zoom functionality
box_select = BoxSelectTool()
wheel_zoom = WheelZoomTool()
pan = PanTool()
reset = ResetTool()
hover = HoverTool(tooltips=[("Category", "@category"), ("X", "@x{0.1}"), ("Y", "@y{0.1}")])

p.add_tools(box_select, wheel_zoom, pan, reset, hover)
p.toolbar.active_drag = box_select  # Default to box select
p.toolbar.active_scroll = wheel_zoom  # Mouse wheel zooms

# Color palette for categories
colors = ["#306998", "#FFD43B", "#E74C3C", "#2ECC71"]  # Python Blue, Yellow, Red, Green
color_map = factor_cmap("category", palette=colors, factors=labels)

# Plot scatter with selection styling
p.scatter(
    "x",
    "y",
    source=source,
    size=25,
    fill_color=color_map,
    line_color="white",
    line_width=2,
    alpha=0.8,
    # Selection styling - selected points are highlighted
    selection_fill_color=color_map,
    selection_line_color="#333333",
    selection_line_width=4,
    selection_alpha=1.0,
    # Non-selected styling - dimmed when selection is active
    nonselection_fill_color=color_map,
    nonselection_line_color="white",
    nonselection_alpha=0.2,
)

# Style the title - large for 4800x2700 canvas
p.title.text_font_size = "48pt"
p.title.align = "center"

# Style axes labels - scaled for large canvas
p.xaxis.axis_label_text_font_size = "36pt"
p.yaxis.axis_label_text_font_size = "36pt"
p.xaxis.major_label_text_font_size = "28pt"
p.yaxis.major_label_text_font_size = "28pt"

# Style axis lines and ticks
p.xaxis.axis_line_width = 3
p.yaxis.axis_line_width = 3
p.xaxis.major_tick_line_width = 3
p.yaxis.major_tick_line_width = 3
p.xaxis.minor_tick_line_width = 2
p.yaxis.minor_tick_line_width = 2

# Grid styling - subtle
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"
p.xgrid.grid_line_width = 2
p.ygrid.grid_line_width = 2

# Toolbar styling
p.toolbar.logo = None
p.toolbar.autohide = False

# Add legend manually with larger sizing
legend_items = []
for i, label in enumerate(labels):
    # Create a dummy renderer for legend
    r = p.scatter([], [], fill_color=colors[i], line_color="white", size=25, alpha=0.8)
    legend_items.append(LegendItem(label=label, renderers=[r]))

legend = Legend(items=legend_items, location="top_right")
legend.label_text_font_size = "28pt"
legend.glyph_height = 35
legend.glyph_width = 35
legend.spacing = 15
legend.padding = 25
legend.background_fill_alpha = 0.85
legend.border_line_width = 2
legend.border_line_color = "#cccccc"
p.add_layout(legend)

# Set outer padding for better layout
p.min_border_left = 120
p.min_border_bottom = 100
p.min_border_right = 50
p.min_border_top = 80

# Save as PNG
export_png(p, filename="plot.png")

# Also save as HTML for full interactivity
output_file("plot.html")
save(p)
