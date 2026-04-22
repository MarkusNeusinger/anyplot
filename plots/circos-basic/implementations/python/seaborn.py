"""pyplots.ai
circos-basic: Circos Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 82/100 | Created: 2025-12-31
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Set seaborn theme for consistent styling with larger fonts
sns.set_theme(style="white", context="poster", font_scale=1.3)

# Data: Regional trade flows (10 regions with trade connections)
np.random.seed(42)

# Define segments (regions) with their sizes (trade volume in billion USD)
# Reordered to ensure adjacent regions have distinct colors
segments = [
    "North America",
    "East Asia",
    "Europe",
    "South Asia",
    "Middle East",
    "Southeast Asia",
    "Africa",
    "Oceania",
    "South America",
    "Central Asia",
]
n_segments = len(segments)

# Segment sizes represent total trade volume (billion USD) - reordered
segment_sizes = np.array([250, 280, 320, 120, 100, 150, 80, 60, 90, 50])

# Create connection data (source, target, value in billion USD)
# Updated indices for reordered segments:
# 0=North America, 1=East Asia, 2=Europe, 3=South Asia, 4=Middle East,
# 5=Southeast Asia, 6=Africa, 7=Oceania, 8=South America, 9=Central Asia
connections = [
    (0, 2, 85),  # North America - Europe
    (0, 1, 120),  # North America - East Asia
    (2, 1, 95),  # Europe - East Asia
    (2, 4, 60),  # Europe - Middle East
    (1, 5, 70),  # East Asia - Southeast Asia
    (1, 3, 45),  # East Asia - South Asia
    (5, 3, 35),  # Southeast Asia - South Asia
    (2, 6, 40),  # Europe - Africa
    (0, 8, 55),  # North America - South America
    (1, 7, 50),  # East Asia - Oceania
    (4, 3, 30),  # Middle East - South Asia
    (4, 6, 25),  # Middle East - Africa
    (2, 9, 20),  # Europe - Central Asia
    (1, 9, 28),  # East Asia - Central Asia
    (0, 5, 38),  # North America - Southeast Asia
]

# Use seaborn's diverging color palette for better distinction between adjacent segments
# tab10 provides 10 distinct colors that work well for categorical data
colors = sns.color_palette("tab10", n_colors=n_segments)

# Create square figure for circular symmetry (3600x3600 at 300 dpi = 12x12 inches)
fig, ax = plt.subplots(figsize=(12, 12))
ax.set_aspect("equal")

# Calculate segment positions (angles)
total_size = segment_sizes.sum()
gap_fraction = 0.02
total_gap = gap_fraction * n_segments
available_angle = 2 * np.pi * (1 - total_gap / (2 * np.pi))

angles = []
current_angle = np.pi / 2

for size in segment_sizes:
    segment_angle = (size / total_size) * available_angle
    start_angle = current_angle
    end_angle = current_angle - segment_angle
    angles.append((start_angle, end_angle))
    current_angle = end_angle - gap_fraction

# Draw outer ring segments
outer_radius = 1.0
ring_width = 0.12

for i, (start, end) in enumerate(angles):
    theta = np.linspace(end, start, 50)
    inner = outer_radius - ring_width
    x_outer = outer_radius * np.cos(theta)
    y_outer = outer_radius * np.sin(theta)
    x_inner = inner * np.cos(theta[::-1])
    y_inner = inner * np.sin(theta[::-1])
    x = np.concatenate([x_outer, x_inner])
    y = np.concatenate([y_outer, y_inner])
    ax.fill(x, y, color=colors[i], alpha=0.85, edgecolor="white", linewidth=2)

    # Add segment label with larger font
    mid_angle = (start + end) / 2
    label_radius = outer_radius + 0.14
    label_x = label_radius * np.cos(mid_angle)
    label_y = label_radius * np.sin(mid_angle)
    rotation_deg = np.degrees(mid_angle)
    norm_angle = rotation_deg % 360
    if 90 < norm_angle < 270:
        rotation = rotation_deg + 180
        ha = "right"
    else:
        rotation = rotation_deg
        ha = "left"
    ax.text(
        label_x,
        label_y,
        segments[i],
        ha=ha,
        va="center",
        fontsize=18,
        fontweight="bold",
        rotation=rotation,
        rotation_mode="anchor",
    )

# Draw inner data track (trade volume as bar heights)
inner_track_outer = outer_radius - ring_width - 0.03
inner_track_inner = inner_track_outer - 0.15

for i, (start, end) in enumerate(angles):
    height_fraction = segment_sizes[i] / segment_sizes.max()
    track_height = (inner_track_outer - inner_track_inner) * height_fraction
    theta = np.linspace(end, start, 30)
    inner = inner_track_outer - track_height
    x_outer = inner_track_outer * np.cos(theta)
    y_outer = inner_track_outer * np.sin(theta)
    x_inner = inner * np.cos(theta[::-1])
    y_inner = inner * np.sin(theta[::-1])
    x = np.concatenate([x_outer, x_inner])
    y = np.concatenate([y_outer, y_inner])
    ax.fill(x, y, color=colors[i], alpha=0.5, edgecolor="none")

# Draw ribbons (connections between segments) - inline bezier curve calculation
ribbon_radius = inner_track_inner - 0.05
max_value = max(c[2] for c in connections)
min_value = min(c[2] for c in connections)
ctrl_radius = ribbon_radius * 0.1
n_points = 50
t = np.linspace(0, 1, n_points)

for source, target, value in connections:
    # Improved width calculation: ensure minimum visibility for smaller values
    # Map values from min-max to 0.25-0.7 range for better distinction
    normalized_value = (value - min_value) / (max_value - min_value)
    width_fraction = 0.25 + normalized_value * 0.45

    start1, end1 = angles[source]
    start2, end2 = angles[target]
    seg1_span = (start1 - end1) * width_fraction * 0.4
    seg2_span = (start2 - end2) * width_fraction * 0.4
    mid1 = (start1 + end1) / 2
    mid2 = (start2 + end2) / 2
    ribbon_start1 = mid1 + seg1_span / 2
    ribbon_end1 = mid1 - seg1_span / 2
    ribbon_start2 = mid2 + seg2_span / 2
    ribbon_end2 = mid2 - seg2_span / 2

    # First bezier curve
    p0 = np.array([ribbon_radius * np.cos(ribbon_start1), ribbon_radius * np.sin(ribbon_start1)])
    p3 = np.array([ribbon_radius * np.cos(ribbon_start2), ribbon_radius * np.sin(ribbon_start2)])
    p1 = ctrl_radius * np.array([np.cos(ribbon_start1), np.sin(ribbon_start1)])
    p2 = ctrl_radius * np.array([np.cos(ribbon_start2), np.sin(ribbon_start2)])
    curve1 = (
        (1 - t)[:, None] ** 3 * p0
        + 3 * (1 - t)[:, None] ** 2 * t[:, None] * p1
        + 3 * (1 - t)[:, None] * t[:, None] ** 2 * p2
        + t[:, None] ** 3 * p3
    )

    # Second bezier curve
    p0 = np.array([ribbon_radius * np.cos(ribbon_end1), ribbon_radius * np.sin(ribbon_end1)])
    p3 = np.array([ribbon_radius * np.cos(ribbon_end2), ribbon_radius * np.sin(ribbon_end2)])
    p1 = ctrl_radius * np.array([np.cos(ribbon_end1), np.sin(ribbon_end1)])
    p2 = ctrl_radius * np.array([np.cos(ribbon_end2), np.sin(ribbon_end2)])
    curve2 = (
        (1 - t)[:, None] ** 3 * p0
        + 3 * (1 - t)[:, None] ** 2 * t[:, None] * p1
        + 3 * (1 - t)[:, None] * t[:, None] ** 2 * p2
        + t[:, None] ** 3 * p3
    )

    # Arcs at source and target segments
    arc1_angles = np.linspace(ribbon_start1, ribbon_end1, 10)
    arc1 = ribbon_radius * np.column_stack([np.cos(arc1_angles), np.sin(arc1_angles)])
    arc2_angles = np.linspace(ribbon_end2, ribbon_start2, 10)
    arc2 = ribbon_radius * np.column_stack([np.cos(arc2_angles), np.sin(arc2_angles)])

    # Combine vertices and draw polygon
    vertices = np.vstack([arc1, curve1, arc2, curve2[::-1]])
    polygon = plt.Polygon(vertices, facecolor=colors[source], edgecolor="none", alpha=0.45, zorder=1)
    ax.add_patch(polygon)

# Configure axes
ax.set_xlim(-1.7, 1.7)
ax.set_ylim(-1.7, 1.7)
ax.axis("off")

# Title with proper format: spec-id · library · pyplots.ai
ax.set_title("circos-basic · seaborn · pyplots.ai", fontsize=28, fontweight="bold", pad=20)

# Add legend explaining the visualization
legend_elements = [
    mpatches.Patch(facecolor=colors[0], alpha=0.85, label="Outer ring: Region (arc size ∝ total trade)"),
    mpatches.Patch(facecolor=colors[0], alpha=0.5, label="Inner track: Trade volume (bar height)"),
    mpatches.Patch(facecolor=colors[0], alpha=0.45, label="Ribbons: Trade flow (width ∝ value)"),
]
ax.legend(handles=legend_elements, loc="lower center", bbox_to_anchor=(0.5, -0.08), ncol=1, fontsize=16, frameon=False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
