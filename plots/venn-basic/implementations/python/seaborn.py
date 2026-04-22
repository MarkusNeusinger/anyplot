""" pyplots.ai
venn-basic: Venn Diagram
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-29
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


np.random.seed(42)

# Data - Survey results on programming language preferences
# Set A: Python users, Set B: JavaScript users, Set C: SQL users
set_labels = ["Python", "JavaScript", "SQL"]
set_sizes = [100, 80, 60]  # Total in each group
# Overlaps: AB=30, AC=20, BC=25, ABC=10
intersections = {"AB": 30, "AC": 20, "BC": 25, "ABC": 10}

# Calculate exclusive counts for each region
only_a = set_sizes[0] - intersections["AB"] - intersections["AC"] + intersections["ABC"]
only_b = set_sizes[1] - intersections["AB"] - intersections["BC"] + intersections["ABC"]
only_c = set_sizes[2] - intersections["AC"] - intersections["BC"] + intersections["ABC"]
ab_only = intersections["AB"] - intersections["ABC"]
ac_only = intersections["AC"] - intersections["ABC"]
bc_only = intersections["BC"] - intersections["ABC"]
abc = intersections["ABC"]

# Total unique respondents using inclusion-exclusion principle
total_respondents = sum(set_sizes) - sum(intersections.values()) + intersections["ABC"]

# Set seaborn style with custom context
sns.set_theme(style="white", context="talk", font_scale=1.2)

# Create figure (square for symmetric diagram)
fig, ax = plt.subplots(figsize=(12, 12))

# Get colors from seaborn palette - using colorblind-safe Set2
palette = sns.color_palette("Set2", n_colors=3)
colors = list(palette)

# Circle positions (equilateral triangle arrangement)
r = 1.5  # Circle radius
center_offset = 0.9  # Distance from center

# Calculate centers for three overlapping circles
centers = [
    (0, center_offset),  # Top (A - Python)
    (-center_offset * np.cos(np.pi / 6), -center_offset * np.sin(np.pi / 6)),  # Bottom-left (B - JavaScript)
    (center_offset * np.cos(np.pi / 6), -center_offset * np.sin(np.pi / 6)),  # Bottom-right (C - SQL)
]

# Draw circles with transparency
circles = []
for center, color, label in zip(centers, colors, set_labels, strict=True):
    circle = mpatches.Circle(center, r, alpha=0.4, facecolor=color, edgecolor=color, linewidth=3, label=label)
    ax.add_patch(circle)
    circles.append(circle)

# Position labels outside circles
label_offset = 2.3
label_positions = [
    (0, label_offset),  # Top
    (-label_offset * np.cos(np.pi / 6) - 0.3, -label_offset * np.sin(np.pi / 6) - 0.3),  # Bottom-left
    (label_offset * np.cos(np.pi / 6) + 0.3, -label_offset * np.sin(np.pi / 6) - 0.3),  # Bottom-right
]

for pos, label, size in zip(label_positions, set_labels, set_sizes, strict=True):
    ax.text(
        pos[0],
        pos[1],
        f"{label}\n(n={size})",
        ha="center",
        va="center",
        fontsize=22,
        fontweight="bold",
        color="#333333",
    )

# Add counts to each region
# Region positions (approximate centers of each region)
region_positions = {
    "A": (0, 1.3),  # Only Python
    "B": (-1.2, -0.8),  # Only JavaScript
    "C": (1.2, -0.8),  # Only SQL
    "AB": (-0.55, 0.3),  # Python & JavaScript
    "AC": (0.55, 0.3),  # Python & SQL
    "BC": (0, -0.7),  # JavaScript & SQL
    "ABC": (0, 0),  # All three
}

region_counts = {"A": only_a, "B": only_b, "C": only_c, "AB": ab_only, "AC": ac_only, "BC": bc_only, "ABC": abc}

for region, pos in region_positions.items():
    count = region_counts[region]
    pct = count / total_respondents * 100
    ax.text(
        pos[0],
        pos[1],
        f"{count}\n({pct:.0f}%)",
        ha="center",
        va="center",
        fontsize=20,
        fontweight="bold",
        color="#333333",
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "none", "alpha": 0.8},
    )

# Set axis properties - tighter bounds for better canvas utilization
ax.set_xlim(-3.0, 3.0)
ax.set_ylim(-2.8, 3.0)
ax.set_aspect("equal")
ax.axis("off")

# Title
ax.set_title("venn-basic · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)

# Add subtitle annotation explaining data context (using computed total)
fig.text(
    0.5,
    0.02,
    f"Developer Survey 2024: Language preferences among {total_respondents} respondents",
    ha="center",
    va="bottom",
    fontsize=14,
    style="italic",
    color="#666666",
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
