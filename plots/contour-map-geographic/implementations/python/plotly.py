"""anyplot.ai
contour-map-geographic: Contour Lines on Geographic Map
Library: plotly 7.1.0 | Python 3.14.10
Quality: 78/100 | Updated: 2026-11-26
"""

import os
import re
import sys


# Remove the script's own directory from sys.path so the sibling matplotlib.py
# implementation file does not shadow the system matplotlib package.
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if p and os.path.abspath(p) != _here]

import matplotlib


matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
from plotly.colors import sample_colorscale


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
LAND_COLOR = "#D8D3BB" if THEME == "light" else "#2A2A25"
OCEAN_BG = "#C5D8E8" if THEME == "light" else "#19242E"
COAST_COLOR = "#888880" if THEME == "light" else "#666660"

FIELD_ALPHA = 0.55  # translucent bands keep the coastlines beneath legible

# Imprint sequential ramp for filled fields (colored cells fill the plot)
SEQ_FIELDS = (
    [[0.0, "#66E2B2"], [0.368, "#009E73"], [0.582, "#4467A3"], [1.0, "#002850"]]
    if THEME == "light"
    else [[0.0, "#00573D"], [0.467, "#009E73"], [1.0, "#CDD9FF"]]
)

# Data - Simulated North Atlantic SST
np.random.seed(42)
lat_range = np.linspace(30, 60, 60)
lon_range = np.linspace(-60, 0, 60)
lon_grid, lat_grid = np.meshgrid(lon_range, lat_range)

base_temp = 20 - 0.5 * (lat_grid - 30)
gulf_stream = 3 * np.exp(-((lon_grid + 30) ** 2) / 400)
variation = 2 * np.sin(lat_grid / 5) * np.cos(lon_grid / 8)
temperature = base_temp + gulf_stream + variation

T_MIN, T_MAX = 4, 24
levels = np.arange(T_MIN, T_MAX + 1, 2)


# Compute contour paths using matplotlib off-screen (allsegs API, matplotlib 3.8+)
_fig, _ax = plt.subplots()
cs_fill = _ax.contourf(lon_range, lat_range, temperature, levels=levels)
cs_line = _ax.contour(lon_range, lat_range, temperature, levels=levels)
plt.close("all")

fig = go.Figure()

# Filled contour patches on the geographic map.
# Plotly's geo fill='toself' picks the interior from the ring's winding order,
# so every ring is normalised to clockwise (negative shoelace area).
for i, segs in enumerate(cs_fill.allsegs):
    mid_val = (levels[i] + levels[i + 1]) / 2
    fill_color = sample_colorscale(SEQ_FIELDS, [(mid_val - T_MIN) / (T_MAX - T_MIN)])[0]
    r, g, b = (int(v) for v in re.findall(r"\d+", fill_color)[:3])
    fill_color = f"rgba({r},{g},{b},{FIELD_ALPHA})"
    for seg in segs:
        if len(seg) < 3:
            continue
        x, y = seg[:, 0], seg[:, 1]
        signed_area = np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y) / 2
        seg = seg[::-1] if signed_area > 0 else seg
        fig.add_trace(
            go.Scattergeo(
                lon=seg[:, 0].tolist(),
                lat=seg[:, 1].tolist(),
                mode="lines",
                fill="toself",
                fillcolor=fill_color,
                line=dict(width=0),
                showlegend=False,
                hoverinfo="skip",
            )
        )

# Contour isolines as Scattergeo line traces
for i, segs in enumerate(cs_line.allsegs):
    level_val = float(cs_line.levels[i])
    for seg in segs:
        if len(seg) < 2:
            continue
        fig.add_trace(
            go.Scattergeo(
                lon=seg[:, 0].tolist(),
                lat=seg[:, 1].tolist(),
                mode="lines",
                line=dict(width=1.5, color=INK_SOFT),
                showlegend=False,
                hovertemplate=f"{level_val:.0f}°C<extra></extra>",
            )
        )

# Isoline value labels at midpoints of selected levels (every 4°C)
label_levels = {8.0, 12.0, 16.0, 20.0}
PLACES = [("Newfoundland", 48.5, -56.0), ("Ireland", 53.3, -8.0), ("Azores", 38.0, -28.0)]
label_lon, label_lat, label_text = [], [], []
for i, segs in enumerate(cs_line.allsegs):
    level_val = float(cs_line.levels[i])
    if level_val not in label_levels:
        continue
    for seg in segs:
        if len(seg) < 10:
            continue
        mid = len(seg) // 2
        label_lon.append(float(seg[mid, 0]))
        label_lat.append(float(seg[mid, 1]))
        label_text.append(f"{level_val:.0f}°C")


def add_haloed_text(lons, lats, texts, position):
    """Text with a page-colored halo (offset copies underneath) so lines never strike through it."""
    offsets = [(dx, dy) for dx in (-0.2, 0, 0.2) for dy in (-0.15, 0, 0.15) if (dx, dy) != (0, 0)]
    fig.add_trace(
        go.Scattergeo(
            lon=[x + dx for dx, _ in offsets for x in lons],
            lat=[y + dy for _, dy in offsets for y in lats],
            mode="text",
            text=texts * len(offsets),
            textposition=position,
            textfont=dict(size=12, color=ELEVATED_BG),
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scattergeo(
            lon=lons,
            lat=lats,
            mode="text",
            text=texts,
            textposition=position,
            textfont=dict(size=12, color=INK),
            showlegend=False,
            hoverinfo="skip",
        )
    )


add_haloed_text(label_lon, label_lat, label_text, "middle center")
# Place names at their own coordinates, set to the right of their dots
add_haloed_text([p[2] + 0.8 for p in PLACES], [p[1] for p in PLACES], [p[0] for p in PLACES], "middle right")
fig.add_trace(
    go.Scattergeo(
        lon=[p[2] for p in PLACES],
        lat=[p[1] for p in PLACES],
        mode="markers",
        marker=dict(size=7, color=INK, line=dict(width=1.5, color=ELEVATED_BG)),
        showlegend=False,
        hoverinfo="skip",
    )
)

# Dummy trace for standalone colorbar
fig.add_trace(
    go.Scattergeo(
        lon=[None],
        lat=[None],
        mode="markers",
        marker=dict(
            color=[0],
            colorscale=SEQ_FIELDS,
            cmin=T_MIN,
            cmax=T_MAX,
            showscale=True,
            colorbar=dict(
                title=dict(text="Temperature (°C)", font=dict(size=12, color=INK)),
                tickfont=dict(size=12, color=INK_SOFT),
                len=0.75,
                thickness=20,
                bgcolor=ELEVATED_BG,
                bordercolor=INK_SOFT,
                borderwidth=1,
                x=1.0,
            ),
        ),
        showlegend=False,
    )
)

# Native Plotly geographic basemap with Natural Earth coastlines and borders
fig.update_geos(
    projection_type="mercator",
    lataxis_range=[28, 62],
    lonaxis_range=[-72, 12],
    showcoastlines=True,
    coastlinecolor=COAST_COLOR,
    coastlinewidth=1.5,
    showland=True,
    landcolor=LAND_COLOR,
    showocean=True,
    oceancolor=OCEAN_BG,
    showlakes=True,
    lakecolor=OCEAN_BG,
    showcountries=True,
    countrycolor=COAST_COLOR,
    countrywidth=0.5,
    bgcolor=OCEAN_BG,
    showframe=True,
    framecolor=INK_SOFT,
    framewidth=1,
)

fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    title=dict(
        text="North Atlantic SST · contour-map-geographic · python · plotly · anyplot.ai",
        font=dict(size=16, color=INK),
        x=0.5,
        xanchor="center",
    ),
    font=dict(color=INK),
    margin=dict(l=20, r=110, t=50, b=20),
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
