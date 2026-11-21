"""anyplot.ai
scatter-regression-lowess: Scatter Plot with LOWESS Regression
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-14
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.nonparametric.smoothers_lowess import lowess


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SMOOTHING_FRAC = 0.4  # share of the points in each local fit; the spec suggests 0.3-0.5

# Columns: set these to your table's column names
AGE = "Tree age (years)"  # role: x
HEIGHT = "Tree height (m)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("trees.csv")
rng = np.random.default_rng(42)
n_points = 150
age = np.linspace(1, 30, n_points)
height = 20 * (1 - np.exp(-0.15 * age)) + rng.normal(0, 0.6, n_points)
df = pd.DataFrame({AGE: age, HEIGHT: height})

# Plot: reads only df and the constants above
smooth = lowess(df[HEIGHT], df[AGE], frac=SMOOTHING_FRAC, return_sorted=True)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.scatter(
    df[AGE], df[HEIGHT], s=45, alpha=0.6, color=IMPRINT_PALETTE[0], edgecolors=PAGE_BG, linewidth=0.4, label="Observed"
)
ax.plot(smooth[:, 0], smooth[:, 1], color=IMPRINT_PALETTE[1], linewidth=2.5, label="LOWESS trend")

# Style
ax.set_xlabel(AGE, fontsize=10, color=INK)
ax.set_ylabel(HEIGHT, fontsize=10, color=INK)
ax.set_title(
    "scatter-regression-lowess · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK
)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

leg = ax.legend(fontsize=8, loc="lower right", frameon=True)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.8)
for text in leg.get_texts():
    text.set_color(INK_SOFT)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
