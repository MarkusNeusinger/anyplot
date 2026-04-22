""" pyplots.ai
sn-curve-basic: S-N Curve (Wöhler Curve)
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-15
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Set style
sns.set_context("talk", font_scale=1.2)

# Generate realistic S-N curve data for steel
np.random.seed(42)

# Material properties (typical structural steel in MPa)
ultimate_strength = 450
yield_strength = 350
endurance_limit = 200

# Generate stress levels for testing
stress_levels = np.array([400, 350, 320, 300, 280, 260, 240, 220, 210, 205])

# Calculate cycles using Basquin equation: S = A * N^b
# Rearranged: N = (S / A)^(1/b)
A = 1200  # Material constant
b = -0.12  # Basquin exponent

# Generate multiple test points per stress level with scatter
cycles_list = []
stress_list = []

for stress in stress_levels:
    # Number of test specimens per stress level
    n_specimens = np.random.randint(3, 6)
    base_cycles = (stress / A) ** (1 / b)

    # Add scatter to simulate real test variation
    scatter = np.random.lognormal(0, 0.3, n_specimens)
    cycles = base_cycles * scatter

    cycles_list.extend(cycles)
    stress_list.extend([stress] * n_specimens)

cycles = np.array(cycles_list)
stress = np.array(stress_list)

# Create fit line for the curve
fit_stress = np.linspace(200, 420, 100)
fit_cycles = (fit_stress / A) ** (1 / b)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Plot data points with seaborn
sns.scatterplot(
    x=cycles, y=stress, s=200, color="#306998", alpha=0.7, edgecolor="white", linewidth=1.5, ax=ax, label="Test Data"
)

# Plot fit line
ax.plot(fit_cycles, fit_stress, color="#306998", linewidth=2.5, linestyle="-", label="S-N Curve Fit")

# Add reference lines for material properties
ax.axhline(
    y=ultimate_strength,
    color="#E74C3C",
    linewidth=2,
    linestyle="--",
    label=f"Ultimate Strength ({ultimate_strength} MPa)",
)
ax.axhline(
    y=yield_strength, color="#FFD43B", linewidth=2, linestyle="--", label=f"Yield Strength ({yield_strength} MPa)"
)
ax.axhline(
    y=endurance_limit, color="#27AE60", linewidth=2, linestyle="--", label=f"Endurance Limit ({endurance_limit} MPa)"
)

# Set logarithmic scale for x-axis
ax.set_xscale("log")

# Styling
ax.set_xlabel("Number of Cycles to Failure (N)", fontsize=20)
ax.set_ylabel("Stress Amplitude (MPa)", fontsize=20)
ax.set_title("sn-curve-basic · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--", which="both")

# Legend
ax.legend(loc="upper right", fontsize=14, framealpha=0.95)

# Set axis limits
ax.set_xlim(1e3, 1e8)
ax.set_ylim(150, 500)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
