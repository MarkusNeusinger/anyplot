""" pyplots.ai
line-parametric: Parametric Curve Plot
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-20
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.layouts import column, gridplot
from bokeh.models import ColumnDataSource, Div, Label, Range1d
from bokeh.palettes import Turbo256
from bokeh.plotting import figure


# Data
n_points = 1000

# Lissajous: offset start slightly so start and end markers don't overlap
t_lissajous = np.linspace(0.05, 2 * np.pi + 0.05, n_points)
x_lissajous = np.sin(3 * t_lissajous)
y_lissajous = np.sin(2 * t_lissajous)

t_spiral = np.linspace(0, 4 * np.pi, n_points)
x_spiral = t_spiral * np.cos(t_spiral)
y_spiral = t_spiral * np.sin(t_spiral)

# Color palette: subset of Turbo256 from cool blue to warm amber
palette = [Turbo256[i] for i in range(30, 210)]
n_colors = len(palette)


# Helper to build segment data for multi_line color gradient
def build_segments(x, y):
    n = len(x)
    xs = [[x[i], x[i + 1]] for i in range(n - 1)]
    ys = [[y[i], y[i + 1]] for i in range(n - 1)]
    colors = [palette[int(i / (n - 2) * (n_colors - 1))] for i in range(n - 1)]
    return ColumnDataSource(data={"xs": xs, "ys": ys, "color": colors})


seg_source_liss = build_segments(x_lissajous, y_lissajous)
seg_source_spiral = build_segments(x_spiral, y_spiral)

# Lissajous figure
p1 = figure(
    width=2400,
    height=2700,
    title="Lissajous: x = sin(3t), y = sin(2t)",
    x_axis_label="x(t)",
    y_axis_label="y(t)",
    match_aspect=True,
)

p1.multi_line(xs="xs", ys="ys", source=seg_source_liss, line_color="color", line_width=7)

p1.scatter(
    x=[x_lissajous[0]],
    y=[y_lissajous[0]],
    size=32,
    fill_color=palette[0],
    line_color="white",
    line_width=4,
    legend_label="Start (t \u2248 0)",
)
p1.scatter(
    x=[x_lissajous[-1]],
    y=[y_lissajous[-1]],
    size=32,
    marker="square",
    fill_color=palette[-1],
    line_color="white",
    line_width=4,
    legend_label="End (t \u2248 2\u03c0)",
)

# Annotation at midpoint of Lissajous
mid_idx = n_points // 2
p1.add_layout(
    Label(
        x=x_lissajous[mid_idx],
        y=y_lissajous[mid_idx],
        text="t = \u03c0",
        text_font_size="20pt",
        text_color="#666666",
        x_offset=12,
        y_offset=-12,
    )
)

# Spiral curve
spiral_margin = 1.5
p2 = figure(
    width=2400,
    height=2700,
    title="Spiral: x = t\u00b7cos(t), y = t\u00b7sin(t)",
    x_axis_label="x(t)",
    y_axis_label="y(t)",
    x_range=Range1d(x_spiral.min() - spiral_margin, x_spiral.max() + spiral_margin),
    y_range=Range1d(y_spiral.min() - spiral_margin, y_spiral.max() + spiral_margin),
    match_aspect=True,
)

p2.multi_line(xs="xs", ys="ys", source=seg_source_spiral, line_color="color", line_width=7)

p2.scatter(
    x=[x_spiral[0]],
    y=[y_spiral[0]],
    size=32,
    fill_color=palette[0],
    line_color="white",
    line_width=4,
    legend_label="Start (t = 0)",
)
p2.scatter(
    x=[x_spiral[-1]],
    y=[y_spiral[-1]],
    size=32,
    marker="square",
    fill_color=palette[-1],
    line_color="white",
    line_width=4,
    legend_label="End (t = 4\u03c0)",
)

# Annotation at midpoint of spiral
mid_spiral = n_points // 2
p2.add_layout(
    Label(
        x=x_spiral[mid_spiral],
        y=y_spiral[mid_spiral],
        text="t = 2\u03c0",
        text_font_size="20pt",
        text_color="#666666",
        x_offset=12,
        y_offset=-12,
    )
)

# Style both figures
for p in [p1, p2]:
    p.title.text_font_size = "34pt"
    p.title.text_font_style = "italic"
    p.title.text_color = "#444444"
    p.xaxis.axis_label_text_font_size = "26pt"
    p.yaxis.axis_label_text_font_size = "26pt"
    p.xaxis.major_label_text_font_size = "20pt"
    p.yaxis.major_label_text_font_size = "20pt"

    p.background_fill_color = "#f8f9fa"
    p.border_fill_color = "white"

    p.xgrid.grid_line_alpha = 0.15
    p.ygrid.grid_line_alpha = 0.15
    p.xgrid.grid_line_dash = [4, 4]
    p.ygrid.grid_line_dash = [4, 4]

    p.axis.axis_line_width = 2
    p.axis.axis_line_color = "#333333"
    p.axis.minor_tick_line_color = None

    p.toolbar_location = None

    p.legend.label_text_font_size = "22pt"
    p.legend.background_fill_alpha = 0.9
    p.legend.background_fill_color = "white"
    p.legend.border_line_alpha = 0.3
    p.legend.border_line_color = "#cccccc"
    p.legend.location = "top_right"
    p.legend.glyph_width = 40
    p.legend.glyph_height = 40
    p.legend.padding = 15
    p.legend.spacing = 10

# Centered main title as Div above the grid
title_div = Div(
    text=(
        '<div style="text-align: center; font-size: 42pt; font-weight: bold;'
        ' color: #222222; padding: 20px 0 10px 0;">'
        "line-parametric \u00b7 bokeh \u00b7 pyplots.ai</div>"
    ),
    width=4800,
)

# Layout
grid = gridplot([[p1, p2]], merge_tools=False)
layout = column(title_div, grid)

# Save
export_png(layout, filename="plot.png")

output_file("plot.html")
save(layout)
