""" anyplot.ai
scatter-regression-polynomial: Scatter Plot with Polynomial Regression
Library: seaborn 0.13.2 | Python 3.13.14
Quality: 87/100 | Updated: 2026-08-11
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # Imprint palette position 1 — first series
ACCENT = "#C475FD"  # Imprint palette position 2 — polynomial curve

# Data: Environmental energy efficiency scenario
np.random.seed(42)
n_points = 90
# Building age (years) vs energy efficiency score
x = np.linspace(0, 25, n_points)
# Quadratic relationship: efficiency peaks at ~12 years, then declines
# y = -0.4x² + 9.6x + 65 + noise (peaks around 80-85 at x≈12, declines to ~45 at x=25)
y = -0.4 * x**2 + 9.6 * x + 65 + np.random.randn(n_points) * 4

# Prepare data for seaborn
df = pd.DataFrame({"Building Age (years)": x, "Energy Efficiency Score": y})

# Coefficients + R² for the annotation (seaborn's regplot fits internally for
# the drawn curve/band, but doesn't expose the fitted params — recompute here)
coeffs = np.polyfit(x, y, 2)
poly = np.poly1d(coeffs)
y_pred = poly(x)
ss_res = np.sum((y - y_pred) ** 2)
ss_tot = np.sum((y - np.mean(y)) ** 2)
r2 = 1 - (ss_res / ss_tot)
a, b, c = coeffs

# Plot setup with theme-adaptive styling
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

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

# Distinctive seaborn feature: regplot's built-in polynomial fit (order=2)
# draws the scatter, the degree-2 curve, and a bootstrapped 95% CI band in
# a single statistically-aware call, rather than hand-rolling numpy fill_between.
sns.regplot(
    data=df,
    x="Building Age (years)",
    y="Energy Efficiency Score",
    order=2,
    ci=95,
    ax=ax,
    scatter_kws={"s": 110, "alpha": 0.65, "color": BRAND, "edgecolor": PAGE_BG, "linewidths": 0.5},
    line_kws={"color": ACCENT, "linewidth": 3},
)

# regplot doesn't label its artists — build a legend from proxy handles
legend_handles = [
    Line2D(
        [0],
        [0],
        marker="o",
        color="none",
        markerfacecolor=BRAND,
        markeredgecolor=PAGE_BG,
        markersize=9,
        alpha=0.65,
        label="Building Data",
    ),
    Line2D([0], [0], color=ACCENT, linewidth=3, label="Polynomial Fit (degree 2)"),
    Patch(facecolor=ACCENT, alpha=0.15, edgecolor="none", label="95% Confidence Band"),
]
ax.legend(
    handles=legend_handles, fontsize=8, loc="upper left", framealpha=0.9, facecolor=ELEVATED_BG, edgecolor=INK_SOFT
)

# Equation and R² annotation with theme-adaptive box
sign_b = "+" if b >= 0 else "-"
sign_c = "+" if c >= 0 else "-"
equation = f"y = {a:.2f}x² {sign_b} {abs(b):.2f}x {sign_c} {abs(c):.2f}"
annotation_text = f"{equation}\nR² = {r2:.3f}"
ax.annotate(
    annotation_text,
    xy=(0.97, 0.97),
    xycoords="axes fraction",
    fontsize=9,
    verticalalignment="top",
    horizontalalignment="right",
    bbox={"boxstyle": "round,pad=0.6", "facecolor": ELEVATED_BG, "alpha": 0.9, "edgecolor": INK_SOFT, "linewidth": 1},
)

# Labels and title
ax.set_xlabel("Building Age (years)", fontsize=10, color=INK)
ax.set_ylabel("Energy Efficiency Score", fontsize=10, color=INK)
ax.set_title(
    "scatter-regression-polynomial · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK
)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

# Grid styling
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

# Spine visibility (L-shaped default)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
