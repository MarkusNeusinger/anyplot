""" pyplots.ai
acf-pacf: Autocorrelation and Partial Autocorrelation (ACF/PACF) Plot
Library: altair 6.0.0 | Python 3.14.3
Quality: 83/100 | Created: 2026-03-14
"""

import altair as alt
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import acf, pacf


# Data - simulate monthly airline-style passenger data with trend and seasonality
np.random.seed(42)
n = 200
t = np.arange(n)
trend = 0.05 * t
seasonal = 10 * np.sin(2 * np.pi * t / 12)
noise = np.random.normal(0, 2, n)
passengers = 100 + trend + seasonal + noise

# Compute ACF and PACF
n_lags = 35
acf_values = acf(passengers, nlags=n_lags, fft=True)
pacf_values = pacf(passengers, nlags=n_lags, method="ywm")

# Confidence interval bounds
ci_bound = 1.96 / np.sqrt(n)

# Build dataframes
acf_df = pd.DataFrame({"lag": np.arange(len(acf_values)), "value": acf_values})
pacf_df = pd.DataFrame({"lag": np.arange(1, len(pacf_values)), "value": pacf_values[1:]})
ci_line_df = pd.DataFrame({"y": [ci_bound, -ci_bound]})

# ACF panel
acf_stems = (
    alt.Chart(acf_df)
    .mark_rule(strokeWidth=3)
    .encode(
        x=alt.X("lag:Q", title="Lag", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        y=alt.Y("value:Q", title="ACF", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        y2=alt.value(0),
        color=alt.value("#306998"),
        tooltip=[alt.Tooltip("lag:Q", title="Lag"), alt.Tooltip("value:Q", title="Correlation", format=".3f")],
    )
)
acf_dots = alt.Chart(acf_df).mark_circle(size=80).encode(x="lag:Q", y="value:Q", color=alt.value("#306998"))
acf_ci_band = (
    alt.Chart(pd.DataFrame({"upper": [ci_bound], "lower": [-ci_bound], "x0": [0], "x1": [n_lags]}))
    .mark_rect(opacity=0.1)
    .encode(x="x0:Q", x2="x1:Q", y="upper:Q", y2="lower:Q", color=alt.value("#E74C3C"))
)
acf_ci_lines = (
    alt.Chart(ci_line_df)
    .mark_rule(strokeDash=[6, 4], strokeWidth=1.5, opacity=0.6)
    .encode(y="y:Q", color=alt.value("#E74C3C"))
)
acf_zero = (
    alt.Chart(pd.DataFrame({"y": [0]}))
    .mark_rule(strokeWidth=1, opacity=0.3)
    .encode(y="y:Q", color=alt.value("#333333"))
)
acf_chart = (acf_ci_band + acf_ci_lines + acf_zero + acf_stems + acf_dots).properties(width=1600, height=400)

# PACF panel
pacf_stems = (
    alt.Chart(pacf_df)
    .mark_rule(strokeWidth=3)
    .encode(
        x=alt.X("lag:Q", title="Lag", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        y=alt.Y("value:Q", title="PACF", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        y2=alt.value(0),
        color=alt.value("#306998"),
        tooltip=[alt.Tooltip("lag:Q", title="Lag"), alt.Tooltip("value:Q", title="Correlation", format=".3f")],
    )
)
pacf_dots = alt.Chart(pacf_df).mark_circle(size=80).encode(x="lag:Q", y="value:Q", color=alt.value("#306998"))
pacf_ci_band = (
    alt.Chart(pd.DataFrame({"upper": [ci_bound], "lower": [-ci_bound], "x0": [1], "x1": [n_lags]}))
    .mark_rect(opacity=0.1)
    .encode(x="x0:Q", x2="x1:Q", y="upper:Q", y2="lower:Q", color=alt.value("#E74C3C"))
)
pacf_ci_lines = (
    alt.Chart(ci_line_df)
    .mark_rule(strokeDash=[6, 4], strokeWidth=1.5, opacity=0.6)
    .encode(y="y:Q", color=alt.value("#E74C3C"))
)
pacf_zero = (
    alt.Chart(pd.DataFrame({"y": [0]}))
    .mark_rule(strokeWidth=1, opacity=0.3)
    .encode(y="y:Q", color=alt.value("#333333"))
)
pacf_chart = (pacf_ci_band + pacf_ci_lines + pacf_zero + pacf_stems + pacf_dots).properties(width=1600, height=400)

# Combine vertically
chart = (
    alt.vconcat(acf_chart, pacf_chart, spacing=40)
    .properties(title=alt.Title(text="acf-pacf · altair · pyplots.ai", fontSize=28))
    .configure_view(strokeWidth=0)
    .configure_axis(grid=False)
    .configure_axisY(grid=True, gridOpacity=0.15, gridDash=[4, 4])
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
