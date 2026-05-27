""" anyplot.ai
radar-multi: Multi-Series Radar Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-07
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first three series)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data: Product comparison across key attributes
categories = ["Performance", "Battery Life", "Camera", "Display", "Build Quality", "Value"]
products = {
    "Product A": [85, 70, 90, 88, 75, 65],
    "Product B": [72, 95, 78, 82, 88, 80],
    "Product C": [90, 60, 85, 75, 70, 90],
}

# Number of variables
n_categories = len(categories)

# Compute angle for each axis
angles = np.linspace(0, 2 * np.pi, n_categories, endpoint=False).tolist()
angles += angles[:1]  # Close the polygon

# Create figure (square format for radar)
fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={"polar": True}, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Plot each product
for idx, (product, values) in enumerate(products.items()):
    values_closed = values + values[:1]  # Close the polygon
    ax.plot(angles, values_closed, "o-", linewidth=3, label=product, color=IMPRINT[idx], markersize=10)
    ax.fill(angles, values_closed, alpha=0.25, color=IMPRINT[idx])

# Set category labels at each axis
ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=18, fontweight="bold", color=INK)

# Set radial grid
ax.set_ylim(0, 100)
ax.set_yticks([20, 40, 60, 80, 100])
ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=16, color=INK_SOFT)

# Grid styling
ax.yaxis.grid(True, linestyle="-", alpha=0.15, linewidth=0.8, color=INK_SOFT)
ax.xaxis.grid(True, linestyle="-", alpha=0.15, linewidth=0.8, color=INK_SOFT)

# Title
ax.set_title("radar-multi · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=40)

# Legend
leg = ax.legend(loc="upper left", bbox_to_anchor=(1.05, 1.0), fontsize=16, framealpha=1.0)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.8)
for text in leg.get_texts():
    text.set_color(INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
