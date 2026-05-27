""" anyplot.ai
area-stacked: Stacked Area Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 95/100 | Updated: 2026-05-07
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

# Okabe-Ito palette (use positions 1→N)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data: Monthly website traffic sources over 24 months
np.random.seed(42)
months = np.arange(1, 25)

# Simulate traffic growth with more dramatic variation between categories
base_organic = 50000 + np.cumsum(np.random.randn(24) * 1200 + 400)
base_direct = 20000 + np.cumsum(np.random.randn(24) * 600 + 150)
base_social = 10000 + np.cumsum(np.random.randn(24) * 400 + 200)
base_referral = 5000 + np.cumsum(np.random.randn(24) * 200 + 50)

# Ensure all values are positive
organic = np.maximum(base_organic, 5000)
direct = np.maximum(base_direct, 3000)
social = np.maximum(base_social, 2000)
referral = np.maximum(base_referral, 1000)

# Stack data (largest at bottom for easier reading)
categories = ["Organic Search", "Direct", "Social Media", "Referral"]
data = np.vstack([organic, direct, social, referral])

# Create plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.stackplot(months, data, labels=categories, colors=IMPRINT, alpha=0.85)

# X-axis formatting (show as months)
tick_positions = [1, 6, 12, 18, 24]
tick_labels = ["Jan 2023", "Jun 2023", "Dec 2023", "Jun 2024", "Dec 2024"]
ax.set_xticks(tick_positions)
ax.set_xticklabels(tick_labels)

# Labels and styling
ax.set_xlabel("Month", fontsize=20, color=INK)
ax.set_ylabel("Monthly Visitors (count)", fontsize=20, color=INK)
ax.set_title("area-stacked · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Grid
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

# Spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Legend
leg = ax.legend(loc="upper left", fontsize=16)
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    leg.get_frame().set_linewidth(0.8)
    for text in leg.get_texts():
        text.set_color(INK_SOFT)

# Ensure y-axis starts at zero
ax.set_ylim(bottom=0)
ax.set_xlim(1, 24)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
