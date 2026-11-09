"""anyplot.ai
residual-plot: Residual Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.nonparametric.smoothers_lowess import lowess


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — residuals take brand green, outliers the matte-red error anchor
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]
OUTLIER_RED = IMPRINT_PALETTE[4]
TREND_BLUE = IMPRINT_PALETTE[2]

# Constants
OUTLIER_SD = 2  # residuals beyond this many standard deviations count as outliers

# Columns: set these to your table's column names
Y_TRUE = "Observed value"  # role: y_true
Y_PRED = "Fitted value"  # role: y_pred

# Data: replace this block with your own table, for example df = pd.read_csv("predictions.csv")
np.random.seed(42)
x = np.linspace(0, 10, 150)
observed = 2.5 * x + 0.3 * x**2 + np.random.randn(150) * 3  # quadratic truth, so a linear fit leaves a curve
slope, intercept = np.polyfit(x, observed, 1)
df = pd.DataFrame({Y_TRUE: observed, Y_PRED: intercept + slope * x})

# Plot: reads only df and the constants above
residuals = df[Y_TRUE] - df[Y_PRED]
sd = residuals.std(ddof=0)
is_outlier = residuals.abs() > OUTLIER_SD * sd
trend = lowess(residuals, df[Y_PRED], frac=0.5)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.axhspan(-OUTLIER_SD * sd, OUTLIER_SD * sd, color=INK_MUTED, alpha=0.08, linewidth=0, label=f"±{OUTLIER_SD}σ band")
for sign in (-1, 1):
    ax.axhline(sign * OUTLIER_SD * sd, color=INK_MUTED, linewidth=1.0, linestyle="--", alpha=0.8)
ax.axhline(0, color=INK, linewidth=1.5, label="Zero residual", zorder=2)

ax.scatter(
    df.loc[~is_outlier, Y_PRED],
    residuals[~is_outlier],
    s=60,
    alpha=0.7,
    color=BRAND,
    edgecolors=PAGE_BG,
    linewidth=0.5,
    label="Residuals",
    zorder=3,
)
ax.scatter(
    df.loc[is_outlier, Y_PRED],
    residuals[is_outlier],
    s=90,
    alpha=0.95,
    color=OUTLIER_RED,
    edgecolors=PAGE_BG,
    linewidth=0.8,
    label=f"Outliers (>{OUTLIER_SD}σ)",
    zorder=4,
)
ax.plot(trend[:, 0], trend[:, 1], color=TREND_BLUE, linewidth=2.5, label="LOWESS trend", zorder=5)

# Style
title = "residual-plot · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12
ax.set_title(title, fontsize=title_fontsize, fontweight="bold", color=INK)
ax.set_xlabel(Y_PRED, fontsize=10, color=INK)
ax.set_ylabel(f"Residual ({Y_TRUE.lower()} − {Y_PRED.lower()})", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, length=0)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

leg = ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=5, frameon=True)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
