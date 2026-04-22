""" pyplots.ai
errorbar-basic: Basic Error Bar Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - experimental measurements with associated uncertainties
np.random.seed(42)
categories = ["Control", "Treatment A", "Treatment B", "Treatment C", "Treatment D", "Treatment E"]
x = np.arange(len(categories))
y = np.array([25.3, 38.7, 42.1, 35.8, 48.2, 31.5])  # Mean values

# Asymmetric errors: Treatment C and D have notably different lower/upper bounds
asymmetric_lower = np.array([2.1, 3.5, 2.8, 6.5, 4.8, 2.5])
asymmetric_upper = np.array([2.1, 3.5, 2.8, 2.8, 2.2, 2.5])

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Error bars with caps
ax.errorbar(
    x,
    y,
    yerr=[asymmetric_lower, asymmetric_upper],
    fmt="o",
    markersize=15,
    color="#306998",
    ecolor="#306998",
    elinewidth=3,
    capsize=10,
    capthick=3,
    alpha=0.9,
)

# Styling
ax.set_xlabel("Experimental Group", fontsize=20)
ax.set_ylabel("Response Value (units)", fontsize=20)
ax.set_title("errorbar-basic · matplotlib · pyplots.ai", fontsize=24)
ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=16)
ax.tick_params(axis="y", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--", axis="y")

# Add some vertical padding
ax.set_ylim(0, max(y + asymmetric_upper) * 1.15)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
