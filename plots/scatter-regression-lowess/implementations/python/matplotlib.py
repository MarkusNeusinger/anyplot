""" anyplot.ai
scatter-regression-lowess: Scatter Plot with LOWESS Regression
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-14
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from statsmodels.nonparametric.smoothers_lowess import lowess


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"
ACCENT = "#C475FD"

# Data - tree height vs age with realistic growth pattern (power law)
np.random.seed(42)
n_points = 150
age = np.linspace(1, 30, n_points)
# Realistic growth curve: power law with decreasing growth rate
height = 20 * (1 - np.exp(-0.15 * age)) + np.random.normal(0, 0.6, n_points)

# Compute LOWESS smoothed curve
lowess_result = lowess(height, age, frac=0.4, return_sorted=True)
age_smooth = lowess_result[:, 0]
height_smooth = lowess_result[:, 1]

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Scatter points
ax.scatter(age, height, s=180, alpha=0.6, color=BRAND, edgecolors=PAGE_BG, linewidth=0.8, label="Observed heights")

# LOWESS regression curve
ax.plot(age_smooth, height_smooth, color=ACCENT, linewidth=4.5, label="LOWESS smoothed trend")

# Style
ax.set_xlabel("Tree Age (years)", fontsize=20, color=INK)
ax.set_ylabel("Height (meters)", fontsize=20, color=INK)
ax.set_title("scatter-regression-lowess · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

leg = ax.legend(fontsize=16, loc="lower right", frameon=True)
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    leg.get_frame().set_linewidth(0.8)
    for text in leg.get_texts():
        text.set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
