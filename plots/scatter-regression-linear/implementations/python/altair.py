""" pyplots.ai
scatter-regression-linear: Scatter Plot with Linear Regression
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-24
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Advertising spend vs sales revenue
np.random.seed(42)
n = 80
x = np.random.uniform(10, 100, n)  # Advertising spend (thousands $)
noise = np.random.normal(0, 8, n)
y = 0.8 * x + 15 + noise  # Sales revenue (thousands $)

# Calculate regression statistics manually
x_mean = np.mean(x)
y_mean = np.mean(y)
ss_xx = np.sum((x - x_mean) ** 2)
ss_xy = np.sum((x - x_mean) * (y - y_mean))
slope = ss_xy / ss_xx
intercept = y_mean - slope * x_mean

# Calculate R-squared
y_pred = slope * x + intercept
ss_res = np.sum((y - y_pred) ** 2)
ss_tot = np.sum((y - y_mean) ** 2)
r_squared = 1 - (ss_res / ss_tot)

# Create regression line and confidence interval
x_line = np.linspace(x.min(), x.max(), 100)
y_line = slope * x_line + intercept

# Standard error and 95% CI (approximation using t-value of 1.99 for df=78)
mse = ss_res / (n - 2)
se_line = np.sqrt(mse * (1 / n + (x_line - x_mean) ** 2 / ss_xx))
t_val = 1.99  # t-critical for 95% CI with ~78 df
y_upper = y_line + t_val * se_line
y_lower = y_line - t_val * se_line

# Create dataframes
df_scatter = pd.DataFrame({"Advertising Spend ($K)": x, "Sales Revenue ($K)": y})
df_line = pd.DataFrame(
    {"Advertising Spend ($K)": x_line, "Sales Revenue ($K)": y_line, "y_upper": y_upper, "y_lower": y_lower}
)

# Create scatter points
scatter = (
    alt.Chart(df_scatter)
    .mark_point(size=150, opacity=0.65, color="#306998", filled=True)
    .encode(
        x=alt.X("Advertising Spend ($K):Q", scale=alt.Scale(zero=False)),
        y=alt.Y("Sales Revenue ($K):Q", scale=alt.Scale(zero=False)),
        tooltip=["Advertising Spend ($K)", "Sales Revenue ($K)"],
    )
)

# Create confidence band
band = (
    alt.Chart(df_line)
    .mark_area(opacity=0.25, color="#FFD43B")
    .encode(x="Advertising Spend ($K):Q", y=alt.Y("y_lower:Q", title="Sales Revenue ($K)"), y2="y_upper:Q")
)

# Create regression line
line = (
    alt.Chart(df_line)
    .mark_line(color="#FFD43B", strokeWidth=4)
    .encode(x="Advertising Spend ($K):Q", y="Sales Revenue ($K):Q")
)

# Annotation text for R² and equation
annotation_text = f"y = {slope:.2f}x + {intercept:.2f}  |  R² = {r_squared:.3f}"
annotation = (
    alt.Chart(pd.DataFrame({"text": [annotation_text]}))
    .mark_text(align="left", baseline="top", fontSize=20, fontWeight="bold", color="#333333", dx=10, dy=10)
    .encode(x=alt.value(80), y=alt.value(30), text="text:N")
)

# Combine layers
chart = (
    alt.layer(band, line, scatter, annotation)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("scatter-regression-linear · altair · pyplots.ai", fontSize=28, anchor="start"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
