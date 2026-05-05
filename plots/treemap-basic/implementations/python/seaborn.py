"""anyplot.ai
treemap-basic: Basic Treemap
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-05-05
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import squarify
from matplotlib.patches import Patch, Rectangle


np.random.seed(42)

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

# Data - Disk usage by storage device and data type (GB)
data = [
    ("SSD-1", "Documents", 120),
    ("SSD-1", "Media", 85),
    ("SSD-1", "Cache", 45),
    ("SSD-2", "Applications", 150),
    ("SSD-2", "System", 60),
    ("HDD-1", "Archives", 320),
    ("HDD-1", "Backups", 280),
    ("HDD-2", "Videos", 410),
    ("HDD-2", "Photos", 190),
    ("Cloud", "Sync", 75),
    ("Cloud", "Versioning", 40),
]

categories = [d[0] for d in data]
subcategories = [d[1] for d in data]
values = [d[2] for d in data]

unique_categories = ["SSD-1", "SSD-2", "HDD-1", "HDD-2", "Cloud"]
category_colors = dict(zip(unique_categories, OKABE_ITO, strict=False))

width, height = 160, 90

rects = squarify.normalize_sizes(values, width, height)
rects = squarify.squarify(rects, 0, 0, width, height)

fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

category_counts = {}
category_indices = {}
for i, cat in enumerate(categories):
    if cat not in category_counts:
        category_counts[cat] = 0
        category_indices[cat] = []
    category_indices[cat].append(i)
    category_counts[cat] += 1

for i, rect in enumerate(rects):
    cat = categories[i]
    base_color = category_colors[cat]

    cat_items = category_indices[cat]
    rank_in_category = cat_items.index(i)
    num_in_category = len(cat_items)

    shades = sns.light_palette(base_color, n_colors=num_in_category + 2, reverse=True)
    shade_color = shades[rank_in_category + 1]

    rectangle = Rectangle(
        (rect["x"], rect["y"]), rect["dx"], rect["dy"], facecolor=shade_color, edgecolor=PAGE_BG, linewidth=3, alpha=0.9
    )
    ax.add_patch(rectangle)

    area = rect["dx"] * rect["dy"]
    if area > 150:
        r_val, g_val, b_val = shade_color[:3]
        luminance = 0.299 * r_val + 0.587 * g_val + 0.114 * b_val
        text_color = INK if luminance > 0.5 else "#FFFFFF"
        fontsize = min(18, max(12, int(area**0.35)))

        label = f"{subcategories[i]}\n{values[i]}GB"
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

ax.set_xlim(0, width)
ax.set_ylim(0, height)
ax.axis("off")
ax.set_aspect("equal")

ax.set_title(
    "Disk Usage by Device · treemap-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=20
)

legend_handles = [Patch(facecolor=category_colors[cat], label=cat, edgecolor=INK_SOFT) for cat in unique_categories]
ax.legend(
    handles=legend_handles,
    loc="upper center",
    fontsize=16,
    framealpha=0.95,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    ncol=5,
    bbox_to_anchor=(0.5, -0.02),
)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
