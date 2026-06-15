""" anyplot.ai
depth-order-book: Order Book Depth Chart
Library: plotly 6.8.0 | Python 3.13.13
Quality: 90/100 | Created: 2026-06-15
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette — semantic: green=bid (buy/gain), red=ask (sell/loss)
BID_COLOR = "#009E73"  # Imprint position 1 — buy-side
ASK_COLOR = "#AE3030"  # Imprint matte-red semantic anchor — sell-side

# Data: BTC/USD synthetic order book snapshot
np.random.seed(42)
MID_PRICE = 60_000.0
SPREAD = 12.0
N_LEVELS = 50
TICK = 8.0

best_bid = MID_PRICE - SPREAD / 2  # 59994.0
best_ask = MID_PRICE + SPREAD / 2  # 60006.0

bid_prices = np.array([best_bid - i * TICK for i in range(N_LEVELS)])
ask_prices = np.array([best_ask + i * TICK for i in range(N_LEVELS)])

bid_qtys = np.random.exponential(0.4, N_LEVELS) + 0.04 * np.arange(N_LEVELS)
ask_qtys = np.random.exponential(0.4, N_LEVELS) + 0.04 * np.arange(N_LEVELS)

# Synthetic order walls: support ~$200 below mid, resistance ~$150 above
bid_qtys[25:27] += 7.5
ask_qtys[19:21] += 9.0

bid_cumulative = np.cumsum(bid_qtys)
ask_cumulative = np.cumsum(ask_qtys)

# Step-chart arrays — bids: ascending price (worst→best), descending cumulative
bid_x = bid_prices[::-1]
bid_y = bid_cumulative[::-1]
# asks: ascending price (best→worst), ascending cumulative
ask_x = ask_prices
ask_y = ask_cumulative

y_max = max(bid_cumulative[-1], ask_cumulative[-1]) * 1.10

# Wall coordinates for annotations
support_x = bid_prices[25]
support_y = bid_cumulative[25]
resist_x = ask_prices[19]
resist_y = ask_cumulative[19]

title = "BTC/USD Order Book · depth-order-book · python · plotly · anyplot.ai"

# Plot
fig = go.Figure()

# Bid area — green step fill
fig.add_trace(
    go.Scatter(
        x=bid_x,
        y=bid_y,
        name="Bid (Buy)",
        mode="lines",
        line=dict(color=BID_COLOR, width=2.5, shape="hv"),
        fill="tozeroy",
        fillcolor="rgba(0,158,115,0.18)",
    )
)

# Ask area — red step fill
fig.add_trace(
    go.Scatter(
        x=ask_x,
        y=ask_y,
        name="Ask (Sell)",
        mode="lines",
        line=dict(color=ASK_COLOR, width=2.5, shape="hv"),
        fill="tozeroy",
        fillcolor="rgba(174,48,48,0.18)",
    )
)

# Mid-price dashed vertical line
fig.add_shape(
    type="line", x0=MID_PRICE, y0=0, x1=MID_PRICE, y1=y_max, line=dict(color=INK_SOFT, width=1.5, dash="dash")
)

# Mid-price annotation box
fig.add_annotation(
    x=MID_PRICE,
    y=y_max * 0.92,
    text=f"Mid: {MID_PRICE:,.0f}  |  Spread: {SPREAD:.0f}",
    showarrow=False,
    font=dict(size=10, color=INK),
    align="center",
    bgcolor=ELEVATED_BG,
    bordercolor=INK_SOFT,
    borderwidth=1,
    borderpad=5,
)

# Support wall label
fig.add_annotation(
    x=support_x,
    y=support_y,
    text="Support Wall",
    showarrow=True,
    arrowhead=2,
    arrowcolor=BID_COLOR,
    arrowwidth=1.5,
    font=dict(size=9, color=BID_COLOR),
    ax=-55,
    ay=-35,
)

# Resistance wall label
fig.add_annotation(
    x=resist_x,
    y=resist_y,
    text="Resistance Wall",
    showarrow=True,
    arrowhead=2,
    arrowcolor=ASK_COLOR,
    arrowwidth=1.5,
    font=dict(size=9, color=ASK_COLOR),
    ax=55,
    ay=-35,
)

# Style
fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    title=dict(text=title, font=dict(size=16, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Price (USD)", font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        tickprefix="$",
        tickformat=",.0f",
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=GRID,
        showgrid=True,
        showline=True,
    ),
    yaxis=dict(
        title=dict(text="Cumulative Volume (BTC)", font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=GRID,
        showgrid=True,
        showline=True,
        range=[0, y_max],
    ),
    legend=dict(
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
        font=dict(size=10, color=INK_SOFT),
        x=0.01,
        y=0.99,
        xanchor="left",
        yanchor="top",
    ),
    margin=dict(l=80, r=40, t=80, b=60),
    hovermode="x unified",
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
