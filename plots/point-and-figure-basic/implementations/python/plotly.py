"""anyplot.ai
point-and-figure-basic: Point and Figure Chart
Library: plotly | Python 3.13
Quality: 91/100 | Updated: 2026-05-20
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
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

COLOR_X = "#009E73"  # Okabe-Ito pos 1 — X (Rising), colorblind-safe
COLOR_O = "#D55E00"  # Okabe-Ito pos 2 — O (Falling), colorblind-safe

# Data — synthetic stock price with distinct trend phases
np.random.seed(42)
n_days = 300

initial_price = 100.0
returns = np.random.normal(0.001, 0.02, n_days)
returns[50:100] += 0.003
returns[120:150] -= 0.004
returns[180:230] += 0.002
returns[250:280] -= 0.003

close = initial_price * np.cumprod(1 + returns)

# P&F parameters
box_size = 2.0
reversal = 3

# Build P&F columns
columns = []
current_direction = None
current_column = []
column_index = 0
current_price = np.floor(close[0] / box_size) * box_size

for i in range(1, len(close)):
    price = close[i]

    if current_direction is None:
        price_boxes = np.floor(price / box_size) * box_size
        if price_boxes > current_price + box_size:
            current_direction = "X"
            for p in np.arange(current_price, price_boxes + box_size, box_size):
                current_column.append(p)
            current_price = price_boxes
        elif price_boxes < current_price - box_size:
            current_direction = "O"
            for p in np.arange(current_price, price_boxes - box_size, -box_size):
                current_column.append(p)
            current_price = price_boxes
    else:
        price_boxes = np.floor(price / box_size) * box_size

        if current_direction == "X":
            if price_boxes > current_price:
                for p in np.arange(current_price + box_size, price_boxes + box_size, box_size):
                    current_column.append(p)
                current_price = price_boxes
            elif price_boxes <= current_price - reversal * box_size:
                if current_column:
                    columns.append((current_column.copy(), "X", column_index))
                    column_index += 1
                current_direction = "O"
                current_column = []
                for p in np.arange(current_price - box_size, price_boxes - box_size, -box_size):
                    current_column.append(p)
                current_price = price_boxes
        else:
            if price_boxes < current_price:
                for p in np.arange(current_price - box_size, price_boxes - box_size, -box_size):
                    current_column.append(p)
                current_price = price_boxes
            elif price_boxes >= current_price + reversal * box_size:
                if current_column:
                    columns.append((current_column.copy(), "O", column_index))
                    column_index += 1
                current_direction = "X"
                current_column = []
                for p in np.arange(current_price + box_size, price_boxes + box_size, box_size):
                    current_column.append(p)
                current_price = price_boxes

if current_column:
    columns.append((current_column.copy(), current_direction, column_index))

# Plot
fig = go.Figure()

# X and O symbols for each column
for prices, direction, col_idx in columns:
    if not prices:
        continue
    color = COLOR_X if direction == "X" else COLOR_O
    symbol = "X" if direction == "X" else "O"
    label = "Rising" if direction == "X" else "Falling"
    fig.add_trace(
        go.Scatter(
            x=[col_idx] * len(prices),
            y=prices,
            mode="text",
            text=[symbol] * len(prices),
            textfont={"size": 11, "color": color, "family": "Arial Black"},
            showlegend=False,
            hovertemplate=f"Column: {col_idx}<br>Price: $%{{y:.0f}}<br>{label}<extra></extra>",
        )
    )

# Compute chart bounds
all_prices = [p for prices, _, _ in columns for p in prices]
min_price = min(all_prices) - box_size * 2 if all_prices else 80
max_price = max(all_prices) + box_size * 2 if all_prices else 140
max_col_idx = columns[-1][2] if columns else 0

# Support trend line: from O column with lowest minimum, ascending 45° (1 box per column)
o_bottoms = [(col_idx, min(prices)) for prices, direction, col_idx in columns if direction == "O" and prices]
if o_bottoms and max_col_idx > 0:
    support_col, support_price = min(o_bottoms, key=lambda t: t[1])
    if support_col < max_col_idx:
        fig.add_trace(
            go.Scatter(
                x=[support_col, max_col_idx],
                y=[support_price, support_price + (max_col_idx - support_col) * box_size],
                mode="lines",
                line={"color": INK_SOFT, "width": 1.5, "dash": "dash"},
                name="Support (45°)",
                showlegend=True,
            )
        )

# Resistance trend line: from X column with highest maximum, descending 45°
x_tops = [(col_idx, max(prices)) for prices, direction, col_idx in columns if direction == "X" and prices]
if x_tops and max_col_idx > 0:
    resist_col, resist_price = max(x_tops, key=lambda t: t[1])
    if resist_col < max_col_idx:
        fig.add_trace(
            go.Scatter(
                x=[resist_col, max_col_idx],
                y=[resist_price, resist_price - (max_col_idx - resist_col) * box_size],
                mode="lines",
                line={"color": INK_SOFT, "width": 1.5, "dash": "dot"},
                name="Resistance (45°)",
                showlegend=True,
            )
        )

# Legend entries — square markers avoid the text-mode legend rendering bug
fig.add_trace(
    go.Scatter(
        x=[None],
        y=[None],
        mode="markers",
        marker={"symbol": "square", "size": 12, "color": COLOR_X},
        name="X (Rising)",
        showlegend=True,
    )
)
fig.add_trace(
    go.Scatter(
        x=[None],
        y=[None],
        mode="markers",
        marker={"symbol": "square", "size": 12, "color": COLOR_O},
        name="O (Falling)",
        showlegend=True,
    )
)

# Style
fig.update_layout(
    title={
        "text": "point-and-figure-basic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Column (Reversal)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zeroline": False,
        "dtick": 5,
    },
    yaxis={
        "title": {"text": "Price ($)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "dtick": 10,
        "range": [min_price, max_price],
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "font": {"size": 10, "color": INK_SOFT},
        "x": 1.02,
        "y": 0.98,
        "xanchor": "left",
        "yanchor": "top",
    },
    margin={"l": 70, "r": 160, "t": 70, "b": 100},
)

fig.add_annotation(
    text=f"Box Size: ${box_size:.0f} | Reversal: {reversal} boxes",
    xref="paper",
    yref="paper",
    x=0.5,
    y=-0.13,
    showarrow=False,
    font={"size": 10, "color": INK_SOFT},
    xanchor="center",
)

# Save
fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
