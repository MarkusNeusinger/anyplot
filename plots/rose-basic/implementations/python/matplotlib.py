""" pyplots.ai
rose-basic: Basic Rose Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Monthly rainfall (mm) showing seasonal patterns
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
values = np.array([85, 72, 95, 110, 145, 160, 180, 165, 130, 105, 90, 80])

# Calculate angles - equal segments
n_categories = len(months)
angles = np.linspace(0, 2 * np.pi, n_categories, endpoint=False)

# Create polar plot (4800x2700 px at 300 dpi)
fig, ax = plt.subplots(figsize=(16, 9), subplot_kw={"projection": "polar"})

# Style the polar plot - set BEFORE plotting
ax.set_theta_zero_location("N")  # Start from top (12 o'clock)
ax.set_theta_direction(-1)  # Clockwise

# Calculate bar width to fill the circle
width = 2 * np.pi / n_categories * 0.9

# Create rose chart using bar plot
ax.bar(angles, values, width=width, bottom=0, color="#306998", edgecolor="white", linewidth=2, alpha=0.85)

# Set category labels at each angle
ax.set_xticks(angles)
ax.set_xticklabels(months, fontsize=18, fontweight="bold")

# Add radial gridlines with labels
ax.set_ylim(0, max(values) * 1.15)
ax.yaxis.set_tick_params(labelsize=14)

# Style the radial grid
ax.grid(True, alpha=0.3, linestyle="--", linewidth=1.5)
ax.spines["polar"].set_visible(True)
ax.spines["polar"].set_linewidth(2)
ax.spines["polar"].set_color("#306998")

# Title
ax.set_title("Monthly Rainfall (mm) · rose-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="bold", pad=30)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
