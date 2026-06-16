""" anyplot.ai
scatter-regression-linear: Scatter Plot with Linear Regression
Library: altair 6.1.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-06
"""

import os

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1
ACCENT = "#C475FD"  # Okabe-Ito position 2 (for regression line)

# Data - Temperature vs Energy Consumption
np.random.seed(42)
n = 100
temperature = np.random.uniform(45, 95, n)  # Fahrenheit
noise = np.random.normal(0, 12, n)
energy_consumption = 0.65 * temperature + 800 + noise  # kWh

# Calculate regression statistics
x_mean = np.mean(temperature)
y_mean = np.mean(energy_consumption)
ss_xx = np.sum((temperature - x_mean) ** 2)
ss_xy = np.sum((temperature - x_mean) * (energy_consumption - y_mean))
slope = ss_xy / ss_xx
intercept = y_mean - slope * x_mean

# Calculate R-squared
y_pred = slope * temperature + intercept
ss_res = np.sum((energy_consumption - y_pred) ** 2)
ss_tot = np.sum((energy_consumption - y_mean) ** 2)
r_squared = 1 - (ss_res / ss_tot)

# Create regression line and confidence interval
x_line = np.linspace(temperature.min(), temperature.max(), 150)
y_line = slope * x_line + intercept

# 95% confidence interval calculation
mse = ss_res / (n - 2)
se_line = np.sqrt(mse * (1 / n + (x_line - x_mean) ** 2 / ss_xx))
t_val = 1.984  # t-critical for 95% CI with df=98
y_upper = y_line + t_val * se_line
y_lower = y_line - t_val * se_line

# Create dataframes
df_scatter = pd.DataFrame({"Temperature (°F)": temperature, "Energy (kWh)": energy_consumption})
df_line = pd.DataFrame({"Temperature (°F)": x_line, "Energy (kWh)": y_line, "y_upper": y_upper, "y_lower": y_lower})

# Create scatter points
scatter = (
    alt.Chart(df_scatter)
    .mark_point(size=180, opacity=0.7, filled=True)
    .encode(
        x=alt.X("Temperature (°F):Q", scale=alt.Scale(zero=False)),
        y=alt.Y("Energy (kWh):Q", scale=alt.Scale(zero=False)),
        color=alt.value(BRAND),
    )
)

# Create confidence band
band = (
    alt.Chart(df_line)
    .mark_area(opacity=0.15, fillOpacity=0.15)
    .encode(x="Temperature (°F):Q", y=alt.Y("y_lower:Q", title="Energy (kWh)"), y2="y_upper:Q", color=alt.value(ACCENT))
)

# Create regression line
line = (
    alt.Chart(df_line)
    .mark_line(strokeWidth=3)
    .encode(x="Temperature (°F):Q", y="Energy (kWh):Q", color=alt.value(ACCENT))
)

# Annotation for R² and equation
equation_text = f"y = {slope:.2f}x + {intercept:.1f}"
r2_text = f"R² = {r_squared:.3f}"
annotation_df = pd.DataFrame({"equation": [equation_text], "r2": [r2_text]})

annotation_eq = (
    alt.Chart(annotation_df)
    .mark_text(align="left", baseline="top", fontSize=18, fontWeight="bold", dx=20, dy=20)
    .encode(x=alt.value(0), y=alt.value(0), text="equation:N", color=alt.value(INK))
)

annotation_r2 = (
    alt.Chart(annotation_df)
    .mark_text(align="left", baseline="top", fontSize=18, fontWeight="bold", dx=20, dy=50)
    .encode(x=alt.value(0), y=alt.value(0), text="r2:N", color=alt.value(INK))
)

# Combine layers
chart = (
    alt.layer(band, line, scatter, annotation_eq, annotation_r2)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("scatter-regression-linear · altair · anyplot.ai", fontSize=28, anchor="start"),
        background=PAGE_BG,
    )
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        labelColor=INK_SOFT,
        titleColor=INK,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridOpacity=0.10,
        gridColor=INK,
    )
    .configure_title(color=INK, fontSize=28, anchor="start", fontWeight="normal")
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
