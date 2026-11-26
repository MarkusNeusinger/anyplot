""" anyplot.ai
map-marker-clustered: Clustered Marker Map
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-26
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D
from sklearn.cluster import AgglomerativeClustering


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — canonical order, 4 categories
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#AE3030", "#4467A3", "#BD8233", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
LAT = "Latitude (°)"  # role: lat
LON = "Longitude (°)"  # role: lon
CATEGORY = "Business Type"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("stores.csv")
np.random.seed(42)
n_points = 500
category_names = ["Coffee Shop", "Restaurant", "Bookstore", "Gym"]

# Business hubs on land: Manhattan, Brooklyn, Queens, Bronx, Newark, Jersey City, White Plains, Nassau
neighborhood_centers = np.array(
    [
        [40.75, -73.99],
        [40.66, -73.95],
        [40.73, -73.82],
        [40.85, -73.88],
        [40.73, -74.17],
        [40.72, -74.07],
        [41.03, -73.77],
        [40.72, -73.60],
    ]
)
points_per_neighborhood = n_points // len(neighborhood_centers)

lats, lons, categories = [], [], []
for i, center in enumerate(neighborhood_centers):
    n_pts = points_per_neighborhood + (n_points % len(neighborhood_centers) if i == 0 else 0)
    lats.extend(np.random.normal(center[0], 0.03, n_pts))
    lons.extend(np.random.normal(center[1], 0.03, n_pts))
    categories.extend(np.random.choice(category_names, n_pts))

df = pd.DataFrame({LAT: lats, LON: lons, CATEGORY: categories})

# Plot
category_palette = dict(zip(category_names, IMPRINT_PALETTE, strict=False))

# Apply hierarchical clustering to group nearby markers
coords = df[[LAT, LON]].values
clustering = AgglomerativeClustering(n_clusters=None, distance_threshold=0.1, linkage="ward")
df["cluster"] = clustering.fit_predict(coords)

# Cluster centers, sizes and dominant category
cluster_stats = (
    df.groupby("cluster")
    .agg(
        lat_center=(LAT, "mean"),
        lon_center=(LON, "mean"),
        count=(LAT, "size"),
        dominant_category=(CATEGORY, lambda x: x.mode().iloc[0]),
    )
    .reset_index()
)

# Compute actual cluster size thresholds for accurate legend labels
count_min = int(cluster_stats["count"].min())
count_p33 = int(cluster_stats["count"].quantile(0.33))
count_p66 = int(cluster_stats["count"].quantile(0.66))
count_max = int(cluster_stats["count"].max())

# Set seaborn theme with theme-adaptive chrome
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

# Plot
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Basemap — simplified NYC-region land outlines (lon, lat), quieter than the markers
land_fill = "#ECE8D9" if THEME == "light" else "#24241F"
land_edge = "#B9B5A5" if THEME == "light" else "#4A4A44"
land_polygons = [
    # New Jersey, west of the Hudson
    [
        (-74.45, 40.53),
        (-74.25, 40.52),
        (-74.20, 40.64),
        (-74.12, 40.67),
        (-74.04, 40.70),
        (-74.02, 40.78),
        (-73.97, 40.87),
        (-73.94, 40.98),
        (-73.93, 41.30),
        (-74.45, 41.30),
    ],
    # Bronx, Westchester and Connecticut shore
    [
        (-73.93, 41.30),
        (-73.89, 41.10),
        (-73.90, 40.98),
        (-73.92, 40.88),
        (-73.93, 40.81),
        (-73.83, 40.80),
        (-73.78, 40.82),
        (-73.72, 40.86),
        (-73.65, 40.93),
        (-73.55, 41.00),
        (-73.45, 41.05),
        (-73.35, 41.10),
        (-73.35, 41.30),
    ],
    # Manhattan
    [
        (-74.015, 40.70),
        (-73.975, 40.71),
        (-73.94, 40.79),
        (-73.93, 40.85),
        (-73.935, 40.875),
        (-73.955, 40.85),
        (-73.975, 40.79),
        (-74.01, 40.73),
    ],
    # Staten Island
    [(-74.25, 40.50), (-74.05, 40.57), (-74.07, 40.63), (-74.20, 40.64)],
    # Long Island, with Brooklyn and Queens at its western end
    [
        (-74.04, 40.60),
        (-73.95, 40.575),
        (-73.75, 40.59),
        (-73.50, 40.63),
        (-73.30, 40.67),
        (-73.35, 40.93),
        (-73.55, 40.93),
        (-73.70, 40.87),
        (-73.78, 40.80),
        (-73.90, 40.78),
        (-73.97, 40.70),
        (-74.02, 40.66),
    ],
]
for outline in land_polygons:
    ax.add_patch(mpatches.Polygon(outline, facecolor=land_fill, edgecolor=land_edge, linewidth=0.8, zorder=0))

# KDE density contours — seaborn-distinctive statistical overlay showing point density
sns.kdeplot(data=df, x=LON, y=LAT, levels=6, color=INK_MUTED, alpha=0.2, linewidths=0.9, ax=ax, zorder=1)

# Background layer — individual points at minimal alpha
sns.scatterplot(data=df, x=LON, y=LAT, hue=CATEGORY, palette=category_palette, s=6, alpha=0.08, ax=ax, legend=False)

# Foreground layer — cluster markers sized by count
sns.scatterplot(
    data=cluster_stats,
    x="lon_center",
    y="lat_center",
    size="count",
    hue="dominant_category",
    palette=category_palette,
    sizes=(50, 250),
    alpha=0.85,
    edgecolor=PAGE_BG,
    linewidth=0.8,
    ax=ax,
    legend=False,
)

# Count labels on clusters
for _, row in cluster_stats.iterrows():
    if row["count"] > 1:
        ax.annotate(
            str(int(row["count"])),
            (row["lon_center"], row["lat_center"]),
            ha="center",
            va="center",
            fontsize=8,
            fontweight="bold",
            color="#1A1A17" if row["dominant_category"] == category_names[1] else "white",
            zorder=10,
        )

# Category legend
cat_handles = [
    mpatches.Patch(facecolor=category_palette[cat], edgecolor=PAGE_BG, linewidth=0.5, label=cat)
    for cat in category_names
]
cat_legend = ax.legend(
    handles=cat_handles,
    title="Business Type",
    loc="upper left",
    fontsize=8,
    title_fontsize=9,
    framealpha=0.95,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
)
cat_legend.get_title().set_color(INK)
for text in cat_legend.get_texts():
    text.set_color(INK_SOFT)

# Size legend — labels derived from actual computed cluster size ranges
small_label = f"{count_min} pt" if count_min == count_p33 else f"{count_min}–{count_p33} pts"
medium_label = f"{count_p33 + 1} pt" if count_p33 + 1 == count_p66 else f"{count_p33 + 1}–{count_p66} pts"
large_label = f"{count_p66 + 1}–{count_max} pts" if count_p66 + 1 < count_max else f"{count_max}+ pts"

size_handles = [
    Line2D(
        [0],
        [0],
        marker="o",
        linestyle="",
        markerfacecolor=INK_SOFT,
        markeredgecolor=PAGE_BG,
        markersize=5,
        alpha=0.7,
        label=small_label,
    ),
    Line2D(
        [0],
        [0],
        marker="o",
        linestyle="",
        markerfacecolor=INK_SOFT,
        markeredgecolor=PAGE_BG,
        markersize=8,
        alpha=0.7,
        label=medium_label,
    ),
    Line2D(
        [0],
        [0],
        marker="o",
        linestyle="",
        markerfacecolor=INK_SOFT,
        markeredgecolor=PAGE_BG,
        markersize=11,
        alpha=0.7,
        label=large_label,
    ),
]
size_legend = ax.legend(
    handles=size_handles,
    title="Cluster Size",
    loc="lower left",
    fontsize=8,
    title_fontsize=9,
    framealpha=0.95,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
)
size_legend.get_title().set_color(INK)
for text in size_legend.get_texts():
    text.set_color(INK_SOFT)
ax.add_artist(cat_legend)

# Style
ax.set_xlabel("Longitude (°)", fontsize=10, color=INK)
ax.set_ylabel("Latitude (°)", fontsize=10, color=INK)
ax.set_title("map-marker-clustered · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

ax.set_aspect(1 / np.cos(np.radians(40.8)))
ax.set_xlim(-74.35, -73.4)
ax.set_ylim(40.48, 41.15)
sns.despine(ax=ax, left=False, bottom=False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)
ax.grid(True, alpha=0.10, linestyle="-", linewidth=0.6, color=INK)

# Summary annotation (lower right, away from size legend)
ax.text(
    0.98,
    0.02,
    f"{n_points} locations · {len(cluster_stats)} clusters",
    transform=ax.transAxes,
    fontsize=7,
    ha="right",
    va="bottom",
    style="italic",
    color=INK_MUTED,
    bbox={"boxstyle": "round,pad=0.3", "facecolor": ELEVATED_BG, "alpha": 0.85, "edgecolor": INK_SOFT},
)

# Save
plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
