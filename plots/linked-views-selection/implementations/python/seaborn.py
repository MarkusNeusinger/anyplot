""" anyplot.ai
linked-views-selection: Multiple Linked Views with Selection Sync
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 79/100 | Created: 2026-05-24
"""

import os
import sys


# Remove the script's own directory from sys.path so that local files like
# matplotlib.py do not shadow the installed matplotlib package.
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if p and os.path.abspath(p) != _here]

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

ANYPLOT_PALETTE = ["#009E73", "#9418DB", "#B71D27", "#16B8F3", "#99B314", "#D359A7", "#BA843E"]

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

# Data
iris = sns.load_dataset("iris")
species_order = iris["species"].unique()
species_colors = {sp: ANYPLOT_PALETTE[i] for i, sp in enumerate(species_order)}

# Plot
fig, axes = plt.subplots(1, 3, figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

# Panel 1: Scatter — petal length vs petal width
ax1 = axes[0]
for sp in species_order:
    mask = iris["species"] == sp
    ax1.scatter(
        iris.loc[mask, "petal_length"],
        iris.loc[mask, "petal_width"],
        color=species_colors[sp],
        s=55,
        alpha=0.80,
        edgecolors=PAGE_BG,
        linewidth=0.4,
    )
ax1.set_xlabel("Petal Length (cm)", fontsize=10, color=INK)
ax1.set_ylabel("Petal Width (cm)", fontsize=10, color=INK)
ax1.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax1.spines[spine].set_color(INK_SOFT)
ax1.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Panel 2: Histogram — sepal length distribution
ax2 = axes[1]
bins = np.linspace(iris["sepal_length"].min(), iris["sepal_length"].max(), 20)
for sp in species_order:
    mask = iris["species"] == sp
    ax2.hist(
        iris.loc[mask, "sepal_length"],
        bins=bins,
        color=species_colors[sp],
        alpha=0.65,
        edgecolor=PAGE_BG,
        linewidth=0.4,
    )
ax2.set_xlabel("Sepal Length (cm)", fontsize=10, color=INK)
ax2.set_ylabel("Count", fontsize=10, color=INK)
ax2.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax2.spines[spine].set_color(INK_SOFT)
ax2.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Panel 3: Bar chart — mean petal length per species with std error
ax3 = axes[2]
stats = iris.groupby("species")["petal_length"].agg(["mean", "std"]).reindex(species_order)
bar_colors = [species_colors[sp] for sp in stats.index]
x_pos = np.arange(len(stats))
ax3.bar(
    x_pos,
    stats["mean"],
    color=bar_colors,
    edgecolor=PAGE_BG,
    linewidth=0.4,
    width=0.55,
    yerr=stats["std"],
    error_kw={"ecolor": INK_SOFT, "capsize": 3, "capthick": 1, "elinewidth": 1},
)
ax3.set_xticks(x_pos)
ax3.set_xticklabels([s.capitalize() for s in stats.index], fontsize=8, color=INK_SOFT)
ax3.set_xlabel("Species", fontsize=10, color=INK)
ax3.set_ylabel("Mean Petal Length (cm)", fontsize=10, color=INK)
ax3.tick_params(axis="y", labelsize=8, colors=INK_SOFT)
ax3.tick_params(axis="x", length=0)
ax3.spines["top"].set_visible(False)
ax3.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax3.spines[spine].set_color(INK_SOFT)
ax3.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Shared legend
legend_handles = [mpatches.Patch(color=species_colors[sp], label=sp.capitalize()) for sp in species_order]
fig.legend(
    handles=legend_handles,
    loc="lower center",
    ncol=3,
    fontsize=8,
    framealpha=0.9,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    bbox_to_anchor=(0.5, 0.01),
)

# Title
title = "linked-views-selection · python · seaborn · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_fontsize = max(8, round(12 * ratio))
fig.suptitle(title, fontsize=title_fontsize, fontweight="medium", color=INK, y=0.98)

fig.subplots_adjust(top=0.91, bottom=0.20, left=0.09, right=0.97, wspace=0.40)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
