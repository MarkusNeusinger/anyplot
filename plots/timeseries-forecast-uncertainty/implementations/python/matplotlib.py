"""anyplot.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: matplotlib | Python 3.13
Quality: 94/100 | Updated: 2026-05-19
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette — positions 1, 2, 6
HISTORICAL_COLOR = "#009E73"  # Position 1: brand green
FORECAST_COLOR = "#D55E00"  # Position 2: vermillion
CI_COLOR = "#56B4E9"  # Position 6: sky blue (for CI bands)

# Data - Monthly retail sales with ARIMA-style forecast
np.random.seed(42)

n_historical = 36
n_forecast = 12
overlap = 1
n_total = n_historical + n_forecast - overlap

dates = pd.date_range(start="2022-01-01", periods=n_total, freq="MS")

# Historical: trend + seasonality + noise
t = np.arange(n_historical)
trend = 100 + t * 1.2
seasonality = 15 * np.sin(2 * np.pi * t / 12)
noise = np.random.normal(0, 5, n_historical)
actual = trend + seasonality + noise

# Forecast: continuation from last historical point
forecast_start_idx = n_historical - overlap
forecast_start = actual[forecast_start_idx]
t_forecast = np.arange(n_forecast)
forecast_trend = forecast_start + t_forecast * 1.2
forecast_seasonality = 15 * np.sin(2 * np.pi * (t[-1] - overlap + 1 + t_forecast) / 12)
forecast_values = forecast_trend + forecast_seasonality

# Confidence intervals that widen with forecast horizon (sqrt fan-out)
uncertainty_growth = np.sqrt(1 + t_forecast * 0.5)
base_std = 8
lower_80 = forecast_values - 1.28 * base_std * uncertainty_growth
upper_80 = forecast_values + 1.28 * base_std * uncertainty_growth
lower_95 = forecast_values - 1.96 * base_std * uncertainty_growth
upper_95 = forecast_values + 1.96 * base_std * uncertainty_growth

historical_dates = dates[:n_historical]
forecast_dates = dates[forecast_start_idx:]

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.set_axisbelow(True)

# Subtle background tint for forecast region
ax.axvspan(forecast_dates[0], forecast_dates[-1], color=INK, alpha=0.03, zorder=0)

# Confidence bands (wider outer band first so narrower sits on top)
ax.fill_between(forecast_dates, lower_95, upper_95, color=CI_COLOR, alpha=0.20, label="95% Confidence Interval")
ax.fill_between(forecast_dates, lower_80, upper_80, color=CI_COLOR, alpha=0.30, label="80% Confidence Interval")

# Historical solid line
ax.plot(historical_dates, actual, color=HISTORICAL_COLOR, linewidth=3, label="Historical Data", solid_capstyle="round")

# Forecast dashed line
ax.plot(
    forecast_dates,
    forecast_values,
    color=FORECAST_COLOR,
    linewidth=3,
    linestyle="--",
    label="Forecast",
    solid_capstyle="round",
    dash_capstyle="round",
)

# Dotted vertical marker at forecast start
ax.axvline(x=forecast_dates[0], color=INK_SOFT, linewidth=1.5, linestyle=":", alpha=0.7, label="Forecast Start")

# Style
ax.set_xlabel("Date", fontsize=20, color=INK)
ax.set_ylabel("Monthly Sales (thousands)", fontsize=20, color=INK)
ax.set_title(
    "timeseries-forecast-uncertainty · python · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK
)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Date axis: semi-annual major ticks, readable labels
tick_dates = pd.date_range(start=dates[0], end=dates[-1], freq="6MS")
ax.set_xticks(tick_dates)
ax.set_xticklabels([d.strftime("%b %Y") for d in tick_dates], rotation=30, ha="right")

# Grid (y-axis only, very subtle)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

# Spines
for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

# Legend — outside plot area, bottom-left
leg = ax.legend(fontsize=16, loc="lower left", framealpha=0.95, bbox_to_anchor=(0, -0.15))
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)

# Y-axis limits with breathing room
y_min = min(actual.min(), lower_95.min()) - 10
y_max = max(actual.max(), upper_95.max()) + 10
ax.set_ylim(y_min, y_max)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
