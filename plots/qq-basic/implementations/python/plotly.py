""" pyplots.ai
qq-basic: Basic Q-Q Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
import plotly.graph_objects as go


# Data - sample with slight positive skew to demonstrate Q-Q plot interpretation
np.random.seed(42)
sample = np.concatenate(
    [
        np.random.normal(50, 10, 80),  # Main normal distribution
        np.random.normal(75, 5, 20),  # Slight right tail for interest
    ]
)
sample = np.sort(sample)

# Calculate theoretical quantiles using Blom's plotting positions
n = len(sample)
probabilities = (np.arange(1, n + 1) - 0.375) / (n + 0.25)

# Approximate inverse normal CDF (Abramowitz & Stegun rational approximation)
a = np.array(
    [
        -3.969683028665376e01,
        2.209460984245205e02,
        -2.759285104469687e02,
        1.383577518672690e02,
        -3.066479806614716e01,
        2.506628277459239e00,
    ]
)
b = np.array(
    [-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02, 6.680131188771972e01, -1.328068155288572e01]
)
c = np.array(
    [
        -7.784894002430293e-03,
        -3.223964580411365e-01,
        -2.400758277161838e00,
        -2.549732539343734e00,
        4.374664141464968e00,
        2.938163982698783e00,
    ]
)
d = np.array([7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00, 3.754408661907416e00])

theoretical_quantiles = np.zeros(n)
for i, p in enumerate(probabilities):
    if p < 0.02425:
        q = np.sqrt(-2 * np.log(p))
        theoretical_quantiles[i] = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
            (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1
        )
    elif p <= 0.97575:
        q = p - 0.5
        r = q * q
        theoretical_quantiles[i] = (
            (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5])
            * q
            / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
        )
    else:
        q = np.sqrt(-2 * np.log(1 - p))
        theoretical_quantiles[i] = -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
            (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1
        )

# Standardize sample for comparison with standard normal
sample_standardized = (sample - np.mean(sample)) / np.std(sample)

# Reference line (y=x for standardized data)
line_min = min(theoretical_quantiles.min(), sample_standardized.min()) - 0.2
line_max = max(theoretical_quantiles.max(), sample_standardized.max()) + 0.2

# Plot
fig = go.Figure()

# Q-Q points
fig.add_trace(
    go.Scatter(
        x=theoretical_quantiles,
        y=sample_standardized,
        mode="markers",
        marker={"size": 14, "color": "#306998", "opacity": 0.7},
        name="Sample Quantiles",
    )
)

# Reference line (y=x)
fig.add_trace(
    go.Scatter(
        x=[line_min, line_max],
        y=[line_min, line_max],
        mode="lines",
        line={"color": "#FFD43B", "width": 3, "dash": "dash"},
        name="Reference (y=x)",
    )
)

# Layout
fig.update_layout(
    title={"text": "qq-basic · plotly · pyplots.ai", "font": {"size": 28}},
    xaxis={
        "title": {"text": "Theoretical Quantiles", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "Sample Quantiles", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
        "zeroline": False,
    },
    template="plotly_white",
    legend={"font": {"size": 18}, "x": 0.02, "y": 0.98, "bgcolor": "rgba(255,255,255,0.8)"},
    margin={"l": 80, "r": 40, "t": 80, "b": 80},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
