""" anyplot.ai
dot-matrix-proportional: Dot Matrix Chart for Proportional Counts
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-18
"""

import math
import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

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
SOURCE = "Energy source"  # role: category
COUNT = "Respondents"  # role: count
TOTAL = "Total respondents"  # role: total

# Data: replace this block with your own table, one row per respondent, for example df = pd.read_csv("survey.csv")
df = pd.DataFrame({SOURCE: ["Solar Power", "Wind Energy", "Hydropower", "Other Sources"], COUNT: [38, 29, 21, 12]})
df[TOTAL] = df[COUNT].sum()

# Plot: reads only df and the constants above
table = df.dropna(subset=[COUNT])
counts = table.groupby(SOURCE, sort=False)[COUNT].sum().astype(int)
categories = list(counts.index)
total = int(counts.sum())

# Grid layout: as square as the total allows, filled left to right, top to bottom
cols = math.ceil(math.sqrt(total))
rows = math.ceil(total / cols)
dots = (
    pd.DataFrame({SOURCE: counts.index.repeat(counts.to_numpy())})
    .reset_index(drop=True)
    .assign(x=[i % cols for i in range(total)], y=[rows - 1 - i // cols for i in range(total)])
)

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.set_position([0.12, 0.27, 0.76, 0.62])

# Dot size follows the grid: one dot fills ~78 % of its cell
cell_pt = min(ax.get_position().width, ax.get_position().height) * fig.get_figwidth() * 72 / (max(cols, rows) + 0.6)
sns.scatterplot(
    data=dots,
    x="x",
    y="y",
    hue=SOURCE,
    hue_order=categories,
    palette=IMPRINT_PALETTE[: len(categories)],
    s=(0.78 * cell_pt) ** 2,
    linewidth=0.8,
    edgecolors=PAGE_BG,
    ax=ax,
    legend=False,
)
ax.set_xlim(-0.8, cols - 0.2)
ax.set_ylim(-0.8, rows - 0.2)
ax.set_aspect("equal")

# Legend with counts and percentages, below the grid
legend_handles = [
    Line2D(
        [0],
        [0],
        marker="o",
        color="none",
        markerfacecolor=IMPRINT_PALETTE[i],
        markeredgecolor=PAGE_BG,
        markeredgewidth=0.5,
        markersize=9,
        label=f"{name}  ·  {counts[name]} / {total}  ({counts[name] / total:.0%})",
    )
    for i, name in enumerate(categories)
]
leg = ax.legend(
    handles=legend_handles,
    fontsize=9,
    title=f"{SOURCE}  (n = {total})",
    title_fontsize=10,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.04),
    ncol=2,
    frameon=True,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    handletextpad=0.8,
    columnspacing=1.8,
    borderpad=0.9,
    labelspacing=0.8,
)
leg.get_title().set_color(INK)
for text in leg.get_texts():
    text.set_color(INK_SOFT)

# Style
title = "Energy Source Survey · dot-matrix-proportional · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=round(12 * min(1, 67 / len(title))), fontweight="medium", color=INK, pad=14)
ax.set_xlabel("")
ax.set_ylabel("")
ax.set_xticks([])
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_visible(False)

fig.text(0.5, 0.045, "1 dot = 1 respondent", ha="center", va="center", fontsize=9, color=INK_MUTED, style="italic")

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
