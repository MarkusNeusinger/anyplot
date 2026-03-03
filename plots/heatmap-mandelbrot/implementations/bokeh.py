"""pyplots.ai
heatmap-mandelbrot: Mandelbrot Set Fractal Visualization
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-03-03
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import BasicTicker, ColorBar, LinearColorMapper
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data — compute Mandelbrot set on the complex plane
x_min, x_max = -2.5, 1.0
y_min, y_max = -1.25, 1.25
width, height = 1200, 714
max_iter = 200

real = np.linspace(x_min, x_max, width)
imag = np.linspace(y_min, y_max, height)
real_grid, imag_grid = np.meshgrid(real, imag)
c = real_grid + 1j * imag_grid

z = np.zeros_like(c, dtype=complex)
iteration_count = np.zeros(c.shape, dtype=float)
escaped = np.zeros(c.shape, dtype=bool)

for i in range(max_iter):
    mask = ~escaped
    z[mask] = z[mask] ** 2 + c[mask]
    newly_escaped = mask & (np.abs(z) > 2.0)
    # Smooth coloring: use log2 of the modulus for fractional escape count
    iteration_count[newly_escaped] = i + 1 - np.log2(np.log2(np.abs(z[newly_escaped])))
    escaped |= newly_escaped

# Points inside the set get NaN so they render as black
iteration_count[~escaped] = np.nan

# Normalize iteration counts for color mapping
valid = ~np.isnan(iteration_count)
low_val = float(np.nanmin(iteration_count[valid])) if np.any(valid) else 0
high_val = float(np.nanmax(iteration_count[valid])) if np.any(valid) else max_iter

# Custom palette — deep blue to cyan to yellow to orange to dark (perceptually rich)
palette = [
    "#000764",
    "#001494",
    "#0025c8",
    "#0638e0",
    "#084cf0",
    "#0860f8",
    "#0878ff",
    "#0890ff",
    "#08a8ff",
    "#08c0ff",
    "#18d8ff",
    "#38e8f0",
    "#60f0d8",
    "#88f8b8",
    "#b0f898",
    "#d0f878",
    "#e8f050",
    "#f8e030",
    "#f8c818",
    "#f8a808",
    "#f08800",
    "#e06800",
    "#c84800",
    "#a83000",
    "#882000",
    "#681800",
    "#481008",
    "#280800",
    "#100400",
]

# Plot
p = figure(
    width=4800,
    height=2700,
    x_range=(x_min, x_max),
    y_range=(y_min, y_max),
    title="heatmap-mandelbrot · bokeh · pyplots.ai",
    x_axis_label="Real Axis",
    y_axis_label="Imaginary Axis",
    toolbar_location=None,
    tools="",
    match_aspect=True,
)

mapper = LinearColorMapper(palette=palette, low=low_val, high=high_val, nan_color="#000000")

p.image(image=[iteration_count], x=x_min, y=y_min, dw=x_max - x_min, dh=y_max - y_min, color_mapper=mapper)

# Color bar
color_bar = ColorBar(
    color_mapper=mapper,
    ticker=BasicTicker(desired_num_ticks=8),
    label_standoff=16,
    width=40,
    title="Escape Iterations",
    title_text_font_size="20pt",
    major_label_text_font_size="18pt",
    title_standoff=20,
    border_line_color=None,
    padding=10,
)
p.add_layout(color_bar, "right")

# Style
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
p.outline_line_color = None
p.background_fill_color = "#000000"
p.border_fill_color = "white"
p.min_border_right = 120

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="heatmap-mandelbrot · bokeh · pyplots.ai")
