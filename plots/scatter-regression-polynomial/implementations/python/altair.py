""" anyplot.ai
scatter-regression-polynomial: Scatter Plot with Polynomial Regression
Library: altair 6.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-07
"""

import os

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
BRAND = "#009E73"  # First series (scatter points)
SECONDARY = "#C475FD"  # Second series (regression curve)

# Data - Quadratic relationship with noise (fertilizer vs crop yield)
np.random.seed(42)
n_points = 80
x = np.linspace(0.5, 10, n_points)
# Quadratic relationship: yield increases then plateaus (diminishing returns)
y_true = -0.6 * x**2 + 7.5 * x + 8
y = y_true + np.random.randn(n_points) * 2.5
# Clip to realistic range (crop yield must be positive)
y = np.clip(y, 1, 30)

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
    .mark_circle(size=180, opacity=0.65, color=BRAND)
    .encode(
        x=alt.X("Fertilizer (kg/ha):Q", title="Fertilizer (kg/ha)"),
        y=alt.Y("Crop Yield (tons/ha):Q", title="Crop Yield (tons/ha)"),
        tooltip=["Fertilizer (kg/ha)", "Crop Yield (tons/ha)"],
    )
)

# Create polynomial regression curve
curve = (
    alt.Chart(df_curve).mark_line(size=4, color=SECONDARY).encode(x="Fertilizer (kg/ha):Q", y="Crop Yield (tons/ha):Q")
)

# Create annotation for R² and equation
r2_text_df = pd.DataFrame({"x": [0.5], "y": [28.5], "text": [f"R² = {r_squared:.3f}"]})
eq_text_df = pd.DataFrame({"x": [0.5], "y": [26.5], "text": [equation]})

r2_annotation = (
    alt.Chart(r2_text_df)
    .mark_text(align="left", baseline="top", fontSize=22, fontWeight="bold", color=INK)
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"), text="text:N")
)

eq_annotation = (
    alt.Chart(eq_text_df)
    .mark_text(align="left", baseline="top", fontSize=20, fontWeight="normal", color=INK_SOFT)
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"), text="text:N")
)

# Combine layers
chart = (
    (scatter + curve + r2_annotation + eq_annotation)
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("scatter-regression-polynomial · altair · anyplot.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        tickSize=10,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_title(color=INK)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
