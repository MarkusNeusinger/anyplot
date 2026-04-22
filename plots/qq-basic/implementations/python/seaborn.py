""" pyplots.ai
qq-basic: Basic Q-Q Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - mixture with slight right skewness to demonstrate Q-Q plot interpretation
np.random.seed(42)
sample = np.concatenate(
    [
        np.random.normal(loc=50, scale=10, size=180),  # Main distribution
        np.random.normal(loc=75, scale=5, size=20),  # Right tail deviation
    ]
)

# Calculate theoretical quantiles using inverse normal CDF approximation
# (Abramowitz & Stegun rational approximation - vectorized inline)
sorted_sample = np.sort(sample)
n = len(sample)
p = (np.arange(1, n + 1) - 0.5) / n

# Coefficients for rational approximation
a = np.array(
    [
        -3.969683028665376e1,
        2.209460984245205e2,
        -2.759285104469687e2,
        1.383577518672690e2,
        -3.066479806614716e1,
        2.506628277459239e0,
    ]
)
b = np.array(
    [-5.447609879822406e1, 1.615858368580409e2, -1.556989798598866e2, 6.680131188771972e1, -1.328068155288572e1]
)
c = np.array(
    [
        -7.784894002430293e-3,
        -3.223964580411365e-1,
        -2.400758277161838e0,
        -2.549732539343734e0,
        4.374664141464968e0,
        2.938163982698783e0,
    ]
)
d = np.array([7.784695709041462e-3, 3.224671290700398e-1, 2.445134137142996e0, 3.754408661907416e0])

# Compute inverse normal CDF (ppf) for each probability
theoretical_quantiles = np.zeros(n)
p_low, p_high = 0.02425, 0.97575

# Lower tail
mask_low = p < p_low
q_low = np.sqrt(-2 * np.log(p[mask_low]))
theoretical_quantiles[mask_low] = (
    ((((c[0] * q_low + c[1]) * q_low + c[2]) * q_low + c[3]) * q_low + c[4]) * q_low + c[5]
) / ((((d[0] * q_low + d[1]) * q_low + d[2]) * q_low + d[3]) * q_low + 1)

# Central region
mask_mid = (p >= p_low) & (p <= p_high)
q_mid = p[mask_mid] - 0.5
r_mid = q_mid * q_mid
theoretical_quantiles[mask_mid] = (
    (((((a[0] * r_mid + a[1]) * r_mid + a[2]) * r_mid + a[3]) * r_mid + a[4]) * r_mid + a[5])
    * q_mid
    / (((((b[0] * r_mid + b[1]) * r_mid + b[2]) * r_mid + b[3]) * r_mid + b[4]) * r_mid + 1)
)

# Upper tail
mask_high = p > p_high
q_high = np.sqrt(-2 * np.log(1 - p[mask_high]))
theoretical_quantiles[mask_high] = -(
    ((((c[0] * q_high + c[1]) * q_high + c[2]) * q_high + c[3]) * q_high + c[4]) * q_high + c[5]
) / ((((d[0] * q_high + d[1]) * q_high + d[2]) * q_high + d[3]) * q_high + 1)

# Standardize sample for comparison with standard normal
sample_mean = np.mean(sample)
sample_std = np.std(sample, ddof=1)
sample_quantiles = (sorted_sample - sample_mean) / sample_std

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Q-Q scatter plot using seaborn
sns.scatterplot(
    x=theoretical_quantiles,
    y=sample_quantiles,
    ax=ax,
    s=200,
    color="#306998",
    alpha=0.7,
    edgecolor="white",
    linewidth=0.5,
)

# Reference line (y = x for perfect normal distribution)
line_min = min(theoretical_quantiles.min(), sample_quantiles.min())
line_max = max(theoretical_quantiles.max(), sample_quantiles.max())
ax.plot(
    [line_min, line_max],
    [line_min, line_max],
    color="#FFD43B",
    linewidth=3,
    linestyle="--",
    label="Reference (y=x)",
    zorder=1,
)

# Labels and styling
ax.set_xlabel("Theoretical Quantiles", fontsize=20)
ax.set_ylabel("Sample Quantiles", fontsize=20)
ax.set_title("qq-basic · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")
ax.legend(fontsize=16, loc="upper left")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
