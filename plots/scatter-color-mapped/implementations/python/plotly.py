""" anyplot.ai
scatter-color-mapped: Color-Mapped Scatter Plot
Library: plotly 7.1.0 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-09
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

# Imprint palette and its sequential colormap (single-polarity continuous data)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
imprint_seq = [[0.0, "#009E73"], [1.0, "#4467A3"]]

# Columns: set these to your table's column names
LONGITUDE = "Longitude (°)"  # role: x
LATITUDE = "Latitude (°N)"  # role: y
TEMPERATURE = "Temperature (°F)"  # role: color

# Data: replace this block with your own table, for example df = pd.read_csv("stations.csv")
# Temperature readings across geographic coordinates, cooler north, warmer south
np.random.seed(42)
n_points = 150
longitude = np.random.uniform(-120, -70, n_points)
latitude = np.random.uniform(25, 50, n_points)
temperature = 40 - 0.6 * (latitude - 25) + np.random.randn(n_points) * 5
df = pd.DataFrame({LONGITUDE: longitude, LATITUDE: latitude, TEMPERATURE: temperature})

# Plot: reads only df and the constants above
title = "scatter-color-mapped · python · plotly · anyplot.ai"
title_size = round(16 * (67 / len(title) if len(title) > 67 else 1.0))

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=df[LONGITUDE],
        y=df[LATITUDE],
        mode="markers",
        marker={
            "size": 10,
            "color": df[TEMPERATURE],
            "colorscale": imprint_seq,
            "reversescale": True,
            "cmin": df[TEMPERATURE].min(),
            "cmax": df[TEMPERATURE].max(),
            "colorbar": {
                "title": {"text": TEMPERATURE, "font": {"size": 12, "color": INK}, "side": "right"},
                "tickfont": {"size": 10, "color": INK_SOFT},
                "thickness": 14,
                "len": 0.85,
                "outlinewidth": 0,
            },
            "opacity": 0.85,
            "line": {"width": 0.8, "color": INK_SOFT},
        },
        hovertemplate=(
            f"{LONGITUDE}: %{{x:.1f}}<br>{LATITUDE}: %{{y:.1f}}<br>{TEMPERATURE}: %{{marker.color:.1f}}<extra></extra>"
        ),
    )
)

fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
    title={"text": title, "font": {"size": title_size, "color": INK}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": LONGITUDE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zeroline": False,
        "showline": True,
    },
    yaxis={
        "title": {"text": LATITUDE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zeroline": False,
        "showline": True,
    },
    template="plotly_white",
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    hoverlabel={"bgcolor": ELEVATED_BG, "font": {"color": INK}},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
