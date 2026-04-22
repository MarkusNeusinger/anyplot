""" pyplots.ai
dumbbell-basic: Basic Dumbbell Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 95/100 | Created: 2025-12-15
"""

import matplotlib.pyplot as plt
import numpy as np


# Data: Employee satisfaction scores before and after workplace policy changes
categories = ["Engineering", "Marketing", "Sales", "HR", "Finance", "Operations", "Customer Support", "Product"]
before_scores = [65, 58, 72, 45, 68, 52, 40, 75]
after_scores = [82, 71, 78, 73, 75, 68, 62, 88]

# Sort by difference (largest improvement first)
differences = [a - b for a, b in zip(after_scores, before_scores, strict=True)]
sorted_indices = np.argsort(differences)[::-1]
categories = [categories[i] for i in sorted_indices]
before_scores = [before_scores[i] for i in sorted_indices]
after_scores = [after_scores[i] for i in sorted_indices]

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

y_positions = np.arange(len(categories))

# Draw connecting lines (thin and subtle)
for i, (start, end) in enumerate(zip(before_scores, after_scores, strict=True)):
    ax.plot([start, end], [i, i], color="#888888", linewidth=2, zorder=1)

# Draw dots with distinct colors
ax.scatter(
    before_scores, y_positions, s=300, color="#306998", label="Before", zorder=2, edgecolors="white", linewidths=2
)
ax.scatter(after_scores, y_positions, s=300, color="#FFD43B", label="After", zorder=2, edgecolors="white", linewidths=2)

# Labels and styling
ax.set_yticks(y_positions)
ax.set_yticklabels(categories)
ax.set_xlabel("Satisfaction Score", fontsize=20)
ax.set_ylabel("Department", fontsize=20)
ax.set_title("dumbbell-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(30, 100)
ax.grid(True, axis="x", alpha=0.3, linestyle="--")
ax.legend(fontsize=16, loc="lower right")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
