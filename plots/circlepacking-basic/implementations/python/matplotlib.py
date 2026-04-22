""" pyplots.ai
circlepacking-basic: Circle Packing Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np


# Set random seed for reproducibility
np.random.seed(42)

# Hierarchical data: Company departments with team sizes
# Structure: {name: value} for leaves, {name: {children}} for branches
hierarchy_data = [
    ("Company", None, 0),  # Root
    ("Engineering", "Company", 1),
    ("Product", "Company", 1),
    ("Operations", "Company", 1),
    ("Sales", "Company", 1),
    ("Frontend", "Engineering", 25),
    ("Backend", "Engineering", 35),
    ("DevOps", "Engineering", 15),
    ("QA", "Engineering", 20),
    ("Design", "Product", 18),
    ("Research", "Product", 12),
    ("PM", "Product", 8),
    ("HR", "Operations", 10),
    ("Finance", "Operations", 12),
    ("Legal", "Operations", 6),
    ("Admin", "Operations", 8),
    ("North", "Sales", 22),
    ("South", "Sales", 18),
    ("Intl", "Sales", 28),
]

# Build node structure with computed values
nodes = {}
for name, parent, value in hierarchy_data:
    nodes[name] = {"name": name, "parent": parent, "value": value, "children": []}

# Link children to parents
for name, node in nodes.items():
    if node["parent"]:
        nodes[node["parent"]]["children"].append(name)

# Compute values for branch nodes (sum of children)
for name in ["Engineering", "Product", "Operations", "Sales"]:
    nodes[name]["value"] = sum(nodes[c]["value"] for c in nodes[name]["children"])
nodes["Company"]["value"] = sum(nodes[c]["value"] for c in nodes["Company"]["children"])

# Color scheme by depth level
depth_colors = {
    0: "#306998",  # Python Blue - root
    1: "#FFD43B",  # Python Yellow - departments
    2: "#5BA0D0",  # Light blue - teams
}
depth_alphas = {0: 0.3, 1: 0.7, 2: 0.7}

# Circle packing layout - compute positions
# We'll use a simple analytical approach for cleaner containment
circles = []

# Root circle
root_radius = 280
circles.append({"name": "Company", "x": 0, "y": 0, "radius": root_radius, "depth": 0})

# Department positioning (4 departments in quadrants)
dept_names = ["Engineering", "Product", "Operations", "Sales"]
dept_values = [nodes[d]["value"] for d in dept_names]
total_dept = sum(dept_values)

# Position departments in a ring within root
dept_ring_radius = root_radius * 0.52
dept_angles = [np.pi * 0.75, np.pi * 0.25, -np.pi * 0.25, -np.pi * 0.75]

dept_circles = {}
for i, dept in enumerate(dept_names):
    # Radius proportional to sqrt of value
    dept_radius = np.sqrt(dept_values[i] / total_dept) * root_radius * 0.42
    dept_x = dept_ring_radius * np.cos(dept_angles[i])
    dept_y = dept_ring_radius * np.sin(dept_angles[i])
    circles.append({"name": dept, "x": dept_x, "y": dept_y, "radius": dept_radius, "depth": 1})
    dept_circles[dept] = {"x": dept_x, "y": dept_y, "radius": dept_radius}

# Team positioning within each department
for dept in dept_names:
    children = nodes[dept]["children"]
    if not children:
        continue

    parent = dept_circles[dept]
    child_values = [nodes[c]["value"] for c in children]
    total_child = sum(child_values)
    n_children = len(children)

    # Arrange children in a circle within parent
    child_ring_radius = parent["radius"] * 0.55
    angle_step = 2 * np.pi / n_children
    start_angle = np.pi / 2

    for j, child in enumerate(children):
        child_radius = np.sqrt(child_values[j] / total_child) * parent["radius"] * 0.40
        angle = start_angle + j * angle_step
        child_x = parent["x"] + child_ring_radius * np.cos(angle)
        child_y = parent["y"] + child_ring_radius * np.sin(angle)

        # Ensure child stays within parent boundary
        dist_to_parent_center = np.sqrt((child_x - parent["x"]) ** 2 + (child_y - parent["y"]) ** 2)
        max_dist = parent["radius"] - child_radius - 3  # padding
        if dist_to_parent_center + child_radius > parent["radius"] - 2:
            scale = max_dist / dist_to_parent_center
            child_x = parent["x"] + (child_x - parent["x"]) * scale
            child_y = parent["y"] + (child_y - parent["y"]) * scale

        circles.append({"name": child, "x": child_x, "y": child_y, "radius": child_radius, "depth": 2})

# Create figure (square format for symmetric visualization)
fig, ax = plt.subplots(figsize=(12, 12))

# Draw circles from largest to smallest (painter's algorithm)
circles_sorted = sorted(circles, key=lambda c: -c["radius"])

for circle in circles_sorted:
    color = depth_colors.get(circle["depth"], "#AAAAAA")
    alpha = depth_alphas.get(circle["depth"], 0.7)

    circ = patches.Circle(
        (circle["x"], circle["y"]), circle["radius"], facecolor=color, edgecolor="#2C3E50", linewidth=2.5, alpha=alpha
    )
    ax.add_patch(circ)

    # Add labels for circles that are large enough
    if circle["radius"] > 30:
        fontsize = min(18, max(11, circle["radius"] * 0.25))
        # Dark text on yellow, white on other colors
        text_color = "#1A1A1A" if circle["depth"] == 1 else "#FFFFFF"
        ax.text(
            circle["x"],
            circle["y"],
            circle["name"],
            ha="center",
            va="center",
            fontsize=fontsize,
            fontweight="bold",
            color=text_color,
        )

# Set equal aspect ratio and limits
ax.set_aspect("equal")
padding = root_radius * 0.15
ax.set_xlim(-root_radius - padding, root_radius + padding)
ax.set_ylim(-root_radius - padding, root_radius + padding)

# Remove axes for cleaner visualization
ax.axis("off")

# Title - exact format: {spec-id} · {library} · pyplots.ai
ax.set_title("circlepacking-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="bold", pad=20)

# Legend with correct colors matching actual rendering
legend_elements = [
    patches.Patch(facecolor="#306998", edgecolor="#2C3E50", alpha=0.3, label="Company (Root)"),
    patches.Patch(facecolor="#FFD43B", edgecolor="#2C3E50", alpha=0.7, label="Departments"),
    patches.Patch(facecolor="#5BA0D0", edgecolor="#2C3E50", alpha=0.7, label="Teams"),
]
ax.legend(handles=legend_elements, loc="upper right", fontsize=16, framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
