""" pyplots.ai
spc-xbar-r: Statistical Process Control Chart (X-bar/R)
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 83/100 | Created: 2026-03-19
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.layouts import column
from bokeh.models import BoxAnnotation, ColumnDataSource, HoverTool, Label, Range1d, Span
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

# Inject range out-of-control point
sample_ranges[12] = sample_ranges[12] * 3.5  # Abnormal range at sample 13

# Control chart constants for n=5
A2 = 0.577
D3 = 0.0
D4 = 2.114

# X-bar chart limits
x_bar_bar = sample_means.mean()
r_bar = sample_ranges.mean()
ucl_xbar = x_bar_bar + A2 * r_bar
lcl_xbar = x_bar_bar - A2 * r_bar
uwl_xbar = x_bar_bar + (2 / 3) * A2 * r_bar
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
source_xbar_ok = ColumnDataSource(
    data={"x": sample_ids[~ooc_xbar], "y": sample_means[~ooc_xbar], "status": ["In Control"] * (~ooc_xbar).sum()}
)
source_xbar_ooc = ColumnDataSource(
    data={"x": sample_ids[ooc_xbar], "y": sample_means[ooc_xbar], "status": ["OUT OF CONTROL"] * ooc_xbar.sum()}
)
source_xbar_line = ColumnDataSource(data={"x": sample_ids, "y": sample_means})

# Sources for R chart
source_r_ok = ColumnDataSource(
    data={"x": sample_ids[~ooc_r], "y": sample_ranges[~ooc_r], "status": ["In Control"] * (~ooc_r).sum()}
)
source_r_ooc = ColumnDataSource(
    data={"x": sample_ids[ooc_r], "y": sample_ranges[ooc_r], "status": ["OUT OF CONTROL"] * ooc_r.sum()}
)
source_r_line = ColumnDataSource(data={"x": sample_ids, "y": sample_ranges})

# Hover tool for X-bar chart
hover_xbar = HoverTool(
    tooltips=[
        ("Sample", "@x"),
        ("X̄", "@y{0.000} mm"),
        ("Status", "@status"),
        ("UCL", f"{ucl_xbar:.3f}"),
        ("CL", f"{x_bar_bar:.3f}"),
        ("LCL", f"{lcl_xbar:.3f}"),
    ],
    mode="mouse",
)

# Hover tool for R chart
hover_r = HoverTool(
    tooltips=[
        ("Sample", "@x"),
        ("Range", "@y{0.000} mm"),
        ("Status", "@status"),
        ("UCL", f"{ucl_r:.3f}"),
        ("R̄", f"{r_bar:.3f}"),
    ],
    mode="mouse",
)

# X-bar chart (top)
x_range = Range1d(start=-0.5, end=n_samples + 3.5)
p_xbar = figure(
    width=4800,
    height=1350,
    title="spc-xbar-r · bokeh · pyplots.ai",
    x_range=x_range,
    x_axis_label=None,
    y_axis_label="X̄ (Sample Mean, mm)",
    tools="pan,wheel_zoom,box_zoom,reset,save",
    toolbar_location="above",
)
p_xbar.add_tools(hover_xbar)

# Zone bands using BoxAnnotation for X-bar chart
xbar_zone_c = BoxAnnotation(bottom=lwl_xbar, top=uwl_xbar, fill_color="#27AE60", fill_alpha=0.06)
xbar_zone_b_upper = BoxAnnotation(bottom=uwl_xbar, top=ucl_xbar, fill_color="#F39C12", fill_alpha=0.08)
xbar_zone_b_lower = BoxAnnotation(bottom=lcl_xbar, top=lwl_xbar, fill_color="#F39C12", fill_alpha=0.08)
p_xbar.add_layout(xbar_zone_c)
p_xbar.add_layout(xbar_zone_b_upper)
p_xbar.add_layout(xbar_zone_b_lower)

# Data line and points
p_xbar.line("x", "y", source=source_xbar_line, line_width=2.5, line_color="#306998", line_alpha=0.5)
r_ok = p_xbar.scatter("x", "y", source=source_xbar_ok, size=13, color="#306998", alpha=0.9)
r_ooc = p_xbar.scatter(
    "x", "y", source=source_xbar_ooc, size=20, color="#C0392B", marker="diamond", line_color="white", line_width=2
)

# Control limits
p_xbar.add_layout(Span(location=ucl_xbar, dimension="width", line_color="#C0392B", line_dash="dashed", line_width=3))
p_xbar.add_layout(Span(location=lcl_xbar, dimension="width", line_color="#C0392B", line_dash="dashed", line_width=3))
p_xbar.add_layout(Span(location=x_bar_bar, dimension="width", line_color="#2C3E50", line_width=3))
p_xbar.add_layout(Span(location=uwl_xbar, dimension="width", line_color="#E67E22", line_dash="dotted", line_width=2))
p_xbar.add_layout(Span(location=lwl_xbar, dimension="width", line_color="#E67E22", line_dash="dotted", line_width=2))

# Labels for control limits (positioned on right side past data)
label_props = {"text_font_size": "18pt", "text_alpha": 0.9, "text_font_style": "bold"}
label_x = n_samples + 0.8
p_xbar.add_layout(Label(x=label_x, y=ucl_xbar, text="UCL", text_color="#C0392B", **label_props))
p_xbar.add_layout(Label(x=label_x, y=lcl_xbar, text="LCL", text_color="#C0392B", **label_props))
p_xbar.add_layout(Label(x=label_x, y=x_bar_bar, text="X̄̄", text_color="#2C3E50", **label_props))
p_xbar.add_layout(Label(x=label_x, y=uwl_xbar, text="+2σ", text_color="#E67E22", **label_props))
p_xbar.add_layout(Label(x=label_x, y=lwl_xbar, text="−2σ", text_color="#E67E22", **label_props))

# Style X-bar chart
p_xbar.title.text_font_size = "36pt"
p_xbar.title.text_color = "#2C3E50"
p_xbar.yaxis.axis_label_text_font_size = "22pt"
p_xbar.yaxis.major_label_text_font_size = "18pt"
p_xbar.xaxis.visible = False
p_xbar.xgrid.grid_line_alpha = 0.12
p_xbar.ygrid.grid_line_alpha = 0.12
p_xbar.xgrid.grid_line_dash = [4, 4]
p_xbar.ygrid.grid_line_dash = [4, 4]
p_xbar.min_border_left = 130
p_xbar.min_border_right = 160
p_xbar.min_border_top = 80
p_xbar.outline_line_color = None
p_xbar.background_fill_color = "#FAFBFC"

# R chart (bottom)
p_r = figure(
    width=4800,
    height=1350,
    x_range=p_xbar.x_range,
    x_axis_label="Sample Number",
    y_axis_label="R (Sample Range, mm)",
    tools="pan,wheel_zoom,box_zoom,reset,save",
    toolbar_location="above",
)
p_r.add_tools(hover_r)

# Zone bands using BoxAnnotation for R chart
r_zone_c = BoxAnnotation(bottom=lwl_r, top=uwl_r, fill_color="#27AE60", fill_alpha=0.06)
r_zone_b_upper = BoxAnnotation(bottom=uwl_r, top=ucl_r, fill_color="#F39C12", fill_alpha=0.08)
r_zone_b_lower = BoxAnnotation(bottom=lcl_r, top=lwl_r, fill_color="#F39C12", fill_alpha=0.08)
p_r.add_layout(r_zone_c)
p_r.add_layout(r_zone_b_upper)
p_r.add_layout(r_zone_b_lower)

# Data line and points
p_r.line("x", "y", source=source_r_line, line_width=2.5, line_color="#306998", line_alpha=0.5)
p_r.scatter("x", "y", source=source_r_ok, size=13, color="#306998", alpha=0.9)
p_r.scatter("x", "y", source=source_r_ooc, size=20, color="#C0392B", marker="diamond", line_color="white", line_width=2)

# Control limits for R chart
p_r.add_layout(Span(location=ucl_r, dimension="width", line_color="#C0392B", line_dash="dashed", line_width=3))
p_r.add_layout(Span(location=lcl_r, dimension="width", line_color="#C0392B", line_dash="dashed", line_width=3))
p_r.add_layout(Span(location=r_bar, dimension="width", line_color="#2C3E50", line_width=3))
p_r.add_layout(Span(location=uwl_r, dimension="width", line_color="#E67E22", line_dash="dotted", line_width=2))
p_r.add_layout(Span(location=lwl_r, dimension="width", line_color="#E67E22", line_dash="dotted", line_width=2))

# Labels for R chart limits
p_r.add_layout(Label(x=label_x, y=ucl_r, text="UCL", text_color="#C0392B", **label_props))
p_r.add_layout(Label(x=label_x, y=lcl_r, text="LCL", text_color="#C0392B", **label_props))
p_r.add_layout(Label(x=label_x, y=r_bar, text="R̄", text_color="#2C3E50", **label_props))
p_r.add_layout(Label(x=label_x, y=uwl_r, text="+2σ", text_color="#E67E22", **label_props))
p_r.add_layout(Label(x=label_x, y=lwl_r, text="−2σ", text_color="#E67E22", **label_props))

# Style R chart
p_r.xaxis.axis_label_text_font_size = "22pt"
p_r.yaxis.axis_label_text_font_size = "22pt"
p_r.xaxis.major_label_text_font_size = "18pt"
p_r.yaxis.major_label_text_font_size = "18pt"
p_r.xgrid.grid_line_alpha = 0.12
p_r.ygrid.grid_line_alpha = 0.12
p_r.xgrid.grid_line_dash = [4, 4]
p_r.ygrid.grid_line_dash = [4, 4]
p_r.min_border_left = 130
p_r.min_border_right = 160
p_r.min_border_bottom = 80
p_r.outline_line_color = None
p_r.background_fill_color = "#FAFBFC"

# Layout
layout = column(p_xbar, p_r, spacing=10)

# Save
export_png(layout, filename="plot.png")
output_file("plot.html")
save(layout)
