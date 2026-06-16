""" anyplot.ai
cat-box-strip: Box Plot with Strip Overlay
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-13
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

BRAND = "#009E73"  # Okabe-Ito position 1

# Data - Generate groups with different distributions to showcase features
np.random.seed(42)

categories = ["Control", "Treatment A", "Treatment B", "Treatment C"]
n_points = [35, 40, 30, 45]  # Different sample sizes per group

# Create varied distributions to show boxplot features
data = {
    "Control": np.random.normal(50, 8, n_points[0]),
    "Treatment A": np.random.normal(65, 12, n_points[1]),  # Higher mean, more spread
    "Treatment B": np.concatenate(
        [  # Bimodal with outliers
            np.random.normal(45, 5, n_points[2] - 3),
            np.array([15, 80, 82]),  # Outliers
        ]
    ),
    "Treatment C": np.random.normal(55, 6, n_points[3]),  # Moderate
}

# Prepare data for plotting
box_data = [data[cat] for cat in categories]
positions = np.arange(len(categories)) + 1

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Box plot
ax.boxplot(
    box_data,
    positions=positions,
    tick_labels=categories,
    widths=0.5,
    patch_artist=True,
    boxprops={"facecolor": BRAND, "alpha": 0.4, "linewidth": 2, "edgecolor": INK_SOFT},
    medianprops={"color": "#AE3030", "linewidth": 3},
    whiskerprops={"color": INK_SOFT, "linewidth": 2},
    capprops={"color": INK_SOFT, "linewidth": 2},
    flierprops={
        "marker": "o",
        "markerfacecolor": BRAND,
        "markersize": 10,
        "alpha": 0.7,
        "markeredgecolor": INK_SOFT,
        "markeredgewidth": 1,
    },
)

# Strip plot overlay - add jittered points
for pos, cat in zip(positions, categories, strict=True):
    y = data[cat]
    # Jitter x positions
    x = np.random.normal(pos, 0.08, len(y))
    ax.scatter(x, y, s=100, alpha=0.6, color=BRAND, edgecolor=PAGE_BG, linewidth=1, zorder=3)

# Style
ax.set_xlabel("Treatment Group", fontsize=20, color=INK)
ax.set_ylabel("Response Value (score)", fontsize=20, color=INK)
ax.set_title("cat-box-strip · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT, labelcolor=INK_SOFT)

# Spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Grid
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

# Adjust y-axis to show all data including outliers
ax.set_ylim(0, 100)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
