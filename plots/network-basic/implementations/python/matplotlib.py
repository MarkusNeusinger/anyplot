"""anyplot.ai
network-basic: Basic Network Graph
Library: matplotlib 3.10.9 | Python 3.14.4
Quality: 84/100 | Updated: 2026-04-27
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette for 4 departments
GROUP_COLORS = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]
GROUP_NAMES = ["Engineering", "Research", "Marketing", "Design"]

# Data: social network of 20 people across 4 company departments
np.random.seed(42)
nodes = [
    {"id": 0, "label": "Alice", "group": 0},
    {"id": 1, "label": "Bob", "group": 0},
    {"id": 2, "label": "Carol", "group": 0},
    {"id": 3, "label": "David", "group": 0},
    {"id": 4, "label": "Eve", "group": 0},
    {"id": 5, "label": "Frank", "group": 1},
    {"id": 6, "label": "Grace", "group": 1},
    {"id": 7, "label": "Henry", "group": 1},
    {"id": 8, "label": "Ivy", "group": 1},
    {"id": 9, "label": "Jack", "group": 1},
    {"id": 10, "label": "Kate", "group": 2},
    {"id": 11, "label": "Leo", "group": 2},
    {"id": 12, "label": "Mia", "group": 2},
    {"id": 13, "label": "Noah", "group": 2},
    {"id": 14, "label": "Olivia", "group": 2},
    {"id": 15, "label": "Paul", "group": 3},
    {"id": 16, "label": "Quinn", "group": 3},
    {"id": 17, "label": "Ryan", "group": 3},
    {"id": 18, "label": "Sara", "group": 3},
    {"id": 19, "label": "Tom", "group": 3},
]

edges = [
    # Engineering internal
    (0, 1),
    (0, 2),
    (1, 2),
    (1, 3),
    (2, 4),
    (3, 4),
    # Research internal
    (5, 6),
    (5, 7),
    (6, 8),
    (7, 8),
    (7, 9),
    (8, 9),
    # Marketing internal
    (10, 11),
    (10, 12),
    (11, 13),
    (12, 13),
    (12, 14),
    (13, 14),
    # Design internal
    (15, 16),
    (15, 17),
    (16, 18),
    (17, 18),
    (17, 19),
    (18, 19),
    # Cross-department bridges
    (0, 5),
    (4, 10),
    (9, 15),
    (14, 19),
    (2, 6),
    (8, 11),
    (13, 16),
]

# Spring layout (force-directed algorithm)
n = len(nodes)
# Initialize by department quadrant so clusters are spatially separated
quadrant_centers = np.array(
    [
        [-0.5, 0.5],  # Engineering: upper-left
        [0.5, 0.5],  # Research: upper-right
        [0.5, -0.5],  # Marketing: lower-right
        [-0.5, -0.5],  # Design: lower-left
    ]
)
positions = np.zeros((n, 2))
for i, node in enumerate(nodes):
    positions[i] = quadrant_centers[node["group"]] + np.random.randn(2) * 0.2
k = 0.4

for iteration in range(150):
    displacement = np.zeros((n, 2))
    for i in range(n):
        for j in range(i + 1, n):
            diff = positions[i] - positions[j]
            dist = max(np.linalg.norm(diff), 0.01)
            force = (k * k / dist) * (diff / dist)
            displacement[i] += force
            displacement[j] -= force
    for src, tgt in edges:
        diff = positions[src] - positions[tgt]
        dist = max(np.linalg.norm(diff), 0.01)
        force = (dist * dist / k) * (diff / dist)
        displacement[src] -= force
        displacement[tgt] += force
    cooling = 1 - iteration / 150
    for i in range(n):
        disp_norm = np.linalg.norm(displacement[i])
        if disp_norm > 0:
            positions[i] += (displacement[i] / disp_norm) * min(disp_norm, 0.1 * cooling)

pos_min = positions.min(axis=0)
pos_max = positions.max(axis=0)
positions = (positions - pos_min) / (pos_max - pos_min + 1e-6) * 0.8 + 0.1
pos = {node["id"]: positions[i] for i, node in enumerate(nodes)}

# Node degrees for size encoding
degrees = {node["id"]: 0 for node in nodes}
for src, tgt in edges:
    degrees[src] += 1
    degrees[tgt] += 1

# Identify cross-department edges for visual emphasis
cross_edge_set = {(src, tgt) for src, tgt in edges if nodes[src]["group"] != nodes[tgt]["group"]}

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

BRIDGE_COLOR = "#E69F00"  # Okabe-Ito amber — distinct cross-department highlight

# Draw curved edges using FancyArrowPatch
for src, tgt in edges:
    is_cross = (src, tgt) in cross_edge_set or (tgt, src) in cross_edge_set
    patch = FancyArrowPatch(
        tuple(pos[src]),
        tuple(pos[tgt]),
        connectionstyle="arc3,rad=0.18",
        arrowstyle="-",
        color=BRIDGE_COLOR if is_cross else INK_SOFT,
        linewidth=2.5 if is_cross else 1.4,
        alpha=0.80 if is_cross else 0.30,
        zorder=1,
    )
    ax.add_patch(patch)

# Draw nodes (size encodes degree)
for node in nodes:
    x, y = pos[node["id"]]
    size = 900 + degrees[node["id"]] * 220
    color = GROUP_COLORS[node["group"]]
    ax.scatter(x, y, s=size, c=color, edgecolors=PAGE_BG, linewidths=2.5, alpha=0.93, zorder=2)

# Draw labels inside nodes
for node in nodes:
    x, y = pos[node["id"]]
    ax.text(x, y, node["label"], fontsize=14, fontweight="bold", ha="center", va="center", color=INK, zorder=3)

# Style
ax.set_title(
    "Social Network · network-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=16
)
ax.set_xlim(-0.05, 1.05)
ax.set_ylim(-0.05, 1.05)
ax.axis("off")

# Legend
legend_handles = [
    ax.scatter([], [], c=color, s=350, edgecolors=PAGE_BG, linewidths=2, label=name)
    for color, name in zip(GROUP_COLORS, GROUP_NAMES, strict=True)
]
leg = ax.legend(handles=legend_handles, loc="upper left", fontsize=16, title="Departments", title_fontsize=18)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_alpha(0.92)
plt.setp(leg.get_texts(), color=INK_SOFT)
leg.get_title().set_color(INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
