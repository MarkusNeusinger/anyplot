"""anyplot.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-05-16
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series is brand green #009E73)
HISTORICAL_COLOR = "#009E73"  # Position 1: brand green
FORECAST_COLOR = "#D55E00"  # Position 2: vermillion
CI_COLOR = "#56B4E9"  # Position 6: sky blue (for CI bands)

# Data - Monthly retail sales with forecast
np.random.seed(42)

# Historical period: 36 months (3 years)
n_historical = 36
# Forecast period: 12 months
n_forecast = 12
# Overlap: 1 month for continuity
overlap = 1

n_total = n_historical + n_forecast - overlap

# Create date range
dates = pd.date_range(start="2022-01-01", periods=n_total, freq="MS")

# Generate historical data with trend, seasonality, and noise
t = np.arange(n_historical)
trend = 100 + t * 1.2  # Upward trend
seasonality = 15 * np.sin(2 * np.pi * t / 12)  # Annual seasonality
noise = np.random.normal(0, 5, n_historical)
actual = trend + seasonality + noise

# Generate forecast starting from last historical value
forecast_start_idx = n_historical - overlap
forecast_start = actual[forecast_start_idx]
t_forecast = np.arange(n_forecast)
forecast_trend = forecast_start + t_forecast * 1.2
forecast_seasonality = 15 * np.sin(2 * np.pi * (t[-1] - overlap + 1 + t_forecast) / 12)
forecast_values = forecast_trend + forecast_seasonality

# Create confidence intervals that widen over time
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
forecast_dates = dates[forecast_start_idx:]

# Create plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Plot 95% confidence band (lighter, wider)
ax.fill_between(forecast_dates, lower_95, upper_95, color=CI_COLOR, alpha=0.2, label="95% Confidence Interval")

# Plot 80% confidence band (darker, narrower)
ax.fill_between(forecast_dates, lower_80, upper_80, color=CI_COLOR, alpha=0.3, label="80% Confidence Interval")

# Plot historical data (solid line)
ax.plot(historical_dates, actual, color=HISTORICAL_COLOR, linewidth=3, label="Historical Data", solid_capstyle="round")

# Plot forecast (dashed line)
ax.plot(
    forecast_dates,
    forecast_values,
    color=FORECAST_COLOR,
    linewidth=3,
    linestyle="--",
    label="Forecast",
    solid_capstyle="round",
)

# Add vertical line at forecast start
ax.axvline(
    x=historical_dates[forecast_start_idx],
    color=INK_SOFT,
    linewidth=2,
    linestyle=":",
    alpha=0.6,
    label="Forecast Start",
)

# Labels and styling
ax.set_xlabel("Date", fontsize=20, color=INK)
ax.set_ylabel("Monthly Sales (thousands)", fontsize=20, color=INK)
ax.set_title("timeseries-forecast-uncertainty · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Format x-axis dates
fig.autofmt_xdate(rotation=30)

# Grid (subtle, y-axis only)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.grid(False, axis="x")

# Spine styling
for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

# Legend (positioned at lower left, outside plot area)
leg = ax.legend(fontsize=16, loc="lower left", framealpha=0.95, bbox_to_anchor=(0, -0.15))
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)

# Set y-axis limits with some padding
y_min = min(actual.min(), lower_95.min()) - 10
y_max = max(actual.max(), upper_95.max()) + 10
ax.set_ylim(y_min, y_max)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
