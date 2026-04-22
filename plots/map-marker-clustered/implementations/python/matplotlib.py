""" pyplots.ai
map-marker-clustered: Clustered Marker Map
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import matplotlib.pyplot as plt
import numpy as np


# Data: Generate store locations across Europe
np.random.seed(42)

# Create clustered geographic data (simulating store locations)
# Cluster centers represent major cities
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

# Generate points around each city
n_points_per_city = [45, 50, 35, 40, 30, 25, 20, 35]
lats = []
lons = []
categories = []
cat_names = ["Retail", "Grocery", "Electronics"]

for (lat, lon), n_points in zip(city_centers, n_points_per_city, strict=True):
    lats.extend(np.random.normal(lat, 0.8, n_points))
    lons.extend(np.random.normal(lon, 1.2, n_points))
    categories.extend(np.random.choice(cat_names, n_points))

lats = np.array(lats)
lons = np.array(lons)
categories = np.array(categories)

# Grid-based clustering (simulates zoom-level clustering)
# Divide map into grid cells and cluster points within each cell
grid_size_lat = 3.0  # degrees
grid_size_lon = 4.0  # degrees

# Compute grid cell for each point
lat_bins = np.floor((lats - 36) / grid_size_lat).astype(int)
lon_bins = np.floor((lons + 12) / grid_size_lon).astype(int)
cell_ids = lat_bins * 100 + lon_bins  # unique cell ID

# Calculate cluster centers and sizes
unique_cells = np.unique(cell_ids)
cluster_centers = []
cluster_sizes = []
cluster_dominant_cat = []

for cell_id in unique_cells:
    mask = cell_ids == cell_id
    cluster_lats = lats[mask]
    cluster_lons = lons[mask]
    cluster_cats = categories[mask]

    center_lat = np.mean(cluster_lats)
    center_lon = np.mean(cluster_lons)
    size = int(np.sum(mask))

    # Find dominant category
    unique_cats, counts = np.unique(cluster_cats, return_counts=True)
    dominant = unique_cats[np.argmax(counts)]

    cluster_centers.append((center_lat, center_lon))
    cluster_sizes.append(size)
    cluster_dominant_cat.append(dominant)

cluster_centers = np.array(cluster_centers)
cluster_sizes = np.array(cluster_sizes)
cluster_dominant_cat = np.array(cluster_dominant_cat)

# Color mapping for categories
cat_colors = {
    "Retail": "#306998",  # Python Blue
    "Grocery": "#2E7D32",  # Green
    "Electronics": "#FFD43B",  # Python Yellow
}

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Draw background to simulate ocean/land
ax.set_facecolor("#d4e6f1")  # Light blue for ocean

# Simplified European coastline outline (approximate polygon)
# This provides geographic context without external dependencies
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
ax.fill(europe_coast_lon, europe_coast_lat, color="#f5f5dc", alpha=0.9, zorder=1)  # Beige land

# Add simplified country boundaries (major borders)
# France-Spain border (Pyrenees)
ax.plot([-2, 3], [42.5, 42.5], color="#999999", linewidth=1, linestyle="-", alpha=0.5, zorder=2)
# France-Germany border
ax.plot([6, 8, 8], [49, 49, 47], color="#999999", linewidth=1, linestyle="-", alpha=0.5, zorder=2)
# Germany-Poland border
ax.plot([15, 15], [51, 54], color="#999999", linewidth=1, linestyle="-", alpha=0.5, zorder=2)
# Alps region line
ax.plot([6, 10, 14], [46, 47, 46], color="#999999", linewidth=1, linestyle="-", alpha=0.5, zorder=2)

# Subtle coordinate grid (dashed for subtlety)
ax.grid(True, alpha=0.3, linestyle="--", color="#888888", linewidth=0.8, zorder=3)

# Plot individual points (semi-transparent, smaller) to show raw data
for cat in cat_names:
    mask = categories == cat
    ax.scatter(lons[mask], lats[mask], c=cat_colors[cat], alpha=0.25, s=50, edgecolors="none", label=None, zorder=4)

# Plot cluster markers (larger circles with count)
for center, size, cat in zip(cluster_centers, cluster_sizes, cluster_dominant_cat, strict=True):
    lat, lon = center
    # Size scales with number of points in cluster
    marker_size = 400 + size * 25

    # Draw cluster circle
    ax.scatter(lon, lat, s=marker_size, c=cat_colors[cat], alpha=0.85, edgecolors="white", linewidths=3, zorder=5)

    # Add count text
    fontsize = 16 if size < 100 else 14
    ax.annotate(
        str(size), (lon, lat), fontsize=fontsize, fontweight="bold", ha="center", va="center", color="white", zorder=6
    )

# Create legend for categories
legend_handles = []
for cat in cat_names:
    handle = ax.scatter([], [], c=cat_colors[cat], s=250, label=cat, edgecolors="white", linewidths=2)
    legend_handles.append(handle)

ax.legend(
    handles=legend_handles,
    loc="upper left",
    fontsize=14,
    framealpha=0.95,
    title="Store Type",
    title_fontsize=16,
    edgecolor="#cccccc",
)

# Add geographic reference labels
ax.annotate("Atlantic\nOcean", (-9, 46), fontsize=13, style="italic", color="#6699bb", ha="center", alpha=0.8)
ax.annotate("Mediterranean Sea", (8, 37.5), fontsize=13, style="italic", color="#6699bb", ha="center", alpha=0.8)

# Labels and styling
ax.set_xlabel("Longitude (degrees)", fontsize=20)
ax.set_ylabel("Latitude (degrees)", fontsize=20)
ax.set_title("map-marker-clustered \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Set axis limits to show Europe
ax.set_xlim(-12, 22)
ax.set_ylim(36, 56)

# Add explanatory note
ax.text(
    0.98,
    0.02,
    f"Total: {len(lats)} locations in {len(cluster_sizes)} clusters",
    transform=ax.transAxes,
    fontsize=13,
    ha="right",
    va="bottom",
    style="italic",
    color="#555555",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.8, "edgecolor": "none"},
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
