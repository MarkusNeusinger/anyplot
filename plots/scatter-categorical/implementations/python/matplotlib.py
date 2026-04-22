""" pyplots.ai
scatter-categorical: Categorical Scatter Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Iris-like measurements with species categories
np.random.seed(42)

# Generate data for 3 plant species with different characteristics
n_per_group = 40

# Species A: Smaller petals
species_a_x = np.random.normal(1.5, 0.3, n_per_group)
species_a_y = np.random.normal(0.3, 0.1, n_per_group)

# Species B: Medium petals
species_b_x = np.random.normal(4.0, 0.5, n_per_group)
species_b_y = np.random.normal(1.3, 0.2, n_per_group)

# Species C: Larger petals
species_c_x = np.random.normal(5.5, 0.6, n_per_group)
species_c_y = np.random.normal(2.0, 0.3, n_per_group)

# Colors - Python Blue, Python Yellow, and a complementary teal
colors = ["#306998", "#FFD43B", "#2AA198"]
categories = ["Species A", "Species B", "Species C"]

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Plot each category with distinct colors and markers
ax.scatter(
    species_a_x,
    species_a_y,
    s=200,
    c=colors[0],
    alpha=0.8,
    label=categories[0],
    marker="o",
    edgecolors="white",
    linewidths=0.5,
)
ax.scatter(
    species_b_x,
    species_b_y,
    s=200,
    c=colors[1],
    alpha=0.8,
    label=categories[1],
    marker="s",
    edgecolors="#666666",
    linewidths=0.5,
)
ax.scatter(
    species_c_x,
    species_c_y,
    s=200,
    c=colors[2],
    alpha=0.8,
    label=categories[2],
    marker="^",
    edgecolors="white",
    linewidths=0.5,
)

# Labels and styling
ax.set_xlabel("Petal Length (cm)", fontsize=20)
ax.set_ylabel("Petal Width (cm)", fontsize=20)
ax.set_title("scatter-categorical · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")
ax.legend(fontsize=16, loc="upper left", framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
