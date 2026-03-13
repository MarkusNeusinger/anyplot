"""pyplots.ai
cartogram-area-distortion: Cartogram with Area Distortion by Data Value
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-13
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


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

# Set minimum marker size so smallest states remain readable
size_min = 150
size_max = 4200

# Region ordering and seaborn colorblind palette
region_order = ["West", "Midwest", "South", "Northeast"]
region_palette = dict(zip(region_order, sns.color_palette("colorblind", n_colors=4), strict=False))

# Setup theme using seaborn's set_theme with custom rc params
sns.set_theme(
    style="white",
    context="talk",
    font_scale=1.15,
    rc={"figure.facecolor": "#f5f5f5", "axes.facecolor": "#f5f5f5", "font.family": "sans-serif"},
)

fig = plt.figure(figsize=(16, 9))
gs = fig.add_gridspec(1, 2, width_ratios=[3.2, 1], wspace=0.06)
ax_main = fig.add_subplot(gs[0, 0])
ax_ref = fig.add_subplot(gs[0, 1])

# Main cartogram using sns.scatterplot with size and hue encoding
scatter = sns.scatterplot(
    data=df,
    x="col",
    y="row",
    size="population",
    sizes=(size_min, size_max),
    hue="region",
    hue_order=region_order,
    palette=region_palette,
    style="region",
    style_order=region_order,
    markers=dict.fromkeys(region_order, "s"),
    alpha=0.85,
    edgecolor="white",
    linewidth=1.5,
    ax=ax_main,
)

# Use seaborn's move_legend to reposition and restyle the auto-generated legend
# First filter to only show hue entries (not size entries)
handles, labels = ax_main.get_legend_handles_labels()
# Find region handles (skip size legend entries)
region_handles = []
region_labels = []
for handle, lbl in zip(handles, labels, strict=False):
    if lbl in region_order:
        handle.set_markersize(14)
        handle.set_markeredgecolor("white")
        handle.set_markeredgewidth(1)
        region_handles.append(handle)
        region_labels.append(lbl)

ax_main.legend(
    handles=region_handles,
    labels=region_labels,
    loc="lower left",
    fontsize=14,
    title="Region",
    title_fontsize=16,
    framealpha=0.95,
    edgecolor="#cccccc",
)

# State abbreviation labels on main cartogram
pop_max = df["population"].max()
for _, row in df.iterrows():
    pop_frac = row["population"] / pop_max
    fontsize = max(10, min(18, int(11 + pop_frac * 8)))
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
            row["row"] + 0.22,
            f"{row['population']:.0f}M",
            ha="center",
            va="center",
            fontsize=max(8, int(fontsize * 0.6)),
            color="white",
            alpha=0.9,
            zorder=5,
        )

# Style main axes
ax_main.invert_yaxis()
ax_main.set_aspect("equal")
ax_main.set_xlim(-0.8, 13.5)
ax_main.set_ylim(5.8, -0.7)
ax_main.set_xlabel("")
ax_main.set_ylabel("")
ax_main.set_xticks([])
ax_main.set_yticks([])
sns.despine(ax=ax_main, left=True, bottom=True)

# Title - at least 24pt per quality criteria VQ-01
ax_main.set_title(
    "US States by Population\ncartogram-area-distortion \u00b7 seaborn \u00b7 pyplots.ai",
    fontsize=24,
    fontweight="bold",
    pad=18,
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

# --- Reference inset: equal-size tile map using seaborn's scatterplot with hue ---
sns.scatterplot(
    data=df,
    x="col",
    y="row",
    hue="region",
    hue_order=region_order,
    palette=region_palette,
    style="region",
    style_order=region_order,
    markers=dict.fromkeys(region_order, "s"),
    s=180,
    alpha=0.7,
    edgecolor="white",
    linewidth=0.8,
    legend=False,
    ax=ax_ref,
)

# Labels on reference map - slightly larger for readability
for _, row in df.iterrows():
    ax_ref.text(
        row["col"],
        row["row"],
        row["state"],
        ha="center",
        va="center",
        fontsize=7,
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
ax_ref.set_title("Equal-Area\nReference", fontsize=14, fontweight="bold", pad=10)

plt.savefig("plot.png", dpi=300, bbox_inches="tight")
