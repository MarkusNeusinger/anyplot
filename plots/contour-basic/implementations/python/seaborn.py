""" pyplots.ai
contour-basic: Basic Contour Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 72/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Apply seaborn styling for enhanced aesthetics
sns.set_theme(style="whitegrid", palette="viridis")

# Data - Topographic elevation map of a mountain region with a valley
# True scalar field z = f(x, y) on a regular meshgrid as specified
x = np.linspace(0, 50, 80)  # Distance East (km)
y = np.linspace(0, 40, 64)  # Distance North (km)
X, Y = np.meshgrid(x, y)

# Create realistic elevation surface with multiple terrain features:
# - Main peak in the northeast
# - Secondary peak in the southwest
# - Valley running between them
z_peak1 = 2800 * np.exp(-((X - 35) ** 2 + (Y - 30) ** 2) / 150)  # Main peak
z_peak2 = 2200 * np.exp(-((X - 12) ** 2 + (Y - 10) ** 2) / 100)  # Secondary peak
z_ridge = 800 * np.exp(-((X - 25) ** 2) / 300)  # Connecting ridge
z_base = 400 + 15 * X + 10 * Y  # Gradual slope (higher to northeast)
Z = z_base + z_peak1 + z_peak2 + z_ridge  # Combined elevation

# Create plot (4800x2700 px at 300 dpi = 16x9 inches)
fig, ax = plt.subplots(figsize=(16, 9))

# Create filled contours using matplotlib (seaborn provides styling context)
levels = np.linspace(Z.min(), Z.max(), 15)
contourf = ax.contourf(X, Y, Z, levels=levels, cmap="viridis", alpha=0.9)

# Add contour lines with labels for key elevation levels
contour = ax.contour(X, Y, Z, levels=levels, colors="white", linewidths=0.8, alpha=0.8)

# Label contour levels at practical intervals (every 3rd level for clarity)
label_levels = levels[::3]
ax.clabel(contour, levels=label_levels, inline=True, fontsize=14, fmt="%d m", colors="white")

# Add colorbar with proper sizing
cbar = fig.colorbar(contourf, ax=ax, shrink=0.85, pad=0.02)
cbar.set_label("Elevation (m)", fontsize=20)
cbar.ax.tick_params(labelsize=16)

# Labels and styling
ax.set_xlabel("Distance East (km)", fontsize=20)
ax.set_ylabel("Distance North (km)", fontsize=20)
ax.set_title("contour-basic · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
