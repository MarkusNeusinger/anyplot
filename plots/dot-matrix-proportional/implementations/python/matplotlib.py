""" anyplot.ai
dot-matrix-proportional: Dot Matrix Chart for Proportional Counts
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 89/100 | Created: 2026-05-08
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data: remote work preference survey, n=100 employees
categories = ["Hybrid", "Fully Remote", "In-Office"]
counts = [44, 35, 21]
total = sum(counts)  # 100

# Grid: 10 columns × 10 rows
n_cols = 10
n_rows = total // n_cols

# Assign category index to each dot (left-to-right, top-to-bottom)
dot_cats = []
for i, c in enumerate(counts):
    dot_cats.extend([i] * c)

xs = [idx % n_cols for idx in range(total)]
ys = [n_rows - 1 - idx // n_cols for idx in range(total)]
dot_colors = [IMPRINT[c] for c in dot_cats]

# Landscape figure: dot grid occupies a square central column; legend sits below
fig, ax = plt.subplots(figsize=(16, 10), facecolor=PAGE_BG)
# Axes spans roughly 7 × 7 inches in the center of a 16 × 10 figure.
# With 10.3 data units in both x and y this gives ~204 px/unit @ 300 dpi,
# so s ≈ 1000 yields ~65 % fill diameter.
fig.subplots_adjust(left=0.265, right=0.735, top=0.88, bottom=0.17)
ax.set_facecolor(PAGE_BG)

ax.scatter(xs, ys, c=dot_colors, s=1000, edgecolors=PAGE_BG, linewidth=1.8, zorder=2)

ax.set_xlim(-0.65, n_cols - 0.35)
ax.set_ylim(-0.65, n_rows - 0.35)
ax.axis("off")

# Legend — three items in one row, centred below the grid
handles = [
    mpatches.Patch(color=IMPRINT[i], label=f"{categories[i]}  —  {counts[i]} / {total}")
    for i in range(len(categories))
]
leg = ax.legend(
    handles=handles,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.05),
    ncol=3,
    fontsize=20,
    frameon=True,
    handlelength=1.8,
    handleheight=1.4,
    borderpad=0.8,
    columnspacing=1.2,
)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

ax.set_title(
    "Remote Work Survey  ·  dot-matrix-proportional  ·  matplotlib  ·  anyplot.ai",
    fontsize=24,
    fontweight="medium",
    color=INK,
    pad=18,
)

plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
