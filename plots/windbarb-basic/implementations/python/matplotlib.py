""" pyplots.ai
windbarb-basic: Wind Barb Plot for Meteorological Data
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-11
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Surface wind observations from a grid of weather stations
np.random.seed(42)

# Create a grid of observation points (simulating weather station network)
x = np.arange(0, 10, 1)
y = np.arange(0, 6, 1)
X, Y = np.meshgrid(x, y)
X = X.flatten()
Y = Y.flatten()

# Generate wind components (u: east-west, v: north-south) in knots
# Create a realistic wind pattern with some spatial coherence
base_u = 15 + 10 * np.sin(X * 0.5)  # Zonal component varies with x
base_v = 5 + 8 * np.cos(Y * 0.8)  # Meridional component varies with y
# Add some random variability
U = base_u + np.random.uniform(-5, 5, size=X.shape)
V = base_v + np.random.uniform(-5, 5, size=Y.shape)

# Include some calm winds (< 2.5 knots) for demonstration
calm_indices = [0, 25, 45]
U[calm_indices] = np.random.uniform(-1, 1, size=len(calm_indices))
V[calm_indices] = np.random.uniform(-1, 1, size=len(calm_indices))

# Include strong winds with pennants (50+ knots) for variety
strong_indices = [12, 38, 55]
U[strong_indices] = 40 + np.random.uniform(0, 15, size=len(strong_indices))
V[strong_indices] = 30 + np.random.uniform(0, 10, size=len(strong_indices))

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Plot wind barbs
# barb_increments defines the knot values for half barb, full barb, and pennant
ax.barbs(
    X,
    Y,
    U,
    V,
    length=8,
    barb_increments={"half": 5, "full": 10, "flag": 50},
    color="#306998",
    linewidth=1.5,
    sizes={"emptybarb": 0.15, "spacing": 0.15, "height": 0.5},
)

# Style
ax.set_xlabel("Longitude (°E)", fontsize=20)
ax.set_ylabel("Latitude (°N)", fontsize=20)
ax.set_title("windbarb-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")

# Set axis limits with padding
ax.set_xlim(-0.5, 9.5)
ax.set_ylim(-0.5, 5.5)

# Add a legend annotation explaining barb notation
legend_text = (
    "Wind Barb Legend:\n○ = Calm (< 2.5 kt)\n╲ = 5 kt (half barb)\n╲╲ = 10 kt (full barb)\n▲ = 50 kt (pennant)"
)
ax.text(
    0.02,
    0.98,
    legend_text,
    transform=ax.transAxes,
    fontsize=14,
    verticalalignment="top",
    fontfamily="monospace",
    bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.9, "edgecolor": "#306998"},
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
