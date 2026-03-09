""" pyplots.ai
calibration-beer-lambert: Beer-Lambert Calibration Curve
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-09
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats


# Seaborn theme and styling
sns.set_theme(
    style="ticks",
    context="talk",
    font_scale=1.0,
    rc={"axes.spines.top": False, "axes.spines.right": False, "grid.alpha": 0.2, "grid.linewidth": 0.8},
)
palette = sns.color_palette(["#306998", "#E25822"])

# Data
np.random.seed(42)
concentrations = np.array([0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0])
epsilon_l = 0.045
true_absorbance = epsilon_l * concentrations
measured_absorbance = true_absorbance + np.random.normal(0, 0.008, len(concentrations))
measured_absorbance[0] = 0.002

df = pd.DataFrame({"Concentration (mg/L)": concentrations, "Absorbance": measured_absorbance})

# Linear regression for equation display and prediction interval
slope, intercept, r_value, p_value, std_err = stats.linregress(concentrations, measured_absorbance)
r_squared = r_value**2

# Prediction interval (wider than CI, required by spec)
n = len(concentrations)
x_mean = np.mean(concentrations)
fit_x = np.linspace(-0.5, 15.5, 200)
fit_y = slope * fit_x + intercept
residuals = measured_absorbance - (slope * concentrations + intercept)
se_pred = np.sqrt(
    (np.sum(residuals**2) / (n - 2)) * (1 + 1 / n + (fit_x - x_mean) ** 2 / np.sum((concentrations - x_mean) ** 2))
)
t_crit = stats.t.ppf(0.975, df=n - 2)
pred_upper = fit_y + t_crit * se_pred
pred_lower = fit_y - t_crit * se_pred

# Unknown sample
unknown_absorbance = 0.38
unknown_concentration = (unknown_absorbance - intercept) / slope

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Prediction interval band (wider, spec-required)
ax.fill_between(fit_x, pred_lower, pred_upper, color=palette[0], alpha=0.08, label="95% Prediction Interval")

# sns.regplot: scatter + regression line + confidence interval band in one call
sns.regplot(
    data=df,
    x="Concentration (mg/L)",
    y="Absorbance",
    ax=ax,
    ci=95,
    color=palette[0],
    scatter_kws={"s": 280, "edgecolor": "white", "linewidths": 1.2, "zorder": 5},
    line_kws={"linewidth": 2.5, "zorder": 4},
    label="Linear Fit (95% CI)",
)

# Unknown sample point
ax.plot(
    unknown_concentration,
    unknown_absorbance,
    marker="D",
    markersize=14,
    color=palette[1],
    markeredgecolor="white",
    markeredgewidth=1.2,
    zorder=6,
    label="Unknown Sample",
)

# Dashed projection lines from unknown to axes
ax.plot(
    [unknown_concentration, unknown_concentration],
    [0, unknown_absorbance],
    linestyle="--",
    color=palette[1],
    linewidth=1.5,
    alpha=0.7,
)
ax.plot(
    [0, unknown_concentration],
    [unknown_absorbance, unknown_absorbance],
    linestyle="--",
    color=palette[1],
    linewidth=1.5,
    alpha=0.7,
)

# Equation and R² annotation
eq_text = f"y = {slope:.4f}x + {intercept:.4f}\nR² = {r_squared:.4f}"
ax.text(
    0.05,
    0.92,
    eq_text,
    transform=ax.transAxes,
    fontsize=18,
    verticalalignment="top",
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.9},
)

# Unknown sample annotation
ax.annotate(
    f"Unknown: {unknown_concentration:.1f} mg/L",
    xy=(unknown_concentration, unknown_absorbance),
    xytext=(unknown_concentration + 1.8, unknown_absorbance + 0.04),
    fontsize=16,
    color=palette[1],
    arrowprops={"arrowstyle": "->", "color": palette[1], "lw": 1.5},
)

# Labels and formatting
ax.set_xlabel("Concentration (mg/L)", fontsize=20)
ax.set_ylabel("Absorbance", fontsize=20)
ax.set_title("calibration-beer-lambert \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.yaxis.grid(True)
ax.set_xlim(-0.5, 16)
ax.set_ylim(-0.03, 0.75)
ax.legend(fontsize=15, loc="lower right", framealpha=0.9)
sns.despine(ax=ax)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
