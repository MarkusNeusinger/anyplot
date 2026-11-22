"""anyplot.ai
renko-basic: Basic Renko Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-17
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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BULLISH = IMPRINT_PALETTE[0]  # green, position 1
BEARISH = IMPRINT_PALETTE[4]  # red, position 5

# Constants
BRICK_SIZE = 2.0  # price move that draws one brick

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Price (USD)"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 250
returns = np.random.randn(n_days) * 0.02  # 2% daily volatility
df = pd.DataFrame(
    {
        DATE: pd.date_range("2025-01-01", periods=n_days, freq="D"),
        CLOSE: 100 * np.exp(np.cumsum(returns)),  # geometric random walk from about $100
    }
)

# Plot: reads only df and the constants above
prices = df.sort_values(DATE)[CLOSE].dropna().to_numpy()
base_price = round(prices[0] / BRICK_SIZE) * BRICK_SIZE
opens, directions = [], []
for price in prices[1:]:
    diff = price - base_price
    for _ in range(int(abs(diff) // BRICK_SIZE)):
        direction = 1 if diff > 0 else -1
        opens.append(base_price)
        directions.append(direction)
        base_price += direction * BRICK_SIZE

bricks = pd.DataFrame({"open": opens, "direction": directions})
bricks["index"] = np.arange(len(bricks))
bricks["close"] = bricks["open"] + bricks["direction"] * BRICK_SIZE
bricks["low"] = bricks[["open", "close"]].min(axis=1)

fig = go.Figure()
for direction, label, color in [(1, "Bullish (up)", BULLISH), (-1, "Bearish (down)", BEARISH)]:
    rows = bricks[bricks["direction"] == direction]
    fig.add_trace(
        go.Bar(
            x=rows["index"],
            y=np.full(len(rows), BRICK_SIZE),
            base=rows["low"],
            width=0.84,
            name=label,
            marker=dict(color=color, line=dict(width=0)),
            customdata=np.column_stack([rows["open"], rows["close"]]),
            hovertemplate="Brick %{x}<br>Open: $%{customdata[0]:.2f}<br>Close: $%{customdata[1]:.2f}<extra></extra>",
        )
    )

fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    margin=dict(l=80, r=40, t=80, b=60),
    title=dict(
        text="renko-basic · python · plotly · anyplot.ai", font=dict(size=16, color=INK), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text="Brick index", font=dict(size=13, color=INK)),
        tickfont=dict(size=11, color=INK_SOFT),
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
        linecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text=f"{CLOSE} · brick = ${BRICK_SIZE:g}", font=dict(size=13, color=INK)),
        tickfont=dict(size=11, color=INK_SOFT),
        tickformat="$.0f",
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
        linecolor=INK_SOFT,
    ),
    plot_bgcolor=PAGE_BG,
    paper_bgcolor=PAGE_BG,
    font=dict(color=INK),
    legend=dict(
        font=dict(size=12, color=INK_SOFT),
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5,
    ),
    barmode="overlay",
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
