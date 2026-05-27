""" anyplot.ai
indicator-rsi: RSI Technical Indicator Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-16
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"

# Generate sample stock data and calculate RSI
np.random.seed(42)
dates = pd.date_range("2024-01-01", periods=120, freq="D").strftime("%Y-%m-%d")

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
        fillcolor="rgba(213, 94, 0, 0.15)",
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
        fillcolor="rgba(0, 158, 115, 0.15)",
        name="Oversold Zone (0-30)",
    )
)

# RSI line
fig.add_trace(go.Scatter(x=dates, y=rsi, mode="lines", name="RSI (14)", line={"color": BRAND, "width": 3}))

# Add reference lines
fig.add_hline(y=70, line_dash="dash", line_color="#AE3030", line_width=2)  # imprint red overbought
fig.add_hline(y=50, line_dash="dot", line_color=INK_SOFT, line_width=1.5)
fig.add_hline(y=30, line_dash="dash", line_color="#4467A3", line_width=2)

# Annotations for threshold lines
fig.add_annotation(
    x=dates[-1],
    y=70,
    text="Overbought (70)",
    showarrow=False,
    xanchor="left",
    xshift=10,
    font={"size": 16, "color": "#AE3030"},
)
fig.add_annotation(
    x=dates[-1],
    y=50,
    text="Neutral (50)",
    showarrow=False,
    xanchor="left",
    xshift=10,
    font={"size": 14, "color": INK_SOFT},
)
fig.add_annotation(
    x=dates[-1],
    y=30,
    text="Oversold (30)",
    showarrow=False,
    xanchor="left",
    xshift=10,
    font={"size": 16, "color": "#4467A3"},
)

# Layout
fig.update_layout(
    title={
        "text": "indicator-rsi · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Date", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
    },
    yaxis={
        "title": {"text": "RSI Value", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "range": [0, 100],
        "showgrid": True,
        "gridcolor": GRID,
        "dtick": 10,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    legend={
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "center",
        "x": 0.5,
        "font": {"size": 16, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    margin={"l": 80, "r": 120, "t": 100, "b": 80},
)

# Save outputs
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
