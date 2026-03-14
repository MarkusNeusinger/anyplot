""" pyplots.ai
phase-diagram-pt: Thermodynamic Phase Diagram (Pressure-Temperature)
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-14
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
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

# Build DataFrame for idiomatic seaborn usage
df = pd.concat(
    [
        pd.DataFrame({"Temperature (K)": T_solid_gas, "Pressure (Pa)": P_solid_gas, "Boundary": "Sublimation curve"}),
        pd.DataFrame(
            {"Temperature (K)": T_liquid_gas, "Pressure (Pa)": P_liquid_gas, "Boundary": "Vaporization curve"}
        ),
        pd.DataFrame({"Temperature (K)": T_solid_liquid, "Pressure (Pa)": P_solid_liquid, "Boundary": "Melting curve"}),
    ],
    ignore_index=True,
)

# Seaborn styling
sns.set_context("talk", font_scale=1.2)
sns.set_style("whitegrid", {"grid.alpha": 0.15, "grid.linewidth": 0.8})
palette = sns.color_palette(["#306998", "#E0832B", "#2CA02C"])

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

sns.lineplot(
    data=df,
    x="Temperature (K)",
    y="Pressure (Pa)",
    hue="Boundary",
    style="Boundary",
    palette=palette,
    linewidth=3,
    ax=ax,
)

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
phase_colors = sns.color_palette(["#306998", "#E0832B", "#2CA02C", "#9467BD"])
ax.text(230, 1e6, "SOLID", fontsize=28, fontweight="bold", color=phase_colors[0], alpha=0.4, ha="center", va="center")
ax.text(400, 5e2, "GAS", fontsize=28, fontweight="bold", color=phase_colors[1], alpha=0.4, ha="center", va="center")
ax.text(450, 5e6, "LIQUID", fontsize=28, fontweight="bold", color=phase_colors[2], alpha=0.4, ha="center", va="center")
ax.text(
    680,
    critical_P * 15,
    "SUPERCRITICAL\nFLUID",
    fontsize=18,
    fontweight="bold",
    color=phase_colors[3],
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
ax.set_title("phase-diagram-pt · seaborn · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
sns.despine(ax=ax)
ax.legend(fontsize=16, loc="lower right", framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
