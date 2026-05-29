""" anyplot.ai
curve-bias-variance-tradeoff: Bias-Variance Tradeoff Curve
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-28
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — semantic assignments for bias-variance curves
C_BIAS = "#009E73"  # position 1 brand green — decreasing / improving direction
C_VAR = "#C475FD"  # position 2 lavender — increasing / overfitting direction
C_TOTAL = "#AE3030"  # position 5 matte red — semantic: error / loss
C_IRRED = INK_MUTED  # adaptive muted — baseline / noise floor

# Data — theoretical curves
complexity = np.linspace(0.5, 10, 100)
bias_squared = 2.5 / (1 + 0.5 * complexity)
variance = 0.05 * complexity**1.5
irreducible_error = np.full_like(complexity, 0.3)
total_error = bias_squared + variance + irreducible_error

optimal_idx = np.argmin(total_error)
optimal_complexity = complexity[optimal_idx]
optimal_error = total_error[optimal_idx]

# Seaborn theme
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
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
fig.set_facecolor(PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Shaded underfitting / overfitting zones (behind curves)
ax.axvspan(0.5, optimal_complexity, alpha=0.07, color=C_BIAS, zorder=0)
ax.axvspan(optimal_complexity, 10, alpha=0.07, color=C_VAR, zorder=0)

# Main curves via seaborn lineplot
sns.lineplot(x=complexity, y=bias_squared, color=C_BIAS, linewidth=2.5, label="Bias²", ax=ax)
sns.lineplot(x=complexity, y=variance, color=C_VAR, linewidth=2.5, label="Variance", ax=ax)
sns.lineplot(
    x=complexity, y=irreducible_error, color=C_IRRED, linewidth=2.0, linestyle="--", label="Irreducible Error", ax=ax
)
sns.lineplot(x=complexity, y=total_error, color=C_TOTAL, linewidth=3.5, label="Total Error", ax=ax)

# Optimal complexity marker
ax.axvline(x=optimal_complexity, color=C_BIAS, linestyle=":", linewidth=1.8, alpha=0.7, zorder=2)
ax.scatter([optimal_complexity], [optimal_error], s=80, color=C_BIAS, zorder=6, edgecolor=PAGE_BG, linewidth=1.5)

# Direct curve annotations
ax.annotate("Bias²", xy=(1.4, bias_squared[9] + 0.13), fontsize=8, color=C_BIAS, fontweight="bold")
ax.annotate("Variance", xy=(8.2, variance[80] + 0.13), fontsize=8, color=C_VAR, fontweight="bold")
ax.annotate("Total Error", xy=(7.3, total_error[70] + 0.18), fontsize=8, color=C_TOTAL, fontweight="bold")
ax.annotate("Irreducible\nError", xy=(1.8, 0.40), fontsize=7, color=C_IRRED, fontweight="bold")

# Zone labels
ax.text(2.1, 2.75, "Underfitting\n(High Bias)", fontsize=7, ha="center", color=C_BIAS, alpha=0.8, fontweight="bold")
ax.text(7.8, 2.75, "Overfitting\n(High Variance)", fontsize=7, ha="center", color=C_VAR, alpha=0.8, fontweight="bold")

# Optimal complexity annotation
ax.annotate(
    "Optimal\nComplexity",
    xy=(optimal_complexity, optimal_error),
    xytext=(optimal_complexity + 1.0, optimal_error + 0.5),
    fontsize=7,
    ha="left",
    color=C_BIAS,
    fontweight="bold",
    arrowprops={"arrowstyle": "->", "color": C_BIAS, "lw": 1.5},
)

# Formula box — bottom-right to avoid legend overlap
ax.text(
    0.99,
    0.03,
    r"Total Error = Bias² + Variance + $\epsilon$",
    transform=ax.transAxes,
    fontsize=7,
    verticalalignment="bottom",
    horizontalalignment="right",
    bbox={"boxstyle": "round,pad=0.4", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.9},
    color=INK,
)

# Title and axis labels
title = "curve-bias-variance-tradeoff · python · seaborn · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_fontsize = max(8, round(12 * ratio))

ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK)
ax.set_xlabel("Model Complexity", fontsize=10, color=INK)
ax.set_ylabel("Prediction Error", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

ax.set_xlim(0.5, 10)
ax.set_ylim(0, 3.8)
ax.set_xticks([1, 3, 5, 7, 9])
ax.set_xticklabels(["Low", "", "Medium", "", "High"])

# Subtle y-axis grid
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

# Spines — L-shaped frame
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for sp in ("left", "bottom"):
    ax.spines[sp].set_color(INK_SOFT)

# Legend — top center, 4 columns
ax.legend(loc="upper center", fontsize=8, ncol=4, framealpha=0.9, bbox_to_anchor=(0.5, 0.99))

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
