""" pyplots.ai
gantt-dependencies: Gantt Chart with Dependencies
Library: letsplot 4.8.2 | Python 3.14
Quality: 87/100 | Updated: 2026-02-25
"""

import pandas as pd
from lets_plot import *
from lets_plot.export import ggsave


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

# Group ordering and curated color palette (muted, harmonious, colorblind-safe)
group_order = ["Requirements", "Design", "Development", "Testing"]
group_colors = {"Requirements": "#4878A8", "Design": "#D4913B", "Development": "#45A5A5", "Testing": "#8B6BAD"}

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

# Prepare plot dataframes using native datetimes
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

# Colorblind-safe dependency arrow colors
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

plot = ggplot()

# Alternating group background bands (softened tones)
for i, group in enumerate(group_order):
    group_task_ys = [y_positions[t] for t, info in task_info.items() if info["group"] == group]
    y_lo = min(group_task_ys) - 0.45
    y_hi = max(group_task_ys) + 0.45
    band_color = "#F0F4F8" if i % 2 == 0 else "#FAFBFC"
    band_df = pd.DataFrame(
        [{"xmin": x_min - pd.Timedelta(days=22), "xmax": x_max + pd.Timedelta(days=5), "ymin": y_lo, "ymax": y_hi}]
    )
    plot += geom_rect(aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"), data=band_df, fill=band_color, alpha=0.8)

# Group header bars with interactive tooltips
plot += geom_segment(
    aes(x="start", xend="end", y="y", yend="y"),
    data=groups_df,
    size=14,
    color="#1a365d",
    alpha=0.95,
    tooltips=layer_tooltips().title("@task").line("@start \u2014 @end").line("Duration: @duration days"),
)

# Task bars — single layer with color mapped to group via scale_color_manual
task_tooltips = (
    layer_tooltips().title("@task").line("@start \u2014 @end").line("Group: @group").line("Duration: @duration days")
)
plot += geom_segment(
    aes(x="start", xend="end", y="y", yend="y", color="group"),
    data=tasks_df,
    size=8,
    alpha=0.85,
    tooltips=task_tooltips,
    show_legend=False,
)
plot += scale_color_manual(values=[group_colors[g] for g in group_order], breaks=group_order)

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
                tooltips=layer_tooltips().line("@from_task \u2192 @to_task").line("Type: @dep_type"),
            )

# Labels: task names on left, group names on right
label_offset = pd.Timedelta(days=1)
group_labels = groups_df.assign(label_x=groups_df["end"] + label_offset)
task_labels_df = tasks_df.assign(label_x=tasks_df["start"] - label_offset)

plot += geom_text(
    aes(x="label_x", y="y", label="task"), data=group_labels, hjust=0, size=14, fontface="bold", color="#1a365d"
)
plot += geom_text(aes(x="label_x", y="y", label="task"), data=task_labels_df, hjust=1, size=14, color="#2D3748")

# Dependency type legend (compact)
legend_x = x_max - pd.Timedelta(days=12)
legend_xend = legend_x + pd.Timedelta(days=5)
legend_text_x = legend_xend + pd.Timedelta(days=1)
legend_entries = [
    ("Finish-to-Start", "finish-to-start", -1.5),
    ("Start-to-Start", "start-to-start", -2.2),
    ("Finish-to-Finish", "finish-to-finish", -2.9),
]

plot += geom_text(
    aes(x="x", y="y", label="label"),
    data=pd.DataFrame([{"x": legend_x, "y": -0.7, "label": "Dependencies:"}]),
    hjust=0,
    size=13,
    fontface="bold",
    color="#1a365d",
)

for label, dep_type, y in legend_entries:
    seg_df = pd.DataFrame([{"x": legend_x, "xend": legend_xend, "y": y}])
    plot += geom_segment(
        aes(x="x", xend="xend", y="y", yend="y"),
        data=seg_df,
        size=1.5,
        color=dep_colors[dep_type],
        arrow=arrow(angle=25, length=10, type="closed"),
    )

legend_lbl_df = pd.DataFrame([{"x": legend_text_x, "y": y, "label": label} for label, _, y in legend_entries])
plot += geom_text(aes(x="x", y="y", label="label"), data=legend_lbl_df, hjust=0, size=13, color="#2D3748")

# Native datetime axis and refined theme
# Explicit weekly breaks starting from first task date (avoids empty Dec labels)
x_breaks = pd.date_range(start=x_min, end=x_max + pd.Timedelta(days=10), freq="W-MON").tolist()
plot += scale_x_datetime(
    format="%b %d", limits=[x_min - pd.Timedelta(days=22), x_max + pd.Timedelta(days=12)], breaks=x_breaks
)
plot += scale_y_continuous(breaks=[], labels=[], limits=[-3.8, n + 0.5])
plot += labs(
    x="Project Timeline (2024)",
    y="",
    title="gantt-dependencies \u00b7 letsplot \u00b7 pyplots.ai",
    subtitle="Software development lifecycle \u2014 task dependencies and critical path across phases",
)
plot += theme_minimal()
plot += theme(
    axis_title_x=element_text(size=22, color="#4A5568"),
    axis_title_y=element_blank(),
    axis_text_x=element_text(size=18, angle=45, color="#4A5568"),
    axis_text_y=element_blank(),
    plot_title=element_text(size=32, face="bold", color="#1a365d"),
    plot_subtitle=element_text(size=20, color="#4A5568"),
    panel_grid_major_y=element_blank(),
    panel_grid_minor=element_blank(),
    panel_grid_major_x=element_line(color="#E2E8F0", size=0.4),
    plot_margin=[30, 20, 20, 120],
)
plot += ggsize(1600, 900)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
