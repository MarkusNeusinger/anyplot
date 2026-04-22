""" pyplots.ai
sn-curve-basic: S-N Curve (Wöhler Curve)
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 94/100 | Created: 2026-01-15
"""

import matplotlib.pyplot as plt
import numpy as np


# Data: Simulated fatigue test results for steel specimens
np.random.seed(42)

# Generate realistic S-N curve data points with scatter
# High stress -> low cycles, Low stress -> high cycles
stress_levels = np.array([450, 400, 350, 320, 300, 280, 260, 250, 240, 230, 220, 210])

# Generate multiple test points per stress level with realistic scatter
cycles_data = []
stress_data = []

for stress in stress_levels:
    # Basquin equation: N = (S/A)^(-1/b) where A and b are material constants
    # Using typical steel values
    A = 1200  # Material constant
    b = 0.12  # Fatigue strength exponent
    N_mean = (stress / A) ** (-1 / b)

    # Add 2-4 test specimens per stress level with log-normal scatter
    n_samples = np.random.randint(2, 5)
    for _ in range(n_samples):
        scatter = np.exp(np.random.normal(0, 0.3))  # Log-normal scatter
        cycles_data.append(N_mean * scatter)
        stress_data.append(stress + np.random.normal(0, 5))  # Small stress measurement error

cycles = np.array(cycles_data)
stress = np.array(stress_data)

# Fit line using Basquin equation (log-linear fit)
log_cycles = np.log10(cycles)
log_stress = np.log10(stress)
coeffs = np.polyfit(log_cycles, log_stress, 1)
fit_cycles = np.logspace(2, 8, 100)
fit_stress = 10 ** (coeffs[0] * np.log10(fit_cycles) + coeffs[1])

# Material property reference values (typical for structural steel)
ultimate_strength = 500  # MPa
yield_strength = 350  # MPa
endurance_limit = 200  # MPa

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Plot data points
ax.scatter(
    cycles, stress, s=200, color="#306998", alpha=0.7, edgecolors="white", linewidths=1.5, label="Test Data", zorder=5
)

# Plot fitted S-N curve
ax.plot(fit_cycles, fit_stress, color="#FFD43B", linewidth=3, label="Basquin Fit", zorder=4)

# Add horizontal reference lines for material properties
ax.axhline(
    y=ultimate_strength,
    color="#E53935",
    linestyle="--",
    linewidth=2.5,
    label=f"Ultimate Strength ({ultimate_strength} MPa)",
    zorder=3,
)
ax.axhline(
    y=yield_strength,
    color="#FB8C00",
    linestyle="--",
    linewidth=2.5,
    label=f"Yield Strength ({yield_strength} MPa)",
    zorder=3,
)
ax.axhline(
    y=endurance_limit,
    color="#43A047",
    linestyle="--",
    linewidth=2.5,
    label=f"Endurance Limit ({endurance_limit} MPa)",
    zorder=3,
)

# Set logarithmic scales
ax.set_xscale("log")
ax.set_yscale("log")

# Set axis limits
ax.set_xlim(1e2, 1e8)
ax.set_ylim(150, 600)

# Labels and styling
ax.set_xlabel("Number of Cycles to Failure (N)", fontsize=20)
ax.set_ylabel("Stress Amplitude (MPa)", fontsize=20)
ax.set_title("sn-curve-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Grid
ax.grid(True, alpha=0.3, linestyle="--", which="both")

# Legend
ax.legend(fontsize=14, loc="upper right", framealpha=0.95)

# Annotations for fatigue regions
ax.annotate("Low-Cycle\nFatigue", xy=(5e2, 420), fontsize=14, ha="center", color="#555555", style="italic")
ax.annotate("High-Cycle\nFatigue", xy=(1e5, 280), fontsize=14, ha="center", color="#555555", style="italic")
ax.annotate("Infinite Life", xy=(5e7, 180), fontsize=14, ha="center", color="#555555", style="italic")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
