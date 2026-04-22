""" pyplots.ai
parallel-categories-basic: Basic Parallel Categories Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.path import Path


# Data: Product purchase flow (Channel -> Category -> Outcome)
np.random.seed(42)

# Create synthetic categorical data representing customer purchase flow
n_samples = 500
channels = np.random.choice(["Online", "Store", "Mobile"], size=n_samples, p=[0.4, 0.35, 0.25])
categories = np.random.choice(["Electronics", "Clothing", "Home", "Sports"], size=n_samples, p=[0.3, 0.25, 0.25, 0.2])
outcomes = np.random.choice(["Purchased", "Returned", "Abandoned"], size=n_samples, p=[0.6, 0.15, 0.25])

df = pd.DataFrame({"Channel": channels, "Category": categories, "Outcome": outcomes})

# Define dimensions and their categories
dimensions = ["Channel", "Category", "Outcome"]
dim_categories = {
    "Channel": ["Online", "Store", "Mobile"],
    "Category": ["Electronics", "Clothing", "Home", "Sports"],
    "Outcome": ["Purchased", "Returned", "Abandoned"],
}

# Color palette for the first dimension (source) - distinct colors for clear differentiation
colors = {"Online": "#1F77B4", "Store": "#FF7F0E", "Mobile": "#2CA02C"}

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Calculate positions for each dimension
n_dims = len(dimensions)
x_positions = np.linspace(0, 1, n_dims)
dim_width = 0.08

# Calculate category positions within each dimension
category_positions = {}
category_heights = {}

for dim in dimensions:
    cats = dim_categories[dim]
    counts = df[dim].value_counts()
    total = counts.sum()

    # Calculate heights proportional to counts
    heights = {cat: counts.get(cat, 0) / total for cat in cats}

    # Stack categories vertically
    y_start = 0.05
    y_end = 0.95
    available_height = y_end - y_start
    gap = 0.02
    total_gap = gap * (len(cats) - 1)
    usable_height = available_height - total_gap

    positions = {}
    current_y = y_start
    for cat in cats:
        h = heights[cat] * usable_height
        positions[cat] = (current_y, current_y + h)
        current_y += h + gap

    category_positions[dim] = positions
    category_heights[dim] = heights

# Draw ribbons between consecutive dimensions
for i in range(n_dims - 1):
    dim1 = dimensions[i]
    dim2 = dimensions[i + 1]
    x1 = x_positions[i]
    x2 = x_positions[i + 1]

    # Get flow counts between categories
    flow_counts = df.groupby([dim1, dim2]).size().reset_index(name="count")

    # Track current y position for each category to stack ribbons
    current_y_left = {cat: category_positions[dim1][cat][0] for cat in dim_categories[dim1]}
    current_y_right = {cat: category_positions[dim2][cat][0] for cat in dim_categories[dim2]}

    total = len(df)

    for _, row in flow_counts.iterrows():
        cat1 = row[dim1]
        cat2 = row[dim2]
        count = row["count"]

        # Calculate ribbon heights
        h1 = (
            (count / total)
            * (category_positions[dim1][cat1][1] - category_positions[dim1][cat1][0])
            / category_heights[dim1][cat1]
        )
        h2 = (
            (count / total)
            * (category_positions[dim2][cat2][1] - category_positions[dim2][cat2][0])
            / category_heights[dim2][cat2]
        )

        # Ribbon corners
        y1_bottom = current_y_left[cat1]
        y1_top = (
            y1_bottom + h1 * (category_positions[dim1][cat1][1] - category_positions[dim1][cat1][0]) / h1
            if h1 > 0
            else y1_bottom
        )
        y1_top = current_y_left[cat1] + (count / df[dim1].value_counts()[cat1]) * (
            category_positions[dim1][cat1][1] - category_positions[dim1][cat1][0]
        )

        y2_bottom = current_y_right[cat2]
        y2_top = current_y_right[cat2] + (count / df[dim2].value_counts()[cat2]) * (
            category_positions[dim2][cat2][1] - category_positions[dim2][cat2][0]
        )

        # Create bezier path for smooth ribbon
        x_ctrl1 = x1 + dim_width + (x2 - x1 - 2 * dim_width) * 0.4
        x_ctrl2 = x1 + dim_width + (x2 - x1 - 2 * dim_width) * 0.6

        # Path vertices
        vertices = [
            (x1 + dim_width, y1_bottom),  # Start bottom left
            (x_ctrl1, y1_bottom),  # Control point 1
            (x_ctrl2, y2_bottom),  # Control point 2
            (x2 - dim_width, y2_bottom),  # End bottom right
            (x2 - dim_width, y2_top),  # End top right
            (x_ctrl2, y2_top),  # Control point 3
            (x_ctrl1, y1_top),  # Control point 4
            (x1 + dim_width, y1_top),  # Start top left
            (x1 + dim_width, y1_bottom),  # Close path
        ]

        codes = [
            Path.MOVETO,
            Path.CURVE4,
            Path.CURVE4,
            Path.CURVE4,
            Path.LINETO,
            Path.CURVE4,
            Path.CURVE4,
            Path.CURVE4,
            Path.CLOSEPOLY,
        ]

        path = Path(vertices, codes)

        # Get color based on first dimension category
        if i == 0:
            color = colors[cat1]
        else:
            # For subsequent flows, trace back to original channel
            orig_cat = df[df[dim1] == cat1]["Channel"].mode()
            if len(orig_cat) > 0:
                color = colors.get(orig_cat.iloc[0], "#306998")
            else:
                color = "#306998"

        patch = mpatches.PathPatch(path, facecolor=color, edgecolor="white", linewidth=0.5, alpha=0.6)
        ax.add_patch(patch)

        # Update current positions
        current_y_left[cat1] = y1_top
        current_y_right[cat2] = y2_top

# Draw category bars
for i, dim in enumerate(dimensions):
    x = x_positions[i]
    for cat in dim_categories[dim]:
        y_start, y_end = category_positions[dim][cat]

        # Draw rectangle for category
        rect = mpatches.Rectangle(
            (x - dim_width, y_start),
            dim_width * 2,
            y_end - y_start,
            facecolor="#2C3E50",
            edgecolor="white",
            linewidth=2,
        )
        ax.add_patch(rect)

        # Add category label
        ax.text(x, (y_start + y_end) / 2, cat, ha="center", va="center", fontsize=14, fontweight="bold", color="white")

# Add dimension labels
for i, dim in enumerate(dimensions):
    ax.text(x_positions[i], 1.02, dim, ha="center", va="bottom", fontsize=20, fontweight="bold", color="#2C3E50")

# Styling
ax.set_xlim(-0.15, 1.15)
ax.set_ylim(-0.05, 1.15)
ax.set_aspect("equal")
ax.axis("off")

# Title
ax.set_title(
    "parallel-categories-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="bold", pad=20, color="#2C3E50"
)

# Legend
legend_patches = [mpatches.Patch(color=colors[ch], alpha=0.6, label=ch) for ch in ["Online", "Store", "Mobile"]]
ax.legend(
    handles=legend_patches,
    loc="lower right",
    fontsize=16,
    title="Channel",
    title_fontsize=18,
    framealpha=0.9,
    bbox_to_anchor=(1.12, 0.0),
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
