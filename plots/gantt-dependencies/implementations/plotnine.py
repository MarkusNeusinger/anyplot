"""pyplots.ai
gantt-dependencies: Gantt Chart with Dependencies
Library: plotnine 0.15.3 | Python 3.14
Quality: /100 | Updated: 2026-02-25
"""

from datetime import datetime, timedelta

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
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

# Define group colors
group_colors = {"Requirements": "#306998", "Design": "#4B8BBE", "Development": "#FFD43B", "Testing": "#646464"}

# Create ordered task list with group headers (top to bottom)
group_order = ["Requirements", "Design", "Development", "Testing"]
task_display_order = []  # Top to bottom display order
task_labels = {}  # Map y position to label

y_pos = 0
group_positions = {}
task_positions = {}

for grp in group_order:
    # Group header
    group_label = f"▸ {grp}"
    task_display_order.append({"label": group_label, "y": y_pos, "is_group": True, "group": grp})
    group_positions[grp] = y_pos
    task_labels[y_pos] = group_label
    y_pos += 1

    # Tasks in this group
    group_tasks = df[df["group"] == grp]
    for _, task_row in group_tasks.iterrows():
        task_label = f"   {task_row['task']}"
        task_display_order.append(
            {
                "label": task_label,
                "y": y_pos,
                "is_group": False,
                "group": grp,
                "task": task_row["task"],
                "start": task_row["start"],
                "end": task_row["end"],
            }
        )
        task_positions[task_row["task"]] = y_pos
        task_labels[y_pos] = task_label
        y_pos += 1

# Calculate group aggregates
group_data = []
for grp in group_order:
    group_tasks = df[df["group"] == grp]
    group_data.append(
        {
            "y": group_positions[grp],
            "start": group_tasks["start"].min(),
            "end": group_tasks["end"].max(),
            "group": grp,
            "is_group": True,
        }
    )

# Create task data with y positions
task_data = []
for grp in group_order:
    group_tasks = df[df["group"] == grp]
    for _, task_row in group_tasks.iterrows():
        task_data.append(
            {
                "y": task_positions[task_row["task"]],
                "start": task_row["start"],
                "end": task_row["end"],
                "group": grp,
                "is_group": False,
            }
        )

# Create DataFrames for plotting
tasks_df = pd.DataFrame(task_data)
groups_df = pd.DataFrame(group_data)

# Set explicit category ordering for legend (project phase order, not alphabetical)
phase_order = pd.CategoricalDtype(categories=group_order, ordered=True)
tasks_df["group"] = tasks_df["group"].astype(phase_order)
groups_df["group"] = groups_df["group"].astype(phase_order)

# Build dependency arrows as L-shaped connectors (vertical then horizontal)
arrows_data = []
arrowheads_data = []
arrow_size_days = 1.5  # Size of arrowhead in days

for _, row in df.iterrows():
    if row["depends_on"]:
        for dep_name in row["depends_on"]:
            if dep_name in task_positions:
                dep_row = df[df["task"] == dep_name].iloc[0]
                x_start = dep_row["end"]
                x_end = row["start"]
                y_start = task_positions[dep_name]
                y_end = task_positions[row["task"]]

                # Vertical segment: from predecessor end down to successor row
                arrows_data.append({"x_start": x_start, "x_end": x_start, "y_start": y_start, "y_end": y_end})
                # Horizontal segment: from corner to successor start (shortened for arrowhead)
                arrows_data.append(
                    {
                        "x_start": x_start,
                        "x_end": x_end - timedelta(days=arrow_size_days * 0.4),
                        "y_start": y_end,
                        "y_end": y_end,
                    }
                )

                # Arrowhead (V pointing right at successor start)
                arrow_tip_x = x_end
                arrow_base_x = x_end - timedelta(days=arrow_size_days)
                arrow_wing_offset = 0.25

                arrowheads_data.append(
                    {
                        "x_start": arrow_base_x,
                        "x_end": arrow_tip_x,
                        "y_start": y_end - arrow_wing_offset,
                        "y_end": y_end,
                    }
                )
                arrowheads_data.append(
                    {
                        "x_start": arrow_base_x,
                        "x_end": arrow_tip_x,
                        "y_start": y_end + arrow_wing_offset,
                        "y_end": y_end,
                    }
                )

arrows_df = pd.DataFrame(arrows_data) if arrows_data else None
arrowheads_df = pd.DataFrame(arrowheads_data) if arrowheads_data else None

# Create y-axis labels and breaks
y_breaks = list(task_labels.keys())
y_labels = [task_labels[y] for y in y_breaks]

# Build the plot
plot = (
    ggplot()
    # Task bars
    + geom_segment(
        data=tasks_df, mapping=aes(x="start", xend="end", y="y", yend="y", color="group"), size=10, lineend="butt"
    )
    # Group aggregate bars (thicker)
    + geom_segment(
        data=groups_df,
        mapping=aes(x="start", xend="end", y="y", yend="y", color="group"),
        size=14,
        lineend="butt",
        alpha=0.9,
    )
)

# Add dependency arrows with arrowheads
if arrows_df is not None and len(arrows_df) > 0:
    plot = plot + geom_segment(
        data=arrows_df,
        mapping=aes(x="x_start", xend="x_end", y="y_start", yend="y_end"),
        color="#333333",
        size=1.0,
        alpha=0.7,
    )
    if arrowheads_df is not None and len(arrowheads_df) > 0:
        plot = plot + geom_segment(
            data=arrowheads_df,
            mapping=aes(x="x_start", xend="x_end", y="y_start", yend="y_end"),
            color="#333333",
            size=1.4,
            alpha=0.85,
        )

# Add scales, labels, and theme
plot = (
    plot
    + scale_color_manual(values=group_colors, name="Project Phase", limits=group_order)
    + scale_y_continuous(
        breaks=y_breaks,
        labels=y_labels,
        trans="reverse",  # Reverse so first group is at top
    )
    + scale_x_datetime()
    + labs(title="gantt-dependencies · plotnine · pyplots.ai", x="Date (2024)", y="")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold", margin={"b": 15}),
        axis_title_x=element_text(size=18),
        axis_text_x=element_text(size=14, rotation=45, ha="right"),
        axis_text_y=element_text(size=12, ha="right"),
        legend_title=element_text(size=16, weight="bold"),
        legend_text=element_text(size=14),
        legend_position="right",
        legend_background=element_rect(fill="white", alpha=0.8),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_line(color="#DDDDDD", size=0.4, alpha=0.4),
        plot_background=element_rect(fill="white", color="white"),
    )
)

# Save the plot
plot.save("plot.png", dpi=300, width=16, height=9, verbose=False)
