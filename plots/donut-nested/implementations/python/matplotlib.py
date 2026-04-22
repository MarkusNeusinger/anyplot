""" pyplots.ai
donut-nested: Nested Donut Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Budget allocation: departments (inner) and expense categories (outer)
departments = ["Engineering", "Marketing", "Operations", "Sales"]
categories = {
    "Engineering": ["Salaries", "Equipment", "Software"],
    "Marketing": ["Advertising", "Events", "Content"],
    "Operations": ["Facilities", "Utilities", "Maintenance"],
    "Sales": ["Travel", "Commissions", "Training"],
}
values = {
    "Engineering": [450, 120, 80],
    "Marketing": [200, 150, 100],
    "Operations": [180, 90, 60],
    "Sales": [140, 220, 70],
}

# Calculate department totals for inner ring
dept_totals = [sum(values[dept]) for dept in departments]

# Flatten outer ring data while maintaining order
outer_labels = []
outer_values = []
for dept in departments:
    outer_labels.extend(categories[dept])
    outer_values.extend(values[dept])

# Color palette - use consistent color families per department
dept_colors = {
    "Engineering": ["#306998", "#4a8fc2", "#6fb5e8"],  # Python Blue family
    "Marketing": ["#FFD43B", "#ffe066", "#fff099"],  # Python Yellow family
    "Operations": ["#2E7D32", "#4CAF50", "#81C784"],  # Green family
    "Sales": ["#C62828", "#EF5350", "#EF9A9A"],  # Red family
}

inner_colors = [dept_colors[dept][0] for dept in departments]
outer_colors = []
for dept in departments:
    outer_colors.extend(dept_colors[dept])

# Create figure - square format for pie/donut charts (3600x3600 px at 300 dpi = 12x12 inches)
fig, ax = plt.subplots(figsize=(12, 12))

# Inner ring (departments)
inner_wedge_props = {"width": 0.4, "edgecolor": "white", "linewidth": 2}
wedges_inner, texts_inner = ax.pie(
    dept_totals, radius=0.6, colors=inner_colors, wedgeprops=inner_wedge_props, startangle=90
)

# Outer ring (categories within departments)
outer_wedge_props = {"width": 0.35, "edgecolor": "white", "linewidth": 1.5}
wedges_outer, texts_outer = ax.pie(
    outer_values, radius=1.0, colors=outer_colors, wedgeprops=outer_wedge_props, startangle=90
)

# Add labels for inner ring (departments with totals)
for wedge, dept, total in zip(wedges_inner, departments, dept_totals, strict=True):
    angle = (wedge.theta2 + wedge.theta1) / 2
    x = 0.42 * np.cos(np.radians(angle))
    y = 0.42 * np.sin(np.radians(angle))
    ax.text(x, y, f"{dept}\n${total}K", ha="center", va="center", fontsize=14, fontweight="bold", color="white")

# Add labels for outer ring (larger segments only)
for wedge, label, value in zip(wedges_outer, outer_labels, outer_values, strict=True):
    if value >= 100:  # Only label segments >= $100K
        angle = (wedge.theta2 + wedge.theta1) / 2
        x = 0.82 * np.cos(np.radians(angle))
        y = 0.82 * np.sin(np.radians(angle))
        ax.text(
            x,
            y,
            f"{label}\n${value}K",
            ha="center",
            va="center",
            fontsize=11,
            color="white" if value >= 150 else "black",
        )

# Create custom legend for all categories
legend_elements = []
for dept in departments:
    for cat, color in zip(categories[dept], dept_colors[dept], strict=True):
        legend_elements.append(plt.Rectangle((0, 0), 1, 1, facecolor=color, edgecolor="white", label=f"{dept}: {cat}"))

ax.legend(
    handles=legend_elements,
    loc="center left",
    bbox_to_anchor=(1.05, 0.5),
    fontsize=12,
    frameon=True,
    fancybox=True,
    shadow=True,
)

# Title
ax.set_title("donut-nested · matplotlib · pyplots.ai", fontsize=24, fontweight="bold", pad=20)

# Equal aspect ratio for circular donuts
ax.set_aspect("equal")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
