""" pyplots.ai
histogram-basic: Basic Histogram
Library: seaborn 0.13.2 | Python 3.14.0
Quality: 95/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import seaborn as sns


# Data - simulated exam scores with multimodal distribution
np.random.seed(42)
main_group = np.random.normal(loc=72, scale=10, size=350)
high_achievers = np.random.normal(loc=92, scale=4, size=120)
low_tail = np.random.uniform(30, 50, size=30)
values = np.concatenate([main_group, high_achievers, low_tail])

# Statistics for storytelling
mean_val = np.mean(values)
median_val = np.median(values)

# Seaborn theme — leverages sns.set_theme for cohesive styling
sns.set_theme(
    style="whitegrid",
    rc={
        "axes.facecolor": "#FAFBFC",
        "figure.facecolor": "#FFFFFF",
        "grid.color": "#E0E4E8",
        "grid.alpha": 0.5,
        "grid.linewidth": 0.6,
        "axes.edgecolor": "#BBBFC4",
        "axes.linewidth": 0.8,
        "font.family": "sans-serif",
    },
)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Histogram — seaborn axes-level API with stat="count"
sns.histplot(values, bins=30, color="#306998", edgecolor="white", linewidth=1.0, alpha=0.82, stat="count", ax=ax)

# Separate KDE overlay — seaborn kdeplot for styled density curve
ax2 = ax.twinx()
sns.kdeplot(values, color="#1A3A5C", linewidth=2.5, alpha=0.85, ax=ax2)
ax2.set_ylabel("")
ax2.set_yticks([])
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

# Rug plot — seaborn-distinctive feature showing individual observations
sns.rugplot(values, color="#306998", alpha=0.08, height=0.02, ax=ax)

# Storytelling: annotate mean and median lines
ax.axvline(mean_val, color="#D35400", linewidth=2, linestyle="--", alpha=0.85, zorder=5)
ax.axvline(median_val, color="#27AE60", linewidth=2, linestyle="-.", alpha=0.85, zorder=5)

y_top = ax.get_ylim()[1]

# Mean label — placed to the right of the mean line, mid-height
ax.text(
    mean_val + 1.5,
    y_top * 0.52,
    f"Mean\n{mean_val:.1f}",
    fontsize=13,
    fontweight="bold",
    color="#D35400",
    ha="left",
    va="center",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#D35400", "alpha": 0.9},
)
# Median label — placed to the left of the median line, mid-height
ax.text(
    median_val - 1.5,
    y_top * 0.38,
    f"Median\n{median_val:.1f}",
    fontsize=13,
    fontweight="bold",
    color="#27AE60",
    ha="right",
    va="center",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#27AE60", "alpha": 0.9},
)

# Storytelling: label the two modes with arrows from empty regions
ax.annotate(
    "Primary mode\n~72 pts",
    xy=(70, y_top * 0.88),
    xytext=(42, y_top * 0.88),
    fontsize=13,
    fontstyle="italic",
    color="#555555",
    ha="center",
    va="center",
    arrowprops={"arrowstyle": "-|>", "color": "#888888", "lw": 1.3},
)
ax.annotate(
    "Secondary mode\n~92 pts",
    xy=(91, y_top * 0.72),
    xytext=(105, y_top * 0.80),
    fontsize=13,
    fontstyle="italic",
    color="#555555",
    ha="center",
    va="center",
    arrowprops={"arrowstyle": "-|>", "color": "#888888", "lw": 1.3},
)

# Style — typography hierarchy
ax.set_title("histogram-basic · seaborn · pyplots.ai", fontsize=24, fontweight="semibold", color="#1A1A2E", pad=16)
ax.set_xlabel("Exam Score (points)", fontsize=20, color="#333333", labelpad=10)
ax.set_ylabel("Frequency (count)", fontsize=20, color="#333333", labelpad=10)
ax.tick_params(axis="both", labelsize=16, colors="#555555")

# Layout — tighten x-axis to data range, remove top/right spines
ax.set_xlim(25, 110)
ax.set_ylim(bottom=0)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_alpha(0.4)
ax.spines["bottom"].set_alpha(0.4)
ax.xaxis.set_major_locator(ticker.MultipleLocator(10))
ax.yaxis.grid(True)
ax.xaxis.grid(False)

# Subtitle with sample size
ax.text(
    0.99,
    0.97,
    f"n = {len(values)} students",
    transform=ax.transAxes,
    fontsize=13,
    color="#777777",
    ha="right",
    va="top",
    fontstyle="italic",
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
