""" anyplot.ai
line-confidence: Line Plot with Confidence Interval
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

# Set theme for seaborn
sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Data - Daily temperature forecast with growing confidence interval
np.random.seed(42)

# Generate daily forecast for 30 days
days = np.arange(1, 31)

# Create a realistic temperature trend with daily variation
base_temp = 18 + days * 0.3  # Warming trend
daily_cycle = 3 * np.sin(2 * np.pi * days / 7)  # Weekly pattern
noise = np.random.randn(len(days)) * 1.5

# Central forecast
y_forecast = base_temp + daily_cycle + noise

# Confidence interval - widens as forecast horizon extends
uncertainty = 1.5 + days * 0.15  # Growing uncertainty
y_lower = y_forecast - 1.96 * uncertainty
y_upper = y_forecast + 1.96 * uncertainty

# Create plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)

# Plot confidence band using fill_between
ax.fill_between(days, y_lower, y_upper, alpha=0.25, color=BRAND, label="95% Confidence Interval")

# Plot central line
ax.plot(days, y_forecast, color=BRAND, linewidth=3, label="Forecast", marker="o", markersize=5)

# Style
ax.set_xlabel("Day", fontsize=20, color=INK)
ax.set_ylabel("Temperature (°C)", fontsize=20, color=INK)
ax.set_title(
    "Temperature Forecast · line-confidence · seaborn · anyplot.ai", fontsize=24, color=INK, fontweight="medium"
)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Grid
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, linestyle="-")

# Legend - position to avoid overlap with data
ax.legend(fontsize=16, loc="lower right", framealpha=0.95)

# Set axis limits with padding
ax.set_xlim(0, 31)
ax.set_ylim(min(y_lower) - 2, max(y_upper) + 2)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
