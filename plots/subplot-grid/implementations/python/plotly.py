""" anyplot.ai
subplot-grid: Subplot Grid Layout
Library: plotly 7.1.0 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-21
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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
MA_WINDOW = 20  # days in the moving average

# Columns: set these to your table's column names
DATE = "Date"  # role: x
PRICE = "Price ($)"  # role: y
VOLUME = "Volume"  # role: extra
DAILY_RETURN = "Daily Return (%)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("stock.csv")
np.random.seed(42)
days = 60
returns = np.random.normal(0.001, 0.02, days)
price = 100 * np.cumprod(1 + returns)
volume = 1000000 + np.abs(returns) * 50000000 + np.random.normal(0, 200000, days)
df = pd.DataFrame(
    {
        DATE: pd.date_range("2024-01-01", periods=days, freq="D"),
        PRICE: price,
        VOLUME: np.clip(volume, 500000, 3000000),
        DAILY_RETURN: returns * 100,
    }
)

# Plot
ma_label = f"{MA_WINDOW}-day MA"
ma = df[PRICE].rolling(MA_WINDOW).mean()
up_down = [IMPRINT_PALETTE[0] if r >= 0 else IMPRINT_PALETTE[1] for r in df[DAILY_RETURN]]

fig = make_subplots(
    rows=2,
    cols=2,
    subplot_titles=("Stock Price & Moving Average", "Trading Volume", "Daily Returns Distribution", "Price vs Volume"),
    horizontal_spacing=0.1,
    vertical_spacing=0.25,
    specs=[[{"type": "scatter"}, {"type": "bar"}], [{"type": "histogram"}, {"type": "scatter"}]],
)

# Line chart: price with moving average (the only cell with a legend)
fig.add_trace(
    go.Scatter(x=df[DATE], y=df[PRICE], mode="lines", name="Price", line={"color": IMPRINT_PALETTE[0], "width": 2.5}),
    row=1,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=df[DATE], y=ma, mode="lines", name=ma_label, line={"color": IMPRINT_PALETTE[1], "width": 2, "dash": "dash"}
    ),
    row=1,
    col=1,
)

# Bar chart: volume, colored by up / down day
fig.add_trace(
    go.Bar(x=df[DATE], y=df[VOLUME], marker={"color": up_down, "opacity": 0.8}, showlegend=False), row=1, col=2
)

# Histogram: distribution of daily returns
fig.add_trace(
    go.Histogram(
        x=df[DAILY_RETURN].iloc[1:],
        nbinsx=20,
        marker={"color": IMPRINT_PALETTE[0], "opacity": 0.75, "line": {"color": PAGE_BG, "width": 1}},
        showlegend=False,
    ),
    row=2,
    col=1,
)

# Scatter: price against volume
fig.add_trace(
    go.Scatter(
        x=df[VOLUME],
        y=df[PRICE],
        mode="markers",
        marker={"color": IMPRINT_PALETTE[0], "size": 8, "opacity": 0.7, "line": {"color": PAGE_BG, "width": 1}},
        showlegend=False,
    ),
    row=2,
    col=2,
)

fig.update_layout(
    autosize=False,
    title={
        "text": "subplot-grid · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    showlegend=True,
    legend={
        "font": {"size": 10, "color": INK_SOFT},
        "x": 0.44,
        "y": 0.97,
        "xanchor": "right",
        "yanchor": "top",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 70, "r": 30, "t": 80, "b": 55},
)

axis_style = {
    "tickfont": {"size": 10, "color": INK_SOFT},
    "title_font": {"size": 12, "color": INK},
    "gridcolor": GRID,
    "showgrid": True,
    "gridwidth": 1,
    "linecolor": INK_SOFT,
    "zerolinecolor": INK_SOFT,
}
fig.update_xaxes(**axis_style)
fig.update_yaxes(**axis_style)

fig.update_xaxes(title_text=DATE, tickformat="%b %d", nticks=5, row=1, col=1)
fig.update_yaxes(title_text=PRICE, row=1, col=1)
fig.update_xaxes(title_text=DATE, tickformat="%b %d", nticks=5, row=1, col=2)
fig.update_yaxes(title_text=VOLUME, row=1, col=2)
fig.update_xaxes(title_text=DAILY_RETURN, row=2, col=1)
fig.update_yaxes(title_text="Frequency", row=2, col=1)
fig.update_xaxes(title_text=VOLUME, row=2, col=2)
fig.update_yaxes(title_text=PRICE, row=2, col=2)

for annotation in fig["layout"]["annotations"]:
    annotation["font"] = {"size": 13, "color": INK}

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
