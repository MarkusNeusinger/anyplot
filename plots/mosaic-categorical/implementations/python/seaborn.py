""" pyplots.ai
mosaic-categorical: Mosaic Plot for Categorical Association Analysis
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Set seed for reproducibility
np.random.seed(42)

# Load Titanic dataset using seaborn's built-in data
df = sns.load_dataset("titanic")

# Apply seaborn theme for consistent styling
sns.set_theme(style="white", context="talk", font_scale=1.2)

# Create contingency table from actual Titanic data
contingency_df = df.groupby(["class", "survived"], observed=True).size().unstack(fill_value=0)

# Reorder to match expected format: [Survived, Did Not Survive]
contingency = contingency_df[[1, 0]].values  # 1=Survived, 0=Not Survived
categories_1 = ["First", "Second", "Third"]
categories_2 = ["Survived", "Did Not Survive"]

# Calculate proportions for mosaic
row_totals = contingency.sum(axis=1)
total = contingency.sum()
col_widths = row_totals / total
col_heights = contingency / row_totals[:, np.newaxis]

# Use seaborn colorblind palette for accessibility
palette = sns.color_palette("colorblind", n_colors=2)
color_survived = palette[0]  # Blue
color_not_survived = palette[1]  # Orange

# Create figure with larger canvas utilization
fig, ax = plt.subplots(figsize=(16, 9))

# Gap between rectangles
gap = 0.015

# Define plot area to maximize canvas usage
plot_left = 0.15
plot_bottom = 0.12
plot_width = 0.75
plot_height = 0.75

# Draw mosaic rectangles with improved layout
x_start = plot_left
for i, cat1 in enumerate(categories_1):
    width = col_widths[i] * plot_width - gap
    y_start = plot_bottom

    for j in range(len(categories_2)):
        height = col_heights[i, j] * plot_height - gap / 2

        # Color: Blue for survived (j=0), Orange for not survived (j=1)
        color = color_survived if j == 0 else color_not_survived

        # Draw rectangle with rounded corners
        rect = mpatches.FancyBboxPatch(
            (x_start + gap / 2, y_start + gap / 4),
            width,
            height,
            boxstyle="round,pad=0,rounding_size=0.008",
            facecolor=color,
            edgecolor="white",
            linewidth=3,
        )
        ax.add_patch(rect)

        # Add frequency label in center of rectangle
        freq = contingency[i, j]
        cx = x_start + gap / 2 + width / 2
        cy = y_start + gap / 4 + height / 2

        # Only show label if rectangle is large enough
        if height > 0.05:
            ax.text(cx, cy, f"{freq}", ha="center", va="center", fontsize=22, fontweight="bold", color="white")

        y_start += height + gap / 2

    # Add class label below each column
    cx = x_start + gap / 2 + width / 2
    ax.text(cx, plot_bottom - 0.04, cat1, ha="center", va="top", fontsize=18, fontweight="bold")

    x_start += col_widths[i] * plot_width

# Calculate y positions for row labels based on average heights
avg_survived_height = col_heights[:, 0].mean() * plot_height
avg_not_survived_height = col_heights[:, 1].mean() * plot_height

survived_y = plot_bottom + avg_survived_height / 2
not_survived_y = plot_bottom + avg_survived_height + avg_not_survived_height / 2

# Add row labels on the left side
ax.text(plot_left - 0.02, survived_y, "Survived", ha="right", va="center", fontsize=18, fontweight="bold", rotation=0)
ax.text(
    plot_left - 0.02,
    not_survived_y,
    "Did Not\nSurvive",
    ha="right",
    va="center",
    fontsize=18,
    fontweight="bold",
    rotation=0,
)

# Set axis limits to show full plot
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_aspect("auto")
ax.axis("off")

# Add title with seaborn's title style
ax.set_title(
    "Titanic Passenger Survival by Class · mosaic-categorical · seaborn · pyplots.ai",
    fontsize=24,
    fontweight="bold",
    pad=15,
    loc="center",
)

# Create legend using seaborn palette colors
legend_elements = [
    mpatches.Patch(facecolor=color_survived, edgecolor="white", linewidth=2, label="Survived"),
    mpatches.Patch(facecolor=color_not_survived, edgecolor="white", linewidth=2, label="Did Not Survive"),
]
ax.legend(
    handles=legend_elements,
    loc="upper right",
    fontsize=16,
    framealpha=0.95,
    edgecolor="gray",
    bbox_to_anchor=(0.98, 0.98),
)

# Add axis labels
ax.text(
    plot_left + plot_width / 2,
    plot_bottom - 0.09,
    "Passenger Class",
    ha="center",
    va="top",
    fontsize=20,
    fontweight="bold",
)
ax.text(
    0.02,
    plot_bottom + plot_height / 2,
    "Survival Status",
    ha="left",
    va="center",
    fontsize=20,
    fontweight="bold",
    rotation=90,
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
