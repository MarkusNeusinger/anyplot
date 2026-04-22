""" pyplots.ai
qq-basic: Basic Q-Q Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - sample with slight right skew to demonstrate Q-Q plot characteristics
np.random.seed(42)
sample = np.concatenate(
    [
        np.random.normal(loc=50, scale=10, size=80),  # Main bulk of data
        np.random.normal(loc=75, scale=5, size=20),  # Slight right tail for asymmetry
    ]
)

# Sort sample and calculate quantile positions
sample_sorted = np.sort(sample)
n = len(sample_sorted)
probabilities = (np.arange(1, n + 1) - 0.5) / n

# Inverse normal CDF using Abramowitz & Stegun approximation (accurate to ~1.5e-7)
a = [
    -3.969683028665376e01,
    2.209460984245205e02,
    -2.759285104469687e02,
    1.383577518672690e02,
    -3.066479806614716e01,
    2.506628277459239e00,
]
b = [-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02, 6.680131188771972e01, -1.328068155288572e01]
c = [
    -7.784894002430293e-03,
    -3.223964580411365e-01,
    -2.400758277161838e00,
    -2.549732539343734e00,
    4.374664141464968e00,
    2.938163982698783e00,
]
d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00, 3.754408661907416e00]

p_low, p_high = 0.02425, 1 - 0.02425
theoretical_quantiles = np.zeros(n)

# Low region
mask_low = probabilities < p_low
q = np.sqrt(-2 * np.log(probabilities[mask_low]))
theoretical_quantiles[mask_low] = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
    (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1
)

# Central region
mask_mid = (probabilities >= p_low) & (probabilities <= p_high)
q = probabilities[mask_mid] - 0.5
r = q * q
theoretical_quantiles[mask_mid] = (
    (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5])
    * q
    / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
)

# High region
mask_high = probabilities > p_high
q = np.sqrt(-2 * np.log(1 - probabilities[mask_high]))
theoretical_quantiles[mask_high] = -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
    (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1
)

# Standardize sample to z-scores for comparison with standard normal quantiles
sample_mean = np.mean(sample_sorted)
sample_std = np.std(sample_sorted, ddof=1)
sample_quantiles = (sample_sorted - sample_mean) / sample_std

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Q-Q points
ax.scatter(
    theoretical_quantiles,
    sample_quantiles,
    s=200,
    alpha=0.7,
    color="#306998",
    edgecolors="white",
    linewidths=1.5,
    zorder=3,
)

# Reference line (y = x) showing perfect normal distribution match
line_min = min(theoretical_quantiles.min(), sample_quantiles.min())
line_max = max(theoretical_quantiles.max(), sample_quantiles.max())
ax.plot(
    [line_min, line_max],
    [line_min, line_max],
    color="#FFD43B",
    linewidth=3,
    linestyle="--",
    label="Reference line (y=x)",
    zorder=2,
)

# Labels and styling
ax.set_xlabel("Theoretical Quantiles", fontsize=20)
ax.set_ylabel("Sample Quantiles", fontsize=20)
ax.set_title("qq-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper left")
ax.grid(True, alpha=0.3, linestyle="--", zorder=1)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
