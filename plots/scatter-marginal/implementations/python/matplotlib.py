"""anyplot.ai
scatter-marginal: Scatter Plot with Marginal Distributions
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpec


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 is the brand green
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

# Columns: set these to your table's column names
FEATURE_A = "Feature A"  # role: x
FEATURE_B = "Feature B"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("measurements.csv")
rng = np.random.default_rng(42)
n = 200
x = np.concatenate([rng.normal(30, 8, n // 2), rng.normal(60, 10, n // 2)])
y = 0.7 * x + rng.normal(0, 8, n) + 10
df = pd.DataFrame({FEATURE_A: x, FEATURE_B: y})

# Plot: reads only df and the constants above
fig = plt.figure(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
gs = GridSpec(4, 4, figure=fig, hspace=0.05, wspace=0.05, left=0.08, right=0.97, top=0.88, bottom=0.12)

# Main scatter plot (lower-left, 3x3)
ax_main = fig.add_subplot(gs[1:4, 0:3], facecolor=PAGE_BG)
ax_main.scatter(df[FEATURE_A], df[FEATURE_B], s=45, alpha=0.65, color=BRAND, edgecolors=PAGE_BG, linewidth=0.4)
ax_main.set_xlabel(FEATURE_A, fontsize=10, color=INK)
ax_main.set_ylabel(FEATURE_B, fontsize=10, color=INK)

# Top marginal histogram, sharing the scatter's x axis
ax_top = fig.add_subplot(gs[0, 0:3], sharex=ax_main, facecolor=PAGE_BG)
ax_top.hist(df[FEATURE_A], bins=25, color=BRAND, alpha=0.5, edgecolor=PAGE_BG, linewidth=0.4)
ax_top.set_ylabel("Count", fontsize=9, color=INK)
ax_top.tick_params(axis="x", labelbottom=False)

# Right marginal histogram, sharing the scatter's y axis
ax_right = fig.add_subplot(gs[1:4, 3], sharey=ax_main, facecolor=PAGE_BG)
ax_right.hist(
    df[FEATURE_B], bins=25, orientation="horizontal", color=BRAND, alpha=0.5, edgecolor=PAGE_BG, linewidth=0.4
)
ax_right.set_xlabel("Count", fontsize=9, color=INK)
ax_right.tick_params(axis="y", labelleft=False)

# Shared chrome
for ax in (ax_main, ax_top, ax_right):
    ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK_SOFT)
for ax in (ax_main, ax_top):
    ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax_right.xaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

fig.suptitle("scatter-marginal · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, y=0.97)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
