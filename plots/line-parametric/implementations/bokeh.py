""" pyplots.ai
line-parametric: Parametric Curve Plot
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 83/100 | Created: 2026-03-20
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.layouts import gridplot
from bokeh.models import ColumnDataSource, Range1d, Title
from bokeh.plotting import figure


# Data
n_points = 1000
t_lissajous = np.linspace(0, 2 * np.pi, n_points)
x_lissajous = np.sin(3 * t_lissajous)
y_lissajous = np.sin(2 * t_lissajous)

t_spiral = np.linspace(0, 4 * np.pi, n_points)
x_spiral = t_spiral * np.cos(t_spiral)
y_spiral = t_spiral * np.sin(t_spiral)

# Color palette for gradient (cool to warm: blue -> teal -> amber)
n_colors = 256
r_start, g_start, b_start = 0x30, 0x69, 0x98
r_mid, g_mid, b_mid = 0x2A, 0xA1, 0x98
r_end, g_end, b_end = 0xE8, 0x8D, 0x2A

palette = []
for i in range(n_colors):
    frac = i / (n_colors - 1)
    if frac < 0.5:
        f = frac * 2
        r = int(r_start + (r_mid - r_start) * f)
        g = int(g_start + (g_mid - g_start) * f)
        b = int(b_start + (b_mid - b_start) * f)
    else:
        f = (frac - 0.5) * 2
        r = int(r_mid + (r_end - r_mid) * f)
        g = int(g_mid + (g_end - g_mid) * f)
        b = int(b_mid + (b_end - b_mid) * f)
    palette.append(f"#{r:02x}{g:02x}{b:02x}")

# Segment data for color-mapped lines
xs_liss = [[x_lissajous[i], x_lissajous[i + 1]] for i in range(n_points - 1)]
ys_liss = [[y_lissajous[i], y_lissajous[i + 1]] for i in range(n_points - 1)]
colors_liss = [palette[int(i / (n_points - 2) * (n_colors - 1))] for i in range(n_points - 1)]

xs_spiral = [[x_spiral[i], x_spiral[i + 1]] for i in range(n_points - 1)]
ys_spiral = [[y_spiral[i], y_spiral[i + 1]] for i in range(n_points - 1)]
colors_spiral = [palette[int(i / (n_points - 2) * (n_colors - 1))] for i in range(n_points - 1)]

seg_source_liss = ColumnDataSource(data={"xs": xs_liss, "ys": ys_liss, "color": colors_liss})
seg_source_spiral = ColumnDataSource(data={"xs": xs_spiral, "ys": ys_spiral, "color": colors_spiral})

# Lissajous figure
p1 = figure(
    width=2400,
    height=2500,
    title="Lissajous: x = sin(3t), y = sin(2t)",
    x_axis_label="x(t)",
    y_axis_label="y(t)",
    match_aspect=True,
)

p1.multi_line(xs="xs", ys="ys", source=seg_source_liss, line_color="color", line_width=6)

p1.scatter(
    x=[x_lissajous[0]],
    y=[y_lissajous[0]],
    size=30,
    fill_color=palette[0],
    line_color="white",
    line_width=4,
    legend_label="Start (t = 0)",
)
p1.scatter(
    x=[x_lissajous[-1]],
    y=[y_lissajous[-1]],
    size=30,
    marker="square",
    fill_color=palette[-1],
    line_color="white",
    line_width=4,
    legend_label="End (t = 2\u03c0)",
)

# Spiral curve with padding to avoid clipping
spiral_margin = 1.5
p2 = figure(
    width=2400,
    height=2500,
    title="Spiral: x = t\u00b7cos(t), y = t\u00b7sin(t)",
    x_axis_label="x(t)",
    y_axis_label="y(t)",
    x_range=Range1d(x_spiral.min() - spiral_margin, x_spiral.max() + spiral_margin),
    y_range=Range1d(y_spiral.min() - spiral_margin, y_spiral.max() + spiral_margin),
    match_aspect=True,
)

p2.multi_line(xs="xs", ys="ys", source=seg_source_spiral, line_color="color", line_width=6)

p2.scatter(
    x=[x_spiral[0]],
    y=[y_spiral[0]],
    size=30,
    fill_color=palette[0],
    line_color="white",
    line_width=4,
    legend_label="Start (t = 0)",
)
p2.scatter(
    x=[x_spiral[-1]],
    y=[y_spiral[-1]],
    size=30,
    marker="square",
    fill_color=palette[-1],
    line_color="white",
    line_width=4,
    legend_label="End (t = 4\u03c0)",
)

# Style both figures
for p in [p1, p2]:
    p.title.text_font_size = "34pt"
    p.title.text_font_style = "normal"
    p.title.text_color = "#444444"
    p.xaxis.axis_label_text_font_size = "26pt"
    p.yaxis.axis_label_text_font_size = "26pt"
    p.xaxis.major_label_text_font_size = "20pt"
    p.yaxis.major_label_text_font_size = "20pt"

    p.background_fill_color = "#fafafa"
    p.border_fill_color = "white"

    p.xgrid.grid_line_alpha = 0.2
    p.ygrid.grid_line_alpha = 0.2

    p.axis.axis_line_width = 2
    p.axis.axis_line_color = "#333333"

    p.toolbar_location = None

    p.legend.label_text_font_size = "22pt"
    p.legend.background_fill_alpha = 0.85
    p.legend.border_line_alpha = 0
    p.legend.location = "top_right"
    p.legend.glyph_width = 40
    p.legend.glyph_height = 40
    p.legend.padding = 15
    p.legend.spacing = 10

# Main title above p1
p1.add_layout(
    Title(
        text="line-parametric \u00b7 bokeh \u00b7 pyplots.ai",
        text_font_size="42pt",
        text_font_style="bold",
        text_color="#222222",
    ),
    "above",
)

# Layout
layout = gridplot([[p1, p2]], merge_tools=False)

# Save
export_png(layout, filename="plot.png")

output_file("plot.html")
save(layout)
