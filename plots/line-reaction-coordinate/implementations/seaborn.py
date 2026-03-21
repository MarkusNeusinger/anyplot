""" pyplots.ai
line-reaction-coordinate: Reaction Coordinate Energy Diagram
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 81/100 | Created: 2026-03-21
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import PchipInterpolator


# Data
reactant_energy = 50.0
transition_energy = 120.0
product_energy = 20.0

control_x = np.array([0.0, 0.12, 0.22, 0.35, 0.47, 0.59, 0.72, 0.82, 0.90, 1.0])
control_y = np.array(
    [
        reactant_energy,
        reactant_energy,
        reactant_energy + 2,
        85,
        transition_energy,
        85,
        product_energy + 5,
        product_energy,
        product_energy,
        product_energy,
    ]
)

reaction_coord = np.linspace(0, 1, 500)
spline = PchipInterpolator(control_x, control_y)
energy = spline(reaction_coord)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

ax.plot(reaction_coord, energy, color="#306998", linewidth=3.5, zorder=3)

# Horizontal dashed lines at reactant and product energy levels
ax.hlines(y=reactant_energy, xmin=-0.02, xmax=0.18, color="#888888", linestyle="--", linewidth=1.5, alpha=0.5)
ax.hlines(y=product_energy, xmin=0.82, xmax=1.02, color="#888888", linestyle="--", linewidth=1.5, alpha=0.5)

# Labels for reactants, products, transition state
ax.text(
    0.02, reactant_energy + 3, "Reactants\n(50 kJ/mol)", fontsize=16, fontweight="bold", color="#333333", va="bottom"
)
ax.text(
    0.98,
    product_energy + 3,
    "Products\n(20 kJ/mol)",
    fontsize=16,
    fontweight="bold",
    color="#333333",
    va="bottom",
    ha="right",
)
ax.text(
    0.47,
    transition_energy + 3,
    "Transition State\n(120 kJ/mol)",
    fontsize=16,
    fontweight="bold",
    color="#333333",
    va="bottom",
    ha="center",
)

# Activation energy arrow (Ea) — in clear space left of the curve rise
ea_x = 0.13
ax.annotate(
    "",
    xy=(ea_x, transition_energy),
    xytext=(ea_x, reactant_energy),
    arrowprops={"arrowstyle": "<->", "color": "#C0392B", "lw": 2.5, "shrinkA": 0, "shrinkB": 0},
)
ax.text(
    ea_x - 0.02,
    (reactant_energy + transition_energy) / 2,
    f"$E_a$ = {transition_energy - reactant_energy:.0f} kJ/mol",
    fontsize=15,
    color="#C0392B",
    fontweight="bold",
    ha="right",
    va="center",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "none", "alpha": 0.9},
)

# Enthalpy change arrow (ΔH) — in clear space right of the curve
dh_x = 0.90
ax.annotate(
    "",
    xy=(dh_x, product_energy),
    xytext=(dh_x, reactant_energy),
    arrowprops={"arrowstyle": "<->", "color": "#2E86C1", "lw": 2.5, "shrinkA": 0, "shrinkB": 0},
)
ax.text(
    dh_x + 0.02,
    (reactant_energy + product_energy) / 2,
    f"$\\Delta H$ = {product_energy - reactant_energy:.0f} kJ/mol",
    fontsize=15,
    color="#2E86C1",
    fontweight="bold",
    ha="left",
    va="center",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "none", "alpha": 0.9},
)

# Style
ax.set_xlabel("Reaction Coordinate", fontsize=20)
ax.set_ylabel("Potential Energy (kJ/mol)", fontsize=20)
ax.set_title("line-reaction-coordinate · seaborn · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(0, 145)
ax.set_xticks([])
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
