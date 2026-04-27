""" anyplot.ai
marimekko-basic: Basic Marimekko Chart
Library: matplotlib 3.10.9 | Python 3.14.4
Quality: 85/100 | Updated: 2026-04-27
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data: Market share by region (x-category) and product line (y-category)
regions = ["North America", "Europe", "Asia Pacific", "Latin America"]
products = ["Electronics", "Apparel", "Home & Garden", "Sports"]

# Values matrix: rows = products, columns = regions
# Each column total determines that region's bar width
values = np.array(
    [
        [120, 85, 200, 35],  # Electronics
        [80, 110, 150, 45],  # Apparel
        [60, 70, 80, 25],  # Home & Garden
        [40, 35, 70, 15],  # Sports
    ]
)

# Okabe-Ito palette (positions 1-4 in canonical order)
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]
# Smart label contrast: white on dark segments, ink on lighter #CC79A7
label_colors = ["white", "white", "white", INK]

# Calculate bar widths (proportional to column totals)
column_totals = values.sum(axis=0)
total = column_totals.sum()
bar_widths = column_totals / total
cum_widths = np.concatenate([[0], np.cumsum(bar_widths)[:-1]])

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for i, (product, color, label_color) in enumerate(zip(products, OKABE_ITO, label_colors, strict=True)):
    heights = values[i] / column_totals
    bottoms = values[:i].sum(axis=0) / column_totals if i > 0 else np.zeros(len(regions))

    for j in range(len(regions)):
        ax.bar(
            cum_widths[j] + bar_widths[j] / 2,
            heights[j],
            width=bar_widths[j] * 0.98,
            bottom=bottoms[j],
            color=color,
            edgecolor=PAGE_BG,
            linewidth=2,
            label=product if j == 0 else None,
        )

        if heights[j] > 0.12:
            ax.text(
                cum_widths[j] + bar_widths[j] / 2,
                bottoms[j] + heights[j] / 2,
                f"${values[i, j]}M",
                ha="center",
                va="center",
                fontsize=14,
                fontweight="bold",
                color=label_color,
            )

# Region labels below bars
for j, region in enumerate(regions):
    ax.text(
        cum_widths[j] + bar_widths[j] / 2,
        -0.05,
        f"{region}\n(${column_totals[j]:.0f}M)",
        ha="center",
        va="top",
        fontsize=14,
        fontweight="bold",
        color=INK,
    )

# Style
ax.set_xlim(0, 1)
ax.set_ylim(-0.20, 1.05)
ax.set_ylabel("Share within Region", fontsize=20, color=INK)

fig.suptitle("marimekko-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK, y=0.99)
ax.set_title("Bar width proportional to total regional market size", fontsize=16, color=INK_MUTED, pad=10)

ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
ax.tick_params(axis="y", labelsize=16, colors=INK_SOFT)
ax.set_xticks([])

# Legend below the chart, horizontal layout
leg = ax.legend(
    loc="upper center",
    bbox_to_anchor=(0.5, -0.16),
    ncol=len(products),
    fontsize=16,
    title="Product Lines",
    title_fontsize=16,
    frameon=True,
)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)
leg.get_title().set_color(INK_SOFT)

# Grid and spines
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
