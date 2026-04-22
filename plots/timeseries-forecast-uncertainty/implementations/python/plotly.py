""" pyplots.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-07
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data
np.random.seed(42)

# Historical data: 36 months of monthly sales data with trend and seasonality
n_historical = 36
n_forecast = 12
dates_historical = pd.date_range("2023-01-01", periods=n_historical, freq="MS")
dates_forecast = pd.date_range(dates_historical[-1] + pd.DateOffset(months=1), periods=n_forecast, freq="MS")

# Generate historical values with trend, seasonality, and noise
time_idx = np.arange(n_historical)
trend = 100 + 2.5 * time_idx
seasonality = 15 * np.sin(2 * np.pi * time_idx / 12)
noise = np.random.normal(0, 8, n_historical)
actual = trend + seasonality + noise

# Generate forecast values continuing the pattern
forecast_time_idx = np.arange(n_historical, n_historical + n_forecast)
forecast_trend = 100 + 2.5 * forecast_time_idx
forecast_seasonality = 15 * np.sin(2 * np.pi * forecast_time_idx / 12)
forecast_values = forecast_trend + forecast_seasonality

# Generate confidence intervals (widening over time)
uncertainty_base = 10
uncertainty_growth = np.sqrt(np.arange(1, n_forecast + 1)) * 5

# 80% confidence interval
lower_80 = forecast_values - (uncertainty_base + uncertainty_growth * 0.8)
upper_80 = forecast_values + (uncertainty_base + uncertainty_growth * 0.8)

# 95% confidence interval (wider)
lower_95 = forecast_values - (uncertainty_base + uncertainty_growth * 1.3)
upper_95 = forecast_values + (uncertainty_base + uncertainty_growth * 1.3)

# Combine dates for full timeline
all_dates = dates_historical.append(dates_forecast)

# Create figure
fig = go.Figure()

# 95% confidence band (lighter, add first so it's in back)
fig.add_trace(
    go.Scatter(
        x=pd.concat([pd.Series(dates_forecast), pd.Series(dates_forecast[::-1])]),
        y=np.concatenate([upper_95, lower_95[::-1]]),
        fill="toself",
        fillcolor="rgba(255, 212, 59, 0.2)",
        line=dict(color="rgba(255, 212, 59, 0)"),
        name="95% CI",
        showlegend=True,
        hoverinfo="skip",
    )
)

# 80% confidence band (darker)
fig.add_trace(
    go.Scatter(
        x=pd.concat([pd.Series(dates_forecast), pd.Series(dates_forecast[::-1])]),
        y=np.concatenate([upper_80, lower_80[::-1]]),
        fill="toself",
        fillcolor="rgba(255, 212, 59, 0.4)",
        line=dict(color="rgba(255, 212, 59, 0)"),
        name="80% CI",
        showlegend=True,
        hoverinfo="skip",
    )
)

# Vertical line at forecast start using shape
forecast_start = dates_forecast[0]
fig.add_shape(
    type="line",
    x0=forecast_start,
    x1=forecast_start,
    y0=0,
    y1=1,
    yref="paper",
    line=dict(color="#888888", width=2, dash="dash"),
)

# Annotation for forecast start
fig.add_annotation(
    x=forecast_start, y=1.02, yref="paper", text="Forecast Start", showarrow=False, font=dict(size=16, color="#666666")
)

# Historical data (solid line)
fig.add_trace(
    go.Scatter(
        x=dates_historical,
        y=actual,
        mode="lines",
        name="Historical",
        line=dict(color="#306998", width=3),
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
        line=dict(color="#FFD43B", width=3, dash="dash"),
        hovertemplate="Date: %{x}<br>Forecast: %{y:.1f}<extra></extra>",
    )
)

# Connection point between historical and forecast
fig.add_trace(
    go.Scatter(
        x=[dates_historical[-1], dates_forecast[0]],
        y=[actual[-1], forecast_values[0]],
        mode="lines",
        line=dict(color="#306998", width=2, dash="dot"),
        showlegend=False,
        hoverinfo="skip",
    )
)

# Layout
fig.update_layout(
    title=dict(
        text="timeseries-forecast-uncertainty · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text="Date", font=dict(size=22)),
        tickfont=dict(size=18),
        showgrid=True,
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
    ),
    yaxis=dict(
        title=dict(text="Monthly Sales (Units)", font=dict(size=22)),
        tickfont=dict(size=18),
        showgrid=True,
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
    ),
    template="plotly_white",
    legend=dict(
        font=dict(size=18),
        x=0.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="rgba(0,0,0,0.2)",
        borderwidth=1,
    ),
    margin=dict(l=80, r=40, t=80, b=80),
    hovermode="x unified",
)

# Save as PNG
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs="cdn")
