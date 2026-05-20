"""anyplot.ai
histogram-returns-distribution: Returns Distribution Histogram
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-20
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.patches import Patch
from scipy import stats


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

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

np.random.seed(42)
n_days = 504
daily_returns = np.random.normal(loc=0.05, scale=1.5, size=n_days)  # % units

mean_ret = np.mean(daily_returns)
std_ret = np.std(daily_returns)
skewness = stats.skew(daily_returns)
kurtosis = stats.kurtosis(daily_returns)

lower_tail = mean_ret - 2 * std_ret
upper_tail = mean_ret + 2 * std_ret

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

bins = np.linspace(daily_returns.min() - 0.1, daily_returns.max() + 0.1, 32)

# Single histplot on the full dataset so all bars share the same density normalization;
# recolor tail-region bars afterward (two-call approach normalizes each subset independently)
sns.histplot(daily_returns, bins=bins, stat="density", color=OKABE_ITO[0], alpha=0.7, ax=ax)
for patch in ax.patches:
    bin_center = patch.get_x() + patch.get_width() / 2
    if bin_center < lower_tail or bin_center > upper_tail:
        patch.set_facecolor(OKABE_ITO[1])
        patch.set_alpha(0.85)

# Empirical KDE via seaborn (seaborn-native feature for distribution comparison)
sns.kdeplot(daily_returns, ax=ax, color=OKABE_ITO[0], linewidth=1.5, linestyle=":", alpha=0.8)
kde_line = ax.lines[-1]

# Normal distribution curve fitted to the data
x_range = np.linspace(daily_returns.min() - 0.5, daily_returns.max() + 0.5, 300)
normal_pdf = stats.norm.pdf(x_range, mean_ret, std_ret)
ax.plot(x_range, normal_pdf, color=OKABE_ITO[2], linewidth=2.0)
normal_line = ax.lines[-1]

# Vertical dashed lines at ±2σ boundaries
ax.axvline(lower_tail, color=INK_SOFT, linestyle="--", linewidth=1.0, alpha=0.7)
ax.axvline(upper_tail, color=INK_SOFT, linestyle="--", linewidth=1.0, alpha=0.7)

# Statistics text box — header with separator for visual hierarchy
stats_text = (
    f"Statistics\n"
    f"{'─' * 18}\n"
    f"Mean: {mean_ret:.3f}%\n"
    f"Std Dev: {std_ret:.3f}%\n"
    f"Skewness: {skewness:.3f}\n"
    f"Kurtosis: {kurtosis:.3f}"
)
ax.text(
    0.975,
    0.97,
    stats_text,
    transform=ax.transAxes,
    fontsize=7,
    verticalalignment="top",
    horizontalalignment="right",
    bbox={"boxstyle": "round,pad=0.4", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.9},
    color=INK,
)

ax.set_xlabel("Daily Returns (%)", fontsize=10)
ax.set_ylabel("Density", fontsize=10)
ax.set_title("histogram-returns-distribution · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium")
ax.tick_params(axis="both", labelsize=8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Legend: histogram bars first (primary data), then analytical curves; no frame
center_patch = Patch(facecolor=OKABE_ITO[0], alpha=0.7, label="Returns (±2σ)")
tail_patch = Patch(facecolor=OKABE_ITO[1], alpha=0.7, label="Tail regions (>2σ)")
kde_line.set_label("Empirical KDE")
normal_line.set_label("Normal fit")
ax.legend(handles=[center_patch, tail_patch, kde_line, normal_line], fontsize=8, loc="lower left", frameon=False)

ax.yaxis.grid(True, alpha=0.12, linewidth=0.5)
ax.set_axisbelow(True)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
