""" anyplot.ai
map-marker-clustered: Clustered Marker Map
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-23
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

# Geographic context colors (theme-adaptive)
OCEAN_BG = "#C4D9E8" if THEME == "light" else "#192633"
LAND_BG = "#EDE8D4" if THEME == "light" else "#2A2820"
BORDER_COL = "#AAAAAA" if THEME == "light" else "#555550"

# anyplot categorical palette (positions 1-3)
cat_names = ["Retail", "Grocery", "Electronics"]
cat_colors = {"Retail": "#009E73", "Grocery": "#9418DB", "Electronics": "#B71D27"}

# Data: European store locations clustered by city
np.random.seed(42)
city_centers = [
    (48.8566, 2.3522),  # Paris
    (51.5074, -0.1278),  # London
    (52.5200, 13.4050),  # Berlin
    (41.9028, 12.4964),  # Rome
    (40.4168, -3.7038),  # Madrid
    (48.2082, 16.3738),  # Vienna
    (50.0755, 14.4378),  # Prague
    (52.3676, 4.9041),  # Amsterdam
]
n_points_per_city = [45, 50, 35, 40, 30, 25, 20, 35]

lats, lons, categories = [], [], []
for (lat, lon), n_points in zip(city_centers, n_points_per_city, strict=True):
    lats.extend(np.random.normal(lat, 0.8, n_points))
    lons.extend(np.random.normal(lon, 1.2, n_points))
    categories.extend(np.random.choice(cat_names, n_points))

lats = np.array(lats)
lons = np.array(lons)
categories = np.array(categories)

# Grid-based clustering (simulates zoom-level clustering)
grid_size_lat = 3.0
grid_size_lon = 4.0
lat_bins = np.floor((lats - 36) / grid_size_lat).astype(int)
lon_bins = np.floor((lons + 12) / grid_size_lon).astype(int)
cell_ids = lat_bins * 100 + lon_bins

cluster_centers, cluster_sizes, cluster_dominant_cat = [], [], []
for cell_id in np.unique(cell_ids):
    mask = cell_ids == cell_id
    cluster_cats = categories[mask]
    unique_cats, counts = np.unique(cluster_cats, return_counts=True)
    cluster_centers.append((np.mean(lats[mask]), np.mean(lons[mask])))
    cluster_sizes.append(int(np.sum(mask)))
    cluster_dominant_cat.append(unique_cats[np.argmax(counts)])

cluster_centers = np.array(cluster_centers)
cluster_sizes = np.array(cluster_sizes)
cluster_dominant_cat = np.array(cluster_dominant_cat)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(OCEAN_BG)

# Simplified European land polygon
europe_coast_lon = [
    -10,
    -9,
    -9.5,
    -8,
    -5,
    -2,
    0,
    2,
    3,
    5,
    7,
    9,
    10,
    12,
    13,
    15,
    16,
    18,
    20,
    22,
    22,
    20,
    18,
    15,
    12,
    10,
    8,
    5,
    3,
    0,
    -2,
    -5,
    -8,
    -10,
    -10,
]
europe_coast_lat = [
    36,
    37,
    40,
    42,
    43,
    44,
    46,
    47,
    50,
    52,
    54,
    55,
    54,
    52,
    50,
    48,
    46,
    44,
    42,
    40,
    56,
    56,
    55,
    54,
    55,
    55,
    54,
    52,
    50,
    51,
    52,
    48,
    44,
    40,
    36,
]
ax.fill(europe_coast_lon, europe_coast_lat, color=LAND_BG, alpha=0.9, zorder=1)

# Country boundary lines
ax.plot([-2, 3], [42.5, 42.5], color=BORDER_COL, linewidth=0.5, alpha=0.4, zorder=2)
ax.plot([6, 8, 8], [49, 49, 47], color=BORDER_COL, linewidth=0.5, alpha=0.4, zorder=2)
ax.plot([15, 15], [51, 54], color=BORDER_COL, linewidth=0.5, alpha=0.4, zorder=2)
ax.plot([6, 10, 14], [46, 47, 46], color=BORDER_COL, linewidth=0.5, alpha=0.4, zorder=2)

# Subtle coordinate grid
ax.grid(True, alpha=0.10, linestyle="--", color=INK, linewidth=0.5, zorder=3)

# Individual data points (semi-transparent)
for cat in cat_names:
    mask = categories == cat
    ax.scatter(lons[mask], lats[mask], c=cat_colors[cat], alpha=0.20, s=12, edgecolors="none", zorder=4)

# Cluster markers — logarithmic size scaling prevents over-large small-count markers
for center, size, cat in zip(cluster_centers, cluster_sizes, cluster_dominant_cat, strict=True):
    lat, lon = center
    marker_size = 150 + np.log1p(size) * 80
    ax.scatter(lon, lat, s=marker_size, c=cat_colors[cat], alpha=0.88, edgecolors=PAGE_BG, linewidths=1.5, zorder=5)
    ax.annotate(str(size), (lon, lat), fontsize=6, fontweight="bold", ha="center", va="center", color="white", zorder=6)

# Legend
legend_handles = [
    ax.scatter([], [], c=cat_colors[cat], s=60, label=cat, edgecolors=PAGE_BG, linewidths=1) for cat in cat_names
]
leg = ax.legend(
    handles=legend_handles,
    loc="upper left",
    fontsize=7,
    framealpha=0.95,
    title="Store Type",
    title_fontsize=8,
    borderpad=0.6,
    labelspacing=0.4,
)
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)
    leg.get_title().set_color(INK)

# Geographic reference labels
ax.annotate("Atlantic\nOcean", (-9, 46), fontsize=7, style="italic", color=INK_MUTED, ha="center", alpha=0.8, zorder=4)
ax.annotate(
    "Mediterranean Sea", (8, 37.5), fontsize=7, style="italic", color=INK_MUTED, ha="center", alpha=0.8, zorder=4
)

# Style
ax.set_xlabel("Longitude (°)", fontsize=10, color=INK)
ax.set_ylabel("Latitude (°)", fontsize=10, color=INK)
ax.set_title("map-marker-clustered · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.set_xlim(-12, 22)
ax.set_ylim(36, 56)

# Summary annotation
ax.text(
    0.98,
    0.02,
    f"Total: {len(lats)} locations · {len(cluster_sizes)} clusters",
    transform=ax.transAxes,
    fontsize=7,
    ha="right",
    va="bottom",
    style="italic",
    color=INK_MUTED,
    bbox={"boxstyle": "round,pad=0.3", "facecolor": ELEVATED_BG, "alpha": 0.85, "edgecolor": INK_SOFT},
)

fig.subplots_adjust(left=0.09, right=0.98, top=0.93, bottom=0.11)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
