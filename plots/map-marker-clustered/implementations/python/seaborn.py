""" pyplots.ai
map-marker-clustered: Clustered Marker Map
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-20
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D
from sklearn.cluster import AgglomerativeClustering


# Generate sample geographic data - business locations across NYC region
np.random.seed(42)
n_points = 500

# Create clustered geographic data (simulating city with neighborhoods)
n_neighborhoods = 8
neighborhood_centers = np.random.uniform(-0.5, 0.5, (n_neighborhoods, 2))
points_per_neighborhood = n_points // n_neighborhoods

lats, lons, categories = [], [], []
category_names = ["Coffee Shop", "Restaurant", "Bookstore", "Gym"]

for i, center in enumerate(neighborhood_centers):
    n_pts = points_per_neighborhood + (n_points % n_neighborhoods if i == 0 else 0)
    lat = np.random.normal(center[0], 0.08, n_pts) + 40.7  # NYC-like latitude
    lon = np.random.normal(center[1], 0.08, n_pts) - 74.0  # NYC-like longitude
    lats.extend(lat)
    lons.extend(lon)
    categories.extend(np.random.choice(category_names, n_pts))

df = pd.DataFrame({"lat": lats, "lon": lons, "category": categories})

# Apply hierarchical clustering to group nearby markers
coords = df[["lat", "lon"]].values
clustering = AgglomerativeClustering(n_clusters=None, distance_threshold=0.05, linkage="ward")
df["cluster"] = clustering.fit_predict(coords)

# Calculate cluster centers and sizes
cluster_stats = (
    df.groupby("cluster")
    .agg(
        lat_center=("lat", "mean"),
        lon_center=("lon", "mean"),
        count=("lat", "size"),
        dominant_category=("category", lambda x: x.mode().iloc[0]),
    )
    .reset_index()
)

# Set seaborn context and style for the entire plot
sns.set_theme(style="whitegrid", context="talk", font_scale=1.2)

# Use colorblind-friendly palette from seaborn
palette = sns.color_palette("colorblind", n_colors=4)
category_palette = dict(zip(category_names, palette, strict=True))

# Create the plot
fig, ax = plt.subplots(figsize=(16, 9))

# Add simplified geographic context - stylized NYC region boundaries
# Hudson River approximation (western boundary)
hudson_river = [[(-74.05, 40.70), (-74.02, 40.85), (-73.95, 41.00), (-73.90, 41.15)]]
# Long Island Sound approximation (eastern boundary)
li_sound = [[(-73.80, 40.85), (-73.70, 40.95), (-73.55, 41.05)]]
# Atlantic coast approximation (southern boundary)
coast = [[(-74.20, 40.55), (-74.00, 40.50), (-73.80, 40.58), (-73.60, 40.62)]]

# Draw water boundaries as light blue lines for geographic context
for boundary in [hudson_river, li_sound, coast]:
    for segment in boundary:
        xs, ys = zip(*segment, strict=True)
        ax.plot(xs, ys, color="#a8d4e6", linewidth=8, alpha=0.4, zorder=0, solid_capstyle="round")

# Add a subtle land area fill
land_coords = [(-74.45, 40.0), (-74.45, 41.25), (-73.35, 41.25), (-73.35, 40.0)]
land_patch = mpatches.Polygon(land_coords, facecolor="#f5f5dc", edgecolor="none", alpha=0.3, zorder=-1)
ax.add_patch(land_patch)

# Plot individual points as background layer using seaborn scatterplot
sns.scatterplot(
    data=df, x="lon", y="lat", hue="category", palette=category_palette, s=40, alpha=0.3, ax=ax, legend=False
)

# Create cluster dataframe for seaborn visualization
cluster_stats["size_scaled"] = cluster_stats["count"] * 20
cluster_stats["color"] = cluster_stats["dominant_category"].map(category_palette)

# Plot cluster markers using seaborn scatterplot with size encoding
sns.scatterplot(
    data=cluster_stats,
    x="lon_center",
    y="lat_center",
    size="count",
    hue="dominant_category",
    palette=category_palette,
    sizes=(100, 800),
    alpha=0.85,
    edgecolor="white",
    linewidth=2,
    ax=ax,
    legend=False,
)

# Add count labels to larger clusters
for _, row in cluster_stats.iterrows():
    if row["count"] > 4:
        ax.annotate(
            str(int(row["count"])),
            (row["lon_center"], row["lat_center"]),
            ha="center",
            va="center",
            fontsize=11,
            fontweight="bold",
            color="white",
            zorder=10,
        )

# Create custom legend using matplotlib patches to avoid seaborn override
handles = [
    mpatches.Patch(facecolor=category_palette[cat], edgecolor="white", linewidth=1.5, label=cat)
    for cat in category_names
]
legend = ax.legend(
    handles=handles,
    title="Business Type",
    loc="upper left",
    fontsize=14,
    title_fontsize=16,
    framealpha=0.95,
    edgecolor="gray",
)
legend.get_frame().set_linewidth(1.5)

# Add size legend for cluster markers
size_handles = [
    Line2D([0], [0], marker="o", color="w", markerfacecolor="gray", markersize=8, alpha=0.7, label="2-5 points"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="gray", markersize=14, alpha=0.7, label="6-15 points"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="gray", markersize=20, alpha=0.7, label="16+ points"),
]
size_legend = ax.legend(
    handles=size_handles,
    title="Cluster Size",
    loc="lower left",
    fontsize=12,
    title_fontsize=14,
    framealpha=0.95,
    edgecolor="gray",
)
size_legend.get_frame().set_linewidth(1.5)
ax.add_artist(legend)  # Re-add the first legend

# Styling with seaborn-friendly axis formatting
ax.set_xlabel("Longitude (°)", fontsize=20)
ax.set_ylabel("Latitude (°)", fontsize=20)
ax.set_title("map-marker-clustered · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=15)
ax.tick_params(axis="both", labelsize=16)

# Customize grid using seaborn despine and grid settings
sns.despine(ax=ax, left=False, bottom=False)
ax.grid(True, alpha=0.15, linestyle="-", color="lightgray")

# Add annotation about clustering
ax.text(
    0.02,
    0.02,
    f"{n_points} locations · {len(cluster_stats)} clusters",
    transform=ax.transAxes,
    fontsize=13,
    ha="left",
    va="bottom",
    style="italic",
    color="dimgray",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.8, "edgecolor": "lightgray"},
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
