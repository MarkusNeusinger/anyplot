"""anyplot.ai
mosaic-categorical: Mosaic Plot for Categorical Association Analysis
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-19
"""

import os

import matplotlib.patches as mpatches
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

# Imprint palette: all eight positions, first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

sns.set_theme(
    style="white",
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
TREATMENT = "Treatment arm"  # role: category_1
OUTCOME = "Clinical outcome"  # role: category_2
PATIENTS = "Patients"  # role: frequency

# Data: replace this block with your own table, for example df = pd.read_csv("trial.csv")
df = pd.DataFrame(
    {
        TREATMENT: ["Placebo"] * 3 + ["Drug A"] * 3 + ["Drug B"] * 3,
        OUTCOME: ["Recovered", "Improved", "No change"] * 3,
        PATIENTS: [24, 42, 54, 52, 38, 20, 30, 40, 25],
    }
)

# Plot: reads only df and the constants above
table = df.pivot_table(index=TREATMENT, columns=OUTCOME, values=PATIENTS, aggfunc="sum", sort=False)
arms = list(table.index)
outcomes = list(table.columns)
counts = table.to_numpy(dtype=float)
arm_totals = np.nansum(counts, axis=1)
col_widths = arm_totals / arm_totals.sum()
col_heights = counts / arm_totals[:, np.newaxis]
outcome_palette = sns.color_palette(IMPRINT_PALETTE, n_colors=len(outcomes))
outcome_colors = {outcome: outcome_palette[k] for k, outcome in enumerate(outcomes)}

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

gap = 0.012
x_start = 0.0
centers = []
for i in range(len(arms)):
    width = col_widths[i]
    y_start = 0.0
    for j, outcome in enumerate(outcomes):
        height = col_heights[i, j]
        if not np.isfinite(height):
            continue
        rect = mpatches.FancyBboxPatch(
            (x_start + gap / 2, y_start + gap / 2),
            width - gap,
            height - gap,
            boxstyle="round,pad=0,rounding_size=0.008",
            facecolor=outcome_colors[outcome],
            edgecolor=PAGE_BG,
            linewidth=1.5,
        )
        ax.add_patch(rect)
        if height > 0.08:
            ax.text(
                x_start + width / 2,
                y_start + height / 2,
                f"{counts[i, j]:.0f}",
                ha="center",
                va="center",
                fontsize=12,
                fontweight="bold",
                color="white",
            )
        y_start += height
    centers.append(x_start + width / 2)
    x_start += width

ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_xticks(centers, [f"{arm}\n(n={total:.0f})" for arm, total in zip(arms, arm_totals, strict=True)])
ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0], ["0%", "25%", "50%", "75%", "100%"])
ax.tick_params(axis="both", labelsize=10, length=0, pad=6)
ax.set_xlabel(f"{TREATMENT} (column width = share of all patients)", fontsize=11, fontweight="bold", labelpad=8)
ax.set_ylabel(f"Share of arm by {OUTCOME.lower()}", fontsize=11, fontweight="bold", labelpad=8)
sns.despine(ax=ax, left=True, bottom=True)

title = "Trial Outcomes by Treatment Arm · mosaic-categorical · python · seaborn · anyplot.ai"
title_fontsize = round(12 * (67 / len(title) if len(title) > 67 else 1.0))
ax.set_title(title, fontsize=title_fontsize, fontweight="bold", pad=10, color=INK)

legend_handles = [
    mpatches.Patch(facecolor=outcome_colors[o], edgecolor=PAGE_BG, linewidth=1.5, label=o) for o in outcomes
]
ax.legend(
    handles=legend_handles,
    title=OUTCOME,
    loc="center left",
    bbox_to_anchor=(1.01, 0.5),
    fontsize=10,
    title_fontsize=10,
    framealpha=0.95,
    labelcolor=INK,
)

fig.subplots_adjust(left=0.1, right=0.78, top=0.9, bottom=0.17)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
