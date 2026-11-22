""" anyplot.ai
waffle-basic: Basic Waffle Chart
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-22
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import ListedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette - first series always #009E73 (brand)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
GRID_SIZE = 10  # 10x10 grid, one square = 1% of the whole

# Columns
CATEGORY = "category"  # role: category
SHARE = "share"  # role: value

# Data - budget allocation example
df = pd.DataFrame(
    {CATEGORY: ["Housing", "Food", "Transportation", "Utilities", "Entertainment"], SHARE: [35, 25, 20, 12, 8]}
)

# Plot
n_categories = len(df)
colors = [IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i in range(n_categories)]

# Whole squares per category: shares rescaled to the grid and rounded so the grid is exactly filled
n_squares = GRID_SIZE * GRID_SIZE
shares = df[SHARE].fillna(0)
exact = shares / shares.sum() * n_squares
counts = np.floor(exact).astype(int)
leftover = n_squares - counts.sum()
counts[exact.sub(counts).sort_values(ascending=False).index[:leftover]] += 1

# Fill bottom-left, going right then up (like filling a glass); one contiguous block per category
labels = np.repeat(np.arange(n_categories), counts.to_numpy())
grid = np.flipud(labels.reshape(GRID_SIZE, GRID_SIZE))

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.heatmap(
    grid,
    cmap=ListedColormap(colors),
    vmin=0,
    vmax=n_categories - 1,
    cbar=False,
    linewidths=1.5,
    linecolor=PAGE_BG,
    square=True,
    xticklabels=False,
    yticklabels=False,
    ax=ax,
)
sns.despine(ax=ax, left=True, bottom=True)

ax.set_title("waffle-basic · python · seaborn · anyplot.ai", fontsize=13, fontweight="medium", color=INK, pad=14)

legend_handles = [
    mpatches.Patch(color=colors[i], label=f"{cat} ({int(pct)}%)")
    for i, (cat, pct) in enumerate(zip(df[CATEGORY], counts, strict=True))
]
ax.legend(
    handles=legend_handles,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.02),
    ncol=3,
    fontsize=9,
    frameon=True,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    labelcolor=INK,
)

fig.subplots_adjust(left=0.04, right=0.96, top=0.93, bottom=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
