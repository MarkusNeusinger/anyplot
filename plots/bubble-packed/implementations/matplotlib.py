"""pyplots.ai
bubble-packed: Basic Packed Bubble Chart
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 87/100 | Updated: 2026-02-23
"""

import matplotlib.collections as mcoll
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


# Data - Department budget allocation (in thousands)
labels = [
    "Engineering",
    "Marketing",
    "Sales",
    "Operations",
    "HR",
    "Finance",
    "R&D",
    "Customer Support",
    "Legal",
    "IT",
    "Design",
    "Product",
    "Data Science",
    "Security",
    "QA",
]
values = [950, 420, 680, 310, 160, 280, 820, 200, 130, 370, 230, 580, 470, 145, 175]

# Group assignments - realistic organizational structure
group_map = {
    "Engineering": "Engineering",
    "IT": "Engineering",
    "Data Science": "Engineering",
    "R&D": "Engineering",
    "Marketing": "Business",
    "Sales": "Business",
    "Product": "Business",
    "Design": "Business",
    "Operations": "Operations",
    "HR": "Operations",
    "Finance": "Operations",
    "Customer Support": "Operations",
    "Legal": "Compliance",
    "Security": "Compliance",
    "QA": "Compliance",
}

# Colorblind-safe palette with high hue separation
group_colors = {"Engineering": "#306998", "Business": "#E8C33A", "Operations": "#D4654A", "Compliance": "#8B6DB0"}
colors = [group_colors[group_map[label]] for label in labels]

# Scale values to radius (sqrt for area-proportional sizing)
min_radius = 0.30
max_radius = 2.0
values_array = np.array(values, dtype=float)
radii = min_radius + (max_radius - min_radius) * np.sqrt(
    (values_array - values_array.min()) / (values_array.max() - values_array.min())
)

# Sort by size (largest first) for better packing
n = len(labels)
order = np.argsort(-radii)
radii_sorted = radii[order]
labels_sorted = [labels[i] for i in order]
values_sorted = [values[i] for i in order]
colors_sorted = [colors[i] for i in order]
groups_sorted = [group_map[labels[i]] for i in order]

# Assign group IDs for clustering
unique_groups = list(group_colors.keys())
group_ids = np.array([unique_groups.index(g) for g in groups_sorted])

# Initial positions in spiral pattern for tighter convergence
angles = np.linspace(0, 4 * np.pi, n)
spiral_r = np.linspace(0, 3, n)
positions = np.column_stack([spiral_r * np.cos(angles), spiral_r * np.sin(angles)])

# Physics simulation with group-aware clustering
for iteration in range(500):
    progress = iteration / 500
    pull_strength = 0.06 * (1 - progress * 0.8)
    group_pull = 0.04 * (1 - progress * 0.5)

    # Compute group centers of mass
    group_centers = {}
    for gid in range(len(unique_groups)):
        mask = group_ids == gid
        if np.any(mask):
            group_centers[gid] = positions[mask].mean(axis=0)

    # Pull toward center + pull toward own group center
    for i in range(n):
        dist = np.linalg.norm(positions[i])
        if dist > 0.01:
            positions[i] -= pull_strength * positions[i] / dist

        gc = group_centers[group_ids[i]]
        to_group = gc - positions[i]
        gd = np.linalg.norm(to_group)
        if gd > 0.01:
            positions[i] += group_pull * to_group / gd

    # Push apart overlapping circles
    for i in range(n):
        for j in range(i + 1, n):
            delta = positions[j] - positions[i]
            dist = np.linalg.norm(delta)
            same_group = group_ids[i] == group_ids[j]
            gap = 0.04 if same_group else 0.15
            min_dist = radii_sorted[i] + radii_sorted[j] + gap

            if dist < min_dist and dist > 0.001:
                overlap = (min_dist - dist) / 2
                direction = delta / dist
                positions[i] -= overlap * direction
                positions[j] += overlap * direction

# Center the layout: shift all positions so the bounding box is centered at origin
bbox_min = positions.min(axis=0) - radii_sorted.max()
bbox_max = positions.max(axis=0) + radii_sorted.max()
positions -= (bbox_min + bbox_max) / 2

# Plot (4800x2700 px at 300 dpi)
fig, ax = plt.subplots(figsize=(16, 9))

# Draw circles using PatchCollection for efficient rendering
circles = []
face_colors = []
for i in range(n):
    circle = mpatches.Circle((positions[i, 0], positions[i, 1]), radii_sorted[i])
    circles.append(circle)
    face_colors.append(colors_sorted[i])

collection = mcoll.PatchCollection(
    circles, facecolors=face_colors, edgecolors="white", linewidths=2.5, alpha=0.90, zorder=2
)
ax.add_collection(collection)

# Add labels inside circles that are large enough, external labels for small ones
small_circles = []
for i in range(n):
    label_chars = len(labels_sorted[i])
    min_r_for_label = 0.48 + label_chars * 0.018
    if radii_sorted[i] > min_r_for_label:
        font_scale = min(1.0, radii_sorted[i] / 1.4)
        label_fontsize = max(11, int(15 * font_scale))
        value_fontsize = max(10, int(13 * font_scale))

        # Determine text color based on background brightness
        bg_color = colors_sorted[i]
        text_color = "#1a1a2e" if bg_color == "#FFD43B" else "white"

        # Wrap long labels for smaller circles
        display_label = labels_sorted[i]
        is_wrapped = False
        if " " in display_label and radii_sorted[i] < 1.0:
            display_label = display_label.replace(" ", "\n")
            is_wrapped = True

        # Adjust vertical offsets for wrapped vs single-line labels
        label_y_offset = 0.05 if is_wrapped else 0.12
        value_y_offset = -0.35 if is_wrapped else -0.22

        ax.text(
            positions[i, 0],
            positions[i, 1] + radii_sorted[i] * label_y_offset,
            display_label,
            ha="center",
            va="center",
            fontsize=label_fontsize,
            fontweight="bold",
            color=text_color,
            zorder=3,
        )
        ax.text(
            positions[i, 0],
            positions[i, 1] + radii_sorted[i] * value_y_offset,
            f"${values_sorted[i]}K",
            ha="center",
            va="center",
            fontsize=value_fontsize,
            color=text_color,
            alpha=0.85,
            zorder=3,
        )
    else:
        small_circles.append(i)

# External labels with leader lines for small circles
for i in small_circles:
    cx, cy = positions[i, 0], positions[i, 1]
    r = radii_sorted[i]

    # Find direction away from center for label placement
    angle = np.arctan2(cy, cx)
    offset_dist = r + 0.6
    lx = cx + offset_dist * np.cos(angle)
    ly = cy + offset_dist * np.sin(angle)

    ax.annotate(
        f"{labels_sorted[i]}\n${values_sorted[i]}K",
        xy=(cx, cy),
        xytext=(lx, ly),
        fontsize=11,
        fontweight="bold",
        color="#333333",
        ha="center",
        va="center",
        arrowprops={"arrowstyle": "-", "color": "#666666", "lw": 1.2, "shrinkA": 0, "shrinkB": 2},
        zorder=4,
    )

# Axis limits with padding
all_x = positions[:, 0]
all_y = positions[:, 1]
max_r = radii_sorted.max()
padding = 1.2
ax.set_xlim(all_x.min() - max_r - padding, all_x.max() + max_r + padding)
ax.set_ylim(all_y.min() - max_r - padding, all_y.max() + max_r + padding)
ax.set_aspect("equal")
ax.axis("off")

# Title
ax.set_title(
    "Department Budget Allocation · bubble-packed · matplotlib · pyplots.ai", fontsize=24, fontweight="bold", pad=20
)

# Legend for group colors
legend_handles = [
    mpatches.Patch(facecolor=color, edgecolor="white", linewidth=1.5, label=group)
    for group, color in group_colors.items()
]
ax.legend(
    handles=legend_handles,
    loc="lower right",
    fontsize=16,
    framealpha=0.9,
    edgecolor="#cccccc",
    fancybox=True,
    borderpad=0.8,
    handlelength=1.5,
    handleheight=1.2,
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
