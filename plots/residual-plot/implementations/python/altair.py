""" pyplots.ai
residual-plot: Residual Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import altair as alt
import numpy as np
import pandas as pd


# Data: Simulate a linear regression scenario with some non-linearity
np.random.seed(42)
n = 150

# Generate realistic housing price prediction scenario
x = np.linspace(1000, 3000, n)  # House size in sq ft
noise = np.random.randn(n) * 15000
y_true = 50000 + 150 * x + 0.02 * (x - 2000) ** 2 + noise  # True prices with slight curvature
y_pred = 50000 + 155 * x  # Linear model predictions

residuals = y_true - y_pred
std_residual = np.std(residuals)

# Identify outliers (beyond ±2 standard deviations)
is_outlier = np.abs(residuals) > 2 * std_residual

# Create DataFrame
df = pd.DataFrame(
    {
        "Fitted Values ($)": y_pred,
        "Residuals ($)": residuals,
        "Outlier": np.where(is_outlier, "Outlier (>2σ)", "Normal"),
    }
)

# Base scatter plot with color encoding for outliers
scatter = (
    alt.Chart(df)
    .mark_point(size=120, opacity=0.7)
    .encode(
        x=alt.X("Fitted Values ($):Q", title="Fitted Values ($)", scale=alt.Scale(nice=True)),
        y=alt.Y("Residuals ($):Q", title="Residuals ($)", scale=alt.Scale(nice=True)),
        color=alt.Color(
            "Outlier:N",
            scale=alt.Scale(domain=["Normal", "Outlier (>2σ)"], range=["#306998", "#FFD43B"]),
            legend=alt.Legend(title="Point Type", titleFontSize=18, labelFontSize=16),
        ),
        tooltip=["Fitted Values ($):Q", "Residuals ($):Q", "Outlier:N"],
    )
)

# Zero reference line
zero_line = (
    alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color="#333333", strokeWidth=2, strokeDash=[8, 4]).encode(y="y:Q")
)

# ±2 standard deviation bands
bands_df = pd.DataFrame({"y": [2 * std_residual, -2 * std_residual], "label": ["+2σ", "-2σ"]})

band_lines = alt.Chart(bands_df).mark_rule(color="#888888", strokeWidth=1.5, strokeDash=[4, 4]).encode(y="y:Q")

# Add LOWESS-like trend using polynomial regression
loess_df = df.copy()
loess_df = loess_df.sort_values("Fitted Values ($)")

loess_line = (
    alt.Chart(loess_df)
    .transform_loess("Fitted Values ($)", "Residuals ($)", bandwidth=0.3)
    .mark_line(color="#E24A33", strokeWidth=3)
    .encode(x="Fitted Values ($):Q", y="Residuals ($):Q")
)

# Combine all layers
chart = (
    alt.layer(zero_line, band_lines, scatter, loess_line)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(text="residual-plot · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
    .configure_legend(orient="right", padding=10)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
