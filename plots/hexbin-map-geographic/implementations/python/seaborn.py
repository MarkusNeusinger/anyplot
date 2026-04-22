""" pyplots.ai
hexbin-map-geographic: Hexagonal Binning Map
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Set seaborn style for consistent aesthetics
sns.set_theme(style="whitegrid")

# Data: Simulated taxi pickup locations in New York City area
np.random.seed(42)
n_points = 5000

# NYC bounding box approximately
center_lon, center_lat = -73.98, 40.75
lon = np.random.normal(center_lon, 0.08, n_points)
lat = np.random.normal(center_lat, 0.05, n_points)

# Add clustering for realistic density patterns
# Manhattan cluster (higher density)
mask1 = np.random.random(n_points) < 0.4
lon[mask1] = np.random.normal(-73.97, 0.015, np.sum(mask1))
lat[mask1] = np.random.normal(40.78, 0.015, np.sum(mask1))

# Downtown/Financial District cluster
mask2 = np.random.random(n_points) < 0.2
lon[mask2] = np.random.normal(-74.01, 0.01, np.sum(mask2))
lat[mask2] = np.random.normal(40.71, 0.012, np.sum(mask2))

# Brooklyn cluster
mask3 = np.random.random(n_points) < 0.15
lon[mask3] = np.random.normal(-73.95, 0.025, np.sum(mask3))
lat[mask3] = np.random.normal(40.68, 0.018, np.sum(mask3))

# Create DataFrame for seaborn
df = pd.DataFrame({"longitude": lon, "latitude": lat})

# Create figure with seaborn jointplot for hexbin visualization
# This is seaborn's idiomatic approach for 2D density/hexbin plots
g = sns.jointplot(
    data=df,
    x="longitude",
    y="latitude",
    kind="hex",
    cmap="YlOrRd",
    mincnt=1,
    gridsize=30,
    marginal_kws={"bins": 40, "color": "#e34a33", "edgecolor": "white"},
    joint_kws={"alpha": 0.85, "edgecolors": "white", "linewidths": 0.3},
    height=12,
    ratio=8,
)

# Get the main axes
ax = g.ax_joint

# Add simplified base map overlay - coastline/water boundary approximation for NYC
# Hudson River / East River simplified boundary
water_coords = [
    # Hudson River west boundary
    [(-74.02, 40.88), (-74.02, 40.70), (-74.05, 40.68), (-74.05, 40.60)],
    # East River / Upper Bay
    [(-74.02, 40.70), (-74.00, 40.68), (-73.98, 40.69), (-73.97, 40.70)],
    # Long Island Sound boundary
    [(-73.85, 40.82), (-73.80, 40.78), (-73.78, 40.75)],
]

for coords in water_coords:
    xs, ys = zip(*coords, strict=True)
    ax.plot(xs, ys, color="#4a90d9", linewidth=2.5, alpha=0.7, solid_capstyle="round")

# Add land boundary patches for geographic context
# Manhattan island approximate outline
manhattan_outline = mpatches.FancyBboxPatch(
    (-74.02, 40.70),
    0.07,
    0.15,
    boxstyle="round,pad=0.01",
    facecolor="none",
    edgecolor="#2d5016",
    linewidth=1.5,
    alpha=0.5,
)
ax.add_patch(manhattan_outline)

# Brooklyn approximate outline
brooklyn_outline = mpatches.FancyBboxPatch(
    (-74.01, 40.62),
    0.12,
    0.08,
    boxstyle="round,pad=0.01",
    facecolor="none",
    edgecolor="#2d5016",
    linewidth=1.5,
    alpha=0.5,
)
ax.add_patch(brooklyn_outline)

# Add geographic annotations for context
ax.annotate(
    "Manhattan", xy=(-73.97, 40.82), fontsize=14, color="#1a3d0c", ha="center", fontweight="bold", fontstyle="italic"
)
ax.annotate(
    "Brooklyn", xy=(-73.95, 40.60), fontsize=14, color="#1a3d0c", ha="center", fontweight="bold", fontstyle="italic"
)
ax.annotate(
    "Hudson\nRiver", xy=(-74.04, 40.76), fontsize=11, color="#2b6dad", ha="center", fontweight="bold", alpha=0.8
)

# Styling - axis labels with units (degree symbols)
ax.set_xlabel("Longitude (°W)", fontsize=20)
ax.set_ylabel("Latitude (°N)", fontsize=20)
ax.tick_params(axis="both", labelsize=16)

# Set axis limits to focus on data area with padding
lon_margin = (lon.max() - lon.min()) * 0.12
lat_margin = (lat.max() - lat.min()) * 0.12
ax.set_xlim(lon.min() - lon_margin, lon.max() + lon_margin)
ax.set_ylim(lat.min() - lat_margin, lat.max() + lat_margin)

# Add colorbar to main plot
cbar = plt.colorbar(ax.collections[0], ax=ax, shrink=0.7, pad=0.02, aspect=25)
cbar.set_label("Pickup Count", fontsize=18, labelpad=10)
cbar.ax.tick_params(labelsize=16)

# Title with required format (on figure to span full width)
g.figure.suptitle("NYC Taxi Pickups · hexbin-map-geographic · seaborn · pyplots.ai", fontsize=24, y=0.98)

# Set background color to light blue for water indication
ax.set_facecolor("#e8f4f8")

plt.tight_layout()
plt.subplots_adjust(top=0.94)
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
