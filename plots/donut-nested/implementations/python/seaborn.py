""" anyplot.ai
donut-nested: Nested Donut Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-08
"""

import os
import sys


sys.path.pop(0)

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.patches import Patch


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette - positions 1-4 for parent categories
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data: Regional budget allocation with expense categories
regions = ["North America", "Europe", "Asia Pacific", "Latin America"]
categories = ["Salaries", "Marketing", "Operations", "R&D"]

data = {
    "North America": [45, 22, 18, 35],
    "Europe": [38, 18, 15, 24],
    "Asia Pacific": [32, 25, 20, 28],
    "Latin America": [18, 12, 10, 10],
}

# Calculate totals for inner ring
inner_values = [sum(data[r]) for r in regions]
outer_values = []
for r in regions:
    outer_values.extend(data[r])

total_budget = sum(inner_values)

# Set seaborn style with theme-adaptive colors
sns.set_theme(style="white", rc={"figure.facecolor": PAGE_BG, "axes.facecolor": PAGE_BG, "text.color": INK})

# Create figure (square for symmetric donut)
fig, ax = plt.subplots(figsize=(12, 12), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Create outer colors - lighter shades of each parent category color
outer_colors = []
for i, _region in enumerate(regions):
    parent_color = IMPRINT[i]
    shades = sns.light_palette(parent_color, n_colors=5, reverse=True)[:-1]
    outer_colors.extend(shades)

# Outer ring (categories within regions)
outer_wedges, _ = ax.pie(
    outer_values,
    radius=1.0,
    colors=outer_colors,
    wedgeprops={"width": 0.35, "edgecolor": PAGE_BG, "linewidth": 2.5},
    startangle=90,
)

# Inner ring (regions)
inner_wedges, inner_texts = ax.pie(
    inner_values,
    radius=0.6,
    colors=IMPRINT,
    wedgeprops={"width": 0.3, "edgecolor": PAGE_BG, "linewidth": 2.5},
    startangle=90,
    labels=None,
)

# Add center text
ax.text(0, 0, f"Total Budget\n${total_budget}M", ha="center", va="center", fontsize=26, fontweight="bold", color=INK)

# Add labels for inner ring (regions with values)
cumsum = 0
for region, val in zip(regions, inner_values, strict=True):
    angle = 90 - (cumsum + val / 2) / total_budget * 360
    angle_rad = np.radians(angle)
    x = 0.45 * np.cos(angle_rad)
    y = 0.45 * np.sin(angle_rad)
    ax.text(x, y, f"{region}\n${val}M", ha="center", va="center", fontsize=13, fontweight="bold", color="white")
    cumsum += val

# Create legend for regions (inner ring)
region_patches = [
    Patch(facecolor=IMPRINT[i], label=f"{regions[i]}", edgecolor=INK_SOFT, linewidth=1) for i in range(len(regions))
]

# Create legend for categories with sample colors
category_patches = [
    Patch(
        facecolor=sns.light_palette(IMPRINT[0], n_colors=5, reverse=True)[:-1][i],
        label=categories[i],
        edgecolor=INK_SOFT,
        linewidth=1,
    )
    for i in range(len(categories))
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
    edgecolor=INK_SOFT,
    facecolor=ELEVATED_BG,
    labelcolor=INK,
)
for text in legend1.get_texts():
    text.set_color(INK)
legend1.get_title().set_fontsize(18)
legend1.get_title().set_weight("bold")
legend1.get_title().set_color(INK)
ax.add_artist(legend1)

legend2 = ax.legend(
    handles=category_patches,
    title="Categories (Outer)",
    loc="lower left",
    bbox_to_anchor=(-0.15, 0.0),
    fontsize=16,
    title_fontsize=18,
    framealpha=0.95,
    edgecolor=INK_SOFT,
    facecolor=ELEVATED_BG,
    labelcolor=INK,
)
for text in legend2.get_texts():
    text.set_color(INK)
legend2.get_title().set_fontsize(18)
legend2.get_title().set_weight("bold")
legend2.get_title().set_color(INK)

# Title
ax.set_title("donut-nested · seaborn · anyplot.ai", fontsize=28, fontweight="bold", pad=30, color=INK)

ax.set_aspect("equal")
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
