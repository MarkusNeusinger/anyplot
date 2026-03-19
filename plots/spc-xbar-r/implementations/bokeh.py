""" pyplots.ai
spc-xbar-r: Statistical Process Control Chart (X-bar/R)
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-19
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Label, Span
from bokeh.plotting import figure


# Data - CNC shaft diameter measurements (subgroups of 5)
np.random.seed(42)
n_samples = 30
subgroup_size = 5
target_diameter = 25.0  # mm

# Generate measurement data with a few out-of-control points
measurements = np.random.normal(target_diameter, 0.05, (n_samples, subgroup_size))

# Inject process shifts for out-of-control signals
measurements[8] += 0.15  # Shift up at sample 9
measurements[17] -= 0.18  # Shift down at sample 18
measurements[24] += 0.20  # Shift up at sample 25

sample_ids = np.arange(1, n_samples + 1)
sample_means = measurements.mean(axis=1)
sample_ranges = measurements.max(axis=1) - measurements.min(axis=1)

# Control chart constants for n=5
A2 = 0.577
D3 = 0.0
D4 = 2.114

# X-bar chart limits
x_bar_bar = sample_means.mean()
r_bar = sample_ranges.mean()
ucl_xbar = x_bar_bar + A2 * r_bar
lcl_xbar = x_bar_bar - A2 * r_bar
uwl_xbar = x_bar_bar + (2 / 3) * A2 * r_bar  # Warning at ±2 sigma
lwl_xbar = x_bar_bar - (2 / 3) * A2 * r_bar

# R chart limits
ucl_r = D4 * r_bar
lcl_r = D3 * r_bar
uwl_r = r_bar + (2 / 3) * (ucl_r - r_bar)
lwl_r = max(0, r_bar - (2 / 3) * (r_bar - lcl_r))

# Identify out-of-control points
ooc_xbar = (sample_means > ucl_xbar) | (sample_means < lcl_xbar)
ooc_r = (sample_ranges > ucl_r) | (sample_ranges < lcl_r)

# Sources for X-bar chart
source_xbar_ok = ColumnDataSource(data={"x": sample_ids[~ooc_xbar], "y": sample_means[~ooc_xbar]})
source_xbar_ooc = ColumnDataSource(data={"x": sample_ids[ooc_xbar], "y": sample_means[ooc_xbar]})
source_xbar_line = ColumnDataSource(data={"x": sample_ids, "y": sample_means})

# Sources for R chart
source_r_ok = ColumnDataSource(data={"x": sample_ids[~ooc_r], "y": sample_ranges[~ooc_r]})
source_r_ooc = ColumnDataSource(data={"x": sample_ids[ooc_r], "y": sample_ranges[ooc_r]})
source_r_line = ColumnDataSource(data={"x": sample_ids, "y": sample_ranges})

# X-bar chart (top)
p_xbar = figure(
    width=4800,
    height=1350,
    title="spc-xbar-r · bokeh · pyplots.ai",
    x_axis_label=None,
    y_axis_label="X̄ (Sample Mean, mm)",
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

# Data line and points
p_xbar.line("x", "y", source=source_xbar_line, line_width=2, line_color="#306998", line_alpha=0.6)
p_xbar.scatter("x", "y", source=source_xbar_ok, size=12, color="#306998", alpha=0.9)
p_xbar.scatter(
    "x", "y", source=source_xbar_ooc, size=18, color="#E74C3C", marker="diamond", line_color="white", line_width=2
)

# Control limits
ucl_span = Span(location=ucl_xbar, dimension="width", line_color="#E74C3C", line_dash="dashed", line_width=3)
lcl_span = Span(location=lcl_xbar, dimension="width", line_color="#E74C3C", line_dash="dashed", line_width=3)
cl_span = Span(location=x_bar_bar, dimension="width", line_color="#2C3E50", line_width=3)
uwl_span = Span(location=uwl_xbar, dimension="width", line_color="#F39C12", line_dash="dotted", line_width=2)
lwl_span = Span(location=lwl_xbar, dimension="width", line_color="#F39C12", line_dash="dotted", line_width=2)
p_xbar.add_layout(ucl_span)
p_xbar.add_layout(lcl_span)
p_xbar.add_layout(cl_span)
p_xbar.add_layout(uwl_span)
p_xbar.add_layout(lwl_span)

# Labels for control limits
label_props = {"text_font_size": "16pt", "text_alpha": 0.8}
p_xbar.add_layout(Label(x=n_samples + 0.5, y=ucl_xbar, text="UCL", text_color="#E74C3C", **label_props))
p_xbar.add_layout(Label(x=n_samples + 0.5, y=lcl_xbar, text="LCL", text_color="#E74C3C", **label_props))
p_xbar.add_layout(Label(x=n_samples + 0.5, y=x_bar_bar, text="X̄̄", text_color="#2C3E50", **label_props))
p_xbar.add_layout(Label(x=n_samples + 0.5, y=uwl_xbar, text="+2σ", text_color="#F39C12", **label_props))
p_xbar.add_layout(Label(x=n_samples + 0.5, y=lwl_xbar, text="−2σ", text_color="#F39C12", **label_props))

# Style X-bar chart
p_xbar.title.text_font_size = "36pt"
p_xbar.yaxis.axis_label_text_font_size = "22pt"
p_xbar.yaxis.major_label_text_font_size = "18pt"
p_xbar.xaxis.visible = False
p_xbar.xgrid.grid_line_alpha = 0.15
p_xbar.ygrid.grid_line_alpha = 0.15
p_xbar.min_border_left = 120
p_xbar.min_border_right = 120
p_xbar.outline_line_color = None

# R chart (bottom)
p_r = figure(
    width=4800,
    height=1350,
    x_range=p_xbar.x_range,
    x_axis_label="Sample Number",
    y_axis_label="R (Sample Range, mm)",
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

# Data line and points
p_r.line("x", "y", source=source_r_line, line_width=2, line_color="#306998", line_alpha=0.6)
p_r.scatter("x", "y", source=source_r_ok, size=12, color="#306998", alpha=0.9)
p_r.scatter("x", "y", source=source_r_ooc, size=18, color="#E74C3C", marker="diamond", line_color="white", line_width=2)

# Control limits for R chart
ucl_r_span = Span(location=ucl_r, dimension="width", line_color="#E74C3C", line_dash="dashed", line_width=3)
lcl_r_span = Span(location=lcl_r, dimension="width", line_color="#E74C3C", line_dash="dashed", line_width=3)
cl_r_span = Span(location=r_bar, dimension="width", line_color="#2C3E50", line_width=3)
uwl_r_span = Span(location=uwl_r, dimension="width", line_color="#F39C12", line_dash="dotted", line_width=2)
lwl_r_span = Span(location=lwl_r, dimension="width", line_color="#F39C12", line_dash="dotted", line_width=2)
p_r.add_layout(ucl_r_span)
p_r.add_layout(lcl_r_span)
p_r.add_layout(cl_r_span)
p_r.add_layout(uwl_r_span)
p_r.add_layout(lwl_r_span)

# Labels for R chart limits
p_r.add_layout(Label(x=n_samples + 0.5, y=ucl_r, text="UCL", text_color="#E74C3C", **label_props))
p_r.add_layout(Label(x=n_samples + 0.5, y=lcl_r, text="LCL", text_color="#E74C3C", **label_props))
p_r.add_layout(Label(x=n_samples + 0.5, y=r_bar, text="R̄", text_color="#2C3E50", **label_props))
p_r.add_layout(Label(x=n_samples + 0.5, y=uwl_r, text="+2σ", text_color="#F39C12", **label_props))
p_r.add_layout(Label(x=n_samples + 0.5, y=lwl_r, text="−2σ", text_color="#F39C12", **label_props))

# Style R chart
p_r.xaxis.axis_label_text_font_size = "22pt"
p_r.yaxis.axis_label_text_font_size = "22pt"
p_r.xaxis.major_label_text_font_size = "18pt"
p_r.yaxis.major_label_text_font_size = "18pt"
p_r.xgrid.grid_line_alpha = 0.15
p_r.ygrid.grid_line_alpha = 0.15
p_r.min_border_left = 120
p_r.min_border_right = 120
p_r.outline_line_color = None

# Layout
layout = column(p_xbar, p_r)

# Save
export_png(layout, filename="plot.png")
output_file("plot.html")
save(layout)
