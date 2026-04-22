""" pyplots.ai
histogram-basic: Basic Histogram
Library: bokeh 3.8.2 | Python 3.14.0
Quality: 93/100 | Created: 2025-12-23
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Legend, LegendItem, NumeralTickFormatter
from bokeh.palettes import Blues256
from bokeh.plotting import figure
from bokeh.transform import linear_cmap


# Data - Marathon finish times in minutes (right-skewed with bimodal character and outliers)
np.random.seed(42)
main_group = np.random.normal(loc=240, scale=30, size=380)
slower_group = np.random.normal(loc=305, scale=18, size=100)
outliers = np.random.normal(loc=370, scale=12, size=20)
values = np.concatenate([main_group, slower_group, outliers])
values = values[(values > 120) & (values < 420)]

# Statistics for annotations
median_val = np.median(values)
mean_val = np.mean(values)

# Calculate histogram bins
counts, edges = np.histogram(values, bins=28)
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
        "bin_start": [f"{e:.0f}" for e in left_edges],
        "bin_end": [f"{e:.0f}" for e in right_edges],
    }
)

# Idiomatic Bokeh color mapping: linear_cmap maps count values to a blue palette
# Blues256 goes light-to-dark; reverse so higher counts get darker blue (#306998-range)
fill_mapper = linear_cmap(field_name="top", palette=list(reversed(Blues256)), low=0, high=int(max_count))

# Create figure (4800 x 2700 px)
p = figure(
    width=4800,
    height=2700,
    title="histogram-basic · bokeh · pyplots.ai",
    x_axis_label="Finish Time (min)",
    y_axis_label="Number of Runners",
    toolbar_location=None,
    x_range=(118, 410),
)

# Plot histogram as quad glyphs with linear_cmap color mapping
bars = p.quad(
    left="left",
    right="right",
    top="top",
    bottom="bottom",
    source=source,
    fill_color=fill_mapper,
    line_color="white",
    line_width=1.5,
    fill_alpha=0.85,
    hover_fill_color="#FFD43B",
    hover_fill_alpha=0.95,
    hover_line_color="white",
)

# HoverTool with custom formatters — distinctive Bokeh interactive feature
hover = HoverTool(
    renderers=[bars], tooltips=[("Range", "@bin_start–@bin_end min"), ("Runners", "@count")], mode="mouse"
)
p.add_tools(hover)

# Annotation: median line (solid red)
median_line = p.line(
    x=[median_val, median_val], y=[0, max_count * 1.05], line_color="#C0392B", line_width=4, line_alpha=0.85
)

# Annotation: mean line (dashed teal)
mean_line = p.line(
    x=[mean_val, mean_val],
    y=[0, max_count * 1.05],
    line_color="#1A9E76",
    line_width=4,
    line_dash=[10, 5],
    line_alpha=0.85,
)

# Formal legend using Bokeh Legend model — rendered inside the plot area
legend = Legend(
    items=[
        LegendItem(label=f"Median: {median_val:.0f} min", renderers=[median_line]),
        LegendItem(label=f"Mean: {mean_val:.0f} min", renderers=[mean_line]),
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

# Annotation: label the main peak with an arrow-like callout
peak_label = Label(
    x=205,
    y=max_count * 1.02,
    text="\u25bc Main group (~4 hr pace)",
    text_font_size="22pt",
    text_color="#306998",
    text_font_style="bold",
)
p.add_layout(peak_label)

# Annotation: slower group shoulder — position above the shoulder bars
slower_bin_idx = np.argmin(np.abs(left_edges - 295))
slower_peak = counts[max(0, slower_bin_idx - 1) : slower_bin_idx + 2].max()
shoulder_label = Label(
    x=288,
    y=slower_peak + max_count * 0.08,
    text="\u25bc Slower group (~5 hr pace)",
    text_font_size="22pt",
    text_color="#5B8BA8",
    text_font_style="bold",
)
p.add_layout(shoulder_label)

# Subtitle with dataset context
subtitle = Label(
    x=130,
    y=max_count * 1.10,
    text=f"N = {len(values)} runners  \u2502  Right-skewed bimodal distribution",
    text_font_size="22pt",
    text_color="#777777",
)
p.add_layout(subtitle)

# Typography hierarchy for 4800x2700 canvas
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

# Format y-axis with comma separator for readability
p.yaxis.formatter = NumeralTickFormatter(format="0,0")

# Grid styling - y-axis only, very subtle
p.xgrid.visible = False
p.ygrid.grid_line_alpha = 0.15
p.ygrid.grid_line_color = "#CCCCCC"
p.ygrid.grid_line_width = 1

# Clean frame — remove top/right spines via axis visibility
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

# Y-axis starts at zero with headroom for annotations
p.y_range.start = 0
p.y_range.end = max_count * 1.22

# Balanced margins for full canvas utilization
p.min_border_left = 140
p.min_border_right = 60
p.min_border_bottom = 110
p.min_border_top = 80

# Save outputs
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
