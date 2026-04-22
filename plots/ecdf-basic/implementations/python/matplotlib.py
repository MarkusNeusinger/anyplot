""" pyplots.ai
ecdf-basic: Basic ECDF Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np


# Data
np.random.seed(42)
values = np.random.normal(loc=50, scale=15, size=200)

# Sort values and compute ECDF
sorted_values = np.sort(values)
ecdf = np.arange(1, len(sorted_values) + 1) / len(sorted_values)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
ax.step(sorted_values, ecdf, where="post", linewidth=3, color="#306998")

# Styling
ax.set_xlabel("Value", fontsize=20)
ax.set_ylabel("Cumulative Proportion", fontsize=20)
ax.set_title("ecdf-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.set_ylim(0, 1)
ax.grid(True, alpha=0.3, linestyle="--")

# Add horizontal reference lines for quartiles (Q1, Median, Q3)
for q in [0.25, 0.5, 0.75]:
    ax.axhline(y=q, color="#FFD43B", linestyle=":", linewidth=2, alpha=0.7)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
