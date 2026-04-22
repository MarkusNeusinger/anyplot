""" pyplots.ai
timeline-basic: Event Timeline
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-29
"""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Data - Software project milestones (8 events for better readability)
np.random.seed(42)
events = pd.DataFrame(
    {
        "date": pd.to_datetime(
            [
                "2024-01-15",
                "2024-03-01",
                "2024-04-20",
                "2024-06-10",
                "2024-08-01",
                "2024-09-15",
                "2024-10-30",
                "2024-12-10",
            ]
        ),
        "event": [
            "Project Kickoff",
            "Requirements Done",
            "Alpha Release",
            "Beta Launch",
            "User Testing",
            "Bug Fixes",
            "Final Review",
            "Go Live",
        ],
        "category": ["Planning", "Planning", "Development", "Development", "Testing", "Testing", "Release", "Release"],
    }
)

# Color mapping for categories
category_colors = {
    "Planning": "#306998",  # Python Blue
    "Development": "#FFD43B",  # Python Yellow
    "Testing": "#4ECDC4",  # Teal
    "Release": "#FF6B6B",  # Coral
}
colors = [category_colors[cat] for cat in events["category"]]

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Draw the timeline axis
ax.axhline(y=0, color="#666666", linewidth=2, zorder=1)

# Plot events with alternating positions
levels = np.tile([1, -1], len(events) // 2 + 1)[: len(events)]
level_heights = levels * 0.3

# Draw vertical stems
for date, height, color in zip(events["date"], level_heights, colors, strict=True):
    ax.plot([date, date], [0, height], color=color, linewidth=2.5, zorder=2)

# Draw event markers
ax.scatter(events["date"], level_heights, c=colors, s=300, zorder=3, edgecolors="white", linewidths=2)

# Add event labels with alternating positions
for date, event, height, color in zip(events["date"], events["event"], level_heights, colors, strict=True):
    va = "bottom" if height > 0 else "top"
    offset = 0.08 if height > 0 else -0.08
    ax.annotate(
        event,
        xy=(date, height),
        xytext=(0, offset * 300),
        textcoords="offset points",
        ha="center",
        va=va,
        fontsize=14,
        fontweight="bold",
        color="#333333",
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": color, "linewidth": 1.5, "alpha": 0.9},
    )

# Add date labels below each marker
for date, height in zip(events["date"], level_heights, strict=True):
    ax.annotate(
        date.strftime("%b %d"),
        xy=(date, 0),
        xytext=(0, -20 if height > 0 else 20),
        textcoords="offset points",
        ha="center",
        va="top" if height > 0 else "bottom",
        fontsize=12,
        color="#666666",
    )

# Create legend for categories
legend_handles = [
    plt.scatter([], [], c=color, s=200, label=cat, edgecolors="white", linewidths=1.5)
    for cat, color in category_colors.items()
]
ax.legend(
    handles=legend_handles, loc="upper right", fontsize=14, framealpha=0.9, title="Project Phase", title_fontsize=16
)

# Styling
ax.set_xlim(events["date"].min() - pd.Timedelta(days=35), events["date"].max() + pd.Timedelta(days=35))
ax.set_ylim(-0.6, 0.6)

# Format x-axis with months
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
ax.tick_params(axis="x", labelsize=14)

# Hide y-axis and spines
ax.yaxis.set_visible(False)
ax.spines["left"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["top"].set_visible(False)
ax.spines["bottom"].set_visible(False)

# Title
ax.set_title("timeline-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="bold", pad=20)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
