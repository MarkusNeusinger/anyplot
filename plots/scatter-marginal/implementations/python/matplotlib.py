""" anyplot.ai
scatter-marginal: Scatter Plot with Marginal Distributions
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - correlated bivariate data with realistic pattern
np.random.seed(42)
n = 200

# Create correlated data with bimodal structure
x = np.concatenate([np.random.normal(30, 8, n // 2), np.random.normal(60, 10, n // 2)])
y = 0.7 * x + np.random.normal(0, 8, n) + 10

# Create figure with GridSpec for layout
fig = plt.figure(figsize=(16, 9), facecolor=PAGE_BG)
gs = GridSpec(4, 4, figure=fig, hspace=0.05, wspace=0.05)

# Main scatter plot (lower-left, 3x3)
ax_main = fig.add_subplot(gs[1:4, 0:3], facecolor=PAGE_BG)
ax_main.scatter(x, y, s=100, alpha=0.65, color=BRAND, edgecolors=PAGE_BG, linewidth=0.5)
ax_main.set_xlabel("Feature A", fontsize=20, color=INK)
ax_main.set_ylabel("Feature B", fontsize=20, color=INK)
ax_main.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax_main.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
for s in ("left", "bottom"):
    ax_main.spines[s].set_color(INK_SOFT)
ax_main.spines["top"].set_visible(False)
ax_main.spines["right"].set_visible(False)

# Top marginal histogram (aligned with main x-axis)
ax_top = fig.add_subplot(gs[0, 0:3], sharex=ax_main, facecolor=PAGE_BG)
ax_top.hist(x, bins=25, color=BRAND, alpha=0.5, edgecolor=PAGE_BG, linewidth=0.5)
ax_top.tick_params(axis="x", labelbottom=False, colors=INK_SOFT)
ax_top.tick_params(axis="y", labelsize=14, colors=INK_SOFT)
ax_top.set_ylabel("Count", fontsize=16, color=INK)
ax_top.spines["top"].set_visible(False)
ax_top.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax_top.spines[s].set_color(INK_SOFT)
ax_top.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Right marginal histogram (aligned with main y-axis)
ax_right = fig.add_subplot(gs[1:4, 3], sharey=ax_main, facecolor=PAGE_BG)
ax_right.hist(y, bins=25, orientation="horizontal", color=BRAND, alpha=0.5, edgecolor=PAGE_BG, linewidth=0.5)
ax_right.tick_params(axis="y", labelleft=False, colors=INK_SOFT)
ax_right.tick_params(axis="x", labelsize=14, colors=INK_SOFT)
ax_right.set_xlabel("Count", fontsize=16, color=INK)
ax_right.spines["top"].set_visible(False)
ax_right.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax_right.spines[s].set_color(INK_SOFT)
ax_right.xaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Title
fig.text(
    0.5,
    0.98,
    "scatter-marginal · matplotlib · anyplot.ai",
    fontsize=24,
    ha="center",
    va="top",
    color=INK,
    fontweight="medium",
)

plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
