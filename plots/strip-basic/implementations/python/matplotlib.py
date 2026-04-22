""" pyplots.ai
strip-basic: Basic Strip Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Survey response scores by department
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "HR"]
n_per_group = [45, 38, 52, 35]

categories = []
values = []

# Generate realistic survey scores (1-10 scale) with different distributions
distributions = {
    "Engineering": (7.2, 1.5),  # Higher scores, moderate spread
    "Marketing": (6.5, 1.8),  # Medium scores, wider spread
    "Sales": (7.8, 1.2),  # Highest scores, tight spread
    "HR": (6.0, 2.0),  # Lower scores, widest spread
}

for dept, n in zip(departments, n_per_group, strict=True):
    mean, std = distributions[dept]
    scores = np.clip(np.random.normal(mean, std, n), 1, 10)
    categories.extend([dept] * n)
    values.extend(scores)

values = np.array(values)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Plot strip plot with jitter
colors = ["#306998", "#FFD43B", "#306998", "#FFD43B"]  # Alternating Python colors

for i, dept in enumerate(departments):
    mask = np.array(categories) == dept
    dept_values = values[mask]

    # Add random jitter for x-position (0.2 spread)
    jitter = np.random.uniform(-0.2, 0.2, len(dept_values))
    x_positions = np.full(len(dept_values), i) + jitter

    ax.scatter(x_positions, dept_values, s=200, alpha=0.6, color=colors[i], edgecolors="white", linewidth=0.5)

# Add horizontal lines for group means
for i, dept in enumerate(departments):
    mask = np.array(categories) == dept
    mean_val = values[mask].mean()
    ax.hlines(mean_val, i - 0.35, i + 0.35, colors="#333333", linewidth=2.5, linestyles="-")

# Styling
ax.set_xticks(range(len(departments)))
ax.set_xticklabels(departments)
ax.set_xlabel("Department", fontsize=20)
ax.set_ylabel("Survey Response Score", fontsize=20)
ax.set_title("strip-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.set_ylim(0, 11)
ax.grid(True, alpha=0.3, linestyle="--", axis="y")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
