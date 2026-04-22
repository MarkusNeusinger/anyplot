""" pyplots.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-07
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_text,
    geom_line,
    geom_ribbon,
    geom_vline,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_datetime,
    theme,
    theme_minimal,
)


# Data - Monthly electricity demand with forecast
np.random.seed(42)

# Historical period: 36 months
n_historical = 36
dates_historical = pd.date_range("2022-01-01", periods=n_historical, freq="MS")

# Base trend with seasonality
trend = np.linspace(100, 130, n_historical)
seasonality = 15 * np.sin(2 * np.pi * np.arange(n_historical) / 12)
noise = np.random.normal(0, 5, n_historical)
actual_values = trend + seasonality + noise

# Forecast period: 12 months
n_forecast = 12
dates_forecast = pd.date_range(dates_historical[-1] + pd.DateOffset(months=1), periods=n_forecast, freq="MS")

# Forecast with expanding uncertainty
forecast_trend = np.linspace(actual_values[-1], 145, n_forecast)
forecast_seasonality = 15 * np.sin(2 * np.pi * (np.arange(n_forecast) + n_historical) / 12)
forecast_values = forecast_trend + forecast_seasonality

# Confidence intervals widen over time
time_factor = np.sqrt(np.arange(1, n_forecast + 1))
ci_80 = 5 * time_factor
ci_95 = 10 * time_factor

# Build dataframe for historical data
df_historical = pd.DataFrame({"date": dates_historical, "value": actual_values, "series": "Historical"})

# Build dataframe for forecast
df_forecast = pd.DataFrame(
    {
        "date": dates_forecast,
        "value": forecast_values,
        "lower_80": forecast_values - ci_80,
        "upper_80": forecast_values + ci_80,
        "lower_95": forecast_values - ci_95,
        "upper_95": forecast_values + ci_95,
        "series": "Forecast",
    }
)

# Combine for plotting
df_combined = pd.concat([df_historical, df_forecast], ignore_index=True)

# Forecast start date for vertical line
forecast_start = dates_forecast[0]

# Plot
plot = (
    ggplot()
    # 95% confidence band (lighter)
    + geom_ribbon(data=df_forecast, mapping=aes(x="date", ymin="lower_95", ymax="upper_95"), fill="#FFD43B", alpha=0.3)
    # 80% confidence band (darker)
    + geom_ribbon(data=df_forecast, mapping=aes(x="date", ymin="lower_80", ymax="upper_80"), fill="#FFD43B", alpha=0.5)
    # Vertical line at forecast start
    + geom_vline(xintercept=forecast_start, linetype="dashed", color="#888888", size=1)
    # Historical line
    + geom_line(data=df_historical, mapping=aes(x="date", y="value", color="series"), size=1.5)
    # Forecast line
    + geom_line(data=df_forecast, mapping=aes(x="date", y="value", color="series"), size=1.5, linetype="dashed")
    # Color mapping
    + scale_color_manual(values={"Historical": "#306998", "Forecast": "#B85C00"}, name="")
    # Labels
    + labs(x="Date", y="Electricity Demand (GWh)", title="timeseries-forecast-uncertainty · plotnine · pyplots.ai")
    # Date axis formatting
    + scale_x_datetime(date_breaks="6 months", date_labels="%b %Y")
    # Theme
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        axis_text_x=element_text(angle=45, ha="right"),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_position="top",
        panel_grid_major=element_line(color="#CCCCCC", size=0.5, alpha=0.3),
        panel_grid_minor=element_line(color="#EEEEEE", size=0.25, alpha=0.2),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
