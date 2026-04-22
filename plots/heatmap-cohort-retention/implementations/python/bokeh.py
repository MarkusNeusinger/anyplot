""" pyplots.ai
heatmap-cohort-retention: Cohort Retention Heatmap
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-16
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import BasicTicker, ColorBar, ColumnDataSource, HoverTool, Label, LinearColorMapper
from bokeh.plotting import figure
from bokeh.transform import transform


# Data: Monthly signup cohorts with retention tracking
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
            # Adaptive text color with refined threshold for viridis
            text_colors.append("white" if val < 45 else "#1a1a1a")

source = ColumnDataSource(
    data={"x": x_coords, "y": y_coords, "value": values, "text": text_values, "text_color": text_colors}
)

# Viridis-inspired palette: perceptually uniform, colorblind-safe
viridis_palette = [
    "#440154",
    "#482878",
    "#3e4989",
    "#31688e",
    "#26828e",
    "#1f9e89",
    "#35b779",
    "#6ece58",
    "#b5de2b",
    "#fde725",
]
mapper = LinearColorMapper(palette=viridis_palette, low=0, high=100)

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
rects = p.rect(
    x="x",
    y="y",
    width=1,
    height=1,
    source=source,
    fill_color=transform("value", mapper),
    line_color="#f0f0f0",
    line_width=2,
)

# Add HoverTool for interactive exploration (distinctive Bokeh feature)
hover = HoverTool(renderers=[rects], tooltips=[("Cohort", "@y"), ("Period", "@x"), ("Retention", "@text")])
p.add_tools(hover)

# Add retention percentage text
p.text(
    x="x",
    y="y",
    text="text",
    source=source,
    text_align="center",
    text_baseline="middle",
    text_font_size="17pt",
    text_color="text_color",
    text_font_style="bold",
)

# Style: refined typography and spacing
p.title.text_font_size = "30pt"
p.title.align = "center"
p.title.text_color = "#2d2d2d"
p.xaxis.axis_label = "Months Since Signup"
p.yaxis.axis_label = "Signup Cohort"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_font_style = "bold"
p.yaxis.axis_label_text_font_style = "bold"
p.xaxis.axis_label_text_color = "#3a3a3a"
p.yaxis.axis_label_text_color = "#3a3a3a"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = "#4a4a4a"
p.yaxis.major_label_text_color = "#4a4a4a"
p.axis.axis_line_color = None
p.axis.major_tick_line_color = None
p.axis.minor_tick_line_color = None
p.grid.grid_line_color = None
p.background_fill_color = "#fafafa"
p.border_fill_color = "white"
p.outline_line_color = None
p.min_border_left = 80
p.min_border_right = 120
p.min_border_top = 60
p.min_border_bottom = 40

# Storytelling: annotate the retention drop-off insight
# Find the best and worst performing cohorts at Month 3
month3_retentions = {y_labels[i]: retention[i, 3] for i in range(n_cohorts) if not np.isnan(retention[i, 3])}
best_cohort = max(month3_retentions, key=month3_retentions.get)
worst_cohort = min(month3_retentions, key=month3_retentions.get)

insight_label = Label(
    x=30,
    y=30,
    x_units="screen",
    y_units="screen",
    text=(
        f"Month 3 retention ranges from {month3_retentions[worst_cohort]:.0f}% "
        f"to {month3_retentions[best_cohort]:.0f}% across cohorts"
    ),
    text_font_size="16pt",
    text_color="#666666",
    text_font_style="italic",
)
p.add_layout(insight_label)

# Add colorbar with improved spacing
color_bar = ColorBar(
    color_mapper=mapper,
    ticker=BasicTicker(desired_num_ticks=6),
    label_standoff=16,
    major_label_text_font_size="18pt",
    major_label_text_color="#4a4a4a",
    title="Retention %",
    title_text_font_size="20pt",
    title_text_font_style="bold",
    title_standoff=16,
    width=45,
    location=(0, 0),
    bar_line_color=None,
    border_line_color=None,
    background_fill_color="white",
)
p.add_layout(color_bar, "right")

# Save
export_png(p, filename="plot.png")
