""" anyplot.ai
scatter-regression-lowess: Scatter Plot with LOWESS Regression
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 76/100 | Updated: 2026-11-21
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 for the points, position 2 for the LOWESS curve
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Configure theme
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
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Columns: set these to your table's column names
INPUT = "Input variable (x)"  # role: x
RESPONSE = "Response variable (y)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("measurements.csv")
np.random.seed(42)
n_points = 200
x = np.linspace(0, 10, n_points)

# Non-linear pattern: steep rise 0-2, plateau 2-5, sharp dip 5-6, gentle rise 6-10
signal = np.where(x < 2, 3 * x, 6) + np.where((x >= 5) & (x < 6), -4 * (x - 5), 0) + np.where(x >= 6, 0.5 * (x - 6), 0)
df = pd.DataFrame({INPUT: x, RESPONSE: signal + np.random.normal(0, 0.6, n_points)})

# Plot: reads only df and the constants above
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

sns.regplot(
    data=df,
    x=INPUT,
    y=RESPONSE,
    lowess=True,
    scatter_kws={"alpha": 0.6, "s": 40, "color": IMPRINT_PALETTE[0], "edgecolors": PAGE_BG, "linewidths": 0.3},
    line_kws={"color": IMPRINT_PALETTE[1], "linewidth": 2.5},
    ax=ax,
)

# Style
ax.set_xlabel(INPUT, fontsize=10, color=INK)
ax.set_ylabel(RESPONSE, fontsize=10, color=INK)
ax.set_title("scatter-regression-lowess · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Subtle grid
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
