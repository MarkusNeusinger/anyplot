""" anyplot.ai
lollipop-basic: Basic Lollipop Chart
Library: matplotlib 3.11.0 | Python 3.13.14
Quality: 87/100 | Updated: 2026-07-01
"""

import os

import matplotlib.pyplot as plt
import numpy as np


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

BRAND_GREEN = "#009E73"  # Imprint palette position 1

# Data: product sales by category (thousands), sorted descending
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

sorted_indices = np.argsort(values)[::-1]
categories = [categories[i] for i in sorted_indices]
values = [values[i] for i in sorted_indices]

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

x_positions = np.arange(len(categories))

# ax.stem() — the idiomatic matplotlib lollipop primitive
container = ax.stem(x_positions, values)
plt.setp(container.stemlines, color=BRAND_GREEN, linewidth=2.5)
plt.setp(container.markerline, markerfacecolor=BRAND_GREEN, markeredgecolor=PAGE_BG, markeredgewidth=1.5, markersize=12)
container.baseline.set_visible(False)

# Value labels above each marker
for xi, val in zip(x_positions, values, strict=True):
    ax.text(xi, val + 2, str(val), ha="center", va="bottom", fontsize=7, color=INK_SOFT)

# Style
title = "lollipop-basic · python · matplotlib · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel("Product Category", fontsize=10, color=INK)
ax.set_ylabel("Sales (thousands)", fontsize=10, color=INK)

ax.set_xticks(x_positions)
ax.set_xticklabels(categories, rotation=45, ha="right", fontsize=8)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)

ax.set_ylim(0, max(values) * 1.18)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.15, color=INK, linewidth=0.8)
ax.set_axisbelow(True)

fig.subplots_adjust(left=0.10, right=0.97, top=0.92, bottom=0.22)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
