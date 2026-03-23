""" pyplots.ai
histogram-capability: Process Capability Plot with Specification Limits
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-19
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Legend, LegendItem, Span
from bokeh.plotting import figure
from scipy import stats


# Data - Shaft diameter measurements (mm)
np.random.seed(42)
lsl = 9.95
usl = 10.05
target = 10.00
measurements = np.random.normal(loc=10.005, scale=0.012, size=200)

# Statistics
mean_val = np.mean(measurements)
sigma = np.std(measurements, ddof=1)
cp = (usl - lsl) / (6 * sigma)
cpk = min((usl - mean_val) / (3 * sigma), (mean_val - lsl) / (3 * sigma))

# Histogram bins
counts, edges = np.histogram(measurements, bins=25)
left_edges = edges[:-1]
right_edges = edges[1:]
max_count = counts.max()

source = ColumnDataSource(
    data={
        "left": left_edges,
        "right": right_edges,
        "top": counts,
        "bottom": [0] * len(counts),
        "count": counts,
        "bin_start": [f"{e:.4f}" for e in left_edges],
        "bin_end": [f"{e:.4f}" for e in right_edges],
    }
)

# Normal distribution curve - extend to cover spec limits
x_curve = np.linspace(min(lsl - 0.01, measurements.min() - 0.01), max(usl + 0.01, measurements.max() + 0.01), 300)
bin_width = edges[1] - edges[0]
y_curve = stats.norm.pdf(x_curve, mean_val, sigma) * len(measurements) * bin_width
curve_source = ColumnDataSource(data={"x": x_curve, "y": y_curve})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="histogram-capability · bokeh · pyplots.ai",
    x_axis_label="Shaft Diameter (mm)",
    y_axis_label="Frequency",
    toolbar_location=None,
)

# Histogram bars
bars = p.quad(
    left="left",
    right="right",
    top="top",
    bottom="bottom",
    source=source,
    fill_color="#306998",
    fill_alpha=0.75,
    line_color="white",
    line_width=1.5,
    hover_fill_color="#FFD43B",
    hover_fill_alpha=0.95,
    hover_line_color="white",
)

# Hover tool
hover = HoverTool(renderers=[bars], tooltips=[("Range", "@bin_start – @bin_end mm"), ("Count", "@count")], mode="mouse")
p.add_tools(hover)

# Normal distribution curve
curve_line = p.line(x="x", y="y", source=curve_source, line_color="#306998", line_width=4, line_alpha=0.9)

# Specification limit lines using Span (idiomatic Bokeh for reference lines)
lsl_span = Span(location=lsl, dimension="height", line_color="#C0392B", line_width=4, line_dash=[12, 6], line_alpha=0.9)
usl_span = Span(location=usl, dimension="height", line_color="#C0392B", line_width=4, line_dash=[12, 6], line_alpha=0.9)
p.add_layout(lsl_span)
p.add_layout(usl_span)

# Target line - using teal (colorblind-safe, avoids red-green pairing)
target_span = Span(
    location=target, dimension="height", line_color="#17BECF", line_width=4, line_dash=[12, 6], line_alpha=0.9
)
p.add_layout(target_span)

# Mean line
mean_span = Span(
    location=mean_val, dimension="height", line_color="#7B4F9D", line_width=3, line_dash=[6, 4], line_alpha=0.85
)
p.add_layout(mean_span)

# Off-screen renderers for legend entries (Span doesn't support legend directly)
_off = -999
lsl_line = p.line(x=[_off, _off], y=[_off, _off], line_color="#C0392B", line_width=4, line_dash=[12, 6])
usl_line = p.line(x=[_off, _off], y=[_off, _off], line_color="#C0392B", line_width=4, line_dash=[12, 6])
target_line = p.line(x=[_off, _off], y=[_off, _off], line_color="#17BECF", line_width=4, line_dash=[12, 6])
mean_line = p.line(x=[_off, _off], y=[_off, _off], line_color="#7B4F9D", line_width=3, line_dash=[6, 4])

# Legend
legend = Legend(
    items=[
        LegendItem(label="Normal Fit", renderers=[curve_line]),
        LegendItem(label=f"LSL = {lsl:.2f}", renderers=[lsl_line]),
        LegendItem(label=f"USL = {usl:.2f}", renderers=[usl_line]),
        LegendItem(label=f"Target = {target:.2f}", renderers=[target_line]),
        LegendItem(label=f"Mean = {mean_val:.4f}", renderers=[mean_line]),
    ],
    location="top_right",
    label_text_font_size="22pt",
    label_text_color="#333333",
    glyph_width=60,
    glyph_height=6,
    spacing=14,
    padding=20,
    background_fill_alpha=0.75,
    background_fill_color="white",
    border_line_color="#CCCCCC",
    border_line_alpha=0.5,
)
p.add_layout(legend, "center")

# Capability indices annotation
cap_text = f"Cp = {cp:.2f}  |  Cpk = {cpk:.2f}  |  N = {len(measurements)}"
cap_label = Label(
    x=lsl + 0.002,
    y=max_count * 1.12,
    text=cap_text,
    text_font_size="26pt",
    text_color="#222222",
    text_font_style="bold",
)
p.add_layout(cap_label)

# Typography
p.title.text_font_size = "38pt"
p.title.text_color = "#222222"
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.axis_label_text_color = "#444444"
p.yaxis.axis_label_text_color = "#444444"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"
p.xaxis.major_label_text_color = "#555555"
p.yaxis.major_label_text_color = "#555555"

# Grid - y-axis only, subtle
p.xgrid.visible = False
p.ygrid.grid_line_alpha = 0.15
p.ygrid.grid_line_color = "#CCCCCC"
p.ygrid.grid_line_width = 1

# Clean frame
p.outline_line_color = None
p.background_fill_color = "white"
p.border_fill_color = "white"
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.axis_line_color = "#AAAAAA"
p.yaxis.axis_line_color = "#AAAAAA"
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.major_tick_line_color = "#AAAAAA"
p.yaxis.major_tick_line_color = "#AAAAAA"

# Axis ranges - ensure LSL/USL are visible with margin
p.x_range.start = lsl - 0.015
p.x_range.end = usl + 0.015
p.y_range.start = 0
p.y_range.end = max_count * 1.25

# Margins
p.min_border_left = 140
p.min_border_right = 60
p.min_border_bottom = 110
p.min_border_top = 80

# Save
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
