""" pyplots.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-07
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Data - Monthly retail sales with forecast
np.random.seed(42)

# Historical period: 36 months (3 years)
n_historical = 36
# Forecast period: 12 months
n_forecast = 12
n_total = n_historical + n_forecast

# Create date range
dates = pd.date_range(start="2022-01-01", periods=n_total, freq="MS")

# Generate historical data with trend, seasonality, and noise
t = np.arange(n_historical)
trend = 100 + t * 1.2  # Upward trend
seasonality = 15 * np.sin(2 * np.pi * t / 12)  # Annual seasonality
noise = np.random.normal(0, 5, n_historical)
actual = trend + seasonality + noise

# Generate forecast starting from last historical value
forecast_start = actual[-1]
t_forecast = np.arange(n_forecast)
forecast_trend = forecast_start + t_forecast * 1.2
forecast_seasonality = 15 * np.sin(2 * np.pi * (t[-1] + 1 + t_forecast) / 12)
forecast_values = forecast_trend + forecast_seasonality

# Create confidence intervals that widen over time
# Uncertainty grows with forecast horizon
uncertainty_growth = np.sqrt(1 + t_forecast * 0.5)
base_std = 8

# 80% confidence interval (1.28 std deviations)
lower_80 = forecast_values - 1.28 * base_std * uncertainty_growth
upper_80 = forecast_values + 1.28 * base_std * uncertainty_growth

# 95% confidence interval (1.96 std deviations)
lower_95 = forecast_values - 1.96 * base_std * uncertainty_growth
upper_95 = forecast_values + 1.96 * base_std * uncertainty_growth

# Combine dates for forecast
historical_dates = dates[:n_historical]
forecast_dates = dates[n_historical:]

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Plot 95% confidence band (lighter, wider)
ax.fill_between(forecast_dates, lower_95, upper_95, color="#FFD43B", alpha=0.3, label="95% Confidence Interval")

# Plot 80% confidence band (darker, narrower)
ax.fill_between(forecast_dates, lower_80, upper_80, color="#FFD43B", alpha=0.5, label="80% Confidence Interval")

# Plot historical data (solid line)
ax.plot(historical_dates, actual, color="#306998", linewidth=3, label="Historical Data", solid_capstyle="round")

# Plot forecast (dashed line)
ax.plot(
    forecast_dates,
    forecast_values,
    color="#E07000",
    linewidth=3,
    linestyle="--",
    label="Forecast",
    solid_capstyle="round",
)

# Add vertical line at forecast start
ax.axvline(x=historical_dates[-1], color="#666666", linewidth=2, linestyle=":", alpha=0.8, label="Forecast Start")

# Labels and styling
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Monthly Sales (thousands)", fontsize=20)
ax.set_title("timeseries-forecast-uncertainty · matplotlib · pyplots.ai", fontsize=24, fontweight="bold")
ax.tick_params(axis="both", labelsize=16)

# Format x-axis dates
fig.autofmt_xdate(rotation=30)

# Grid
ax.grid(True, alpha=0.3, linestyle="--")

# Legend
ax.legend(fontsize=16, loc="upper left", framealpha=0.95)

# Set y-axis limits with some padding
y_min = min(actual.min(), lower_95.min()) - 10
y_max = max(actual.max(), upper_95.max()) + 10
ax.set_ylim(y_min, y_max)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
