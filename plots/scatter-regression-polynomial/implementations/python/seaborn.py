""" anyplot.ai
scatter-regression-polynomial: Scatter Plot with Polynomial Regression
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-07
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

BRAND = "#009E73"  # Okabe-Ito position 1 — first series
ACCENT = "#C475FD"  # Okabe-Ito position 2 — polynomial curve

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

# Fit polynomial regression (degree 2 - quadratic)
coeffs = np.polyfit(x, y, 2)
poly = np.poly1d(coeffs)
y_pred = poly(x)

# Calculate R² score
ss_res = np.sum((y - y_pred) ** 2)
ss_tot = np.sum((y - np.mean(y)) ** 2)
r2 = 1 - (ss_res / ss_tot)

# Coefficient signs for equation display
a, b, c = coeffs

# Generate smooth curve for plotting
x_smooth = np.linspace(x.min(), x.max(), 200)
y_smooth = poly(x_smooth)

# Calculate confidence band based on residual standard error
residuals = y - y_pred
std_err = np.std(residuals)

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
        "grid.alpha": 0.10,
    },
)

fig, ax = plt.subplots(figsize=(16, 9))

# Scatter points with Okabe-Ito brand color
sns.scatterplot(
    data=df,
    x="Building Age (years)",
    y="Energy Efficiency Score",
    ax=ax,
    s=200,
    alpha=0.65,
    color=BRAND,
    edgecolor=PAGE_BG,
    linewidth=0.5,
    label="Building Data",
)

# Polynomial regression curve
ax.plot(x_smooth, y_smooth, color=ACCENT, linewidth=4, label="Polynomial Fit (degree 2)")

# Confidence band with theme-adaptive fill
ax.fill_between(
    x_smooth,
    y_smooth - 1.96 * std_err,
    y_smooth + 1.96 * std_err,
    color=ACCENT,
    alpha=0.15,
    label="95% Confidence Band",
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
    fontsize=18,
    verticalalignment="top",
    horizontalalignment="right",
    bbox={"boxstyle": "round,pad=0.7", "facecolor": ELEVATED_BG, "alpha": 0.9, "edgecolor": INK_SOFT, "linewidth": 1},
)

# Labels and title
ax.set_xlabel("Building Age (years)", fontsize=20, color=INK)
ax.set_ylabel("Energy Efficiency Score", fontsize=20, color=INK)
ax.set_title("scatter-regression-polynomial · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Legend positioning (upper left to avoid data overlap)
ax.legend(fontsize=16, loc="upper left", framealpha=0.9, facecolor=ELEVATED_BG, edgecolor=INK_SOFT)

# Grid styling
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Spine visibility (L-shaped default)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
