""" pyplots.ai
rose-basic: Basic Rose Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data: Monthly rainfall (mm) showing seasonal patterns
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
rainfall = [89, 72, 95, 112, 135, 168, 142, 125, 98, 76, 82, 91]

# Calculate angles - start at top (12 o'clock position)
n_categories = len(months)
angles = np.linspace(0, 2 * np.pi, n_categories, endpoint=False)

# Bar width (slightly less than full segment for gaps)
width = 2 * np.pi / n_categories * 0.85

# Create figure with polar projection (square format for radial plot)
fig, ax = plt.subplots(figsize=(12, 12), subplot_kw={"projection": "polar"})

# Use seaborn color palette - Blues gradient for rainfall theme
palette = sns.color_palette("Blues", n_colors=n_categories)

# Plot bars - radius proportional to value
ax.bar(angles, rainfall, width=width, bottom=0, color=palette, edgecolor="white", linewidth=2, alpha=0.9)

# Configure polar axis - start at top, go clockwise
ax.set_theta_offset(np.pi / 2)  # Start at top (12 o'clock)
ax.set_theta_direction(-1)  # Clockwise direction

# Set category labels at correct positions
ax.set_xticks(angles)
ax.set_xticklabels(months, fontsize=20, fontweight="bold")

# Configure radial gridlines and labels
max_val = max(rainfall)
ax.set_ylim(0, max_val * 1.15)
ax.set_yticks([50, 100, 150])
ax.set_yticklabels(["50 mm", "100 mm", "150 mm"], fontsize=14, color="#555555")

# Style the grid
ax.grid(True, alpha=0.3, linestyle="--", linewidth=1.5, color="#888888")
ax.spines["polar"].set_visible(False)

# Add title with proper formatting
ax.set_title(
    "Monthly Rainfall (mm) · rose-basic · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=35, color="#333333"
)

# Add value labels on each bar
for angle, value in zip(angles, rainfall, strict=True):
    # Position label just outside the bar
    label_radius = value + 12
    ax.text(angle, label_radius, f"{value}", ha="center", va="center", fontsize=14, fontweight="bold", color="#306998")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
