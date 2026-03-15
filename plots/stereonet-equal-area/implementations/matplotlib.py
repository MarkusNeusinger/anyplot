"""pyplots.ai
stereonet-equal-area: Structural Geology Stereonet (Equal-Area Projection)
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-03-15
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - structural geology field measurements (strike/dip format)
np.random.seed(42)

bedding_strike = np.random.normal(45, 12, 30) % 360
bedding_dip = np.clip(np.random.normal(30, 8, 30), 2, 88)

joint_strike = np.random.normal(300, 10, 25) % 360
joint_dip = np.clip(np.random.normal(72, 7, 25), 2, 88)

fault_strike = np.random.normal(185, 15, 20) % 360
fault_dip = np.clip(np.random.normal(58, 10, 20), 2, 88)

all_strikes = np.concatenate([bedding_strike, joint_strike, fault_strike])
all_dips = np.concatenate([bedding_dip, joint_dip, fault_dip])
feature_types = ["Bedding"] * 30 + ["Joint"] * 25 + ["Fault"] * 20
colors = {"Bedding": "#306998", "Joint": "#E8833A", "Fault": "#9B2335"}
markers = {"Bedding": "o", "Joint": "s", "Fault": "^"}

# Pole orientations in equal-area (Schmidt) projection
# Pole trend = dip direction = strike + 90 degrees
# Equal-area radius: r = sqrt(2) * sin(dip_rad / 2)
pole_trend_rad = np.deg2rad((all_strikes + 90) % 360)
pole_r = np.sqrt(2) * np.sin(np.deg2rad(all_dips) / 2)

# Pole unit vectors on sphere (East, North, Down coordinates)
pole_colat = np.deg2rad(all_dips)
pole_vx = np.sin(pole_colat) * np.sin(pole_trend_rad)
pole_vy = np.sin(pole_colat) * np.cos(pole_trend_rad)
pole_vz = np.cos(pole_colat)

# Plot
fig = plt.figure(figsize=(12, 12))
ax = fig.add_subplot(111, projection="polar")
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)

# Density contours using spherical Gaussian kernel on pole data
theta_grid = np.linspace(0, 2 * np.pi, 150)
r_grid = np.linspace(0.02, 0.98, 75)
THETA, R = np.meshgrid(theta_grid, r_grid)
colat_grid = 2 * np.arcsin(np.clip(R / np.sqrt(2), 0, 1))
gx = np.sin(colat_grid) * np.sin(THETA)
gy = np.sin(colat_grid) * np.cos(THETA)
gz = np.cos(colat_grid)

sigma = 0.20
Z = np.zeros(THETA.shape)
for j in range(len(all_dips)):
    cos_dist = gx * pole_vx[j] + gy * pole_vy[j] + gz * pole_vz[j]
    Z += np.exp(-(np.arccos(np.clip(cos_dist, -1, 1)) ** 2) / (2 * sigma**2))

ax.contourf(THETA, R, Z, levels=8, cmap="Greys", alpha=0.25, zorder=1)

# Great circles for each plane
t_param = np.linspace(0, np.pi, 180)
for i in range(len(all_strikes)):
    alpha = np.deg2rad(all_strikes[i])
    delta = np.deg2rad(all_dips[i])
    px = np.cos(t_param) * np.sin(alpha) + np.sin(t_param) * np.cos(alpha) * np.cos(delta)
    py = np.cos(t_param) * np.cos(alpha) - np.sin(t_param) * np.sin(alpha) * np.cos(delta)
    pz = np.sin(t_param) * np.sin(delta)
    trend = np.arctan2(px, py)
    horiz = np.sqrt(px**2 + py**2)
    plunge = np.arctan2(pz, horiz)
    colat = np.pi / 2 - plunge
    r = np.sqrt(2) * np.sin(colat / 2)
    ax.plot(trend, r, color=colors[feature_types[i]], alpha=0.15, linewidth=0.7, zorder=2)

# Poles as scatter points with distinct markers per feature type
for feat in colors:
    mask = np.array([ft == feat for ft in feature_types])
    ax.scatter(
        pole_trend_rad[mask],
        pole_r[mask],
        c=colors[feat],
        s=150,
        marker=markers[feat],
        edgecolors="white",
        linewidth=0.8,
        label=f"{feat} poles",
        zorder=5,
    )

# Style
ax.set_rlim(0, 1)
ax.set_rticks([])
theta_ticks = np.arange(0, 360, 10)
ax.set_xticks(np.deg2rad(theta_ticks))
tick_labels = []
for d in theta_ticks:
    if d == 0:
        tick_labels.append("N")
    elif d == 90:
        tick_labels.append("E")
    elif d == 180:
        tick_labels.append("S")
    elif d == 270:
        tick_labels.append("W")
    elif d % 30 == 0:
        tick_labels.append(f"{d}°")
    else:
        tick_labels.append("")
ax.set_xticklabels(tick_labels, fontsize=16)
ax.grid(True, alpha=0.15, linewidth=0.5, color="gray")

ax.legend(
    loc="upper right", bbox_to_anchor=(1.22, 1.05), fontsize=16, framealpha=0.9, edgecolor="none", markerscale=1.2
)
ax.set_title("stereonet-equal-area · matplotlib · pyplots.ai", fontsize=22, fontweight="medium", pad=30)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
