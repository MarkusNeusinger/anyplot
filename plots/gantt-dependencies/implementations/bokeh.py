""" pyplots.ai
gantt-dependencies: Gantt Chart with Dependencies
Library: bokeh 3.8.2 | Python 3.14
Quality: 93/100 | Updated: 2026-02-25
"""

import pandas as pd
from bokeh.io import export_png, output_file, save
from bokeh.models import BoxAnnotation, ColumnDataSource, HoverTool, LabelSet, Legend, LegendItem
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
df["duration"] = (df["end"] - df["start"]).dt.days

# Create task lookup for dependencies
task_lookup = {row["task"]: idx for idx, row in df.iterrows()}

# Compute critical path (longest path through dependency graph)
successors = {row["task"]: [] for _, row in df.iterrows()}
for _, row in df.iterrows():
    for dep in row["depends_on"]:
        if dep in successors:
            successors[dep].append(row["task"])

# Forward pass: longest path from any root to each task's end
lp_to = {}
for _, row in df.iterrows():
    task = row["task"]
    dur = row["duration"]
    if not row["depends_on"]:
        lp_to[task] = dur
    else:
        lp_to[task] = max(lp_to[dep] for dep in row["depends_on"] if dep in lp_to) + dur

# Backward pass: longest path from each task's start to project end
lp_from = {}
for _, row in df.sort_values("end", ascending=False).iterrows():
    task = row["task"]
    dur = row["duration"]
    if not successors[task]:
        lp_from[task] = dur
    else:
        lp_from[task] = dur + max(lp_from[s] for s in successors[task])

# Critical tasks: longest path through task equals overall longest path
max_lp = max(lp_to.values())
critical_tasks = {t for t in lp_to if lp_to[t] + lp_from[t] - df.iloc[task_lookup[t]]["duration"] == max_lp}

# Refined color palette — cohesive muted tones with strong contrast on #FAFAFA
groups = ["Requirements", "Design", "Development", "Testing"]
group_colors = {
    "Requirements": "#2B6C94",  # Deep steel blue
    "Design": "#BF8B2E",  # Warm amber (replaces low-contrast yellow)
    "Development": "#3A7D44",  # Forest green
    "Testing": "#A3567D",  # Muted rose
}

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
p.title.text_color = "#2A2A2A"
p.xaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.visible = False
p.xgrid.grid_line_alpha = 0.15
p.xgrid.grid_line_dash = [6, 4]
p.ygrid.grid_line_alpha = 0.0
p.outline_line_color = None
p.background_fill_color = "#FAFAFA"

# Alternating row bands
for i in range(max_y):
    if i % 2 == 0:
        p.add_layout(
            BoxAnnotation(
                bottom=i - 0.5, top=i + 0.5, fill_color="#F0F0F0", fill_alpha=0.5, level="underlay", line_color=None
            )
        )

# Draw group span bars
group_renderers = {}
for group in groups:
    span = group_spans[group]
    y = y_positions[f"__group__{group}"]
    source = ColumnDataSource(data={"y": [y], "left": [span["start"]], "right": [span["end"]], "height": [0.7]})
    r = p.hbar(y="y", left="left", right="right", height="height", color=group_colors[group], alpha=0.25, source=source)
    group_renderers[group] = r

# Build task bar data with hover metadata
task_ys, task_lefts, task_rights = [], [], []
task_colors, task_names, task_groups = [], [], []
task_starts, task_ends, task_durations, task_deps, task_crit = [], [], [], [], []

for _, row in df.iterrows():
    task_ys.append(y_positions[row["task"]])
    task_lefts.append(row["start"])
    task_rights.append(row["end"])
    task_colors.append(group_colors[row["group"]])
    task_names.append(row["task"])
    task_groups.append(row["group"])
    task_starts.append(row["start"].strftime("%b %d, %Y"))
    task_ends.append(row["end"].strftime("%b %d, %Y"))
    task_durations.append(f"{row['duration']} days")
    deps = row["depends_on"]
    task_deps.append(", ".join(deps) if deps else "None")
    task_crit.append("\u2605 Critical Path" if row["task"] in critical_tasks else "")

task_source = ColumnDataSource(
    data={
        "y": task_ys,
        "left": task_lefts,
        "right": task_rights,
        "bar_color": task_colors,
        "task_name": task_names,
        "group_name": task_groups,
        "start_str": task_starts,
        "end_str": task_ends,
        "duration": task_durations,
        "dependencies": task_deps,
        "critical": task_crit,
    }
)

# Draw task bars (single source for HoverTool)
task_renderer = p.hbar(
    y="y",
    left="left",
    right="right",
    height=0.5,
    fill_color="bar_color",
    fill_alpha=0.9,
    line_color="white",
    line_width=1,
    source=task_source,
)

# Critical path border overlay (dark outline on critical tasks)
for _, row in df.iterrows():
    if row["task"] in critical_tasks:
        y = y_positions[row["task"]]
        src = ColumnDataSource(data={"y": [y], "left": [row["start"]], "right": [row["end"]]})
        p.hbar(
            y="y", left="left", right="right", height=0.54, fill_alpha=0, line_color="#1A1A1A", line_width=3, source=src
        )

# Draw dependency arrows with critical path emphasis
crit_arrow_xs, crit_arrow_ys = [], []
norm_arrow_xs, norm_arrow_ys = [], []
crit_head_xs, crit_head_ys = [], []
norm_head_xs, norm_head_ys = [], []

for _, row in df.iterrows():
    task_name = row["task"]
    task_y = y_positions[task_name]
    task_start_ms = row["start"].value / 1e6
    is_task_critical = task_name in critical_tasks

    for dep_name in row["depends_on"]:
        if dep_name in task_lookup:
            dep_row = df.iloc[task_lookup[dep_name]]
            dep_end_ms = dep_row["end"].value / 1e6
            dep_y = y_positions[dep_name]

            is_crit_dep = is_task_critical and dep_name in critical_tasks
            h_offset = 1.0 * 24 * 60 * 60 * 1000  # 1 day in ms

            if task_y != dep_y:
                mid_x = dep_end_ms + h_offset
                xs = [dep_end_ms, mid_x, mid_x, task_start_ms]
                ys = [dep_y, dep_y, task_y, task_y]
            else:
                xs = [dep_end_ms, task_start_ms]
                ys = [dep_y, task_y]

            arrow_size = 1.5 * 24 * 60 * 60 * 1000
            hxs = [task_start_ms - arrow_size, task_start_ms, task_start_ms - arrow_size]
            hys = [task_y - 0.12, task_y, task_y + 0.12]

            if is_crit_dep:
                crit_arrow_xs.append(xs)
                crit_arrow_ys.append(ys)
                crit_head_xs.append(hxs)
                crit_head_ys.append(hys)
            else:
                norm_arrow_xs.append(xs)
                norm_arrow_ys.append(ys)
                norm_head_xs.append(hxs)
                norm_head_ys.append(hys)

# Non-critical arrows (light, drawn first)
dep_renderer = None
if norm_arrow_xs:
    dep_renderer = p.multi_line(xs=norm_arrow_xs, ys=norm_arrow_ys, line_color="#BBBBBB", line_width=2, line_alpha=0.45)
    p.patches(
        xs=norm_head_xs, ys=norm_head_ys, fill_color="#BBBBBB", fill_alpha=0.45, line_color="#BBBBBB", line_width=1
    )

# Critical path arrows (bold, drawn on top)
crit_dep_renderer = None
if crit_arrow_xs:
    crit_dep_renderer = p.multi_line(
        xs=crit_arrow_xs, ys=crit_arrow_ys, line_color="#1A1A1A", line_width=4, line_alpha=0.8
    )
    p.patches(
        xs=crit_head_xs, ys=crit_head_ys, fill_color="#1A1A1A", fill_alpha=0.8, line_color="#1A1A1A", line_width=1
    )

# Y-axis labels
group_label_ys, group_label_texts = [], []
task_label_ys, task_label_texts = [], []

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
        text_color="#1A1A1A",
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

# X range
x_min = df["start"].min() - pd.Timedelta(days=14)
x_max = df["end"].max() + pd.Timedelta(days=2)
p.x_range.start = x_min
p.x_range.end = x_max

# Legend with phase colors, dependency, and critical path
legend_items = []
for group in groups:
    legend_items.append(LegendItem(label=group, renderers=[group_renderers[group]]))
if dep_renderer:
    legend_items.append(LegendItem(label="Dependency", renderers=[dep_renderer]))
if crit_dep_renderer:
    legend_items.append(LegendItem(label="Critical Path", renderers=[crit_dep_renderer]))

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

# Remove toolbar for PNG
p.toolbar_location = None

# Save PNG
export_png(p, filename="plot.png")

# Add HoverTool and enable toolbar for interactive HTML
hover = HoverTool(
    renderers=[task_renderer],
    tooltips=[
        ("Task", "@task_name"),
        ("Phase", "@group_name"),
        ("Start", "@start_str"),
        ("End", "@end_str"),
        ("Duration", "@duration"),
        ("Dependencies", "@dependencies"),
        ("Status", "@critical"),
    ],
)
p.add_tools(hover)
p.toolbar_location = "above"

# Save HTML
output_file("plot.html", title="gantt-dependencies \u00b7 bokeh \u00b7 pyplots.ai")
save(p)
