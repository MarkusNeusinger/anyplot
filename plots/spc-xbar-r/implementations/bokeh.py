"""pyplots.ai
spc-xbar-r: Statistical Process Control Chart (X-bar/R)
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 83/100 | Created: 2026-03-19
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.layouts import column
from bokeh.models import BoxAnnotation, ColumnDataSource, HoverTool, Label, Legend, LegendItem, Range1d, Span
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
        ("X\u0304", "@y{0.000} mm"),
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
        ("R\u0304", f"{r_bar:.3f}"),
    ],
    mode="mouse",
)

# Color palette - colorblind-safe
CLR_DATA = "#306998"
CLR_OOC = "#C0392B"
CLR_CENTER = "#2C3E50"
CLR_WARNING = "#8E44AD"
CLR_ZONE_C = "#306998"
CLR_ZONE_B = "#8E44AD"
CLR_BG = "#F7F9FB"

# X-bar chart (top)
x_range = Range1d(start=-0.5, end=n_samples + 4.5)
p_xbar = figure(
    width=4800,
    height=1350,
    title="spc-xbar-r \u00b7 bokeh \u00b7 pyplots.ai",
    x_range=x_range,
    x_axis_label=None,
    y_axis_label="X\u0304 (Sample Mean, mm)",
    toolbar_location=None,
)
p_xbar.add_tools(hover_xbar)

# Zone bands - colorblind-safe blue/purple tones
xbar_zone_c = BoxAnnotation(bottom=lwl_xbar, top=uwl_xbar, fill_color=CLR_ZONE_C, fill_alpha=0.05)
xbar_zone_b_upper = BoxAnnotation(bottom=uwl_xbar, top=ucl_xbar, fill_color=CLR_ZONE_B, fill_alpha=0.06)
xbar_zone_b_lower = BoxAnnotation(bottom=lcl_xbar, top=lwl_xbar, fill_color=CLR_ZONE_B, fill_alpha=0.06)
p_xbar.add_layout(xbar_zone_c)
p_xbar.add_layout(xbar_zone_b_upper)
p_xbar.add_layout(xbar_zone_b_lower)

# Data line and points
p_xbar.line("x", "y", source=source_xbar_line, line_width=2.5, line_color=CLR_DATA, line_alpha=0.7)
r_ok_xbar = p_xbar.scatter("x", "y", source=source_xbar_ok, size=13, color=CLR_DATA, alpha=0.9)
r_ooc_xbar = p_xbar.scatter(
    "x", "y", source=source_xbar_ooc, size=20, color=CLR_OOC, marker="diamond", line_color="white", line_width=2
)

# Legend for X-bar chart
legend_xbar = Legend(
    items=[
        LegendItem(label="In Control", renderers=[r_ok_xbar]),
        LegendItem(label="Out of Control", renderers=[r_ooc_xbar]),
    ],
    location="top_left",
    label_text_font_size="16pt",
    border_line_color=None,
    background_fill_alpha=0.7,
    background_fill_color="white",
    padding=12,
    spacing=8,
)
p_xbar.add_layout(legend_xbar)

# Control limits
p_xbar.add_layout(Span(location=ucl_xbar, dimension="width", line_color=CLR_OOC, line_dash="dashed", line_width=3))
p_xbar.add_layout(Span(location=lcl_xbar, dimension="width", line_color=CLR_OOC, line_dash="dashed", line_width=3))
p_xbar.add_layout(Span(location=x_bar_bar, dimension="width", line_color=CLR_CENTER, line_width=3))
p_xbar.add_layout(Span(location=uwl_xbar, dimension="width", line_color=CLR_WARNING, line_dash="dotted", line_width=2))
p_xbar.add_layout(Span(location=lwl_xbar, dimension="width", line_color=CLR_WARNING, line_dash="dotted", line_width=2))

# Labels - combined to avoid crowding
label_props = {"text_font_size": "16pt", "text_alpha": 0.85, "text_font_style": "bold"}
label_x = n_samples + 1.2
p_xbar.add_layout(Label(x=label_x, y=ucl_xbar, text=f"UCL ({ucl_xbar:.3f})", text_color=CLR_OOC, **label_props))
p_xbar.add_layout(Label(x=label_x, y=lcl_xbar, text=f"LCL ({lcl_xbar:.3f})", text_color=CLR_OOC, **label_props))
p_xbar.add_layout(
    Label(x=label_x, y=x_bar_bar, text=f"X\u0304 = {x_bar_bar:.3f}", text_color=CLR_CENTER, **label_props)
)
p_xbar.add_layout(Label(x=label_x, y=uwl_xbar, text="+2\u03c3", text_color=CLR_WARNING, **label_props))
p_xbar.add_layout(Label(x=label_x, y=lwl_xbar, text="\u22122\u03c3", text_color=CLR_WARNING, **label_props))

# Style X-bar chart
p_xbar.title.text_font_size = "36pt"
p_xbar.title.text_color = CLR_CENTER
p_xbar.title.text_font_style = "bold"
p_xbar.yaxis.axis_label_text_font_size = "22pt"
p_xbar.yaxis.major_label_text_font_size = "18pt"
p_xbar.xaxis.visible = False
p_xbar.xgrid.grid_line_alpha = 0.1
p_xbar.ygrid.grid_line_alpha = 0.1
p_xbar.xgrid.grid_line_dash = [4, 4]
p_xbar.ygrid.grid_line_dash = [4, 4]
p_xbar.min_border_left = 140
p_xbar.min_border_right = 220
p_xbar.min_border_top = 80
p_xbar.outline_line_color = None
p_xbar.background_fill_color = CLR_BG
p_xbar.border_fill_color = "white"

# R chart (bottom)
p_r = figure(
    width=4800,
    height=1350,
    x_range=p_xbar.x_range,
    x_axis_label="Sample Number",
    y_axis_label="R (Sample Range, mm)",
    toolbar_location=None,
)
p_r.add_tools(hover_r)

# Zone bands for R chart
r_zone_c = BoxAnnotation(bottom=lwl_r, top=uwl_r, fill_color=CLR_ZONE_C, fill_alpha=0.05)
r_zone_b_upper = BoxAnnotation(bottom=uwl_r, top=ucl_r, fill_color=CLR_ZONE_B, fill_alpha=0.06)
r_zone_b_lower = BoxAnnotation(bottom=lcl_r, top=lwl_r, fill_color=CLR_ZONE_B, fill_alpha=0.06)
p_r.add_layout(r_zone_c)
p_r.add_layout(r_zone_b_upper)
p_r.add_layout(r_zone_b_lower)

# Data line and points
p_r.line("x", "y", source=source_r_line, line_width=2.5, line_color=CLR_DATA, line_alpha=0.7)
r_ok_r = p_r.scatter("x", "y", source=source_r_ok, size=13, color=CLR_DATA, alpha=0.9)
r_ooc_r = p_r.scatter(
    "x", "y", source=source_r_ooc, size=20, color=CLR_OOC, marker="diamond", line_color="white", line_width=2
)

# Legend for R chart
legend_r = Legend(
    items=[LegendItem(label="In Control", renderers=[r_ok_r]), LegendItem(label="Out of Control", renderers=[r_ooc_r])],
    location="top_left",
    label_text_font_size="16pt",
    border_line_color=None,
    background_fill_alpha=0.7,
    background_fill_color="white",
    padding=12,
    spacing=8,
)
p_r.add_layout(legend_r)

# Control limits for R chart
p_r.add_layout(Span(location=ucl_r, dimension="width", line_color=CLR_OOC, line_dash="dashed", line_width=3))
p_r.add_layout(Span(location=lcl_r, dimension="width", line_color=CLR_OOC, line_dash="dashed", line_width=3))
p_r.add_layout(Span(location=r_bar, dimension="width", line_color=CLR_CENTER, line_width=3))
p_r.add_layout(Span(location=uwl_r, dimension="width", line_color=CLR_WARNING, line_dash="dotted", line_width=2))
p_r.add_layout(Span(location=lwl_r, dimension="width", line_color=CLR_WARNING, line_dash="dotted", line_width=2))

# Labels for R chart limits
p_r.add_layout(Label(x=label_x, y=ucl_r, text=f"UCL ({ucl_r:.3f})", text_color=CLR_OOC, **label_props))
p_r.add_layout(Label(x=label_x, y=lcl_r, text=f"LCL ({lcl_r:.3f})", text_color=CLR_OOC, **label_props))
p_r.add_layout(Label(x=label_x, y=r_bar, text=f"R\u0304 = {r_bar:.3f}", text_color=CLR_CENTER, **label_props))
p_r.add_layout(Label(x=label_x, y=uwl_r, text="+2\u03c3", text_color=CLR_WARNING, **label_props))
p_r.add_layout(Label(x=label_x, y=lwl_r, text="\u22122\u03c3", text_color=CLR_WARNING, **label_props))

# Style R chart
p_r.xaxis.axis_label_text_font_size = "22pt"
p_r.yaxis.axis_label_text_font_size = "22pt"
p_r.xaxis.major_label_text_font_size = "18pt"
p_r.yaxis.major_label_text_font_size = "18pt"
p_r.xgrid.grid_line_alpha = 0.1
p_r.ygrid.grid_line_alpha = 0.1
p_r.xgrid.grid_line_dash = [4, 4]
p_r.ygrid.grid_line_dash = [4, 4]
p_r.min_border_left = 140
p_r.min_border_right = 220
p_r.min_border_bottom = 80
p_r.outline_line_color = None
p_r.background_fill_color = CLR_BG
p_r.border_fill_color = "white"

# Layout
layout = column(p_xbar, p_r, spacing=10)

# Save
export_png(layout, filename="plot.png")
output_file("plot.html")
save(layout)
