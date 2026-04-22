""" pyplots.ai
map-connection-lines: Connection Lines Map (Origin-Destination)
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-21
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


# Data - Major international flight routes with passenger volume
np.random.seed(42)

# Major airports: (name, lat, lon, label_offset_x, label_offset_y)
# Custom offsets to avoid label overlaps
airports = [
    ("New York", 40.6413, -73.7781, 4, 4),
    ("London", 51.4700, -0.4543, 4, 6),
    ("Tokyo", 35.5494, 139.7798, -4, 4),
    ("Dubai", 25.2532, 55.3657, 4, 4),
    ("Singapore", 1.3644, 103.9915, 4, -8),
    ("Sydney", -33.9399, 151.1753, 4, 4),
    ("São Paulo", -23.4356, -46.4731, 4, 4),
    ("Los Angeles", 33.9416, -118.4085, -4, 4),
    ("Paris", 49.0097, 2.5479, 4, -10),
    ("Hong Kong", 22.3080, 113.9185, -4, -8),
]

# Define connections: (origin_idx, dest_idx, passenger_volume in millions)
connections = [
    (0, 1, 4.2),  # NYC - London (busiest transatlantic)
    (0, 8, 2.1),  # NYC - Paris
    (1, 3, 3.5),  # London - Dubai
    (1, 9, 2.8),  # London - Hong Kong
    (3, 4, 3.2),  # Dubai - Singapore
    (4, 5, 2.4),  # Singapore - Sydney
    (4, 9, 2.9),  # Singapore - Hong Kong
    (2, 9, 3.1),  # Tokyo - Hong Kong
    (2, 7, 2.2),  # Tokyo - LA
    (0, 7, 2.5),  # NYC - LA (domestic but major)
    (6, 0, 1.8),  # São Paulo - NYC
    (6, 1, 1.5),  # São Paulo - London
    (5, 4, 1.9),  # Sydney - Singapore
    (3, 9, 2.6),  # Dubai - Hong Kong
    (7, 2, 2.0),  # LA - Tokyo
]

# Extract coordinates and values
routes = []
for orig_idx, dest_idx, volume in connections:
    orig = airports[orig_idx]
    dest = airports[dest_idx]
    routes.append(
        {
            "origin_name": orig[0],
            "origin_lat": orig[1],
            "origin_lon": orig[2],
            "dest_name": dest[0],
            "dest_lat": dest[1],
            "dest_lon": dest[2],
            "volume": volume,
        }
    )

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Simple world map outline using pre-defined coastline coordinates
# Create a simplified world map background
ax.set_xlim(-180, 180)
ax.set_ylim(-90, 90)
ax.set_facecolor("#D4E5F7")  # Ocean color

# Draw simple continent rectangles as background (approximation)
continents = [
    # North America
    [(-170, 15), (-170, 75), (-50, 75), (-50, 15)],
    # South America
    [(-85, -60), (-85, 15), (-35, 15), (-35, -60)],
    # Europe
    [(-10, 35), (-10, 72), (40, 72), (40, 35)],
    # Africa
    [(-20, -35), (-20, 38), (55, 38), (55, -35)],
    # Asia
    [(40, 5), (40, 80), (180, 80), (180, 5)],
    # Australia
    [(110, -45), (110, -10), (155, -10), (155, -45)],
]

for cont in continents:
    xs = [p[0] for p in cont] + [cont[0][0]]
    ys = [p[1] for p in cont] + [cont[0][1]]
    ax.fill(xs, ys, color="#E8E8E8", alpha=0.7)

# Normalize volumes for line width scaling
volumes = [r["volume"] for r in routes]
min_vol, max_vol = min(volumes), max(volumes)

# Draw connection lines using geodesic paths (inlined great circle calculation)
n_points = 100
for route in routes:
    # Calculate normalized volume for styling
    norm_vol = (route["volume"] - min_vol) / (max_vol - min_vol)
    linewidth = 2 + norm_vol * 5  # Scale from 2 to 7
    alpha = 0.4 + norm_vol * 0.35  # Scale from 0.4 to 0.75

    # Calculate great circle path using spherical interpolation
    lon1, lat1 = route["origin_lon"], route["origin_lat"]
    lon2, lat2 = route["dest_lon"], route["dest_lat"]
    lon1_r, lat1_r = np.radians(lon1), np.radians(lat1)
    lon2_r, lat2_r = np.radians(lon2), np.radians(lat2)

    # Angular distance
    d = np.arccos(np.sin(lat1_r) * np.sin(lat2_r) + np.cos(lat1_r) * np.cos(lat2_r) * np.cos(lon2_r - lon1_r))

    # Handle very short distances
    if d < 1e-10:
        lons, lats = np.array([lon1, lon2]), np.array([lat1, lat2])
    else:
        # Interpolate along great circle
        t = np.linspace(0, 1, n_points)
        a = np.sin((1 - t) * d) / np.sin(d)
        b = np.sin(t * d) / np.sin(d)
        x = a * np.cos(lat1_r) * np.cos(lon1_r) + b * np.cos(lat2_r) * np.cos(lon2_r)
        y = a * np.cos(lat1_r) * np.sin(lon1_r) + b * np.cos(lat2_r) * np.sin(lon2_r)
        z = a * np.sin(lat1_r) + b * np.sin(lat2_r)
        lats = np.degrees(np.arctan2(z, np.sqrt(x**2 + y**2)))
        lons = np.degrees(np.arctan2(y, x))

    # Handle date line crossing by splitting the line
    lon_diff = np.abs(np.diff(lons))
    if np.any(lon_diff > 180):
        # Split the line at date line crossing
        split_idx = np.where(lon_diff > 180)[0][0] + 1
        ax.plot(
            lons[:split_idx],
            lats[:split_idx],
            color="#306998",
            linewidth=linewidth,
            alpha=alpha,
            solid_capstyle="round",
            zorder=2,
        )
        ax.plot(
            lons[split_idx:],
            lats[split_idx:],
            color="#306998",
            linewidth=linewidth,
            alpha=alpha,
            solid_capstyle="round",
            zorder=2,
        )
    else:
        ax.plot(lons, lats, color="#306998", linewidth=linewidth, alpha=alpha, solid_capstyle="round", zorder=2)

# Draw airport markers
for _name, lat, lon, _offset_x, _offset_y in airports:
    ax.plot(
        lon, lat, marker="o", markersize=14, color="#FFD43B", markeredgecolor="#306998", markeredgewidth=2.5, zorder=3
    )

# Draw airport labels with custom offsets to avoid overlap
for name, lat, lon, offset_x, offset_y in airports:
    ax.annotate(
        name,
        (lon, lat),
        xytext=(offset_x, offset_y),
        textcoords="offset points",
        fontsize=14,
        fontweight="bold",
        color="#333333",
        ha="left" if offset_x > 0 else "right",
        va="bottom" if offset_y > 0 else "top",
        zorder=4,
    )

# Styling
ax.set_xlabel("Longitude (°)", fontsize=20)
ax.set_ylabel("Latitude (°)", fontsize=20)
ax.tick_params(axis="both", labelsize=16)
ax.set_aspect("equal", adjustable="box")

# Add grid
ax.grid(True, alpha=0.3, linestyle="--", color="#666666")

# Title
ax.set_title(
    "Major International Flight Routes · map-connection-lines · matplotlib · pyplots.ai",
    fontsize=24,
    fontweight="bold",
    pad=20,
)

# Legend for line thickness
legend_elements = [
    Line2D([0], [0], color="#306998", linewidth=2, alpha=0.4, label="1.5M passengers/year"),
    Line2D([0], [0], color="#306998", linewidth=4.5, alpha=0.57, label="3M passengers/year"),
    Line2D([0], [0], color="#306998", linewidth=7, alpha=0.75, label="4.2M passengers/year"),
    Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor="#FFD43B",
        markeredgecolor="#306998",
        markeredgewidth=2.5,
        markersize=12,
        label="Major Airport",
    ),
]
ax.legend(handles=legend_elements, loc="lower left", fontsize=16, framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
