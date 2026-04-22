""" pyplots.ai
map-marker-clustered: Clustered Marker Map
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 78/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_text,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    scale_size_continuous,
    theme,
    theme_minimal,
)
from scipy.cluster.hierarchy import fcluster, linkage


# Random seed for reproducibility
np.random.seed(42)

# Generate sample store locations (simulating US West Coast region)
# Major city centers - spread out more to ensure clusters don't overlap
cities = {
    "Seattle": (47.6, -122.3),
    "Portland": (45.5, -122.7),
    "San Francisco": (37.8, -122.4),
    "Los Angeles": (34.1, -118.2),
    "San Diego": (32.7, -117.2),
}

# Generate 300 store locations clustered around major cities
n_points = 300
lats = []
lons = []
categories = []

category_types = ["Retail", "Restaurant", "Service", "Entertainment"]
city_names = list(cities.keys())

for _ in range(n_points):
    # Pick a random city center
    city = np.random.choice(city_names)
    center_lat, center_lon = cities[city]

    # Add random offset (very tight clustering to ensure single cluster per city)
    lat = center_lat + np.random.normal(0, 0.08)
    lon = center_lon + np.random.normal(0, 0.08)

    lats.append(lat)
    lons.append(lon)
    categories.append(np.random.choice(category_types))

df = pd.DataFrame({"lat": lats, "lon": lons, "category": categories})

# Apply hierarchical clustering with large threshold to create ONE cluster per city
# This eliminates overlap by having exactly 5 non-overlapping clusters
coords = df[["lat", "lon"]].values
Z = linkage(coords, method="ward")
cluster_labels = fcluster(Z, t=5, criterion="maxclust")  # Force exactly 5 clusters
df["cluster"] = cluster_labels

# Calculate cluster centers and counts
cluster_data = (
    df.groupby("cluster")
    .agg(
        lat=("lat", "mean"),
        lon=("lon", "mean"),
        count=("cluster", "size"),
        dominant_category=("category", lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.iloc[0]),
    )
    .reset_index()
)

# Prepare cluster markers for plotting
cluster_markers = cluster_data.copy()
cluster_markers = cluster_markers.rename(columns={"dominant_category": "category"})
cluster_markers["label"] = cluster_markers["count"].astype(str)

# Define colors for categories (colorblind-friendly palette)
category_colors = {
    "Retail": "#4477AA",  # Blue
    "Restaurant": "#EE6677",  # Red/pink
    "Service": "#228833",  # Green
    "Entertainment": "#CCBB44",  # Yellow
}

# Create the plot - single layer for clusters with unified legend
# Convert longitude to positive values for display (West Coast = positive °W)
cluster_markers["lon_display"] = -cluster_markers["lon"]

plot = (
    ggplot(cluster_markers, aes(x="lon_display", y="lat"))
    # Plot cluster markers with size and color
    + geom_point(aes(size="count", color="category"), alpha=0.85, stroke=1.5)
    # Add count labels on clusters - larger size for readability
    + geom_text(aes(label="label"), size=11, color="white", fontweight="bold")
    # Color scale - shows all categories
    + scale_color_manual(values=category_colors, name="Category")
    # Size scale for cluster markers - adjusted range and breaks for actual data
    + scale_size_continuous(range=(12, 22), name="Count", breaks=[40, 50, 60, 70, 80])
    # Labels with proper units
    + labs(title="map-marker-clustered · plotnine · pyplots.ai", x="Longitude (°W)", y="Latitude (°N)")
    # Theme
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        legend_position="right",
        legend_box="vertical",
        panel_grid_major=element_line(color="#cccccc", size=0.3),
        panel_grid_minor=element_line(color="#eeeeee", size=0.2),
        panel_background=element_rect(fill="#f8f8f8"),
        plot_background=element_rect(fill="white"),
    )
    + guides(
        color=guide_legend(override_aes={"size": 10, "alpha": 1}),
        size=guide_legend(override_aes={"color": "#666666", "alpha": 0.8}),
    )
)

# Save the plot
plot.save("plot.png", dpi=300, width=16, height=9, verbose=False)
