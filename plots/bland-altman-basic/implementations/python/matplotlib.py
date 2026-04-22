""" pyplots.ai
bland-altman-basic: Bland-Altman Agreement Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import matplotlib.pyplot as plt
import numpy as np


# Data: Simulated blood pressure readings from two sphygmomanometers
np.random.seed(42)
n_samples = 80

# Method 1: Reference sphygmomanometer
method1 = np.random.normal(120, 15, n_samples)

# Method 2: New sphygmomanometer (slightly biased with some random error)
bias_true = 2.5  # Small systematic difference
method2 = method1 + bias_true + np.random.normal(0, 5, n_samples)

# Bland-Altman calculations
mean_values = (method1 + method2) / 2
differences = method1 - method2

mean_diff = np.mean(differences)
std_diff = np.std(differences, ddof=1)
upper_loa = mean_diff + 1.96 * std_diff
lower_loa = mean_diff - 1.96 * std_diff

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Scatter points with transparency for overlapping observations
ax.scatter(mean_values, differences, s=150, alpha=0.6, color="#306998", edgecolors="white", linewidth=0.5)

# Mean difference (bias) line
ax.axhline(y=mean_diff, color="#306998", linestyle="-", linewidth=2.5, label=f"Mean: {mean_diff:.2f} mmHg")

# Limits of agreement (dashed lines)
ax.axhline(y=upper_loa, color="#FFD43B", linestyle="--", linewidth=2.5, label=f"+1.96 SD: {upper_loa:.2f} mmHg")
ax.axhline(y=lower_loa, color="#FFD43B", linestyle="--", linewidth=2.5, label=f"-1.96 SD: {lower_loa:.2f} mmHg")

# Zero reference line (subtle)
ax.axhline(y=0, color="gray", linestyle=":", linewidth=1.5, alpha=0.5)

# Annotations on the right side
x_max = ax.get_xlim()[1]
ax.text(
    x_max + 1,
    mean_diff,
    f"Bias: {mean_diff:.2f}",
    fontsize=14,
    va="center",
    ha="left",
    color="#306998",
    fontweight="bold",
)
ax.text(x_max + 1, upper_loa, f"+1.96 SD: {upper_loa:.2f}", fontsize=14, va="center", ha="left", color="#D4A000")
ax.text(x_max + 1, lower_loa, f"-1.96 SD: {lower_loa:.2f}", fontsize=14, va="center", ha="left", color="#D4A000")

# Labels and title
ax.set_xlabel("Mean of Two Methods (mmHg)", fontsize=20)
ax.set_ylabel("Difference (Method 1 - Method 2) (mmHg)", fontsize=20)
ax.set_title("bland-altman-basic \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24)

# Tick parameters
ax.tick_params(axis="both", labelsize=16)

# Grid
ax.grid(True, alpha=0.3, linestyle="--")

# Legend
ax.legend(fontsize=14, loc="upper left")

# Adjust layout to make room for annotations
plt.tight_layout()
plt.subplots_adjust(right=0.85)

plt.savefig("plot.png", dpi=300, bbox_inches="tight")
