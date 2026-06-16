""" anyplot.ai
parallel-categories-basic: Basic Parallel Categories Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-13
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.path import Path


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data: Product purchase flow (Channel -> Category -> Outcome)
np.random.seed(42)

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

# Okabe-Ito palette for channel colors
colors = {"Online": "#009E73", "Store": "#C475FD", "Mobile": "#4467A3"}

# Create figure
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

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

    heights = {cat: counts.get(cat, 0) / total for cat in cats}

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

    flow_counts = df.groupby([dim1, dim2]).size().reset_index(name="count")

    current_y_left = {cat: category_positions[dim1][cat][0] for cat in dim_categories[dim1]}
    current_y_right = {cat: category_positions[dim2][cat][0] for cat in dim_categories[dim2]}

    total = len(df)

    for _, row in flow_counts.iterrows():
        cat1 = row[dim1]
        cat2 = row[dim2]
        count = row["count"]

        y1_top = current_y_left[cat1] + (count / df[dim1].value_counts()[cat1]) * (
            category_positions[dim1][cat1][1] - category_positions[dim1][cat1][0]
        )

        y2_bottom = current_y_right[cat2]
        y2_top = current_y_right[cat2] + (count / df[dim2].value_counts()[cat2]) * (
            category_positions[dim2][cat2][1] - category_positions[dim2][cat2][0]
        )

        y1_bottom = current_y_left[cat1]

        x_ctrl1 = x1 + dim_width + (x2 - x1 - 2 * dim_width) * 0.4
        x_ctrl2 = x1 + dim_width + (x2 - x1 - 2 * dim_width) * 0.6

        vertices = [
            (x1 + dim_width, y1_bottom),
            (x_ctrl1, y1_bottom),
            (x_ctrl2, y2_bottom),
            (x2 - dim_width, y2_bottom),
            (x2 - dim_width, y2_top),
            (x_ctrl2, y2_top),
            (x_ctrl1, y1_top),
            (x1 + dim_width, y1_top),
            (x1 + dim_width, y1_bottom),
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

        if i == 0:
            color = colors[cat1]
        else:
            orig_cat = df[df[dim1] == cat1]["Channel"].mode()
            if len(orig_cat) > 0:
                color = colors.get(orig_cat.iloc[0], INK_SOFT)
            else:
                color = INK_SOFT

        patch = mpatches.PathPatch(path, facecolor=color, edgecolor=PAGE_BG, linewidth=0.5, alpha=0.6)
        ax.add_patch(patch)

        current_y_left[cat1] = y1_top
        current_y_right[cat2] = y2_top

# Draw category bars
for i, dim in enumerate(dimensions):
    x = x_positions[i]
    for cat in dim_categories[dim]:
        y_start, y_end = category_positions[dim][cat]

        rect = mpatches.Rectangle(
            (x - dim_width, y_start),
            dim_width * 2,
            y_end - y_start,
            facecolor=ELEVATED_BG,
            edgecolor=INK_SOFT,
            linewidth=2,
        )
        ax.add_patch(rect)

        ax.text(x, (y_start + y_end) / 2, cat, ha="center", va="center", fontsize=14, fontweight="bold", color=INK)

# Add dimension labels
for i, dim in enumerate(dimensions):
    ax.text(x_positions[i], 1.02, dim, ha="center", va="bottom", fontsize=20, fontweight="bold", color=INK)

# Styling
ax.set_xlim(-0.15, 1.15)
ax.set_ylim(-0.05, 1.15)
ax.set_aspect("equal")
ax.axis("off")

# Title
ax.set_title("parallel-categories-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", pad=20, color=INK)

# Legend
legend_patches = [mpatches.Patch(color=colors[ch], alpha=0.6, label=ch) for ch in ["Online", "Store", "Mobile"]]
leg = ax.legend(
    handles=legend_patches,
    loc="lower right",
    fontsize=16,
    title="Channel",
    title_fontsize=18,
    bbox_to_anchor=(1.12, 0.0),
)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
