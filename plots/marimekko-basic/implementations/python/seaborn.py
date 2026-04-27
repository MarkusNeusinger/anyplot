"""anyplot.ai
marimekko-basic: Basic Marimekko Chart
Library: seaborn 0.13.2 | Python 3.14.4
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

# Okabe-Ito palette — canonical order, first series always #009E73
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

np.random.seed(42)

regions = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East"]
products = ["Electronics", "Apparel", "Food & Beverage", "Home Goods"]

data = {
    "North America": [45, 32, 28, 25],
    "Europe": [38, 42, 35, 22],
    "Asia Pacific": [65, 48, 52, 38],
    "Latin America": [18, 15, 22, 12],
    "Middle East": [12, 8, 15, 10],
}

df_data = []
for region in regions:
    for i, product in enumerate(products):
        df_data.append({"Region": region, "Product": product, "Revenue": data[region][i]})
df = pd.DataFrame(df_data)

region_totals = df.groupby("Region")["Revenue"].sum()
total_revenue = region_totals.sum()
widths = region_totals / total_revenue

fig, ax = plt.subplots(figsize=(16, 9))
fig.subplots_adjust(top=0.86)

x_positions = np.zeros(len(regions))
cumsum = 0
for i, region in enumerate(regions):
    x_positions[i] = cumsum
    cumsum += widths[region]

for region_idx, region in enumerate(regions):
    region_data = df[df["Region"] == region]
    region_total = region_totals[region]
    bar_width = widths[region]
    x_start = x_positions[region_idx]

    y_bottom = 0
    for prod_idx, product in enumerate(products):
        value = region_data[region_data["Product"] == product]["Revenue"].values[0]
        height = value / region_total  # Normalized to proportion

        # Draw rectangle (seaborn has no native Marimekko; matplotlib patches required)
        rect = mpatches.Rectangle(
            (x_start, y_bottom), bar_width, height, facecolor=OKABE_ITO[prod_idx], edgecolor="white", linewidth=2
        )
        ax.add_patch(rect)

        if height > 0.12:
            ax.text(
                x_start + bar_width / 2,
                y_bottom + height / 2,
                f"${value}B",
                ha="center",
                va="center",
                fontsize=16,
                fontweight="bold",
                color="white",
            )

        y_bottom += height

ax.set_xlim(0, 1)
ax.set_ylim(0, 1)

x_centers = x_positions + widths.values / 2
ax.set_xticks(x_centers)
ax.set_xticklabels(regions, fontsize=16)

ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=16)

ax.set_xlabel("Region (width ∝ total revenue)", fontsize=20)
ax.set_ylabel("Product Mix (%)", fontsize=20)

# Title with storytelling subtitle
fig.text(
    0.5,
    0.96,
    "marimekko-basic · seaborn · anyplot.ai",
    ha="center",
    va="top",
    fontsize=24,
    fontweight="bold",
    color=INK,
)
fig.text(
    0.5,
    0.90,
    "Asia Pacific leads with $203B total revenue — Electronics is the top product line globally",
    ha="center",
    va="top",
    fontsize=16,
    color=INK_SOFT,
    style="italic",
)

legend_handles = [
    mpatches.Patch(facecolor=OKABE_ITO[i], edgecolor="white", label=products[i]) for i in range(len(products))
]
ax.legend(
    handles=legend_handles,
    loc="upper left",
    bbox_to_anchor=(1.02, 1),
    fontsize=16,
    title="Product Line",
    title_fontsize=16,
)

# Solid thin grid lines (not dashed)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, linestyle="-")
ax.set_axisbelow(True)

sns.despine(ax=ax, top=True, right=True)

plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
