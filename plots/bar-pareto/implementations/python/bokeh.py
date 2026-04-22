""" pyplots.ai
bar-pareto: Pareto Chart with Cumulative Line
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-20
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, HoverTool, Label, LinearAxis, PrintfTickFormatter, Range1d, Span
from bokeh.plotting import figure, output_file, save


# Data - Manufacturing defect types sorted by frequency (descending)
categories = [
    "Scratches",
    "Dents",
    "Misalignment",
    "Discoloration",
    "Cracks",
    "Burrs",
    "Warping",
    "Contamination",
    "Chipping",
    "Porosity",
]
counts = np.array([187, 143, 98, 72, 54, 38, 27, 19, 12, 7])

# Cumulative percentage
cumulative_pct = np.cumsum(counts) / counts.sum() * 100

# Identify vital few (contribute to first 80%)
vital_mask = cumulative_pct <= 80
# Include the bar that crosses 80%
if not vital_mask.all():
    first_over = np.argmax(~vital_mask)
    vital_mask[first_over] = True
bar_colors = ["#306998" if v else "#7BA4C7" for v in vital_mask]

source = ColumnDataSource(
    data={
        "categories": categories,
        "counts": counts,
        "cumulative_pct": cumulative_pct,
        "colors": bar_colors,
        "pct_label": [f"{p:.0f}%" for p in cumulative_pct],
    }
)

# Figure with categorical x-axis
p = figure(
    x_range=categories,
    width=4800,
    height=2700,
    title="bar-pareto · bokeh · pyplots.ai",
    x_axis_label="Defect Type",
    y_axis_label="Defect Count",
    toolbar_location=None,
)

# Bars - vital few in dark blue, trivial many in lighter blue
p.vbar(
    x="categories",
    top="counts",
    source=source,
    width=0.7,
    color="colors",
    alpha=0.9,
    line_color="white",
    line_width=2,
    legend_label="Defect Count",
)

# Secondary y-axis for cumulative percentage
p.extra_y_ranges = {"pct": Range1d(start=0, end=105)}
pct_axis = LinearAxis(
    y_range_name="pct",
    axis_label="Cumulative %",
    axis_label_text_font_size="28pt",
    major_label_text_font_size="24pt",
    axis_line_color="#333333",
    axis_line_width=2,
    major_tick_line_color=None,
    minor_tick_line_color=None,
)
pct_axis.formatter = PrintfTickFormatter(format="%d%%")
p.add_layout(pct_axis, "right")

# Cumulative line on secondary axis
p.line(
    x="categories",
    y="cumulative_pct",
    source=source,
    y_range_name="pct",
    line_width=4,
    line_color="#E8833A",
    line_join="round",
    legend_label="Cumulative %",
)

# Cumulative line markers
p.scatter(
    x="categories",
    y="cumulative_pct",
    source=source,
    y_range_name="pct",
    size=14,
    color="#E8833A",
    line_color="white",
    line_width=2,
)

# Add cumulative percentage labels at each marker
for i, (_cat, pct) in enumerate(zip(categories, cumulative_pct, strict=False)):
    p.add_layout(
        Label(
            x=i,
            y=pct,
            text=f"{pct:.0f}%",
            text_font_size="18pt",
            text_color="#C0652A",
            text_font_style="bold",
            text_align="left" if i == 0 else "center",
            y_offset=18,
            y_range_name="pct",
        )
    )

# 80% reference line - more prominent
span_80 = Span(
    location=80,
    dimension="width",
    line_color="#E8833A",
    line_dash="dashed",
    line_width=3,
    line_alpha=0.7,
    y_range_name="pct",
)
p.add_layout(span_80)

# Label for 80% reference line
p.add_layout(
    Label(
        x=9,
        y=80,
        text="80% threshold",
        text_font_size="20pt",
        text_color="#E8833A",
        text_font_style="bold",
        text_align="right",
        y_offset=12,
        x_offset=-10,
        y_range_name="pct",
    )
)

# HoverTool - Bokeh signature interactive feature
hover = HoverTool(
    tooltips=[("Defect", "@categories"), ("Count", "@counts"), ("Cumulative", "@pct_label")], mode="vline"
)
p.add_tools(hover)

# Styling
p.title.text_font_size = "36pt"
p.title.align = "center"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "24pt"
p.xaxis.major_label_orientation = 0.5

# Clean frame
p.outline_line_color = None
p.xaxis.axis_line_color = "#333333"
p.yaxis.axis_line_color = "#333333"
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2

# Remove tick marks
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Grid - y-axis only, subtle
p.xgrid.grid_line_color = None
p.ygrid.grid_line_alpha = 0.2

# Y-axis range
p.y_range.start = 0
p.y_range.end = max(counts) * 1.12

# Legend
p.legend.location = "top_left"
p.legend.label_text_font_size = "20pt"
p.legend.background_fill_alpha = 0.8
p.legend.border_line_color = None
p.legend.padding = 15
p.legend.spacing = 8

# Background
p.background_fill_color = "#FFFFFF"

# Save
export_png(p, filename="plot.png")

output_file("plot.html")
save(p)
