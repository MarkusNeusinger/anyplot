"""anyplot.ai
contour-basic: Basic Contour Plot
Library: plotly 6.7.0 | Python 3.14.4
Quality: 85/100 | Updated: 2026-06-25
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens — Imprint palette chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint diverging colormap: matte-red (low) → PAGE_BG (zero) → blue (high)
midpoint = "#FAF8F1" if THEME == "light" else "#1A1A17"
imprint_div = [[0.0, "#AE3030"], [0.5, midpoint], [1.0, "#4467A3"]]

# Data — regional surface pressure anomaly (hPa deviation from 1013 hPa)
lon = np.linspace(-6, 6, 90)  # longitude offset (°E)
lat = np.linspace(-4, 4, 70)  # latitude offset (°N)
LON, LAT = np.meshgrid(lon, lat)

anticyclone = 14.0 * np.exp(-((LON + 2.5) ** 2 / 4.0 + LAT**2 / 2.5))
cyclone = -12.0 * np.exp(-((LON - 2.5) ** 2 / 3.5 + LAT**2 / 2.0))
pressure_anomaly = anticyclone + cyclone

# Title fontsize scaled by character count
title = "contour-basic · python · plotly · anyplot.ai"
title_fontsize = round(16 * (67 / len(title) if len(title) > 67 else 1.0))

# Plot
fig = go.Figure()

fig.add_trace(
    go.Contour(
        x=lon,
        y=lat,
        z=pressure_anomaly,
        colorscale=imprint_div,
        zmid=0,
        contours={
            "showlabels": True,
            "labelfont": {"size": 10, "color": INK},
            "coloring": "fill",
            "start": -14,
            "end": 14,
            "size": 2,
        },
        colorbar={
            "title": {"text": "Pressure Anomaly (hPa)", "font": {"size": 12, "color": INK}, "side": "right"},
            "tickfont": {"size": 10, "color": INK_SOFT},
            "thickness": 18,
            "len": 0.85,
            "bgcolor": ELEVATED_BG,
            "bordercolor": INK_SOFT,
            "borderwidth": 1,
        },
        line={"width": 1.5, "color": INK_SOFT},
    )
)

fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    title={"text": title, "font": {"size": title_fontsize, "color": INK}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Longitude Offset (°E)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": GRID,
    },
    yaxis={
        "title": {"text": "Latitude Offset (°N)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": GRID,
    },
    margin={"l": 80, "r": 100, "t": 80, "b": 60},
    font={"color": INK},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
