"""anyplot.ai
line-stepwise: Step Line Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-13
"""

import os

import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions, first series is always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
HOUR = "Hour of day"  # role: x
RESPONSE = "Response time (ms)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("response_times.csv")
# Server response time monitoring: the value holds until the next hourly reading
df = pd.DataFrame(
    {
        HOUR: list(range(24)),
        RESPONSE: [45, 45, 42, 42, 48, 55, 65, 72, 78, 82, 80, 75] + [85, 90, 88, 85, 78, 65, 55, 50, 48, 45, 44, 43],
    }
)

# Plot: reads only df and the constants above
fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=df[HOUR],
        y=df[RESPONSE],
        mode="lines+markers",
        line={"shape": "hv", "color": IMPRINT_PALETTE[0], "width": 3},
        marker={"size": 8, "color": IMPRINT_PALETTE[0], "line": {"color": PAGE_BG, "width": 1.5}},
        hovertemplate=f"{HOUR}: %{{x}}<br>{RESPONSE}: %{{y}}<extra></extra>",
    )
)

# Style
y_low, y_high = df[RESPONSE].min(), df[RESPONSE].max()
y_pad = (y_high - y_low) * 0.1
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    margin={"l": 70, "r": 40, "t": 70, "b": 60},
    title={
        "text": "line-stepwise · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": HOUR, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "dtick": 2,
        "range": [df[HOUR].min() - 0.5, df[HOUR].max() + 0.5],
        "showgrid": True,
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": RESPONSE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "range": [y_low - y_pad, y_high + y_pad],
        "showgrid": True,
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zeroline": False,
    },
    font={"color": INK},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    showlegend=False,
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
