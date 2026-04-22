""" pyplots.ai
donut-nested: Nested Donut Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.patches import Patch


# Data: Regional budget allocation with expense categories
# Inner ring: Regions, Outer ring: Expense categories within each region
regions = ["North America", "Europe", "Asia Pacific", "Latin America"]
categories = ["Salaries", "Marketing", "Operations", "R&D"]

# Values for each region's categories (in millions)
data = {
    "North America": [45, 22, 18, 35],  # Total: 120
    "Europe": [38, 18, 15, 24],  # Total: 95
    "Asia Pacific": [32, 25, 20, 28],  # Total: 105
    "Latin America": [18, 12, 10, 10],  # Total: 50
}

# Calculate totals for inner ring
inner_values = [sum(data[r]) for r in regions]
outer_values = []
for r in regions:
    outer_values.extend(data[r])

# Total budget
total_budget = sum(inner_values)

# Set seaborn style
sns.set_theme(style="white")

# Create figure (square for symmetric donut)
fig, ax = plt.subplots(figsize=(12, 12))

# Define color palettes using seaborn
# Each region gets a gradient of shades
inner_palette = sns.color_palette(["#306998", "#FFD43B", "#4B8BBE", "#7B7B7B"])

# Create outer colors - variations for each region's categories
outer_colors = []
blue_shades = sns.light_palette("#306998", n_colors=5, reverse=True)[:-1]  # North America
yellow_shades = sns.light_palette("#FFD43B", n_colors=5, reverse=True)[:-1]  # Europe
teal_shades = sns.light_palette("#4B8BBE", n_colors=5, reverse=True)[:-1]  # Asia Pacific
gray_shades = sns.light_palette("#7B7B7B", n_colors=5, reverse=True)[:-1]  # Latin America

for shade in blue_shades:
    outer_colors.append(shade)
for shade in yellow_shades:
    outer_colors.append(shade)
for shade in teal_shades:
    outer_colors.append(shade)
for shade in gray_shades:
    outer_colors.append(shade)

# Outer ring (categories within regions)
outer_wedges, _ = ax.pie(
    outer_values,
    radius=1.0,
    colors=outer_colors,
    wedgeprops={"width": 0.35, "edgecolor": "white", "linewidth": 2.5},
    startangle=90,
)

# Inner ring (regions)
inner_wedges, inner_texts = ax.pie(
    inner_values,
    radius=0.6,
    colors=inner_palette,
    wedgeprops={"width": 0.3, "edgecolor": "white", "linewidth": 2.5},
    startangle=90,
    labels=None,
)

# Add center text
ax.text(
    0, 0, f"Total Budget\n${total_budget}M", ha="center", va="center", fontsize=26, fontweight="bold", color="#333333"
)

# Add labels for inner ring (regions with values)
cumsum = 0
for region, val in zip(regions, inner_values, strict=True):
    # Calculate angle for label positioning
    angle = 90 - (cumsum + val / 2) / total_budget * 360
    angle_rad = np.radians(angle)
    # Position at the middle of the wedge
    x = 0.45 * np.cos(angle_rad)
    y = 0.45 * np.sin(angle_rad)
    ax.text(x, y, f"{region}\n${val}M", ha="center", va="center", fontsize=13, fontweight="bold", color="white")
    cumsum += val

# Create legend for regions (inner ring)
region_patches = [
    Patch(facecolor=inner_palette[i], label=f"{regions[i]}", edgecolor="white", linewidth=1)
    for i in range(len(regions))
]

# Create legend for categories with sample colors
category_patches = [
    Patch(facecolor=blue_shades[i], label=categories[i], edgecolor="white", linewidth=1) for i in range(len(categories))
]

# Add legends
legend1 = ax.legend(
    handles=region_patches,
    title="Regions (Inner)",
    loc="upper left",
    bbox_to_anchor=(-0.15, 1.0),
    fontsize=16,
    title_fontsize=18,
    framealpha=0.95,
    edgecolor="#cccccc",
)
ax.add_artist(legend1)

legend2 = ax.legend(
    handles=category_patches,
    title="Categories (Outer)",
    loc="lower left",
    bbox_to_anchor=(-0.15, 0.0),
    fontsize=16,
    title_fontsize=18,
    framealpha=0.95,
    edgecolor="#cccccc",
)

# Title
ax.set_title("donut-nested · seaborn · pyplots.ai", fontsize=28, fontweight="bold", pad=30, color="#333333")

ax.set_aspect("equal")
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
