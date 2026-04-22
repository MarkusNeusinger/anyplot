""" pyplots.ai
contour-filled: Filled Contour Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Set seaborn style for consistent aesthetics
sns.set_theme(style="whitegrid")
sns.set_context("talk", font_scale=1.2)

# Data: Create a 2D Gaussian surface with multiple peaks
np.random.seed(42)
x = np.linspace(-3, 3, 80)
y = np.linspace(-3, 3, 80)
X, Y = np.meshgrid(x, y)

# Create surface with two Gaussian peaks and a saddle region
z1 = np.exp(-((X - 1) ** 2 + (Y - 1) ** 2) / 0.8)
z2 = np.exp(-((X + 1) ** 2 + (Y + 1) ** 2) / 1.2)
z3 = -0.5 * np.exp(-((X - 0.5) ** 2 + (Y + 0.5) ** 2) / 0.5)
Z = z1 + z2 + z3

# Create figure with seaborn styling
fig, ax = plt.subplots(figsize=(16, 9))

# Create filled contour using seaborn's color palette
palette = sns.color_palette("viridis", as_cmap=True)
levels = np.linspace(Z.min(), Z.max(), 15)
contourf = ax.contourf(X, Y, Z, levels=levels, cmap=palette)

# Overlay contour lines for precise level identification
contour_lines = ax.contour(X, Y, Z, levels=levels, colors="white", linewidths=0.5, alpha=0.4)

# Add colorbar with proper sizing
cbar = fig.colorbar(contourf, ax=ax, shrink=0.85, pad=0.02)
cbar.set_label("Intensity", fontsize=20)
cbar.ax.tick_params(labelsize=16)

# Styling
ax.set_xlabel("X Coordinate", fontsize=20)
ax.set_ylabel("Y Coordinate", fontsize=20)
ax.set_title("contour-filled · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.set_aspect("equal")

# Remove grid (not appropriate for contour plots)
ax.grid(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
