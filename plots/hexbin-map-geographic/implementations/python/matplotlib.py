""" pyplots.ai
hexbin-map-geographic: Hexagonal Binning Map
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-20
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle


# Data: Simulated taxi pickup locations in New York City area
np.random.seed(42)
n_points = 5000

# Generate clustered points around Manhattan, Brooklyn, and Queens
n_manhattan = 2500
n_brooklyn = 1500
n_queens = 1000

# Manhattan cluster (denser, central)
lat_manhattan = np.random.normal(40.758, 0.03, n_manhattan)
lon_manhattan = np.random.normal(-73.985, 0.015, n_manhattan)

# Brooklyn cluster
lat_brooklyn = np.random.normal(40.68, 0.04, n_brooklyn)
lon_brooklyn = np.random.normal(-73.96, 0.03, n_brooklyn)

# Queens cluster
lat_queens = np.random.normal(40.73, 0.03, n_queens)
lon_queens = np.random.normal(-73.85, 0.04, n_queens)

# Combine all points
lat = np.concatenate([lat_manhattan, lat_brooklyn, lat_queens])
lon = np.concatenate([lon_manhattan, lon_brooklyn, lon_queens])

# Optional value for aggregation (trip fare amounts in dollars)
values = np.random.exponential(15, n_points) + 5

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Set background color to represent water/land context
ax.set_facecolor("#e8f4f8")

# Add a light rectangle to suggest land area
land = Rectangle((-74.05, 40.58), 0.35, 0.32, linewidth=0, facecolor="#f5f5f2", zorder=0)
ax.add_patch(land)

# Hexbin plot showing density with mean fare values
hb = ax.hexbin(
    lon,
    lat,
    C=values,
    gridsize=35,
    reduce_C_function=np.mean,
    cmap="YlOrRd",
    alpha=0.85,
    edgecolors="#555555",
    linewidths=0.4,
    mincnt=1,
    zorder=2,
)

# Colorbar
cbar = plt.colorbar(hb, ax=ax, shrink=0.85, pad=0.02, aspect=30)
cbar.set_label("Mean Trip Fare ($)", fontsize=18, labelpad=10)
cbar.ax.tick_params(labelsize=14)

# Set axis limits to NYC area
ax.set_xlim(-74.05, -73.70)
ax.set_ylim(40.58, 40.90)

# Labels and title
ax.set_xlabel("Longitude", fontsize=20)
ax.set_ylabel("Latitude", fontsize=20)
ax.set_title("hexbin-map-geographic · matplotlib · pyplots.ai", fontsize=24, pad=15)
ax.tick_params(axis="both", labelsize=14)

# Add geographic grid
ax.grid(True, alpha=0.4, linestyle="--", color="#888888", zorder=1)

# Add geographic context annotations
locations = [(-73.985, 40.758, "Manhattan"), (-73.96, 40.68, "Brooklyn"), (-73.85, 40.73, "Queens")]
for x, y, name in locations:
    ax.annotate(
        name,
        xy=(x, y),
        xytext=(x + 0.02, y + 0.03),
        fontsize=14,
        fontweight="bold",
        color="#333333",
        ha="left",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7, edgecolor="#cccccc"),
        zorder=5,
    )

# Add context text
ax.text(
    0.02,
    0.02,
    "NYC Taxi Pickup Density\n5,000 simulated points\nHexagonal binning with mean fare",
    transform=ax.transAxes,
    fontsize=12,
    verticalalignment="bottom",
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.85, edgecolor="#cccccc"),
    zorder=5,
)

# Format tick labels to show proper coordinate notation
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{abs(x):.2f}°W"))
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, p: f"{y:.2f}°N"))

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
