""" anyplot.ai
rose-basic: Basic Rose Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 80/100 | Updated: 2026-04-30
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

# Apply seaborn theme with full adaptive chrome
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
        "grid.color": INK_SOFT,
        "grid.alpha": 0.12,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Data: Monthly rainfall (mm) showing seasonal patterns
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
rainfall = [89, 72, 95, 112, 135, 168, 142, 125, 98, 76, 82, 91]

# Calculate angles - start at top (12 o'clock position)
n_categories = len(months)
angles = np.linspace(0, 2 * np.pi, n_categories, endpoint=False)
width = 2 * np.pi / n_categories * 0.85

# Create figure with polar projection (square format for radial plot)
fig, ax = plt.subplots(figsize=(12, 12), subplot_kw={"projection": "polar"})
fig.patch.set_facecolor(PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Use seaborn Blues palette for sequential rainfall depth; skip lightest shades
palette = sns.color_palette("Blues", n_colors=n_categories + 3)[3:]

# Plot bars - radius proportional to value
ax.bar(angles, rainfall, width=width, bottom=0, color=palette, edgecolor=PAGE_BG, linewidth=1.5, alpha=0.92)

# Configure polar axis - start at top (12 o'clock), clockwise
ax.set_theta_offset(np.pi / 2)
ax.set_theta_direction(-1)

# Category labels
ax.set_xticks(angles)
ax.set_xticklabels(months, fontsize=20, fontweight="bold", color=INK)

# Radial gridlines and labels
max_val = max(rainfall)
ax.set_ylim(0, max_val * 1.15)
ax.set_yticks([50, 100, 150])
ax.set_yticklabels(["50 mm", "100 mm", "150 mm"], fontsize=14, color=INK_SOFT)

# Grid and spine styling
ax.grid(True, alpha=0.18, linestyle="--", linewidth=1.2, color=INK_SOFT)
ax.spines["polar"].set_visible(False)

# Title
ax.set_title(
    "Monthly Rainfall (mm) · rose-basic · seaborn · anyplot.ai", fontsize=24, fontweight="bold", pad=35, color=INK
)

# Value labels on each bar
for angle, value in zip(angles, rainfall, strict=True):
    ax.text(angle, value + 12, f"{value}", ha="center", va="center", fontsize=14, fontweight="bold", color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
