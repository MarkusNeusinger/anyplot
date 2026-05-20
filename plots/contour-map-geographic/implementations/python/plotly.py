"""anyplot.ai
contour-map-geographic: Contour Lines on Geographic Map
Library: plotly | Python 3.13
Quality: 91/100 | Created: 2026-01-17
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

# Data - Simulated surface temperature over North Atlantic region
np.random.seed(42)

lat_range = np.linspace(30, 60, 50)
lon_range = np.linspace(-60, 0, 50)
lon_grid, lat_grid = np.meshgrid(lon_range, lat_range)

base_temp = 20 - 0.5 * (lat_grid - 30)
gulf_stream = 3 * np.exp(-((lon_grid + 30) ** 2) / 400)
variation = 2 * np.sin(lat_grid / 5) * np.cos(lon_grid / 8)
temperature = base_temp + gulf_stream + variation

# Plot
fig = go.Figure()

fig.add_trace(
    go.Contour(
        x=lon_range,
        y=lat_range,
        z=temperature,
        contours={"start": 0, "end": 22, "size": 2, "showlabels": True, "labelfont": {"size": 10, "color": "white"}},
        colorscale="RdYlBu_r",
        colorbar={
            "title": {"text": "Temperature (°C)", "font": {"size": 12, "color": INK}},
            "tickfont": {"size": 10, "color": INK_SOFT},
            "len": 0.75,
            "thickness": 20,
            "bgcolor": ELEVATED_BG,
            "bordercolor": INK_SOFT,
            "borderwidth": 1,
        },
        line={"width": 1.5, "color": "rgba(50,50,50,0.4)"},
        hovertemplate="Lat: %{y:.1f}°N<br>Lon: %{x:.1f}°<br>Temp: %{z:.1f}°C<extra></extra>",
    )
)

# Style
fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    title={
        "text": "North Atlantic SST · contour-map-geographic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Longitude", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "ticksuffix": "°",
        "dtick": 10,
        "showgrid": True,
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zeroline": False,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Latitude", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "ticksuffix": "°N",
        "dtick": 5,
        "showgrid": True,
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zeroline": False,
        "zerolinecolor": INK_SOFT,
        "scaleanchor": "x",
        "scaleratio": 1,
    },
    font={"color": INK},
    margin={"l": 80, "r": 120, "t": 80, "b": 60},
    annotations=[
        {"x": -50, "y": 47, "text": "Newfoundland", "showarrow": False, "font": {"size": 10, "color": INK_SOFT}},
        {"x": -10, "y": 50, "text": "Ireland", "showarrow": False, "font": {"size": 10, "color": INK_SOFT}},
        {"x": -20, "y": 37, "text": "Azores", "showarrow": False, "font": {"size": 10, "color": INK_SOFT}},
    ],
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
