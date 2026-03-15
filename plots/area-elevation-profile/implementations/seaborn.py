""" pyplots.ai
area-elevation-profile: Terrain Elevation Profile Along Transect
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 93/100 | Created: 2026-03-15
"""

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Seaborn theming and context
sns.set_theme(
    style="ticks",
    rc={
        "axes.facecolor": "#fafaf8",
        "figure.facecolor": "white",
        "grid.linestyle": "--",
        "grid.linewidth": 0.6,
        "grid.alpha": 0.3,
    },
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

# Gradient fill colors via seaborn palette blending
gradient_colors = sns.color_palette("blend:#a8c686,#5a8a3c,#306998", n_colors=40)
elev_min_val, elev_max_val = elevation.min(), elevation.max()
elev_range = elev_max_val - elev_min_val

# Classify terrain slope for coloring landmarks
slopes = np.gradient(elevation, distance)
landmark_slopes = []
for d in landmarks["distance_km"]:
    idx = np.argmin(np.abs(distance - d))
    landmark_slopes.append(abs(slopes[idx]))
landmarks["slope"] = landmark_slopes
slope_palette = sns.color_palette("YlOrRd", n_colors=5)
slope_max = max(landmark_slopes)
landmarks["slope_color"] = [slope_palette[min(int(s / slope_max * 4), 4)] for s in landmark_slopes]

# Plot: main profile + marginal elevation KDE
fig = plt.figure(figsize=(16, 9))
gs = gridspec.GridSpec(1, 2, width_ratios=[20, 1], wspace=0.02)
ax = fig.add_subplot(gs[0])
ax_kde = fig.add_subplot(gs[1], sharey=ax)

# Gradient terrain fill
y_min = elev_min_val - 0.05 * elev_range
n_bands = len(gradient_colors)
for i in range(n_bands):
    band_low = elev_min_val + i / n_bands * elev_range
    band_high = elev_min_val + (i + 1) / n_bands * elev_range
    clipped = np.clip(elevation, band_low, band_high)
    ax.fill_between(
        distance, np.full_like(distance, band_low), clipped, color=gradient_colors[i], alpha=0.85, linewidth=0
    )
ax.fill_between(
    distance, y_min, np.full_like(distance, elev_min_val), color=gradient_colors[0], alpha=0.85, linewidth=0
)

# Profile line via seaborn lineplot
sns.lineplot(data=df, x="distance_km", y="elevation_m", ax=ax, color="#306998", linewidth=2.5, legend=False)

# Landmark markers via seaborn scatterplot with hue mapped to slope
sns.scatterplot(
    data=landmarks,
    x="distance_km",
    y="elevation_m",
    hue="slope",
    palette="YlOrRd",
    ax=ax,
    s=140,
    edgecolor="white",
    linewidth=1.8,
    zorder=5,
    legend=False,
)

# Landmark annotations with smart positioning
for _, lm in landmarks.iterrows():
    ax.vlines(lm["distance_km"], y_min, lm["elevation_m"], color="#555555", linewidth=0.8, linestyle=":", alpha=0.5)
    label_text = f"{lm['name']}\n{int(lm['elevation_m'])} m"
    y_offset = 60 if lm["elevation_m"] < (elev_max_val - 200) else -120
    # Shift End Station annotation left to avoid right edge cramping
    x_offset = -40 if lm["distance_km"] >= total_distance - 1 else (55 if lm["distance_km"] <= 1 else 0)
    ha = "right" if lm["distance_km"] >= total_distance - 1 else ("left" if lm["distance_km"] <= 1 else "center")
    ax.annotate(
        label_text,
        xy=(lm["distance_km"], lm["elevation_m"]),
        xytext=(x_offset, y_offset),
        textcoords="offset points",
        fontsize=13,
        fontweight="bold",
        color="#333333",
        ha=ha,
        va="bottom" if y_offset > 0 else "top",
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.9},
        zorder=6,
    )

# Marginal KDE of elevation distribution (distinctively seaborn)
sns.kdeplot(y=df["elevation_m"], ax=ax_kde, fill=True, color="#306998", alpha=0.3, linewidth=1.5)
sns.rugplot(data=landmarks, y="elevation_m", ax=ax_kde, color="#306998", height=0.3, linewidth=2, alpha=0.7)
ax_kde.set_xlabel("")
ax_kde.set_ylabel("")
ax_kde.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)
ax_kde.set_facecolor("#fafaf8")
sns.despine(ax=ax_kde, left=True, bottom=True)

# Style main axes
ax.set_xlabel("Distance (km)", fontsize=20)
ax.set_ylabel("Elevation (m)", fontsize=20)
ax.set_title("area-elevation-profile · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=16)
ax.tick_params(axis="both", labelsize=16)
ax.yaxis.set_major_locator(plt.MultipleLocator(200))
ax.xaxis.set_major_locator(plt.MultipleLocator(20))
sns.despine(ax=ax)
ax.yaxis.grid(True)
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
    style="italic",
)

fig.subplots_adjust(left=0.07, right=0.97, top=0.93, bottom=0.09)
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
