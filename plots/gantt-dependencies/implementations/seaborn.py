"""pyplots.ai
gantt-dependencies: Gantt Chart with Dependencies
Library: seaborn 0.13.2 | Python 3.14
Quality: 88/100 | Updated: 2026-02-25
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import FancyArrowPatch


# Set seaborn theme and context for proper sizing at 4800x2700
sns.set_theme(style="whitegrid", context="talk", font_scale=1.1)

# Data: Software Development Project with Dependencies
# All dependent tasks start at or after their predecessors end
tasks_data = [
    # Requirements Phase
    {
        "task": "Requirements Gathering",
        "start": "2024-01-01",
        "end": "2024-01-14",
        "group": "Requirements",
        "depends_on": [],
    },
    {
        "task": "Requirements Review",
        "start": "2024-01-15",
        "end": "2024-01-21",
        "group": "Requirements",
        "depends_on": ["Requirements Gathering"],
    },
    {
        "task": "Requirements Sign-off",
        "start": "2024-01-22",
        "end": "2024-01-25",
        "group": "Requirements",
        "depends_on": ["Requirements Review"],
    },
    # Design Phase
    {
        "task": "System Architecture",
        "start": "2024-01-26",
        "end": "2024-02-08",
        "group": "Design",
        "depends_on": ["Requirements Sign-off"],
    },
    {
        "task": "Database Design",
        "start": "2024-02-09",
        "end": "2024-02-20",
        "group": "Design",
        "depends_on": ["System Architecture"],
    },
    {
        "task": "UI/UX Design",
        "start": "2024-02-09",
        "end": "2024-02-22",
        "group": "Design",
        "depends_on": ["System Architecture"],
    },
    {
        "task": "Design Review",
        "start": "2024-02-23",
        "end": "2024-02-28",
        "group": "Design",
        "depends_on": ["Database Design", "UI/UX Design"],
    },
    # Development Phase
    {
        "task": "Backend Core",
        "start": "2024-02-29",
        "end": "2024-03-18",
        "group": "Development",
        "depends_on": ["Design Review"],
    },
    {
        "task": "API Development",
        "start": "2024-03-19",
        "end": "2024-04-05",
        "group": "Development",
        "depends_on": ["Backend Core"],
    },
    {
        "task": "Frontend Components",
        "start": "2024-04-06",
        "end": "2024-04-22",
        "group": "Development",
        "depends_on": ["UI/UX Design", "API Development"],
    },
    {
        "task": "Integration",
        "start": "2024-04-23",
        "end": "2024-05-06",
        "group": "Development",
        "depends_on": ["API Development", "Frontend Components"],
    },
    # Testing Phase
    {
        "task": "Unit Testing",
        "start": "2024-03-19",
        "end": "2024-04-05",
        "group": "Testing",
        "depends_on": ["Backend Core"],
    },
    {
        "task": "Integration Testing",
        "start": "2024-05-07",
        "end": "2024-05-17",
        "group": "Testing",
        "depends_on": ["Integration", "Unit Testing"],
    },
    {
        "task": "UAT",
        "start": "2024-05-20",
        "end": "2024-05-31",
        "group": "Testing",
        "depends_on": ["Integration Testing"],
    },
    {"task": "Bug Fixes", "start": "2024-06-03", "end": "2024-06-14", "group": "Testing", "depends_on": ["UAT"]},
]

df = pd.DataFrame(tasks_data)
df["start"] = pd.to_datetime(df["start"])
df["end"] = pd.to_datetime(df["end"])

# Reference date for x-axis (convert dates to numeric)
ref_date = df["start"].min()
df["start_num"] = (df["start"] - ref_date).dt.days
df["end_num"] = (df["end"] - ref_date).dt.days
df["duration"] = df["end_num"] - df["start_num"]

# Calculate y positions - groups first, then tasks
groups = df["group"].unique()
# Curated 4-color palette with clearly distinct hues (colorblind-safe)
phase_palette = sns.color_palette(["#306998", "#FFD43B", "#CC553D", "#2A9D8F"])
group_colors = {
    "Requirements": phase_palette[0],
    "Design": phase_palette[1],
    "Development": phase_palette[2],
    "Testing": phase_palette[3],
}

y_positions = {}
task_to_y = {}
y_counter = 0

for group in groups:
    y_positions[group] = y_counter
    y_counter += 1
    group_tasks = df[df["group"] == group]["task"].tolist()
    for task in group_tasks:
        task_to_y[task] = y_counter
        y_counter += 1

# Add y position to dataframe
df["y_pos"] = df["task"].map(task_to_y)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Create data for seaborn lineplot (bars as thick lines)
line_data = []
for _, row in df.iterrows():
    line_data.append(
        {"x": row["start_num"], "y": row["y_pos"], "task": row["task"], "group": row["group"], "point": "start"}
    )
    line_data.append(
        {"x": row["end_num"], "y": row["y_pos"], "task": row["task"], "group": row["group"], "point": "end"}
    )

line_df = pd.DataFrame(line_data)

# Use seaborn lineplot with units parameter to draw separate lines for each task
sns.lineplot(
    data=line_df,
    x="x",
    y="y",
    hue="group",
    units="task",
    estimator=None,
    palette=group_colors,
    linewidth=14,
    alpha=0.85,
    ax=ax,
    legend=False,
)

# Draw group bars (aggregate spans) as thinner lines
for group in groups:
    group_df = df[df["group"] == group]
    group_start = group_df["start_num"].min()
    group_end = group_df["end_num"].max()
    y = y_positions[group]
    color = group_colors[group]

    ax.plot([group_start, group_end], [y, y], color=color, linewidth=10, alpha=0.4, solid_capstyle="round")

# Add phase milestone markers at group completion points using scatterplot
milestone_data = []
for group in groups:
    group_df = df[df["group"] == group]
    milestone_data.append({"x": group_df["end_num"].max(), "y": y_positions[group], "group": group})
milestone_df = pd.DataFrame(milestone_data)

sns.scatterplot(
    data=milestone_df,
    x="x",
    y="y",
    hue="group",
    palette=group_colors,
    marker="D",
    s=120,
    edgecolor="white",
    linewidth=1.5,
    zorder=6,
    ax=ax,
    legend=False,
)

# Draw dependency arrows from right edge of predecessor to left edge of successor
for _, row in df.iterrows():
    if row["depends_on"]:
        end_y = task_to_y[row["task"]]
        end_x = row["start_num"]

        for dep in row["depends_on"]:
            dep_row = df[df["task"] == dep].iloc[0]
            start_y = task_to_y[dep]
            start_x = dep_row["end_num"]

            # Draw arrow with curved path
            arrow = FancyArrowPatch(
                (start_x, start_y),
                (end_x, end_y),
                connectionstyle="arc3,rad=0.1",
                arrowstyle="->,head_width=0.6,head_length=0.4",
                color="#333333",
                linewidth=2.2,
                alpha=0.8,
                zorder=5,
            )
            ax.add_patch(arrow)

# Y-axis labels with proper formatting
all_labels = []
all_y = []

for group in groups:
    all_labels.append(f"▪ {group}")
    all_y.append(y_positions[group])
    group_tasks = df[df["group"] == group]["task"].tolist()
    for task in group_tasks:
        all_labels.append(f"   {task}")
        all_y.append(task_to_y[task])

ax.set_yticks(all_y)
ax.set_yticklabels(all_labels, fontsize=16)
ax.invert_yaxis()

# Bold group labels for hierarchy emphasis
for label in ax.get_yticklabels():
    if label.get_text().startswith("▪"):
        label.set_fontweight("bold")
        label.set_fontsize(17)

# X-axis formatting (dates)
max_day = int(df["end_num"].max()) + 7
date_ticks = np.arange(0, max_day, 14)
date_labels = [(ref_date + pd.Timedelta(days=int(d))).strftime("%b %d") for d in date_ticks]
ax.set_xticks(date_ticks)
ax.set_xticklabels(date_labels, fontsize=16, rotation=45, ha="right")
ax.set_xlim(-2, max_day)

# Labels and title
ax.set_xlabel("Project Timeline (2024)", fontsize=20)
ax.set_ylabel("Tasks by Phase", fontsize=20)
ax.set_title("gantt-dependencies · seaborn · pyplots.ai", fontsize=24, fontweight="bold")

# Grid (subtle, vertical only)
ax.grid(True, axis="x", alpha=0.3, linestyle="--", linewidth=0.8)
ax.grid(False, axis="y")
ax.set_axisbelow(True)

# Legend for groups
legend_patches = [mpatches.Patch(color=color, alpha=0.85, label=group) for group, color in group_colors.items()]
arrow_legend = plt.Line2D(
    [0], [0], color="#333333", linewidth=2.2, linestyle="-", marker=">", markersize=9, label="Dependency"
)
legend_patches.append(arrow_legend)

ax.legend(
    handles=legend_patches, loc="upper right", fontsize=14, framealpha=0.9, title="Project Phases", title_fontsize=16
)

# Clean up spines
sns.despine(left=True, bottom=False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
