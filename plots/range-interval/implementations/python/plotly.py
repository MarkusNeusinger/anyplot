""" anyplot.ai
range-interval: Range Interval Chart
Library: plotly 7.1.0 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-22
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

# Columns: set these to your table's column names
MONTH = "Month"  # role: category
TEMP_MIN = "Min temperature (°C)"  # role: min_value
TEMP_MAX = "Max temperature (°C)"  # role: max_value
TEMP = "Temperature (°C)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("ranges.csv")
np.random.seed(42)
base_temps = np.array([-2, 0, 5, 12, 18, 22, 25, 24, 19, 12, 5, 0])
df = pd.DataFrame(
    {
        MONTH: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        TEMP_MIN: [t - np.random.uniform(3, 6) for t in base_temps],
        TEMP_MAX: [t + np.random.uniform(4, 8) for t in base_temps],
    }
)

# Plot: reads only df and the constants above
months = df[MONTH].tolist()
midpoints = (df[TEMP_MIN] + df[TEMP_MAX]) / 2
brand, secondary = IMPRINT_PALETTE[0], IMPRINT_PALETTE[1]

fig = go.Figure()

# Range bars: one vertical segment per category from its minimum to its maximum
for month, low, high in zip(df[MONTH], df[TEMP_MIN], df[TEMP_MAX], strict=True):
    fig.add_trace(
        go.Scatter(
            x=[month, month],
            y=[low, high],
            mode="lines",
            line={"color": brand, "width": 9},
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Endpoint markers on the two bounds
for column, label in ((TEMP_MIN, "Min Temperature"), (TEMP_MAX, "Max Temperature")):
    fig.add_trace(
        go.Scatter(
            x=months,
            y=df[column],
            mode="markers",
            marker={"color": secondary, "size": 9, "line": {"color": brand, "width": 1.5}},
            name=label,
            hovertemplate=f"%{{x}}<br>{label}: %{{y:.1f}}°C<extra></extra>",
        )
    )

# Midpoint markers, kept small so the ranges stay dominant
fig.add_trace(
    go.Scatter(
        x=months,
        y=midpoints,
        mode="markers",
        marker={"color": INK, "size": 5, "line": {"color": brand, "width": 1}},
        name="Midpoint",
        hovertemplate="%{x}<br>Mid: %{y:.1f}°C<extra></extra>",
    )
)

# Style
fig.update_layout(
    autosize=False,
    title={
        "text": "range-interval · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": MONTH, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "categoryorder": "array",
        "categoryarray": months,
        "showgrid": False,
        "linecolor": INK_SOFT,
        "linewidth": 1,
    },
    yaxis={
        "title": {"text": TEMP, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": True,
        "zerolinecolor": INK_SOFT,
        "zerolinewidth": 1,
        "linecolor": INK_SOFT,
        "linewidth": 1,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "font": {"size": 10, "color": INK_SOFT},
        "x": 0.02,
        "y": 0.98,
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    margin={"l": 80, "r": 40, "t": 60, "b": 60},
    hovermode="closest",
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
