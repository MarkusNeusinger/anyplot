""" pyplots.ai
area-elevation-profile: Terrain Elevation Profile Along Transect
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-15
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Seaborn theming and context for consistent styling
sns.set_theme(
    style="ticks",
    rc={"axes.facecolor": "#fafaf8", "figure.facecolor": "white", "grid.color": "#dddddd", "grid.linewidth": 0.8},
)
sns.set_context("talk", font_scale=1.1, rc={"lines.linewidth": 2.5})

# Data
np.random.seed(42)

total_distance = 120
n_points = 480
distance = np.linspace(0, total_distance, n_points)

base_profile = (
    800
    + 600 * np.sin(distance / total_distance * np.pi * 0.8)
    + 400 * np.sin(distance / total_distance * np.pi * 2.5 + 0.5)
    + 200 * np.sin(distance / total_distance * np.pi * 5 + 1.2)
    + 150 * np.cos(distance / total_distance * np.pi * 3.8)
)
noise = np.cumsum(np.random.normal(0, 2, n_points))
noise -= np.linspace(noise[0], noise[-1], n_points)
elevation = base_profile + noise
elevation = np.clip(elevation, 400, None)

df = pd.DataFrame({"distance_km": distance, "elevation_m": elevation})

landmarks = pd.DataFrame(
    {
        "name": ["Trailhead", "North Peak", "Lake Valley", "Ridge Pass", "River Crossing", "Summit", "End Station"],
        "distance_km": [0.0, 8.0, 28.0, 52.0, 75.0, 105.0, 120.0],
    }
)
landmark_elevations = []
for d in landmarks["distance_km"]:
    idx = np.argmin(np.abs(distance - d))
    landmark_elevations.append(elevation[idx])
landmarks["elevation_m"] = landmark_elevations

# Build gradient fill data using seaborn color palette
gradient_colors = sns.color_palette("blend:#a8c686,#5a8a3c,#306998", n_colors=40)
elev_min_val, elev_max_val = elevation.min(), elevation.max()
elev_range = elev_max_val - elev_min_val

# Segment the profile by elevation for gradient coloring
n_bands = len(gradient_colors)
segment_rows = []
for i in range(n_bands):
    frac = i / n_bands
    band_low = elev_min_val + frac * elev_range
    band_high = elev_min_val + (i + 1) / n_bands * elev_range
    segment_rows.append({"band": i, "frac": frac, "band_low": band_low, "band_high": band_high})
segments_df = pd.DataFrame(segment_rows)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Gradient terrain fill
y_min = elev_min_val - 0.05 * elev_range
for _, seg in segments_df.iterrows():
    clipped = np.clip(elevation, seg["band_low"], seg["band_high"])
    bottom = np.full_like(distance, seg["band_low"])
    ax.fill_between(distance, bottom, clipped, color=gradient_colors[int(seg["band"])], alpha=0.85, linewidth=0)
ax.fill_between(
    distance, y_min, np.full_like(distance, elev_min_val), color=gradient_colors[0], alpha=0.85, linewidth=0
)

# Profile line using seaborn lineplot
sns.lineplot(data=df, x="distance_km", y="elevation_m", ax=ax, color="#306998", linewidth=2.5, legend=False)

# Landmark markers using seaborn scatterplot
sns.scatterplot(
    data=landmarks,
    x="distance_km",
    y="elevation_m",
    ax=ax,
    color="#306998",
    s=120,
    edgecolor="white",
    linewidth=1.5,
    zorder=5,
    legend=False,
)

# Landmark annotations
for _, lm in landmarks.iterrows():
    ax.vlines(lm["distance_km"], y_min, lm["elevation_m"], color="#555555", linewidth=1, linestyle="--", alpha=0.5)
    label_text = f"{lm['name']}\n{int(lm['elevation_m'])} m"
    y_offset = 60 if lm["elevation_m"] < (elev_max_val - 200) else -120
    ax.annotate(
        label_text,
        xy=(lm["distance_km"], lm["elevation_m"]),
        xytext=(0, y_offset),
        textcoords="offset points",
        fontsize=13,
        fontweight="bold",
        color="#333333",
        ha="center",
        va="bottom" if y_offset > 0 else "top",
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.85},
    )

# Style using seaborn utilities
ax.set_xlabel("Distance (km)", fontsize=20)
ax.set_ylabel("Elevation (m)", fontsize=20)
ax.set_title("area-elevation-profile · seaborn · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
sns.despine(ax=ax)
ax.yaxis.grid(True, alpha=0.2)
ax.set_xlim(0, total_distance)
ax.set_ylim(bottom=y_min)

ax.text(
    0.98,
    0.02,
    "Vertical exaggeration ~10×",
    transform=ax.transAxes,
    fontsize=13,
    color="#888888",
    ha="right",
    va="bottom",
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
