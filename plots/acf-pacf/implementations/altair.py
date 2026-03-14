""" pyplots.ai
acf-pacf: Autocorrelation and Partial Autocorrelation (ACF/PACF) Plot
Library: altair 6.0.0 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-14
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

# Build dataframes with color categories for visual storytelling
acf_df = pd.DataFrame({"lag": np.arange(len(acf_values)), "value": acf_values})
acf_df["significant"] = acf_df["value"].abs() > ci_bound
acf_df["category"] = "Non-significant"
acf_df.loc[acf_df["significant"], "category"] = "Significant"
acf_df.loc[(acf_df["lag"] % 12 == 0) & (acf_df["lag"] > 0), "category"] = "Seasonal (12-month)"

pacf_df = pd.DataFrame({"lag": np.arange(1, len(pacf_values)), "value": pacf_values[1:]})
pacf_df["significant"] = pacf_df["value"].abs() > ci_bound
pacf_df["category"] = "Non-significant"
pacf_df.loc[pacf_df["significant"], "category"] = "Significant"

ci_rect_acf = pd.DataFrame({"upper": [ci_bound], "lower": [-ci_bound], "x0": [0], "x1": [n_lags]})
ci_rect_pacf = pd.DataFrame({"upper": [ci_bound], "lower": [-ci_bound], "x0": [1], "x1": [n_lags]})
ci_line_df = pd.DataFrame({"y": [ci_bound, -ci_bound]})
zero_df = pd.DataFrame({"y": [0]})

# Color scale: seasonal=gold, significant=blue, non-significant=muted
cat_color = alt.Color(
    "category:N",
    scale=alt.Scale(
        domain=["Seasonal (12-month)", "Significant", "Non-significant"], range=["#D4A017", "#306998", "#A0B4C8"]
    ),
    legend=None,
)

# Shared encoding components
x_lag = alt.X("lag:Q", title="Lag (months)", axis=alt.Axis(labelFontSize=18, titleFontSize=22))
ci_lines = (
    alt.Chart(ci_line_df)
    .mark_rule(strokeDash=[6, 4], strokeWidth=1.5, opacity=0.6)
    .encode(y="y:Q", color=alt.value("#E74C3C"))
)
zero_line = alt.Chart(zero_df).mark_rule(strokeWidth=1, opacity=0.3).encode(y="y:Q", color=alt.value("#333333"))
ci_band_base = alt.Chart().mark_rect(opacity=0.1)
ci_band_acf = ci_band_base.properties(data=ci_rect_acf).encode(
    x="x0:Q", x2="x1:Q", y="upper:Q", y2="lower:Q", color=alt.value("#E74C3C")
)
ci_band_pacf = ci_band_base.properties(data=ci_rect_pacf).encode(
    x="x0:Q", x2="x1:Q", y="upper:Q", y2="lower:Q", color=alt.value("#E74C3C")
)
bg_layers_acf = ci_band_acf + ci_lines + zero_line
bg_layers_pacf = ci_band_pacf + ci_lines + zero_line

# ACF panel - seasonal spikes highlighted in gold
acf_stems = (
    alt.Chart(acf_df)
    .mark_rule(strokeWidth=3)
    .encode(
        x=x_lag,
        y=alt.Y("value:Q", title="ACF", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        y2=alt.value(0),
        color=cat_color,
        tooltip=[
            alt.Tooltip("lag:Q", title="Lag"),
            alt.Tooltip("value:Q", title="Correlation", format=".3f"),
            alt.Tooltip("category:N", title="Status"),
        ],
    )
)
acf_dots = alt.Chart(acf_df).mark_circle(size=120).encode(x="lag:Q", y="value:Q", color=cat_color)
acf_chart = (bg_layers_acf + acf_stems + acf_dots).properties(width=1600, height=400)

# PACF panel
pacf_stems = (
    alt.Chart(pacf_df)
    .mark_rule(strokeWidth=3)
    .encode(
        x=x_lag,
        y=alt.Y("value:Q", title="PACF", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        y2=alt.value(0),
        color=cat_color,
        tooltip=[
            alt.Tooltip("lag:Q", title="Lag"),
            alt.Tooltip("value:Q", title="Correlation", format=".3f"),
            alt.Tooltip("category:N", title="Status"),
        ],
    )
)
pacf_dots = alt.Chart(pacf_df).mark_circle(size=120).encode(x="lag:Q", y="value:Q", color=cat_color)
pacf_chart = (bg_layers_pacf + pacf_stems + pacf_dots).properties(width=1600, height=400)

# Combine vertically
chart = (
    alt.vconcat(acf_chart, pacf_chart, spacing=40)
    .properties(
        title=alt.Title(
            text="acf-pacf · altair · pyplots.ai",
            subtitle="Seasonal period ≈ 12 months · Gold stems mark seasonal lags",
            fontSize=28,
            subtitleFontSize=18,
            subtitleColor="#666666",
        )
    )
    .configure_view(strokeWidth=0)
    .configure_axis(grid=False)
    .configure_axisY(grid=True, gridOpacity=0.15, gridDash=[4, 4])
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
