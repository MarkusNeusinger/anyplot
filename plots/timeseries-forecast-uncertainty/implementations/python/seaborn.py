""" pyplots.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-07
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Set seed for reproducibility
np.random.seed(42)

# Generate time series data - monthly sales with 3 years history + 6 month forecast
n_historical = 36
n_forecast = 6
n_total = n_historical + n_forecast

dates = pd.date_range(start="2022-01-01", periods=n_total, freq="MS")

# Generate historical data with trend and seasonality
t = np.arange(n_historical)
trend = 100 + 0.8 * t
seasonality = 15 * np.sin(2 * np.pi * t / 12)
noise = np.random.normal(0, 5, n_historical)
historical_values = trend + seasonality + noise

# Generate forecast with increasing uncertainty
t_forecast = np.arange(n_historical, n_total)
trend_forecast = 100 + 0.8 * t_forecast
seasonality_forecast = 15 * np.sin(2 * np.pi * t_forecast / 12)
forecast_values = trend_forecast + seasonality_forecast

# Confidence intervals widen over time
forecast_horizon = np.arange(1, n_forecast + 1)
std_base = 5
std_growth = std_base * np.sqrt(forecast_horizon)

lower_95 = forecast_values - 1.96 * std_growth
upper_95 = forecast_values + 1.96 * std_growth
lower_80 = forecast_values - 1.28 * std_growth
upper_80 = forecast_values + 1.28 * std_growth

# Create DataFrame
df = pd.DataFrame(
    {
        "date": dates,
        "actual": list(historical_values) + [np.nan] * n_forecast,
        "forecast": [np.nan] * (n_historical - 1) + [historical_values[-1]] + list(forecast_values),
        "lower_80": [np.nan] * (n_historical - 1) + [historical_values[-1]] + list(lower_80),
        "upper_80": [np.nan] * (n_historical - 1) + [historical_values[-1]] + list(upper_80),
        "lower_95": [np.nan] * (n_historical - 1) + [historical_values[-1]] + list(lower_95),
        "upper_95": [np.nan] * (n_historical - 1) + [historical_values[-1]] + list(upper_95),
    }
)

# Create figure with seaborn styling
sns.set_style("whitegrid")
fig, ax = plt.subplots(figsize=(16, 9))

# Plot 95% confidence interval (lighter band)
ax.fill_between(df["date"], df["lower_95"], df["upper_95"], alpha=0.2, color="#FFD43B", label="95% Confidence")

# Plot 80% confidence interval (darker band)
ax.fill_between(df["date"], df["lower_80"], df["upper_80"], alpha=0.35, color="#FFD43B", label="80% Confidence")

# Plot historical data
sns.lineplot(data=df, x="date", y="actual", ax=ax, color="#306998", linewidth=3, label="Historical")

# Plot forecast
sns.lineplot(data=df, x="date", y="forecast", ax=ax, color="#FFD43B", linewidth=3, linestyle="--", label="Forecast")

# Add vertical line at forecast start
forecast_start = dates[n_historical - 1]
ax.axvline(x=forecast_start, color="#666666", linestyle=":", linewidth=2, alpha=0.7)
ax.text(
    forecast_start, ax.get_ylim()[1] * 0.98, " Forecast Start", fontsize=14, color="#666666", verticalalignment="top"
)

# Styling for large canvas
ax.set_title("timeseries-forecast-uncertainty · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Monthly Sales (units)", fontsize=20)
ax.tick_params(axis="both", labelsize=16)

# Legend
ax.legend(fontsize=16, loc="upper left", framealpha=0.9)

# Grid styling
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
