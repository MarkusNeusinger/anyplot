""" pyplots.ai
gantt-basic: Basic Gantt Chart
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-27
"""

import pandas as pd
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, Legend, LegendItem
from bokeh.palettes import Category10
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Software Development Project
tasks = [
    {"task": "Requirements Analysis", "start": "2025-01-06", "end": "2025-01-17", "category": "Planning"},
    {"task": "System Design", "start": "2025-01-13", "end": "2025-01-31", "category": "Planning"},
    {"task": "Database Schema", "start": "2025-01-27", "end": "2025-02-07", "category": "Development"},
    {"task": "Backend API", "start": "2025-02-03", "end": "2025-02-28", "category": "Development"},
    {"task": "Frontend UI", "start": "2025-02-10", "end": "2025-03-14", "category": "Development"},
    {"task": "Integration", "start": "2025-03-03", "end": "2025-03-21", "category": "Development"},
    {"task": "Unit Testing", "start": "2025-02-17", "end": "2025-03-14", "category": "Testing"},
    {"task": "System Testing", "start": "2025-03-17", "end": "2025-03-28", "category": "Testing"},
    {"task": "User Acceptance", "start": "2025-03-24", "end": "2025-04-04", "category": "Testing"},
    {"task": "Documentation", "start": "2025-03-10", "end": "2025-04-04", "category": "Deployment"},
    {"task": "Deployment", "start": "2025-04-01", "end": "2025-04-11", "category": "Deployment"},
    {"task": "Training", "start": "2025-04-07", "end": "2025-04-18", "category": "Deployment"},
]

df = pd.DataFrame(tasks)
df["start"] = pd.to_datetime(df["start"])
df["end"] = pd.to_datetime(df["end"])

# Sort by start date for chronological order
df = df.sort_values(["start", "category"], ascending=[True, True]).reset_index(drop=True)

# Convert dates to numeric for plotting (milliseconds since epoch)
df["start_ms"] = df["start"].astype("int64") // 10**6
df["end_ms"] = df["end"].astype("int64") // 10**6

# Assign y positions (inverted so first task is at top)
df["y"] = list(range(len(df) - 1, -1, -1))

# Color mapping by category
categories = df["category"].unique().tolist()
color_map = {cat: Category10[10][i % 10] for i, cat in enumerate(categories)}
# Override with Python colors for first two categories
color_map[categories[0]] = "#306998"  # Python Blue
if len(categories) > 1:
    color_map[categories[1]] = "#FFD43B"  # Python Yellow
df["color"] = df["category"].map(color_map)

# Create ColumnDataSource
source = ColumnDataSource(
    data={
        "task": df["task"],
        "y": df["y"],
        "left": df["start_ms"],
        "right": df["end_ms"],
        "color": df["color"],
        "category": df["category"],
    }
)

# Create figure with extra left margin for task labels
p = figure(
    width=4800,
    height=2700,
    title="gantt-basic · bokeh · pyplots.ai",
    x_axis_type="datetime",
    y_range=(-0.5, len(df) - 0.5),
    tools="",
    toolbar_location=None,
)

# Bar height
bar_height = 0.65

# Draw Gantt bars using hbar
p.hbar(
    y="y",
    left="left",
    right="right",
    height=bar_height,
    color="color",
    alpha=0.9,
    source=source,
    line_color="#444444",
    line_width=3,
)

# Add task labels on the left side with larger font
x_range_span = df["end_ms"].max() - df["start_ms"].min()
for i, row in df.iterrows():
    y_pos = df.loc[i, "y"]
    task_name = row["task"]
    p.text(
        x=[df["start_ms"].min() - x_range_span * 0.015],
        y=[y_pos],
        text=[task_name],
        text_font_size="32pt",
        text_align="right",
        text_baseline="middle",
        text_color="#333333",
    )

# Title styling
p.title.text_font_size = "48pt"
p.title.text_font_style = "bold"
p.title.text_color = "#333333"

# X-axis styling
p.xaxis.axis_label = "Timeline"
p.xaxis.axis_label_text_font_size = "36pt"
p.xaxis.major_label_text_font_size = "28pt"
p.xaxis.axis_label_text_color = "#333333"
p.xaxis.major_label_text_color = "#333333"
p.xaxis.axis_line_width = 3
p.xaxis.major_tick_line_width = 3
p.xaxis.minor_tick_line_color = None

# Hide y-axis (task labels are added as text)
p.yaxis.visible = False

# Grid styling
p.xgrid.grid_line_color = "#cccccc"
p.xgrid.grid_line_alpha = 0.5
p.xgrid.grid_line_dash = [8, 4]
p.xgrid.grid_line_width = 2
p.ygrid.grid_line_color = None

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "white"
p.outline_line_color = None

# Extend x-range to accommodate task labels
x_min = df["start_ms"].min()
x_max = df["end_ms"].max()
x_padding = (x_max - x_min) * 0.22
p.x_range.start = x_min - x_padding
p.x_range.end = x_max + (x_max - x_min) * 0.03

# Add legend manually using dummy glyphs
legend_items = []
for cat in categories:
    dummy = p.hbar(y=[-100], left=[0], right=[1], height=0.1, color=color_map[cat], visible=False)
    legend_items.append(LegendItem(label=cat, renderers=[dummy]))

legend = Legend(items=legend_items, location="top_right")
legend.label_text_font_size = "30pt"
legend.glyph_height = 40
legend.glyph_width = 50
legend.spacing = 25
legend.padding = 30
legend.background_fill_alpha = 0.85
legend.border_line_color = "#cccccc"
legend.border_line_width = 2
p.add_layout(legend, "right")

# Save as PNG
export_png(p, filename="plot.png")

# Save as HTML for interactivity
save(p, filename="plot.html", resources=CDN, title="gantt-basic")
