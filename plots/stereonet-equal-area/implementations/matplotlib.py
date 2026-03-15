"""pyplots.ai
stereonet-equal-area: Structural Geology Stereonet (Equal-Area Projection)
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 83/100 | Created: 2026-03-15
"""

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection


# Data - structural geology field measurements (strike/dip format)
np.random.seed(42)

bedding_strike = np.random.normal(45, 12, 30) % 360
bedding_dip = np.clip(np.random.normal(30, 8, 30), 2, 88)

joint_strike = np.random.normal(300, 10, 25) % 360
joint_dip = np.clip(np.random.normal(72, 7, 25), 2, 88)

fault_strike = np.random.normal(185, 15, 20) % 360
fault_dip = np.clip(np.random.normal(58, 10, 20), 2, 88)

datasets = {
    "Bedding": (bedding_strike, bedding_dip),
    "Joint": (joint_strike, joint_dip),
    "Fault": (fault_strike, fault_dip),
}
all_strikes = np.concatenate([bedding_strike, joint_strike, fault_strike])
all_dips = np.concatenate([bedding_dip, joint_dip, fault_dip])
feature_types = ["Bedding"] * 30 + ["Joint"] * 25 + ["Fault"] * 20

# Visual hierarchy: Bedding is primary focus (thicker, more opaque)
colors = {"Bedding": "#306998", "Joint": "#E8833A", "Fault": "#8B2252"}
markers = {"Bedding": "o", "Joint": "s", "Fault": "^"}
pole_sizes = {"Bedding": 200, "Joint": 140, "Fault": 140}
gc_alpha = {"Bedding": 0.55, "Joint": 0.25, "Fault": 0.25}
gc_lw = {"Bedding": 1.8, "Joint": 0.9, "Fault": 0.9}

# Pole orientations in equal-area (Schmidt) projection
pole_trend_rad = np.deg2rad((all_strikes + 90) % 360)
pole_r = np.sqrt(2) * np.sin(np.deg2rad(all_dips) / 2)

# Pole unit vectors on sphere (East, North, Down coordinates)
pole_colat = np.deg2rad(all_dips)
pole_vx = np.sin(pole_colat) * np.sin(pole_trend_rad)
pole_vy = np.sin(pole_colat) * np.cos(pole_trend_rad)
pole_vz = np.cos(pole_colat)

# Plot
fig = plt.figure(figsize=(12, 12), facecolor="white")
ax = fig.add_subplot(111, projection="polar")
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
ax.set_facecolor("#FAFAF8")

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

contour_fill = ax.contourf(THETA, R, Z, levels=10, cmap="YlOrBr", alpha=0.35, zorder=1)
ax.contour(THETA, R, Z, levels=10, colors="#B87333", alpha=0.35, linewidths=0.5, zorder=1)

# Great circles - representative subset only (5 per group to reduce clutter)
t_param = np.linspace(0, np.pi, 180)


def draw_great_circle(strike_deg, dip_deg):
    alpha = np.deg2rad(strike_deg)
    delta = np.deg2rad(dip_deg)
    px = np.cos(t_param) * np.sin(alpha) + np.sin(t_param) * np.cos(alpha) * np.cos(delta)
    py = np.cos(t_param) * np.cos(alpha) - np.sin(t_param) * np.sin(alpha) * np.cos(delta)
    pz = np.sin(t_param) * np.sin(delta)
    trend = np.arctan2(px, py)
    horiz = np.sqrt(px**2 + py**2)
    plunge = np.arctan2(pz, horiz)
    colat = np.pi / 2 - plunge
    r = np.sqrt(2) * np.sin(colat / 2)
    return trend, r


for feat, (strikes, dips) in datasets.items():
    # Mean great circle (bold)
    mean_strike = (
        np.degrees(np.arctan2(np.mean(np.sin(np.deg2rad(strikes))), np.mean(np.cos(np.deg2rad(strikes))))) % 360
    )
    mean_dip = np.mean(dips)
    trend, r = draw_great_circle(mean_strike, mean_dip)
    ax.plot(trend, r, color=colors[feat], alpha=gc_alpha[feat] + 0.2, linewidth=gc_lw[feat] + 0.8, zorder=2)

    # 4 representative great circles (evenly spaced indices)
    indices = np.linspace(0, len(strikes) - 1, 4, dtype=int)
    segments = []
    for idx in indices:
        trend, r = draw_great_circle(strikes[idx], dips[idx])
        points = np.column_stack([trend, r])
        segments.append(points)
    lc = LineCollection(segments, colors=colors[feat], alpha=gc_alpha[feat], linewidths=gc_lw[feat], zorder=2)
    ax.add_collection(lc)

# Poles as scatter points with distinct markers per feature type
for feat in colors:
    mask = np.array([ft == feat for ft in feature_types])
    ax.scatter(
        pole_trend_rad[mask],
        pole_r[mask],
        c=colors[feat],
        s=pole_sizes[feat],
        marker=markers[feat],
        edgecolors="white",
        linewidth=1.2,
        label=f"{feat} poles",
        zorder=5,
        path_effects=[pe.withStroke(linewidth=2.5, foreground="white")],
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
ax.set_xticklabels(tick_labels, fontsize=16, fontweight="medium")

# Bold cardinal direction labels
for label in ax.get_xticklabels():
    txt = label.get_text()
    if txt in ("N", "E", "S", "W"):
        label.set_fontsize(20)
        label.set_fontweight("bold")
        label.set_color("#222222")
        label.set_path_effects([pe.withStroke(linewidth=2, foreground="white")])
ax.grid(True, alpha=0.12, linewidth=0.4, color="#888888")

# Primitive circle emphasis
circle_theta = np.linspace(0, 2 * np.pi, 300)
ax.plot(circle_theta, np.ones_like(circle_theta), color="#333333", linewidth=2.0, zorder=3)

# Legend positioned to avoid tick mark overlap
legend = ax.legend(
    loc="lower left",
    bbox_to_anchor=(-0.02, -0.08),
    fontsize=16,
    framealpha=0.95,
    edgecolor="#bbbbbb",
    fancybox=True,
    markerscale=1.3,
    shadow=True,
    borderpad=0.8,
)
legend.get_frame().set_linewidth(0.8)

ax.set_title(
    "stereonet-equal-area · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=28, color="#333333"
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
