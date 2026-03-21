"""pyplots.ai
line-arrhenius: Arrhenius Plot for Reaction Kinetics
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-21
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import seaborn as sns
from scipy import stats


# Data — first-order decomposition reaction rate constants at various temperatures
temperature_K = np.array([300, 325, 350, 400, 450, 500, 550, 600])
R = 8.314  # gas constant (J/mol·K)
Ea_true = 75000  # activation energy (J/mol)
A = 1e13  # pre-exponential factor

np.random.seed(42)
noise = np.random.normal(0, 0.35, len(temperature_K))
rate_constant_k = A * np.exp(-Ea_true / (R * temperature_K)) * np.exp(noise)

inv_T = 1.0 / temperature_K
ln_k = np.log(rate_constant_k)

# Linear regression for annotation values
slope, intercept, r_value, p_value, std_err = stats.linregress(inv_T, ln_k)
r_squared = r_value**2
Ea_extracted = -slope * R

# Plot using sns.regplot — idiomatic seaborn regression + scatter
sns.set_theme(style="ticks", rc={"axes.spines.top": False, "axes.spines.right": False, "font.family": "sans-serif"})

fig, ax = plt.subplots(figsize=(16, 9))

sns.regplot(
    x=inv_T,
    y=ln_k,
    ci=95,
    scatter_kws={"s": 280, "color": "#306998", "edgecolor": "white", "linewidths": 2, "zorder": 5},
    line_kws={"color": "#306998", "linewidth": 3, "alpha": 0.8},
    ax=ax,
)

# Annotation box with key results
annotation_text = f"$R^2$ = {r_squared:.4f}\nSlope = {slope:.0f} K\n$E_a$ = {Ea_extracted / 1000:.1f} kJ/mol"
ax.text(
    0.03,
    0.35,
    annotation_text,
    transform=ax.transAxes,
    fontsize=18,
    verticalalignment="top",
    horizontalalignment="left",
    bbox={"boxstyle": "round,pad=0.5", "facecolor": "#f8f9fa", "edgecolor": "#306998", "alpha": 0.95, "linewidth": 1.5},
)

# Secondary x-axis for temperature in K
ax_top = ax.twiny()
ax_top.set_xlim(ax.get_xlim())
temp_ticks_K = np.array([300, 350, 400, 450, 500, 550, 600])
temp_ticks_inv = 1.0 / temp_ticks_K
ax_top.set_xticks(temp_ticks_inv)
ax_top.set_xticklabels([f"{t} K" for t in temp_ticks_K], fontsize=14)
ax_top.set_xlabel("Temperature (K)", fontsize=20, labelpad=12)
ax_top.tick_params(axis="x", labelsize=14)
ax_top.spines["right"].set_visible(False)

# Style
ax.set_xlabel("1/T (K⁻¹)", fontsize=20)
ax.set_ylabel("ln(k)", fontsize=20)
ax.set_title("line-arrhenius · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=40)
ax.tick_params(axis="both", labelsize=16)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color="#888888")
ax.xaxis.set_major_formatter(ticker.FormatStrFormatter("%.4f"))

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
