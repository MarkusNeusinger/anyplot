"""anyplot.ai
upset-basic: UpSet Plot for Multi-Set Intersection Analysis
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-11-21
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: first position is the single-series brand color
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

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

# Constants
MAX_INTERSECTIONS = 14  # show only the largest combinations

# Columns: set these to your table's column names
ELEMENT = "Customer"  # role: element
SET_NAME = "Channel"  # role: sets

# Data: replace this block with your own table, for example df = pd.read_csv("memberships.csv")
# One row per (element, set) membership: customer segments across marketing channels
rng = np.random.default_rng(42)
channel_names = ["Email", "Mobile", "Social", "Premium", "Loyalty"]
channel_probs = [0.62, 0.51, 0.39, 0.27, 0.21]
member = rng.random((1200, len(channel_names))) < np.array(channel_probs)
customer_idx, channel_idx = np.nonzero(member)
df = pd.DataFrame({ELEMENT: [f"C{i:04d}" for i in customer_idx], SET_NAME: [channel_names[j] for j in channel_idx]})

# Plot: reads only df and the constants above
set_order = list(df[SET_NAME].unique())
n_sets = len(set_order)
membership = pd.crosstab(df[ELEMENT], df[SET_NAME]).reindex(columns=set_order).gt(0)
combo_counts = membership.value_counts().head(MAX_INTERSECTIONS)  # sorted by size, descending
n_ints = len(combo_counts)
set_sizes = membership.sum().reindex(set_order)

# Long table of matrix cells: one row per (intersection, set)
cells = pd.DataFrame(
    [
        {"col": c, "row": r, "active": bool(flag)}
        for c, combo in enumerate(combo_counts.index)
        for r, flag in enumerate(combo)
    ]
)

fig = plt.figure(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
gs = fig.add_gridspec(
    2,
    3,
    width_ratios=[1.5, 0.9, 5],
    height_ratios=[3, 2],
    hspace=0.0,
    wspace=0.0,
    left=0.05,
    right=0.98,
    top=0.89,
    bottom=0.13,
)
ax_intbar = fig.add_subplot(gs[0, 2])
ax_setbar = fig.add_subplot(gs[1, 0])
ax_matrix = fig.add_subplot(gs[1, 2])

# Intersection bars (top)
x_cols = np.arange(n_ints)
sns.barplot(x=x_cols, y=combo_counts.to_numpy(), color=BRAND, saturation=1, linewidth=0, width=0.55, ax=ax_intbar)
ax_intbar.yaxis.grid(True)
ax_intbar.set_axisbelow(True)
for i, cnt in enumerate(combo_counts):
    ax_intbar.text(i, cnt + combo_counts.max() * 0.015, str(cnt), ha="center", va="bottom", fontsize=7, color=INK_SOFT)
ax_intbar.set_ylim(0, combo_counts.max() * 1.12)
ax_intbar.set_xlim(-0.5, n_ints - 0.5)
ax_intbar.set_ylabel("Intersection size", fontsize=10)
ax_intbar.tick_params(axis="y", labelsize=8)
ax_intbar.tick_params(axis="x", bottom=False, labelbottom=False)
sns.despine(ax=ax_intbar, bottom=True)

# Dot matrix (bottom right): active dots filled and joined, inactive dots muted
for row in range(n_sets):
    ax_matrix.axhline(row, color=INK, alpha=0.06, linewidth=0.6, zorder=1)
for col, group in cells[cells["active"]].groupby("col"):
    if len(group) > 1:
        ax_matrix.plot([col, col], [group["row"].min(), group["row"].max()], color=BRAND, linewidth=2.2, zorder=3)
sns.scatterplot(
    data=cells[~cells["active"]],
    x="col",
    y="row",
    color=INK_MUTED,
    alpha=0.3,
    s=30,
    linewidth=0,
    zorder=2,
    legend=False,
    ax=ax_matrix,
)
sns.scatterplot(
    data=cells[cells["active"]], x="col", y="row", color=BRAND, s=85, linewidth=0, zorder=4, legend=False, ax=ax_matrix
)
ax_matrix.set_xlim(-0.5, n_ints - 0.5)
ax_matrix.set_ylim(n_sets - 0.5, -0.5)  # first set on top, matching the set-size bars
ax_matrix.set_xlabel("")
ax_matrix.set_ylabel("")
ax_matrix.set_yticks(range(n_sets), set_order)
ax_matrix.tick_params(axis="y", left=False, labelsize=8, labelcolor=INK)
ax_matrix.tick_params(axis="x", bottom=False, labelbottom=False)
sns.despine(ax=ax_matrix, left=True, bottom=True)

# Set-size bars (bottom left): zero at the right edge, bars extend left
sns.barplot(
    x=set_sizes.to_numpy(), y=set_order, color=BRAND, saturation=1, linewidth=0, width=0.45, orient="h", ax=ax_setbar
)
ax_setbar.xaxis.grid(True)
ax_setbar.set_axisbelow(True)
ax_setbar.invert_xaxis()
ax_setbar.set_xlabel("Set size", fontsize=10)
ax_setbar.tick_params(axis="x", labelsize=8)
ax_setbar.tick_params(axis="y", left=False, labelleft=False)
sns.despine(ax=ax_setbar, left=True)

fig.text(
    0.5,
    0.95,
    "Customer Segments · upset-basic · python · seaborn · anyplot.ai",
    ha="center",
    va="center",
    fontsize=12,
    fontweight="medium",
    color=INK,
)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
