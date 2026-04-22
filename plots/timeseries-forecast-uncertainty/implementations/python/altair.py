""" pyplots.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-07
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Monthly sales with 36 months history + 12 months forecast
np.random.seed(42)

# Historical period (36 months)
historical_dates = pd.date_range("2021-01-01", periods=36, freq="MS")
trend = np.linspace(100, 180, 36)
seasonal = 15 * np.sin(np.linspace(0, 6 * np.pi, 36))
noise = np.random.normal(0, 8, 36)
historical_values = trend + seasonal + noise

# Forecast period (12 months)
forecast_dates = pd.date_range("2024-01-01", periods=12, freq="MS")
forecast_trend = np.linspace(180, 210, 12)
forecast_seasonal = 15 * np.sin(np.linspace(6 * np.pi, 8 * np.pi, 12))
forecast_values = forecast_trend + forecast_seasonal

# Confidence intervals - widening over forecast horizon
forecast_std = np.linspace(5, 20, 12)
lower_80 = forecast_values - 1.28 * forecast_std
upper_80 = forecast_values + 1.28 * forecast_std
lower_95 = forecast_values - 1.96 * forecast_std
upper_95 = forecast_values + 1.96 * forecast_std

# Create DataFrames
historical_df = pd.DataFrame({"date": historical_dates, "actual": historical_values, "series": "Historical"})

forecast_df = pd.DataFrame(
    {
        "date": forecast_dates,
        "forecast": forecast_values,
        "lower_80": lower_80,
        "upper_80": upper_80,
        "lower_95": lower_95,
        "upper_95": upper_95,
        "series": "Forecast",
    }
)

# Shared Y-axis scale to focus on data range (avoiding wasted space at 0)
y_scale = alt.Scale(domain=[50, 270])

# Historical line chart with legend
historical_line = (
    alt.Chart(historical_df)
    .mark_line(strokeWidth=3)
    .encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("actual:Q", title="Sales (thousands USD)", scale=y_scale),
        color=alt.Color(
            "series:N",
            scale=alt.Scale(domain=["Historical"], range=["#306998"]),
            legend=alt.Legend(title="Series", orient="right", titleFontSize=16, labelFontSize=14),
        ),
    )
)

# 95% confidence band (lighter) with legend entry
band_95_df = forecast_df.copy()
band_95_df["band"] = "95% CI"
band_95 = (
    alt.Chart(band_95_df)
    .mark_area(opacity=0.2)
    .encode(
        x=alt.X("date:T"),
        y=alt.Y("lower_95:Q", scale=y_scale),
        y2=alt.Y2("upper_95:Q"),
        color=alt.Color(
            "band:N",
            scale=alt.Scale(domain=["95% CI"], range=["#FFD43B"]),
            legend=alt.Legend(title="Confidence", orient="right", titleFontSize=16, labelFontSize=14),
        ),
    )
)

# 80% confidence band (darker) with legend entry
band_80_df = forecast_df.copy()
band_80_df["band"] = "80% CI"
band_80 = (
    alt.Chart(band_80_df)
    .mark_area(opacity=0.35)
    .encode(
        x=alt.X("date:T"),
        y=alt.Y("lower_80:Q", scale=y_scale),
        y2=alt.Y2("upper_80:Q"),
        color=alt.Color(
            "band:N",
            scale=alt.Scale(domain=["80% CI"], range=["#FFD43B"]),
            legend=alt.Legend(title="Confidence", orient="right", titleFontSize=16, labelFontSize=14),
        ),
    )
)

# Forecast line (dashed) with legend entry
forecast_line = (
    alt.Chart(forecast_df)
    .mark_line(strokeWidth=3, strokeDash=[8, 4])
    .encode(
        x=alt.X("date:T"),
        y=alt.Y("forecast:Q", scale=y_scale),
        color=alt.Color(
            "series:N",
            scale=alt.Scale(domain=["Forecast"], range=["#E67E22"]),
            legend=alt.Legend(title="Series", orient="right", titleFontSize=16, labelFontSize=14),
        ),
    )
)

# Vertical line at forecast start
forecast_start = pd.DataFrame({"date": [pd.Timestamp("2024-01-01")]})
vertical_rule = (
    alt.Chart(forecast_start).mark_rule(strokeWidth=2, strokeDash=[6, 3], color="#555555").encode(x="date:T")
)

# Combine all layers
chart = (
    alt.layer(band_95, band_80, historical_line, forecast_line, vertical_rule)
    .resolve_scale(color="independent")
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "timeseries-forecast-uncertainty · altair · pyplots.ai",
            fontSize=28,
            anchor="middle",
            subtitle="Monthly Sales with 80% and 95% Confidence Intervals",
            subtitleFontSize=20,
        ),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
