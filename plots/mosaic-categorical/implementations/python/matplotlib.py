""" pyplots.ai
mosaic-categorical: Mosaic Plot for Categorical Association Analysis
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


# Set seed for reproducibility
np.random.seed(42)

# Create contingency table data: Titanic-style survival by class
# Rows: Passenger Class (First, Second, Third)
# Columns: Survived (Yes, No)
categories_1 = ["First", "Second", "Third"]
categories_2 = ["Survived", "Did Not Survive"]

# Frequency data (realistic Titanic-like proportions)
# Each row: [Survived, Did Not Survive]
contingency = np.array(
    [
        [136, 64],  # First class: 68% survival
        [87, 93],  # Second class: 48% survival
        [119, 381],  # Third class: 24% survival
    ]
)

# Calculate proportions for mosaic
row_totals = contingency.sum(axis=1)
total = contingency.sum()
col_widths = row_totals / total
col_heights = contingency / row_totals[:, np.newaxis]

# Color scheme using Python colors
colors = [
    ["#306998", "#FFD43B"],  # First class: Blue (survived), Yellow (not survived)
    ["#4A90C2", "#E8C547"],  # Second class: Lighter shades
    ["#6EB5E0", "#D4A84A"],  # Third class: Even lighter shades
]

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Gap between rectangles
gap = 0.02

# Draw mosaic rectangles
x_start = 0
for i, cat1 in enumerate(categories_1):
    width = col_widths[i] - gap
    y_start = 0

    for j in range(len(categories_2)):
        height = col_heights[i, j] - gap / 2

        # Draw rectangle
        rect = mpatches.FancyBboxPatch(
            (x_start + gap / 2, y_start + gap / 4),
            width,
            height,
            boxstyle="round,pad=0,rounding_size=0.01",
            facecolor=colors[i][j],
            edgecolor="white",
            linewidth=3,
        )
        ax.add_patch(rect)

        # Add frequency label in center of rectangle
        freq = contingency[i, j]
        cx = x_start + gap / 2 + width / 2
        cy = y_start + gap / 4 + height / 2

        # Only show label if rectangle is large enough
        if height > 0.08:
            ax.text(cx, cy, f"{freq}", ha="center", va="center", fontsize=20, fontweight="bold", color="white")

        y_start += height + gap / 2

    # Add class label below each column
    cx = x_start + gap / 2 + width / 2
    ax.text(cx, -0.08, cat1, ha="center", va="top", fontsize=18, fontweight="bold")

    x_start += col_widths[i]

# Calculate average y positions for row labels based on actual data
# Survived is the bottom section (index 0)
avg_survived_height = col_heights[:, 0].mean()
avg_not_survived_height = col_heights[:, 1].mean()

survived_y = avg_survived_height / 2
not_survived_y = avg_survived_height + avg_not_survived_height / 2

# Add row labels on the left side
ax.text(-0.04, survived_y, "Survived", ha="right", va="center", fontsize=18, fontweight="bold", rotation=0)
ax.text(-0.04, not_survived_y, "Did Not\nSurvive", ha="right", va="center", fontsize=18, fontweight="bold", rotation=0)

# Set axis properties
ax.set_xlim(-0.18, 1.02)
ax.set_ylim(-0.15, 1.05)
ax.set_aspect("equal")
ax.axis("off")

# Add title
ax.set_title(
    "Titanic Passenger Survival by Class · mosaic-categorical · matplotlib · pyplots.ai",
    fontsize=24,
    fontweight="bold",
    pad=20,
)

# Add legend
legend_elements = [
    mpatches.Patch(facecolor="#306998", edgecolor="white", linewidth=2, label="Survived"),
    mpatches.Patch(facecolor="#FFD43B", edgecolor="white", linewidth=2, label="Did Not Survive"),
]
ax.legend(handles=legend_elements, loc="upper right", fontsize=16, framealpha=0.95, edgecolor="gray")

# Add axis labels as text
ax.text(0.5, -0.13, "Passenger Class", ha="center", va="top", fontsize=20, fontweight="bold")
ax.text(-0.15, 0.5, "Survival Status", ha="right", va="center", fontsize=20, fontweight="bold", rotation=90)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
