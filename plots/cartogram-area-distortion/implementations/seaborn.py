""" pyplots.ai
cartogram-area-distortion: Cartogram with Area Distortion by Data Value
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-13
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D


# Data: US states with population (millions) and grid positions
np.random.seed(42)

states_data = {
    # (row, col, population_millions, region)
    "WA": (0, 1, 7.7, "West"),
    "MT": (0, 3, 1.1, "West"),
    "ND": (0, 5, 0.8, "Midwest"),
    "MN": (0, 6, 5.7, "Midwest"),
    "WI": (0, 7, 5.9, "Midwest"),
    "MI": (0, 8, 10.0, "Midwest"),
    "NY": (0, 10, 19.5, "Northeast"),
    "VT": (0, 11, 0.6, "Northeast"),
    "ME": (0, 12, 1.4, "Northeast"),
    "OR": (1, 1, 4.2, "West"),
    "ID": (1, 2, 1.9, "West"),
    "WY": (1, 3, 0.6, "West"),
    "SD": (1, 5, 0.9, "Midwest"),
    "IA": (1, 6, 3.2, "Midwest"),
    "IL": (1, 7, 12.6, "Midwest"),
    "IN": (1, 8, 6.8, "Midwest"),
    "OH": (1, 9, 11.8, "Midwest"),
    "PA": (1, 10, 13.0, "Northeast"),
    "MA": (1, 11, 7.0, "Northeast"),
    "NH": (1, 12, 1.4, "Northeast"),
    "NV": (2, 1, 3.1, "West"),
    "UT": (2, 2, 3.3, "West"),
    "CO": (2, 3, 5.8, "West"),
    "NE": (2, 5, 2.0, "Midwest"),
    "KS": (2, 6, 2.9, "Midwest"),
    "MO": (2, 7, 6.2, "Midwest"),
    "KY": (2, 8, 4.5, "South"),
    "WV": (2, 9, 1.8, "South"),
    "VA": (2, 10, 8.6, "South"),
    "MD": (2, 11, 6.2, "South"),
    "NJ": (2, 12, 9.3, "Northeast"),
    "CA": (3, 1, 39.0, "West"),
    "AZ": (3, 2, 7.3, "West"),
    "NM": (3, 3, 2.1, "West"),
    "OK": (3, 5, 4.0, "South"),
    "AR": (3, 6, 3.0, "South"),
    "TN": (3, 7, 7.0, "South"),
    "NC": (3, 9, 10.6, "South"),
    "SC": (3, 10, 5.2, "South"),
    "DE": (3, 11, 1.0, "Northeast"),
    "CT": (3, 12, 3.6, "Northeast"),
    "TX": (4, 3, 29.5, "South"),
    "LA": (4, 5, 4.6, "South"),
    "MS": (4, 6, 3.0, "South"),
    "AL": (4, 7, 5.0, "South"),
    "GA": (4, 8, 10.8, "South"),
    "FL": (4, 10, 22.2, "South"),
    "RI": (4, 12, 1.1, "Northeast"),
    "AK": (5, 0, 0.7, "West"),
    "HI": (5, 2, 1.4, "West"),
}

# Build dataframe
rows = []
for state, (r, c, pop, region) in states_data.items():
    rows.append({"state": state, "row": r, "col": c, "population": pop, "region": region})
df = pd.DataFrame(rows)

# Marker size range for sns.scatterplot size mapping
size_min = 80
size_max = 4000

# Colorblind-safe palette using seaborn's "colorblind" palette
region_order = ["West", "Midwest", "South", "Northeast"]
cb_palette = sns.color_palette("colorblind", n_colors=4)
region_palette = dict(zip(region_order, cb_palette, strict=False))

# Setup theme using seaborn
sns.set_theme(
    style="white", context="talk", font_scale=1.1, rc={"figure.facecolor": "#f5f5f5", "axes.facecolor": "#f5f5f5"}
)

fig = plt.figure(figsize=(16, 9))
gs = fig.add_gridspec(1, 2, width_ratios=[3.5, 1], wspace=0.08)
ax_main = fig.add_subplot(gs[0, 0])
ax_ref = fig.add_subplot(gs[0, 1])

# Main cartogram using sns.scatterplot with size parameter
sns.scatterplot(
    data=df,
    x="col",
    y="row",
    size="population",
    sizes=(size_min, size_max),
    hue="region",
    hue_order=region_order,
    palette=region_palette,
    marker="s",
    alpha=0.85,
    edgecolor="white",
    linewidth=1.5,
    legend=False,
    ax=ax_main,
)

# State abbreviation labels on main cartogram
for _, row in df.iterrows():
    pop_frac = row["population"] / df["population"].max()
    fontsize = max(9, min(18, int(10 + pop_frac * 8)))
    ax_main.text(
        row["col"],
        row["row"] - 0.03,
        row["state"],
        ha="center",
        va="center",
        fontsize=fontsize,
        fontweight="bold",
        color="white",
        zorder=5,
    )
    # Population label for larger states
    if row["population"] >= 5.0:
        ax_main.text(
            row["col"],
            row["row"] + 0.2,
            f"{row['population']:.0f}M",
            ha="center",
            va="center",
            fontsize=max(7, int(fontsize * 0.6)),
            color="white",
            alpha=0.9,
            zorder=5,
        )

# Style main axes
ax_main.invert_yaxis()
ax_main.set_aspect("equal")
ax_main.set_xlim(-1.0, 13.5)
ax_main.set_ylim(6.0, -0.8)
ax_main.set_xlabel("")
ax_main.set_ylabel("")
ax_main.set_xticks([])
ax_main.set_yticks([])
sns.despine(ax=ax_main, left=True, bottom=True)

# Title
ax_main.set_title(
    "US States by Population\ncartogram-area-distortion · seaborn · pyplots.ai", fontsize=22, fontweight="bold", pad=16
)

# Build custom legend with seaborn palette colors
legend_handles = [
    Line2D(
        [0],
        [0],
        marker="s",
        color="none",
        markerfacecolor=region_palette[r],
        markersize=14,
        markeredgecolor="white",
        markeredgewidth=1,
        label=r,
    )
    for r in region_order
]
ax_main.legend(
    handles=legend_handles,
    loc="lower left",
    fontsize=14,
    title="Region",
    title_fontsize=16,
    framealpha=0.95,
    edgecolor="#cccccc",
)

# Size annotation
ax_main.text(
    0.98,
    0.02,
    "Tile area \u221d state population",
    ha="right",
    va="bottom",
    fontsize=13,
    color="#666666",
    fontstyle="italic",
    transform=ax_main.transAxes,
)

# --- Reference inset: equal-size tile map for comparison ---
sns.scatterplot(
    data=df,
    x="col",
    y="row",
    hue="region",
    hue_order=region_order,
    palette=region_palette,
    marker="s",
    s=150,
    alpha=0.7,
    edgecolor="white",
    linewidth=0.8,
    legend=False,
    ax=ax_ref,
)

# Labels on reference map
for _, row in df.iterrows():
    ax_ref.text(
        row["col"],
        row["row"],
        row["state"],
        ha="center",
        va="center",
        fontsize=6,
        fontweight="bold",
        color="white",
        zorder=5,
    )

ax_ref.invert_yaxis()
ax_ref.set_aspect("equal")
ax_ref.set_xlim(-0.5, 13.0)
ax_ref.set_ylim(5.8, -0.5)
ax_ref.set_xlabel("")
ax_ref.set_ylabel("")
ax_ref.set_xticks([])
ax_ref.set_yticks([])
sns.despine(ax=ax_ref, left=True, bottom=True)
ax_ref.set_title("Equal-Area\nReference", fontsize=13, fontweight="bold", pad=10)

plt.savefig("plot.png", dpi=300, bbox_inches="tight")
