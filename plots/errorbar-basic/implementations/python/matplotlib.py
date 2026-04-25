"""anyplot.ai
errorbar-basic: Basic Error Bar Plot
Library: matplotlib | Python 3.13
Quality: pending | Updated: 2026-04-25
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - experimental measurements with associated uncertainties
np.random.seed(42)
categories = ["Control", "Treatment A", "Treatment B", "Treatment C", "Treatment D", "Treatment E"]
x = np.arange(len(categories))
y = np.array([25.3, 38.7, 42.1, 35.8, 48.2, 31.5])

# Asymmetric errors: Treatment C and D have notably different lower/upper bounds
asymmetric_lower = np.array([2.1, 3.5, 2.8, 6.5, 4.8, 2.5])
asymmetric_upper = np.array([2.1, 3.5, 2.8, 2.8, 2.2, 2.5])

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.errorbar(
    x,
    y,
    yerr=[asymmetric_lower, asymmetric_upper],
    fmt="o",
    markersize=15,
    color=BRAND,
    ecolor=BRAND,
    elinewidth=3,
    capsize=10,
    capthick=3,
    markeredgecolor=PAGE_BG,
    markeredgewidth=1.2,
    alpha=0.95,
)

# Style
ax.set_xlabel("Experimental Group", fontsize=20, color=INK)
ax.set_ylabel("Response Value (units)", fontsize=20, color=INK)
ax.set_title("errorbar-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.set_xticks(x)
ax.set_xticklabels(categories)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.set_axisbelow(True)
ax.set_ylim(0, max(y + asymmetric_upper) * 1.15)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
