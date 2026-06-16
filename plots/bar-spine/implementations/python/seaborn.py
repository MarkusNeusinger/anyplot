""" anyplot.ai
bar-spine: Spine Plot for Two-Variable Proportions
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 87/100 | Created: 2026-05-08
"""

import os

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

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

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
titanic = sns.load_dataset("titanic")
titanic = titanic.dropna(subset=["pclass", "survived"])
titanic["survived_label"] = titanic["survived"].map({1: "Survived", 0: "Did Not Survive"})

ct = titanic.groupby(["pclass", "survived_label"]).size().reset_index(name="count")
pclass_totals = titanic.groupby("pclass").size()
total = pclass_totals.sum()

pclass_order = [1, 2, 3]
pclass_labels = ["1st Class", "2nd Class", "3rd Class"]
fill_order = ["Survived", "Did Not Survive"]
colors = [IMPRINT[0], IMPRINT[1]]

widths = [pclass_totals[p] / total for p in pclass_order]
x_positions = np.cumsum([0] + widths[:-1])

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for i, pclass in enumerate(pclass_order):
    pclass_data = ct[ct["pclass"] == pclass].set_index("survived_label")
    class_total = pclass_totals[pclass]
    bottom = 0.0

    for j, fill_cat in enumerate(fill_order):
        count = pclass_data.loc[fill_cat, "count"] if fill_cat in pclass_data.index else 0
        proportion = count / class_total

        ax.bar(
            x=x_positions[i],
            height=proportion,
            width=widths[i],
            bottom=bottom,
            color=colors[j],
            align="edge",
            edgecolor=PAGE_BG,
            linewidth=1.0,
        )

        if proportion > 0.06:
            ax.text(
                x_positions[i] + widths[i] / 2,
                bottom + proportion / 2,
                f"{proportion:.0%}",
                ha="center",
                va="center",
                fontsize=18,
                color="white",
                fontweight="bold",
            )

        bottom += proportion

# X-axis labels centered under variable-width bars
ax.set_ylim(-0.09, 1.05)
for i, (pclass, label) in enumerate(zip(pclass_order, pclass_labels, strict=True)):
    center = x_positions[i] + widths[i] / 2
    ax.text(center, -0.04, f"{label}\n(n={pclass_totals[pclass]})", ha="center", va="top", fontsize=16, color=INK_SOFT)

# Style
ax.set_xlim(0, 1)
ax.set_xticks([])
ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=16, color=INK_SOFT)
ax.set_ylabel("Proportion of Passengers", fontsize=20, color=INK)
ax.set_title(
    "Titanic Survival by Passenger Class · bar-spine · seaborn · anyplot.ai",
    fontsize=24,
    fontweight="medium",
    color=INK,
)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

legend_patches = [mpatches.Patch(color=colors[j], label=fill_order[j]) for j in range(len(fill_order))]
ax.legend(
    handles=legend_patches, loc="upper right", fontsize=16, frameon=True, facecolor=ELEVATED_BG, edgecolor=INK_SOFT
)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
