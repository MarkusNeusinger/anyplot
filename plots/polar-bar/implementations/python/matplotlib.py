""" pyplots.ai
polar-bar: Polar Bar Chart (Wind Rose)
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Wind direction frequencies (8 compass directions)
np.random.seed(42)
directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
n_directions = len(directions)

# Convert directions to angles (in radians, starting from N=0, clockwise)
angles = np.linspace(0, 2 * np.pi, n_directions, endpoint=False)

# Generate wind frequency data for 3 speed categories (stacked bars)
# Calm (0-5 m/s), Moderate (5-10 m/s), Strong (>10 m/s)
calm = np.array([12, 8, 15, 6, 18, 10, 22, 14])
moderate = np.array([8, 5, 10, 4, 12, 7, 15, 9])
strong = np.array([4, 2, 5, 2, 6, 3, 8, 4])

# Bar width (slightly less than full sector for visual separation)
width = 2 * np.pi / n_directions * 0.8

# Create polar plot (square format works well for radial charts)
fig, ax = plt.subplots(figsize=(12, 12), subplot_kw={"projection": "polar"})

# Plot stacked bars with Python colors and a third complementary color
bars1 = ax.bar(
    angles,
    calm,
    width=width,
    bottom=0,
    color="#306998",
    edgecolor="white",
    linewidth=1.5,
    label="Calm (0-5 m/s)",
    alpha=0.9,
)
bars2 = ax.bar(
    angles,
    moderate,
    width=width,
    bottom=calm,
    color="#FFD43B",
    edgecolor="white",
    linewidth=1.5,
    label="Moderate (5-10 m/s)",
    alpha=0.9,
)
bars3 = ax.bar(
    angles,
    strong,
    width=width,
    bottom=calm + moderate,
    color="#4ECDC4",
    edgecolor="white",
    linewidth=1.5,
    label="Strong (>10 m/s)",
    alpha=0.9,
)

# Configure polar axes
ax.set_theta_zero_location("N")  # North at top
ax.set_theta_direction(-1)  # Clockwise

# Set direction labels
ax.set_xticks(angles)
ax.set_xticklabels(directions, fontsize=18, fontweight="bold")

# Configure radial axis
ax.set_ylim(0, 50)
ax.set_yticks([10, 20, 30, 40])
ax.set_yticklabels(["10%", "20%", "30%", "40%"], fontsize=14)
ax.set_rlabel_position(45)  # Move radial labels to avoid overlap

# Grid styling
ax.grid(True, alpha=0.3, linestyle="--", linewidth=1)

# Title
ax.set_title("polar-bar · matplotlib · pyplots.ai", fontsize=24, pad=30, fontweight="bold")

# Legend
ax.legend(
    loc="upper left", bbox_to_anchor=(1.05, 1), fontsize=14, title="Wind Speed", title_fontsize=16, framealpha=0.9
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
