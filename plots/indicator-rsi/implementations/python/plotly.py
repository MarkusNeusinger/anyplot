""" pyplots.ai
indicator-rsi: RSI Technical Indicator Chart
Library: plotly 6.5.1 | Python 3.13.11
Quality: 94/100 | Created: 2026-01-07
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Generate sample stock data and calculate RSI
np.random.seed(42)
dates = pd.date_range("2024-01-01", periods=120, freq="D")

# Simulate price movement with trends
returns = np.random.randn(120) * 0.015
returns[20:40] += 0.01  # Bull run
returns[60:80] -= 0.012  # Bear period
returns[95:110] += 0.008  # Recovery
price = 100 * np.cumprod(1 + returns)

# Calculate RSI (14-period)
delta = pd.Series(price).diff()
gain = delta.where(delta > 0, 0)
loss = (-delta).where(delta < 0, 0)

avg_gain = gain.rolling(window=14, min_periods=14).mean()
avg_loss = loss.rolling(window=14, min_periods=14).mean()

rs = avg_gain / avg_loss
rsi = 100 - (100 / (1 + rs))
rsi = rsi.fillna(50)

# Create figure
fig = go.Figure()

# Overbought zone (70-100)
fig.add_trace(
    go.Scatter(
        x=dates, y=[100] * len(dates), fill=None, mode="lines", line={"width": 0}, showlegend=False, hoverinfo="skip"
    )
)
fig.add_trace(
    go.Scatter(
        x=dates,
        y=[70] * len(dates),
        fill="tonexty",
        mode="lines",
        line={"width": 0},
        fillcolor="rgba(255, 99, 71, 0.2)",
        name="Overbought Zone (70-100)",
    )
)

# Oversold zone (0-30)
fig.add_trace(
    go.Scatter(
        x=dates, y=[30] * len(dates), fill=None, mode="lines", line={"width": 0}, showlegend=False, hoverinfo="skip"
    )
)
fig.add_trace(
    go.Scatter(
        x=dates,
        y=[0] * len(dates),
        fill="tonexty",
        mode="lines",
        line={"width": 0},
        fillcolor="rgba(50, 205, 50, 0.2)",
        name="Oversold Zone (0-30)",
    )
)

# RSI line
fig.add_trace(go.Scatter(x=dates, y=rsi, mode="lines", name="RSI (14)", line={"color": "#306998", "width": 3}))

# Add reference lines
fig.add_hline(y=70, line_dash="dash", line_color="#FF6347", line_width=2)
fig.add_hline(y=50, line_dash="dot", line_color="#888888", line_width=1.5)
fig.add_hline(y=30, line_dash="dash", line_color="#32CD32", line_width=2)

# Annotations for threshold lines
fig.add_annotation(
    x=dates[-1],
    y=70,
    text="Overbought (70)",
    showarrow=False,
    xanchor="left",
    xshift=10,
    font={"size": 16, "color": "#FF6347"},
)
fig.add_annotation(
    x=dates[-1],
    y=50,
    text="Neutral (50)",
    showarrow=False,
    xanchor="left",
    xshift=10,
    font={"size": 14, "color": "#888888"},
)
fig.add_annotation(
    x=dates[-1],
    y=30,
    text="Oversold (30)",
    showarrow=False,
    xanchor="left",
    xshift=10,
    font={"size": 16, "color": "#32CD32"},
)

# Layout
fig.update_layout(
    title={"text": "indicator-rsi · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Date", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "showgrid": True,
        "gridcolor": "rgba(128, 128, 128, 0.2)",
    },
    yaxis={
        "title": {"text": "RSI Value", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "range": [0, 100],
        "showgrid": True,
        "gridcolor": "rgba(128, 128, 128, 0.2)",
        "dtick": 10,
    },
    template="plotly_white",
    legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "center", "x": 0.5, "font": {"size": 16}},
    margin={"l": 80, "r": 120, "t": 100, "b": 80},
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
