"""anyplot.ai
line-annotated-events: Annotated Line Plot with Event Markers
Library: plotly 6.7.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-16
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

# Imprint palette: position 1 for the data line, position 2 for the event markers
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
PRICE = "Stock Price (USD)"  # role: value
EVENT_DATE = "Event date"  # role: event_date
EVENT = "Event"  # role: event_label

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
# One row per trading day; the event columns are filled on an event's day and empty otherwise
np.random.seed(42)
dates = pd.date_range("2024-01-01", periods=252, freq="B")
returns = np.random.normal(0.0005, 0.015, len(dates))
events = {
    "2024-01-25": "Q4 Earnings",
    "2024-03-15": "Product Launch",
    "2024-04-24": "Q1 Earnings",
    "2024-06-10": "Expansion Announced",
    "2024-07-25": "Q2 Earnings",
    "2024-09-20": "Partnership Deal",
    "2024-10-24": "Q3 Earnings",
}
df = pd.DataFrame({DATE: dates, PRICE: 100 * np.exp(np.cumsum(returns))})
df[EVENT] = df[DATE].dt.strftime("%Y-%m-%d").map(events)
df[EVENT_DATE] = df[DATE].where(df[EVENT].notna())

# Plot: reads only df and the constants above
df = df.sort_values(DATE)
marked = df[df[EVENT_DATE].notna() & df[EVENT].notna()]

# Headroom above the series holds the event labels, so they never cover the line
low, high = df[PRICE].min(), df[PRICE].max()
span = (high - low) or abs(high) or 1.0
y_bottom = low - span * 0.05
y_top = y_bottom + (high - y_bottom) / 0.70
label_heights = [0.93, 0.83]  # paper fractions, alternated so neighbouring labels stay apart
event_color = IMPRINT_PALETTE[1]

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=df[DATE],
        y=df[PRICE],
        mode="lines",
        name=PRICE,
        line={"color": IMPRINT_PALETTE[0], "width": 2.5},
        hovertemplate=f"{DATE}: %{{x|%Y-%m-%d}}<br>{PRICE}: %{{y:.2f}}<extra></extra>",
    )
)

for i, (event_date, label) in enumerate(zip(marked[EVENT_DATE], marked[EVENT], strict=True)):
    label_y = label_heights[i % len(label_heights)]
    fig.add_shape(
        type="line",
        x0=event_date,
        x1=event_date,
        xref="x",
        y0=0,
        y1=label_y - 0.03,
        yref="paper",
        line={"color": event_color, "width": 1.2, "dash": "dash"},
        opacity=0.75,
        layer="below",
    )
    fig.add_annotation(
        x=event_date,
        y=label_y,
        xref="x",
        yref="paper",
        text=str(label),
        showarrow=False,
        font={"size": 10, "color": INK},
        bgcolor=ELEVATED_BG,
        bordercolor=event_color,
        borderwidth=1.5,
        borderpad=4,
    )

fig.add_trace(
    go.Scatter(
        x=marked[EVENT_DATE],
        y=marked[PRICE],
        mode="markers",
        name=EVENT,
        text=marked[EVENT].astype(str),
        marker={"size": 11, "color": event_color, "symbol": "diamond", "line": {"color": PAGE_BG, "width": 1.5}},
        hovertemplate=f"%{{text}}<br>{DATE}: %{{x|%Y-%m-%d}}<br>{PRICE}: %{{y:.2f}}<extra></extra>",
    )
)

title = "line-annotated-events · python · plotly · anyplot.ai"
title_size = max(11, round(16 * (67 / len(title) if len(title) > 67 else 1.0)))

fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
    title={"text": title, "font": {"size": title_size, "color": INK}, "x": 0.5, "xanchor": "center"},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    xaxis={
        "title": {"text": DATE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": False,
        "showline": True,
        "linecolor": INK_SOFT,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": PRICE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "range": [y_bottom, y_top],
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "showline": True,
        "linecolor": INK_SOFT,
        "zeroline": False,
    },
    showlegend=True,
    legend={
        "orientation": "h",
        "x": 1.0,
        "xanchor": "right",
        "y": 1.02,
        "yanchor": "bottom",
        "font": {"size": 10, "color": INK_SOFT},
        "bgcolor": "rgba(0,0,0,0)",
    },
    hoverlabel={"bgcolor": ELEVATED_BG, "font": {"color": INK}},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
