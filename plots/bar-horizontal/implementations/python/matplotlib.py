""" anyplot.ai
bar-horizontal: Horizontal Bar Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-07
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
BRAND = "#009E73"

# Data: Top 10 programming languages by popularity
np.random.seed(42)
categories = ["Python", "JavaScript", "Java", "C++", "TypeScript", "C#", "Go", "Rust", "PHP", "Swift"]
values = [68.2, 62.5, 45.8, 42.1, 38.7, 33.5, 28.4, 25.1, 22.8, 18.3]

# Sort by value for better visual comparison (largest at top)
sorted_indices = np.argsort(values)
categories = [categories[i] for i in sorted_indices]
values = [values[i] for i in sorted_indices]

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Horizontal bar chart
y_positions = np.arange(len(categories))
ax.barh(y_positions, values, height=0.65, color=BRAND, edgecolor="none")

# Value labels at the end of bars
for i, value in enumerate(values):
    ax.text(value + 1.2, i, f"{value:.1f}%", va="center", ha="left", fontsize=16, color=INK)

# Labels and styling
ax.set_xlabel("Popularity (%)", fontsize=20, color=INK)
ax.set_ylabel("Programming Language", fontsize=20, color=INK)
ax.set_title("bar-horizontal · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.set_yticks(y_positions)
ax.set_yticklabels(categories, color=INK_SOFT)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.set_xlim(0, max(values) * 1.2)

# Grid on x-axis only
ax.grid(True, axis="x", alpha=0.1, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
