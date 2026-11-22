"""anyplot.ai
area-stacked-confidence: Stacked Area Chart with Confidence Bands
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-18
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
GRID = "rgba(26, 26, 23, 0.10)" if THEME == "light" else "rgba(240, 239, 232, 0.10)"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
QUARTER = "Quarter"  # role: x
ENERGY = ["Hydro", "Wind", "Solar"]  # role: y
LOWER = ["Hydro lower", "Wind lower", "Solar lower"]  # role: y_lower
UPPER = ["Hydro upper", "Wind upper", "Solar upper"]  # role: y_upper
SERIES = "Source"  # role: category
ENERGY_UNIT = "Energy consumption (TWh)"

# Data: replace this block with your own table, for example df = pd.read_csv("energy.csv")
np.random.seed(42)
quarters = [d.strftime("%Y-%m-%d") for d in pd.date_range("2020-01-01", periods=20, freq="QE")]
n = len(quarters)
growth = np.linspace(1, 2.5, n)  # forecast uncertainty widens over time
trends = [(100, 110, 3, 8), (80, 150, 8, 15), (50, 120, 5, 10)]  # start, end, noise, band half-width
values = [np.linspace(start, end, n) + np.random.randn(n) * noise for start, end, noise, _ in trends]
df = pd.DataFrame(
    {QUARTER: quarters}
    | dict(zip(ENERGY, values))
    | {col: v - trend[3] * growth for col, v, trend in zip(LOWER, values, trends)}
    | {col: v + trend[3] * growth for col, v, trend in zip(UPPER, values, trends)}
)

# Plot: reads only df and the constants above
x = list(df[QUARTER])
central = df[ENERGY]
lower = df[LOWER].set_axis(ENERGY, axis=1)
upper = df[UPPER].set_axis(ENERGY, axis=1)

# Stack the central values and both bounds in the same order
edge = central.cumsum(axis=1)
band_low = lower.cumsum(axis=1)
band_high = upper.cumsum(axis=1)


def rgba(hex_color, alpha):
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r}, {g}, {b}, {alpha})"


fig = go.Figure()
for i, name in enumerate(central.columns):
    color = IMPRINT_PALETTE[i]
    # Confidence band around the stacked edge
    fig.add_trace(
        go.Scatter(
            x=x + x[::-1],
            y=list(band_high[name]) + list(band_low[name][::-1]),
            fill="toself",
            fillcolor=rgba(color, 0.25),
            line=dict(width=0),
            name=f"{name} band",
            legendgroup=name,
            hoverinfo="skip",
        )
    )
    # Layer between the edge below and this edge
    fig.add_trace(
        go.Scatter(
            x=x,
            y=edge[name],
            mode="lines",
            line=dict(color=color, width=2),
            fill="tozeroy" if i == 0 else "tonexty",
            fillcolor=rgba(color, 0.6),
            name=name,
            legendgroup=name,
        )
    )

fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    margin=dict(l=80, r=150, t=60, b=60),
    title=dict(
        text="area-stacked-confidence · python · plotly · anyplot.ai",
        font=dict(size=16, color=INK),
        x=0.5,
        xanchor="center",
    ),
    xaxis=dict(
        title=dict(text=QUARTER, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        showgrid=False,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text=ENERGY_UNIT, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        showgrid=True,
        gridwidth=1,
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
        range=[0, np.nanmax(band_high.to_numpy()) * 1.05],
    ),
    legend=dict(
        font=dict(size=9, color=INK_SOFT),
        title=dict(text=f"{SERIES} (band = lower<br>to upper bound)", font=dict(size=9, color=INK_SOFT)),
        x=1.01,
        xanchor="left",
        y=1,
        yanchor="top",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    hovermode="x unified",
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
