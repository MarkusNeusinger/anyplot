""" pyplots.ai
gantt-basic: Basic Gantt Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-27
"""

from datetime import datetime

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Data - Software Development Project Timeline
tasks_data = {
    "task": [
        "Requirements Analysis",
        "UI/UX Design",
        "Database Design",
        "Backend Development",
        "Frontend Development",
        "API Integration",
        "Unit Testing",
        "Integration Testing",
        "User Acceptance Testing",
        "Deployment",
        "Documentation",
        "Training",
    ],
    "start": [
        "2025-01-06",
        "2025-01-13",
        "2025-01-13",
        "2025-01-27",
        "2025-02-03",
        "2025-02-17",
        "2025-02-10",
        "2025-03-03",
        "2025-03-17",
        "2025-03-31",
        "2025-02-24",
        "2025-04-07",
    ],
    "end": [
        "2025-01-17",
        "2025-01-31",
        "2025-01-24",
        "2025-02-28",
        "2025-03-14",
        "2025-03-07",
        "2025-03-07",
        "2025-03-21",
        "2025-03-28",
        "2025-04-04",
        "2025-03-21",
        "2025-04-11",
    ],
    "category": [
        "Planning",
        "Design",
        "Design",
        "Development",
        "Development",
        "Development",
        "Testing",
        "Testing",
        "Testing",
        "Deployment",
        "Documentation",
        "Deployment",
    ],
}

df = pd.DataFrame(tasks_data)
df["start"] = pd.to_datetime(df["start"])
df["end"] = pd.to_datetime(df["end"])
df["duration"] = (df["end"] - df["start"]).dt.days

# Sort by start date for logical ordering
df = df.sort_values("start").reset_index(drop=True)

# Calculate numeric start position for seaborn barplot
df["start_num"] = mdates.date2num(df["start"])

# Set seaborn style BEFORE creating figure
sns.set_style("whitegrid")
sns.set_context("talk", font_scale=1.0)

# Category palette using colorblind-friendly colors
category_order = ["Planning", "Design", "Development", "Testing", "Documentation", "Deployment"]
category_palette = {
    "Planning": "#306998",
    "Design": "#FFD43B",
    "Development": "#4B8BBE",
    "Testing": "#646464",
    "Documentation": "#8B4513",
    "Deployment": "#2E8B57",
}

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Use seaborn barplot with hue for category coloring
sns.barplot(
    data=df,
    y="task",
    x="duration",
    hue="category",
    hue_order=category_order,
    palette=category_palette,
    orient="h",
    dodge=False,
    ax=ax,
    edgecolor="white",
    linewidth=1.5,
    alpha=0.9,
    legend=False,
)

# Get current bar positions and shift by start date
for bar, start_num in zip(ax.patches, df["start_num"], strict=True):
    bar.set_x(start_num)

# Format x-axis as dates
ax.xaxis_date()
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d, %Y"))
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0, interval=2))

# Add current date indicator (vertical line)
today = datetime(2025, 2, 15)
ax.axvline(x=mdates.date2num(today), color="#E74C3C", linestyle="--", linewidth=2.5, label="Today", alpha=0.8)

# Styling with year context in x-axis label
ax.set_xlabel("Timeline (2025)", fontsize=20)
ax.set_ylabel("Tasks", fontsize=20)
ax.set_title("gantt-basic · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)
ax.tick_params(axis="x", labelsize=14, rotation=45)
ax.tick_params(axis="y", labelsize=16)

# Adjust grid
ax.grid(axis="x", alpha=0.3, linestyle="--")
ax.grid(axis="y", alpha=0.15)

# Create legend for categories - position at lower right to avoid overlap
legend_elements = [
    plt.Rectangle((0, 0), 1, 1, facecolor=color, edgecolor="white", label=cat)
    for cat, color in category_palette.items()
]
legend_elements.append(plt.Line2D([0], [0], color="#E74C3C", linestyle="--", linewidth=2.5, label="Today"))
ax.legend(handles=legend_elements, loc="lower right", fontsize=14, framealpha=0.95)

# Invert y-axis to have first task at top
ax.invert_yaxis()

# Set x-axis limits with padding
date_min = df["start"].min() - pd.Timedelta(days=3)
date_max = df["end"].max() + pd.Timedelta(days=3)
ax.set_xlim(mdates.date2num(date_min), mdates.date2num(date_max))

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
