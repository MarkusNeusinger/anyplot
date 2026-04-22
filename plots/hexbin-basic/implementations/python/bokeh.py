""" pyplots.ai
hexbin-basic: Basic Hexbin Plot
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 90/100 | Created: 2026-02-21
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.plotting import figure
from bokeh.transform import linear_cmap
from bokeh.util.hex import hexbin


# Data - environmental sensor network readings across monitoring zones
np.random.seed(42)

centers = [(-3, -1), (3, 1), (-1, 4)]
cluster_sizes = [4000, 4000, 2000]
spreads = [1.0, 1.4, 0.7]

x_data = []
y_data = []
for (cx, cy), size, sigma in zip(centers, cluster_sizes, spreads, strict=True):
    x_data.extend(np.random.randn(size) * sigma + cx)
    y_data.extend(np.random.randn(size) * sigma + cy)

x = np.array(x_data)
y = np.array(y_data)

# Hexbin computation using Bokeh's native utility
bins = hexbin(x, y, 0.3)

# Plot
p = figure(
    width=4800,
    height=2700,
    title="hexbin-basic · bokeh · pyplots.ai",
    x_axis_label="Distance East (km)",
    y_axis_label="Distance North (km)",
    tools="",
    toolbar_location=None,
    background_fill_color="#440154",
)

# Hex tiles with Viridis color mapping
r = p.hex_tile(
    q="q",
    r="r",
    size=0.3,
    line_color=None,
    source=bins,
    fill_color=linear_cmap("counts", "Viridis256", 0, max(bins.counts)),
)

# Color bar from renderer
color_bar = r.construct_color_bar(width=30, title="Count", location=(0, 0))
color_bar.title_text_font_size = "20pt"
color_bar.major_label_text_font_size = "16pt"
color_bar.title_text_color = "white"
color_bar.major_label_text_color = "white"
color_bar.background_fill_color = "#440154"
color_bar.background_fill_alpha = 0
p.add_layout(color_bar, "right")

# Styling for 4800x2700
p.title.text_font_size = "28pt"
p.title.text_color = "white"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

p.xaxis.axis_line_color = None
p.yaxis.axis_line_color = None
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.axis_label_text_color = "white"
p.yaxis.axis_label_text_color = "white"
p.xaxis.major_label_text_color = "#CCCCCC"
p.yaxis.major_label_text_color = "#CCCCCC"

p.border_fill_color = "#440154"
p.outline_line_color = None
p.grid.visible = False

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html")
