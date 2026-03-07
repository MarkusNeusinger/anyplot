"""pyplots.ai
bar-tornado-sensitivity: Tornado Diagram for Sensitivity Analysis
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-03-07
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - NPV sensitivity analysis for a capital investment project
parameters = [
    "Discount Rate",
    "Revenue Growth",
    "Material Cost",
    "Labor Cost",
    "Tax Rate",
    "Initial Investment",
    "Operating Margin",
    "Terminal Value",
    "Working Capital",
    "Inflation Rate",
]

base_npv = 120.0  # Base case NPV in $M

np.random.seed(42)
low_values = base_npv + np.array([-38, -30, -25, -18, -15, -14, -10, -8, -5, -3], dtype=float)
high_values = base_npv + np.array([32, 28, 20, 22, 12, 11, 13, 9, 6, 4], dtype=float)

# Calculate ranges and sort by total impact
total_range = high_values - low_values
sort_idx = np.argsort(total_range)
parameters = [parameters[i] for i in sort_idx]
low_values = low_values[sort_idx]
high_values = high_values[sort_idx]

# Build bar data relative to base case
low_delta = low_values - base_npv
high_delta = high_values - base_npv

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

y_pos = np.arange(len(parameters))

ax.barh(y_pos, low_delta, left=base_npv, height=0.6, color="#D95F02", label="Low Scenario", zorder=2)
ax.barh(y_pos, high_delta, left=base_npv, height=0.6, color="#306998", label="High Scenario", zorder=2)

# Base case reference line
ax.axvline(x=base_npv, color="#333333", linewidth=1.5, linestyle="--", zorder=3)

# Style
ax.set_yticks(y_pos)
ax.set_yticklabels(parameters, fontsize=16)
ax.set_xlabel("Net Present Value ($M)", fontsize=20)
ax.set_title("bar-tornado-sensitivity · seaborn · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="x", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.xaxis.grid(True, alpha=0.2, linewidth=0.8)

ax.legend(fontsize=16, frameon=False, loc="lower right")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
