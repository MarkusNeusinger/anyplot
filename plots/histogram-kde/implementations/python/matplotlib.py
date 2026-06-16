""" anyplot.ai
histogram-kde: Histogram with KDE Overlay
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-06
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import gaussian_kde


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"
ACCENT = "#C475FD"

# Data - simulate stock daily returns (realistic financial data)
np.random.seed(42)
normal_returns = np.random.normal(0.0005, 0.015, 800)
volatile_returns = np.random.normal(-0.002, 0.035, 150)
extreme_returns = np.random.normal(0.001, 0.05, 50)
returns = np.concatenate([normal_returns, volatile_returns, extreme_returns])
np.random.shuffle(returns)
returns = returns * 100

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Histogram with density scaling (semi-transparent, brand color)
ax.hist(returns, bins=40, density=True, alpha=0.5, color=BRAND, edgecolor=INK_SOFT, linewidth=1.5, label="Histogram")

# KDE overlay using scipy
kde = gaussian_kde(returns)
x_range = np.linspace(returns.min() - 0.5, returns.max() + 0.5, 500)
kde_values = kde(x_range)
ax.plot(x_range, kde_values, color=ACCENT, linewidth=4, label="KDE")

# Style
ax.set_xlabel("Daily Return (%)", fontsize=20, color=INK)
ax.set_ylabel("Density", fontsize=20, color=INK)
ax.set_title("histogram-kde · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.legend(fontsize=16, loc="upper right")
leg = ax.get_legend()
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK_SOFT)

# Save
plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
