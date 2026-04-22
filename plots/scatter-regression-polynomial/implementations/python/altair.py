""" pyplots.ai
scatter-regression-polynomial: Scatter Plot with Polynomial Regression
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Quadratic relationship with noise (simulating plant growth vs fertilizer)
np.random.seed(42)
n_points = 80
x = np.linspace(0, 10, n_points)
# Quadratic relationship: growth increases then plateaus (diminishing returns)
y_true = -0.8 * x**2 + 8 * x + 5
y = y_true + np.random.randn(n_points) * 3

# Fit polynomial regression (degree 2)
coeffs = np.polyfit(x, y, 2)
y_pred = np.polyval(coeffs, x)

# Calculate R² value
ss_res = np.sum((y - y_pred) ** 2)
ss_tot = np.sum((y - np.mean(y)) ** 2)
r_squared = 1 - (ss_res / ss_tot)

# Create equation string
a, b, c = coeffs
equation = f"y = {a:.2f}x² + {b:.2f}x + {c:.2f}"

# Prepare DataFrames
df_points = pd.DataFrame({"Fertilizer (kg/ha)": x, "Crop Yield (tons/ha)": y})

# Generate smooth curve for regression line
x_smooth = np.linspace(x.min(), x.max(), 200)
y_smooth = np.polyval(coeffs, x_smooth)
df_curve = pd.DataFrame({"Fertilizer (kg/ha)": x_smooth, "Crop Yield (tons/ha)": y_smooth})

# Create scatter plot
scatter = (
    alt.Chart(df_points)
    .mark_circle(size=180, opacity=0.65, color="#306998")
    .encode(
        x=alt.X("Fertilizer (kg/ha):Q", title="Fertilizer (kg/ha)"),
        y=alt.Y("Crop Yield (tons/ha):Q", title="Crop Yield (tons/ha)"),
        tooltip=["Fertilizer (kg/ha)", "Crop Yield (tons/ha)"],
    )
)

# Create polynomial regression curve
curve = (
    alt.Chart(df_curve).mark_line(size=4, color="#FFD43B").encode(x="Fertilizer (kg/ha):Q", y="Crop Yield (tons/ha):Q")
)

# Create annotation for R² and equation (two separate text marks for multi-line)
r2_text_df = pd.DataFrame({"x": [0.5], "y": [28.5], "text": [f"R² = {r_squared:.3f}"]})
eq_text_df = pd.DataFrame({"x": [0.5], "y": [26.5], "text": [equation]})

r2_annotation = (
    alt.Chart(r2_text_df)
    .mark_text(align="left", baseline="top", fontSize=22, fontWeight="bold", color="#333333")
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"), text="text:N")
)

eq_annotation = (
    alt.Chart(eq_text_df)
    .mark_text(align="left", baseline="top", fontSize=20, fontWeight="normal", color="#333333")
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"), text="text:N")
)

# Combine layers
chart = (
    (scatter + curve + r2_annotation + eq_annotation)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("scatter-regression-polynomial · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, tickSize=10)
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
