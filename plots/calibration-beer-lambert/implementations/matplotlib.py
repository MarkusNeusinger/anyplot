""" pyplots.ai
calibration-beer-lambert: Beer-Lambert Calibration Curve
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-09
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats


# Data
np.random.seed(42)
concentrations = np.array([0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0])
molar_absorptivity = 0.045
absorbances = molar_absorptivity * concentrations + np.random.normal(0, 0.008, len(concentrations))
absorbances[0] = 0.003

# Linear regression
slope, intercept, r_value, p_value, std_err = stats.linregress(concentrations, absorbances)
r_squared = r_value**2

# Regression line and prediction interval
conc_fit = np.linspace(-0.5, 14, 200)
abs_fit = slope * conc_fit + intercept

n = len(concentrations)
conc_mean = np.mean(concentrations)
residual_std = np.sqrt(np.sum((absorbances - slope * concentrations - intercept) ** 2) / (n - 2))
se_pred = residual_std * np.sqrt(1 + 1 / n + (conc_fit - conc_mean) ** 2 / np.sum((concentrations - conc_mean) ** 2))
t_crit = stats.t.ppf(0.975, n - 2)
pred_upper = abs_fit + t_crit * se_pred
pred_lower = abs_fit - t_crit * se_pred

# Unknown sample
unknown_absorbance = 0.32
unknown_concentration = (unknown_absorbance - intercept) / slope

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor="#FAFBFC")
ax.set_facecolor("#FAFBFC")

# Prediction interval band
ax.fill_between(
    conc_fit, pred_lower, pred_upper, alpha=0.12, color="#306998", label="95% Prediction Interval", zorder=1
)

# Fit line
ax.plot(conc_fit, abs_fit, color="#306998", linewidth=3, zorder=3, label="Linear Fit")

# Calibration standards with subtle shadow effect
ax.scatter(
    concentrations, absorbances, s=280, color="#306998", edgecolors="white", linewidth=2, zorder=5, label="Standards"
)

# Unknown sample dashed guide lines
ax.plot(
    [unknown_concentration, unknown_concentration],
    [-0.02, unknown_absorbance],
    linestyle="--",
    color="#E85D3A",
    linewidth=1.8,
    alpha=0.6,
    zorder=2,
)
ax.plot(
    [-0.5, unknown_concentration],
    [unknown_absorbance, unknown_absorbance],
    linestyle="--",
    color="#E85D3A",
    linewidth=1.8,
    alpha=0.6,
    zorder=2,
)

# Unknown sample marker
ax.scatter(
    [unknown_concentration],
    [unknown_absorbance],
    s=320,
    color="#E85D3A",
    edgecolors="white",
    linewidth=2,
    zorder=6,
    marker="D",
    label="Unknown Sample",
)

# Regression equation annotation with refined styling
eq_text = f"y = {slope:.4f}x + {intercept:.4f}\nR² = {r_squared:.4f}"
ax.text(
    0.04,
    0.93,
    eq_text,
    transform=ax.transAxes,
    fontsize=18,
    fontfamily="monospace",
    verticalalignment="top",
    bbox={"boxstyle": "round,pad=0.5", "facecolor": "white", "edgecolor": "#306998", "alpha": 0.95, "linewidth": 1.5},
)

# Unknown annotation with refined arrow
ax.annotate(
    f"Unknown: {unknown_concentration:.1f} mg/L",
    xy=(unknown_concentration, unknown_absorbance),
    xytext=(unknown_concentration + 1.8, unknown_absorbance + 0.06),
    fontsize=16,
    fontweight="semibold",
    color="#E85D3A",
    arrowprops={"arrowstyle": "-|>", "color": "#E85D3A", "lw": 2, "mutation_scale": 15},
    zorder=7,
)

# Axis tick markers at unknown values
ax.annotate(
    f"{unknown_concentration:.1f}",
    xy=(unknown_concentration, -0.02),
    fontsize=13,
    color="#E85D3A",
    fontweight="bold",
    ha="center",
    va="top",
)
ax.annotate(
    f"{unknown_absorbance:.2f}",
    xy=(-0.5, unknown_absorbance),
    fontsize=13,
    color="#E85D3A",
    fontweight="bold",
    ha="left",
    va="bottom",
)

# Style
ax.set_xlabel("Concentration (mg/L)", fontsize=20, labelpad=10)
ax.set_ylabel("Absorbance", fontsize=20, labelpad=10)
ax.set_title(
    "calibration-beer-lambert · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=15, color="#2C3E50"
)
ax.tick_params(axis="both", labelsize=16, colors="#555555")
ax.legend(fontsize=16, loc="lower right", framealpha=0.95, edgecolor="#dddddd", fancybox=True)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
for spine in ["bottom", "left"]:
    ax.spines[spine].set_color("#cccccc")
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color="#999999")
ax.xaxis.grid(True, alpha=0.08, linewidth=0.5, color="#999999")
ax.set_xlim(-0.5, 14)
ax.set_ylim(-0.02, 0.65)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="#FAFBFC")
