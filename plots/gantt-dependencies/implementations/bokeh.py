""" pyplots.ai
gantt-dependencies: Gantt Chart with Dependencies
Library: bokeh 3.8.2 | Python 3.14
Quality: 87/100 | Updated: 2026-02-25
"""

import pandas as pd
from bokeh.io import export_png, output_file, save
from bokeh.models import BoxAnnotation, ColumnDataSource, LabelSet, Legend, LegendItem
from bokeh.plotting import figure


# Data - Software development project with dependencies
tasks_data = [
    # Requirements Phase
    {
        "task": "Requirements Gathering",
        "start": "2026-01-06",
        "end": "2026-01-10",
        "group": "Requirements",
        "depends_on": [],
    },
    {
        "task": "Stakeholder Review",
        "start": "2026-01-13",
        "end": "2026-01-15",
        "group": "Requirements",
        "depends_on": ["Requirements Gathering"],
    },
    {
        "task": "Requirements Sign-off",
        "start": "2026-01-16",
        "end": "2026-01-17",
        "group": "Requirements",
        "depends_on": ["Stakeholder Review"],
    },
    # Design Phase
    {
        "task": "System Architecture",
        "start": "2026-01-20",
        "end": "2026-01-24",
        "group": "Design",
        "depends_on": ["Requirements Sign-off"],
    },
    {
        "task": "Database Design",
        "start": "2026-01-27",
        "end": "2026-01-30",
        "group": "Design",
        "depends_on": ["System Architecture"],
    },
    {
        "task": "UI/UX Design",
        "start": "2026-01-27",
        "end": "2026-01-31",
        "group": "Design",
        "depends_on": ["System Architecture"],
    },
    # Development Phase
    {
        "task": "Backend Core",
        "start": "2026-02-03",
        "end": "2026-02-14",
        "group": "Development",
        "depends_on": ["Database Design"],
    },
    {
        "task": "Frontend Core",
        "start": "2026-02-03",
        "end": "2026-02-12",
        "group": "Development",
        "depends_on": ["UI/UX Design"],
    },
    {
        "task": "API Integration",
        "start": "2026-02-17",
        "end": "2026-02-21",
        "group": "Development",
        "depends_on": ["Backend Core", "Frontend Core"],
    },
    # Testing Phase
    {
        "task": "Unit Testing",
        "start": "2026-02-17",
        "end": "2026-02-21",
        "group": "Testing",
        "depends_on": ["Backend Core"],
    },
    {
        "task": "Integration Testing",
        "start": "2026-02-24",
        "end": "2026-02-28",
        "group": "Testing",
        "depends_on": ["API Integration", "Unit Testing"],
    },
    {
        "task": "User Acceptance",
        "start": "2026-03-03",
        "end": "2026-03-07",
        "group": "Testing",
        "depends_on": ["Integration Testing"],
    },
]

# Convert to DataFrame
df = pd.DataFrame(tasks_data)
df["start"] = pd.to_datetime(df["start"])
df["end"] = pd.to_datetime(df["end"])

# Create task lookup for dependencies
task_lookup = {row["task"]: idx for idx, row in df.iterrows()}

# Define groups and colors
groups = ["Requirements", "Design", "Development", "Testing"]
group_colors = {"Requirements": "#306998", "Design": "#FFD43B", "Development": "#4CAF50", "Testing": "#E91E63"}

# Calculate group spans
group_spans = {}
for group in groups:
    group_df = df[df["group"] == group]
    group_spans[group] = {"start": group_df["start"].min(), "end": group_df["end"].max()}

# Build y-positions with group headers
y_positions = {}
y_labels = []
y_is_group = []
current_y = 0

for group in groups:
    y_positions[f"__group__{group}"] = current_y
    y_labels.append((current_y, group))
    y_is_group.append(True)
    current_y += 1
    group_tasks = df[df["group"] == group]["task"].tolist()
    for task in group_tasks:
        y_positions[task] = current_y
        y_labels.append((current_y, f"   {task}"))
        y_is_group.append(False)
        current_y += 1

max_y = current_y

# Create figure
p = figure(
    width=4800,
    height=2700,
    x_axis_type="datetime",
    y_range=(max_y + 0.5, -0.5),
    title="gantt-dependencies \u00b7 bokeh \u00b7 pyplots.ai",
    x_axis_label="Timeline (Weeks)",
    tools="",
)

# Style
p.title.text_font_size = "42pt"
p.title.text_color = "#333333"
p.xaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.visible = False
p.xgrid.grid_line_alpha = 0.15
p.xgrid.grid_line_dash = [6, 4]
p.ygrid.grid_line_alpha = 0.0
p.outline_line_color = None
p.background_fill_color = "#FAFAFA"

# Alternating row bands for readability
for i in range(max_y):
    if i % 2 == 0:
        p.add_layout(
            BoxAnnotation(
                bottom=i - 0.5, top=i + 0.5, fill_color="#F0F0F0", fill_alpha=0.5, level="underlay", line_color=None
            )
        )

# Draw group span bars (lighter background)
group_renderers = {}
for group in groups:
    span = group_spans[group]
    y = y_positions[f"__group__{group}"]
    source = ColumnDataSource(data={"y": [y], "left": [span["start"]], "right": [span["end"]], "height": [0.7]})
    r = p.hbar(y="y", left="left", right="right", height="height", color=group_colors[group], alpha=0.3, source=source)
    group_renderers[group] = r

# Draw task bars
for _, row in df.iterrows():
    y = y_positions[row["task"]]
    source = ColumnDataSource(data={"y": [y], "left": [row["start"]], "right": [row["end"]], "height": [0.5]})
    p.hbar(
        y="y",
        left="left",
        right="right",
        height="height",
        color=group_colors[row["group"]],
        alpha=0.9,
        line_color="white",
        line_width=1,
        source=source,
    )

# Draw dependency arrows (finish-to-start)
arrow_xs = []
arrow_ys = []
arrowhead_xs = []
arrowhead_ys = []

dep_color = "#666666"

for _, row in df.iterrows():
    task_name = row["task"]
    task_y = y_positions[task_name]
    task_start_ms = row["start"].value / 1e6

    for dep_name in row["depends_on"]:
        if dep_name in task_lookup:
            dep_row = df.iloc[task_lookup[dep_name]]
            dep_end_ms = dep_row["end"].value / 1e6
            dep_y = y_positions[dep_name]

            # Horizontal offset for the vertical drop segment
            h_offset = 1.0 * 24 * 60 * 60 * 1000  # 1 day in ms

            if task_y != dep_y:
                # Route: right from dep end → down/up → horizontal → into successor start
                mid_x = dep_end_ms + h_offset
                arrow_xs.append([dep_end_ms, mid_x, mid_x, task_start_ms])
                arrow_ys.append([dep_y, dep_y, task_y, task_y])
            else:
                arrow_xs.append([dep_end_ms, task_start_ms])
                arrow_ys.append([dep_y, task_y])

            # Arrowhead pointing right into the successor bar
            arrow_size = 1.5 * 24 * 60 * 60 * 1000  # 1.5 days in ms
            arrowhead_xs.append([task_start_ms - arrow_size, task_start_ms, task_start_ms - arrow_size])
            arrowhead_ys.append([task_y - 0.12, task_y, task_y + 0.12])

# Draw dependency lines
dep_renderer = None
if arrow_xs:
    dep_renderer = p.multi_line(xs=arrow_xs, ys=arrow_ys, line_color=dep_color, line_width=3, line_alpha=0.6)

# Draw arrowheads
if arrowhead_xs:
    p.patches(
        xs=arrowhead_xs, ys=arrowhead_ys, fill_color=dep_color, fill_alpha=0.7, line_color=dep_color, line_width=1
    )

# Y-axis labels — group headers bold, task names regular
group_label_ys = []
group_label_texts = []
task_label_ys = []
task_label_texts = []

for (y, label), is_group in zip(y_labels, y_is_group, strict=True):
    if is_group:
        group_label_ys.append(y)
        group_label_texts.append(label)
    else:
        task_label_ys.append(y)
        task_label_texts.append(label)

label_x = df["start"].min() - pd.Timedelta(days=1)

# Group header labels (bold, larger)
group_label_source = ColumnDataSource(
    data={"y": group_label_ys, "text": group_label_texts, "x": [label_x] * len(group_label_ys)}
)
p.add_layout(
    LabelSet(
        x="x",
        y="y",
        text="text",
        source=group_label_source,
        text_font_size="24pt",
        text_font_style="bold",
        text_align="right",
        x_offset=-10,
        text_baseline="middle",
        text_color="#222222",
    )
)

# Task labels (regular, slightly smaller)
task_label_source = ColumnDataSource(
    data={"y": task_label_ys, "text": task_label_texts, "x": [label_x] * len(task_label_ys)}
)
p.add_layout(
    LabelSet(
        x="x",
        y="y",
        text="text",
        source=task_label_source,
        text_font_size="20pt",
        text_align="right",
        x_offset=-10,
        text_baseline="middle",
        text_color="#444444",
    )
)

# Adjust x range for labels
x_min = df["start"].min() - pd.Timedelta(days=14)
x_max = df["end"].max() + pd.Timedelta(days=3)
p.x_range.start = x_min
p.x_range.end = x_max

# Legend with phase colors and dependency line
legend_items = []
for group in groups:
    legend_items.append(LegendItem(label=group, renderers=[group_renderers[group]]))
if dep_renderer:
    legend_items.append(LegendItem(label="Dependency (finish-to-start)", renderers=[dep_renderer]))

legend = Legend(
    items=legend_items,
    location="top_right",
    label_text_font_size="20pt",
    spacing=12,
    padding=20,
    background_fill_alpha=0.85,
    border_line_color="#cccccc",
    border_line_width=1,
)
p.add_layout(legend)

# Remove toolbar
p.toolbar_location = None

# Save PNG
export_png(p, filename="plot.png")

# Save HTML (interactive)
output_file("plot.html", title="gantt-dependencies \u00b7 bokeh \u00b7 pyplots.ai")
save(p)
