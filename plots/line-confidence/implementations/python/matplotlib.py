""" anyplot.ai
line-confidence: Line Plot with Confidence Interval
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-09
"""

import sys


sys.path.pop(0)

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme-adaptive colors
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data - Simulated temperature forecast with 95% confidence interval
np.random.seed(42)
days = np.arange(1, 31)  # 30 days forecast

# Central forecast (mean temperature with slight trend)
base_temp = 15 + 0.3 * days + 3 * np.sin(days / 5)
y = base_temp + np.random.randn(30) * 0.5

# Confidence interval widens over time (typical for forecasts)
uncertainty = 1.5 + 0.15 * days
y_lower = y - uncertainty
y_upper = y + uncertainty

# Create plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Shaded confidence band (contrasting color with semi-transparent alpha)
# Use sky blue (#2ABCCD) for the band to contrast with green line
ax.fill_between(days, y_lower, y_upper, alpha=0.25, color="#2ABCCD", label="95% Confidence Interval")

# Central trend line (prominent, brand green)
ax.plot(days, y, color="#009E73", linewidth=3, label="Forecast Mean")

# Styling
ax.set_xlabel("Days Ahead", fontsize=20, color=INK)
ax.set_ylabel("Temperature (°C)", fontsize=20, color=INK)
ax.set_title("Temperature Forecast with 95% Confidence Interval", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT, labelcolor=INK_SOFT)

# Spine styling
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color(INK_SOFT)
    ax.spines[spine].set_linewidth(0.8)

# Grid (subtle, y-axis only)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Legend with theme-adaptive styling
leg = ax.legend(fontsize=16, loc="upper left", framealpha=0.95)
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    leg.get_frame().set_linewidth(0.8)
    for text in leg.get_texts():
        text.set_color(INK_SOFT)

# Set axis limits for clean display
ax.set_xlim(1, 30)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
