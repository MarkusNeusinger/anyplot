""" anyplot.ai
histogram-basic: Basic Histogram
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-28
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgba


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # anyplot palette position 1 — ALWAYS first series
MEAN_COLOR = "#AE3030"  # matte red — semantic anchor for reference/alert
MED_COLOR = "#4467A3"  # anyplot palette position 3 — blue

# Data - exam scores with slight left skew and high-performer cluster
np.random.seed(42)
base = np.random.normal(loc=72, scale=12, size=450)
high_cluster = np.random.normal(loc=88, scale=4, size=50)
scores = np.clip(np.concatenate([base, high_cluster]), 0, 100)

# Title
title = "histogram-basic · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

n, bins, patches = ax.hist(scores, bins=25, color=BRAND, edgecolor=PAGE_BG, linewidth=1.2)

# Intensity-graded bar coloring via patch manipulation (matplotlib-distinctive)
max_count = max(n)
base_rgba = to_rgba(BRAND)
for count, patch in zip(n, patches, strict=True):
    intensity = 0.5 + 0.5 * (count / max_count)
    patch.set_facecolor((*base_rgba[:3], intensity * 0.85))

# Key statistics
mean_score = np.mean(scores)
median_score = np.median(scores)
y_max = max(n)
pct_above_80 = 100 * np.sum(scores >= 80) / len(scores)

# Mean line with annotation
ax.axvline(mean_score, color=MEAN_COLOR, linewidth=2.5, linestyle="--", zorder=5)
ax.annotate(
    f"Mean: {mean_score:.1f}",
    xy=(mean_score, y_max * 0.92),
    xytext=(mean_score - 18, y_max * 0.97),
    fontsize=8,
    fontweight="bold",
    color=MEAN_COLOR,
    arrowprops={"arrowstyle": "->", "color": MEAN_COLOR, "lw": 1.8},
    bbox={"boxstyle": "round,pad=0.3", "facecolor": ELEVATED_BG, "edgecolor": MEAN_COLOR, "alpha": 0.9},
    zorder=6,
)

# Median line with annotation
ax.axvline(median_score, color=MED_COLOR, linewidth=2.5, linestyle=":", zorder=5)
ax.annotate(
    f"Median: {median_score:.1f}",
    xy=(median_score, y_max * 0.78),
    xytext=(median_score + 9, y_max * 0.86),
    fontsize=8,
    fontweight="bold",
    color=MED_COLOR,
    arrowprops={"arrowstyle": "->", "color": MED_COLOR, "lw": 1.8},
    bbox={"boxstyle": "round,pad=0.3", "facecolor": ELEVATED_BG, "edgecolor": MED_COLOR, "alpha": 0.9},
    zorder=6,
)

# High-performer cluster annotation with percentage insight
ax.annotate(
    f"High-performer cluster\n{pct_above_80:.0f}% scored above 80",
    xy=(88, y_max * 0.35),
    xytext=(96, y_max * 0.58),
    fontsize=8,
    fontstyle="italic",
    color=INK_SOFT,
    ha="center",
    arrowprops={"arrowstyle": "->", "color": INK_SOFT, "lw": 1.5, "connectionstyle": "arc3,rad=-0.2"},
    bbox={"boxstyle": "round,pad=0.3", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.9},
    zorder=6,
)

# Labels and styling
ax.set_xlabel("Exam Score (points)", fontsize=10, color=INK)
ax.set_ylabel("Frequency (count)", fontsize=10, color=INK)
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=12)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

# Spine removal
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Subtle y-axis grid
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

# Y-axis starts at zero
ax.set_ylim(bottom=0)

fig.subplots_adjust(left=0.09, right=0.97, top=0.91, bottom=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
