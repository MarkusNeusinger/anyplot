"""anyplot.ai
bar-drilldown: Column Chart with Hierarchical Drilling
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 85/100 | Created: 2026-05-20
"""

import os
import sys


sys.path = [p for p in sys.path if "implementations" not in p]  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.gridspec import GridSpec  # noqa: E402
from matplotlib.patches import ConnectionPatch  # noqa: E402


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"
BAR_MUTED = "#C0BEB8" if THEME == "light" else "#4E4E48"

# Data — 2024 global retail revenue by product category ($K)
categories = ["Electronics", "Apparel", "Home & Garden", "Sports"]
totals = [4820, 3150, 2760, 2390]
focus_idx = 0  # Electronics is the active drilldown category

sub_labels = ["Phones", "Laptops", "Tablets", "Accessories"]
sub_values = [1820, 1640, 890, 470]

# Layout: two stacked panels (1:1 canvas = 2400 × 2400 px)
fig = plt.figure(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
gs = GridSpec(2, 1, figure=fig, height_ratios=[1, 1.05], hspace=0.48, top=0.91, bottom=0.08, left=0.13, right=0.97)
ax1 = fig.add_subplot(gs[0])
ax2 = fig.add_subplot(gs[1])
ax1.set_facecolor(PAGE_BG)
ax2.set_facecolor(PAGE_BG)

# Overview panel — all top-level categories
x1 = np.arange(len(categories))
bar_colors = [BRAND if i == focus_idx else BAR_MUTED for i in range(len(categories))]
bars1 = ax1.bar(x1, totals, color=bar_colors, width=0.55, edgecolor=PAGE_BG, linewidth=0.8)
for bar, val in zip(bars1, totals, strict=True):
    ax1.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 55,
        f"${val:,}K",
        ha="center",
        va="bottom",
        fontsize=8.5,
        color=INK_SOFT,
    )
ax1.set_xticks(x1)
ax1.set_xticklabels(categories, fontsize=9, color=INK_SOFT)
ax1.set_ylabel("Revenue ($K)", fontsize=9, color=INK)
ax1.tick_params(axis="both", labelsize=8.5, colors=INK_SOFT)
ax1.set_ylim(0, max(totals) * 1.22)
ax1.set_title("All Categories  ·  2024", fontsize=11, color=INK, pad=6)

# Drilldown panel — Electronics subcategories
x2 = np.arange(len(sub_labels))
bars2 = ax2.bar(x2, sub_values, color=BRAND, width=0.55, edgecolor=PAGE_BG, linewidth=0.8)
for bar, val in zip(bars2, sub_values, strict=True):
    ax2.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 28,
        f"${val:,}K",
        ha="center",
        va="bottom",
        fontsize=8.5,
        color=INK_SOFT,
    )
ax2.set_xticks(x2)
ax2.set_xticklabels(sub_labels, fontsize=9, color=INK_SOFT)
ax2.set_ylabel("Revenue ($K)", fontsize=9, color=INK)
ax2.tick_params(axis="both", labelsize=8.5, colors=INK_SOFT)
ax2.set_ylim(0, max(sub_values) * 1.22)
# Title doubles as breadcrumb trail
ax2.set_title("All Categories  ›  Electronics", fontsize=11, color=INK, pad=6)

# Back-navigation affordance (static approximation of back-button)
ax2.text(
    0.01,
    0.97,
    "◄ Back to All Categories",
    transform=ax2.transAxes,
    fontsize=8,
    color=INK_SOFT,
    va="top",
    ha="left",
    fontstyle="italic",
)

for ax in (ax1, ax2):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK_SOFT)
    ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
    ax.set_axisbelow(True)

# ConnectionPatch: visual connector from the active bar's top edges to the drilldown panel
bar_hw = 0.55 / 2  # half-width of the Electronics bar
for x_a, x_b in [(-bar_hw, 0.0), (bar_hw, 1.0)]:
    con = ConnectionPatch(
        xyA=(focus_idx + x_a, totals[focus_idx]),
        xyB=(x_b, 1.0),
        coordsA="data",
        coordsB="axes fraction",
        axesA=ax1,
        axesB=ax2,
        color=BRAND,
        lw=0.9,
        linestyle="--",
        alpha=0.35,
        clip_on=False,
    )
    fig.add_artist(con)

fig.suptitle("bar-drilldown · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)

plt.savefig(f"plot-{THEME}.png", dpi=400, bbox_inches="tight", facecolor=PAGE_BG)
