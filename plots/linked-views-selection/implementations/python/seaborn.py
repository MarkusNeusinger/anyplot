""" anyplot.ai
linked-views-selection: Multiple Linked Views with Selection Sync
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 82/100 | Created: 2026-05-24
"""

import os
import sys


# Remove the script's own directory from sys.path so that local files like
# matplotlib.py do not shadow the installed matplotlib package.
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if p and os.path.abspath(p) != _here]

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
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
sns.scatterplot(
    data=iris,
    x="petal_length",
    y="petal_width",
    hue="species",
    palette=species_colors,
    s=100,
    alpha=0.80,
    edgecolor=PAGE_BG,
    linewidth=0.4,
    ax=ax1,
    legend=False,
)
ax1.set_title("Scatter", fontsize=9, color=INK_SOFT, pad=4)
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
sns.histplot(
    data=iris,
    x="sepal_length",
    hue="species",
    palette=species_colors,
    multiple="layer",
    bins=18,
    alpha=0.60,
    ax=ax2,
    legend=False,
)
ax2.set_title("Distribution", fontsize=9, color=INK_SOFT, pad=4)
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
sns.barplot(
    data=iris,
    x="species",
    y="petal_length",
    hue="species",
    palette=species_colors,
    errorbar="sd",
    capsize=0.15,
    order=list(species_order),
    ax=ax3,
    legend=False,
    width=0.55,
)
ax3.set_title("Summary", fontsize=9, color=INK_SOFT, pad=4)
ax3.set_xlabel("Species", fontsize=10, color=INK)
ax3.set_ylabel("Mean Petal Length (cm)", fontsize=10, color=INK)
ax3.set_xticks(range(len(species_order)))
ax3.set_xticklabels([sp.capitalize() for sp in species_order], fontsize=8, color=INK_SOFT)
ax3.tick_params(axis="y", labelsize=8, colors=INK_SOFT)
ax3.tick_params(axis="x", length=0)
ax3.spines["top"].set_visible(False)
ax3.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax3.spines[spine].set_color(INK_SOFT)
ax3.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Shared legend — frameon=False keeps layout clean
legend_handles = [mpatches.Patch(color=species_colors[sp], label=sp.capitalize()) for sp in species_order]
fig.legend(handles=legend_handles, loc="lower center", ncol=3, fontsize=8, frameon=False, bbox_to_anchor=(0.5, 0.01))

# Title
title = "linked-views-selection · python · seaborn · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_fontsize = max(8, round(12 * ratio))
fig.suptitle(title, fontsize=title_fontsize, fontweight="medium", color=INK, y=0.98)

fig.subplots_adjust(top=0.86, bottom=0.18, left=0.09, right=0.97, wspace=0.45)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
