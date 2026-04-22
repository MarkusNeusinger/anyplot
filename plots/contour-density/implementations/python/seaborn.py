""" pyplots.ai
contour-density: Density Contour Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - bivariate normal distributions with two clusters
np.random.seed(42)

# Main cluster
n1 = 300
x1 = np.random.normal(loc=5, scale=1.5, size=n1)
y1 = np.random.normal(loc=5, scale=1.5, size=n1)

# Secondary cluster
n2 = 150
x2 = np.random.normal(loc=9, scale=1.0, size=n2)
y2 = np.random.normal(loc=8, scale=1.0, size=n2)

# Combine clusters
x = np.concatenate([x1, x2])
y = np.concatenate([y1, y2])

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Density contour plot using seaborn's kdeplot (filled)
sns.kdeplot(x=x, y=y, ax=ax, levels=10, fill=True, cmap="viridis", alpha=0.8)

# Add contour lines for clarity
sns.kdeplot(x=x, y=y, ax=ax, levels=10, color="#306998", linewidths=1.5, alpha=0.7)

# Scatter plot overlay for context (small, semi-transparent points)
ax.scatter(x, y, s=15, color="white", alpha=0.3, edgecolors="none")

# Styling
ax.set_xlabel("X Variable (units)", fontsize=20)
ax.set_ylabel("Y Variable (units)", fontsize=20)
ax.set_title("contour-density · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
