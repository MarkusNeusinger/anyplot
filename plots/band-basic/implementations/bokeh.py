""" pyplots.ai
band-basic: Basic Band Plot
Library: bokeh 3.8.2 | Python 3.14
Quality: 93/100 | Updated: 2026-02-23
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


# Data - Solar irradiance forecast with 95% confidence interval
np.random.seed(42)
hours = np.linspace(6, 20, 120)  # 6 AM to 8 PM

# Solar irradiance follows a bell curve peaking around solar noon (1 PM)
peak_hour = 13.0
irradiance = 850 * np.exp(-0.5 * ((hours - peak_hour) / 2.8) ** 2) + 50

# Uncertainty is tight at midday (clear sky, predictable) but grows
# in the afternoon when convective clouds develop — a dramatic shift
base_uncertainty = 15 + 8 * np.abs(hours - peak_hour)
# Sudden uncertainty spike after 3 PM (cloud development)
afternoon_spike = 45 * np.clip((hours - 15) / 2, 0, 1) ** 1.5
uncertainty = base_uncertainty + afternoon_spike

y_upper = irradiance + 1.96 * uncertainty
y_lower = np.maximum(irradiance - 1.96 * uncertainty, 0)  # Irradiance can't be negative

source = ColumnDataSource(data={"hours": hours, "irradiance": irradiance, "y_upper": y_upper, "y_lower": y_lower})

# Create figure (4800 x 2700 px)
p = figure(
    width=4800,
    height=2700,
    title="band-basic · bokeh · pyplots.ai",
    x_axis_label="Hour of Day",
    y_axis_label="Solar Irradiance (W/m²)",
    toolbar_location=None,
    background_fill_color="#FAFBFD",
)

# Plot band using varea (idiomatic Bokeh band glyph)
p.varea(
    x="hours",
    y1="y_lower",
    y2="y_upper",
    source=source,
    fill_color="#306998",
    fill_alpha=0.25,
    legend_label="95% Confidence Interval",
)

# Plot center line — warm amber contrasts the cool blue band
p.line(x="hours", y="irradiance", source=source, line_color="#E8910C", line_width=7, legend_label="Forecast Mean")

# Styling for 4800x2700 px
p.title.text_font_size = "96pt"
p.title.text_font_style = "normal"
p.title.text_color = "#2B2B2B"
p.xaxis.axis_label_text_font_size = "72pt"
p.yaxis.axis_label_text_font_size = "72pt"
p.xaxis.axis_label_text_color = "#444444"
p.yaxis.axis_label_text_color = "#444444"
p.xaxis.major_label_text_font_size = "56pt"
p.yaxis.major_label_text_font_size = "56pt"
p.xaxis.major_label_text_color = "#555555"
p.yaxis.major_label_text_color = "#555555"

# Remove outline, refined axis lines
p.outline_line_color = None
p.xaxis.axis_line_color = "#AAAAAA"
p.yaxis.axis_line_color = "#AAAAAA"
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2

# Grid styling - subtle dashed lines for depth
p.xgrid.grid_line_alpha = 0.12
p.ygrid.grid_line_alpha = 0.12
p.xgrid.grid_line_dash = [6, 4]
p.ygrid.grid_line_dash = [6, 4]
p.xgrid.grid_line_color = "#999999"
p.ygrid.grid_line_color = "#999999"

# Remove tick marks, keep labels
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Legend styling
p.legend.label_text_font_size = "56pt"
p.legend.label_text_color = "#444444"
p.legend.location = "top_right"
p.legend.background_fill_color = "#FAFBFD"
p.legend.background_fill_alpha = 0.85
p.legend.border_line_color = None
p.legend.glyph_width = 60
p.legend.glyph_height = 40
p.legend.padding = 20
p.legend.spacing = 12

# Save as PNG and HTML
export_png(p, filename="plot.png")
save(p, filename="plot.html", title="band-basic · bokeh · pyplots.ai")
