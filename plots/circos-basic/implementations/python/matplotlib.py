""" pyplots.ai
circos-basic: Circos Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.path import Path


# Data: Software module dependencies
np.random.seed(42)

# Define segments (software modules)
segments = ["Core", "API", "Database", "Auth", "Cache", "Queue", "Logger", "Config"]
n_segments = len(segments)

# Segment sizes (relative importance/size of each module)
segment_sizes = np.array([25, 20, 18, 15, 12, 10, 8, 6])
segment_sizes = segment_sizes / segment_sizes.sum() * 360  # Convert to degrees

# Connection matrix (dependencies between modules)
connections = [
    ("Core", "API", 15),
    ("Core", "Database", 12),
    ("Core", "Logger", 8),
    ("API", "Auth", 10),
    ("API", "Cache", 8),
    ("Database", "Cache", 6),
    ("Database", "Logger", 5),
    ("Auth", "Logger", 4),
    ("Queue", "Logger", 7),
    ("Queue", "Database", 5),
    ("Config", "Core", 9),
    ("Config", "Logger", 3),
    ("Cache", "Logger", 4),
    ("API", "Queue", 6),
]

# Colors for each segment (colorblind-safe palette)
colors = [
    "#306998",  # Python Blue
    "#FFD43B",  # Python Yellow
    "#2E8B57",  # Sea Green
    "#DC143C",  # Crimson
    "#9370DB",  # Medium Purple
    "#20B2AA",  # Light Sea Green
    "#FF8C00",  # Dark Orange
    "#708090",  # Slate Gray
]

# Create figure (square for circular plot)
fig, ax = plt.subplots(figsize=(12, 12))
ax.set_aspect("equal")
ax.axis("off")

# Calculate segment positions
gap = 2  # Gap between segments in degrees
total_gap = gap * n_segments
available = 360 - total_gap
segment_angles = segment_sizes / 360 * available

# Calculate start and end angles for each segment
starts = []
ends = []
current = 90  # Start at top

for angle in segment_angles:
    starts.append(current)
    ends.append(current - angle)
    current = current - angle - gap

segment_dict = {name: i for i, name in enumerate(segments)}

# Draw outer ring segments
r_outer = 1.0
r_inner = 0.85
n_arc_points = 50

for i in range(n_segments):
    start, end = starts[i], ends[i]
    theta1_rad = np.radians(end)
    theta2_rad = np.radians(start)
    theta = np.linspace(theta1_rad, theta2_rad, n_arc_points)

    # Outer arc
    x_outer = r_outer * np.cos(theta)
    y_outer = r_outer * np.sin(theta)
    # Inner arc (reversed)
    x_inner = r_inner * np.cos(theta[::-1])
    y_inner = r_inner * np.sin(theta[::-1])
    # Combine into closed polygon
    x = np.concatenate([x_outer, x_inner])
    y = np.concatenate([y_outer, y_inner])
    ax.fill(x, y, color=colors[i], alpha=0.9, edgecolor="white", linewidth=1)

    # Add segment label
    mid_angle = np.radians((start + end) / 2)
    label_r = r_outer + 0.08
    lx = label_r * np.cos(mid_angle)
    ly = label_r * np.sin(mid_angle)
    ax.text(lx, ly, segments[i], fontsize=18, fontweight="bold", ha="center", va="center", color=colors[i])

# Draw inner data track (simulated importance values)
track_data = np.random.uniform(0.3, 1.0, n_segments)
r_track_outer = 0.82
r_track_inner = 0.70

for i in range(n_segments):
    start, end = starts[i], ends[i]
    track_height = (r_track_outer - r_track_inner) * track_data[i]
    theta1_rad = np.radians(end)
    theta2_rad = np.radians(start)
    theta = np.linspace(theta1_rad, theta2_rad, n_arc_points)

    x_outer = (r_track_inner + track_height) * np.cos(theta)
    y_outer = (r_track_inner + track_height) * np.sin(theta)
    x_inner = r_track_inner * np.cos(theta[::-1])
    y_inner = r_track_inner * np.sin(theta[::-1])
    x = np.concatenate([x_outer, x_inner])
    y = np.concatenate([y_outer, y_inner])
    ax.fill(x, y, color=colors[i], alpha=0.6, edgecolor="none")

# Draw connections (ribbons)
max_value = max(c[2] for c in connections)
r_ribbon = r_inner - 0.02

for source, target, value in connections:
    idx1 = segment_dict[source]
    idx2 = segment_dict[target]

    # Calculate positions within segments
    mid1 = np.radians((starts[idx1] + ends[idx1]) / 2)
    mid2 = np.radians((starts[idx2] + ends[idx2]) / 2)

    # Ribbon width proportional to value
    width_factor = value / max_value * 0.15

    # Points for segment 1
    angle1_start = mid1 - width_factor
    angle1_end = mid1 + width_factor
    x1_start = r_ribbon * np.cos(angle1_start)
    y1_start = r_ribbon * np.sin(angle1_start)
    x1_end = r_ribbon * np.cos(angle1_end)
    y1_end = r_ribbon * np.sin(angle1_end)

    # Points for segment 2
    angle2_start = mid2 - width_factor
    angle2_end = mid2 + width_factor
    x2_start = r_ribbon * np.cos(angle2_start)
    y2_start = r_ribbon * np.sin(angle2_start)
    x2_end = r_ribbon * np.cos(angle2_end)
    y2_end = r_ribbon * np.sin(angle2_end)

    # Control points at center for bezier curves
    ctrl_factor = 0.3
    ctrl1_x = ctrl_factor * (x1_start + x2_end) / 2
    ctrl1_y = ctrl_factor * (y1_start + y2_end) / 2
    ctrl2_x = ctrl_factor * (x1_end + x2_start) / 2
    ctrl2_y = ctrl_factor * (y1_end + y2_start) / 2

    # Path vertices
    verts = [
        (x1_start, y1_start),
        (ctrl1_x, ctrl1_y),
        (x2_end, y2_end),
        (x2_start, y2_start),
        (ctrl2_x, ctrl2_y),
        (x1_end, y1_end),
        (x1_start, y1_start),
    ]
    codes = [Path.MOVETO, Path.CURVE3, Path.CURVE3, Path.LINETO, Path.CURVE3, Path.CURVE3, Path.CLOSEPOLY]

    path = Path(verts, codes)
    patch = mpatches.PathPatch(path, facecolor=colors[idx1], alpha=0.5, edgecolor="none")
    ax.add_patch(patch)

# Title
ax.set_title("circos-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="bold", pad=20)

# Set limits with padding
ax.set_xlim(-1.4, 1.4)
ax.set_ylim(-1.4, 1.4)

# Legend (outside the plot)
legend_elements = [mpatches.Patch(facecolor=colors[i], label=segments[i], alpha=0.9) for i in range(n_segments)]
ax.legend(
    handles=legend_elements,
    loc="lower right",
    fontsize=14,
    frameon=True,
    fancybox=True,
    framealpha=0.9,
    ncol=1,
    bbox_to_anchor=(1.35, 0.0),
    title="Modules",
    title_fontsize=16,
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
