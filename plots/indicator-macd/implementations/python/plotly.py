""" anyplot.ai
indicator-macd: MACD Technical Indicator Chart
Library: plotly 7.1.0 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-22
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
GRID = "rgba(26,26,23,0.12)" if THEME == "light" else "rgba(240,239,232,0.12)"

# Imprint palette: histogram green first, then red for negative bars, blue and ochre for the two lines
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
UP_COLOR = IMPRINT_PALETTE[0]
DOWN_COLOR = IMPRINT_PALETTE[4]
MACD_COLOR = IMPRINT_PALETTE[2]
SIGNAL_COLOR = IMPRINT_PALETTE[3]

# Constants
FAST, SLOW, SIGNAL_SPAN = 12, 26, 9  # standard MACD parameters

# Columns: set these to your table's column names
DATE = "Date"  # role: date
MACD = "MACD"  # role: macd
SIGNAL = "Signal"  # role: signal
HISTOGRAM = "Histogram"  # role: histogram

# Data: replace this block with your own table, for example df = pd.read_csv("macd.csv")
# Synthetic daily crypto closes with alternating trend regimes; MACD from 12/26/9 EMAs
rng = np.random.default_rng(7)
n_days = 200
dates = pd.date_range("2025-01-01", periods=n_days, freq="D")
drift = np.repeat([0.004, -0.005, 0.003, -0.003, 0.005], n_days // 5)
returns = rng.normal(drift, 0.022)
close = pd.Series(30000 * np.exp(np.cumsum(returns)))
macd_line = close.ewm(span=FAST, adjust=False).mean() - close.ewm(span=SLOW, adjust=False).mean()
signal_line = macd_line.ewm(span=SIGNAL_SPAN, adjust=False).mean()
df = pd.DataFrame({DATE: dates, MACD: macd_line, SIGNAL: signal_line, HISTOGRAM: macd_line - signal_line}).iloc[
    SLOW + SIGNAL_SPAN :
]

# Plot
bar_colors = np.where(df[HISTOGRAM] >= 0, UP_COLOR, DOWN_COLOR)
title = "indicator-macd · python · plotly · anyplot.ai"

fig = go.Figure()
fig.add_trace(
    go.Bar(
        x=df[DATE], y=df[HISTOGRAM], name=HISTOGRAM, marker={"color": bar_colors, "line": {"width": 0}}, opacity=0.75
    )
)
fig.add_trace(
    go.Scatter(x=df[DATE], y=df[MACD], name=f"{MACD} ({FAST}, {SLOW})", line={"color": MACD_COLOR, "width": 2.5})
)
fig.add_trace(
    go.Scatter(x=df[DATE], y=df[SIGNAL], name=f"{SIGNAL} ({SIGNAL_SPAN})", line={"color": SIGNAL_COLOR, "width": 2.5})
)

fig.add_hline(y=0, layer="above", line={"color": INK_SOFT, "width": 1.5, "dash": "dash"})

fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    title={"text": title, "font": {"size": 16, "color": INK}, "x": 0.5, "xanchor": "center"},
    font={"color": INK},
    xaxis={
        "title": {"text": DATE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "showgrid": False,
    },
    yaxis={
        "title": {"text": "MACD value (USD)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zeroline": False,
    },
    legend={
        "font": {"size": 10, "color": INK_SOFT},
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
    bargap=0.1,
    margin={"l": 80, "r": 40, "t": 60, "b": 60},
    annotations=[
        {
            "text": f"Parameters: EMA({FAST}), EMA({SLOW}), Signal({SIGNAL_SPAN})",
            "xref": "paper",
            "yref": "paper",
            "x": 0.99,
            "y": 0.02,
            "xanchor": "right",
            "yanchor": "bottom",
            "font": {"size": 10, "color": INK_SOFT},
            "showarrow": False,
        }
    ],
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
