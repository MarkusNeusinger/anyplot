"""anyplot.ai
raincloud-basic: Basic Raincloud Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-26
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

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
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Columns: set these to your table's column names
METHOD = "Teaching method"  # role: category
SCORE = "Exam score (points)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
# Exam scores by teaching method; the lecture group is bimodal (two student subgroups),
# which a raincloud shows and a box plot would hide.
rng = np.random.default_rng(42)
lecture = np.concatenate([rng.normal(56, 6, 40), rng.normal(79, 5, 40)])
flipped = rng.normal(73, 8, 80)
project = rng.normal(82, 6, 80)
df = pd.DataFrame(
    {
        METHOD: ["Lecture"] * len(lecture) + ["Flipped"] * len(flipped) + ["Project-based"] * len(project),
        SCORE: np.clip(np.concatenate([lecture, flipped, project]), 0, 100),
    }
)

# Plot: reads only df and the constants above
order = list(df[METHOD].unique())
n_groups = len(order)
palette = IMPRINT_PALETTE[:n_groups]

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

# Cloud — half-violin, clipped to the upper half above each category baseline
sns.violinplot(
    data=df,
    x=SCORE,
    y=METHOD,
    hue=METHOD,
    palette=palette,
    order=order,
    hue_order=order,
    cut=0,
    inner=None,
    density_norm="width",
    width=0.8,
    linewidth=0.6,
    bw_adjust=0.6,
    ax=ax,
    legend=False,
)
n_violin_collections = len(ax.collections)
for i, collection in enumerate(ax.collections):
    for path in collection.get_paths():
        v = path.vertices
        v[v[:, 1] < i, 1] = i

# Rain — jittered strip points, shifted below the baseline
sns.stripplot(
    data=df,
    x=SCORE,
    y=METHOD,
    hue=METHOD,
    palette=palette,
    order=order,
    hue_order=order,
    jitter=0.07,
    size=3.5,
    alpha=0.55,
    edgecolor=PAGE_BG,
    linewidth=0.3,
    ax=ax,
    legend=False,
)
for collection in ax.collections[n_violin_collections:]:
    offsets = collection.get_offsets()
    offsets[:, 1] -= 0.25
    collection.set_offsets(offsets)
    collection.set_zorder(2)

# Box plot — outlined boxes on the baseline; palette colours the outline,
# whiskers, caps, and median in one stroke (no fragile post-hoc recolouring).
sns.boxplot(
    data=df,
    x=SCORE,
    y=METHOD,
    hue=METHOD,
    palette=palette,
    order=order,
    hue_order=order,
    fill=False,
    width=0.14,
    showfliers=False,
    linewidth=1.4,
    medianprops={"linewidth": 2.0, "solid_capstyle": "butt"},
    ax=ax,
    legend=False,
    zorder=4,
)

ax.set_xlabel(SCORE, fontsize=10, labelpad=6, color=INK)
ax.set_ylabel(METHOD, fontsize=10, labelpad=6, color=INK)
ax.set_title("raincloud-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", pad=10, color=INK)
ax.tick_params(axis="both", labelsize=9, colors=INK_SOFT, length=3, width=0.6)
ax.grid(True, axis="x", alpha=0.15, linewidth=0.5, color=INK)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_linewidth(0.6)
ax.spines["bottom"].set_linewidth(0.6)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

ax.set_ylim(-0.55, n_groups - 0.55)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
