"""anyplot.ai
line-basic: Basic Line Plot
Library: matplotlib | Python 3.13
Quality: pending | Updated: 2026-04-29
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"

# Data - Average monthly temperature across 5 simulated years
np.random.seed(42)
months = np.arange(1, 13)
base_temp = 15 + 12 * np.sin((months - 4) * np.pi / 6)
all_years = base_temp + np.random.randn(5, 12) * 2.5
mean_temp = all_years.mean(axis=0)
std_temp = all_years.std(axis=0)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Year-to-year variability band
ax.fill_between(months, mean_temp - std_temp, mean_temp + std_temp, color=BRAND, alpha=0.15, linewidth=0)

# Mean temperature line with markers
ax.plot(
    months,
    mean_temp,
    linewidth=3,
    color=BRAND,
    marker="o",
    markersize=10,
    markerfacecolor=PAGE_BG,
    markeredgecolor=BRAND,
    markeredgewidth=2,
)

# Style
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
ax.set_xticks(months)
ax.set_xticklabels(month_labels)
ax.tick_params(axis="both", labelsize=16, labelcolor=INK_SOFT, length=0)

ax.set_xlabel("Month", fontsize=20, color=INK)
ax.set_ylabel("Temperature (°C)", fontsize=20, color=INK)
ax.set_title(
    "Monthly Temperature Trend · line-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK
)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.12, linewidth=0.8, color=INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
