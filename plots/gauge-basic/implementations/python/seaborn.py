""" pyplots.ai
gauge-basic: Basic Gauge Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Sales performance gauge
value = 72  # Current sales performance
min_value = 0
max_value = 100
thresholds = [30, 70]  # Zone boundaries

# Create figure with larger gauge
fig, ax = plt.subplots(figsize=(16, 9))
sns.set_theme(style="white")

# Gauge parameters - larger for better canvas utilization
center = (0.5, 0.30)
radius = 0.42
width = 0.18
start_angle = 180
end_angle = 0
angle_range = start_angle - end_angle
value_range = max_value - min_value

# Colorblind-safe palette using seaborn's colorblind palette
cb_palette = sns.color_palette("colorblind", 3)
zone_colors = [cb_palette[2], cb_palette[1], cb_palette[0]]  # Blue-ish, Orange, Green-ish order for low-med-high

# Draw gauge arc segments using seaborn scatterplot for the zone markers
# Create data for zone indicator points along the arc
n_points_per_zone = 50
zone_boundaries = [min_value] + thresholds + [max_value]
zone_data = []

for i in range(len(zone_boundaries) - 1):
    zone_start = zone_boundaries[i]
    zone_end = zone_boundaries[i + 1]
    zone_name = ["Low", "Medium", "High"][i]

    for v in np.linspace(zone_start, zone_end, n_points_per_zone, endpoint=(i == len(zone_boundaries) - 2)):
        angle = start_angle - (v - min_value) / value_range * angle_range
        rad = np.radians(angle)
        # Points along the middle of the arc width
        for r_offset in np.linspace(-width / 2 + 0.01, width / 2 - 0.01, 8):
            r = radius - width / 2 + r_offset + width / 2
            x = center[0] + r * np.cos(rad)
            y = center[1] + r * np.sin(rad)
            zone_data.append({"x": x, "y": y, "zone": zone_name, "value": v})

df_zones = pd.DataFrame(zone_data)

# Use seaborn scatterplot to draw the gauge arc zones with denser points for smooth appearance
sns.scatterplot(
    data=df_zones,
    x="x",
    y="y",
    hue="zone",
    hue_order=["Low", "Medium", "High"],
    palette=[zone_colors[0], zone_colors[1], zone_colors[2]],
    s=180,
    marker="o",
    edgecolor="none",
    alpha=1.0,
    legend=False,
    ax=ax,
)

# Add thin white arc lines at zone boundaries using seaborn for visual separation
for threshold in thresholds:
    boundary_angle = start_angle - (threshold - min_value) / value_range * angle_range
    rad = np.radians(boundary_angle)
    boundary_line_data = []
    for r in np.linspace(radius - width, radius, 10):
        boundary_line_data.append({"x": center[0] + r * np.cos(rad), "y": center[1] + r * np.sin(rad)})
    boundary_df = pd.DataFrame(boundary_line_data)
    sns.lineplot(data=boundary_df, x="x", y="y", color="white", linewidth=3, ax=ax, legend=False)

# Create needle indicator data point using seaborn
needle_angle = start_angle - (value - min_value) / value_range * angle_range
needle_rad = np.radians(needle_angle)
needle_length = radius - width / 2

# Draw needle line
needle_tip_x = center[0] + needle_length * np.cos(needle_rad)
needle_tip_y = center[1] + needle_length * np.sin(needle_rad)

# Use seaborn lineplot for the needle
needle_df = pd.DataFrame({"x": [center[0], needle_tip_x], "y": [center[1], needle_tip_y]})
sns.lineplot(data=needle_df, x="x", y="y", color="#2C3E50", linewidth=6, ax=ax)

# Draw needle tip marker using seaborn scatterplot - larger and more prominent
tip_df = pd.DataFrame({"x": [needle_tip_x], "y": [needle_tip_y]})
# White outline for contrast
sns.scatterplot(data=tip_df, x="x", y="y", s=900, color="white", marker="v", ax=ax, zorder=9)
# Main tip marker
sns.scatterplot(data=tip_df, x="x", y="y", s=700, color="#E74C3C", marker="v", ax=ax, zorder=10)

# Draw center hub using seaborn scatterplot
hub_df = pd.DataFrame({"x": [center[0]], "y": [center[1]]})
sns.scatterplot(data=hub_df, x="x", y="y", s=800, color="#2C3E50", marker="o", ax=ax, zorder=11)

# Value display
ax.text(
    center[0], center[1] - 0.22, f"{value}%", ha="center", va="center", fontsize=52, fontweight="bold", color="#2C3E50"
)

# Min and max labels
ax.text(
    center[0] - radius + width / 2,
    center[1] - 0.10,
    f"{min_value}",
    ha="center",
    va="top",
    fontsize=22,
    color="#555555",
)
ax.text(
    center[0] + radius - width / 2,
    center[1] - 0.10,
    f"{max_value}",
    ha="center",
    va="top",
    fontsize=22,
    color="#555555",
)

# Zone labels on the arc
zone_label_angles = [
    start_angle - (15 / value_range) * angle_range,
    start_angle - (50 / value_range) * angle_range,
    start_angle - (85 / value_range) * angle_range,
]
zone_label_names = ["Low", "Medium", "High"]
label_radius = radius - width / 2

for angle, label in zip(zone_label_angles, zone_label_names, strict=True):
    rad = np.radians(angle)
    x = center[0] + label_radius * np.cos(rad)
    y = center[1] + label_radius * np.sin(rad)
    # Text shadow/outline for better contrast on colored backgrounds
    for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]:
        ax.text(
            x + dx * 0.003,
            y + dy * 0.003,
            label,
            ha="center",
            va="center",
            fontsize=18,
            color="#1a1a1a",
            fontweight="bold",
        )
    ax.text(x, y, label, ha="center", va="center", fontsize=18, color="white", fontweight="bold")

# Title and subtitle
ax.set_title("gauge-basic · seaborn · pyplots.ai", fontsize=28, fontweight="bold", pad=20, color="#333333")
ax.text(center[0], 0.95, "Sales Performance", ha="center", va="top", fontsize=24, color="#555555")

# Axis settings
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_aspect("equal")
ax.axis("off")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
