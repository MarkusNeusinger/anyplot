""" anyplot.ai
heatmap-basic: Basic Heatmap
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-27
"""

import os
import sys


# Remove this script's directory from sys.path so "matplotlib" resolves to the
# installed package rather than this file (which shares its name).
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _here and p != ""]

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm, to_rgb


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (categorical positions; this plot uses the diverging ramp below)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint diverging colormap: the midpoint is the page color (fields ramp)
imprint_div = LinearSegmentedColormap.from_list("imprint_div", ["#AE3030", PAGE_BG, "#4467A3"])


def luminance(color):
    r, g, b = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in to_rgb(color)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


# Columns: set these to your table's column names
X = "Department (column)"  # role: x
Y = "Department (row)"  # role: y
VALUE = "Correlation"  # role: value

# Data: replace this block with your own long table, for example df = pd.read_csv("corr_long.csv")
departments = ["Sales", "Marketing", "Finance", "Dev", "Ops", "Support", "HR", "Legal"]
matrix = [
    [1.00, 0.82, 0.61, 0.12, 0.44, 0.35, -0.15, 0.08],
    [0.82, 1.00, 0.48, 0.18, 0.30, 0.28, 0.10, -0.20],
    [0.61, 0.48, 1.00, -0.65, 0.05, -0.38, 0.30, 0.40],
    [0.12, 0.18, -0.65, 1.00, 0.42, 0.55, -0.10, -0.30],
    [0.44, 0.30, 0.05, 0.42, 1.00, 0.60, -0.08, 0.20],
    [0.35, 0.28, -0.38, 0.55, 0.60, 1.00, 0.22, 0.15],
    [-0.15, 0.10, 0.30, -0.10, -0.08, 0.22, 1.00, 0.52],
    [0.08, -0.20, 0.40, -0.30, 0.20, 0.15, 0.52, 1.00],
]
df = pd.DataFrame(
    {
        Y: [row for row in departments for _ in departments],
        X: departments * len(departments),
        VALUE: [v for line in matrix for v in line],
    }
)

# Plot
table = df.pivot_table(index=Y, columns=X, values=VALUE, sort=False)
values = table.to_numpy()
n_rows, n_cols = values.shape
bound = np.nanmax(np.abs(values))

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

norm = TwoSlopeNorm(vmin=-bound, vcenter=0, vmax=bound)
im = ax.imshow(values, cmap=imprint_div, norm=norm, aspect="equal")

for spine in ax.spines.values():
    spine.set_visible(False)

# Cell separators via minor-tick grid
ax.set_xticks(np.arange(n_cols + 1) - 0.5, minor=True)
ax.set_yticks(np.arange(n_rows + 1) - 0.5, minor=True)
ax.grid(which="minor", color=PAGE_BG, linewidth=1.5)
ax.tick_params(which="minor", bottom=False, left=False)

ax.set_xticks(np.arange(n_cols), table.columns, fontsize=8, rotation=45, ha="right", color=INK_SOFT)
ax.set_yticks(np.arange(n_rows), table.index, fontsize=8, color=INK_SOFT)
ax.tick_params(axis="both", length=0, colors=INK_SOFT)

# Cell annotations: per cell, the page color or INK, whichever contrasts more with the cell fill
for i in range(n_rows):
    for j in range(n_cols):
        val = values[i, j]
        fill = im.cmap(norm(val))
        text_color = max((INK, PAGE_BG), key=lambda c: contrast(c, fill))
        ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=8, color=text_color, zorder=4)

cbar = fig.colorbar(im, ax=ax, fraction=0.032, pad=0.025, aspect=28)
cbar.ax.tick_params(labelsize=7, colors=INK_SOFT)
cbar.set_label(VALUE, fontsize=8, color=INK_SOFT, labelpad=8)
cbar.outline.set_visible(False)

title = "heatmap-basic · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=10)
ax.set_xlabel(X, fontsize=10, color=INK, labelpad=8)
ax.set_ylabel(Y, fontsize=10, color=INK, labelpad=8)

fig.subplots_adjust(left=0.2, right=0.87, top=0.94, bottom=0.16)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
