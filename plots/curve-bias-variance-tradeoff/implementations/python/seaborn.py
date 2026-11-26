"""anyplot.ai
curve-bias-variance-tradeoff: Bias-Variance Tradeoff Curve
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-28
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
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

# Constants
FONT_ON_PLOT = 9

# Column constants
COMPLEXITY = "Model Complexity"  # role: model_complexity
BIAS = "Bias²"  # role: bias_squared
VARIANCE = "Variance"  # role: variance
IRREDUCIBLE = "Irreducible Error"  # role: irreducible_error
TOTAL = "Total Error"  # role: total_error
CURVE = "Curve"  # long-form key for hue / style / size
ERROR = "Prediction Error"  # long-form value column

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

# Data — theoretical curves, one column per curve
complexity = np.linspace(0.5, 10, 100)
bias_squared = 2.5 / (1 + 0.5 * complexity)
variance = 0.05 * complexity**1.5
irreducible_error = np.full_like(complexity, 0.3)
df = pd.DataFrame(
    {
        COMPLEXITY: complexity,
        BIAS: bias_squared,
        VARIANCE: variance,
        IRREDUCIBLE: irreducible_error,
        TOTAL: bias_squared + variance + irreducible_error,
    }
)

# Plot
curves = [BIAS, VARIANCE, IRREDUCIBLE, TOTAL]
long = df.melt(id_vars=COMPLEXITY, value_vars=curves, var_name=CURVE, value_name=ERROR)
wide = df.set_index(COMPLEXITY)
optimal_complexity = wide[TOTAL].idxmin()
optimal_error = wide[TOTAL].min()
x_min, x_max = df[COMPLEXITY].min(), df[COMPLEXITY].max()
y_max = long[ERROR].max() * 1.62
n_curves = len(curves)


def at(name, frac):
    """Return (x, curve value) at a fraction of the complexity range."""
    x = x_min + frac * (x_max - x_min)
    return x, np.interp(x, wide.index, wide[name])


fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

# Shaded underfitting / overfitting zones (behind curves)
ax.axvspan(x_min, optimal_complexity, alpha=0.07, color=C_BIAS, zorder=0)
ax.axvspan(optimal_complexity, x_max, alpha=0.07, color=C_VAR, zorder=0)

# All four curves in one call: hue, dash style and line width all keyed on the curve
sns.lineplot(
    data=long,
    x=COMPLEXITY,
    y=ERROR,
    hue=CURVE,
    style=CURVE,
    size=CURVE,
    hue_order=curves,
    palette=dict(zip(curves, [C_BIAS, C_VAR, C_IRRED, C_TOTAL], strict=True)),
    dashes=dict(zip(curves, ["", "", (4, 2), ""], strict=True)),
    sizes=dict(zip(curves, [2.5, 2.5, 2.0, 3.5], strict=True)),
    errorbar=None,
    ax=ax,
)

# Optimal complexity marker
ax.axvline(x=optimal_complexity, color=C_BIAS, linestyle=":", linewidth=1.8, alpha=0.7, zorder=2)
ax.scatter([optimal_complexity], [optimal_error], s=80, color=C_BIAS, zorder=6, edgecolor=PAGE_BG, linewidth=1.5)

# Direct curve annotations
kw = {"fontsize": FONT_ON_PLOT, "fontweight": "bold"}
for name, frac, lift, color in [
    (BIAS, 0.095, 0.13, C_BIAS),
    (VARIANCE, 0.79, 0.3, C_VAR),
    (TOTAL, 0.685, 0.3, C_TOTAL),
]:
    x, y = at(name, frac)
    ax.annotate(name, xy=(x, y + lift), color=color, **kw)
x, y = at(IRREDUCIBLE, 0.137)
ax.annotate("Irreducible\nError", xy=(x, y + 0.1), color=C_IRRED, **kw)

# Zone labels
zone_y = y_max * 0.72
ax.text(
    x_min + 0.168 * (x_max - x_min), zone_y, "Underfitting\n(High Bias)", ha="center", color=C_BIAS, alpha=0.9, **kw
)
ax.text(
    x_min + 0.768 * (x_max - x_min), zone_y, "Overfitting\n(High Variance)", ha="center", color=C_VAR, alpha=0.9, **kw
)

# Optimal complexity annotation
ax.annotate(
    "Optimal\nComplexity",
    xy=(optimal_complexity, optimal_error),
    xytext=(optimal_complexity + 1.0, optimal_error + 0.5),
    ha="left",
    color=C_BIAS,
    arrowprops={"arrowstyle": "->", "color": C_BIAS, "lw": 1.5},
    **kw,
)

# Formula box — bottom-right to avoid legend overlap
ax.text(
    0.99,
    0.03,
    r"Total Error = Bias² + Variance + Irreducible Error ($\epsilon$)",
    transform=ax.transAxes,
    fontsize=FONT_ON_PLOT,
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
ax.set_xlabel(COMPLEXITY, fontsize=10, color=INK)
ax.set_ylabel(ERROR, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=9, colors=INK_SOFT)

ax.set_xlim(x_min, x_max)
ax.set_ylim(0, y_max)
ax.set_xticks(np.linspace(x_min, x_max, 11)[1:10:2])
ax.set_xticklabels(["Low", "", "Medium", "", "High"])

# Subtle y-axis grid
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

# L-shaped frame
sns.despine(ax=ax)

# Legend — top center, one column per curve
ax.legend(title=None, loc="upper center", fontsize=9, ncol=n_curves, framealpha=0.9, bbox_to_anchor=(0.5, 0.99))

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
