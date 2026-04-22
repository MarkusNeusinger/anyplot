""" pyplots.ai
gantt-basic: Basic Gantt Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 95/100 | Created: 2025-12-27
"""

from datetime import datetime, timedelta

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


# Data - Software Development Project
tasks = [
    {
        "task": "Requirements Analysis",
        "start": datetime(2025, 1, 6),
        "end": datetime(2025, 1, 17),
        "category": "Planning",
    },
    {"task": "System Design", "start": datetime(2025, 1, 13), "end": datetime(2025, 1, 31), "category": "Planning"},
    {"task": "Database Setup", "start": datetime(2025, 1, 27), "end": datetime(2025, 2, 7), "category": "Development"},
    {
        "task": "Backend Development",
        "start": datetime(2025, 2, 3),
        "end": datetime(2025, 3, 7),
        "category": "Development",
    },
    {
        "task": "Frontend Development",
        "start": datetime(2025, 2, 10),
        "end": datetime(2025, 3, 14),
        "category": "Development",
    },
    {"task": "API Integration", "start": datetime(2025, 3, 3), "end": datetime(2025, 3, 21), "category": "Development"},
    {"task": "Unit Testing", "start": datetime(2025, 3, 10), "end": datetime(2025, 3, 28), "category": "Testing"},
    {
        "task": "Integration Testing",
        "start": datetime(2025, 3, 24),
        "end": datetime(2025, 4, 11),
        "category": "Testing",
    },
    {
        "task": "User Acceptance Testing",
        "start": datetime(2025, 4, 7),
        "end": datetime(2025, 4, 18),
        "category": "Testing",
    },
    {"task": "Documentation", "start": datetime(2025, 3, 17), "end": datetime(2025, 4, 11), "category": "Deployment"},
    {"task": "Deployment Prep", "start": datetime(2025, 4, 14), "end": datetime(2025, 4, 25), "category": "Deployment"},
    {"task": "Go Live", "start": datetime(2025, 4, 28), "end": datetime(2025, 5, 2), "category": "Deployment"},
]

# Category colors (Python Blue variations + complementary)
category_colors = {
    "Planning": "#306998",  # Python Blue
    "Development": "#FFD43B",  # Python Yellow
    "Testing": "#4B8BBE",  # Light Python Blue
    "Deployment": "#646464",  # Neutral Gray
}

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Sort tasks by start date for logical ordering
tasks_sorted = sorted(tasks, key=lambda x: x["start"], reverse=True)

# Draw bars
bar_height = 0.6
y_positions = range(len(tasks_sorted))

for i, task in enumerate(tasks_sorted):
    start = task["start"]
    duration = (task["end"] - task["start"]).days
    color = category_colors[task["category"]]

    ax.barh(i, duration, left=start, height=bar_height, color=color, edgecolor="white", linewidth=1.5, alpha=0.9)

# Y-axis: task names
ax.set_yticks(y_positions)
ax.set_yticklabels([t["task"] for t in tasks_sorted], fontsize=16)

# X-axis: dates
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
ax.tick_params(axis="x", labelsize=14, rotation=45)

# Set x-axis limits with padding
all_starts = [t["start"] for t in tasks]
all_ends = [t["end"] for t in tasks]
ax.set_xlim(min(all_starts) - timedelta(days=3), max(all_ends) + timedelta(days=3))

# Add "today" marker line (mid-project for demonstration)
today = datetime(2025, 3, 15)
ax.axvline(today, color="#E74C3C", linewidth=2.5, linestyle="--", label="Today (Mar 15)", zorder=5)

# Labels and title
ax.set_xlabel("Timeline", fontsize=20)
ax.set_ylabel("Tasks", fontsize=20)
ax.set_title("gantt-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="bold")

# Grid (subtle, only on x-axis)
ax.grid(True, axis="x", alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

# Legend for categories
legend_elements = [Patch(facecolor=color, edgecolor="white", label=cat) for cat, color in category_colors.items()]
legend_elements.append(plt.Line2D([0], [0], color="#E74C3C", linewidth=2.5, linestyle="--", label="Today"))
ax.legend(handles=legend_elements, loc="upper right", fontsize=14, framealpha=0.95)

# Remove top and right spines for cleaner look
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
