"""anyplot.ai
stock-event-flags: Stock Chart with Event Flags
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-27
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
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
EVENT_SYMBOLS = ["star", "diamond", "triangle-up", "square", "circle", "cross", "hexagon", "pentagon"]
FLAG_HEIGHTS = [0.07, 0.14, 0.10, 0.17, 0.11, 0.15, 0.08]  # share of the price range, cycled over the flags

# Columns: set these to your table's column names
DATE = "Date"  # role: date
OPEN = "Open ($)"  # role: open
HIGH = "High ($)"  # role: high
LOW = "Low ($)"  # role: low
CLOSE = "Price ($)"  # role: close
EVENT_DATE = "Event date"  # role: event_date
EVENT_TYPE = "Event type"  # role: event_type
EVENT_LABEL = "Event label"  # role: event_label

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
# One row per trading day; the three event columns are filled on the days an event falls on.
np.random.seed(42)
n_days = 180
dates = pd.date_range(start="2024-01-02", periods=n_days, freq="B")

initial_price = 150.0
returns = np.random.randn(n_days) * 0.02
close_prices = initial_price * np.exp(np.cumsum(returns))
high_prices = close_prices * (1 + np.abs(np.random.randn(n_days)) * 0.015)
low_prices = close_prices * (1 - np.abs(np.random.randn(n_days)) * 0.015)
open_prices = np.roll(close_prices, 1)
open_prices[0] = initial_price

high_prices = np.maximum(high_prices, np.maximum(open_prices, close_prices))
low_prices = np.minimum(low_prices, np.minimum(open_prices, close_prices))

sample_events = {
    "2024-01-25": ("Earnings", "Q4 Beat"),
    "2024-03-15": ("Dividend", "Div $0.50"),
    "2024-04-18": ("News", "Product Launch"),
    "2024-05-10": ("Earnings", "Q1 Miss"),
    "2024-06-07": ("Split", "4:1 Split"),
    "2024-07-18": ("Dividend", "Div $0.55"),
    "2024-08-22": ("Earnings", "Q2 Beat"),
}
event_rows = {
    int(np.abs(dates - pd.Timestamp(day)).argmin()): info for day, info in sample_events.items()
}  # closest trading day

df = pd.DataFrame(
    {
        DATE: dates,
        OPEN: open_prices,
        HIGH: high_prices,
        LOW: low_prices,
        CLOSE: close_prices,
        EVENT_DATE: [dates[i] if i in event_rows else pd.NaT for i in range(n_days)],
        EVENT_TYPE: [event_rows[i][0] if i in event_rows else None for i in range(n_days)],
        EVENT_LABEL: [event_rows[i][1] if i in event_rows else None for i in range(n_days)],
    }
)

# Plot
events = df[df[EVENT_TYPE].notna()]
event_types = list(dict.fromkeys(events[EVENT_TYPE]))
event_colors = {
    t: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, t in enumerate(event_types)
}  # Imprint positions in order of appearance
event_symbols = {t: EVENT_SYMBOLS[i % len(EVENT_SYMBOLS)] for i, t in enumerate(event_types)}

fig = go.Figure()

# Candlestick — semantic colors: green=bullish, red=bearish
fig.add_trace(
    go.Candlestick(
        x=df[DATE],
        open=df[OPEN],
        high=df[HIGH],
        low=df[LOW],
        close=df[CLOSE],
        name="Price",
        increasing_line_color="#009E73",
        decreasing_line_color="#AE3030",
        increasing_fillcolor="#009E73",
        decreasing_fillcolor="#AE3030",
        line_width=1.5,
        showlegend=False,
    )
)

# Event flags with alternating heights to reduce visual clustering
price_range = df[HIGH].max() - df[LOW].min()

for i, (_, event) in enumerate(events.iterrows()):
    event_day = event[DATE]
    price_at_event = event[HIGH]
    flag_y = price_at_event + price_range * FLAG_HEIGHTS[i % len(FLAG_HEIGHTS)]
    color = event_colors[event[EVENT_TYPE]]
    symbol = event_symbols[event[EVENT_TYPE]]

    # Vertical dashed connector line
    fig.add_trace(
        go.Scatter(
            x=[event_day, event_day],
            y=[price_at_event, flag_y],
            mode="lines",
            line={"color": color, "width": 1.5, "dash": "dash"},
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # Flag marker with label
    fig.add_trace(
        go.Scatter(
            x=[event_day],
            y=[flag_y],
            mode="markers+text",
            marker={"size": 18, "color": color, "symbol": symbol, "line": {"color": PAGE_BG, "width": 2}},
            text=[event[EVENT_LABEL]],
            textposition="top center",
            textfont={"size": 11, "color": color, "family": "Arial Black"},
            name=event[EVENT_TYPE],
            showlegend=False,
            hovertemplate=(
                f"<b>{event[EVENT_TYPE]}</b><br>{event[EVENT_LABEL]}<br>{DATE}: %{{x|%Y-%m-%d}}<extra></extra>"
            ),
        )
    )

# Legend entries for event types only — no redundant Price entry
for event_type in event_types:
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker={"size": 14, "color": event_colors[event_type], "symbol": event_symbols[event_type]},
            name=event_type,
        )
    )

title = "stock-event-flags · python · plotly · anyplot.ai"

fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    title={"text": title, "font": {"size": 16, "color": INK}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": DATE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "rangeslider": {"visible": False},
        "gridcolor": GRID,
        "showgrid": True,
        "showline": True,
        "mirror": False,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": CLOSE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickformat": "$.0f",
        "gridcolor": GRID,
        "showgrid": True,
        "showline": True,
        "mirror": False,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    legend={
        "yanchor": "top",
        "y": 0.99,
        "xanchor": "right",
        "x": 0.99,
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "font": {"size": 10, "color": INK_SOFT},
    },
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
    hovermode="x unified",
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
