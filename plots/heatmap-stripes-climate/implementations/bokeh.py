"""pyplots.ai
heatmap-stripes-climate: Climate Warming Stripes
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-03-06
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import LinearColorMapper, Range1d
from bokeh.palettes import RdBu11
from bokeh.plotting import figure, save
from bokeh.resources import Resources


# Data - Synthetic global temperature anomalies (1850-2024) relative to 1961-1990 baseline
np.random.seed(42)
years = np.arange(1850, 2025)
n_years = len(years)

base_trend = np.concatenate(
    [
        np.linspace(-0.3, -0.2, 60),
        np.linspace(-0.2, -0.1, 40),
        np.linspace(-0.1, 0.0, 25),
        np.linspace(0.0, 0.4, 25),
        np.linspace(0.4, 1.2, 25),
    ]
)
noise = np.random.normal(0, 0.1, n_years)
anomalies = base_trend + noise

# Symmetric color range centered at 0
vmax = max(abs(anomalies.min()), abs(anomalies.max()))
vmax = np.ceil(vmax * 10) / 10

# Color mapper - RdBu11 goes blue-to-red: low (cold) maps to blue, high (warm) to red
color_mapper = LinearColorMapper(palette=list(RdBu11), low=-vmax, high=vmax)

# Reshape anomalies as 2D image (1 row x n_years columns) for seamless rendering
img_data = anomalies.reshape(1, -1)

# Plot - wide and short (approximately 3:1 aspect ratio)
p = figure(
    width=4800,
    height=1600,
    title="heatmap-stripes-climate · bokeh · pyplots.ai",
    tools="",
    toolbar_location=None,
    x_range=Range1d(years[0], years[-1] + 1),
    y_range=Range1d(0, 1),
)

p.image(image=[img_data], x=years[0], y=0, dw=n_years, dh=1, color_mapper=color_mapper)

# Style - minimalist: no axes, no labels, no gridlines, no ticks
p.title.text_font_size = "28pt"
p.title.text_font_style = "normal"
p.title.align = "center"

p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
p.outline_line_color = None
p.background_fill_color = "#FFFFFF"
p.border_fill_color = "#FFFFFF"
p.min_border_left = 0
p.min_border_right = 0
p.min_border_top = 40
p.min_border_bottom = 0

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=Resources(mode="cdn"), title="Climate Warming Stripes")
