"""anyplot.ai
residual-plot: Residual Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
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

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
OUTLIER_SD = 2  # residuals beyond this many standard deviations count as outliers

# Columns: set these to your table's column names
OBSERVED = "Observed defect count"  # role: y_true
PREDICTED = "Fitted values (predicted defect count)"  # role: y_pred
RESIDUAL = "Residuals (observed - predicted)"  # role: extra
GROUP = "Residual type"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("predictions.csv")
# Manufacturing quality control: wafer defect counts against process temperature, fitted linearly
np.random.seed(42)
n_samples = 150
temperature = np.random.uniform(700, 1100, n_samples)
y_true = 1000 + 0.5 * temperature + 0.0005 * temperature**2 + np.random.normal(0, 150, n_samples)
slope, intercept = np.polyfit(temperature, y_true, 1)
df = pd.DataFrame({OBSERVED: y_true, PREDICTED: slope * temperature + intercept})

# Plot: reads only df and the constants above
df[RESIDUAL] = df[OBSERVED] - df[PREDICTED]
residual_std = df[RESIDUAL].std(ddof=0)
outlier_label = f"Outlier (|z| > {OUTLIER_SD})"
df[GROUP] = np.where(df[RESIDUAL].abs() > OUTLIER_SD * residual_std, outlier_label, "Normal")
palette = {"Normal": IMPRINT_PALETTE[0], outlier_label: IMPRINT_PALETTE[1]}

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

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Points: outliers get their own hue; alpha keeps the dense middle readable
sns.scatterplot(
    data=df,
    x=PREDICTED,
    y=RESIDUAL,
    hue=GROUP,
    hue_order=[g for g in palette if g in set(df[GROUP])],
    palette=palette,
    s=60,
    alpha=0.75,
    edgecolor=PAGE_BG,
    linewidth=0.4,
    ax=ax,
)

# Quadratic trend of the residuals: reveals the curvature the linear model misses
sns.regplot(
    data=df,
    x=PREDICTED,
    y=RESIDUAL,
    scatter=False,
    order=2,
    ci=None,
    line_kws={"color": INK_SOFT, "linewidth": 2.0, "linestyle": "--", "label": "Trend (2nd order)"},
    ax=ax,
)

# Zero reference line and the +/- SD outlier bands
ax.axhline(0, color=INK, linewidth=1.5, zorder=2, alpha=0.8)
ax.axhline(OUTLIER_SD * residual_std, color=INK_SOFT, linestyle=":", linewidth=1.2, label=f"±{OUTLIER_SD} SD")
ax.axhline(-OUTLIER_SD * residual_std, color=INK_SOFT, linestyle=":", linewidth=1.2)

# Style
ax.set_title("residual-plot · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(PREDICTED, fontsize=10)
ax.set_ylabel(RESIDUAL, fontsize=10)
ax.tick_params(axis="both", labelsize=8)
ax.grid(True, alpha=0.15, linewidth=0.6)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.legend(fontsize=8, loc="upper right", framealpha=0.95)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
