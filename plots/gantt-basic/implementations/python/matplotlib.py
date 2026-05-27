""" anyplot.ai
gantt-basic: Basic Gantt Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 95/100 | Updated: 2026-05-10
"""

import os
from datetime import datetime, timedelta

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette for categories
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]

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

# Category to color mapping using Okabe-Ito palette
category_colors = {
    "Planning": IMPRINT[0],
    "Development": IMPRINT[1],
    "Testing": IMPRINT[2],
    "Deployment": IMPRINT[3],
}

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Sort tasks by start date for logical ordering
tasks_sorted = sorted(tasks, key=lambda x: x["start"], reverse=True)

# Draw bars
bar_height = 0.6
y_positions = range(len(tasks_sorted))

for i, task in enumerate(tasks_sorted):
    start = task["start"]
    duration = (task["end"] - task["start"]).days
    color = category_colors[task["category"]]

    ax.barh(i, duration, left=start, height=bar_height, color=color, edgecolor=PAGE_BG, linewidth=1, alpha=0.9)

# Y-axis: task names
ax.set_yticks(y_positions)
ax.set_yticklabels([t["task"] for t in tasks_sorted], fontsize=16, color=INK)

# X-axis: dates
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
ax.tick_params(axis="x", labelsize=16, rotation=45, colors=INK_SOFT)
ax.tick_params(axis="y", labelsize=16, colors=INK_SOFT)

# Set x-axis limits with padding
all_starts = [t["start"] for t in tasks]
all_ends = [t["end"] for t in tasks]
ax.set_xlim(min(all_starts) - timedelta(days=3), max(all_ends) + timedelta(days=3))

# Add "today" marker line (mid-project for demonstration)
today = datetime(2025, 3, 15)
ax.axvline(today, color=INK_MUTED, linewidth=3, linestyle="--", label="Today", zorder=5)

# Style
ax.set_xlabel("Project Timeline (2025)", fontsize=20, color=INK)
ax.set_ylabel("Project Tasks", fontsize=20, color=INK)
ax.set_title("gantt-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)

# Grid (subtle, only on x-axis)
ax.grid(True, axis="x", alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

# Legend for categories
legend_elements = [Patch(facecolor=color, edgecolor=INK_SOFT, label=cat) for cat, color in category_colors.items()]
legend_elements.append(plt.Line2D([0], [0], color=INK_MUTED, linewidth=3, linestyle="--", label="Today"))
leg = ax.legend(handles=legend_elements, loc="upper right", fontsize=16, framealpha=0.95, fancybox=True)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
for text in leg.get_texts():
    text.set_color(INK_SOFT)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
