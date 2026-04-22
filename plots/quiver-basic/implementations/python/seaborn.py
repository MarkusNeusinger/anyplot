""" pyplots.ai
quiver-basic: Basic Quiver Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - create a circular rotation pattern (u = -y, v = x)
np.random.seed(42)
grid_size = 15
x_vals = np.linspace(-3, 3, grid_size)
y_vals = np.linspace(-3, 3, grid_size)
X, Y = np.meshgrid(x_vals, y_vals)
x = X.flatten()
y = Y.flatten()

# Vector components: rotation field
u = -y
v = x

# Calculate magnitude for each vector
magnitude = np.sqrt(u**2 + v**2)

# Scale vectors for visibility (avoid division by zero)
scale = 0.15
mag_safe = np.where(magnitude > 0, magnitude, 1)
u_scaled = np.where(magnitude > 0, u / mag_safe * scale, 0)
v_scaled = np.where(magnitude > 0, v / mag_safe * scale, 0)

# Calculate end points
x_end = x + u_scaled
y_end = y + v_scaled

# Build line data for seaborn - each arrow is represented by line segments
# We'll create arrow shafts and arrowheads as separate line groups
line_data = []

# Arrowhead parameters
head_length = 0.05
head_angle = 0.45  # radians

for i in range(len(x)):
    mag = magnitude[i]
    if mag < 0.01:
        continue

    # Arrow shaft line segment
    angle = np.arctan2(v_scaled[i], u_scaled[i])

    # Create shaft segment data
    line_data.append({"x": x[i], "y": y[i], "segment": f"arrow_{i}", "order": 0, "magnitude": mag})
    line_data.append({"x": x_end[i], "y": y_end[i], "segment": f"arrow_{i}", "order": 1, "magnitude": mag})

    # Create arrowhead left barb
    left_x = x_end[i] - head_length * np.cos(angle - head_angle)
    left_y = y_end[i] - head_length * np.sin(angle - head_angle)
    line_data.append({"x": x_end[i], "y": y_end[i], "segment": f"head_l_{i}", "order": 0, "magnitude": mag})
    line_data.append({"x": left_x, "y": left_y, "segment": f"head_l_{i}", "order": 1, "magnitude": mag})

    # Create arrowhead right barb
    right_x = x_end[i] - head_length * np.cos(angle + head_angle)
    right_y = y_end[i] - head_length * np.sin(angle + head_angle)
    line_data.append({"x": x_end[i], "y": y_end[i], "segment": f"head_r_{i}", "order": 0, "magnitude": mag})
    line_data.append({"x": right_x, "y": right_y, "segment": f"head_r_{i}", "order": 1, "magnitude": mag})

df = pd.DataFrame(line_data)

# Set seaborn style
sns.set_theme(style="whitegrid")

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Plot arrows using seaborn lineplot with units parameter to separate segments
sns.lineplot(
    data=df,
    x="x",
    y="y",
    hue="magnitude",
    units="segment",
    estimator=None,
    sort=False,
    palette="viridis",
    linewidth=2.5,
    legend=False,
    ax=ax,
)

# Add colorbar for magnitude
norm = plt.Normalize(magnitude.min(), magnitude.max())
sm = plt.cm.ScalarMappable(cmap="viridis", norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, shrink=0.8, pad=0.02)
cbar.set_label("Vector Magnitude", fontsize=20)
cbar.ax.tick_params(labelsize=16)

# Styling
ax.set_xlabel("X Position", fontsize=20)
ax.set_ylabel("Y Position", fontsize=20)
ax.set_title("quiver-basic · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.set_aspect("equal")
ax.grid(True, alpha=0.3, linestyle="--")

# Set axis limits
ax.set_xlim(-3.5, 3.5)
ax.set_ylim(-3.5, 3.5)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
