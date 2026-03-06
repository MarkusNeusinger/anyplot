"""pyplots.ai
heatmap-stripes-climate: Climate Warming Stripes
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-06
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import LinearColorMapper, Range1d
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

# Smooth 256-color blue-white-red palette for gradient without banding
blues = [
    (8, 48, 107),
    (8, 81, 156),
    (33, 113, 181),
    (66, 146, 198),
    (107, 174, 214),
    (158, 202, 225),
    (198, 219, 239),
    (222, 235, 247),
]
reds = [
    (255, 245, 240),
    (254, 224, 210),
    (252, 187, 161),
    (252, 146, 114),
    (251, 106, 74),
    (239, 59, 44),
    (203, 24, 29),
    (153, 0, 13),
]

n_half = 128
palette = []
for i in range(n_half):
    t = i / (n_half - 1)
    idx = t * (len(blues) - 1)
    lo = int(idx)
    hi = min(lo + 1, len(blues) - 1)
    frac = idx - lo
    r = int(blues[lo][0] + frac * (blues[hi][0] - blues[lo][0]))
    g = int(blues[lo][1] + frac * (blues[hi][1] - blues[lo][1]))
    b = int(blues[lo][2] + frac * (blues[hi][2] - blues[lo][2]))
    palette.append(f"#{r:02x}{g:02x}{b:02x}")
for i in range(n_half):
    t = i / (n_half - 1)
    idx = t * (len(reds) - 1)
    lo = int(idx)
    hi = min(lo + 1, len(reds) - 1)
    frac = idx - lo
    r = int(reds[lo][0] + frac * (reds[hi][0] - reds[lo][0]))
    g = int(reds[lo][1] + frac * (reds[hi][1] - reds[lo][1]))
    b = int(reds[lo][2] + frac * (reds[hi][2] - reds[lo][2]))
    palette.append(f"#{r:02x}{g:02x}{b:02x}")

color_mapper = LinearColorMapper(palette=palette, low=-vmax, high=vmax)

# Reshape anomalies as 2D image (1 row x n_years columns) for seamless rendering
img_data = anomalies.reshape(1, -1)

# Plot - landscape format 4800x2700 (allowed canvas size)
p = figure(
    width=4800,
    height=2700,
    title="heatmap-stripes-climate · bokeh · pyplots.ai",
    tools="",
    toolbar_location=None,
    x_range=Range1d(years[0], years[-1] + 1),
    y_range=Range1d(0, 1),
)

p.image(image=[img_data], x=years[0], y=0, dw=n_years, dh=1, color_mapper=color_mapper)

# Style - minimalist: no axes, no labels, no gridlines, no ticks
p.title.text_font_size = "42pt"
p.title.text_font_style = "normal"
p.title.align = "center"
p.title.text_color = "#333333"

p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
p.outline_line_color = None
p.background_fill_color = "#FFFFFF"
p.border_fill_color = "#FFFFFF"
p.min_border_left = 0
p.min_border_right = 0
p.min_border_top = 80
p.min_border_bottom = 0

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=Resources(mode="cdn"), title="Climate Warming Stripes")
