""" pyplots.ai
map-marker-clustered: Clustered Marker Map
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_rect,
    element_text,
    geom_point,
    geom_polygon,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_fill_manual,
    scale_size,
    theme,
    theme_void,
    xlim,
    ylim,
)


LetsPlot.setup_html()

np.random.seed(42)

# Data: Generate store locations across US regions
# West Coast cluster (around Los Angeles and San Francisco)
west_lon = np.concatenate(
    [
        np.random.normal(-118.2, 0.8, 80),  # LA area
        np.random.normal(-122.4, 0.6, 60),  # SF area
        np.random.normal(-121.9, 1.0, 40),  # Central CA
    ]
)
west_lat = np.concatenate(
    [np.random.normal(34.0, 0.6, 80), np.random.normal(37.8, 0.5, 60), np.random.normal(36.5, 0.8, 40)]
)

# East Coast cluster (around NYC, Boston, DC)
east_lon = np.concatenate(
    [
        np.random.normal(-74.0, 0.5, 90),  # NYC area
        np.random.normal(-71.1, 0.4, 50),  # Boston area
        np.random.normal(-77.0, 0.5, 60),  # DC area
    ]
)
east_lat = np.concatenate(
    [np.random.normal(40.7, 0.4, 90), np.random.normal(42.4, 0.3, 50), np.random.normal(38.9, 0.4, 60)]
)

# Midwest cluster (around Chicago)
midwest_lon = np.random.normal(-87.6, 1.2, 100)
midwest_lat = np.random.normal(41.9, 0.8, 100)

# Texas cluster (around Houston and Dallas)
texas_lon = np.concatenate(
    [
        np.random.normal(-95.4, 0.6, 60),  # Houston
        np.random.normal(-96.8, 0.5, 50),  # Dallas
    ]
)
texas_lat = np.concatenate([np.random.normal(29.8, 0.5, 60), np.random.normal(32.8, 0.4, 50)])

# Florida cluster
florida_lon = np.random.normal(-80.2, 0.8, 70)
florida_lat = np.random.normal(26.0, 0.6, 70)

# Combine all points
all_lon = np.concatenate([west_lon, east_lon, midwest_lon, texas_lon, florida_lon])
all_lat = np.concatenate([west_lat, east_lat, midwest_lat, texas_lat, florida_lat])

# Assign categories (store types)
n_total = len(all_lon)
categories = np.random.choice(["Retail", "Warehouse", "Service Center"], size=n_total, p=[0.5, 0.3, 0.2])

# Create dataframe of all individual points
df_points = pd.DataFrame({"lon": all_lon, "lat": all_lat, "category": categories})

# Grid-based clustering: assign points to grid cells (simulates zoom level)
grid_size = 5.0  # Degrees - larger grid to reduce overlaps
df_points["grid_lon"] = np.floor(df_points["lon"] / grid_size) * grid_size
df_points["grid_lat"] = np.floor(df_points["lat"] / grid_size) * grid_size
df_points["cluster"] = df_points["grid_lon"].astype(str) + "_" + df_points["grid_lat"].astype(str)

# Create cluster summary data
cluster_summary = (
    df_points.groupby("cluster")
    .agg(
        {
            "lon": "mean",
            "lat": "mean",
            "category": lambda x: x.mode().iloc[0],  # Dominant category
        }
    )
    .reset_index()
)

cluster_counts = df_points.groupby("cluster").size().reset_index(name="count")
df_clusters = cluster_summary.merge(cluster_counts, on="cluster")

# Separate single points (show individually) from clusters (count > 3 for visual clarity)
df_singles = df_clusters[df_clusters["count"] <= 3].copy()
df_multiples = df_clusters[df_clusters["count"] > 3].copy()


# Function to displace overlapping clusters
def displace_overlapping_clusters(df, min_distance=3.0):
    """Move clusters that are too close to each other to prevent overlap."""
    coords = df[["lon", "lat"]].values.copy()
    n = len(coords)
    for _ in range(5):  # Multiple passes
        for i in range(n):
            for j in range(i + 1, n):
                dist = np.sqrt((coords[i, 0] - coords[j, 0]) ** 2 + (coords[i, 1] - coords[j, 1]) ** 2)
                if dist < min_distance and dist > 0:
                    # Calculate displacement vector
                    dx = coords[j, 0] - coords[i, 0]
                    dy = coords[j, 1] - coords[i, 1]
                    # Normalize and scale
                    scale = (min_distance - dist) / (2 * dist)
                    # Move both clusters apart
                    coords[i, 0] -= dx * scale
                    coords[i, 1] -= dy * scale
                    coords[j, 0] += dx * scale
                    coords[j, 1] += dy * scale
    df = df.copy()
    df["lon"] = coords[:, 0]
    df["lat"] = coords[:, 1]
    return df


# Apply displacement to prevent overlapping clusters
df_multiples = displace_overlapping_clusters(df_multiples, min_distance=4.0)

# Add region labels for tooltips
df_multiples["region"] = df_multiples.apply(
    lambda r: (
        "West Coast"
        if r["lon"] < -110
        else (
            "Midwest"
            if -100 < r["lon"] < -80 and r["lat"] > 38
            else (
                "Texas"
                if r["lat"] < 35 and -100 < r["lon"] < -90
                else ("Florida" if r["lon"] > -85 and r["lat"] < 30 else "East Coast")
            )
        )
    ),
    axis=1,
)

# Simplified US boundary polygon
us_coords = [
    (-125, 49),
    (-120, 49),
    (-115, 49),
    (-110, 49),
    (-105, 49),
    (-100, 49),
    (-95, 49),
    (-90, 47),
    (-85, 46),
    (-82, 46),
    (-82, 42),
    (-79, 43),
    (-76, 44),
    (-70, 45),
    (-67, 45),
    (-67, 44),
    (-70, 41),
    (-74, 40),
    (-75, 39),
    (-76, 37),
    (-76, 35),
    (-80, 32),
    (-81, 31),
    (-81, 25),
    (-80, 25),
    (-82, 28),
    (-84, 30),
    (-88, 30),
    (-89, 29),
    (-94, 29),
    (-97, 26),
    (-97, 28),
    (-100, 29),
    (-104, 29),
    (-106, 32),
    (-109, 31),
    (-111, 31),
    (-114, 32),
    (-117, 32),
    (-120, 34),
    (-123, 37),
    (-124, 40),
    (-124, 43),
    (-123, 46),
    (-124, 48),
    (-125, 49),
]

df_us = pd.DataFrame(us_coords, columns=["x", "y"])
df_us["group"] = 0

# Color palette for categories
colors = {"Retail": "#306998", "Warehouse": "#FFD43B", "Service Center": "#DC2626"}

# Create the plot with interactive tooltips
plot = (
    ggplot()
    # US background
    + geom_polygon(data=df_us, mapping=aes(x="x", y="y", group="group"), fill="#E8E8E8", color="#AAAAAA", size=0.5)
    # Cluster markers (larger circles with count) - with tooltips
    + geom_point(
        data=df_multiples,
        mapping=aes(x="lon", y="lat", size="count", fill="category"),
        color="#333333",
        alpha=0.85,
        shape=21,
        stroke=1.5,
        tooltips=layer_tooltips()
        .title("@region Cluster")
        .line("@count locations")
        .line("Type|@category")
        .line("Click to explore"),
    )
    # Cluster count labels
    + geom_text(
        data=df_multiples, mapping=aes(x="lon", y="lat", label="count"), color="#FFFFFF", size=10, fontface="bold"
    )
    # Individual markers (single locations) - with tooltips
    + geom_point(
        data=df_singles,
        mapping=aes(x="lon", y="lat", fill="category"),
        color="#333333",
        size=5,
        alpha=0.9,
        shape=21,
        stroke=1.0,
        tooltips=layer_tooltips().title("Individual Location").line("Type|@category").line("@count location(s)"),
    )
    # Scales
    + scale_fill_manual(values=colors, name="Store Type")
    + scale_size(range=[10, 28], name="Locations", breaks=[10, 50, 100, 200])
    # Labels
    + labs(
        title="map-marker-clustered · letsplot · pyplots.ai",
        caption="Store locations clustered by proximity | Hover for details | 760 total locations",
    )
    # Theme
    + theme_void()
    + theme(
        plot_title=element_text(size=28, hjust=0.5, face="bold"),
        plot_caption=element_text(size=14, hjust=0.5, color="#666666"),
        legend_title=element_text(size=18),
        legend_text=element_text(size=14),
        legend_position="right",
        plot_background=element_rect(fill="#F5F5F5"),
    )
    # Size and limits
    + ggsize(1600, 900)
    + xlim(-130, -65)
    + ylim(23, 52)
)

# Save outputs
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
