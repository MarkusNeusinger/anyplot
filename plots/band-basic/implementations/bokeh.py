"""pyplots.ai
band-basic: Basic Band Plot
Library: bokeh 3.8.2 | Python 3.14
Quality: /100 | Updated: 2026-02-23
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


# Data - Time series with 95% confidence interval
np.random.seed(42)
x = np.linspace(0, 10, 100)
y_center = 2 + 0.5 * x + 0.3 * np.sin(2 * x)  # Central trend with slight oscillation
uncertainty = 0.5 + 0.1 * x  # Growing uncertainty over time
y_upper = y_center + 1.96 * uncertainty  # 95% CI upper bound
y_lower = y_center - 1.96 * uncertainty  # 95% CI lower bound

# Create ColumnDataSource
source = ColumnDataSource(data={"x": x, "y_center": y_center, "y_upper": y_upper, "y_lower": y_lower})

# Create figure (4800 x 2700 px)
p = figure(
    width=4800,
    height=2700,
    title="band-basic \u00b7 bokeh \u00b7 pyplots.ai",
    x_axis_label="Time (s)",
    y_axis_label="Value",
    toolbar_location=None,
)

# Plot band using varea (idiomatic Bokeh band glyph)
p.varea(
    x="x",
    y1="y_lower",
    y2="y_upper",
    source=source,
    fill_color="#306998",
    fill_alpha=0.3,
    legend_label="95% Confidence Interval",
)

# Plot center line
p.line(x="x", y="y_center", source=source, line_color="#FFD43B", line_width=6, legend_label="Mean Trend")

# Styling for 4800x2700 px — Bokeh pt renders at CSS scale, need large values
p.title.text_font_size = "96pt"
p.title.text_font_style = "normal"
p.xaxis.axis_label_text_font_size = "72pt"
p.yaxis.axis_label_text_font_size = "72pt"
p.xaxis.major_label_text_font_size = "56pt"
p.yaxis.major_label_text_font_size = "56pt"

# Remove top and right spines
p.outline_line_color = None
p.xaxis.axis_line_color = "#333333"
p.yaxis.axis_line_color = "#333333"

# Grid styling - subtle solid lines
p.xgrid.grid_line_alpha = 0.15
p.ygrid.grid_line_alpha = 0.15
p.xgrid.grid_line_dash = "solid"
p.ygrid.grid_line_dash = "solid"

# Remove tick marks, keep labels
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Legend styling
p.legend.label_text_font_size = "56pt"
p.legend.location = "top_left"
p.legend.background_fill_alpha = 0.7
p.legend.border_line_color = None
p.legend.glyph_width = 60
p.legend.glyph_height = 40
p.legend.padding = 20
p.legend.spacing = 12

# Save as PNG and HTML
export_png(p, filename="plot.png")
save(p, filename="plot.html", title="band-basic \u00b7 bokeh \u00b7 pyplots.ai")
