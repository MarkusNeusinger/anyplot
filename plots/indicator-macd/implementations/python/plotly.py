""" anyplot.ai
indicator-macd: MACD Technical Indicator Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 81/100 | Updated: 2026-05-16
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
BRAND = "#009E73"  # MACD
SIGNAL_COLOR = "#BD8233"  # imprint ochre — signal line (categorical contrast)

# Data - Generate realistic stock price data and calculate MACD
np.random.seed(42)

n_days = 150
dates = pd.date_range("2025-06-01", periods=n_days, freq="B")

returns = np.random.normal(0.0005, 0.015, n_days)
price = pd.Series(100 * np.exp(np.cumsum(returns)))

# Calculate EMAs for MACD
ema_12 = price.ewm(span=12, adjust=False).mean()
ema_26 = price.ewm(span=26, adjust=False).mean()

# MACD components
macd_line = ema_12 - ema_26
signal_line = macd_line.ewm(span=9, adjust=False).mean()
histogram = macd_line - signal_line

# Use data from day 35 onwards (stable EMA values)
start_idx = 35
dates = dates[start_idx:]
macd_line = macd_line.values[start_idx:]
signal_line = signal_line.values[start_idx:]
histogram = histogram.values[start_idx:]

# Create histogram colors using diverging approach
hist_positive = histogram >= 0
hist_colors = [
    "#4467A3" if val else "#BD8233"  # Blue for positive, purple for negative
    for val in hist_positive
]

# Create figure
fig = make_subplots(rows=1, cols=1, vertical_spacing=0.1)

# Add MACD histogram bars
fig.add_trace(
    go.Bar(x=dates, y=histogram, name="Histogram", marker={"color": hist_colors}, opacity=0.7, showlegend=True)
)

# Add MACD line
fig.add_trace(go.Scatter(x=dates, y=macd_line, name="MACD (12, 26)", line={"color": BRAND, "width": 3}, mode="lines"))

# Add Signal line
fig.add_trace(
    go.Scatter(x=dates, y=signal_line, name="Signal (9)", line={"color": SIGNAL_COLOR, "width": 3}, mode="lines")
)

# Add zero reference line
fig.add_hline(
    y=0,
    line={"color": INK_SOFT, "width": 2, "dash": "dash"},
    annotation_text="Zero Line",
    annotation_position="left",
    annotation_font_size=16,
)

# Update layout for theme-adaptive styling
fig.update_layout(
    title={
        "text": "indicator-macd · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Date", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "showgrid": True,
    },
    yaxis={
        "title": {"text": "MACD Value", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "showgrid": True,
        "zeroline": False,
    },
    legend={
        "font": {"size": 18, "color": INK_SOFT},
        "x": 0.01,
        "y": 0.99,
        "xanchor": "left",
        "yanchor": "top",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin={"l": 100, "r": 60, "t": 100, "b": 80},
    annotations=[
        {
            "text": "Parameters: EMA(12), EMA(26), Signal(9)",
            "xref": "paper",
            "yref": "paper",
            "x": 0.99,
            "y": 0.01,
            "xanchor": "right",
            "yanchor": "bottom",
            "font": {"size": 16, "color": INK_SOFT},
            "showarrow": False,
        }
    ],
)

# Save as PNG
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
