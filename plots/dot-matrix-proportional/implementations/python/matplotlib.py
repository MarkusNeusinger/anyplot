"""anyplot.ai
dot-matrix-proportional: Dot Matrix Chart for Proportional Counts
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-11-19
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
CATEGORY = "Preferred work model"  # role: category
COUNT = "Employees"  # role: count
TOTAL = "Surveyed"  # role: total

# Data: remote work preference survey, replace with your own table, for example df = pd.read_csv("survey.csv")
df = pd.DataFrame({CATEGORY: ["Hybrid", "Fully Remote", "In-Office"], COUNT: [44, 35, 21], TOTAL: [100] * 3})

# Plot: reads only df and the constants above
counts = df[COUNT].fillna(0).round().astype(int).to_numpy()
total = int(df[TOTAL].max())
rest = max(total - int(counts.sum()), 0)  # units in no listed category: neutral remainder
n_cols = int(np.ceil(np.sqrt(total)))
n_rows = int(np.ceil(total / n_cols))

# One dot per unit, filled left to right and top to bottom
dot_cats = np.repeat(np.arange(len(df) + 1), np.append(counts, rest))[:total]
idx = np.arange(total)
xs = idx % n_cols
ys = n_rows - 1 - idx // n_cols
dot_colors = [IMPRINT_PALETTE[c % len(IMPRINT_PALETTE)] if c < len(df) else INK_MUTED for c in dot_cats]

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
fig.subplots_adjust(left=0.2, right=0.8, top=0.84, bottom=0.2)

ax.scatter(xs, ys, c=dot_colors, s=190, edgecolors=PAGE_BG, linewidth=0.8, zorder=2)
ax.set_xlim(-0.65, n_cols - 0.35)
ax.set_ylim(-0.65, n_rows - 0.35)
ax.set_aspect("equal")
ax.axis("off")

# Legend: one item per category with its count, centred below the grid
handles = [
    mpatches.Patch(color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)], label=f"{cat}  —  {n} / {total}")
    for i, (cat, n) in enumerate(zip(df[CATEGORY], counts, strict=True))
]
if rest:
    handles.append(mpatches.Patch(color=INK_MUTED, label=f"Other  —  {rest} / {total}"))
leg = ax.legend(
    handles=handles,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.04),
    ncol=len(handles),
    fontsize=9,
    frameon=True,
    handlelength=1.6,
    handleheight=1.2,
    borderpad=0.7,
    columnspacing=1.6,
)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

# Style
title = "Remote Work Survey  ·  dot-matrix-proportional  ·  python  ·  matplotlib  ·  anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12
fig.suptitle(title, fontsize=title_fontsize, fontweight="medium", color=INK, y=0.94)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
