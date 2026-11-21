"""anyplot.ai
polar-bar: Polar Bar Chart (Wind Rose)
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-13
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

# Imprint palette: all eight positions, one per speed bin in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DIRECTION = "Wind direction"  # role: direction
SPEED_BIN = "Wind speed (km/h)"  # role: extra
FREQUENCY = "Frequency (% of hours)"  # role: frequency

# Data: replace this block with your own table, for example df = pd.read_csv("wind.csv")
# Mountain-valley site: winds blow mostly from the north-east, with a weaker afternoon sea breeze from the south-west
rng = np.random.default_rng(42)
directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
speed_bins = ["0-5", "5-12", "12-20", "20+"]
bearing = np.arange(16) * 22.5
prevailing = np.exp(2.2 * np.cos(np.radians(bearing - 45))) + 0.35 * np.exp(1.8 * np.cos(np.radians(bearing - 225)))
direction_share = prevailing / prevailing.sum() * 100
bin_share = np.array([0.34, 0.38, 0.22, 0.06])
# Strong winds concentrate in the prevailing direction
strong_tilt = np.outer(prevailing / prevailing.max(), [-0.25, -0.05, 0.15, 0.45])
weights = bin_share * np.exp(strong_tilt)
weights = weights / weights.sum(axis=1, keepdims=True)
freq = direction_share[:, None] * weights * rng.normal(1.0, 0.04, size=weights.shape)
df = pd.DataFrame(
    {
        DIRECTION: np.repeat(directions, len(speed_bins)),
        SPEED_BIN: speed_bins * len(directions),
        FREQUENCY: freq.round(2).ravel(),
    }
)

# Plot: reads only df and the constants above
table = df.pivot_table(index=DIRECTION, columns=SPEED_BIN, values=FREQUENCY, sort=False)
top = table.sum(axis=1).max()

fig = go.Figure()
for i, speed in enumerate(table.columns):
    fig.add_trace(
        go.Barpolar(
            r=table[speed],
            theta=table.index,
            name=f"{speed} km/h",
            marker=dict(color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)], line=dict(color=PAGE_BG, width=1.5)),
            hovertemplate="<b>%{theta}</b><br>" + f"{speed} km/h" + "<br>Frequency: %{r:.2f}%<extra></extra>",
        )
    )

# Style
fig.update_layout(
    autosize=False,
    width=600,
    height=600,
    title=dict(text="polar-bar · python · plotly · anyplot.ai", font=dict(size=17, color=INK), x=0.5, xanchor="center"),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    polar=dict(
        domain=dict(x=[0.0, 0.82], y=[0.0, 0.9]),
        bgcolor=PAGE_BG,
        barmode="stack",
        bargap=0.04,
        radialaxis=dict(
            range=[0, top * 1.05],
            angle=-11,
            tickangle=0,
            ticksuffix="%",
            tickfont=dict(size=11, color=INK_SOFT),
            gridcolor=GRID,
            linecolor=INK_SOFT,
            showline=False,
        ),
        angularaxis=dict(
            tickfont=dict(size=12, color=INK), direction="clockwise", rotation=90, gridcolor=GRID, linecolor=INK_SOFT
        ),
    ),
    legend=dict(
        title=dict(text=SPEED_BIN, font=dict(size=12, color=INK)),
        font=dict(size=12, color=INK_SOFT),
        x=0.85,
        y=0.5,
        xanchor="left",
        yanchor="middle",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    margin=dict(l=30, r=20, t=70, b=30),
)

fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
