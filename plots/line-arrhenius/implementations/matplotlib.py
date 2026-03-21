""" pyplots.ai
line-arrhenius: Arrhenius Plot for Reaction Kinetics
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-21
"""

import matplotlib.pyplot as plt
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

inv_temp_fit = np.linspace(1 / temperature_K.max(), 1 / temperature_K.min(), 100)
ln_k_fit = slope * inv_temp_fit + intercept

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

ax.plot(inv_temp_fit * 1000, ln_k_fit, color="#306998", linewidth=3, alpha=0.7, label="Linear fit", zorder=2)
ax.scatter(
    inv_temperature,
    ln_k,
    s=220,
    color="#306998",
    edgecolors="white",
    linewidth=1.5,
    zorder=3,
    label="Experimental data",
)

# Annotation — activation energy and R²
mid_idx = len(inv_temp_fit) // 3
ax.annotate(
    f"$E_a$ = {activation_energy:.1f} kJ/mol\n$R^2$ = {r_squared:.4f}",
    xy=(inv_temp_fit[mid_idx] * 1000, ln_k_fit[mid_idx]),
    xytext=(35, 45),
    textcoords="offset points",
    fontsize=18,
    color="#333333",
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.9},
    arrowprops={"arrowstyle": "->", "color": "#666666", "lw": 1.5},
)

# Style
ax.set_xlabel("1000 / T  (K⁻¹)", fontsize=20)
ax.set_ylabel("ln(k)", fontsize=20)
ax.set_title("line-arrhenius · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
ax.legend(fontsize=16, framealpha=0.9, edgecolor="#cccccc")

# Secondary x-axis — original temperature in K
ax2 = ax.twiny()
ax2.set_xlim(ax.get_xlim())
temp_ticks = np.array([600, 550, 500, 450, 400, 350, 300])
tick_positions = 1000 / temp_ticks
ax2.set_xticks(tick_positions)
ax2.set_xticklabels([f"{t} K" for t in temp_ticks], fontsize=14)
ax2.set_xlabel("Temperature (K)", fontsize=18)
ax2.spines["right"].set_visible(False)
ax2.tick_params(axis="x", labelsize=14)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
