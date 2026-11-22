""" anyplot.ai
bar-permutation-importance: Permutation Feature Importance Plot
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-22
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

# Imprint palette: sequential map built from positions 1 and 3
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature
IMPORTANCE = "Mean decrease in accuracy"  # role: importance_mean
IMPORTANCE_STD = "Std across shuffles"  # role: importance_std

# Data: replace this block with your own table, for example df = pd.read_csv("importance.csv")
df = pd.DataFrame(
    {
        FEATURE: [
            "alcohol",
            "malic_acid",
            "ash",
            "alcalinity_of_ash",
            "magnesium",
            "total_phenols",
            "flavanoids",
            "nonflavanoid_phenols",
            "proanthocyanins",
            "color_intensity",
            "hue",
            "od280/od315_of_diluted_wines",
            "proline",
        ],
        IMPORTANCE: [0.032, 0.003, -0.002, 0.008, 0.012, 0.048, 0.142, 0.001, 0.018, 0.095, 0.055, 0.068, 0.105],
        IMPORTANCE_STD: [0.015, 0.008, 0.006, 0.010, 0.009, 0.020, 0.025, 0.005, 0.012, 0.022, 0.018, 0.019, 0.023],
    }
)

# Plot: reads only df and the constants above
ranked = df.sort_values(IMPORTANCE, ascending=True).reset_index(drop=True)  # highest ends up at the top
norm = plt.Normalize(ranked[IMPORTANCE].min(), ranked[IMPORTANCE].max())
colors = imprint_seq(norm(ranked[IMPORTANCE].to_numpy()))

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG, layout="constrained")
ax.set_facecolor(PAGE_BG)

y_pos = np.arange(len(ranked))
ax.barh(
    y_pos,
    ranked[IMPORTANCE],
    xerr=ranked[IMPORTANCE_STD],
    color=colors,
    edgecolor=INK_SOFT,
    linewidth=0.6,
    height=0.7,
    capsize=3,
    error_kw={"elinewidth": 1.0, "capthick": 1.0, "ecolor": INK_SOFT},
)

# Reference line at zero
ax.axvline(0, color=INK_SOFT, linewidth=1.2, alpha=0.9)

# Style
title = "bar-permutation-importance · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK)
ax.set_yticks(y_pos, ranked[FEATURE])
ax.set_xlabel(IMPORTANCE, fontsize=10, color=INK)
ax.set_ylabel(FEATURE, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.set_ylim(-0.6, len(ranked) - 0.4)
ax.grid(True, axis="x", alpha=0.15, linewidth=0.5, color=INK)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Colorbar tied to the importance values
sm = plt.cm.ScalarMappable(cmap=imprint_seq, norm=norm)
cbar = fig.colorbar(sm, ax=ax, pad=0.02)
cbar.set_label("Importance", fontsize=9, color=INK)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
