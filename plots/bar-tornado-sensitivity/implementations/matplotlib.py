""" pyplots.ai
bar-tornado-sensitivity: Tornado Diagram for Sensitivity Analysis
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-07
"""

import matplotlib.pyplot as plt
import numpy as np


# Data — NPV sensitivity analysis for a capital investment project
base_npv = 12.5  # Base case NPV in $M

parameters = [
    "Discount Rate",
    "Revenue Growth",
    "Initial CapEx",
    "Operating Costs",
    "Tax Rate",
    "Terminal Value",
    "Working Capital",
    "Inflation Rate",
    "Project Duration",
    "Salvage Value",
]

low_npv = np.array([16.8, 8.2, 14.9, 15.1, 14.0, 10.1, 13.6, 13.4, 10.9, 11.8])
high_npv = np.array([9.1, 17.3, 10.4, 10.2, 11.2, 15.4, 11.5, 11.7, 14.3, 13.3])

# Sort by total range (widest bar at top)
total_range = np.abs(high_npv - low_npv)
sort_idx = np.argsort(total_range)
parameters = [parameters[i] for i in sort_idx]
low_npv = low_npv[sort_idx]
high_npv = high_npv[sort_idx]

# Compute bar segments relative to base
low_delta = low_npv - base_npv
high_delta = high_npv - base_npv

y_pos = np.arange(len(parameters))

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

ax.barh(
    y_pos, low_delta, left=base_npv, height=0.6, color="#4A90D9", label="Low Scenario", edgecolor="white", linewidth=0.5
)
ax.barh(
    y_pos,
    high_delta,
    left=base_npv,
    height=0.6,
    color="#D94A4A",
    label="High Scenario",
    edgecolor="white",
    linewidth=0.5,
)

# Base case reference line
ax.axvline(x=base_npv, color="#333333", linewidth=1.5, linestyle="-", zorder=3)

# Style
ax.set_yticks(y_pos)
ax.set_yticklabels(parameters, fontsize=16)
ax.set_xlabel("Net Present Value ($M)", fontsize=20)
ax.set_title("bar-tornado-sensitivity · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="x", labelsize=16)
ax.tick_params(axis="y", length=0)
ax.legend(fontsize=16, loc="lower right", frameon=False)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.xaxis.grid(True, alpha=0.2, linewidth=0.8)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
