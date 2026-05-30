""" anyplot.ai
density-basic: Basic Density Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-30
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy import stats


# Theme tokens — Imprint palette + theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1 — always first series

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Data — bimodal API response latencies: cache hits (fast) vs. cache misses (slow)
np.random.seed(42)
latencies = np.concatenate(
    [
        np.random.normal(45, 12, 350),  # Cache hit: fast path ~45ms
        np.random.normal(185, 40, 150),  # Cache miss: slow path ~185ms
    ]
)
latencies = np.clip(latencies, 5, 320)

# Pre-compute KDE peaks for annotation placement
kde_func = stats.gaussian_kde(latencies)
x_fine = np.linspace(5, 310, 1000)
y_fine = kde_func(x_fine)

peak1_mask = x_fine < 120
peak1_x = x_fine[peak1_mask][np.argmax(y_fine[peak1_mask])]
peak1_y = np.max(y_fine[peak1_mask])

peak2_mask = x_fine >= 120
peak2_x = x_fine[peak2_mask][np.argmax(y_fine[peak2_mask])]
peak2_y = np.max(y_fine[peak2_mask])

# Canvas: 3200 × 1800 px (16:9 landscape)
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# KDE with native seaborn fill (idiomatic fill=True)
sns.kdeplot(data=latencies, ax=ax, fill=True, alpha=0.35, color=BRAND, linewidth=2.5, bw_adjust=0.9)

# Rug plot showing individual observations
sns.rugplot(data=latencies, ax=ax, color=BRAND, alpha=0.3, height=0.04)

# Peak annotations
ax.annotate(
    "Cache hit",
    xy=(peak1_x, peak1_y),
    xytext=(peak1_x - 18, peak1_y * 0.65),
    fontsize=8,
    fontweight="medium",
    color=INK,
    arrowprops={"arrowstyle": "->", "color": INK_SOFT, "lw": 1.2},
    ha="center",
    va="top",
)
ax.annotate(
    "Cache miss",
    xy=(peak2_x, peak2_y),
    xytext=(peak2_x + 32, peak2_y + peak1_y * 0.18),
    fontsize=8,
    fontweight="medium",
    color=INK,
    arrowprops={"arrowstyle": "->", "color": INK_SOFT, "lw": 1.2},
    ha="center",
    va="bottom",
)

# Style
title = "density-basic · python · seaborn · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_fontsize = max(8, round(12 * ratio))

ax.set_xlabel("Response Latency (ms)", fontsize=10, color=INK)
ax.set_ylabel("Density", fontsize=10, color=INK)
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)
ax.set_xlim(left=0)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8)

plt.tight_layout()
# No bbox_inches='tight' — preserves exact 3200×1800 canvas
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
