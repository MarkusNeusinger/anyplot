""" anyplot.ai
bar-diverging: Diverging Bar Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-08
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Product satisfaction survey scores (-100 to +100)
categories = [
    "Customer Support",
    "Product Quality",
    "Pricing",
    "Website Experience",
    "Delivery Speed",
    "Return Policy",
    "Mobile App",
    "Product Range",
    "Payment Options",
    "Brand Trust",
    "Sustainability",
    "Loyalty Program",
]

# Net satisfaction scores (positive = satisfied, negative = dissatisfied)
values = np.array([45, 72, -38, 28, -15, 55, -52, 33, 61, 85, -8, 18])

# Sort by value for better pattern recognition
sorted_indices = np.argsort(values)
categories_sorted = [categories[i] for i in sorted_indices]
values_sorted = values[sorted_indices]

# Create colors using Okabe-Ito palette
# #009E73 (position 1) for positive, #C475FD (position 2) for negative
colors = ["#009E73" if v >= 0 else "#C475FD" for v in values_sorted]

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Create horizontal bars
y_pos = np.arange(len(categories_sorted))
ax.barh(y_pos, values_sorted, color=colors, height=0.7, edgecolor=INK_SOFT, linewidth=0.8)

# Add vertical line at zero
ax.axvline(x=0, color=INK_SOFT, linewidth=2, alpha=0.8)

# Styling
ax.set_yticks(y_pos)
ax.set_yticklabels(categories_sorted, fontsize=16, color=INK_SOFT)
ax.set_xlabel("Net Satisfaction Score", fontsize=20, color=INK)
ax.set_title("bar-diverging · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="x", labelsize=16, colors=INK_SOFT)

# Grid on x-axis only, subtle
ax.xaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK_SOFT)
ax.set_axisbelow(True)

# Add value labels at the end of each bar
for val, y in zip(values_sorted, y_pos, strict=True):
    offset = 3 if val >= 0 else -3
    ha = "left" if val >= 0 else "right"
    ax.text(val + offset, y, f"{val:+d}", va="center", ha=ha, fontsize=14, color=INK, fontweight="bold")

# Set x-axis limits with padding
max_abs = max(abs(values_sorted.min()), abs(values_sorted.max()))
ax.set_xlim(-max_abs - 20, max_abs + 20)

# Remove top and right spines for cleaner look
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Add legend
legend_elements = [
    Patch(facecolor="#009E73", edgecolor=INK_SOFT, label="Positive (Satisfied)"),
    Patch(facecolor="#C475FD", edgecolor=INK_SOFT, label="Negative (Dissatisfied)"),
]
leg = ax.legend(handles=legend_elements, loc="lower right", fontsize=16)
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    leg.get_frame().set_linewidth(0.8)
    plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
