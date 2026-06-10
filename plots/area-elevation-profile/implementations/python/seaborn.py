"""anyplot.ai
area-elevation-profile: Terrain Elevation Profile Along Transect
Library: seaborn | Python 3.14
Quality: 93/100 | Updated: 2026-06-10
"""

import os

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — first categorical series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential cmap for continuous terrain fill and slope-coded markers
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.15,
        "grid.linestyle": "-",
        "grid.linewidth": 0.5,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

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

slopes = np.gradient(elevation, distance)
landmark_slopes = []
for d in landmarks["distance_km"]:
    idx = np.argmin(np.abs(distance - d))
    landmark_slopes.append(abs(slopes[idx]))
landmarks["slope"] = landmark_slopes
slope_max = max(landmark_slopes)

# Figure layout: main profile + marginal elevation KDE strip
fig = plt.figure(figsize=(8, 4.5), dpi=400)
gs = gridspec.GridSpec(1, 2, width_ratios=[20, 1], wspace=0.02)
ax = fig.add_subplot(gs[0])
ax_kde = fig.add_subplot(gs[1], sharey=ax)

# Gradient terrain fill — Imprint sequential cmap (green→blue, low→high elevation)
elev_min_val, elev_max_val = elevation.min(), elevation.max()
elev_range = elev_max_val - elev_min_val
y_min = elev_min_val - 0.05 * elev_range
n_bands = 40
for i in range(n_bands):
    band_low = elev_min_val + i / n_bands * elev_range
    band_high = elev_min_val + (i + 1) / n_bands * elev_range
    clipped = np.clip(elevation, band_low, band_high)
    ax.fill_between(
        distance, np.full_like(distance, band_low), clipped, color=imprint_seq(i / n_bands), alpha=0.8, linewidth=0
    )
ax.fill_between(distance, y_min, np.full_like(distance, elev_min_val), color=imprint_seq(0.0), alpha=0.8, linewidth=0)

# Profile line via seaborn lineplot
sns.lineplot(data=df, x="distance_km", y="elevation_m", ax=ax, color=IMPRINT_PALETTE[2], linewidth=2.0, legend=False)

# Landmark markers — slope intensity encoded via Imprint sequential cmap
for _, lm in landmarks.iterrows():
    ax.scatter(
        lm["distance_km"],
        lm["elevation_m"],
        color=imprint_seq(lm["slope"] / slope_max),
        s=90,
        edgecolor=PAGE_BG,
        linewidth=1.0,
        zorder=5,
    )

# Landmark annotations with smart positioning
for _, lm in landmarks.iterrows():
    ax.vlines(lm["distance_km"], y_min, lm["elevation_m"], color=INK_SOFT, linewidth=0.5, linestyle=":", alpha=0.5)
    label_text = f"{lm['name']}\n{int(lm['elevation_m'])} m"
    y_offset = 35 if lm["elevation_m"] < (elev_max_val - 200) else -50
    x_offset = -28 if lm["distance_km"] >= total_distance - 1 else (28 if lm["distance_km"] <= 1 else 0)
    ha = "right" if lm["distance_km"] >= total_distance - 1 else ("left" if lm["distance_km"] <= 1 else "center")
    ax.annotate(
        label_text,
        xy=(lm["distance_km"], lm["elevation_m"]),
        xytext=(x_offset, y_offset),
        textcoords="offset points",
        fontsize=7,
        fontweight="bold",
        color=INK,
        ha=ha,
        va="bottom" if y_offset > 0 else "top",
        bbox={"boxstyle": "round,pad=0.25", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.9},
        zorder=6,
    )

# Marginal KDE strip — distinctive seaborn feature showing elevation distribution
sns.kdeplot(y=df["elevation_m"], ax=ax_kde, fill=True, color=IMPRINT_PALETTE[2], alpha=0.3, linewidth=1.2)
sns.rugplot(data=landmarks, y="elevation_m", ax=ax_kde, color=IMPRINT_PALETTE[2], height=0.3, linewidth=1.5, alpha=0.7)
ax_kde.set_xlabel("")
ax_kde.set_ylabel("")
ax_kde.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)
ax_kde.set_facecolor(PAGE_BG)
sns.despine(ax=ax_kde, left=True, bottom=True)

# Style main axes
title = "area-elevation-profile · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK, pad=8)
ax.set_xlabel("Distance (km)", fontsize=10, color=INK)
ax.set_ylabel("Elevation (m)", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.yaxis.set_major_locator(plt.MultipleLocator(200))
ax.xaxis.set_major_locator(plt.MultipleLocator(20))
sns.despine(ax=ax)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.5)
ax.set_xlim(0, total_distance)
ax.set_ylim(bottom=y_min)

ax.text(
    0.98,
    0.02,
    "Vertical exaggeration ~10×",
    transform=ax.transAxes,
    fontsize=7,
    color=INK_MUTED,
    ha="right",
    va="bottom",
    style="italic",
)

fig.subplots_adjust(left=0.07, right=0.97, top=0.92, bottom=0.10)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
