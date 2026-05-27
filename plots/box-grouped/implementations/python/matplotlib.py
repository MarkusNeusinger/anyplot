""" anyplot.ai
box-grouped: Grouped Box Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-08
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (positions 1-3 for three subcategories)
COLORS = ["#009E73", "#C475FD", "#4467A3"]

# Data - Employee performance scores across departments and experience levels
np.random.seed(42)

categories = ["Sales", "Engineering", "Marketing", "Support"]
subcategories = ["Junior", "Mid-Level", "Senior"]

# Generate realistic performance data with varying distributions per department
data = {}
for cat_idx, cat in enumerate(categories):
    data[cat] = {}
    for sub_idx, sub in enumerate(subcategories):
        # Vary base performance by department (Sales lower, Support higher)
        dept_offset = cat_idx * 5
        base = 55 + sub_idx * 12 + dept_offset
        variance = 15 - sub_idx * 3
        n_points = np.random.randint(30, 60)
        scores = np.random.normal(base, variance, n_points)
        # Add outliers to some groups
        if np.random.random() > 0.6:
            outliers = np.random.choice([base - 25, base + 25], size=np.random.randint(1, 3))
            scores = np.concatenate([scores, outliers])
        data[cat][sub] = np.clip(scores, 0, 100)

# Create plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Calculate positions for grouped boxes
n_categories = len(categories)
n_subcategories = len(subcategories)
box_width = 0.25
group_gap = 0.4

# Plot boxes for each subcategory
for sub_idx, sub in enumerate(subcategories):
    positions = []
    box_data = []
    for cat_idx, cat in enumerate(categories):
        pos = cat_idx * (n_subcategories * box_width + group_gap) + sub_idx * box_width
        positions.append(pos)
        box_data.append(data[cat][sub])

    bp = ax.boxplot(
        box_data,
        positions=positions,
        widths=box_width * 0.8,
        patch_artist=True,
        showfliers=True,
        flierprops={"marker": "o", "markerfacecolor": COLORS[sub_idx], "markersize": 8, "alpha": 0.7},
        medianprops={"color": INK, "linewidth": 2.5},
        whiskerprops={"color": INK_SOFT, "linewidth": 1.5},
        capprops={"color": INK_SOFT, "linewidth": 1.5},
        boxprops={"linewidth": 1.5},
    )

    # Color the boxes with Okabe-Ito palette
    for patch in bp["boxes"]:
        patch.set_facecolor(COLORS[sub_idx])
        patch.set_alpha(0.85)
        patch.set_edgecolor(INK_SOFT)

# Set x-axis tick positions and labels
center_positions = [
    cat_idx * (n_subcategories * box_width + group_gap) + (n_subcategories - 1) * box_width / 2
    for cat_idx in range(n_categories)
]
ax.set_xticks(center_positions)
ax.set_xticklabels(categories, fontsize=20, color=INK)

# Labels and title
ax.set_xlabel("Department", fontsize=20, color=INK)
ax.set_ylabel("Performance Score (0-100)", fontsize=20, color=INK)
ax.set_title("box-grouped · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)

# Tick params
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT, labelcolor=INK_SOFT)

# Legend
legend_patches = [
    plt.Rectangle((0, 0), 1, 1, facecolor=COLORS[i], edgecolor=INK_SOFT, alpha=0.85) for i in range(len(subcategories))
]
leg = ax.legend(legend_patches, subcategories, loc="upper right", fontsize=16, framealpha=0.95)
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)

# Grid (y-axis only, subtle)
ax.yaxis.grid(True, alpha=0.12, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

# Spine styling
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
    ax.spines[s].set_linewidth(1.2)

# Y-axis limits
ax.set_ylim(0, 110)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
