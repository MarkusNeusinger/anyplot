""" anyplot.ai
donut-nested: Nested Donut Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-08
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (positions 1-4 for departments)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

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

# Color palette - use Okabe-Ito base with varying opacity per subcategory
dept_colors = {}
for i, dept in enumerate(departments):
    base_color = IMPRINT[i]
    num_cats = len(categories[dept])
    dept_colors[dept] = [base_color] * num_cats

inner_colors = [IMPRINT[i] for i in range(len(departments))]
outer_colors = []
for dept in departments:
    outer_colors.extend(dept_colors[dept])

# Create figure - square format for pie/donut charts (3600x3600 px at 300 dpi = 12x12 inches)
fig, ax = plt.subplots(figsize=(12, 12), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Inner ring (departments)
inner_wedge_props = {"width": 0.4, "edgecolor": PAGE_BG, "linewidth": 2}
wedges_inner, texts_inner = ax.pie(
    dept_totals, radius=0.6, colors=inner_colors, wedgeprops=inner_wedge_props, startangle=90
)

# Outer ring (categories within departments) - use varying opacity for subcategories
outer_wedge_props = {"width": 0.35, "edgecolor": PAGE_BG, "linewidth": 1.5}
outer_colors_with_alpha = []
for dept, color in zip(departments, inner_colors, strict=True):
    num_cats = len(categories[dept])
    alphas = np.linspace(0.5, 1.0, num_cats)
    for alpha in alphas:
        # Convert hex to RGB, apply alpha
        rgb = tuple(int(color[j : j + 2], 16) / 255.0 for j in (1, 3, 5))
        outer_colors_with_alpha.append((*rgb, alpha))

wedges_outer, texts_outer = ax.pie(
    outer_values, radius=1.0, colors=outer_colors_with_alpha, wedgeprops=outer_wedge_props, startangle=90
)

# Add labels for inner ring (departments with totals)
for wedge, dept, total in zip(wedges_inner, departments, dept_totals, strict=True):
    angle = (wedge.theta2 + wedge.theta1) / 2
    x = 0.42 * np.cos(np.radians(angle))
    y = 0.42 * np.sin(np.radians(angle))
    ax.text(x, y, f"{dept}\n${total}K", ha="center", va="center", fontsize=16, fontweight="bold", color=INK)

# Add labels for outer ring (larger segments only)
for wedge, label, value in zip(wedges_outer, outer_labels, outer_values, strict=True):
    if value >= 100:  # Only label segments >= $100K
        angle = (wedge.theta2 + wedge.theta1) / 2
        x = 0.82 * np.cos(np.radians(angle))
        y = 0.82 * np.sin(np.radians(angle))
        ax.text(x, y, f"{label}\n${value}K", ha="center", va="center", fontsize=12, color=INK)

# Create custom legend for all categories
legend_elements = []
for i, dept in enumerate(departments):
    for cat in categories[dept]:
        legend_elements.append(
            plt.Rectangle((0, 0), 1, 1, facecolor=IMPRINT[i], edgecolor=INK_SOFT, label=f"{dept}: {cat}")
        )

ax.legend(
    handles=legend_elements,
    loc="center left",
    bbox_to_anchor=(1.0, 0.5),
    fontsize=14,
    frameon=True,
    fancybox=False,
    edgecolor=INK_SOFT,
    facecolor=ELEVATED_BG,
)
plt.setp(ax.get_legend().get_texts(), color=INK_SOFT)

# Title
ax.set_title("donut-nested · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=20)

# Equal aspect ratio for circular donuts
ax.set_aspect("equal")

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
