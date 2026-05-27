""" anyplot.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: plotly 6.7.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-19
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme and chrome colors
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
COLOR_HISTORICAL = "#009E73"  # Position 1 - brand green
COLOR_FORECAST = "#C475FD"  # Position 2 - vermillion

# Data generation
np.random.seed(42)
n_historical = 36
n_forecast = 12
dates_hist_range = pd.date_range("2023-01-01", periods=n_historical, freq="MS")
dates_historical = dates_hist_range.strftime("%Y-%m-%d").tolist()
dates_forecast_range = pd.date_range(dates_hist_range[-1] + pd.DateOffset(months=1), periods=n_forecast, freq="MS")
dates_forecast = dates_forecast_range.strftime("%Y-%m-%d").tolist()

# Historical data: trend + seasonality + noise
time_idx = np.arange(n_historical)
trend = 100 + 2.5 * time_idx
seasonality = 15 * np.sin(2 * np.pi * time_idx / 12)
noise = np.random.normal(0, 8, n_historical)
actual = trend + seasonality + noise

# Forecast values
forecast_time_idx = np.arange(n_historical, n_historical + n_forecast)
forecast_trend = 100 + 2.5 * forecast_time_idx
forecast_seasonality = 15 * np.sin(2 * np.pi * forecast_time_idx / 12)
forecast_values = forecast_trend + forecast_seasonality

# Confidence intervals (widening over time)
uncertainty_base = 10
uncertainty_growth = np.sqrt(np.arange(1, n_forecast + 1)) * 5
lower_80 = forecast_values - (uncertainty_base + uncertainty_growth * 0.8)
upper_80 = forecast_values + (uncertainty_base + uncertainty_growth * 0.8)
lower_95 = forecast_values - (uncertainty_base + uncertainty_growth * 1.3)
upper_95 = forecast_values + (uncertainty_base + uncertainty_growth * 1.3)

# Create figure
fig = go.Figure()

# 95% confidence band (lighter)
fig.add_trace(
    go.Scatter(
        x=dates_forecast + dates_forecast[::-1],
        y=np.concatenate([upper_95, lower_95[::-1]]),
        fill="toself",
        fillcolor="rgba(196, 117, 253, 0.10)",
        line=dict(color="rgba(196, 117, 253, 0)"),
        name="95% CI",
        showlegend=True,
        hoverinfo="skip",
    )
)

# 80% confidence band (darker)
fig.add_trace(
    go.Scatter(
        x=dates_forecast + dates_forecast[::-1],
        y=np.concatenate([upper_80, lower_80[::-1]]),
        fill="toself",
        fillcolor="rgba(196, 117, 253, 0.32)",
        line=dict(color="rgba(196, 117, 253, 0)"),
        name="80% CI",
        showlegend=True,
        hoverinfo="skip",
    )
)

# Forecast start marker
forecast_start = dates_forecast[0]
fig.add_shape(
    type="line",
    x0=forecast_start,
    x1=forecast_start,
    y0=0,
    y1=1,
    yref="paper",
    line=dict(color=INK_SOFT, width=2, dash="dash"),
)

# Forecast start annotation
fig.add_annotation(
    x=forecast_start, y=1.02, yref="paper", text="Forecast Start", showarrow=False, font=dict(size=16, color=INK_SOFT)
)

# Historical data (solid line)
fig.add_trace(
    go.Scatter(
        x=dates_historical,
        y=actual,
        mode="lines",
        name="Historical",
        line=dict(color=COLOR_HISTORICAL, width=3),
        hovertemplate="Date: %{x}<br>Sales: %{y:.1f}<extra></extra>",
    )
)

# Forecast line (dashed)
fig.add_trace(
    go.Scatter(
        x=dates_forecast,
        y=forecast_values,
        mode="lines",
        name="Forecast",
        line=dict(color=COLOR_FORECAST, width=3, dash="dash"),
        hovertemplate="Date: %{x}<br>Forecast: %{y:.1f}<extra></extra>",
    )
)

# Connection line between historical and forecast
fig.add_trace(
    go.Scatter(
        x=[dates_historical[-1], dates_forecast[0]],
        y=[actual[-1], forecast_values[0]],
        mode="lines",
        line=dict(color=COLOR_HISTORICAL, width=2, dash="dot"),
        showlegend=False,
        hoverinfo="skip",
    )
)

# Layout with theme-adaptive colors and chrome
fig.update_layout(
    title=dict(
        text="timeseries-forecast-uncertainty · python · plotly · anyplot.ai",
        font=dict(size=28, color=INK),
        x=0.5,
        xanchor="center",
    ),
    xaxis=dict(
        title=dict(text="Date", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        showgrid=False,
        showline=True,
        mirror=False,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text="Monthly Sales (Units)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        showgrid=True,
        gridcolor=GRID,
        showline=True,
        mirror=False,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    legend=dict(
        font=dict(size=18, color=INK_SOFT),
        x=0.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    margin=dict(l=100, r=60, t=100, b=100),
    hovermode="x unified",
)

# Save outputs
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
