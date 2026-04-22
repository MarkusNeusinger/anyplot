""" pyplots.ai
map-projections: World Map with Different Projections
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import numpy as np


# Define projections to compare
projections = [
    ("Mercator", ccrs.Mercator()),
    ("Robinson", ccrs.Robinson()),
    ("Mollweide", ccrs.Mollweide()),
    ("Orthographic", ccrs.Orthographic(central_longitude=0, central_latitude=30)),
]

# Create figure with 2x2 subplots
fig, axes = plt.subplots(2, 2, figsize=(16, 9), subplot_kw={"projection": ccrs.PlateCarree()})
axes = axes.flatten()

# Color scheme
land_color = "#E8E4D9"
ocean_color = "#A8D5E5"
border_color = "#4A4A4A"
graticule_color = "#888888"

# Create each map projection
for ax, (name, proj) in zip(axes, projections, strict=True):
    # Clear default projection and set the specific one
    ax.remove()
    ax = fig.add_subplot(2, 2, projections.index((name, proj)) + 1, projection=proj)
    axes[projections.index((name, proj))] = ax

    # Set global extent where possible
    try:
        ax.set_global()
    except Exception:
        pass

    # Add ocean and land features
    ax.add_feature(cfeature.OCEAN, facecolor=ocean_color, zorder=0)
    ax.add_feature(cfeature.LAND, facecolor=land_color, zorder=1)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor=border_color, zorder=2)
    ax.add_feature(cfeature.BORDERS, linewidth=0.4, edgecolor=border_color, alpha=0.5, zorder=2)

    # Add graticule (latitude/longitude grid lines)
    gl = ax.gridlines(draw_labels=False, linewidth=0.5, color=graticule_color, alpha=0.5, linestyle="--")
    gl.xlocator = plt.FixedLocator(np.arange(-180, 181, 30))
    gl.ylocator = plt.FixedLocator(np.arange(-90, 91, 30))

    # Add Tissot indicatrices to show distortion
    # Draw circles at regular intervals to visualize how the projection distorts area/shape
    tissot_lons = np.arange(-150, 180, 60)
    tissot_lats = np.arange(-60, 90, 30)

    for lon in tissot_lons:
        for lat in tissot_lats:
            try:
                ax.tissot(
                    rad_km=500,
                    lons=lon,
                    lats=lat,
                    n_samples=64,
                    facecolor="#FF6B6B",
                    edgecolor="#D63031",
                    alpha=0.4,
                    linewidth=1,
                    zorder=3,
                )
            except Exception:
                # Some projections may not support tissot at certain locations
                pass

    # Set title for each projection
    ax.set_title(name, fontsize=18, fontweight="bold", pad=10)

# Main title
fig.suptitle("map-projections · matplotlib · pyplots.ai", fontsize=24, fontweight="bold", y=0.98)

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
