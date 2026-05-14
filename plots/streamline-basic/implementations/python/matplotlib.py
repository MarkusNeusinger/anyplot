""" anyplot.ai
streamline-basic: Basic Streamline Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-14
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Create a more complex flow field showing vortex and source features
np.random.seed(42)

# Grid setup (40x40 for smooth streamlines)
x = np.linspace(-3, 3, 40)
y = np.linspace(-3, 3, 40)
X, Y = np.meshgrid(x, y)

# Create a more interesting flow field combining vortex and source patterns
# Vortex: u = -y, v = x (circular flow)
# Add a source/sink at (0, 0): radial outflow
# Add secondary vortex at (1.5, 0): counterclockwise rotation
U = -0.8 * Y + 0.3 * X / (X**2 + Y**2 + 0.1)
V = 0.8 * X + 0.3 * Y / (X**2 + Y**2 + 0.1)

# Secondary vortex contribution
dx, dy = X - 1.5, Y
U += -0.4 * dy / ((dx**2 + dy**2 + 0.5) ** 0.5)
V += 0.4 * dx / ((dx**2 + dy**2 + 0.5) ** 0.5)

# Calculate velocity magnitude for color and linewidth encoding
speed = np.sqrt(U**2 + V**2)
speed_norm = (speed - speed.min()) / (speed.max() - speed.min() + 1e-6)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Create streamlines with color based on velocity magnitude
strm = ax.streamplot(
    X,
    Y,
    U,
    V,
    color=speed,
    cmap="viridis",
    linewidth=1.5 + 2.5 * speed_norm,  # Linewidth varies with speed
    density=1.5,
    arrowsize=2,
    arrowstyle="->",
)

# Colorbar for velocity magnitude
cbar = fig.colorbar(strm.lines, ax=ax, shrink=0.8, pad=0.02)
cbar.set_label("Velocity Magnitude", fontsize=20, color=INK)
cbar.ax.tick_params(labelsize=16, colors=INK_SOFT)
cbar.outline.set_color(INK_SOFT)
cbar.outline.set_linewidth(0.5)

# Styling
ax.set_xlabel("X Position (m)", fontsize=20, color=INK)
ax.set_ylabel("Y Position (m)", fontsize=20, color=INK)
ax.set_title("streamline-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.set_aspect("equal")

# Grid styling - subtle solid lines
ax.grid(True, alpha=0.10, linestyle="-", linewidth=0.8, color=INK)

# Spine styling
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
    ax.spines[s].set_linewidth(0.5)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
