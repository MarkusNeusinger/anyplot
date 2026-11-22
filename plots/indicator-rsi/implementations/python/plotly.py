"""anyplot.ai
indicator-rsi: RSI Technical Indicator Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-16
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
GRID = "rgba(26, 26, 23, 0.10)" if THEME == "light" else "rgba(240, 239, 232, 0.10)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
LOOKBACK = 14  # standard RSI lookback period, in periods
OVERBOUGHT = 70
CENTER = 50
OVERSOLD = 30
RSI_RANGE = [0, 100]  # RSI is bounded by definition

# Columns: set these to your table's column names
DATE = "Date"  # role: date
RSI = "RSI (14)"  # role: rsi

# Data: replace this block with your own table, for example df = pd.read_csv("rsi.csv")
np.random.seed(42)
dates = pd.date_range("2024-01-01", periods=120, freq="D")

# Simulate price movement with trends
returns = np.random.randn(120) * 0.015
returns[20:40] += 0.01  # Bull run
returns[60:80] -= 0.012  # Bear period
returns[95:110] += 0.008  # Recovery
price = pd.Series(100 * np.cumprod(1 + returns))

# RSI from simple rolling averages of gains and losses; the first values stay missing until the lookback is filled
change = price.diff()
avg_gain = change.clip(lower=0).rolling(window=LOOKBACK, min_periods=LOOKBACK).mean()
avg_loss = (-change).clip(lower=0).rolling(window=LOOKBACK, min_periods=LOOKBACK).mean()
df = pd.DataFrame({DATE: dates, RSI: 100 - 100 / (1 + avg_gain / avg_loss)})

# Plot: reads only df and the constants above
x = df[DATE]
n = len(df)
green, red, blue = IMPRINT_PALETTE[0], IMPRINT_PALETTE[4], IMPRINT_PALETTE[2]

fig = go.Figure()

# Overbought zone (above the upper threshold): invisible ceiling trace, then fill down to the threshold
fig.add_trace(
    go.Scatter(x=x, y=[RSI_RANGE[1]] * n, mode="lines", line={"width": 0}, showlegend=False, hoverinfo="skip")
)
fig.add_trace(
    go.Scatter(
        x=x,
        y=[OVERBOUGHT] * n,
        fill="tonexty",
        mode="lines",
        line={"width": 0},
        fillcolor="rgba(196, 117, 253, 0.15)",
        name=f"Overbought zone ({OVERBOUGHT}-{RSI_RANGE[1]})",
        hoverinfo="skip",
    )
)

# Oversold zone (below the lower threshold)
fig.add_trace(go.Scatter(x=x, y=[OVERSOLD] * n, mode="lines", line={"width": 0}, showlegend=False, hoverinfo="skip"))
fig.add_trace(
    go.Scatter(
        x=x,
        y=[RSI_RANGE[0]] * n,
        fill="tonexty",
        mode="lines",
        line={"width": 0},
        fillcolor="rgba(0, 158, 115, 0.15)",
        name=f"Oversold zone ({RSI_RANGE[0]}-{OVERSOLD})",
        hoverinfo="skip",
    )
)

# RSI line
fig.add_trace(go.Scatter(x=x, y=df[RSI], mode="lines", name=RSI, line={"color": green, "width": 2.5}))

# Reference lines with labels at the right edge
for level, label, color, dash, width in [
    (OVERBOUGHT, "Overbought", red, "dash", 1.5),
    (CENTER, "Neutral", INK_SOFT, "dot", 1.2),
    (OVERSOLD, "Oversold", blue, "dash", 1.5),
]:
    fig.add_hline(y=level, line_dash=dash, line_color=color, line_width=width)
    fig.add_annotation(
        x=x.iloc[-1],
        y=level,
        text=f"{label} ({level})",
        showarrow=False,
        xanchor="left",
        xshift=6,
        font={"size": 11, "color": color},
    )

# Style
fig.update_layout(
    autosize=False,
    title={
        "text": "indicator-rsi · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "range": [x.min(), x.max()],
        "title": {"text": DATE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": RSI, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "range": RSI_RANGE,
        "showgrid": True,
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "dtick": 10,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "center",
        "x": 0.5,
        "font": {"size": 10, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    margin={"l": 60, "r": 100, "t": 80, "b": 50},
)

# Save outputs
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
