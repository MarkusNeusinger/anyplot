"""pyplots.ai
phase-diagram-pt: Thermodynamic Phase Diagram (Pressure-Temperature)
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-03-14
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - Water phase diagram (realistic values)
# Triple point: 273.16 K, 611.73 Pa
# Critical point: 647.1 K, 22.064 MPa = 22064000 Pa
triple_T, triple_P = 273.16, 611.73
critical_T, critical_P = 647.1, 22064000.0

# Solid-gas boundary (sublimation curve) - Clausius-Clapeyron approximation
T_solid_gas = np.linspace(200, triple_T, 100)
L_sub = 51059.0
R = 8.314
P_solid_gas = triple_P * np.exp((L_sub / R) * (1 / triple_T - 1 / T_solid_gas))

# Liquid-gas boundary (vaporization curve) - from triple point to critical point
T_liquid_gas = np.linspace(triple_T, critical_T, 100)
L_vap = 40660.0
P_liquid_gas = triple_P * np.exp((L_vap / R) * (1 / triple_T - 1 / T_liquid_gas))

# Solid-liquid boundary (melting curve) - water has negative slope (anomalous)
P_solid_liquid = np.logspace(np.log10(triple_P), np.log10(critical_P * 5), 100)
dT_dP = -7.4e-8
T_solid_liquid = triple_T + dT_dP * (P_solid_liquid - triple_P)

# Plot
sns.set_context("talk", font_scale=1.2)
fig, ax = plt.subplots(figsize=(16, 9))

sns.lineplot(x=T_solid_gas, y=P_solid_gas, ax=ax, color="#306998", linewidth=3, label="Sublimation curve")
sns.lineplot(x=T_liquid_gas, y=P_liquid_gas, ax=ax, color="#E0832B", linewidth=3, label="Vaporization curve")
sns.lineplot(x=T_solid_liquid, y=P_solid_liquid, ax=ax, color="#2CA02C", linewidth=3, label="Melting curve")

# Mark triple point and critical point
ax.scatter([triple_T], [triple_P], color="#D62728", s=250, zorder=5, edgecolors="white", linewidth=1.5)
ax.scatter([critical_T], [critical_P], color="#9467BD", s=250, zorder=5, edgecolors="white", linewidth=1.5, marker="D")

ax.annotate(
    "Triple Point\n(273.16 K, 611.7 Pa)",
    xy=(triple_T, triple_P),
    xytext=(triple_T + 40, triple_P * 0.05),
    fontsize=15,
    fontweight="bold",
    color="#D62728",
    arrowprops={"arrowstyle": "->", "color": "#D62728", "lw": 2},
    va="center",
)

ax.annotate(
    "Critical Point\n(647.1 K, 22.1 MPa)",
    xy=(critical_T, critical_P),
    xytext=(critical_T - 120, critical_P * 8),
    fontsize=15,
    fontweight="bold",
    color="#9467BD",
    arrowprops={"arrowstyle": "->", "color": "#9467BD", "lw": 2},
    va="center",
)

# Phase region labels
ax.text(230, 1e6, "SOLID", fontsize=28, fontweight="bold", color="#306998", alpha=0.4, ha="center", va="center")
ax.text(400, 5e2, "GAS", fontsize=28, fontweight="bold", color="#E0832B", alpha=0.4, ha="center", va="center")
ax.text(450, 5e6, "LIQUID", fontsize=28, fontweight="bold", color="#2CA02C", alpha=0.4, ha="center", va="center")
ax.text(
    680,
    critical_P * 15,
    "SUPERCRITICAL\nFLUID",
    fontsize=18,
    fontweight="bold",
    color="#9467BD",
    alpha=0.4,
    ha="center",
    va="center",
)

# Style
ax.set_yscale("log")
ax.set_xlim(190, 750)
ax.set_ylim(1e1, 1e9)
ax.set_xlabel("Temperature (K)", fontsize=20)
ax.set_ylabel("Pressure (Pa)", fontsize=20)
ax.set_title("Water Phase Diagram · phase-diagram-pt · seaborn · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8)
ax.xaxis.grid(True, alpha=0.15, linewidth=0.8)
ax.legend(fontsize=16, loc="lower right", framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
