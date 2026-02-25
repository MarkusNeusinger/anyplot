""" pyplots.ai
gantt-dependencies: Gantt Chart with Dependencies
Library: plotnine 0.15.3 | Python 3.14
Quality: 89/100 | Updated: 2026-02-25
"""

from datetime import datetime, timedelta

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_datetime,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - Software development project with dependencies
# All dependent tasks start at or after the end of their predecessors (finish-to-start)
tasks_data = [
    # Requirements Phase
    {
        "task": "Gather Requirements",
        "start": datetime(2024, 1, 1),
        "end": datetime(2024, 1, 10),
        "group": "Requirements",
        "depends_on": [],
    },
    {
        "task": "Document Specs",
        "start": datetime(2024, 1, 10),
        "end": datetime(2024, 1, 17),
        "group": "Requirements",
        "depends_on": ["Gather Requirements"],
    },
    {
        "task": "Review & Approve",
        "start": datetime(2024, 1, 17),
        "end": datetime(2024, 1, 20),
        "group": "Requirements",
        "depends_on": ["Document Specs"],
    },
    # Design Phase
    {
        "task": "System Architecture",
        "start": datetime(2024, 1, 20),
        "end": datetime(2024, 1, 30),
        "group": "Design",
        "depends_on": ["Review & Approve"],
    },
    {
        "task": "Database Design",
        "start": datetime(2024, 1, 30),
        "end": datetime(2024, 2, 7),
        "group": "Design",
        "depends_on": ["System Architecture"],
    },
    {
        "task": "UI/UX Mockups",
        "start": datetime(2024, 1, 20),
        "end": datetime(2024, 2, 3),
        "group": "Design",
        "depends_on": ["Review & Approve"],
    },
    # Development Phase
    {
        "task": "Backend API",
        "start": datetime(2024, 2, 7),
        "end": datetime(2024, 2, 28),
        "group": "Development",
        "depends_on": ["Database Design"],
    },
    {
        "task": "Frontend Components",
        "start": datetime(2024, 2, 3),
        "end": datetime(2024, 2, 25),
        "group": "Development",
        "depends_on": ["UI/UX Mockups"],
    },
    {
        "task": "Integration",
        "start": datetime(2024, 2, 28),
        "end": datetime(2024, 3, 8),
        "group": "Development",
        "depends_on": ["Backend API", "Frontend Components"],
    },
    # Testing Phase
    {
        "task": "Unit Testing",
        "start": datetime(2024, 2, 28),
        "end": datetime(2024, 3, 8),
        "group": "Testing",
        "depends_on": ["Backend API"],
    },
    {
        "task": "Integration Testing",
        "start": datetime(2024, 3, 8),
        "end": datetime(2024, 3, 15),
        "group": "Testing",
        "depends_on": ["Integration"],
    },
    {
        "task": "User Acceptance",
        "start": datetime(2024, 3, 15),
        "end": datetime(2024, 3, 21),
        "group": "Testing",
        "depends_on": ["Integration Testing"],
    },
]

df = pd.DataFrame(tasks_data)

# Differentiated color palette - colorblind-safe with distinct hues
group_colors = {
    "Requirements": "#306998",  # Deep blue
    "Design": "#2A9D8F",  # Teal (distinct from blue)
    "Development": "#E9A820",  # Amber
    "Testing": "#7B2D8E",  # Purple
}

# Critical path: longest dependency chain through the project
# Gather Req → Doc Specs → Review → Sys Arch → DB Design → Backend API → Integration → Int Testing → UAT
critical_path_tasks = {
    "Gather Requirements",
    "Document Specs",
    "Review & Approve",
    "System Architecture",
    "Database Design",
    "Backend API",
    "Integration",
    "Integration Testing",
    "User Acceptance",
}

# Create ordered task list with group headers (top to bottom)
group_order = ["Requirements", "Design", "Development", "Testing"]
task_labels = {}
y_pos = 0
group_positions = {}
task_positions = {}

for grp in group_order:
    group_label = f"\u25b8 {grp}"
    group_positions[grp] = y_pos
    task_labels[y_pos] = group_label
    y_pos += 1

    group_tasks = df[df["group"] == grp]
    for _, task_row in group_tasks.iterrows():
        task_label = f"   {task_row['task']}"
        task_positions[task_row["task"]] = y_pos
        task_labels[y_pos] = task_label
        y_pos += 1

# Calculate group aggregates
group_data = []
for grp in group_order:
    group_tasks = df[df["group"] == grp]
    group_data.append(
        {"y": group_positions[grp], "start": group_tasks["start"].min(), "end": group_tasks["end"].max(), "group": grp}
    )

# Create task data with y positions, split into critical path and non-critical
critical_task_data = []
normal_task_data = []
for _, task_row in df.iterrows():
    entry = {
        "y": task_positions[task_row["task"]],
        "start": task_row["start"],
        "end": task_row["end"],
        "group": task_row["group"],
    }
    if task_row["task"] in critical_path_tasks:
        critical_task_data.append(entry)
    else:
        normal_task_data.append(entry)

# Create DataFrames for plotting
phase_order = pd.CategoricalDtype(categories=group_order, ordered=True)
groups_df = pd.DataFrame(group_data)
groups_df["group"] = groups_df["group"].astype(phase_order)

critical_df = pd.DataFrame(critical_task_data)
critical_df["group"] = critical_df["group"].astype(phase_order)

normal_df = pd.DataFrame(normal_task_data)
normal_df["group"] = normal_df["group"].astype(phase_order)

# Build dependency arrows as L-shaped connectors
arrows_data = []
arrowheads_data = []
arrow_size_days = 1.8

for _, row in df.iterrows():
    if row["depends_on"]:
        for dep_name in row["depends_on"]:
            if dep_name in task_positions:
                dep_row = df[df["task"] == dep_name].iloc[0]
                x_start = dep_row["end"]
                x_end = row["start"]
                y_start = task_positions[dep_name]
                y_end = task_positions[row["task"]]

                is_critical = dep_name in critical_path_tasks and row["task"] in critical_path_tasks

                # Vertical segment
                arrows_data.append(
                    {"x_start": x_start, "x_end": x_start, "y_start": y_start, "y_end": y_end, "critical": is_critical}
                )
                # Horizontal segment
                arrows_data.append(
                    {
                        "x_start": x_start,
                        "x_end": x_end - timedelta(days=arrow_size_days * 0.3),
                        "y_start": y_end,
                        "y_end": y_end,
                        "critical": is_critical,
                    }
                )

                # Arrowhead (V pointing right)
                arrow_tip_x = x_end
                arrow_base_x = x_end - timedelta(days=arrow_size_days)
                arrow_wing = 0.28

                arrowheads_data.append(
                    {
                        "x_start": arrow_base_x,
                        "x_end": arrow_tip_x,
                        "y_start": y_end - arrow_wing,
                        "y_end": y_end,
                        "critical": is_critical,
                    }
                )
                arrowheads_data.append(
                    {
                        "x_start": arrow_base_x,
                        "x_end": arrow_tip_x,
                        "y_start": y_end + arrow_wing,
                        "y_end": y_end,
                        "critical": is_critical,
                    }
                )

arrows_df = pd.DataFrame(arrows_data)
arrowheads_df = pd.DataFrame(arrowheads_data)

# Split arrows into critical and non-critical
crit_arrows = arrows_df[arrows_df["critical"]]
norm_arrows = arrows_df[~arrows_df["critical"]]
crit_heads = arrowheads_df[arrowheads_df["critical"]]
norm_heads = arrowheads_df[~arrowheads_df["critical"]]

# Milestone markers at phase handoff dates
milestones = pd.DataFrame(
    [
        {"x": datetime(2024, 1, 20), "y": task_positions["Review & Approve"], "label": "Design Start"},
        {"x": datetime(2024, 2, 7), "y": task_positions["Database Design"], "label": "Dev Start"},
        {"x": datetime(2024, 2, 28), "y": task_positions["Backend API"], "label": "Testing Start"},
        {"x": datetime(2024, 3, 21), "y": task_positions["User Acceptance"], "label": "Launch"},
    ]
)

# Y-axis configuration
y_breaks = list(task_labels.keys())
y_labels_list = [task_labels[y] for y in y_breaks]

# Build the plot using grammar of graphics layer composition
plot = (
    ggplot()
    # Non-critical task bars (subdued)
    + geom_segment(
        data=normal_df,
        mapping=aes(x="start", xend="end", y="y", yend="y", color="group"),
        size=9,
        lineend="butt",
        alpha=0.5,
    )
    # Critical path task bars (prominent)
    + geom_segment(
        data=critical_df,
        mapping=aes(x="start", xend="end", y="y", yend="y", color="group"),
        size=11,
        lineend="butt",
        alpha=1.0,
    )
    # Group aggregate bars (thicker, bold)
    + geom_segment(
        data=groups_df,
        mapping=aes(x="start", xend="end", y="y", yend="y", color="group"),
        size=15,
        lineend="butt",
        alpha=0.85,
    )
    # Non-critical dependency arrows (lighter but visible)
    + geom_segment(
        data=norm_arrows,
        mapping=aes(x="x_start", xend="x_end", y="y_start", yend="y_end"),
        color="#888888",
        size=1.0,
        alpha=0.6,
    )
    + geom_segment(
        data=norm_heads,
        mapping=aes(x="x_start", xend="x_end", y="y_start", yend="y_end"),
        color="#888888",
        size=1.2,
        alpha=0.6,
    )
    # Critical path dependency arrows (bold, dark)
    + geom_segment(
        data=crit_arrows,
        mapping=aes(x="x_start", xend="x_end", y="y_start", yend="y_end"),
        color="#1A1A1A",
        size=1.4,
        alpha=0.85,
    )
    + geom_segment(
        data=crit_heads,
        mapping=aes(x="x_start", xend="x_end", y="y_start", yend="y_end"),
        color="#1A1A1A",
        size=1.8,
        alpha=0.9,
    )
    # Milestone diamond markers at key handoff points
    + geom_point(
        data=milestones, mapping=aes(x="x", y="y"), shape="D", size=5, color="#C0392B", fill="#C0392B", alpha=0.9
    )
    # Scales
    + scale_color_manual(values=group_colors, name="Project Phase", limits=group_order)
    + scale_y_continuous(breaks=y_breaks, labels=y_labels_list, trans="reverse")
    + scale_x_datetime(
        date_breaks="1 week", date_labels="%b %d", limits=(datetime(2023, 12, 29), datetime(2024, 3, 23))
    )
    # Labels
    + labs(
        title="gantt-dependencies \u00b7 plotnine \u00b7 pyplots.ai",
        subtitle="Bold bars & dark arrows = Critical Path  |  Subdued bars & gray arrows = Non-critical",
        x="Date (2024)",
        y="",
    )
    # Theme - publication-quality styling
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=26, weight="bold", margin={"b": 5}),
        plot_subtitle=element_text(size=14, color="#555555", margin={"b": 15}),
        axis_title_x=element_text(size=20),
        axis_text_x=element_text(size=16, rotation=45, ha="right"),
        axis_text_y=element_text(size=16, ha="right"),
        legend_title=element_text(size=18, weight="bold"),
        legend_text=element_text(size=16),
        legend_position="right",
        legend_background=element_rect(fill="white", alpha=0.85, color="#CCCCCC", size=0.5),
        legend_key_size=18,
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_line(color="#E0E0E0", size=0.3, alpha=0.5),
        plot_background=element_rect(fill="white", color="white"),
        panel_background=element_rect(fill="#FAFAFA", color="white"),
    )
)

# Save the plot
plot.save("plot.png", dpi=300, width=16, height=9, verbose=False)
