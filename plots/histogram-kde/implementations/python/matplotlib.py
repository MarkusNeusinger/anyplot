""" anyplot.ai
histogram-kde: Histogram with KDE Overlay
Library: matplotlib 3.11.1 | Python 3.13.14
Quality: 85/100 | Updated: 2026-08-05
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import gaussian_kde


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1 — ALWAYS first series
ACCENT = "#C475FD"  # Imprint palette position 2 — KDE curve

# Data - simulate stock daily returns blending calm, volatile, and tail-risk regimes
np.random.seed(42)
normal_returns = np.random.normal(0.0005, 0.015, 800)
volatile_returns = np.random.normal(-0.002, 0.035, 150)
extreme_returns = np.random.normal(0.001, 0.05, 50)
returns = np.concatenate([normal_returns, volatile_returns, extreme_returns]) * 100
np.random.shuffle(returns)
mean_return = returns.mean()

# Plot — see default-style-guide.md "Visual Sizing Defaults" for the canvas + sizing values
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Histogram with density scaling (semi-transparent, brand color)
ax.hist(
    returns,
    bins=44,
    density=True,
    alpha=0.5,
    color=BRAND,
    edgecolor=PAGE_BG,
    linewidth=0.6,
    label="Histogram",
    zorder=2,
)

# KDE overlay using scipy, with a soft fill to give the curve visual weight
# and separate it from the discrete bars beneath it
kde = gaussian_kde(returns)
x_range = np.linspace(returns.min() - 0.5, returns.max() + 0.5, 500)
kde_values = kde(x_range)
ax.fill_between(x_range, kde_values, color=ACCENT, alpha=0.15, zorder=1)
ax.plot(x_range, kde_values, color=ACCENT, linewidth=2.5, label="KDE", zorder=3)

# Mean reference line — draws the eye to the distribution's center of mass
ax.axvline(mean_return, color=INK_SOFT, linewidth=1.2, linestyle="--", zorder=4)
ax.annotate(
    f"mean {mean_return:.2f}%",
    xy=(mean_return, kde_values.max()),
    xytext=(6, -2),
    textcoords="offset points",
    fontsize=8,
    color=INK_SOFT,
    va="top",
)

# Style
title = "histogram-kde · python · matplotlib · anyplot.ai"
ax.set_xlabel("Daily Return (%)", fontsize=10, color=INK)
ax.set_ylabel("Density", fontsize=10, color=INK)
ax.set_title(title, fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.legend(fontsize=8, loc="upper right")
leg = ax.get_legend()
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_ylim(bottom=0)

# Save
plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
