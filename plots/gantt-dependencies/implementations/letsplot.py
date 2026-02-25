""" pyplots.ai
gantt-dependencies: Gantt Chart with Dependencies
Library: letsplot 4.8.2 | Python 3.14
Quality: 84/100 | Updated: 2026-02-25
"""

import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - Software development project with phases and dependencies
tasks_data = [
    # Requirements phase
    {
        "task": "Gather Requirements",
        "start": "2024-01-01",
        "end": "2024-01-08",
        "group": "Requirements",
        "depends_on": [],
    },
    {
        "task": "Stakeholder Interviews",
        "start": "2024-01-03",
        "end": "2024-01-10",
        "group": "Requirements",
        "depends_on": [("Gather Requirements", "start-to-start")],
    },
    {
        "task": "Document Specs",
        "start": "2024-01-10",
        "end": "2024-01-17",
        "group": "Requirements",
        "depends_on": [("Stakeholder Interviews", "finish-to-start")],
    },
    # Design phase
    {
        "task": "Architecture Design",
        "start": "2024-01-17",
        "end": "2024-01-27",
        "group": "Design",
        "depends_on": [("Document Specs", "finish-to-start")],
    },
    {
        "task": "UI/UX Mockups",
        "start": "2024-01-20",
        "end": "2024-01-30",
        "group": "Design",
        "depends_on": [("Document Specs", "finish-to-start")],
    },
    {
        "task": "Database Schema",
        "start": "2024-01-22",
        "end": "2024-01-31",
        "group": "Design",
        "depends_on": [("Architecture Design", "start-to-start")],
    },
    # Development phase
    {
        "task": "Backend API",
        "start": "2024-01-31",
        "end": "2024-02-21",
        "group": "Development",
        "depends_on": [("Database Schema", "finish-to-start"), ("Architecture Design", "finish-to-start")],
    },
    {
        "task": "Frontend Components",
        "start": "2024-01-30",
        "end": "2024-02-18",
        "group": "Development",
        "depends_on": [("UI/UX Mockups", "finish-to-start")],
    },
    {
        "task": "Integration",
        "start": "2024-02-18",
        "end": "2024-02-28",
        "group": "Development",
        "depends_on": [("Backend API", "finish-to-finish"), ("Frontend Components", "finish-to-start")],
    },
    # Testing phase
    {
        "task": "Unit Testing",
        "start": "2024-02-10",
        "end": "2024-02-24",
        "group": "Testing",
        "depends_on": [("Backend API", "start-to-start")],
    },
    {
        "task": "Integration Testing",
        "start": "2024-02-28",
        "end": "2024-03-08",
        "group": "Testing",
        "depends_on": [("Integration", "finish-to-start")],
    },
    {
        "task": "User Acceptance",
        "start": "2024-03-08",
        "end": "2024-03-15",
        "group": "Testing",
        "depends_on": [("Integration Testing", "finish-to-start")],
    },
]

df = pd.DataFrame(tasks_data)
df["start"] = pd.to_datetime(df["start"])
df["end"] = pd.to_datetime(df["end"])

# Group ordering and colors
group_order = ["Requirements", "Design", "Development", "Testing"]
group_colors = {"Requirements": "#306998", "Design": "#E8A838", "Development": "#2CA02C", "Testing": "#9467BD"}

# Build y positions — assign in reading order top-to-bottom, then flip
y_positions = {}
task_info = {}
reading_order = []

for group in group_order:
    group_tasks = df[df["group"] == group]
    reading_order.append(group)
    task_info[group] = {
        "start": group_tasks["start"].min(),
        "end": group_tasks["end"].max(),
        "is_group": True,
        "group": group,
    }
    for _, row in group_tasks.sort_values("start").iterrows():
        reading_order.append(row["task"])
        task_info[row["task"]] = {
            "start": row["start"],
            "end": row["end"],
            "is_group": False,
            "group": row["group"],
            "depends_on": row["depends_on"],
        }

# Flip: first in reading order gets highest y (top of chart)
n = len(reading_order)
for i, name in enumerate(reading_order):
    y_positions[name] = n - 1 - i

# Prepare plot dataframes using native datetimes (no timestamp conversion)
plot_data = []
for name, y in y_positions.items():
    info = task_info[name]
    plot_data.append(
        {
            "task": name,
            "y": y,
            "start": info["start"],
            "end": info["end"],
            "is_group": info["is_group"],
            "group": info["group"],
            "duration": (info["end"] - info["start"]).days,
        }
    )

plot_df = pd.DataFrame(plot_data)
groups_df = plot_df[plot_df["is_group"]]
tasks_df = plot_df[~plot_df["is_group"]]

# Colorblind-safe dependency arrow colors (orange/blue/purple instead of red/blue/green)
dep_colors = {"finish-to-start": "#D95F02", "start-to-start": "#3498DB", "finish-to-finish": "#7570B3"}

# Build arrow data with native datetimes
arrows_data = []
for task_name, info in task_info.items():
    if info["is_group"] or not info.get("depends_on"):
        continue
    for dep_name, dep_type in info["depends_on"]:
        if dep_name not in task_info:
            continue
        dep_info = task_info[dep_name]
        if dep_type == "start-to-start":
            x_from, x_to = dep_info["start"], info["start"]
        elif dep_type == "finish-to-finish":
            x_from, x_to = dep_info["end"], info["end"]
        else:
            x_from, x_to = dep_info["end"], info["start"]
        arrows_data.append(
            {
                "x": x_from,
                "y": y_positions[dep_name],
                "xend": x_to,
                "yend": y_positions[task_name],
                "dep_type": dep_type,
                "from_task": dep_name,
                "to_task": task_name,
            }
        )

arrows_df = pd.DataFrame(arrows_data) if arrows_data else None

# Build plot
x_min = plot_df["start"].min()
x_max = plot_df["end"].max()
y_pos = n

plot = ggplot()

# Alternating group background bands for visual separation
for i, group in enumerate(group_order):
    group_task_ys = [y_positions[t] for t, info in task_info.items() if info["group"] == group]
    y_lo = min(group_task_ys) - 0.45
    y_hi = max(group_task_ys) + 0.45
    band_color = "#F7F9FC" if i % 2 == 0 else "#FFFFFF"
    band_df = pd.DataFrame(
        [{"xmin": x_min - pd.Timedelta(days=18), "xmax": x_max + pd.Timedelta(days=5), "ymin": y_lo, "ymax": y_hi}]
    )
    plot += geom_rect(aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"), data=band_df, fill=band_color, alpha=0.8)

# Group header bars with interactive tooltips
plot += geom_segment(
    aes(x="start", xend="end", y="y", yend="y"),
    data=groups_df,
    size=14,
    color="#1a365d",
    alpha=0.95,
    tooltips=layer_tooltips().title("@task").line("@start — @end").line("Duration: @duration days"),
)

# Task bars colored by group with interactive tooltips
task_tooltips = (
    layer_tooltips().title("@task").line("@start — @end").line("Group: @group").line("Duration: @duration days")
)
for group in group_order:
    gdf = tasks_df[tasks_df["group"] == group]
    if not gdf.empty:
        plot += geom_segment(
            aes(x="start", xend="end", y="y", yend="y"),
            data=gdf,
            size=8,
            color=group_colors[group],
            alpha=0.85,
            tooltips=task_tooltips,
        )

# Dependency arrows by type with interactive tooltips
if arrows_df is not None and not arrows_df.empty:
    for dep_type, color in dep_colors.items():
        type_df = arrows_df[arrows_df["dep_type"] == dep_type]
        if not type_df.empty:
            plot += geom_segment(
                aes(x="x", xend="xend", y="y", yend="yend"),
                data=type_df,
                size=1.5,
                color=color,
                alpha=0.85,
                arrow=arrow(angle=25, length=10, type="closed"),
                tooltips=layer_tooltips().line("@from_task → @to_task").line("Type: @dep_type"),
            )

# Labels: task names on left, group names on right
label_offset = pd.Timedelta(days=1)
group_labels = groups_df.assign(label_x=groups_df["end"] + label_offset)
task_labels_df = tasks_df.assign(label_x=tasks_df["start"] - label_offset)

plot += geom_text(
    aes(x="label_x", y="y", label="task"), data=group_labels, hjust=0, size=12, fontface="bold", color="#1a365d"
)
plot += geom_text(aes(x="label_x", y="y", label="task"), data=task_labels_df, hjust=1, size=12, color="#333333")

# Dependency type legend (data-driven)
legend_x = x_max - pd.Timedelta(days=12)
legend_xend = legend_x + pd.Timedelta(days=5)
legend_text_x = legend_xend + pd.Timedelta(days=1)
legend_items = [
    ("Finish-to-Start", "finish-to-start", -2.0),
    ("Start-to-Start", "start-to-start", -2.9),
    ("Finish-to-Finish", "finish-to-finish", -3.8),
]

plot += geom_text(
    aes(x="x", y="y", label="label"),
    data=pd.DataFrame([{"x": legend_x, "y": -1.1, "label": "Dependencies:"}]),
    hjust=0,
    size=12,
    fontface="bold",
    color="#222222",
)

legend_seg_df = pd.DataFrame([{"x": legend_x, "xend": legend_xend, "y": y} for _, _, y in legend_items])
legend_lbl_df = pd.DataFrame([{"x": legend_text_x, "y": y, "label": label} for label, _, y in legend_items])

for (label, dep_type, y), (_, seg_row) in zip(legend_items, legend_seg_df.iterrows()):
    plot += geom_segment(
        aes(x="x", xend="xend", y="y", yend="y"),
        data=pd.DataFrame([seg_row]),
        size=1.5,
        color=dep_colors[dep_type],
        arrow=arrow(angle=25, length=10, type="closed"),
    )

plot += geom_text(aes(x="x", y="y", label="label"), data=legend_lbl_df, hjust=0, size=11, color="#333333")

# Native datetime axis and theme
plot += scale_x_datetime(format="%b %d", limits=[x_min - pd.Timedelta(days=18), x_max + pd.Timedelta(days=12)])
plot += scale_y_continuous(breaks=[], labels=[], limits=[-5.0, y_pos + 0.5])
plot += labs(x="Timeline", y="", title="gantt-dependencies \u00b7 letsplot \u00b7 pyplots.ai")
plot += theme_minimal()
plot += theme(
    axis_title_x=element_text(size=22),
    axis_title_y=element_blank(),
    axis_text_x=element_text(size=18, angle=45),
    axis_text_y=element_blank(),
    plot_title=element_text(size=28),
    panel_grid_major_y=element_blank(),
    panel_grid_minor=element_blank(),
    panel_grid_major_x=element_line(color="#E0E4E8", size=0.5),
)
plot += ggsize(1600, 900)

# Save
ggsave(plot, "plot.png", scale=3)
ggsave(plot, "plot.html")
