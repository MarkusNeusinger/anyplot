"""anyplot.ai
histogram-2d: 2D Histogram Heatmap
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-08
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: continuous data uses the sequential cmap derived from it
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

# Columns: set these to your table's column names
X = "Feature X"  # role: x
Y = "Feature Y"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("points.csv")
rng = np.random.default_rng(42)
samples = rng.multivariate_normal([0, 0], [[1, 0.7], [0.7, 1]], 5000)
df = pd.DataFrame({X: samples[:, 0], Y: samples[:, 1]})

# Plot: reads only df and the constants above
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

points = df[[X, Y]].dropna()
h = ax.hist2d(points[X], points[Y], bins=40, cmap=imprint_seq, cmin=1)

cbar = fig.colorbar(h[3], ax=ax, pad=0.02)
cbar.set_label("Count per bin", fontsize=10, color=INK)
cbar.ax.tick_params(axis="y", labelsize=8, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

ax.set_xlabel(X, fontsize=10, color=INK)
ax.set_ylabel(Y, fontsize=10, color=INK)
ax.set_title("histogram-2d · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
