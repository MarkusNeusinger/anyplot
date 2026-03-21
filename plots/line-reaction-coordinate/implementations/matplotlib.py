"""pyplots.ai
line-reaction-coordinate: Reaction Coordinate Energy Diagram
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-03-21
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch


# Data
reactant_energy = 50.0
transition_energy = 120.0
product_energy = 20.0
peak_pos = 0.45

reaction_coord = np.linspace(0, 1, 500)
sigma = 0.13
baseline = reactant_energy + (product_energy - reactant_energy) * (3 * reaction_coord**2 - 2 * reaction_coord**3)
gaussian_bump = (transition_energy - (reactant_energy + product_energy) / 2) * np.exp(
    -((reaction_coord - peak_pos) ** 2) / (2 * sigma**2)
)
energy = baseline + gaussian_bump

peak_idx = np.argmax(energy)
actual_peak = energy[peak_idx]
peak_x = reaction_coord[peak_idx]

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

ax.plot(reaction_coord, energy, color="#306998", linewidth=3.5, zorder=3)

# Dashed reference lines at reactant and product energy levels
ax.hlines(reactant_energy, -0.05, 0.20, colors="#999999", linestyles="--", linewidth=1.5, alpha=0.5)
ax.hlines(reactant_energy, 0.82, 1.12, colors="#999999", linestyles="--", linewidth=1.5, alpha=0.5)
ax.hlines(product_energy, 0.78, 1.12, colors="#999999", linestyles="--", linewidth=1.5, alpha=0.5)

# Transition state marker
ax.scatter([peak_x], [actual_peak], s=140, color="#C84B31", zorder=4, edgecolors="white", linewidth=1.5)

# Labels
ax.text(
    0.02, reactant_energy + 4, "Reactants\n(50 kJ/mol)", fontsize=16, fontweight="medium", color="#333333", va="bottom"
)
ax.text(0.78, product_energy - 4, "Products\n(20 kJ/mol)", fontsize=16, fontweight="medium", color="#333333", va="top")
ax.text(
    peak_x,
    actual_peak + 5,
    "Transition State",
    fontsize=16,
    fontweight="medium",
    color="#C84B31",
    va="bottom",
    ha="center",
)

# Activation energy arrow (Ea)
ea_x = 0.14
arrow_ea = FancyArrowPatch(
    (ea_x, reactant_energy),
    (ea_x, actual_peak),
    arrowstyle="<->",
    mutation_scale=18,
    linewidth=2,
    color="#E07A2F",
    zorder=5,
)
ax.add_patch(arrow_ea)
ea_value = actual_peak - reactant_energy
ax.text(
    ea_x + 0.03,
    (reactant_energy + actual_peak) / 2,
    f"$E_a$ = {ea_value:.0f} kJ/mol",
    fontsize=16,
    fontweight="bold",
    color="#E07A2F",
    ha="left",
    va="center",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "none", "alpha": 0.9},
)

# Enthalpy change arrow (ΔH)
dh_x = 1.05
arrow_dh = FancyArrowPatch(
    (dh_x, reactant_energy),
    (dh_x, product_energy),
    arrowstyle="<->",
    mutation_scale=18,
    linewidth=2,
    color="#2D8659",
    zorder=5,
)
ax.add_patch(arrow_dh)
dh_value = product_energy - reactant_energy
ax.text(
    dh_x + 0.02,
    (reactant_energy + product_energy) / 2,
    f"$\\Delta H$ = {dh_value:.0f} kJ/mol",
    fontsize=16,
    fontweight="bold",
    color="#2D8659",
    ha="left",
    va="center",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "none", "alpha": 0.9},
)

# Style
ax.set_xlabel("Reaction Coordinate", fontsize=20)
ax.set_ylabel("Potential Energy (kJ/mol)", fontsize=20)
ax.set_title("line-reaction-coordinate · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(-0.05, 1.22)
ax.set_ylim(0, actual_peak + 25)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
ax.set_xticks([])

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
