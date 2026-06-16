""" anyplot.ai
scatter-regression-polynomial: Scatter Plot with Polynomial Regression
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-07
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1 — ALWAYS first series
SECONDARY = "#C475FD"  # Okabe-Ito position 2

# Data - Modeling diminishing returns (economics example)
np.random.seed(42)
x = np.linspace(0, 10, 80)
# Quadratic relationship: y = -0.5x² + 6x + 5 + noise
y = -0.5 * x**2 + 6 * x + 5 + np.random.normal(0, 2, len(x))

# Fit polynomial regression (degree 2 - quadratic)
coeffs = np.polyfit(x, y, 2)
poly = np.poly1d(coeffs)
x_smooth = np.linspace(x.min(), x.max(), 200)
y_fit = poly(x_smooth)

# Calculate R² value
y_pred = poly(x)
ss_res = np.sum((y - y_pred) ** 2)
ss_tot = np.sum((y - np.mean(y)) ** 2)
r_squared = 1 - (ss_res / ss_tot)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Scatter points with transparency
ax.scatter(x, y, s=150, alpha=0.7, color=BRAND, edgecolors=PAGE_BG, linewidth=0.5, label="Data points", zorder=3)

# Confidence band (approximate using residual standard error)
residuals = y - y_pred
std_err = np.std(residuals)
ax.fill_between(
    x_smooth,
    y_fit - 1.96 * std_err,
    y_fit + 1.96 * std_err,
    alpha=0.15,
    color=SECONDARY,
    label="95% confidence band",
    zorder=1,
)

# Polynomial regression curve
ax.plot(x_smooth, y_fit, color=SECONDARY, linewidth=3.5, label="Polynomial fit (degree 2)", zorder=2)

# Format polynomial equation
a, b, c = coeffs
equation = f"y = {a:.2f}x² + {b:.2f}x + {c:.2f}"

# Add R² and equation annotation
annotation_text = f"{equation}\nR² = {r_squared:.3f}"
ax.annotate(
    annotation_text,
    xy=(0.03, 0.97),
    xycoords="axes fraction",
    fontsize=16,
    verticalalignment="top",
    bbox={
        "boxstyle": "round,pad=0.5",
        "facecolor": ELEVATED_BG,
        "edgecolor": INK_SOFT,
        "alpha": 0.9,
    },
    color=INK,
)

# Style
ax.set_xlabel("Investment (units)", fontsize=20, color=INK)
ax.set_ylabel("Return (units)", fontsize=20, color=INK)
ax.set_title("scatter-regression-polynomial · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.grid(True, alpha=0.1, linewidth=0.8, color=INK)

# Legend positioned outside plot area
leg = ax.legend(fontsize=16, loc="upper left", bbox_to_anchor=(0.02, 0.98))
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
