""" pyplots.ai
line-parametric: Parametric Curve Plot
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-20
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.layouts import column, gridplot
from bokeh.models import BasicTicker, ColorBar, ColumnDataSource, Div, Label, LinearColorMapper, Range1d
from bokeh.palettes import Viridis256
from bokeh.plotting import figure


# Data
n_points = 1000
n_seg = n_points - 1

# Lissajous: offset start slightly so start and end markers don't overlap
t_lissajous = np.linspace(0.05, 2 * np.pi + 0.05, n_points)
x_lissajous = np.sin(3 * t_lissajous)
y_lissajous = np.sin(2 * t_lissajous)

t_spiral = np.linspace(0, 4 * np.pi, n_points)
x_spiral = t_spiral * np.cos(t_spiral)
y_spiral = t_spiral * np.sin(t_spiral)

# Colorblind-safe palette from Viridis256
palette = list(Viridis256)

# Segment data for multi_line color gradient — Lissajous
seg_colors_liss = [palette[int(i / (n_seg - 1) * 255)] for i in range(n_seg)]
seg_source_liss = ColumnDataSource(
    data={
        "xs": [[x_lissajous[i], x_lissajous[i + 1]] for i in range(n_seg)],
        "ys": [[y_lissajous[i], y_lissajous[i + 1]] for i in range(n_seg)],
        "color": seg_colors_liss,
    }
)

# Segment data for multi_line color gradient — Spiral
seg_colors_spiral = [palette[int(i / (n_seg - 1) * 255)] for i in range(n_seg)]
seg_source_spiral = ColumnDataSource(
    data={
        "xs": [[x_spiral[i], x_spiral[i + 1]] for i in range(n_seg)],
        "ys": [[y_spiral[i], y_spiral[i + 1]] for i in range(n_seg)],
        "color": seg_colors_spiral,
    }
)

# Color mapper for the colorbar showing parameter t
liss_mapper = LinearColorMapper(palette=palette, low=0, high=round(2 * np.pi, 2))
spiral_mapper = LinearColorMapper(palette=palette, low=0, high=round(4 * np.pi, 2))

# Lissajous figure
p1 = figure(
    width=2350,
    height=2450,
    title="Lissajous Figure",
    x_axis_label="x(t) = sin(3t)",
    y_axis_label="y(t) = sin(2t)",
    match_aspect=True,
)

p1.multi_line(xs="xs", ys="ys", source=seg_source_liss, line_color="color", line_width=7)

p1.scatter(
    x=[x_lissajous[0]],
    y=[y_lissajous[0]],
    size=34,
    fill_color=palette[0],
    line_color="white",
    line_width=4,
    legend_label="Start (t ≈ 0)",
)
p1.scatter(
    x=[x_lissajous[-1]],
    y=[y_lissajous[-1]],
    size=34,
    marker="square",
    fill_color=palette[-1],
    line_color="white",
    line_width=4,
    legend_label="End (t ≈ 2π)",
)

# Annotation at midpoint
mid_idx = n_points // 2
p1.add_layout(
    Label(
        x=x_lissajous[mid_idx],
        y=y_lissajous[mid_idx],
        text="t = π",
        text_font_size="22pt",
        text_font_style="italic",
        text_color="#555555",
        x_offset=14,
        y_offset=-14,
    )
)

# ColorBar for Lissajous — shows parameter t progression
liss_colorbar = ColorBar(
    color_mapper=liss_mapper,
    ticker=BasicTicker(desired_num_ticks=5),
    title="t (rad)",
    title_text_font_size="20pt",
    title_text_font_style="italic",
    major_label_text_font_size="18pt",
    label_standoff=12,
    width=24,
    padding=20,
    margin=10,
)
p1.add_layout(liss_colorbar, "right")

# Spiral curve
spiral_margin = 1.5
p2 = figure(
    width=2350,
    height=2450,
    title="Archimedean Spiral",
    x_axis_label="x(t) = t·cos(t)",
    y_axis_label="y(t) = t·sin(t)",
    x_range=Range1d(x_spiral.min() - spiral_margin, x_spiral.max() + spiral_margin),
    y_range=Range1d(y_spiral.min() - spiral_margin, y_spiral.max() + spiral_margin),
    match_aspect=True,
)

p2.multi_line(xs="xs", ys="ys", source=seg_source_spiral, line_color="color", line_width=7)

p2.scatter(
    x=[x_spiral[0]],
    y=[y_spiral[0]],
    size=34,
    fill_color=palette[0],
    line_color="white",
    line_width=4,
    legend_label="Start (t = 0)",
)
p2.scatter(
    x=[x_spiral[-1]],
    y=[y_spiral[-1]],
    size=34,
    marker="square",
    fill_color=palette[-1],
    line_color="white",
    line_width=4,
    legend_label="End (t = 4π)",
)

# Annotation at midpoint of spiral
mid_spiral = n_points // 2
p2.add_layout(
    Label(
        x=x_spiral[mid_spiral],
        y=y_spiral[mid_spiral],
        text="t = 2π",
        text_font_size="22pt",
        text_font_style="italic",
        text_color="#555555",
        x_offset=14,
        y_offset=-14,
    )
)

# ColorBar for spiral — shows parameter t progression
spiral_colorbar = ColorBar(
    color_mapper=spiral_mapper,
    ticker=BasicTicker(desired_num_ticks=5),
    title="t (rad)",
    title_text_font_size="20pt",
    title_text_font_style="italic",
    major_label_text_font_size="18pt",
    label_standoff=12,
    width=24,
    padding=20,
    margin=10,
)
p2.add_layout(spiral_colorbar, "right")

# Style both figures
for p in [p1, p2]:
    p.title.text_font_size = "34pt"
    p.title.text_font_style = "bold italic"
    p.title.text_color = "#2c3e50"
    p.xaxis.axis_label_text_font_size = "26pt"
    p.yaxis.axis_label_text_font_size = "26pt"
    p.xaxis.axis_label_text_font_style = "italic"
    p.yaxis.axis_label_text_font_style = "italic"
    p.xaxis.axis_label_text_color = "#34495e"
    p.yaxis.axis_label_text_color = "#34495e"
    p.xaxis.major_label_text_font_size = "20pt"
    p.yaxis.major_label_text_font_size = "20pt"
    p.xaxis.major_label_text_color = "#555555"
    p.yaxis.major_label_text_color = "#555555"

    p.background_fill_color = "#fafbfc"
    p.border_fill_color = "white"

    p.xgrid.grid_line_alpha = 0.12
    p.ygrid.grid_line_alpha = 0.12
    p.xgrid.grid_line_dash = [4, 4]
    p.ygrid.grid_line_dash = [4, 4]
    p.xgrid.grid_line_color = "#888888"
    p.ygrid.grid_line_color = "#888888"

    p.axis.axis_line_width = 2
    p.axis.axis_line_color = "#2c3e50"
    p.axis.minor_tick_line_color = None
    p.axis.major_tick_line_color = "#888888"
    p.axis.major_tick_line_width = 1

    p.outline_line_color = "#dce1e6"
    p.outline_line_width = 2

    p.toolbar_location = None

    p.legend.label_text_font_size = "22pt"
    p.legend.label_text_color = "#2c3e50"
    p.legend.background_fill_alpha = 0.92
    p.legend.background_fill_color = "white"
    p.legend.border_line_alpha = 0.25
    p.legend.border_line_color = "#bdc3c7"
    p.legend.location = "top_right"
    p.legend.glyph_width = 40
    p.legend.glyph_height = 40
    p.legend.padding = 16
    p.legend.spacing = 10

# Centered main title as styled HTML Div
title_div = Div(
    text=(
        '<div style="text-align: center; font-family: Georgia, serif;'
        " font-size: 44pt; font-weight: bold;"
        " color: #2c3e50; padding: 24px 0 6px 0;"
        ' letter-spacing: 1px;">'
        "line-parametric · bokeh · pyplots.ai</div>"
        '<div style="text-align: center; font-family: Georgia, serif;'
        " font-size: 22pt; color: #7f8c8d;"
        ' font-style: italic; padding: 0 0 12px 0;">'
        "Parametric curves colored by parameter t (Viridis palette)</div>"
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
