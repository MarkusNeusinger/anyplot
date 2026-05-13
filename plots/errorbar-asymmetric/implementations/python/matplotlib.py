""" anyplot.ai
errorbar-asymmetric: Asymmetric Error Bars Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-13
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
BRAND = "#009E73"  # Okabe-Ito position 1

# Data: Monthly sales performance with asymmetric confidence intervals
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"]
sales = np.array([42, 55, 48, 61, 73, 68, 82, 78])

# Asymmetric errors: lower bound smaller (more confident), upper larger (more uncertain)
error_lower = np.array([5, 8, 6, 9, 7, 10, 8, 6])
error_upper = np.array([12, 15, 10, 18, 14, 20, 16, 12])

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Error bars with asymmetric magnitudes
ax.errorbar(
    months,
    sales,
    yerr=[error_lower, error_upper],
    fmt="o",
    markersize=22,
    color=BRAND,
    ecolor=BRAND,
    elinewidth=3,
    capsize=10,
    capthick=3,
    alpha=0.9,
    label="Median with 10th-90th percentile bounds",
)

# Subtle fill to show confidence region
x_positions = np.arange(len(months))
ax.fill_between(x_positions, sales - error_lower, sales + error_upper, alpha=0.15, color=BRAND)

# Style
ax.set_xlabel("Month", fontsize=20, color=INK)
ax.set_ylabel("Sales (thousands USD)", fontsize=20, color=INK)
ax.set_title("errorbar-asymmetric · matplotlib · anyplot.ai", fontsize=24, color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK_SOFT)

# Legend
leg = ax.legend(fontsize=16, loc="upper left", framealpha=0.95)
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    for text in leg.get_texts():
        text.set_color(INK_SOFT)

ax.set_ylim(0, 120)
plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
