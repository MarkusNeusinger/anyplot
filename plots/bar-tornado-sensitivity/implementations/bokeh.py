""" pyplots.ai
bar-tornado-sensitivity: Tornado Diagram for Sensitivity Analysis
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-07
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, HoverTool, Label, LabelSet, Span
from bokeh.plotting import figure, save


# Data - NPV sensitivity analysis for a renewable energy project
# Base case NPV: $12.5M
base_npv = 12.5

parameters = [
    "Electricity Price ($/MWh)",
    "Discount Rate (%)",
    "Construction Cost ($M)",
    "Capacity Factor (%)",
    "Equipment Lifetime (yrs)",
    "O&M Cost ($/MWh)",
    "Tax Credit Rate (%)",
    "Inflation Rate (%)",
    "Salvage Value ($M)",
    "Insurance Cost ($M/yr)",
]

# [low_scenario_NPV, high_scenario_NPV] when each parameter is varied
low_values = np.array([6.2, 8.1, 9.8, 8.5, 10.3, 11.0, 10.8, 11.2, 12.0, 11.8])
high_values = np.array([18.8, 17.4, 15.2, 16.5, 14.7, 14.0, 14.2, 13.8, 13.0, 13.2])

# Sort by total range (widest bar at top)
total_range = high_values - low_values
sort_idx = np.argsort(total_range)
parameters_sorted = [parameters[i] for i in sort_idx]
low_sorted = low_values[sort_idx]
high_sorted = high_values[sort_idx]
ranges_sorted = total_range[sort_idx]

# Build source for low-scenario side and high-scenario side
low_left = np.where(low_sorted < base_npv, low_sorted, base_npv)
low_right = np.where(low_sorted < base_npv, base_npv, low_sorted)
high_left = np.where(high_sorted > base_npv, base_npv, high_sorted)
high_right = np.where(high_sorted > base_npv, high_sorted, base_npv)

# Color intensity based on influence rank for visual hierarchy
n = len(parameters_sorted)
low_alphas = [0.55 + 0.4 * (i / (n - 1)) for i in range(n)]
high_alphas = [0.55 + 0.4 * (i / (n - 1)) for i in range(n)]

source_low = ColumnDataSource(
    data={
        "parameter": parameters_sorted,
        "left": low_left,
        "right": low_right,
        "low_val": [f"${v:.1f}M" for v in low_sorted],
        "range_val": [f"${r:.1f}M" for r in ranges_sorted],
        "alpha": low_alphas,
    }
)

source_high = ColumnDataSource(
    data={
        "parameter": parameters_sorted,
        "left": high_left,
        "right": high_right,
        "high_val": [f"${v:.1f}M" for v in high_sorted],
        "range_val": [f"${r:.1f}M" for r in ranges_sorted],
        "alpha": high_alphas,
    }
)

# Annotation labels at bar ends
label_low_source = ColumnDataSource(
    data={"parameter": parameters_sorted, "x": low_sorted, "text": [f"${v:.1f}M" for v in low_sorted]}
)

label_high_source = ColumnDataSource(
    data={"parameter": parameters_sorted, "x": high_sorted, "text": [f"${v:.1f}M" for v in high_sorted]}
)

# Plot
p = figure(
    width=4800,
    height=2700,
    y_range=parameters_sorted,
    x_range=(3.5, 21.5),
    title="NPV Sensitivity Analysis · bar-tornado-sensitivity · bokeh · pyplots.ai",
    x_axis_label="Net Present Value ($M)",
)

# Color palette - refined blue/amber with good contrast
blue = "#1a5276"
amber = "#d4a017"

# Low-scenario bars
p.hbar(
    y="parameter",
    left="left",
    right="right",
    height=0.6,
    color=blue,
    alpha="alpha",
    source=source_low,
    legend_label="Low Scenario",
    line_color=blue,
    line_width=1,
)

# High-scenario bars
p.hbar(
    y="parameter",
    left="left",
    right="right",
    height=0.6,
    color=amber,
    alpha="alpha",
    source=source_high,
    legend_label="High Scenario",
    line_color=amber,
    line_width=1,
)

# Value annotations at low-scenario bar ends
low_labels = LabelSet(
    x="x",
    y="parameter",
    text="text",
    source=label_low_source,
    text_font_size="14pt",
    text_color="#333333",
    text_align="right",
    x_offset=-8,
    y_offset=-1,
    text_font_style="bold",
)
p.add_layout(low_labels)

# Value annotations at high-scenario bar ends
high_labels = LabelSet(
    x="x",
    y="parameter",
    text="text",
    source=label_high_source,
    text_font_size="14pt",
    text_color="#333333",
    text_align="left",
    x_offset=8,
    y_offset=-1,
    text_font_style="bold",
)
p.add_layout(high_labels)

# Base case vertical reference line
baseline = Span(location=base_npv, dimension="height", line_color="#2c3e50", line_width=3, line_dash="solid")
p.add_layout(baseline)

# Base case label
base_label = Label(
    x=base_npv,
    y=n - 0.3,
    text=f"Base Case: ${base_npv}M",
    text_font_size="16pt",
    text_color="#2c3e50",
    text_font_style="bold",
    text_align="center",
    y_units="data",
    y_offset=30,
)
p.add_layout(base_label)

# HoverTool for interactive exploration
hover = HoverTool(
    tooltips=[
        ("Parameter", "@parameter"),
        ("Low NPV", "@low_val"),
        ("High NPV", "@high_val"),
        ("Impact Range", "@range_val"),
    ]
)
p.add_tools(hover)

# Typography & styling - publication quality
p.title.text_font_size = "30pt"
p.title.text_color = "#2c3e50"
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = "#555555"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = "#555555"
p.yaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_color = "#333333"

# Grid and frame refinement
p.xgrid.grid_line_alpha = 0.15
p.xgrid.grid_line_dash = [6, 4]
p.xgrid.grid_line_color = "#aaaaaa"
p.ygrid.grid_line_alpha = 0.0
p.outline_line_color = None
p.background_fill_color = "#fafafa"
p.border_fill_color = "#ffffff"

# Axis styling
p.xaxis.axis_line_color = "#cccccc"
p.yaxis.axis_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.major_tick_line_color = "#cccccc"
p.yaxis.major_tick_line_color = None

# Legend placement near data
p.legend.label_text_font_size = "16pt"
p.legend.location = "bottom_right"
p.legend.background_fill_alpha = 0.85
p.legend.background_fill_color = "#ffffff"
p.legend.border_line_color = "#dddddd"
p.legend.border_line_width = 1
p.legend.padding = 12
p.legend.margin = 20
p.legend.glyph_height = 20
p.legend.glyph_width = 30
p.legend.label_text_color = "#333333"

# Toolbar position
p.toolbar_location = "above"

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", title="bar-tornado-sensitivity · bokeh · pyplots.ai")
