""" pyplots.ai
radar-basic: Basic Radar Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Employee performance comparison across competencies (deterministic, no random)
categories = ["Communication", "Technical Skills", "Teamwork", "Problem Solving", "Leadership", "Creativity"]
employee_a = [85, 90, 78, 88, 72, 80]  # Senior Developer
employee_b = [75, 70, 92, 65, 85, 88]  # Team Lead

# Number of variables
num_vars = len(categories)

# Compute angle for each axis
angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()

# Close the polygons by appending first value
employee_a_closed = employee_a + [employee_a[0]]
employee_b_closed = employee_b + [employee_b[0]]
angles_closed = angles + [angles[0]]

# Create square plot (better for radar charts)
_, ax = plt.subplots(figsize=(12, 12), subplot_kw={"polar": True})

# Plot Employee A (Python Blue)
ax.fill(angles_closed, employee_a_closed, color="#306998", alpha=0.25)
ax.plot(
    angles_closed, employee_a_closed, color="#306998", linewidth=3, marker="o", markersize=12, label="Senior Developer"
)

# Plot Employee B (Python Yellow)
ax.fill(angles_closed, employee_b_closed, color="#FFD43B", alpha=0.25)
ax.plot(angles_closed, employee_b_closed, color="#FFD43B", linewidth=3, marker="o", markersize=12, label="Team Lead")

# Set the angle for each axis label
ax.set_xticks(angles)
ax.set_xticklabels(categories, fontsize=18)

# Set radial limits and gridlines
ax.set_ylim(0, 100)
ax.set_yticks([20, 40, 60, 80, 100])

# Position radial tick labels outside the chart for better clarity
ax.set_rlabel_position(22.5)  # Move labels to 22.5 degrees for better visibility
ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=14, color="#555555", fontweight="medium")

# Style grid
ax.grid(True, alpha=0.4, linestyle="--", linewidth=1.5)

# Title
ax.set_title("Employee Performance · radar-basic · matplotlib · pyplots.ai", fontsize=24, pad=40)

# Legend (positioned to not cover data)
ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.05), fontsize=16)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
