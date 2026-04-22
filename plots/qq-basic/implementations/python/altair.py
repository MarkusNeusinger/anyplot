""" pyplots.ai
qq-basic: Basic Q-Q Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - sample with slight right skew to demonstrate Q-Q interpretation
np.random.seed(42)
sample = np.concatenate(
    [
        np.random.normal(50, 10, 80),  # Main distribution
        np.random.normal(75, 5, 20),  # Right tail (creates slight skew)
    ]
)

# Calculate Q-Q theoretical quantiles using Abramowitz & Stegun rational approximation
n = len(sample)
sorted_sample = np.sort(sample)
p = (np.arange(1, n + 1) - 0.5) / n

# Inverse normal CDF approximation (vectorized inline)
# Constants for rational approximation
a = [
    -3.969683028665376e1,
    2.209460984245205e2,
    -2.759285104469687e2,
    1.383577518672690e2,
    -3.066479806614716e1,
    2.506628277459239e0,
]
b = [-5.447609879822406e1, 1.615858368580409e2, -1.556989798598866e2, 6.680131188771972e1, -1.328068155288572e1]
c = [
    -7.784894002430293e-3,
    -3.223964580411365e-1,
    -2.400758277161838e0,
    -2.549732539343734e0,
    4.374664141464968e0,
    2.938163982698783e0,
]
d = [7.784695709041462e-3, 3.224671290700398e-1, 2.445134137142996e0, 3.754408661907416e0]
p_low = 0.02425

theoretical_quantiles = np.zeros(n)
# Lower tail
mask_low = p < p_low
q_low = np.sqrt(-2 * np.log(p[mask_low]))
theoretical_quantiles[mask_low] = (
    ((((c[0] * q_low + c[1]) * q_low + c[2]) * q_low + c[3]) * q_low + c[4]) * q_low + c[5]
) / ((((d[0] * q_low + d[1]) * q_low + d[2]) * q_low + d[3]) * q_low + 1)
# Central region
mask_mid = (p >= p_low) & (p <= 1 - p_low)
q_mid = p[mask_mid] - 0.5
r_mid = q_mid * q_mid
theoretical_quantiles[mask_mid] = (
    (((((a[0] * r_mid + a[1]) * r_mid + a[2]) * r_mid + a[3]) * r_mid + a[4]) * r_mid + a[5]) * q_mid
) / (((((b[0] * r_mid + b[1]) * r_mid + b[2]) * r_mid + b[3]) * r_mid + b[4]) * r_mid + 1)
# Upper tail
mask_high = p > 1 - p_low
q_high = np.sqrt(-2 * np.log(1 - p[mask_high]))
theoretical_quantiles[mask_high] = -(
    ((((c[0] * q_high + c[1]) * q_high + c[2]) * q_high + c[3]) * q_high + c[4]) * q_high + c[5]
) / ((((d[0] * q_high + d[1]) * q_high + d[2]) * q_high + d[3]) * q_high + 1)

# Scale theoretical quantiles to match sample mean and std
sample_mean = np.mean(sample)
sample_std = np.std(sample, ddof=1)
theoretical_scaled = theoretical_quantiles * sample_std + sample_mean

# Create DataFrame for Altair
df = pd.DataFrame({"Theoretical Quantiles": theoretical_scaled, "Sample Quantiles": sorted_sample})

# Reference line data (y = x)
line_min = min(theoretical_scaled.min(), sorted_sample.min())
line_max = max(theoretical_scaled.max(), sorted_sample.max())
line_df = pd.DataFrame({"x": [line_min, line_max], "y": [line_min, line_max]})

# Create Q-Q scatter plot
points = (
    alt.Chart(df)
    .mark_point(size=200, color="#306998", filled=True, opacity=0.7)
    .encode(
        x=alt.X("Theoretical Quantiles:Q", title="Theoretical Quantiles"),
        y=alt.Y("Sample Quantiles:Q", title="Sample Quantiles"),
        tooltip=["Theoretical Quantiles:Q", "Sample Quantiles:Q"],
    )
)

# Reference line (45-degree)
reference_line = (
    alt.Chart(line_df)
    .mark_line(color="#FFD43B", strokeWidth=3, strokeDash=[8, 4])
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"))
)

# Combine layers
chart = (
    (reference_line + points)
    .properties(width=1600, height=900, title=alt.Title("qq-basic · altair · pyplots.ai", fontSize=28))
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3, gridDash=[4, 4])
    .configure_view(strokeWidth=0)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
