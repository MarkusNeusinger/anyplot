""" pyplots.ai
bland-altman-basic: Bland-Altman Agreement Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-25
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - Simulated blood pressure measurements from two sphygmomanometers
np.random.seed(42)
n = 80

# Method 1: Reference standard (e.g., mercury sphygmomanometer)
method1 = np.random.normal(120, 15, n)

# Method 2: New device with slight systematic bias and proportional error
method2 = method1 + np.random.normal(2, 5, n) + 0.02 * (method1 - 120)

# Calculate Bland-Altman statistics
mean_values = (method1 + method2) / 2
differences = method1 - method2
mean_diff = np.mean(differences)
std_diff = np.std(differences, ddof=1)
upper_loa = mean_diff + 1.96 * std_diff
lower_loa = mean_diff - 1.96 * std_diff

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Scatter plot of differences vs means using seaborn
sns.scatterplot(
    x=mean_values, y=differences, s=150, alpha=0.7, color="#306998", edgecolor="white", linewidth=0.5, ax=ax
)

# Mean difference line (bias)
ax.axhline(y=mean_diff, color="#FFD43B", linewidth=3, label=f"Mean: {mean_diff:.2f} mmHg")

# Limits of agreement (±1.96 SD)
ax.axhline(y=upper_loa, color="#E74C3C", linewidth=2, linestyle="--", label=f"+1.96 SD: {upper_loa:.2f} mmHg")
ax.axhline(y=lower_loa, color="#E74C3C", linewidth=2, linestyle="--", label=f"-1.96 SD: {lower_loa:.2f} mmHg")

# Zero reference line
ax.axhline(y=0, color="gray", linewidth=1, linestyle=":", alpha=0.5)

# Annotate values on the right side
x_max = ax.get_xlim()[1]
ax.annotate(
    f"{mean_diff:.1f}",
    xy=(x_max, mean_diff),
    xytext=(5, 0),
    textcoords="offset points",
    fontsize=16,
    color="#FFD43B",
    fontweight="bold",
    va="center",
)
ax.annotate(
    f"{upper_loa:.1f}",
    xy=(x_max, upper_loa),
    xytext=(5, 0),
    textcoords="offset points",
    fontsize=14,
    color="#E74C3C",
    va="center",
)
ax.annotate(
    f"{lower_loa:.1f}",
    xy=(x_max, lower_loa),
    xytext=(5, 0),
    textcoords="offset points",
    fontsize=14,
    color="#E74C3C",
    va="center",
)

# Labels and styling
ax.set_xlabel("Mean of Two Methods (mmHg)", fontsize=20)
ax.set_ylabel("Difference (Method 1 - Method 2) (mmHg)", fontsize=20)
ax.set_title("bland-altman-basic · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")

# Legend
ax.legend(loc="upper left", fontsize=14, framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
