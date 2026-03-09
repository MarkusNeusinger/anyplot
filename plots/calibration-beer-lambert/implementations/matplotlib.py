"""pyplots.ai
calibration-beer-lambert: Beer-Lambert Calibration Curve
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-03-09
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
se_fit = np.sqrt((1 / n + (conc_fit - conc_mean) ** 2 / np.sum((concentrations - conc_mean) ** 2))) * np.sqrt(
    np.sum((absorbances - slope * concentrations - intercept) ** 2) / (n - 2)
)
t_crit = stats.t.ppf(0.975, n - 2)
prediction_upper = abs_fit + t_crit * se_fit
prediction_lower = abs_fit - t_crit * se_fit

# Unknown sample
unknown_absorbance = 0.32
unknown_concentration = (unknown_absorbance - intercept) / slope

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

ax.fill_between(
    conc_fit, prediction_lower, prediction_upper, alpha=0.15, color="#306998", label="95% Confidence Interval"
)
ax.plot(conc_fit, abs_fit, color="#306998", linewidth=3, label="Linear Fit")
ax.scatter(
    concentrations, absorbances, s=250, color="#306998", edgecolors="white", linewidth=1.5, zorder=5, label="Standards"
)

# Unknown sample lines and marker
ax.plot(
    [unknown_concentration, unknown_concentration],
    [0, unknown_absorbance],
    linestyle="--",
    color="#E85D3A",
    linewidth=2,
    alpha=0.8,
)
ax.plot(
    [0, unknown_concentration],
    [unknown_absorbance, unknown_absorbance],
    linestyle="--",
    color="#E85D3A",
    linewidth=2,
    alpha=0.8,
)
ax.scatter(
    [unknown_concentration],
    [unknown_absorbance],
    s=300,
    color="#E85D3A",
    edgecolors="white",
    linewidth=1.5,
    zorder=6,
    marker="D",
    label="Unknown Sample",
)

# Regression equation annotation
eq_text = f"y = {slope:.4f}x + {intercept:.4f}\nR\u00b2 = {r_squared:.4f}"
ax.text(
    0.05,
    0.92,
    eq_text,
    transform=ax.transAxes,
    fontsize=18,
    verticalalignment="top",
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.9},
)

# Unknown annotation
ax.annotate(
    f"Unknown: {unknown_concentration:.1f} mg/L",
    xy=(unknown_concentration, unknown_absorbance),
    xytext=(unknown_concentration + 1.5, unknown_absorbance + 0.05),
    fontsize=16,
    color="#E85D3A",
    arrowprops={"arrowstyle": "->", "color": "#E85D3A", "lw": 2},
)

# Style
ax.set_xlabel("Concentration (mg/L)", fontsize=20)
ax.set_ylabel("Absorbance", fontsize=20)
ax.set_title("calibration-beer-lambert \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="lower right")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
ax.set_xlim(-0.5, 14)
ax.set_ylim(-0.02, 0.65)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
