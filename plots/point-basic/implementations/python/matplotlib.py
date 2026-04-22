""" pyplots.ai
point-basic: Point Estimate Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 99/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Customer satisfaction scores by department with 95% confidence intervals
np.random.seed(42)

departments = ["Customer Service", "Technical Support", "Sales", "Billing", "Shipping", "Product Quality", "Returns"]

# Simulated mean satisfaction scores (1-10 scale) with varying confidence intervals
estimates = np.array([7.8, 6.2, 7.1, 5.4, 8.3, 6.9, 5.8])
# Different CI widths show varying sample sizes/uncertainty
ci_lower = np.array([7.2, 5.4, 6.5, 4.6, 7.9, 6.2, 5.1])
ci_upper = np.array([8.4, 7.0, 7.7, 6.2, 8.7, 7.6, 6.5])

# Calculate errors for errorbar (asymmetric)
lower_errors = estimates - ci_lower
upper_errors = ci_upper - estimates

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Create horizontal point estimate plot with error bars
y_positions = np.arange(len(departments))

ax.errorbar(
    estimates,
    y_positions,
    xerr=[lower_errors, upper_errors],
    fmt="o",
    color="#306998",
    markersize=14,
    markeredgecolor="white",
    markeredgewidth=2,
    capsize=8,
    capthick=2.5,
    elinewidth=2.5,
    ecolor="#306998",
)

# Add reference line at overall mean
overall_mean = np.mean(estimates)
ax.axvline(x=overall_mean, color="#FFD43B", linestyle="--", linewidth=2.5, alpha=0.8)
ax.text(
    overall_mean + 0.05,
    len(departments) - 0.3,
    f"Overall Mean: {overall_mean:.1f}",
    fontsize=16,
    color="#B8860B",
    fontweight="bold",
)

# Styling
ax.set_yticks(y_positions)
ax.set_yticklabels(departments)
ax.set_xlabel("Satisfaction Score (1-10)", fontsize=20)
ax.set_ylabel("Department", fontsize=20)
ax.set_title("point-basic \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Set x-axis limits with padding
ax.set_xlim(3.5, 9.5)
ax.set_ylim(-0.5, len(departments) - 0.5)

# Grid - subtle horizontal lines
ax.grid(True, axis="x", alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

# Invert y-axis so first category is at top
ax.invert_yaxis()

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
