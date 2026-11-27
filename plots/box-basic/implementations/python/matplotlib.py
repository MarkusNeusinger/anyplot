"""anyplot.ai
box-basic: Basic Box Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-28
"""

import os
import sys


# Prevent this file (named matplotlib.py) from shadowing the installed matplotlib package
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.realpath(p or ".") != _here]
del _here

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SECTOR = "Sector"  # role: category
SALARY = "Annual Salary (USD thousands)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("salaries.csv")
rng = np.random.RandomState(42)
spec = [  # (sector, mean, sd, n, low clip, high clip, deliberate outliers)
    ("Technology", 118, 28, 80, 55, 260, [228, 246]),
    ("Finance", 108, 35, 75, 45, 300, [268, 290, 47]),
    ("Healthcare", 94, 20, 85, 42, 200, []),
    ("Education", 66, 14, 70, 35, 120, []),
    ("Retail", 50, 11, 65, 28, 95, []),
]
sectors, salaries = [], []
for name, mean, sd, n, lo, hi, extra in spec:
    values = np.append(np.clip(rng.normal(mean, sd, n), lo, hi), extra)
    sectors += [name] * len(values)
    salaries += list(values)
df = pd.DataFrame({SECTOR: sectors, SALARY: salaries})

# Plot
groups = [(sector, rows[SALARY].to_numpy()) for sector, rows in df.groupby(SECTOR, sort=False)]

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

bp = ax.boxplot(
    [values for _, values in groups],
    tick_labels=[sector for sector, _ in groups],
    patch_artist=True,
    widths=0.55,
    flierprops={
        "marker": "o",
        "markerfacecolor": INK_MUTED,
        "markersize": 5,
        "alpha": 0.65,
        "markeredgecolor": PAGE_BG,
        "markeredgewidth": 0.5,
    },
    medianprops={"color": INK, "linewidth": 2.5},
    whiskerprops={"linewidth": 1.8, "color": INK_SOFT},
    capprops={"linewidth": 2.0, "color": INK_SOFT},
)

# One Imprint color per box, with a thin theme-adaptive outline stroke for depth
for i, patch in enumerate(bp["boxes"]):
    color = IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)]
    patch.set_facecolor(color)
    patch.set_alpha(0.75)
    patch.set_edgecolor(color)
    patch.set_linewidth(2.0)
    patch.set_path_effects([pe.withStroke(linewidth=3.5, foreground=INK_SOFT)])

# Style
title = "box-basic · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12

ax.set_xlabel(SECTOR, fontsize=10, color=INK)
ax.set_ylabel(SALARY, fontsize=10, color=INK)
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=15)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.tick_params(axis="x", length=0, pad=6)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

fig.subplots_adjust(left=0.12, right=0.97, top=0.88, bottom=0.13)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
