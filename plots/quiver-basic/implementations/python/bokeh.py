""" anyplot.ai
quiver-basic: Basic Quiver Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-04-29
"""

import os

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColorBar, ColumnDataSource, Label, LinearColorMapper, Title
from bokeh.palettes import Viridis256
from bokeh.plotting import figure


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data - counterclockwise vortex wind field: u = -y, v = x
grid_size = 15
axis_coords = np.linspace(-2, 2, grid_size)
X, Y = np.meshgrid(axis_coords, axis_coords)
x = X.flatten()
y = Y.flatten()

u = -y.copy()
v = x.copy()

# Magnitude-proportional arrow lengths (length encodes wind speed)
magnitude = np.sqrt(u**2 + v**2)

grid_spacing = 4.0 / (grid_size - 1)
max_mag = np.max(magnitude) if np.max(magnitude) > 0 else 1.0
scale = grid_spacing * 0.65 / max_mag
u_scaled = u * scale
v_scaled = v * scale

# Arrow geometry — enforce minimum displayed length so near-origin arrows stay visible
arrow_lengths = np.sqrt(u_scaled**2 + v_scaled**2)
MIN_DISP = grid_spacing * 0.12
display_lengths = np.maximum(arrow_lengths, MIN_DISP)

# Unit direction vectors (default to pointing up for zero-magnitude vectors)
near_zero = arrow_lengths < 1e-10
safe_lengths = np.where(near_zero, 1.0, arrow_lengths)
dx = np.where(near_zero, 0.0, u_scaled / safe_lengths)
dy = np.where(near_zero, 1.0, v_scaled / safe_lengths)
perp_x = -dy
perp_y = dx

head_len = display_lengths * 0.30
head_wid = display_lengths * 0.35

arrow_x_end = x + dx * display_lengths
arrow_y_end = y + dy * display_lengths
arrow_base_x = arrow_x_end - head_len * dx
arrow_base_y = arrow_y_end - head_len * dy
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
    x_axis_label="East–West Distance (km)",
    y_axis_label="North–South Distance (km)",
    x_range=(-2.5, 2.5),
    y_range=(-2.5, 2.5),
)

# Subtitle
p.add_layout(
    Title(
        text="Counterclockwise vortex wind field — colour encodes wind speed",
        text_font_size="18pt",
        text_color=INK_SOFT,
    ),
    "above",
)

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None  # suppress plot frame box for cleaner look

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
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.15
p.ygrid.grid_line_alpha = 0.15

# Arrow shafts (stop at arrowhead base to avoid shaft poking through head)
segment_source = ColumnDataSource(data={"x0": x, "y0": y, "x1": arrow_base_x, "y1": arrow_base_y, "color": colors})
p.segment(x0="x0", y0="y0", x1="x1", y1="y1", source=segment_source, line_width=4, line_color="color")

# Arrowheads as filled triangles
xs = [[arrow_x_end[i], arrow_x1[i], arrow_x2[i]] for i in range(len(x))]
ys = [[arrow_y_end[i], arrow_y1[i], arrow_y2[i]] for i in range(len(y))]
patch_source = ColumnDataSource(data={"xs": xs, "ys": ys, "color": colors})
p.patches(xs="xs", ys="ys", source=patch_source, fill_color="color", line_color="color")

# Vortex centre marker and annotation
p.scatter([0], [0], marker="circle_dot", size=20, color=INK_MUTED, fill_alpha=0.85, line_color=INK_SOFT)
p.add_layout(
    Label(
        x=0,
        y=0,
        text="vortex centre",
        x_offset=20,
        y_offset=10,
        text_font_size="16pt",
        text_color=INK_MUTED,
        background_fill_color=None,
        border_line_color=None,
    )
)

# ColorBar for wind speed legend
color_mapper = LinearColorMapper(palette=Viridis256, low=0.0, high=float(max_mag))
color_bar = ColorBar(
    color_mapper=color_mapper,
    label_standoff=16,
    location=(0, 0),
    title="Wind Speed",
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
