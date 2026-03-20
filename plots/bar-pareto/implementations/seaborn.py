""" pyplots.ai
bar-pareto: Pareto Chart with Cumulative Line
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-20
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Manufacturing defect types sorted by frequency
data = pd.DataFrame(
    {
        "defect": [
            "Scratches",
            "Dents",
            "Misalignment",
            "Cracks",
            "Discoloration",
            "Burrs",
            "Warping",
            "Contamination",
        ],
        "count": [142, 118, 84, 67, 45, 31, 22, 11],
    }
)

# Compute cumulative percentage
cumulative_pct = np.cumsum(data["count"]) / data["count"].sum() * 100

# Plot setup using seaborn theming
sns.set_context("talk", font_scale=1.1)
sns.set_style("whitegrid", {"axes.grid": False})
pareto_palette = sns.color_palette(["#306998" if cum <= 80 else "#A3BFCF" for cum in cumulative_pct])
fig, ax1 = plt.subplots(figsize=(16, 9))

# Bars - descending order (already sorted)
sns.barplot(data=data, x="defect", y="count", hue="defect", palette=pareto_palette, legend=False, width=0.7, ax=ax1)

# Count annotations on bars
for i, (_, row) in enumerate(data.iterrows()):
    ax1.text(
        i,
        row["count"] + 3,
        str(row["count"]),
        ha="center",
        va="bottom",
        fontsize=14,
        fontweight="bold",
        color="#306998" if cumulative_pct.iloc[i] <= 80 else "#8a9bae",
    )

# Primary y-axis styling
ax1.set_xlabel("Defect Type", fontsize=20)
ax1.set_ylabel("Frequency (Count)", fontsize=20)
ax1.tick_params(axis="both", labelsize=16)
ax1.yaxis.grid(True, alpha=0.2, linewidth=0.8)
ax1.set_axisbelow(True)
sns.despine(ax=ax1, top=True, right=True)

# Secondary y-axis for cumulative percentage
ax2 = ax1.twinx()
ax2.plot(
    range(len(data)),
    cumulative_pct,
    color="#E85D3A",
    marker="o",
    markersize=10,
    linewidth=3,
    markeredgecolor="white",
    markeredgewidth=2,
    zorder=5,
)
ax2.set_ylabel("Cumulative %", fontsize=20, color="#E85D3A")
ax2.set_ylim(0, 105)
ax2.tick_params(axis="y", labelsize=16, colors="#E85D3A")
sns.despine(ax=ax2, top=True, left=True, right=False)
ax2.spines["right"].set_color("#E85D3A")

# 80% reference line
ax2.axhline(y=80, color="#E85D3A", linestyle="--", linewidth=1.5, alpha=0.5)
ax2.text(
    len(data) - 0.5,
    81.5,
    "80%",
    fontsize=14,
    color="#E85D3A",
    fontweight="semibold",
    alpha=0.7,
    ha="right",
    va="bottom",
)

# Title
ax1.set_title("bar-pareto · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=16)

# Y-axis room for annotations
ax1.set_ylim(0, data["count"].max() * 1.18)

fig.subplots_adjust(left=0.08, right=0.90, top=0.92, bottom=0.10)
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
