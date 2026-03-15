""" pyplots.ai
stereonet-equal-area: Structural Geology Stereonet (Equal-Area Projection)
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 81/100 | Created: 2026-03-15
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import gaussian_kde


# Data - field measurements from a geological mapping campaign
np.random.seed(42)

bedding_strike = np.random.normal(45, 8, 40) % 360
bedding_dip = np.clip(np.random.normal(35, 5, 40), 1, 89)

joint1_strike = np.random.normal(315, 10, 30) % 360
joint1_dip = np.clip(np.random.normal(75, 8, 30), 1, 89)

joint2_strike = np.random.normal(90, 12, 25) % 360
joint2_dip = np.clip(np.random.normal(60, 10, 25), 1, 89)

fault_strike = np.random.normal(180, 15, 15) % 360
fault_dip = np.clip(np.random.normal(70, 10, 15), 1, 89)

strikes = np.concatenate([bedding_strike, joint1_strike, joint2_strike, fault_strike])
dips = np.concatenate([bedding_dip, joint1_dip, joint2_dip, fault_dip])
feature_types = ["Bedding"] * 40 + ["Joint Set 1"] * 30 + ["Joint Set 2"] * 25 + ["Fault"] * 15

df = pd.DataFrame({"strike": strikes, "dip": dips, "feature_type": feature_types})

# Equal-area projection: convert pole trend/plunge to x, y
pole_trend = (df["strike"].values + 270) % 360
pole_plunge = 90 - df["dip"].values
pole_trend_rad = np.radians(pole_trend)
pole_plunge_rad = np.radians(pole_plunge)
pole_r = np.sqrt(2) * np.sin((np.pi / 2 - pole_plunge_rad) / 2)
df["pole_x"] = pole_r * np.sin(pole_trend_rad)
df["pole_y"] = pole_r * np.cos(pole_trend_rad)

# Plot
sns.set_context("talk", font_scale=1.2)
fig, ax = plt.subplots(figsize=(12, 12))
ax.set_aspect("equal")

palette = {"Bedding": "#306998", "Joint Set 1": "#E88D39", "Joint Set 2": "#3AA655", "Fault": "#C44E52"}

# Primitive circle
theta_circle = np.linspace(0, 2 * np.pi, 300)
ax.plot(np.sin(theta_circle), np.cos(theta_circle), "k-", linewidth=1.5, zorder=4)

# Grid: small circles (constant plunge)
for plunge_deg in range(10, 90, 10):
    r = np.sqrt(2) * np.sin((np.pi / 2 - np.radians(plunge_deg)) / 2)
    grid_circle = plt.Circle((0, 0), r, fill=False, color="#d0d0d0", linewidth=0.4, zorder=1)
    ax.add_patch(grid_circle)

# Grid: great circles for N-S and E-W reference planes
for ref_strike in [0, 90]:
    ref_strike_rad = np.radians(ref_strike)
    for ref_dip in range(10, 90, 10):
        ref_dip_rad = np.radians(ref_dip)
        alpha = np.linspace(0.01, np.pi - 0.01, 150)
        vx = np.cos(alpha) * np.sin(ref_strike_rad) + np.sin(alpha) * np.cos(ref_dip_rad) * np.cos(ref_strike_rad)
        vy = np.cos(alpha) * np.cos(ref_strike_rad) - np.sin(alpha) * np.cos(ref_dip_rad) * np.sin(ref_strike_rad)
        vz = -np.sin(alpha) * np.sin(ref_dip_rad)
        gc_plunge = np.arcsin(np.clip(-vz, -1, 1))
        gc_trend = np.arctan2(vx, vy)
        gc_r = np.sqrt(2) * np.sin((np.pi / 2 - gc_plunge) / 2)
        gc_x = gc_r * np.sin(gc_trend)
        gc_y = gc_r * np.cos(gc_trend)
        ax.plot(gc_x, gc_y, color="#d0d0d0", linewidth=0.4, zorder=1)

# Tick marks every 10 degrees
for azimuth in range(0, 360, 10):
    az_rad = np.radians(azimuth)
    tick_inner = 0.97 if azimuth % 30 != 0 else 0.95
    ax.plot(
        [tick_inner * np.sin(az_rad), np.sin(az_rad)],
        [tick_inner * np.cos(az_rad), np.cos(az_rad)],
        "k-",
        linewidth=0.8,
        zorder=4,
    )

# Cardinal direction labels
for az, label in [(0, "N"), (90, "E"), (180, "S"), (270, "W")]:
    az_rad = np.radians(az)
    ax.text(
        1.08 * np.sin(az_rad),
        1.08 * np.cos(az_rad),
        label,
        ha="center",
        va="center",
        fontsize=20,
        fontweight="bold",
        zorder=6,
    )

# Degree labels every 30 degrees (skip cardinals)
for az in range(30, 360, 30):
    if az in [90, 180, 270]:
        continue
    az_rad = np.radians(az)
    ax.text(
        1.07 * np.sin(az_rad),
        1.07 * np.cos(az_rad),
        f"{az}°",
        ha="center",
        va="center",
        fontsize=13,
        color="#555555",
        zorder=6,
    )

# Density contours (Kamb-style) on pole data
kde = gaussian_kde(np.vstack([df["pole_x"], df["pole_y"]]), bw_method=0.15)
xi = np.linspace(-1, 1, 200)
yi = np.linspace(-1, 1, 200)
Xi, Yi = np.meshgrid(xi, yi)
mask = Xi**2 + Yi**2 <= 1
Zi = kde(np.vstack([Xi.ravel(), Yi.ravel()])).reshape(Xi.shape)
Zi[~mask] = np.nan
ax.contourf(Xi, Yi, Zi, levels=6, cmap="Greys", alpha=0.15, zorder=2)
ax.contour(Xi, Yi, Zi, levels=6, colors="#999999", linewidths=0.7, alpha=0.5, zorder=2)

# Great circles for representative planes (3 per feature type)
for feature_type in df["feature_type"].unique():
    subset = df[df["feature_type"] == feature_type]
    indices = np.linspace(0, len(subset) - 1, min(3, len(subset)), dtype=int)
    for idx in indices:
        row = subset.iloc[idx]
        s_rad = np.radians(row["strike"])
        d_rad = np.radians(row["dip"])
        alpha = np.linspace(0.01, np.pi - 0.01, 200)
        vx = np.cos(alpha) * np.sin(s_rad) + np.sin(alpha) * np.cos(d_rad) * np.cos(s_rad)
        vy = np.cos(alpha) * np.cos(s_rad) - np.sin(alpha) * np.cos(d_rad) * np.sin(s_rad)
        vz = -np.sin(alpha) * np.sin(d_rad)
        gc_plunge = np.arcsin(np.clip(-vz, -1, 1))
        gc_trend = np.arctan2(vx, vy)
        gc_r = np.sqrt(2) * np.sin((np.pi / 2 - gc_plunge) / 2)
        gc_x = gc_r * np.sin(gc_trend)
        gc_y = gc_r * np.cos(gc_trend)
        ax.plot(gc_x, gc_y, color=palette[feature_type], linewidth=1.5, alpha=0.4, zorder=3)

# Poles using seaborn scatterplot
sns.scatterplot(
    data=df,
    x="pole_x",
    y="pole_y",
    hue="feature_type",
    palette=palette,
    s=150,
    edgecolor="white",
    linewidth=0.8,
    alpha=0.85,
    ax=ax,
    zorder=5,
)

# Style
ax.set_xlim(-1.22, 1.22)
ax.set_ylim(-1.22, 1.22)
ax.set_xlabel("")
ax.set_ylabel("")
ax.set_xticks([])
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_visible(False)

ax.legend(
    title="Feature Type",
    loc="upper left",
    fontsize=15,
    title_fontsize=17,
    framealpha=0.95,
    edgecolor="#cccccc",
    bbox_to_anchor=(-0.02, 1.02),
)

ax.set_title("stereonet-equal-area · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=25)

# Save
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
