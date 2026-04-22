""" pyplots.ai
ecdf-basic: Basic ECDF Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - random samples from a normal distribution
np.random.seed(42)
values = np.random.normal(loc=50, scale=15, size=200)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Plot ECDF
sns.ecdfplot(data=values, ax=ax, linewidth=3, color="#306998")

# Styling
ax.set_xlabel("Value", fontsize=20)
ax.set_ylabel("Cumulative Proportion", fontsize=20)
ax.set_title("ecdf-basic · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")

# Ensure y-axis ranges from 0 to 1
ax.set_ylim(0, 1)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
