""" pyplots.ai
heatmap-cohort-retention: Cohort Retention Heatmap
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-16
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import BasicTicker, ColorBar, ColumnDataSource, LinearColorMapper
from bokeh.plotting import figure
from bokeh.transform import transform


# Data: Monthly signup cohorts with weekly retention
np.random.seed(42)
cohort_labels = [
    "Jan 2024",
    "Feb 2024",
    "Mar 2024",
    "Apr 2024",
    "May 2024",
    "Jun 2024",
    "Jul 2024",
    "Aug 2024",
    "Sep 2024",
    "Oct 2024",
]
n_cohorts = len(cohort_labels)
n_periods = 10
cohort_sizes = np.random.randint(800, 2500, size=n_cohorts)

# Generate realistic retention data (triangular shape)
retention = np.full((n_cohorts, n_periods), np.nan)
for i in range(n_cohorts):
    max_periods = n_periods - i
    retention[i, 0] = 100.0
    base_decay = np.random.uniform(0.65, 0.80)
    for j in range(1, max_periods):
        decay = base_decay + np.random.uniform(-0.05, 0.05)
        retention[i, j] = retention[i, j - 1] * decay
        retention[i, j] = max(retention[i, j], 2.0)

# Prepare data for bokeh heatmap
x_coords = []
y_coords = []
values = []
text_values = []
text_colors = []

period_labels = [f"Month {i}" for i in range(n_periods)]
y_labels = [f"{label} (n={size:,})" for label, size in zip(cohort_labels, cohort_sizes, strict=True)]

for i in range(n_cohorts):
    for j in range(n_periods):
        if not np.isnan(retention[i, j]):
            x_coords.append(period_labels[j])
            y_coords.append(y_labels[i])
            val = retention[i, j]
            values.append(val)
            text_values.append(f"{val:.1f}%")
            text_colors.append("white" if val > 55 else "#1a1a1a")

source = ColumnDataSource(
    data={"x": x_coords, "y": y_coords, "value": values, "text": text_values, "text_color": text_colors}
)

# Sequential green colormap (light = low retention, dark = high retention)
colors = ["#f7fcf5", "#e5f5e0", "#c7e9c0", "#a1d99b", "#74c476", "#41ab5d", "#238b45", "#006d2c", "#00441b"]
mapper = LinearColorMapper(palette=colors, low=0, high=100)

# Create figure
p = figure(
    width=4800,
    height=2700,
    x_range=period_labels,
    y_range=list(reversed(y_labels)),
    title="heatmap-cohort-retention · bokeh · pyplots.ai",
    x_axis_location="above",
    toolbar_location=None,
)

# Add heatmap rectangles
p.rect(
    x="x",
    y="y",
    width=1,
    height=1,
    source=source,
    fill_color=transform("value", mapper),
    line_color="white",
    line_width=3,
)

# Add retention percentage text
p.text(
    x="x",
    y="y",
    text="text",
    source=source,
    text_align="center",
    text_baseline="middle",
    text_font_size="18pt",
    text_color="text_color",
)

# Style
p.title.text_font_size = "28pt"
p.title.align = "center"
p.xaxis.axis_label = "Months Since Signup"
p.yaxis.axis_label = "Signup Cohort"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "16pt"
p.yaxis.major_label_text_font_size = "16pt"
p.axis.axis_line_color = None
p.axis.major_tick_line_color = None
p.grid.grid_line_color = None

# Add colorbar
color_bar = ColorBar(
    color_mapper=mapper,
    ticker=BasicTicker(desired_num_ticks=6),
    label_standoff=12,
    major_label_text_font_size="16pt",
    title="Retention %",
    title_text_font_size="20pt",
    width=40,
    location=(0, 0),
)
p.add_layout(color_bar, "right")

# Save
export_png(p, filename="plot.png")
