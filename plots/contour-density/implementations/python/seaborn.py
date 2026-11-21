"""anyplot.ai
contour-density: Density Contour Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-16
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
SCATTER_COLOR = "#4A4A44" if THEME == "light" else "#9A9A94"

# Imprint palette: all eight positions, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential colormap for continuous density (green -> blue)
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]])

# Constants
LEVELS = 10  # number of density bands

# Columns: set these to your table's column names
X = "X Variable (units)"  # role: x
Y = "Y Variable (units)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("measurements.csv")
np.random.seed(42)
n1, n2 = 300, 150
df = pd.DataFrame(
    {
        X: np.concatenate([np.random.normal(5, 1.5, n1), np.random.normal(9, 1.0, n2)]),
        Y: np.concatenate([np.random.normal(5, 1.5, n1), np.random.normal(8, 1.0, n2)]),
    }
)

# Plot: reads only df and the constants above
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

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Filled density bands with a color bar showing which way density rises
sns.kdeplot(
    data=df,
    x=X,
    y=Y,
    ax=ax,
    levels=LEVELS,
    fill=True,
    cmap=imprint_seq,
    alpha=0.85,
    cbar=True,
    cbar_kws={"label": "Relative density", "ticks": []},
)

# Contour lines on the same levels
sns.kdeplot(data=df, x=X, y=Y, ax=ax, levels=LEVELS, color=INK_SOFT, linewidths=0.6, alpha=0.7)

# Faint scatter overlay at the exact values
ax.scatter(df[X], df[Y], s=4, color=SCATTER_COLOR, alpha=0.3, edgecolors="none")

# Colorbar chrome: low/high labels instead of numeric density
cbar = fig.axes[-1]
cbar.set_ylabel("Relative density", fontsize=10, color=INK)
low, high = cbar.get_ylim()
cbar.set_yticks([low, high], labels=["low", "high"])
cbar.tick_params(labelsize=8, colors=INK_SOFT, length=0)
for spine in cbar.spines.values():
    spine.set_visible(False)

# Style
ax.set_title("contour-density · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(X, fontsize=10, color=INK)
ax.set_ylabel(Y, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
sns.despine(ax=ax)
ax.spines["left"].set_linewidth(0.8)
ax.spines["bottom"].set_linewidth(0.8)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.6, color=INK)

fig.subplots_adjust(left=0.08, right=0.94, top=0.92, bottom=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
