""" pyplots.ai
bifurcation-basic: Bifurcation Diagram for Dynamical Systems
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-20
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Range1d, Span
from bokeh.plotting import figure
from bokeh.resources import Resources


# Data - Logistic map: x(n+1) = r * x(n) * (1 - x(n))
r_min, r_max = 2.5, 4.0
n_r = 2000
n_transient = 200
n_keep = 100

r_values = np.linspace(r_min, r_max, n_r)
all_r = np.repeat(r_values, n_keep)
all_x = np.empty_like(all_r)

idx = 0
for r in r_values:
    x = 0.5
    for _ in range(n_transient):
        x = r * x * (1.0 - x)
    for _ in range(n_keep):
        x = r * x * (1.0 - x)
        all_x[idx] = x
        idx += 1

source = ColumnDataSource(data={"r": all_r, "x": all_x})

# Plot
p = figure(
    width=4800,
    height=2700,
    title="bifurcation-basic · bokeh · pyplots.ai",
    x_axis_label="Growth Rate (r)",
    y_axis_label="Steady-State Population (x)",
    x_range=Range1d(r_min - 0.02, r_max + 0.02),
    y_range=Range1d(-0.05, 1.05),
    tools="pan,wheel_zoom,box_zoom,reset,save",
    active_scroll="wheel_zoom",
)

scatter = p.scatter(x="r", y="x", source=source, size=1, color="#306998", alpha=0.12, line_color=None)

# HoverTool - Bokeh-distinctive interactive feature
hover = HoverTool(
    renderers=[scatter], tooltips=[("r", "@r{0.000}"), ("x", "@x{0.0000}")], point_policy="snap_to_data", mode="mouse"
)
p.add_tools(hover)

# Vertical spans at key bifurcation points for visual storytelling
bif_spans = [(3.0, "Period-2"), (3.449, "Period-8"), (3.5699, "Chaos onset")]
for r_bif, _ in bif_spans:
    span = Span(
        location=r_bif, dimension="height", line_color="#AA3939", line_width=2, line_alpha=0.25, line_dash="dashed"
    )
    p.add_layout(span)

# Key bifurcation point annotations - spread apart for readability
annotations = [(3.0, 0.68, "r ≈ 3.0\nPeriod-2"), (3.449, 0.92, "r ≈ 3.449"), (3.5699, 0.05, "r ≈ 3.57\nOnset of chaos")]

for r_bif, y_pos, label_text in annotations:
    label = Label(
        x=r_bif,
        y=y_pos,
        text=label_text,
        text_font_size="36pt",
        text_font_style="bold",
        text_color="#AA3939",
        text_alpha=0.85,
        text_align="center",
        x_offset=5,
    )
    p.add_layout(label)

# Style - typography and colors
p.title.text_font_size = "72pt"
p.title.text_color = "#2B2B2B"
p.title.text_font = "Helvetica"

p.xaxis.axis_label_text_font_size = "48pt"
p.yaxis.axis_label_text_font_size = "48pt"
p.xaxis.axis_label_text_font = "Helvetica"
p.yaxis.axis_label_text_font = "Helvetica"
p.xaxis.major_label_text_font_size = "36pt"
p.yaxis.major_label_text_font_size = "36pt"
p.xaxis.axis_label_text_color = "#3A3A3A"
p.yaxis.axis_label_text_color = "#3A3A3A"
p.xaxis.major_label_text_color = "#555555"
p.yaxis.major_label_text_color = "#555555"

p.xaxis.axis_line_color = None
p.yaxis.axis_line_color = None
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.grid.grid_line_alpha = 0.12
p.grid.grid_line_width = 2
p.grid.grid_line_color = "#999999"

p.background_fill_color = "#FAFAFA"
p.border_fill_color = "white"
p.outline_line_color = None

p.xaxis.ticker.desired_num_ticks = 12
p.yaxis.ticker.desired_num_ticks = 8

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=Resources(mode="cdn"), title="Bifurcation Diagram")
