"""pyplots.ai
line-arrhenius: Arrhenius Plot for Reaction Kinetics
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-03-21
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy import stats


# Data — first-order decomposition reaction rate constants at various temperatures
temperature_K = np.array([300, 350, 400, 450, 500, 550, 600])
R = 8.314  # gas constant (J/mol·K)
Ea_true = 75000  # activation energy (J/mol)
A = 1e13  # pre-exponential factor

np.random.seed(42)
noise = np.random.normal(0, 0.15, len(temperature_K))
rate_constant_k = A * np.exp(-Ea_true / (R * temperature_K)) * np.exp(noise)

inv_T = 1.0 / temperature_K
ln_k = np.log(rate_constant_k)

# Linear regression
slope, intercept, r_value, p_value, std_err = stats.linregress(inv_T, ln_k)
r_squared = r_value**2
Ea_extracted = -slope * R

inv_T_fit = np.linspace(inv_T.min() - 0.0001, inv_T.max() + 0.0001, 200)
ln_k_fit = slope * inv_T_fit + intercept

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

ax.plot(inv_T_fit, ln_k_fit, color="#306998", linewidth=3, alpha=0.7, zorder=1)
sns.scatterplot(x=inv_T, y=ln_k, s=300, color="#306998", edgecolor="white", linewidth=1.5, zorder=2, ax=ax)

# Annotations
ax.text(
    0.97,
    0.05,
    f"R² = {r_squared:.4f}\nSlope = {slope:.0f} K\nEₐ = {Ea_extracted / 1000:.1f} kJ/mol",
    transform=ax.transAxes,
    fontsize=18,
    verticalalignment="bottom",
    horizontalalignment="right",
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.9},
)

# Secondary x-axis for temperature in K
ax_top = ax.twiny()
ax_top.set_xlim(ax.get_xlim())
temp_ticks_K = np.array([300, 350, 400, 450, 500, 550, 600])
temp_ticks_inv = 1.0 / temp_ticks_K
ax_top.set_xticks(temp_ticks_inv)
ax_top.set_xticklabels([f"{t} K" for t in temp_ticks_K], fontsize=14)
ax_top.set_xlabel("Temperature (K)", fontsize=20)
ax_top.tick_params(axis="x", labelsize=14)
ax_top.spines["right"].set_visible(False)

# Style
ax.set_xlabel("1/T (K⁻¹)", fontsize=20)
ax.set_ylabel("ln(k)", fontsize=20)
ax.set_title("line-arrhenius · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=40)
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
