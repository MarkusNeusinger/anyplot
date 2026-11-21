"""anyplot.ai
upset-basic: UpSet Plot for Multi-Set Intersection Analysis
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 89/100 | Created: 2026-05-13
"""

import os
import sys
from collections import Counter


sys.path.pop(0)  # prevent shadowing the matplotlib library with this file

import matplotlib.gridspec as gridspec
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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
MAX_INTERSECTIONS = 12  # keep the largest intersections, the long tail of tiny ones is left out

# Columns: set these to your table's column names
ELEMENT = "Bug report"  # role: element
SETS = "Affected modules"  # role: sets

# Data: replace this block with your own table, for example df = pd.read_csv("bugs.csv")
# (one row per element, SETS holds the list of sets the element belongs to)
np.random.seed(42)
module_names = ["Frontend", "Backend", "Database", "API", "Security"]
module_probs = [0.42, 0.36, 0.28, 0.24, 0.16]
n_bugs = 800
hits = np.column_stack([np.random.rand(n_bugs) < p for p in module_probs])
hits = hits[hits.any(axis=1)]
df = pd.DataFrame(
    {
        ELEMENT: [f"BUG-{i + 1:04d}" for i in range(len(hits))],
        SETS: [tuple(name for name, hit in zip(module_names, row, strict=True) if hit) for row in hits],
    }
)

# Plot: reads only df and the constants above
memberships = df[SETS].dropna()
set_sizes = Counter(name for members in memberships for name in members)
set_names = sorted(set_sizes, key=lambda name: -set_sizes[name])
n_sets = len(set_names)

intersection_counts = Counter(frozenset(members) for members in memberships)
top_ints = sorted(intersection_counts.items(), key=lambda item: -item[1])[:MAX_INTERSECTIONS]
int_counts = [count for _, count in top_ints]
int_members = [members for members, _ in top_ints]
n_ints = len(top_ints)
degrees = [len(members) for members in int_members]
degree_color = {deg: IMPRINT_PALETTE[min(deg - 1, len(IMPRINT_PALETTE) - 1)] for deg in set(degrees)}
bar_colors = [degree_color[deg] for deg in degrees]

# Figure layout: 2x2 grid (top-left empty, top-right = bars, bottom-left = set sizes, bottom-right = matrix)
fig = plt.figure(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
gs = gridspec.GridSpec(
    2,
    2,
    width_ratios=[1, 3.5],
    height_ratios=[2.5, 1.5],
    hspace=0.04,
    wspace=0.06,
    left=0.10,
    right=0.98,
    top=0.89,
    bottom=0.11,
)
ax_bars = fig.add_subplot(gs[0, 1])
ax_matrix = fig.add_subplot(gs[1, 1], sharex=ax_bars)
ax_sets = fig.add_subplot(gs[1, 0], sharey=ax_matrix)

# Intersection bars (top right)
ax_bars.bar(range(n_ints), int_counts, color=bar_colors, width=0.65, zorder=2)
for i, count in enumerate(int_counts):
    ax_bars.text(
        i,
        count + max(int_counts) * 0.018,
        str(count),
        ha="center",
        va="bottom",
        fontsize=8,
        color=INK_SOFT,
        fontweight="medium",
    )

ax_bars.set_xlim(-0.5, n_ints - 0.5)
ax_bars.set_ylim(0, max(int_counts) * 1.15)
ax_bars.set_ylabel("Intersection size", fontsize=10, color=INK, labelpad=4)
ax_bars.set_facecolor(PAGE_BG)
ax_bars.tick_params(axis="y", labelsize=8, labelcolor=INK_SOFT, colors=INK_SOFT)
ax_bars.tick_params(axis="x", bottom=False, labelbottom=False)
ax_bars.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax_bars.set_axisbelow(True)
for side in ("top", "right", "bottom"):
    ax_bars.spines[side].set_visible(False)
ax_bars.spines["left"].set_color(INK_SOFT)

# Degree legend inside the intersection bars area
patches = [
    mpatches.Patch(color=degree_color[deg], label=f"{deg} set" if deg == 1 else f"{deg} sets")
    for deg in sorted(set(degrees))
]
leg = ax_bars.legend(
    handles=patches,
    fontsize=8,
    loc="upper right",
    title="Intersection degree",
    title_fontsize=8,
    frameon=True,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
)
plt.setp(leg.get_texts(), color=INK_SOFT)
plt.setp(leg.get_title(), color=INK_SOFT)

# Dot matrix (bottom right)
ax_matrix.set_facecolor(PAGE_BG)
ax_matrix.set_ylim(n_sets - 0.5, -0.5)
ax_matrix.set_yticks(range(n_sets))
ax_matrix.tick_params(axis="x", bottom=False, labelbottom=False)
ax_matrix.tick_params(axis="y", left=False, labelleft=False)

# Alternating row shading
for row_i in range(0, n_sets, 2):
    ax_matrix.axhspan(row_i - 0.5, row_i + 0.5, color=INK, alpha=0.04, zorder=0)

for col_j, (members, color) in enumerate(zip(int_members, bar_colors, strict=True)):
    active_rows = [row_i for row_i, name in enumerate(set_names) if name in members]
    inactive_rows = [row_i for row_i in range(n_sets) if row_i not in active_rows]
    ax_matrix.scatter(
        [col_j] * len(inactive_rows), inactive_rows, s=55, color=INK_MUTED, alpha=0.30, zorder=1, linewidths=0
    )
    if len(active_rows) > 1:
        ax_matrix.plot(
            [col_j, col_j],
            [min(active_rows), max(active_rows)],
            color=color,
            linewidth=2.4,
            solid_capstyle="round",
            zorder=2,
        )
    ax_matrix.scatter([col_j] * len(active_rows), active_rows, s=60, color=color, zorder=3, linewidths=0)

for spine in ax_matrix.spines.values():
    spine.set_visible(False)

# Set size bars (bottom left)
ax_sets.set_facecolor(PAGE_BG)
ax_sets.barh(range(n_sets), [set_sizes[name] for name in set_names], color=IMPRINT_PALETTE[0], height=0.55, zorder=2)
ax_sets.set_xlim(max(set_sizes.values()) * 1.08, 0)
ax_sets.set_yticks(range(n_sets), set_names, fontsize=9, color=INK_SOFT)
ax_sets.set_xlabel("Set size", fontsize=10, color=INK, labelpad=4)
ax_sets.tick_params(axis="x", labelsize=8, labelcolor=INK_SOFT, colors=INK_SOFT)
ax_sets.tick_params(axis="y", left=False, length=0)
for side in ("top", "right", "left"):
    ax_sets.spines[side].set_visible(False)
ax_sets.spines["bottom"].set_color(INK_SOFT)
ax_sets.xaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax_sets.set_axisbelow(True)

# Title
title = "upset-basic · python · matplotlib · anyplot.ai"
fig.text(0.5, 0.95, title, ha="center", va="center", fontsize=12, fontweight="medium", color=INK)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
