"""pyplots.ai
phase-diagram-pt: Thermodynamic Phase Diagram (Pressure-Temperature)
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-14
"""

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np


# Data — Water phase diagram (representative real data)
# Triple point: 273.16 K, 611.73 Pa
# Critical point: 647.1 K, 22.064 MPa = 22064000 Pa

triple_T, triple_P = 273.16, 611.73
critical_T, critical_P = 647.1, 22.064e6

# Solid-gas boundary (sublimation curve) — Clausius-Clapeyron approximation
T_solid_gas = np.linspace(200, triple_T, 80)
L_sub = 51059  # J/mol (sublimation enthalpy approx)
R = 8.314
P_solid_gas = triple_P * np.exp((L_sub / R) * (1 / triple_T - 1 / T_solid_gas))

# Liquid-gas boundary (vaporization curve) — from triple point to critical point
T_liquid_gas = np.linspace(triple_T, critical_T, 100)
L_vap = 40670  # J/mol (vaporization enthalpy approx)
P_liquid_gas = triple_P * np.exp((L_vap / R) * (1 / triple_T - 1 / T_liquid_gas))

# Solid-liquid boundary (melting curve) — water has negative slope
# Using Simon equation approximation for ice Ih
# Extend to high pressures to make curve visually prominent
T_solid_liquid = np.linspace(triple_T, 240, 100)
P_solid_liquid = triple_P + (T_solid_liquid - triple_T) * (-1.4e7)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Axis limits and log scale (set early for fill operations)
ax.set_yscale("log")
x_min, x_max = 180, 800
y_min, y_max = 10, 5e8
ax.set_xlim(x_min, x_max)
ax.set_ylim(y_min, y_max)

# Phase region fills using fill_between and fill
# Gas region: below vaporization curve and below sublimation curve
# Build the full gas boundary: sublimation curve + vaporization curve
gas_boundary_T = np.concatenate([T_solid_gas, T_liquid_gas])
gas_boundary_P = np.concatenate([P_solid_gas, P_liquid_gas])
ax.fill_between(gas_boundary_T, y_min, gas_boundary_P, color="#E8F4FD", alpha=0.6, zorder=1)

# Liquid region: above vaporization curve, right of melting curve, below critical point
# Fill between vaporization curve and top
ax.fill_between(T_liquid_gas, P_liquid_gas, y_max, color="#D4E8D0", alpha=0.5, zorder=1)

# Solid region: left of melting curve, above sublimation curve
# Use fill for the solid polygon
solid_T = np.concatenate([[x_min], T_solid_gas, T_solid_liquid[::-1], [T_solid_liquid[-1]], [x_min]])
solid_P = np.concatenate([[P_solid_gas[0]], P_solid_gas, P_solid_liquid[::-1], [y_max], [y_max]])
ax.fill(solid_T, solid_P, color="#E8DCF0", alpha=0.5, zorder=1)

# Supercritical region: right of critical point, above critical pressure
ax.fill_between([critical_T, x_max], critical_P, y_max, color="#FFF3CD", alpha=0.5, zorder=1)

# Reference lines at critical point (dashed) to emphasize phase boundaries
ax.axhline(critical_P, color="#999999", linewidth=1, linestyle=(0, (5, 5)), alpha=0.4, zorder=2)
ax.axvline(critical_T, color="#999999", linewidth=1, linestyle=(0, (5, 5)), alpha=0.4, zorder=2)

# Phase boundary curves
text_outline = [pe.withStroke(linewidth=4, foreground="white")]
curve_color = "#306998"
ax.plot(T_solid_gas, P_solid_gas, color=curve_color, linewidth=3, zorder=3)
ax.plot(T_liquid_gas, P_liquid_gas, color=curve_color, linewidth=3, zorder=3)
ax.plot(T_solid_liquid, P_solid_liquid, color=curve_color, linewidth=3, zorder=3)

# Mark triple point and critical point
ax.scatter(triple_T, triple_P, s=250, color="#E74C3C", edgecolors="white", linewidth=1.5, zorder=5)
ax.scatter(critical_T, critical_P, s=250, color="#E74C3C", edgecolors="white", linewidth=1.5, zorder=5)

# Annotate triple point
ax.annotate(
    "Triple Point\n(273.16 K, 611.73 Pa)",
    xy=(triple_T, triple_P),
    xytext=(80, -60),
    textcoords="offset points",
    fontsize=14,
    fontweight="medium",
    color="#333333",
    arrowprops={"arrowstyle": "->", "color": "#666666", "lw": 1.5},
    zorder=6,
    path_effects=text_outline,
)

# Annotate critical point
ax.annotate(
    "Critical Point\n(647.1 K, 22.06 MPa)",
    xy=(critical_T, critical_P),
    xytext=(-140, 50),
    textcoords="offset points",
    fontsize=14,
    fontweight="medium",
    color="#333333",
    arrowprops={"arrowstyle": "->", "color": "#666666", "lw": 1.5},
    zorder=6,
    path_effects=text_outline,
)

# Phase region labels with PathEffects for readability over fills
ax.text(
    215,
    5e6,
    "SOLID",
    fontsize=22,
    fontweight="bold",
    color="#7B2D8E",
    alpha=0.7,
    ha="center",
    path_effects=text_outline,
    zorder=4,
)
ax.text(
    420,
    5e6,
    "LIQUID",
    fontsize=22,
    fontweight="bold",
    color="#2D6E2E",
    alpha=0.7,
    ha="center",
    path_effects=text_outline,
    zorder=4,
)
ax.text(
    550,
    50,
    "GAS",
    fontsize=22,
    fontweight="bold",
    color="#1A6B8A",
    alpha=0.7,
    ha="center",
    path_effects=text_outline,
    zorder=4,
)
ax.text(
    720,
    8e7,
    "SUPERCRITICAL\nFLUID",
    fontsize=16,
    fontweight="bold",
    color="#8B6914",
    alpha=0.7,
    ha="center",
    path_effects=text_outline,
    zorder=4,
)

# Style
ax.set_xlabel("Temperature (K)", fontsize=20)
ax.set_ylabel("Pressure (Pa)", fontsize=20)
ax.set_title("phase-diagram-pt · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
