""" anyplot.ai
bar-error: Bar Chart with Error Bars
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-10
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

# Data: A/B test results comparing feature variants with confidence intervals
np.random.seed(42)
categories = ["Control", "Variant A", "Variant B", "Variant C", "Variant D"]
values = [12.3, 15.8, 14.2, 18.5, 11.7]
errors = [1.2, 2.1, 1.5, 2.8, 1.0]

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

x = np.arange(len(categories))
bar_width = 0.6

bars = ax.bar(x, values, bar_width, color=BRAND, edgecolor=INK_SOFT, linewidth=1.5)
ax.errorbar(x, values, yerr=errors, fmt="none", ecolor=INK_SOFT, elinewidth=2.5, capsize=8, capthick=2)

# Labels and styling
ax.set_xlabel("Test Group", fontsize=20, color=INK)
ax.set_ylabel("Conversion Rate (%)", fontsize=20, color=INK)
ax.set_title("bar-error · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=16, color=INK_SOFT)
ax.tick_params(axis="y", labelsize=16, colors=INK_SOFT)

# Spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Grid
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

# Annotation
ax.annotate(
    "Error bars: 95% CI",
    xy=(0.98, 0.02),
    xycoords="axes fraction",
    fontsize=14,
    ha="right",
    va="bottom",
    color=INK_SOFT,
    bbox={
        "boxstyle": "round,pad=0.5",
        "facecolor": ELEVATED_BG,
        "edgecolor": INK_SOFT,
        "alpha": 0.9,
        "linewidth": 1,
    },
)

ax.set_ylim(0, max(values) * 1.3)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
