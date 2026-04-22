""" pyplots.ai
treemap-basic: Basic Treemap
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import squarify
from matplotlib.patches import Patch, Rectangle


# Random seed for reproducibility
np.random.seed(42)

# Set seaborn style for clean aesthetics
sns.set_style("white")

# Data - Budget allocation by department and project
data = [
    ("Engineering", "Product Dev", 45),
    ("Engineering", "Infrastructure", 25),
    ("Engineering", "QA", 15),
    ("Sales", "Enterprise", 35),
    ("Sales", "SMB", 25),
    ("Sales", "Partners", 15),
    ("Marketing", "Digital", 30),
    ("Marketing", "Events", 20),
    ("Operations", "Logistics", 20),
    ("Operations", "Support", 15),
    ("HR", "Recruiting", 12),
    ("HR", "Training", 8),
]

categories = [d[0] for d in data]
subcategories = [d[1] for d in data]
values = [d[2] for d in data]

# Use seaborn color palette for main categories
unique_categories = ["Engineering", "Sales", "Marketing", "Operations", "HR"]
palette = sns.color_palette("colorblind", n_colors=len(unique_categories))
category_colors = dict(zip(unique_categories, palette, strict=True))

# Normalize values to fill the rectangle area (160x90 to match figsize aspect ratio)
width, height = 160, 90

# Use squarify to compute rectangle positions
rects = squarify.normalize_sizes(values, width, height)
rects = squarify.squarify(rects, 0, 0, width, height)

# Create plot (4800x2700 px at 300 dpi)
fig, ax = plt.subplots(figsize=(16, 9))

# Count items per category to compute depth shading
category_counts = {}
category_indices = {}
for i, cat in enumerate(categories):
    if cat not in category_counts:
        category_counts[cat] = 0
        category_indices[cat] = []
    category_indices[cat].append(i)
    category_counts[cat] += 1

# Draw rectangles with depth-based shading (hierarchy visualization)
for i, rect in enumerate(rects):
    cat = categories[i]
    base_color = category_colors[cat]

    # Create depth shading: use seaborn's light_palette to generate shades
    # Larger values (more prominent) get darker colors, smaller get lighter
    cat_items = category_indices[cat]
    rank_in_category = cat_items.index(i)
    num_in_category = len(cat_items)

    # Generate shades using seaborn's light_palette
    shades = sns.light_palette(base_color, n_colors=num_in_category + 2, reverse=True)
    shade_color = shades[rank_in_category + 1]  # Skip the darkest (index 0)

    rectangle = Rectangle(
        (rect["x"], rect["y"]), rect["dx"], rect["dy"], facecolor=shade_color, edgecolor="white", linewidth=3, alpha=0.9
    )
    ax.add_patch(rectangle)

    # Add label for larger rectangles
    area = rect["dx"] * rect["dy"]
    if area > 150:
        # Determine text color based on luminance
        r_val, g_val, b_val = shade_color[:3]
        luminance = 0.299 * r_val + 0.587 * g_val + 0.114 * b_val
        text_color = "white" if luminance < 0.5 else "black"
        fontsize = min(18, max(12, int(area**0.35)))

        label = f"{subcategories[i]}\n${values[i]}M"
        ax.text(
            rect["x"] + rect["dx"] / 2,
            rect["y"] + rect["dy"] / 2,
            label,
            ha="center",
            va="center",
            fontsize=fontsize,
            fontweight="bold",
            color=text_color,
        )

# Set axis limits and remove axes
ax.set_xlim(0, width)
ax.set_ylim(0, height)
ax.axis("off")
ax.set_aspect("equal")

# Title
ax.set_title(
    "Budget Allocation by Department · treemap-basic · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20
)

# Legend for categories using seaborn palette colors
legend_handles = [Patch(facecolor=category_colors[cat], label=cat, edgecolor="white") for cat in unique_categories]
ax.legend(
    handles=legend_handles,
    loc="upper center",
    fontsize=14,
    framealpha=0.95,
    edgecolor="gray",
    ncol=5,
    bbox_to_anchor=(0.5, -0.02),
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
