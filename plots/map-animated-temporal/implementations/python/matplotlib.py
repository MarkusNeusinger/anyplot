""" pyplots.ai
map-animated-temporal: Animated Map over Time
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.animation import FuncAnimation


# Data: Weather station temperature anomalies spreading across Europe over 12 months
np.random.seed(42)

# European weather station locations (lat, lon, station_name)
stations = [
    (48.86, 2.35, "Paris"),
    (51.51, -0.13, "London"),
    (52.52, 13.40, "Berlin"),
    (41.90, 12.50, "Rome"),
    (40.42, -3.70, "Madrid"),
    (59.33, 18.07, "Stockholm"),
    (60.17, 24.94, "Helsinki"),
    (55.68, 12.57, "Copenhagen"),
    (52.37, 4.90, "Amsterdam"),
    (50.85, 4.35, "Brussels"),
    (48.21, 16.37, "Vienna"),
    (47.50, 19.04, "Budapest"),
    (50.08, 14.44, "Prague"),
    (52.23, 21.01, "Warsaw"),
    (38.72, -9.14, "Lisbon"),
    (45.46, 9.19, "Milan"),
    (43.30, 5.37, "Marseille"),
    (53.55, 9.99, "Hamburg"),
    (48.14, 11.58, "Munich"),
    (45.44, 12.32, "Venice"),
    (41.39, 2.17, "Barcelona"),
    (37.98, 23.73, "Athens"),
    (44.43, 26.10, "Bucharest"),
    (42.70, 23.32, "Sofia"),
    (46.95, 7.45, "Bern"),
]

n_stations = len(stations)
n_months = 12
months = pd.date_range("2025-01-01", periods=n_months, freq="ME")
month_names = [m.strftime("%B %Y") for m in months]

# Generate temperature anomaly data that shows a warming pattern spreading from south to north
lats = np.array([s[0] for s in stations])
lons = np.array([s[1] for s in stations])
names = [s[2] for s in stations]

# Create temporal pattern: warming intensifies over time, starts in south
anomalies = np.zeros((n_months, n_stations))
for t in range(n_months):
    base_anomaly = 0.5 + t * 0.15  # Increasing baseline
    lat_effect = (50 - lats) * 0.03  # Southern stations warm faster
    time_lag = np.maximum(0, (t - (lats - 35) / 5)) * 0.1  # Warming spreads north
    noise = np.random.normal(0, 0.3, n_stations)
    anomalies[t] = base_anomaly + lat_effect + time_lag + noise

# Simplified Europe coastline
europe_coastline = [
    # Iberian Peninsula
    [(-10, 36), (-6, 37), (-2, 36), (3, 43), (0, 44), (-2, 43), (-8, 44), (-9, 42), (-10, 36)],
    # UK
    [(-6, 50), (-5, 54), (-4, 58), (-8, 58), (-6, 55), (-6, 50)],
    # European mainland
    [
        (-5, 43),
        (0, 43),
        (3, 43),
        (6, 44),
        (8, 44),
        (12, 46),
        (14, 45),
        (14, 41),
        (16, 40),
        (20, 40),
        (24, 37),
        (26, 38),
        (28, 41),
        (30, 42),
        (32, 42),
        (28, 56),
        (24, 55),
        (22, 56),
        (19, 55),
        (14, 54),
        (12, 56),
        (10, 56),
        (10, 54),
        (5, 54),
        (3, 51),
        (4, 51),
        (5, 49),
        (8, 48),
        (10, 47),
        (12, 44),
        (10, 47),
        (8, 48),
        (5, 49),
        (4, 51),
        (3, 51),
        (2, 50),
        (-2, 50),
        (-5, 48),
        (-5, 43),
    ],
    # Scandinavia
    [
        (5, 58),
        (10, 62),
        (12, 65),
        (20, 70),
        (28, 70),
        (30, 60),
        (24, 55),
        (22, 56),
        (19, 55),
        (14, 54),
        (12, 56),
        (10, 56),
        (5, 58),
    ],
    # Italy
    [(8, 44), (12, 46), (14, 45), (16, 38), (15, 37), (12, 38), (10, 42), (8, 44)],
    # Greece
    [(20, 40), (24, 37), (26, 38), (28, 41), (24, 40), (20, 40)],
]

# Color scale: blue (cold anomaly) to red (warm anomaly)
vmin, vmax = -1.0, 3.5

# Create figure with space for colorbar
fig, ax = plt.subplots(figsize=(16, 9))

# Set up the initial plot elements that won't change
ax.set_facecolor("#C8DDF0")

# Draw Europe coastline (static elements)
for coastline in europe_coastline:
    poly = plt.Polygon(coastline, facecolor="#E8E4D8", edgecolor="#888888", linewidth=0.8, zorder=1)
    ax.add_patch(poly)

# Add graticule (static)
for lat in range(35, 75, 10):
    ax.axhline(y=lat, color="#AAAAAA", linewidth=0.4, linestyle=":", alpha=0.5, zorder=0)
for lon in range(-10, 35, 10):
    ax.axvline(x=lon, color="#AAAAAA", linewidth=0.4, linestyle=":", alpha=0.5, zorder=0)

# Set axis limits
ax.set_xlim(-15, 35)
ax.set_ylim(33, 72)

# Labels and title (static)
ax.set_xlabel("Longitude (°)", fontsize=20)
ax.set_ylabel("Latitude (°)", fontsize=20)
ax.set_title("map-animated-temporal · matplotlib · pyplots.ai", fontsize=24, fontweight="bold", pad=15)
ax.tick_params(axis="both", labelsize=16)

# Initial scatter plot (will be updated)
initial_sizes = 150 + np.abs(anomalies[0]) * 100
scatter = ax.scatter(
    lons,
    lats,
    c=anomalies[0],
    s=initial_sizes,
    cmap="RdBu_r",
    vmin=vmin,
    vmax=vmax,
    alpha=0.85,
    edgecolors="white",
    linewidths=2,
    zorder=5,
)

# Add colorbar (once, not in animation)
cbar = fig.colorbar(scatter, ax=ax, shrink=0.7, pad=0.02)
cbar.set_label("Temperature Anomaly (°C)", fontsize=16)
cbar.ax.tick_params(labelsize=14)

# Month indicator text (will be updated)
month_text = ax.text(
    0.98,
    0.02,
    month_names[0],
    transform=ax.transAxes,
    fontsize=36,
    fontweight="bold",
    ha="right",
    va="bottom",
    color="#306998",
    alpha=0.6,
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "none", "alpha": 0.8},
)

plt.tight_layout()


def animate(frame):
    # Update scatter plot data
    current_anomalies = anomalies[frame]
    sizes = 150 + np.abs(current_anomalies) * 100

    scatter.set_array(current_anomalies)
    scatter.set_sizes(sizes)

    # Update month text
    month_text.set_text(month_names[frame])

    return scatter, month_text


# Create animation
anim = FuncAnimation(fig, animate, frames=n_months, interval=800, repeat=True, blit=True)

# Save as animated GIF
anim.save("plot.gif", writer="pillow", fps=2, dpi=169)

# Save final frame as PNG
animate(n_months - 1)
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
