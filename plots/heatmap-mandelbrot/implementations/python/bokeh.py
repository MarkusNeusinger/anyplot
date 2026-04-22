""" pyplots.ai
heatmap-mandelbrot: Mandelbrot Set Fractal Visualization
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-03
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import BasicTicker, ColorBar, LogColorMapper, NumeralTickFormatter
from bokeh.palettes import Inferno256
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

# Plot
p = figure(
    width=4800,
    height=2700,
    x_range=(x_min, x_max),
    y_range=(y_min, y_max),
    title="heatmap-mandelbrot · bokeh · pyplots.ai",
    x_axis_label="Re(c)",
    y_axis_label="Im(c)",
    toolbar_location=None,
    tools="",
    match_aspect=True,
)

# LogColorMapper emphasizes boundary detail where iteration counts change rapidly
mapper = LogColorMapper(palette=Inferno256, low=max(low_val, 1.0), high=high_val, nan_color="#000000")

p.image(image=[iteration_count], x=x_min, y=y_min, dw=x_max - x_min, dh=y_max - y_min, color_mapper=mapper)

# Color bar
color_bar = ColorBar(
    color_mapper=mapper,
    ticker=BasicTicker(desired_num_ticks=8),
    formatter=NumeralTickFormatter(format="0"),
    label_standoff=20,
    width=45,
    title="Escape Iterations",
    title_text_font_size="20pt",
    title_text_color="#cccccc",
    major_label_text_font_size="18pt",
    major_label_text_color="#cccccc",
    title_standoff=24,
    border_line_color=None,
    padding=16,
    bar_line_color="#333333",
)
p.add_layout(color_bar, "right")

# Style — dark theme with cohesive color scheme
p.title.text_font_size = "28pt"
p.title.text_color = "#e0e0e0"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.axis_label_text_color = "#cccccc"
p.yaxis.axis_label_text_color = "#cccccc"
p.xaxis.major_label_text_color = "#aaaaaa"
p.yaxis.major_label_text_color = "#aaaaaa"
p.xaxis.axis_line_color = "#555555"
p.yaxis.axis_line_color = "#555555"
p.xaxis.major_tick_line_color = "#555555"
p.yaxis.major_tick_line_color = "#555555"
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
p.outline_line_color = None
p.background_fill_color = "#000000"
p.border_fill_color = "#1a1a1a"
p.min_border_right = 140
p.min_border_left = 100
p.min_border_bottom = 80

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="heatmap-mandelbrot · bokeh · pyplots.ai")
