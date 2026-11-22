""" anyplot.ai
heatmap-geographic: Geographic Heatmap for Spatial Density
Library: plotly 7.1.0 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-22
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
MAP_STYLE = "carto-positron" if THEME == "light" else "carto-darkmatter"

# Imprint palette: continuous single-polarity scale (green to blue)
IMPRINT_SEQ = [[0.0, "#009E73"], [1.0, "#4467A3"]]

# Columns: set these to your table's column names
LATITUDE = "Latitude"  # role: latitude
LONGITUDE = "Longitude"  # role: longitude
INTENSITY = "Trips per hour"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("trips.csv")
# Bike-share trip starts around Sydney: (lat, lon, spread in degrees, trips, mean intensity)
rng = np.random.default_rng(42)
hotspots = [
    (-33.869, 151.209, 0.020, 450, 0.85),  # CBD
    (-33.898, 151.179, 0.015, 280, 0.60),  # Newtown
    (-33.892, 151.277, 0.012, 220, 0.55),  # Bondi
    (-33.797, 151.284, 0.012, 180, 0.45),  # Manly
    (-33.815, 151.001, 0.020, 260, 0.50),  # Parramatta
]
parts = [
    pd.DataFrame(
        {
            LATITUDE: rng.normal(lat, spread, n),
            LONGITUDE: rng.normal(lon, spread * 1.2, n),
            INTENSITY: np.clip(rng.normal(level, 0.12, n), 0.05, 1.0),
        }
    )
    for lat, lon, spread, n, level in hotspots
]
parts.append(
    pd.DataFrame(
        {
            LATITUDE: rng.uniform(-34.0, -33.7, 200),
            LONGITUDE: rng.uniform(150.95, 151.35, 200),
            INTENSITY: rng.uniform(0.05, 0.3, 200),
        }
    )
)
df = pd.concat(parts, ignore_index=True)

# Plot
fig = go.Figure(
    go.Densitymap(
        lat=df[LATITUDE],
        lon=df[LONGITUDE],
        z=df[INTENSITY],
        radius=8,
        colorscale=IMPRINT_SEQ,
        opacity=0.75,
        colorbar={
            "title": {"text": INTENSITY, "font": {"size": 12, "color": INK}},
            "tickfont": {"size": 10, "color": INK_SOFT},
            "len": 0.6,
            "thickness": 14,
        },
        hovertemplate=f"{LATITUDE}: %{{lat:.4f}}<br>{LONGITUDE}: %{{lon:.4f}}<br>{INTENSITY}: %{{z:.2f}}<extra></extra>",
    )
)

fig.update_layout(
    autosize=False,
    title={
        "text": "Bike-Share Trip Density · heatmap-geographic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    map={"style": MAP_STYLE, "center": {"lat": df[LATITUDE].median(), "lon": df[LONGITUDE].median()}, "zoom": 9.5},
    paper_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 10, "r": 10, "t": 50, "b": 10},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
