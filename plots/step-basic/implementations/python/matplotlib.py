""" anyplot.ai
step-basic: Basic Step Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 88/100 | Updated: 2026-04-30
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

# Data - monthly cumulative sales figures
np.random.seed(42)
months = np.arange(1, 13)
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

monthly_sales = np.array([45, 52, 48, 61, 55, 72, 68, 85, 78, 92, 88, 105])
cumulative_sales = np.cumsum(monthly_sales)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Filled area under the step for visual emphasis
ax.fill_between(months, cumulative_sales, step="post", alpha=0.12, color=BRAND)

# Step line with 'post' style — value applies from current point until next
ax.step(months, cumulative_sales, where="post", linewidth=3, color=BRAND, label="Cumulative Sales")

# Markers at each data point to highlight discrete change events
ax.scatter(
    months, cumulative_sales, s=200, color=PAGE_BG, edgecolors=BRAND, linewidth=2.5, zorder=5, label="Monthly Totals"
)

# Style
ax.set_xlabel("Month", fontsize=20, color=INK)
ax.set_ylabel("Cumulative Sales (thousands $)", fontsize=20, color=INK)
ax.set_title("step-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)

ax.set_xticks(months)
ax.set_xticklabels(month_labels)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

leg = ax.legend(fontsize=16, loc="upper left")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
