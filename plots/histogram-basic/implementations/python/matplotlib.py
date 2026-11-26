"""anyplot.ai
histogram-basic: Basic Histogram
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-28
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 is the single series
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SCORE = "Exam Score (points)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
np.random.seed(42)
base = np.random.normal(loc=72, scale=12, size=450)
high_cluster = np.random.normal(loc=88, scale=4, size=50)
df = pd.DataFrame({SCORE: np.clip(np.concatenate([base, high_cluster]), 0, 100)})

# Plot: reads only df and the constants above
title = "histogram-basic · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.hist(df[SCORE].dropna(), bins=25, color=IMPRINT_PALETTE[0], edgecolor=PAGE_BG, linewidth=0.8)

# Style
ax.set_xlabel(SCORE, fontsize=10, color=INK)
ax.set_ylabel("Frequency (count)", fontsize=10, color=INK)
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=12)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)
ax.set_ylim(bottom=0)

fig.subplots_adjust(left=0.09, right=0.97, top=0.91, bottom=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
