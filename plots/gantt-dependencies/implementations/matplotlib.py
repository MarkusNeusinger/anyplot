"""pyplots.ai
gantt-dependencies: Gantt Chart with Dependencies
Library: matplotlib 3.10.8 | Python 3.14
Quality: /100 | Updated: 2026-02-25
"""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, Patch


# Data - Software development project with phases and dependencies
np.random.seed(42)

tasks_data = {
    "task": [
        # Requirements Phase
        "Requirements Phase",
        "Gather Requirements",
        "Document Specs",
        "Review Requirements",
        # Design Phase
        "Design Phase",
        "System Architecture",
        "Database Design",
        "UI/UX Design",
        "Design Review",
        # Development Phase
        "Development Phase",
        "Backend Development",
        "Frontend Development",
        "API Integration",
        "Code Review",
        # Testing Phase
        "Testing Phase",
        "Unit Testing",
        "Integration Testing",
        "User Acceptance Testing",
    ],
    "start": [
        # Requirements Phase
        pd.Timestamp("2024-01-01"),
        pd.Timestamp("2024-01-01"),
        pd.Timestamp("2024-01-08"),
        pd.Timestamp("2024-01-15"),
        # Design Phase
        pd.Timestamp("2024-01-22"),
        pd.Timestamp("2024-01-22"),
        pd.Timestamp("2024-02-05"),
        pd.Timestamp("2024-02-05"),
        pd.Timestamp("2024-02-19"),
        # Development Phase
        pd.Timestamp("2024-02-26"),
        pd.Timestamp("2024-02-26"),
        pd.Timestamp("2024-03-11"),
        pd.Timestamp("2024-03-25"),
        pd.Timestamp("2024-04-08"),
        # Testing Phase
        pd.Timestamp("2024-04-15"),
        pd.Timestamp("2024-04-15"),
        pd.Timestamp("2024-04-22"),
        pd.Timestamp("2024-04-29"),
    ],
    "end": [
        # Requirements Phase
        pd.Timestamp("2024-01-19"),
        pd.Timestamp("2024-01-07"),
        pd.Timestamp("2024-01-14"),
        pd.Timestamp("2024-01-19"),
        # Design Phase
        pd.Timestamp("2024-02-23"),
        pd.Timestamp("2024-02-02"),
        pd.Timestamp("2024-02-16"),
        pd.Timestamp("2024-02-16"),
        pd.Timestamp("2024-02-23"),
        # Development Phase
        pd.Timestamp("2024-04-12"),
        pd.Timestamp("2024-03-08"),
        pd.Timestamp("2024-03-22"),
        pd.Timestamp("2024-04-05"),
        pd.Timestamp("2024-04-12"),
        # Testing Phase
        pd.Timestamp("2024-05-10"),
        pd.Timestamp("2024-04-21"),
        pd.Timestamp("2024-04-28"),
        pd.Timestamp("2024-05-10"),
    ],
    "group": [
        # Requirements Phase
        None,
        "Requirements Phase",
        "Requirements Phase",
        "Requirements Phase",
        # Design Phase
        None,
        "Design Phase",
        "Design Phase",
        "Design Phase",
        "Design Phase",
        # Development Phase
        None,
        "Development Phase",
        "Development Phase",
        "Development Phase",
        "Development Phase",
        # Testing Phase
        None,
        "Testing Phase",
        "Testing Phase",
        "Testing Phase",
    ],
    "depends_on": [
        # Requirements Phase
        [],
        [],
        ["Gather Requirements"],
        ["Document Specs"],
        # Design Phase
        ["Requirements Phase"],
        [],
        ["System Architecture"],
        ["System Architecture"],
        ["Database Design", "UI/UX Design"],
        # Development Phase
        ["Design Phase"],
        [],
        ["Backend Development"],
        ["Backend Development", "Frontend Development"],
        ["API Integration"],
        # Testing Phase
        ["Development Phase"],
        [],
        ["Unit Testing"],
        ["Integration Testing"],
    ],
}

df = pd.DataFrame(tasks_data)

# Calculate durations in days
df["duration"] = (df["end"] - df["start"]).dt.days

# Create task index mapping for y-position
task_to_idx = {task: i for i, task in enumerate(df["task"])}

# Define colors for each phase
phase_colors = {
    "Requirements Phase": "#306998",
    "Design Phase": "#FFD43B",
    "Development Phase": "#4CAF50",
    "Testing Phase": "#E91E63",
}

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Plot bars
bar_height = 0.6
group_bar_height = 0.35

for _idx, row in df.iterrows():
    task = row["task"]
    start = row["start"]
    duration = row["duration"]
    group = row["group"]
    y_pos = len(df) - 1 - task_to_idx[task]

    is_group = group is None and task in phase_colors

    if is_group:
        color = phase_colors[task]
        ax.barh(
            y_pos,
            duration,
            left=start,
            height=group_bar_height,
            color=color,
            alpha=0.95,
            edgecolor="black",
            linewidth=1.5,
            zorder=3,
        )
    else:
        if group and group in phase_colors:
            color = phase_colors[group]
        else:
            color = "#306998"
        ax.barh(
            y_pos,
            duration,
            left=start,
            height=bar_height,
            color=color,
            alpha=0.65,
            edgecolor="black",
            linewidth=0.8,
            zorder=3,
        )

# Draw dependency arrows
for _idx, row in df.iterrows():
    task = row["task"]
    depends = row["depends_on"]
    y_pos = len(df) - 1 - task_to_idx[task]
    task_start = row["start"]

    for dep in depends:
        if dep in task_to_idx:
            dep_idx = task_to_idx[dep]
            dep_y_pos = len(df) - 1 - dep_idx
            dep_row = df[df["task"] == dep].iloc[0]
            dep_end = dep_row["end"]

            # Arrow from right edge (end date) of predecessor to left edge (start date) of successor
            start_x = dep_end
            start_y = dep_y_pos
            end_x = task_start
            end_y = y_pos

            # Curvature based on vertical distance
            dy = abs(end_y - start_y)
            rad = 0.15 if dy <= 2 else (0.1 if dy <= 5 else 0.08)

            arrow = FancyArrowPatch(
                (start_x, start_y),
                (end_x, end_y),
                arrowstyle="->",
                color="#555555",
                linewidth=2,
                connectionstyle=f"arc3,rad={rad}",
                alpha=0.7,
                mutation_scale=15,
                zorder=4,
            )
            ax.add_patch(arrow)

# Format y-axis with task names
task_labels = df["task"].tolist()[::-1]
y_positions = range(len(task_labels))

styled_labels = []
for label in task_labels:
    row = df[df["task"] == label].iloc[0]
    if row["group"] is not None:
        styled_labels.append(f"    {label}")
    else:
        styled_labels.append(label)

ax.set_yticks(y_positions)
ax.set_yticklabels(styled_labels, fontsize=14)

# Bold phase labels
for i, label in enumerate(task_labels):
    row = df[df["task"] == label].iloc[0]
    if row["group"] is None and label in phase_colors:
        ax.get_yticklabels()[i].set_fontweight("bold")

# Format x-axis with dates
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
ax.tick_params(axis="x", labelsize=16)
plt.xticks(rotation=45, ha="right")

# Labels and title
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Tasks", fontsize=20)
ax.set_title("gantt-dependencies · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")

# Grid - subtle vertical lines for timeline
ax.grid(True, axis="x", alpha=0.2, linewidth=0.8, linestyle="--")
ax.set_axisbelow(True)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Create legend with proper dependency arrow entry
legend_patches = [
    Patch(facecolor=color, alpha=0.7, edgecolor="black", label=phase) for phase, color in phase_colors.items()
]
arrow_legend = Line2D(
    [0],
    [0],
    color="#555555",
    linewidth=2,
    alpha=0.7,
    marker=">",
    markersize=8,
    markeredgecolor="#555555",
    label="Dependency",
)
legend_patches.append(arrow_legend)
ax.legend(handles=legend_patches, loc="upper right", fontsize=14, framealpha=0.9, edgecolor="#cccccc")

# Adjust layout
ax.set_xlim(df["start"].min() - pd.Timedelta(days=3), df["end"].max() + pd.Timedelta(days=3))

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
