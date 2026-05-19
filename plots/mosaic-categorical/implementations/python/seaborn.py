"""anyplot.ai
mosaic-categorical: Mosaic Plot for Categorical Association Analysis
Library: seaborn | Python 3.13
Quality: 91/100 | Updated: 2026-05-19
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette — first series always #009E73
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]
color_survived = OKABE_ITO[0]  # bluish green
color_not_survived = OKABE_ITO[1]  # vermillion

sns.set_theme(
    style="white",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Data
df = sns.load_dataset("titanic")

# Contingency table: rows = passenger class, columns = [Survived, Did Not Survive]
contingency_df = df.groupby(["class", "survived"], observed=True).size().unstack(fill_value=0)
contingency = contingency_df[[1, 0]].values  # 1=Survived first
categories_1 = ["First", "Second", "Third"]
categories_2 = ["Survived", "Did Not Survive"]

# Calculate proportions
row_totals = contingency.sum(axis=1)
total = contingency.sum()
col_widths = row_totals / total
col_heights = contingency / row_totals[:, np.newaxis]

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

gap = 0.015
plot_left = 0.15
plot_bottom = 0.12
plot_width = 0.75
plot_height = 0.75

# Draw mosaic rectangles
x_start = plot_left
for i, cat1 in enumerate(categories_1):
    width = col_widths[i] * plot_width - gap
    y_start = plot_bottom

    for j in range(len(categories_2)):
        height = col_heights[i, j] * plot_height - gap / 2
        color = color_survived if j == 0 else color_not_survived

        rect = mpatches.FancyBboxPatch(
            (x_start + gap / 2, y_start + gap / 4),
            width,
            height,
            boxstyle="round,pad=0,rounding_size=0.008",
            facecolor=color,
            edgecolor=PAGE_BG,
            linewidth=3,
        )
        ax.add_patch(rect)

        freq = contingency[i, j]
        cx = x_start + gap / 2 + width / 2
        cy = y_start + gap / 4 + height / 2
        if height > 0.05:
            ax.text(cx, cy, f"{freq}", ha="center", va="center", fontsize=22, fontweight="bold", color="white")

        y_start += height + gap / 2

    cx = x_start + gap / 2 + width / 2
    ax.text(cx, plot_bottom - 0.04, cat1, ha="center", va="top", fontsize=18, fontweight="bold", color=INK)

    x_start += col_widths[i] * plot_width

# Row labels on the left
avg_survived_h = col_heights[:, 0].mean() * plot_height
avg_not_survived_h = col_heights[:, 1].mean() * plot_height
survived_y = plot_bottom + avg_survived_h / 2
not_survived_y = plot_bottom + avg_survived_h + avg_not_survived_h / 2

ax.text(plot_left - 0.02, survived_y, "Survived", ha="right", va="center", fontsize=18, fontweight="bold", color=INK)
ax.text(
    plot_left - 0.02,
    not_survived_y,
    "Did Not\nSurvive",
    ha="right",
    va="center",
    fontsize=18,
    fontweight="bold",
    color=INK,
)

ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_aspect("auto")
ax.axis("off")

# Title
ax.set_title(
    "Titanic Passenger Survival by Class · mosaic-categorical · python · seaborn · anyplot.ai",
    fontsize=24,
    fontweight="bold",
    pad=15,
    loc="center",
    color=INK,
)

# Legend — anchored inside the right margin of the plot area
legend_elements = [
    mpatches.Patch(facecolor=color_survived, edgecolor=PAGE_BG, linewidth=2, label="Survived"),
    mpatches.Patch(facecolor=color_not_survived, edgecolor=PAGE_BG, linewidth=2, label="Did Not Survive"),
]
ax.legend(
    handles=legend_elements,
    loc="center left",
    fontsize=16,
    framealpha=0.95,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    bbox_to_anchor=(0.91, 0.50),
    labelcolor=INK,
)

# Axis labels
ax.text(
    plot_left + plot_width / 2,
    plot_bottom - 0.09,
    "Passenger Class",
    ha="center",
    va="top",
    fontsize=20,
    fontweight="bold",
    color=INK,
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
    color=INK,
)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
