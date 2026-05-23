"""anyplot.ai
dashboard-synchronized-crosshair: Synchronized Multi-Chart Dashboard
Library: plotly | Python 3.13
Quality: pending | Created: 2026-05-23
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

# anyplot palette
PRICE_COLOR = "#009E73"  # position 1 - green
VOLUME_COLOR = "#9418DB"  # position 2 - purple
RSI_COLOR = "#16B8F3"  # position 4 - sky blue

# Data - Stock data: price, volume, and 14-period RSI over 200 trading days
np.random.seed(42)
n_points = 200
dates = pd.date_range("2024-01-01", periods=n_points, freq="B")

price_returns = np.random.normal(0.0005, 0.015, n_points)
price = 100 * np.cumprod(1 + price_returns)

base_volume = 1_000_000
volume = (base_volume * (1 + 2 * np.abs(price_returns) + np.random.uniform(0, 0.5, n_points))).astype(int)

# Standard 14-period RSI using Wilder's smoothing method
period = 14
price_changes = np.diff(price, prepend=np.nan)
gains = np.where(price_changes > 0, price_changes, 0.0)
losses = np.where(price_changes < 0, -price_changes, 0.0)

avg_gain = np.full(n_points, np.nan)
avg_loss = np.full(n_points, np.nan)
avg_gain[period] = np.mean(gains[1 : period + 1])
avg_loss[period] = np.mean(losses[1 : period + 1])
for i in range(period + 1, n_points):
    avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gains[i]) / period
    avg_loss[i] = (avg_loss[i - 1] * (period - 1) + losses[i]) / period

rs = np.where(avg_loss == 0, np.inf, avg_gain / avg_loss)
rsi = np.where(np.isinf(rs), 100.0, 100.0 - 100.0 / (1 + rs))

df = pd.DataFrame({"date": dates, "price": price, "volume": volume, "rsi": rsi})

# Plot - 3 vertically stacked panels with shared x-axis
fig = make_subplots(
    rows=3,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.08,
    row_heights=[0.5, 0.25, 0.25],
    subplot_titles=("Price (USD)", "Volume", "RSI (14-period)"),
)

fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["price"],
        mode="lines",
        name="Price",
        line=dict(color=PRICE_COLOR, width=2.5),
        hovertemplate="$%{y:.2f}<extra>Price</extra>",
    ),
    row=1,
    col=1,
)

fig.add_trace(
    go.Bar(
        x=df["date"],
        y=df["volume"],
        name="Volume",
        marker=dict(color=VOLUME_COLOR, opacity=0.8),
        hovertemplate="%{y:,.0f}<extra>Volume</extra>",
    ),
    row=2,
    col=1,
)

fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["rsi"],
        mode="lines",
        name="RSI",
        line=dict(color=RSI_COLOR, width=2.5),
        hovertemplate="%{y:.1f}<extra>RSI</extra>",
    ),
    row=3,
    col=1,
)

# RSI reference lines — distinct dash patterns for colorblind accessibility
fig.add_hline(y=70, line_dash="dash", line_color="#B71D27", line_width=1.5, row=3, col=1)
fig.add_hline(y=30, line_dash="dot", line_color="#009E73", line_width=1.5, row=3, col=1)

# Style
fig.update_layout(
    autosize=False,
    template="plotly_white",
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    title=dict(
        text="dashboard-synchronized-crosshair · python · plotly · anyplot.ai",
        font=dict(size=16, color=INK),
        x=0.5,
        xanchor="center",
    ),
    hovermode="x unified",
    hoverlabel=dict(font_size=10, bgcolor=ELEVATED_BG, bordercolor=INK_SOFT, font=dict(color=INK)),
    showlegend=False,
    margin=dict(l=100, r=40, t=80, b=60),
    font=dict(color=INK),
)

for annotation in fig["layout"]["annotations"]:
    annotation["font"] = dict(size=12, color=INK_SOFT)

fig.update_yaxes(
    title_text="Price (USD)",
    title_font=dict(size=12, color=INK),
    tickfont=dict(size=10, color=INK_SOFT),
    gridcolor=GRID,
    linecolor=INK_SOFT,
    zerolinecolor=GRID,
    row=1,
    col=1,
)
fig.update_yaxes(
    title_text="Volume",
    title_font=dict(size=12, color=INK),
    tickfont=dict(size=10, color=INK_SOFT),
    gridcolor=GRID,
    linecolor=INK_SOFT,
    zerolinecolor=GRID,
    row=2,
    col=1,
)
fig.update_yaxes(
    title_text="RSI",
    title_font=dict(size=12, color=INK),
    tickfont=dict(size=10, color=INK_SOFT),
    gridcolor=GRID,
    linecolor=INK_SOFT,
    zerolinecolor=GRID,
    range=[0, 100],
    row=3,
    col=1,
)

fig.update_xaxes(gridcolor=GRID, linecolor=INK_SOFT)
fig.update_xaxes(
    title_text="Date", title_font=dict(size=12, color=INK), tickfont=dict(size=10, color=INK_SOFT), row=3, col=1
)

# Spike lines for synchronized crosshair across all panels
fig.update_xaxes(
    showspikes=True, spikemode="across", spikesnap="cursor", spikethickness=1.5, spikecolor=INK_SOFT, spikedash="solid"
)
fig.update_yaxes(showspikes=True, spikethickness=1, spikecolor=INK_SOFT, spikedash="dot")

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
