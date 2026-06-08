"""anyplot.ai
cartogram-area-distortion: Cartogram with Area Distortion by Data Value
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-06-08
"""

import os

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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data: US states with population (millions) and approximate grid positions
np.random.seed(42)

states_data = {
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

rows_data = []
for state, (r, c, pop, region) in states_data.items():
    rows_data.append({"state": state, "row": r, "col": c, "population": pop, "region": region})
df = pd.DataFrame(rows_data)

# Region colors using Imprint palette (West→green, Midwest→lavender, South→blue, Northeast→ochre)
region_order = ["West", "Midwest", "South", "Northeast"]
region_palette = dict(zip(region_order, IMPRINT_PALETTE[:4], strict=False))

# Apply seaborn theme with theme-adaptive tokens
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
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Canvas — exactly 3200×1800 px (landscape 16:9)
fig = plt.figure(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
gs = fig.add_gridspec(
    2,
    2,
    width_ratios=[3.0, 1.2],
    height_ratios=[1, 1],
    wspace=0.12,
    hspace=0.32,
    left=0.01,
    right=0.99,
    top=0.89,
    bottom=0.04,
)
ax_main = fig.add_subplot(gs[:, 0])
ax_ref = fig.add_subplot(gs[0, 1])
ax_bar = fig.add_subplot(gs[1, 1])

# Marker sizes calibrated for 3200×1800 canvas
size_min = 20
size_max = 620

# Main cartogram: bubble area ∝ population, color = geographic region
sns.scatterplot(
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
    alpha=0.88,
    edgecolor=PAGE_BG,
    linewidth=0.5,
    ax=ax_main,
)

# Compact region legend — keep only hue (region) handles, remove size handles
handles, labels = ax_main.get_legend_handles_labels()
region_handles, region_labels = [], []
seen = set()
for handle, lbl in zip(handles, labels, strict=False):
    if lbl in region_order and lbl not in seen:
        try:
            handle.set_markersize(7)
            handle.set_markeredgecolor(PAGE_BG)
            handle.set_markeredgewidth(0.4)
        except AttributeError:
            pass
        region_handles.append(handle)
        region_labels.append(lbl)
        seen.add(lbl)

ax_main.get_legend().remove()
ax_main.legend(
    handles=region_handles,
    labels=region_labels,
    loc="upper center",
    fontsize=5.5,
    title="Region",
    title_fontsize=6,
    framealpha=0.9,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    ncol=4,
    bbox_to_anchor=(0.42, 1.0),
    borderpad=0.4,
    columnspacing=0.7,
    handletextpad=0.3,
)

# State abbreviation labels — size scales with population
pop_max = df["population"].max()
for _, row in df.iterrows():
    pop_frac = row["population"] / pop_max
    fontsize = max(4, min(7, int(4 + pop_frac * 3.5)))
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
    if row["population"] >= 8.0:
        ax_main.text(
            row["col"],
            row["row"] + 0.22,
            f"{row['population']:.0f}M",
            ha="center",
            va="center",
            fontsize=max(3.5, int(fontsize * 0.65)),
            color="white",
            alpha=0.9,
            zorder=5,
        )

ax_main.invert_yaxis()
ax_main.set_xlim(-0.8, 13.5)
ax_main.set_ylim(5.8, -0.7)
ax_main.set_xlabel("")
ax_main.set_ylabel("")
ax_main.set_xticks([])
ax_main.set_yticks([])
ax_main.set_facecolor(PAGE_BG)
sns.despine(ax=ax_main, left=True, bottom=True)

# Title — scale fontsize for long title string
title = "US States by Population · cartogram-area-distortion · python · seaborn · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_fontsize = max(8, round(12 * ratio))
ax_main.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=8)

ax_main.text(
    0.98,
    0.02,
    "Tile area ∝ state population",
    ha="right",
    va="bottom",
    fontsize=5.5,
    color=INK_MUTED,
    fontstyle="italic",
    transform=ax_main.transAxes,
)

# Reference inset — equal-area tile map for comparison
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
    s=22,
    alpha=0.72,
    edgecolor=PAGE_BG,
    linewidth=0.3,
    legend=False,
    ax=ax_ref,
)

for _, row in df.iterrows():
    ax_ref.text(
        row["col"],
        row["row"],
        row["state"],
        ha="center",
        va="center",
        fontsize=3.5,
        fontweight="bold",
        color="white",
        zorder=5,
    )

ax_ref.invert_yaxis()
ax_ref.set_xlim(-0.5, 13.0)
ax_ref.set_ylim(5.8, -0.5)
ax_ref.set_xlabel("")
ax_ref.set_ylabel("")
ax_ref.set_xticks([])
ax_ref.set_yticks([])
ax_ref.set_facecolor(PAGE_BG)
sns.despine(ax=ax_ref, left=True, bottom=True)
ax_ref.set_title("Equal-Area Reference", fontsize=7.5, fontweight="bold", color=INK, pad=4)

# Regional population totals: horizontal bar chart
region_totals = df.groupby("region", observed=True)["population"].sum().reset_index()
region_totals.columns = ["region", "total_pop"]

sns.barplot(
    data=region_totals,
    x="total_pop",
    y="region",
    hue="region",
    hue_order=region_order,
    order=region_order,
    palette=region_palette,
    edgecolor=PAGE_BG,
    linewidth=0.8,
    legend=False,
    ax=ax_bar,
)

for i, region_name in enumerate(region_order):
    val = region_totals.loc[region_totals["region"] == region_name, "total_pop"].values[0]
    ax_bar.text(val + 1.0, i, f"{val:.0f}M", ha="left", va="center", fontsize=6.5, fontweight="bold", color=INK_SOFT)

ax_bar.set_xlabel("Total Population (M)", fontsize=7.5, color=INK)
ax_bar.set_ylabel("", color=INK)
ax_bar.set_title("Regional Totals", fontsize=8, fontweight="bold", color=INK, pad=4)
ax_bar.tick_params(axis="y", labelsize=7, colors=INK_SOFT)
ax_bar.tick_params(axis="x", labelsize=6.5, colors=INK_SOFT)
ax_bar.set_xlim(0, region_totals["total_pop"].max() * 1.25)
ax_bar.set_facecolor(PAGE_BG)
sns.despine(ax=ax_bar, left=True)
ax_bar.xaxis.grid(True, alpha=0.15, linewidth=0.6, color=INK)

# Save — no bbox_inches='tight' per seaborn canvas rules
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
