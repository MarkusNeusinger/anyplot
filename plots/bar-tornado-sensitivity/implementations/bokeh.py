"""pyplots.ai
bar-tornado-sensitivity: Tornado Diagram for Sensitivity Analysis
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-03-07
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, Span
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

# Separate into left (below base) and right (above base) segments
left_of_base = np.minimum(low_sorted, high_sorted)
right_of_base = np.maximum(low_sorted, high_sorted)

# Build source for low-scenario side and high-scenario side
low_left = np.where(low_sorted < base_npv, low_sorted, base_npv)
low_right = np.where(low_sorted < base_npv, base_npv, low_sorted)
high_left = np.where(high_sorted > base_npv, base_npv, high_sorted)
high_right = np.where(high_sorted > base_npv, high_sorted, base_npv)

source_low = ColumnDataSource(data={"parameter": parameters_sorted, "left": low_left, "right": low_right})

source_high = ColumnDataSource(data={"parameter": parameters_sorted, "left": high_left, "right": high_right})

# Plot
p = figure(
    width=4800,
    height=2700,
    y_range=parameters_sorted,
    x_range=(4.0, 21.0),
    title="NPV Sensitivity Analysis · bar-tornado-sensitivity · bokeh · pyplots.ai",
    x_axis_label="Net Present Value ($M)",
)

# Low-scenario bars
p.hbar(
    y="parameter",
    left="left",
    right="right",
    height=0.65,
    color="#306998",
    alpha=0.9,
    source=source_low,
    legend_label="Low Scenario",
)

# High-scenario bars
p.hbar(
    y="parameter",
    left="left",
    right="right",
    height=0.65,
    color="#FFD43B",
    alpha=0.9,
    source=source_high,
    legend_label="High Scenario",
)

# Base case vertical reference line
baseline = Span(location=base_npv, dimension="height", line_color="#333333", line_width=3, line_dash="solid")
p.add_layout(baseline)

# Style
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

p.xgrid.grid_line_alpha = 0.2
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_alpha = 0.0
p.outline_line_color = None
p.background_fill_color = "#ffffff"

p.legend.label_text_font_size = "18pt"
p.legend.location = "bottom_right"
p.legend.background_fill_alpha = 0.8

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", title="bar-tornado-sensitivity · bokeh · pyplots.ai")
