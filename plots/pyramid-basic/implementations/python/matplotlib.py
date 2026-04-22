""" pyplots.ai
pyramid-basic: Basic Pyramid Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Population pyramid showing age distribution by gender
age_groups = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]
male = np.array([4.8, 5.2, 6.1, 7.3, 8.5, 7.8, 5.9, 3.2, 1.2])  # Millions
female = np.array([4.5, 5.0, 6.3, 7.5, 8.7, 8.2, 6.4, 4.1, 2.1])  # Millions

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Create pyramid - male extends left (negative), female extends right (positive)
y_pos = np.arange(len(age_groups))
bar_height = 0.7

ax.barh(y_pos, -male, height=bar_height, color="#306998", label="Male")
ax.barh(y_pos, female, height=bar_height, color="#FFD43B", label="Female")

# Symmetric axis for fair comparison
max_val = max(male.max(), female.max())
ax.set_xlim(-max_val * 1.15, max_val * 1.15)

# Labels and styling
ax.set_yticks(y_pos)
ax.set_yticklabels(age_groups)
ax.set_xlabel("Population (millions)", fontsize=20)
ax.set_ylabel("Age Group", fontsize=20)
ax.set_title("pyramid-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Format x-axis to show absolute values
ax.set_xticks([-8, -6, -4, -2, 0, 2, 4, 6, 8])
ax.set_xticklabels(["8", "6", "4", "2", "0", "2", "4", "6", "8"])

# Add legend
ax.legend(fontsize=16, loc="upper right")

# Subtle grid
ax.grid(True, alpha=0.3, linestyle="--", axis="x")

# Add center line
ax.axvline(x=0, color="black", linewidth=1.5)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
