""" pyplots.ai
andrews-curves: Andrews Curves for Multivariate Data
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np
from sklearn.datasets import load_iris
from sklearn.preprocessing import StandardScaler


# Load and prepare data
iris = load_iris()
X = iris.data
y = iris.target
species_names = ["Setosa", "Versicolor", "Virginica"]

# Normalize data to prevent dominant variables
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Generate t values from -π to π
t = np.linspace(-np.pi, np.pi, 200)

# Build Andrews curve transformation matrix
# f(t) = x1/sqrt(2) + x2*sin(t) + x3*cos(t) + x4*sin(2t) + ...
n_features = X_scaled.shape[1]
basis = np.zeros((len(t), n_features))
basis[:, 0] = 1 / np.sqrt(2)
for i in range(1, n_features):
    freq = (i + 1) // 2
    if i % 2 == 1:
        basis[:, i] = np.sin(freq * t)
    else:
        basis[:, i] = np.cos(freq * t)

# Compute all Andrews curves: each row of X_scaled dot basis.T gives one curve
curves = X_scaled @ basis.T  # shape: (150, 200)

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Colors for each species (Python Blue, Python Yellow, and a complementary color)
colors = ["#306998", "#FFD43B", "#E06C75"]

# Plot Andrews curves for each observation
for i in range(len(curves)):
    ax.plot(t, curves[i], color=colors[y[i]], alpha=0.4, linewidth=1.5)

# Create legend with sample lines
for idx, species in enumerate(species_names):
    ax.plot([], [], color=colors[idx], linewidth=3, label=species, alpha=0.8)

# Styling
ax.set_xlabel("t (radians)", fontsize=20)
ax.set_ylabel("f(t)", fontsize=20)
ax.set_title("andrews-curves · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper right")
ax.grid(True, alpha=0.3, linestyle="--")

# Set x-axis ticks at meaningful positions
ax.set_xticks([-np.pi, -np.pi / 2, 0, np.pi / 2, np.pi])
ax.set_xticklabels(["-π", "-π/2", "0", "π/2", "π"], fontsize=16)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
