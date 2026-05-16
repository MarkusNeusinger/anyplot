"""anyplot.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-05-16
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]
COLOR_HISTORICAL = OKABE_ITO[0]  # Green
COLOR_FORECAST = OKABE_ITO[1]  # Vermillion

# Set seed for reproducibility
np.random.seed(42)

# Generate stock price time series with forecast
n_historical = 60  # 60 trading days (~3 months)
n_forecast = 20  # 20 trading days (~4 weeks)
n_total = n_historical + n_forecast

dates = pd.date_range(start="2025-01-01", periods=n_total, freq="B")  # Business days

# Generate historical stock prices with trend and volatility
t = np.arange(n_historical)
base_price = 150
trend = 0.15 * t  # Slight upward trend
volatility = 2.5 * np.sin(2 * np.pi * t / 20)  # 20-day cycles
noise = np.random.normal(0, 1.5, n_historical)
historical_prices = base_price + trend + volatility + noise

# Generate forecast with increasing uncertainty
t_forecast = np.arange(n_historical, n_total)
trend_forecast = base_price + 0.15 * t_forecast
seasonality_forecast = 2.5 * np.sin(2 * np.pi * t_forecast / 20)
forecast_prices = trend_forecast + seasonality_forecast

# Confidence intervals widen over forecast horizon
forecast_horizon = np.arange(1, n_forecast + 1)
std_base = 1.5
std_growth = std_base * np.sqrt(forecast_horizon)

lower_95 = forecast_prices - 1.96 * std_growth
upper_95 = forecast_prices + 1.96 * std_growth
lower_80 = forecast_prices - 1.28 * std_growth
upper_80 = forecast_prices + 1.28 * std_growth

# Create DataFrame
df = pd.DataFrame(
    {
        "date": dates,
        "actual": list(historical_prices) + [np.nan] * n_forecast,
        "forecast": [np.nan] * (n_historical - 1) + [historical_prices[-1]] + list(forecast_prices),
        "lower_80": [np.nan] * (n_historical - 1) + [historical_prices[-1]] + list(lower_80),
        "upper_80": [np.nan] * (n_historical - 1) + [historical_prices[-1]] + list(upper_80),
        "lower_95": [np.nan] * (n_historical - 1) + [historical_prices[-1]] + list(lower_95),
        "upper_95": [np.nan] * (n_historical - 1) + [historical_prices[-1]] + list(upper_95),
    }
)

# Configure seaborn theme with theme-adaptive colors
sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Plot confidence intervals (95% lighter, 80% darker)
ax.fill_between(df["date"], df["lower_95"], df["upper_95"], alpha=0.15, color=COLOR_FORECAST, label="95% Confidence")
ax.fill_between(df["date"], df["lower_80"], df["upper_80"], alpha=0.25, color=COLOR_FORECAST, label="80% Confidence")

# Plot historical data
ax.plot(df["date"], df["actual"], color=COLOR_HISTORICAL, linewidth=3, label="Historical", zorder=3)

# Plot forecast with dashed line
ax.plot(
    df[df["forecast"].notna()]["date"],
    df[df["forecast"].notna()]["forecast"],
    color=COLOR_FORECAST,
    linewidth=3,
    linestyle="--",
    label="Forecast",
    zorder=3,
)

# Add vertical line at forecast start
forecast_start = dates[n_historical - 1]
ax.axvline(x=forecast_start, color=INK_SOFT, linestyle=":", linewidth=1.5, alpha=0.5)

# Styling
ax.set_title(
    "timeseries-forecast-uncertainty · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=20
)
ax.set_xlabel("Date", fontsize=20, color=INK)
ax.set_ylabel("Stock Price ($)", fontsize=20, color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Subtle grid on y-axis only
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

# Legend
ax.legend(fontsize=16, loc="upper left", framealpha=1.0, fancybox=False, edgecolor=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
