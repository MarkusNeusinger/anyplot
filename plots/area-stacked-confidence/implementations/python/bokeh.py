""" pyplots.ai
area-stacked-confidence: Stacked Area Chart with Confidence Bands
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, output_file, save
from bokeh.models import Band, ColumnDataSource, Legend
from bokeh.plotting import figure


# Data - Quarterly energy consumption by source with uncertainty
np.random.seed(42)
quarters = pd.date_range("2020-01-01", periods=24, freq="QE")
n = len(quarters)

# Generate energy consumption data (GWh) with uncertainty
# Solar - growing trend with increasing uncertainty
solar_base = 50 + np.linspace(0, 80, n) + np.random.normal(0, 5, n)
solar_lower = solar_base - (5 + np.linspace(0, 15, n))
solar_upper = solar_base + (5 + np.linspace(0, 15, n))

# Wind - seasonal variation with moderate uncertainty
wind_base = 80 + 20 * np.sin(np.linspace(0, 6 * np.pi, n)) + np.random.normal(0, 3, n)
wind_lower = wind_base - 10
wind_upper = wind_base + 10

# Hydro - stable with low uncertainty
hydro_base = 60 + np.random.normal(0, 2, n)
hydro_lower = hydro_base - 5
hydro_upper = hydro_base + 5

# Stack the values for cumulative display
# First series (Solar) starts at 0
stack1_base = solar_base
stack1_lower = solar_lower
stack1_upper = solar_upper

# Second series (Wind) stacks on top of Solar
stack2_base = stack1_base + wind_base
stack2_lower = stack1_base + wind_lower
stack2_upper = stack1_base + wind_upper

# Third series (Hydro) stacks on top of Wind
stack3_base = stack2_base + hydro_base
stack3_lower = stack2_base + hydro_lower
stack3_upper = stack2_base + hydro_upper

# Create figure with larger dimensions to accommodate legend
p = figure(
    width=4800,
    height=2700,
    title="area-stacked-confidence · bokeh · pyplots.ai",
    x_axis_label="Quarter",
    y_axis_label="Energy Consumption (GWh)",
    x_axis_type="datetime",
)

# Colors - Python Blue, Python Yellow, and Green
colors = ["#306998", "#FFD43B", "#4DAF4A"]
band_alpha = 0.3

# Create data sources for each stacked area with bands
source_hydro = ColumnDataSource(
    data={"x": quarters, "y": stack3_base, "y_lower": stack3_lower, "y_upper": stack3_upper, "base": stack2_base}
)

source_wind = ColumnDataSource(
    data={"x": quarters, "y": stack2_base, "y_lower": stack2_lower, "y_upper": stack2_upper, "base": stack1_base}
)

source_solar = ColumnDataSource(
    data={"x": quarters, "y": stack1_base, "y_lower": stack1_lower, "y_upper": stack1_upper, "base": np.zeros(n)}
)

# Plot confidence bands (back to front for proper layering)
hydro_band = Band(
    base="x",
    lower="y_lower",
    upper="y_upper",
    source=source_hydro,
    fill_alpha=band_alpha,
    fill_color=colors[2],
    line_color=colors[2],
    line_alpha=0.5,
)
p.add_layout(hydro_band)

wind_band = Band(
    base="x",
    lower="y_lower",
    upper="y_upper",
    source=source_wind,
    fill_alpha=band_alpha,
    fill_color=colors[1],
    line_color=colors[1],
    line_alpha=0.5,
)
p.add_layout(wind_band)

solar_band = Band(
    base="x",
    lower="y_lower",
    upper="y_upper",
    source=source_solar,
    fill_alpha=band_alpha,
    fill_color=colors[0],
    line_color=colors[0],
    line_alpha=0.5,
)
p.add_layout(solar_band)

# Plot stacked areas using varea
r_hydro = p.varea(x="x", y1="base", y2="y", source=source_hydro, fill_color=colors[2], fill_alpha=0.7)
r_wind = p.varea(x="x", y1="base", y2="y", source=source_wind, fill_color=colors[1], fill_alpha=0.7)
r_solar = p.varea(x="x", y1="base", y2="y", source=source_solar, fill_color=colors[0], fill_alpha=0.7)

# Add center lines for each series for better visibility
p.line(x="x", y="y", source=source_hydro, line_color=colors[2], line_width=4, line_alpha=0.9)
p.line(x="x", y="y", source=source_wind, line_color=colors[1], line_width=4, line_alpha=0.9)
p.line(x="x", y="y", source=source_solar, line_color=colors[0], line_width=4, line_alpha=0.9)

# Create legend inside plot area
legend = Legend(
    items=[
        ("Hydro (± uncertainty)", [r_hydro]),
        ("Wind (± uncertainty)", [r_wind]),
        ("Solar (± uncertainty)", [r_solar]),
    ],
    location="top_left",
)
legend.click_policy = "hide"
p.add_layout(legend)
p.legend.location = "top_left"
p.legend.background_fill_alpha = 0.8

# Style settings for large canvas (4800x2700)
p.title.text_font_size = "36pt"
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"
p.legend.label_text_font_size = "24pt"
p.legend.glyph_height = 40
p.legend.glyph_width = 40
p.legend.spacing = 15
p.legend.padding = 20

# Grid styling - subtle dashed lines
p.xgrid.grid_line_color = "gray"
p.xgrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_color = "gray"
p.ygrid.grid_line_alpha = 0.3
p.ygrid.grid_line_dash = "dashed"

# Axis styling
p.axis.axis_line_width = 2
p.axis.major_tick_line_width = 2
p.axis.minor_tick_line_width = 1

# Set y-axis to start at 0
p.y_range.start = 0

# Add some padding
p.min_border_left = 100
p.min_border_right = 50
p.min_border_top = 50
p.min_border_bottom = 80

# Save output
export_png(p, filename="plot.png")
output_file("plot.html", title="area-stacked-confidence · bokeh · pyplots.ai")
save(p)
