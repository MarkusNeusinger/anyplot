""" pyplots.ai
gantt-dependencies: Gantt Chart with Dependencies
Library: matplotlib 3.10.8 | Python 3.14
Quality: 90/100 | Updated: 2026-02-25
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

# Define colorblind-safe palette for each phase
phase_colors = {
    "Requirements Phase": "#306998",
    "Design Phase": "#D4A017",
    "Development Phase": "#E67E22",
    "Testing Phase": "#8E44AD",
}

# Compute critical path (longest path through dependency network)
# Build adjacency with implicit phase↔child edges for a connected graph
task_successors = {t: [] for t in df["task"]}
for _, r in df.iterrows():
    for dep in r["depends_on"]:
        if dep in task_successors:
            task_successors[dep].append(r["task"])

# Add implicit edges: phase header → child tasks with no in-phase deps,
# and last-finishing child → next phase header
for phase_name in phase_colors:
    children = df[df["group"] == phase_name]
    # Children with no explicit dependencies → phase header leads to them
    for _, child in children.iterrows():
        if not child["depends_on"]:
            task_successors[phase_name].append(child["task"])
    # Find last-finishing child and connect to next phase(s)
    if not children.empty:
        last_child = children.loc[children["end"].idxmax(), "task"]
        # Find phases that depend on this phase
        for _, r in df.iterrows():
            if phase_name in r["depends_on"] and r["task"] in phase_colors:
                task_successors[last_child].append(r["task"])

# Longest path from each task using DFS with memoization
longest_from = {}


def longest_path(task):
    if task in longest_from:
        return longest_from[task]
    succs = task_successors[task]
    if not succs:
        longest_from[task] = [task]
        return [task]
    best = []
    for s in succs:
        path = longest_path(s)
        if len(path) > len(best):
            best = path
    longest_from[task] = [task] + best
    return longest_from[task]


# Find the globally longest path
critical_path = []
for task in df["task"]:
    path = longest_path(task)
    if len(path) > len(critical_path):
        critical_path = path
critical_set = set(critical_path)

# Create figure with subtle background — taller for 18 tasks
fig, ax = plt.subplots(figsize=(16, 10))
fig.patch.set_facecolor("#FAFAFA")
ax.set_facecolor("#FAFAFA")

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
    on_critical = task in critical_set

    if is_group:
        color = phase_colors[task]
        edge_clr = "#B22222" if on_critical else "#2C3E50"
        edge_w = 2.5 if on_critical else 1.5
        ax.barh(
            y_pos,
            duration,
            left=start,
            height=group_bar_height,
            color=color,
            alpha=0.95,
            edgecolor=edge_clr,
            linewidth=edge_w,
            zorder=3,
        )
    else:
        if group and group in phase_colors:
            color = phase_colors[group]
        else:
            color = "#306998"
        edge_clr = "#B22222" if on_critical else "#2C3E50"
        edge_w = 2.2 if on_critical else 0.6
        task_alpha = 0.85 if on_critical else 0.7
        ax.barh(
            y_pos,
            duration,
            left=start,
            height=bar_height,
            color=color,
            alpha=task_alpha,
            edgecolor=edge_clr,
            linewidth=edge_w,
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

            # Highlight arrows on the critical path
            is_critical_edge = dep in critical_set and task in critical_set
            arr_color = "#B22222" if is_critical_edge else "#4A4A4A"
            arr_lw = 2.4 if is_critical_edge else 1.8
            arr_alpha = 0.85 if is_critical_edge else 0.5

            arrow = FancyArrowPatch(
                (start_x, start_y),
                (end_x, end_y),
                arrowstyle="-|>",
                color=arr_color,
                linewidth=arr_lw,
                connectionstyle=f"arc3,rad={rad}",
                alpha=arr_alpha,
                mutation_scale=14,
                zorder=5 if is_critical_edge else 4,
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
ax.set_yticklabels(styled_labels)

# Bold phase labels
for i, label in enumerate(task_labels):
    row = df[df["task"] == label].iloc[0]
    if row["group"] is None and label in phase_colors:
        ax.get_yticklabels()[i].set_fontweight("bold")

# Format x-axis with dates
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
ax.tick_params(axis="both", labelsize=16)
plt.xticks(rotation=45, ha="right")

# Labels and title
ax.set_xlabel("Timeline (2024)", fontsize=20)
ax.set_ylabel("Project Tasks", fontsize=20)
ax.set_title("gantt-dependencies · matplotlib · pyplots.ai", fontsize=24, fontweight="bold", color="#2C3E50", pad=20)

# Grid - subtle vertical lines for timeline
ax.grid(True, axis="x", alpha=0.15, linewidth=0.6, linestyle="--", color="#999999")
ax.set_axisbelow(True)

# Remove top and right spines, style remaining
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color("#CCCCCC")
ax.spines["bottom"].set_color("#CCCCCC")

# Add milestone diamond at project completion
project_end = df["end"].max()
last_task_y = len(df) - 1 - task_to_idx["User Acceptance Testing"]
ax.plot(
    project_end,
    last_task_y,
    marker="D",
    markersize=12,
    color="#B22222",
    markeredgecolor="#2C3E50",
    markeredgewidth=1.2,
    zorder=6,
)

# Create legend with critical path and dependency entries
legend_patches = [
    Patch(facecolor=color, alpha=0.8, edgecolor="#2C3E50", linewidth=0.6, label=phase)
    for phase, color in phase_colors.items()
]
critical_legend = Line2D(
    [0],
    [0],
    color="#B22222",
    linewidth=2.5,
    alpha=0.85,
    marker=">",
    markersize=8,
    markeredgecolor="#B22222",
    label="Critical Path",
)
arrow_legend = Line2D(
    [0],
    [0],
    color="#4A4A4A",
    linewidth=2,
    alpha=0.5,
    marker=">",
    markersize=8,
    markeredgecolor="#4A4A4A",
    label="Dependency",
)
milestone_legend = Line2D(
    [0], [0], color="#B22222", marker="D", markersize=10, markeredgecolor="#2C3E50", linestyle="None", label="Milestone"
)
legend_patches.extend([critical_legend, arrow_legend, milestone_legend])
ax.legend(
    handles=legend_patches,
    loc="upper right",
    fontsize=14,
    framealpha=0.95,
    edgecolor="#CCCCCC",
    fancybox=True,
    shadow=False,
)

# Adjust layout
ax.set_xlim(df["start"].min() - pd.Timedelta(days=3), df["end"].max() + pd.Timedelta(days=3))

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
