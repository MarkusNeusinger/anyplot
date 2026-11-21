""" anyplot.ai
line-styled: Styled Line Plot
Library: plotly 7.1.0 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-21
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

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
DASH_STYLES = ["solid", "dash", "dot", "dashdot"]  # standard line styles, assigned per series in order
LINE_WIDTH = 2.5  # one width for every style

# Columns: set these to your table's column names
HOUR = "Hour of day"  # role: x
SENSORS = ["Outdoor", "Indoor", "Greenhouse", "Storage"]  # role: y_

# Data: replace this block with your own table, for example df = pd.read_csv("sensors.csv")
np.random.seed(42)
hours = np.arange(0, 24)
sensor_a = 15 + 8 * np.sin((hours - 6) * np.pi / 12) + np.random.normal(0, 0.5, 24)
sensor_b = 20 + 3 * np.sin((hours - 8) * np.pi / 12) + np.random.normal(0, 0.3, 24)
sensor_c = 18 + 5 * np.sin((hours - 7) * np.pi / 12) + np.random.normal(0, 0.4, 24)
sensor_d = 22 + 2 * np.sin((hours - 10) * np.pi / 12) + np.random.normal(0, 0.2, 24)
df = pd.DataFrame({HOUR: hours, SENSORS[0]: sensor_a, SENSORS[1]: sensor_b, SENSORS[2]: sensor_c, SENSORS[3]: sensor_d})

# Plot: reads only df and the constants above
fig = go.Figure()
for i, sensor in enumerate(SENSORS):
    fig.add_trace(
        go.Scatter(
            x=df[HOUR],
            y=df[sensor],
            mode="lines",
            name=str(sensor),
            line=dict(
                dash=DASH_STYLES[i % len(DASH_STYLES)],
                width=LINE_WIDTH,
                color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
            ),
            hovertemplate=f"<b>{sensor}</b><br>{HOUR}: %{{x}}<br>%{{y:.1f}}<extra></extra>",
        )
    )

# Style
fig.update_layout(
    autosize=False,
    title=dict(
        text="line-styled · python · plotly · anyplot.ai", font=dict(size=16, color=INK), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text=HOUR, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        dtick=4,
        gridcolor=GRID,
        gridwidth=1,
        linecolor=INK_SOFT,
        zeroline=False,
        range=[df[HOUR].min() - 0.5, df[HOUR].max() + 0.5],
    ),
    yaxis=dict(
        title=dict(text="Temperature (°C)", font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        linecolor=INK_SOFT,
        zeroline=False,
    ),
    legend=dict(
        title=dict(text="Sensor", font=dict(size=10, color=INK)),
        font=dict(size=10, color=INK_SOFT),
        itemwidth=70,
        orientation="h",
        x=0.5,
        y=1.0,
        xanchor="center",
        yanchor="bottom",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    margin=dict(l=70, r=40, t=95, b=55),
    hovermode="x unified",
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
