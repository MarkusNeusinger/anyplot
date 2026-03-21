""" pyplots.ai
line-arrhenius: Arrhenius Plot for Reaction Kinetics
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-21
"""

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np


# Data — first-order decomposition reaction rate constants at various temperatures
temperature_K = np.array([300, 350, 400, 450, 500, 550, 600])
activation_energy_true = 75000  # J/mol (75 kJ/mol)
R = 8.314  # J/(mol·K)
pre_exponential = 1e13  # s⁻¹

np.random.seed(42)
rate_constant_k = (
    pre_exponential
    * np.exp(-activation_energy_true / (R * temperature_K))
    * np.exp(np.random.normal(0, 0.15, len(temperature_K)))
)

inv_temperature = 1000 / temperature_K  # 1000/T for cleaner axis values
ln_k = np.log(rate_constant_k)

# Linear regression using numpy
coeffs = np.polyfit(1 / temperature_K, ln_k, 1)
slope, intercept = coeffs
ln_k_predicted = slope * (1 / temperature_K) + intercept
ss_res = np.sum((ln_k - ln_k_predicted) ** 2)
ss_tot = np.sum((ln_k - np.mean(ln_k)) ** 2)
r_squared = 1 - ss_res / ss_tot
activation_energy = -slope * R / 1000  # kJ/mol

inv_temp_fit = np.linspace(1 / temperature_K.max(), 1 / temperature_K.min(), 200)
ln_k_fit = slope * inv_temp_fit + intercept

# Residual standard error for confidence band
residual_se = np.sqrt(ss_res / (len(temperature_K) - 2))
inv_T = 1 / temperature_K
x_mean = np.mean(inv_T)
s_xx = np.sum((inv_T - x_mean) ** 2)
se_fit = residual_se * np.sqrt(1 / len(inv_T) + (inv_temp_fit - x_mean) ** 2 / s_xx)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor="#fafafa")
ax.set_facecolor("#fafafa")

# Confidence band (±2 SE)
ax.fill_between(
    inv_temp_fit * 1000,
    ln_k_fit - 2 * se_fit,
    ln_k_fit + 2 * se_fit,
    color="#306998",
    alpha=0.10,
    zorder=1,
    label="95% confidence band",
)

# Regression line with path effect for subtle glow
ax.plot(
    inv_temp_fit * 1000,
    ln_k_fit,
    color="#306998",
    linewidth=3,
    alpha=0.85,
    label="Linear fit",
    zorder=2,
    path_effects=[pe.withStroke(linewidth=5, foreground="white", alpha=0.4)],
)

# Data points — color-mapped by temperature for visual hierarchy
cmap = plt.cm.YlOrRd
norm = plt.Normalize(temperature_K.min(), temperature_K.max())
scatter = ax.scatter(
    inv_temperature,
    ln_k,
    s=240,
    c=temperature_K,
    cmap=cmap,
    edgecolors="white",
    linewidth=2,
    zorder=4,
    label="Experimental data",
)

# Colorbar as temperature indicator
cbar = fig.colorbar(scatter, ax=ax, pad=0.02, aspect=30, shrink=0.75)
cbar.set_label("Temperature (K)", fontsize=16, labelpad=10)
cbar.ax.tick_params(labelsize=13)
cbar.outline.set_visible(False)

# Annotation — activation energy and R²
mid_idx = len(inv_temp_fit) // 3
ax.annotate(
    f"$E_a$ = {activation_energy:.1f} kJ/mol\n$R^2$ = {r_squared:.4f}",
    xy=(inv_temp_fit[mid_idx] * 1000, ln_k_fit[mid_idx]),
    xytext=(40, 50),
    textcoords="offset points",
    fontsize=18,
    fontweight="medium",
    color="#1a1a1a",
    bbox={"boxstyle": "round,pad=0.5", "facecolor": "white", "edgecolor": "#306998", "alpha": 0.95, "linewidth": 1.5},
    arrowprops={"arrowstyle": "-|>", "color": "#306998", "lw": 1.8, "connectionstyle": "arc3,rad=0.15"},
)

# Style
ax.set_xlabel("1000 / T  (K⁻¹)", fontsize=20, labelpad=10)
ax.set_ylabel("ln(k)", fontsize=20, labelpad=10)
ax.set_title(
    "line-arrhenius · matplotlib · pyplots.ai",
    fontsize=24,
    fontweight="medium",
    pad=30,
    path_effects=[pe.withStroke(linewidth=3, foreground="#fafafa")],
)
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_linewidth(0.8)
ax.spines["left"].set_color("#999999")
ax.spines["bottom"].set_linewidth(0.8)
ax.spines["bottom"].set_color("#999999")
ax.yaxis.grid(True, alpha=0.15, linewidth=0.6, color="#888888")
ax.xaxis.grid(True, alpha=0.08, linewidth=0.4, color="#888888")
ax.legend(fontsize=15, framealpha=0.95, edgecolor="#dddddd", loc="upper right", fancybox=True)

# Custom tick formatter for x-axis
ax.xaxis.set_major_formatter(ticker.FormatStrFormatter("%.1f"))

# Secondary x-axis — original temperature in K
ax2 = ax.twiny()
ax2.set_xlim(ax.get_xlim())
temp_ticks = np.array([600, 550, 500, 450, 400, 350, 300])
tick_positions = 1000 / temp_ticks
ax2.set_xticks(tick_positions)
ax2.set_xticklabels([f"{t} K" for t in temp_ticks], fontsize=14)
ax2.set_xlabel("Temperature (K)", fontsize=18, labelpad=12)
ax2.spines["right"].set_visible(False)
ax2.spines["top"].set_linewidth(0.8)
ax2.spines["top"].set_color("#999999")
ax2.tick_params(axis="x", labelsize=14, colors="#555555")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="#fafafa")
