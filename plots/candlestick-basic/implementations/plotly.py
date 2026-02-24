""" pyplots.ai
candlestick-basic: Basic Candlestick Chart
Library: plotly 6.5.2 | Python 3.14.3
Quality: 95/100 | Updated: 2026-02-24
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data - 30 trading days of simulated stock prices
np.random.seed(42)
dates = pd.date_range(start="2024-01-02", periods=30, freq="B")

# Generate realistic price movement starting at $150 (rally, pullback, recovery)
price = 150.0
drift = [0.4] * 8 + [-0.5] * 12 + [0.35] * 10
opens, highs, lows, closes = [], [], [], []

for i in range(30):
    open_price = price
    change = np.random.randn() * 2.5 + drift[i]
    close_price = open_price + change

    high_price = max(open_price, close_price) + abs(np.random.randn()) * 1.8
    low_price = min(open_price, close_price) - abs(np.random.randn()) * 1.8

    opens.append(open_price)
    highs.append(high_price)
    lows.append(low_price)
    closes.append(close_price)

    price = close_price

df = pd.DataFrame({"date": dates, "open": opens, "high": highs, "low": lows, "close": closes})

# Identify rally peak and pullback low for annotations
peak_idx = df["high"].idxmax()
low_idx = df["low"].idxmin()

# Colorblind-safe palette: blue for bullish, warm red-orange for bearish
BULL_COLOR = "#306998"
BEAR_COLOR = "#C0392B"

# Create candlestick chart
fig = go.Figure(
    data=[
        go.Candlestick(
            x=df["date"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            increasing={"line": {"color": BULL_COLOR, "width": 2}, "fillcolor": BULL_COLOR},
            decreasing={"line": {"color": BEAR_COLOR, "width": 2}, "fillcolor": BEAR_COLOR},
            hovertemplate=(
                "<b>%{x|%b %d, %Y}</b><br>"
                "Open: $%{open:.2f}<br>"
                "High: $%{high:.2f}<br>"
                "Low: $%{low:.2f}<br>"
                "Close: $%{close:.2f}<br>"
                "<extra></extra>"
            ),
        )
    ]
)

# Annotations for data storytelling - mark the rally peak and pullback low
fig.add_annotation(
    x=df.loc[peak_idx, "date"],
    y=df.loc[peak_idx, "high"],
    text=f"Rally Peak<br>${df.loc[peak_idx, 'high']:.0f}",
    showarrow=True,
    arrowhead=0,
    arrowwidth=1.5,
    arrowcolor="#555",
    ax=40,
    ay=-45,
    font={"size": 15, "color": "#333", "family": "Arial"},
    bgcolor="rgba(255,255,255,0.85)",
    bordercolor="#999",
    borderwidth=1,
    borderpad=5,
)

fig.add_annotation(
    x=df.loc[low_idx, "date"],
    y=df.loc[low_idx, "low"],
    text=f"Pullback Low<br>${df.loc[low_idx, 'low']:.0f}",
    showarrow=True,
    arrowhead=0,
    arrowwidth=1.5,
    arrowcolor="#555",
    ax=-40,
    ay=50,
    font={"size": 15, "color": "#333", "family": "Arial"},
    bgcolor="rgba(255,255,255,0.85)",
    bordercolor="#999",
    borderwidth=1,
    borderpad=5,
)

# Subtle shaded regions to delineate market phases
fig.add_vrect(
    x0=dates[0],
    x1=dates[7],
    fillcolor=BULL_COLOR,
    opacity=0.04,
    line_width=0,
    annotation_text="Rally",
    annotation_position="top left",
    annotation_font={"size": 13, "color": "#888", "family": "Arial"},
)
fig.add_vrect(
    x0=dates[8],
    x1=dates[19],
    fillcolor=BEAR_COLOR,
    opacity=0.04,
    line_width=0,
    annotation_text="Pullback",
    annotation_position="top left",
    annotation_font={"size": 13, "color": "#888", "family": "Arial"},
)
fig.add_vrect(
    x0=dates[20],
    x1=dates[29],
    fillcolor=BULL_COLOR,
    opacity=0.04,
    line_width=0,
    annotation_text="Recovery",
    annotation_position="top left",
    annotation_font={"size": 13, "color": "#888", "family": "Arial"},
)

# Layout
fig.update_layout(
    title={
        "text": (
            "<b>ACME Corp Daily Prices</b>"
            "<br><span style='color:#777;font-size:15px;font-weight:normal'>"
            "candlestick-basic · plotly · pyplots.ai</span>"
        ),
        "font": {"size": 28, "color": "#222", "family": "Arial"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.95,
    },
    xaxis={
        "title": {"text": "Date", "font": {"size": 22, "color": "#444", "family": "Arial"}},
        "tickfont": {"size": 18, "color": "#555", "family": "Arial"},
        "tickformat": "%b %d",
        "rangeslider": {"visible": False},
        "rangebreaks": [{"bounds": ["sat", "mon"]}],
        "showgrid": False,
        "linecolor": "#ccc",
        "linewidth": 1,
    },
    yaxis={
        "title": {"text": "Price (USD)", "font": {"size": 22, "color": "#444", "family": "Arial"}},
        "tickfont": {"size": 18, "color": "#555", "family": "Arial"},
        "tickprefix": "$",
        "gridcolor": "rgba(180, 180, 180, 0.2)",
        "gridwidth": 1,
        "zeroline": False,
        "linecolor": "#ccc",
        "linewidth": 1,
    },
    template="plotly_white",
    plot_bgcolor="#FAFAFA",
    paper_bgcolor="white",
    margin={"l": 90, "r": 50, "t": 110, "b": 80},
    hoverlabel={"bgcolor": "white", "font_size": 14, "bordercolor": "#ccc"},
    font={"family": "Arial"},
)

# Save as PNG (4800x2700)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
