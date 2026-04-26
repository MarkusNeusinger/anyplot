""" anyplot.ai
lollipop-basic: Basic Lollipop Chart
Library: matplotlib 3.10.9 | Python 3.14.4
Quality: 88/100 | Updated: 2026-04-26
"""

import os

import matplotlib.pyplot as plt
import numpy as np


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND_GREEN = "#009E73"

# Data: Product sales by category
categories = [
    "Electronics",
    "Clothing",
    "Home & Garden",
    "Sports",
    "Books",
    "Toys",
    "Beauty",
    "Automotive",
    "Food & Beverages",
    "Office Supplies",
]
values = [87, 72, 65, 58, 52, 45, 41, 38, 32, 25]

# Sort by value descending for clear ranking
sorted_indices = np.argsort(values)[::-1]
categories = [categories[i] for i in sorted_indices]
values = [values[i] for i in sorted_indices]

fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

x_positions = np.arange(len(categories))
ax.vlines(x_positions, ymin=0, ymax=values, color=BRAND_GREEN, linewidth=2.5)
ax.scatter(x_positions, values, color=BRAND_GREEN, s=300, zorder=3, edgecolors=PAGE_BG, linewidths=1.5)

ax.set_xlabel("Product Category", fontsize=20, color=INK)
ax.set_ylabel("Sales (thousands)", fontsize=20, color=INK)
ax.set_title("lollipop-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)

ax.set_xticks(x_positions)
ax.set_xticklabels(categories, rotation=45, ha="right", fontsize=16)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT, labelcolor=INK_SOFT)

ax.set_ylim(0, max(values) * 1.1)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.15, color=INK, linewidth=0.8)
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
