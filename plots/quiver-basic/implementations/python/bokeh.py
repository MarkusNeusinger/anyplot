""" anyplot.ai
quiver-basic: Basic Quiver Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-04-29
"""

import os

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColorBar, ColumnDataSource, LinearColorMapper
from bokeh.palettes import Viridis256
from bokeh.plotting import figure


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - circular rotation flow field: u = -y, v = x
grid_size = 15
axis_coords = np.linspace(-2, 2, grid_size)
X, Y = np.meshgrid(axis_coords, axis_coords)
x = X.flatten()
y = Y.flatten()

u = -y.copy()
v = x.copy()

# Magnitude-proportional arrow lengths (length encodes magnitude)
magnitude = np.sqrt(u**2 + v**2)

# Scale so the longest arrow spans ~65% of the grid spacing
grid_spacing = 4.0 / (grid_size - 1)
max_mag = np.max(magnitude) if np.max(magnitude) > 0 else 1.0
scale = grid_spacing * 0.65 / max_mag
u_scaled = u * scale
v_scaled = v * scale

x_end = x + u_scaled
y_end = y + v_scaled

# Arrowhead geometry (size proportional to arrow length)
arrow_lengths = np.sqrt(u_scaled**2 + v_scaled**2)
arrow_lengths = np.where(arrow_lengths < 1e-10, 1e-10, arrow_lengths)

dx = u_scaled / arrow_lengths
dy = v_scaled / arrow_lengths
perp_x = -dy
perp_y = dx

head_len = arrow_lengths * 0.30
head_wid = arrow_lengths * 0.35

arrow_base_x = x_end - head_len * dx
arrow_base_y = y_end - head_len * dy
arrow_x1 = arrow_base_x + head_wid * perp_x
arrow_y1 = arrow_base_y + head_wid * perp_y
arrow_x2 = arrow_base_x - head_wid * perp_x
arrow_y2 = arrow_base_y - head_wid * perp_y

# Color by magnitude using viridis (continuous colormap per style guide)
mag_norm = magnitude / max_mag
color_indices = (mag_norm * 255).astype(int).clip(0, 255)
colors = [Viridis256[i] for i in color_indices]

# Plot
p = figure(
    width=4800,
    height=2700,
    title="quiver-basic · bokeh · anyplot.ai",
    x_axis_label="X Coordinate",
    y_axis_label="Y Coordinate",
    x_range=(-2.5, 2.5),
    y_range=(-2.5, 2.5),
)

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title.text_color = INK
p.title.text_font_size = "28pt"
p.title.text_font_style = "normal"

p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.15
p.ygrid.grid_line_alpha = 0.15

# Arrow shafts (stop at arrowhead base to avoid shaft poking through head)
segment_source = ColumnDataSource(data={"x0": x, "y0": y, "x1": arrow_base_x, "y1": arrow_base_y, "color": colors})
p.segment(x0="x0", y0="y0", x1="x1", y1="y1", source=segment_source, line_width=4, line_color="color")

# Arrowheads as filled triangles
xs = [[x_end[i], arrow_x1[i], arrow_x2[i]] for i in range(len(x))]
ys = [[y_end[i], arrow_y1[i], arrow_y2[i]] for i in range(len(y))]
patch_source = ColumnDataSource(data={"xs": xs, "ys": ys, "color": colors})
p.patches(xs="xs", ys="ys", source=patch_source, fill_color="color", line_color="color")

# ColorBar for magnitude legend
color_mapper = LinearColorMapper(palette=Viridis256, low=0.0, high=float(max_mag))
color_bar = ColorBar(
    color_mapper=color_mapper,
    label_standoff=16,
    location=(0, 0),
    title="Magnitude",
    major_label_text_color=INK_SOFT,
    major_label_text_font_size="16pt",
    background_fill_color=ELEVATED_BG,
    border_line_color=INK_SOFT,
)
p.add_layout(color_bar, "right")

# Save
export_png(p, filename=f"plot-{THEME}.png")
output_file(f"plot-{THEME}.html", title="quiver-basic · bokeh · anyplot.ai")
save(p)
