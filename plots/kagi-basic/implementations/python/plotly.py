""" anyplot.ai
kagi-basic: Basic Kagi Chart
Library: plotly 7.1.0 | Python 3.14.10
Quality: 78/100 | Updated: 2026-11-22
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
YANG_COLOR = IMPRINT_PALETTE[0]  # green: yang (bullish)
YIN_COLOR = IMPRINT_PALETTE[4]  # red: yin (bearish)

# Constants
REVERSAL_PCT = 0.03  # a move of 3% against the current line starts a new column

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Close price ($)"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
# (target move, volatility, steps) per swing, relative to the previous end
swings = [
    (15, 0.4, 15),
    (-20, 0.5, 18),
    (10, 0.4, 12),
    (-18, 0.5, 15),
    (35, 0.5, 20),
    (-15, 0.4, 12),
    (-22, 0.5, 18),
    (25, 0.4, 15),
    (20, 0.5, 15),
    (-18, 0.4, 12),
    (-30, 0.5, 20),
    (35, 0.5, 18),
    (25, 0.5, 15),
    (-20, 0.4, 12),
    (-35, 0.5, 20),
    (40, 0.5, 18),
    (25, 0.5, 15),
    (-22, 0.4, 15),
    (-45, 0.5, 22),
    (30, 0.5, 15),
    (20, 0.5, 12),
]
closes = [100.0]
for target_move, vol, n_steps in swings:
    noise = np.cumsum(np.random.normal(0, vol, n_steps))
    noise = noise - noise[-1] * np.linspace(0, 1, n_steps)  # pull the noise back to the target
    closes.extend((closes[-1] + np.linspace(0, target_move, n_steps) + noise).tolist())
df = pd.DataFrame({DATE: pd.bdate_range("2024-01-02", periods=len(closes)), CLOSE: closes})

# Plot: reads only df and the constants above
prices = df[CLOSE].dropna().to_numpy()

# Build the Kagi line: (x, y, is_yang) points; each reversal adds a horizontal connector
# at the old extreme and starts a new vertical column
points = [(0, prices[0], True)]
shoulders, waists = [], []  # (x, y) of the connectors where the line turned down / up
direction = 1
high = low = prices[0]
prev_shoulder = prev_waist = prices[0]
column = 0
is_yang = True

for price in prices[1:]:
    if direction == 1:
        if price > high:
            high = price
            if price > prev_shoulder:
                is_yang = True  # broke above the previous shoulder
            points[-1] = (column, price, is_yang)
        elif price <= high * (1 - REVERSAL_PCT):
            prev_shoulder = high
            column += 1
            shoulders.append((column, high))
            points.append((column, high, is_yang))
            points.append((column, price, is_yang))
            direction = -1
            low = price
    else:
        if price < low:
            low = price
            if price < prev_waist:
                is_yang = False  # broke below the previous waist
            points[-1] = (column, price, is_yang)
        elif price >= low * (1 + REVERSAL_PCT):
            prev_waist = low
            column += 1
            waists.append((column, low))
            points.append((column, low, is_yang))
            points.append((column, price, is_yang))
            direction = 1
            high = price

fig = go.Figure()

# Yang segments are thick, yin segments thin; each segment takes the state of its first point
for (x0, y0, yang), (x1, y1, _) in zip(points[:-1], points[1:], strict=True):
    fig.add_trace(
        go.Scatter(
            x=[x0, x1],
            y=[y0, y1],
            mode="lines",
            line={"color": YANG_COLOR if yang else YIN_COLOR, "width": 7.5 if yang else 1.5},
            showlegend=False,
            hovertemplate=f"<b>{'Yang (rising)' if yang else 'Yin (falling)'}</b><br>Price: $%{{y:.2f}}<extra></extra>",
        )
    )

# Shoulders (turn down) and waists (turn up)
for label, symbol, color, marks in (
    ("Shoulder", "triangle-down", YANG_COLOR, shoulders),
    ("Waist", "triangle-up", YIN_COLOR, waists),
):
    if marks:
        fig.add_trace(
            go.Scatter(
                x=[m[0] for m in marks],
                y=[m[1] for m in marks],
                mode="markers",
                marker={"symbol": symbol, "size": 9, "color": color, "line": {"width": 1.5, "color": PAGE_BG}},
                name=label,
                hovertemplate=f"<b>{label}</b><br>Price: $%{{y:.2f}}<extra></extra>",
            )
        )

# Legend entries for the two line weights
fig.add_trace(
    go.Scatter(x=[None], y=[None], mode="lines", line={"color": YANG_COLOR, "width": 7.5}, name="Yang (rising)")
)
fig.add_trace(
    go.Scatter(x=[None], y=[None], mode="lines", line={"color": YIN_COLOR, "width": 1.5}, name="Yin (falling)")
)

# Style
axis_style = {
    "tickfont": {"size": 10, "color": INK_SOFT},
    "showgrid": True,
    "gridwidth": 1,
    "gridcolor": GRID,
    "linecolor": INK_SOFT,
    "zerolinecolor": INK_SOFT,
}
fig.update_layout(
    autosize=False,
    title={
        "text": "kagi-basic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={"title": {"text": "Line index", "font": {"size": 12, "color": INK}}, **axis_style},
    yaxis={"title": {"text": CLOSE, "font": {"size": 12, "color": INK}}, **axis_style},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    legend={
        "font": {"size": 10, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.01,
        "xanchor": "center",
        "x": 0.5,
    },
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
    hovermode="x unified",
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
