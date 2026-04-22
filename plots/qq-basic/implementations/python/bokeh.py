""" pyplots.ai
qq-basic: Basic Q-Q Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Slope
from bokeh.plotting import figure


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

# Create ColumnDataSource
source = ColumnDataSource(data={"theoretical": theoretical_quantiles, "sample": sample_quantiles})

# Create figure (4800 × 2700 px)
p = figure(
    width=4800,
    height=2700,
    title="qq-basic · bokeh · pyplots.ai",
    x_axis_label="Theoretical Quantiles",
    y_axis_label="Sample Quantiles",
    toolbar_location=None,
)

# Add reference line (y=x) showing perfect normal distribution match
slope = Slope(gradient=1, y_intercept=0, line_color="#FFD43B", line_width=4, line_dash="dashed")
p.add_layout(slope)

# Plot Q-Q points
p.scatter(x="theoretical", y="sample", source=source, size=20, color="#306998", alpha=0.7)

# Styling for 4800×2700 px
p.title.text_font_size = "36pt"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Grid styling
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = "dashed"

# Background
p.background_fill_color = "#fafafa"

# Save as PNG and HTML
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
