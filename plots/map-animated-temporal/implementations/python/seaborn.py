""" pyplots.ai
map-animated-temporal: Animated Map over Time
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-20
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Set style
sns.set_context("talk", font_scale=1.2)
sns.set_style("whitegrid")

# Generate synthetic earthquake aftershock data over 6 time periods
np.random.seed(42)

# Simulate aftershock sequence spreading from epicenter (California region)
epicenter_lat, epicenter_lon = 35.0, -120.0
n_points_per_period = 15
n_periods = 6

data_records = []
for period in range(n_periods):
    # Spread increases over time (aftershocks diffuse outward)
    spread = 0.5 + period * 0.3
    n_points = n_points_per_period + period * 3

    lats = epicenter_lat + np.random.randn(n_points) * spread
    lons = epicenter_lon + np.random.randn(n_points) * spread
    # Magnitude decreases over time on average
    magnitudes = np.random.uniform(2.0, 5.5 - period * 0.4, n_points)

    for i in range(n_points):
        data_records.append(
            {
                "lat": lats[i],
                "lon": lons[i],
                "magnitude": magnitudes[i],
                "period": f"Day {period + 1}",
                "period_num": period,
            }
        )

df = pd.DataFrame(data_records)

# Define California coastline approximation for geographic context
# Simplified coordinates from north to south
ca_coast_lons = [-124.2, -123.8, -122.5, -121.9, -121.5, -120.6, -120.2, -119.5, -118.5, -117.2, -117.0]
ca_coast_lats = [41.5, 39.8, 38.0, 36.8, 36.2, 35.5, 34.5, 34.4, 34.0, 33.0, 32.5]

# Create small multiples grid showing temporal snapshots
fig, axes = plt.subplots(2, 3, figsize=(16, 9))
axes = axes.flatten()

for idx, period in enumerate(sorted(df["period"].unique(), key=lambda x: int(x.split()[1]))):
    ax = axes[idx]
    period_data = df[df["period"] == period].copy()

    # Draw simplified coastline for geographic context (before plotting data)
    ax.plot(ca_coast_lons, ca_coast_lats, color="#8B7355", linewidth=2, alpha=0.7, zorder=1)
    ax.fill_betweenx([32, 42], -125, ca_coast_lons[0], color="#A8D5E2", alpha=0.3, zorder=0)  # Ocean hint

    # Use seaborn scatterplot for aftershocks
    sns.scatterplot(
        data=period_data,
        x="lon",
        y="lat",
        size="magnitude",
        sizes=(50, 500),
        hue="magnitude",
        palette="viridis",
        alpha=0.7,
        edgecolor="black",
        linewidth=0.5,
        hue_norm=(2.0, 5.5),
        ax=ax,
        legend=False,
    )

    # Mark epicenter with distinctive star
    ax.scatter(
        epicenter_lon, epicenter_lat, marker="*", s=500, c="#E63946", edgecolors="white", linewidths=2, zorder=10
    )

    # Set consistent axis limits for all panels
    ax.set_xlim(epicenter_lon - 4, epicenter_lon + 4)
    ax.set_ylim(epicenter_lat - 4, epicenter_lat + 4)

    # Style each subplot
    ax.set_title(period, fontsize=20, fontweight="bold")
    ax.set_xlabel("Longitude (\u00b0W)" if idx >= 3 else "", fontsize=16)
    ax.set_ylabel("Latitude (\u00b0N)" if idx % 3 == 0 else "", fontsize=16)
    ax.tick_params(axis="both", labelsize=14)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3, linestyle="--")

# Create a ScalarMappable for the colorbar
norm = plt.Normalize(vmin=2.0, vmax=5.5)
sm = plt.cm.ScalarMappable(cmap="viridis", norm=norm)
sm.set_array([])

# Add shared colorbar
cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
cbar = fig.colorbar(sm, cax=cbar_ax)
cbar.set_label("Magnitude", fontsize=18)
cbar.ax.tick_params(labelsize=14)

# Create legend for epicenter and coastline
epicenter_marker = plt.Line2D(
    [0],
    [0],
    marker="*",
    color="w",
    markerfacecolor="#E63946",
    markeredgecolor="white",
    markersize=20,
    linestyle="None",
    label="Epicenter",
)
coast_line = plt.Line2D([0], [0], color="#8B7355", linewidth=2, label="Coastline")

fig.legend(
    handles=[epicenter_marker, coast_line], loc="lower right", bbox_to_anchor=(0.88, 0.02), fontsize=14, framealpha=0.9
)

# Overall title
fig.suptitle("map-animated-temporal \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="bold", y=0.98)

fig.subplots_adjust(left=0.07, right=0.88, top=0.90, bottom=0.08, wspace=0.25, hspace=0.3)
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
