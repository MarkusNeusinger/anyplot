"""anyplot.ai
scatter-map-geographic: Scatter Map with Geographic Points
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
LAND_COLOR = "#E5E5E5" if THEME == "light" else "#3A3A36"
OCEAN_COLOR = "#D4E8F2" if THEME == "light" else "#2A3F4D"
COAST_COLOR = "#999999" if THEME == "light" else "#666666"
COUNTRY_COLOR = "#CCCCCC" if THEME == "light" else "#555555"

# Imprint palette: continuous single-polarity scale (green to blue)
IMPRINT_SEQ = [[0.0, "#009E73"], [1.0, "#4467A3"]]

# Columns: set these to your table's column names
LATITUDE = "Latitude (°)"  # role: latitude
LONGITUDE = "Longitude (°)"  # role: longitude
AQI = "AQI"  # role: value
READINGS = "Readings per month"  # role: size

# Data: replace this block with your own table, for example df = pd.read_csv("sensors.csv")
# Global air-quality sensor network; columns are latitude, longitude, AQI and monthly reading count.
rng = np.random.default_rng(42)
regions = [
    # (sensors in region, lat range(s), lon range(s), AQI range, readings range)
    (15, (40, 45), (-82, -70), (20, 120), (15, 30)),  # US northeast corridor
    (10, (32, 38), (-85, -75), (20, 120), (15, 30)),  # US southeast
    (10, (50, 55), (5, 15), (25, 140), (20, 30)),  # Central Europe
    (10, (45, 50), (10, 25), (25, 140), (20, 30)),  # Mediterranean
    (12, (30, 40), (100, 120), (30, 250), (10, 30)),  # China
    (8, (10, 20), (95, 110), (30, 250), (10, 30)),  # Southeast Asia
    (5, (-10, 10), (110, 140), (30, 250), (10, 30)),  # Indonesia
    (10, (-35, 20), (-20, 55), (15, 180), (8, 25)),  # Africa
    (5, (-40, -15), (110, 180), (20, 80), (12, 28)),  # Australia-Pacific
]
parts = []
for n, lat_range, lon_range, aqi_range, count_range in regions:
    parts.append(
        pd.DataFrame(
            {
                LATITUDE: rng.uniform(*lat_range, n),
                LONGITUDE: rng.uniform(*lon_range, n),
                AQI: rng.uniform(*aqi_range, n),
                READINGS: rng.uniform(*count_range, n),
            }
        )
    )
df = pd.concat(parts, ignore_index=True)

# Plot: reads only df and the constants above
readings = df[READINGS]
marker_sizes = 4 + 12 * (readings - readings.min()) / (readings.max() - readings.min())

hover_texts = [f"{AQI}: {aqi:.0f}<br>{READINGS}: {count:.0f}" for aqi, count in zip(df[AQI], readings, strict=True)]

fig = go.Figure()
fig.add_trace(
    go.Scattergeo(
        lat=df[LATITUDE],
        lon=df[LONGITUDE],
        mode="markers",
        marker={
            "size": marker_sizes,
            "color": df[AQI],
            "colorscale": IMPRINT_SEQ,
            "colorbar": {
                "title": {"text": AQI, "font": {"size": 12, "color": INK}},
                "tickfont": {"size": 10, "color": INK_SOFT},
                "len": 0.5,
                "y": 0.65,
                "thickness": 14,
                "x": 1.0,
                "outlinecolor": INK_SOFT,
                "outlinewidth": 0.5,
            },
            "line": {"width": 0.6, "color": INK},
            "opacity": 0.85,
        },
        text=hover_texts,
        hovertemplate=(
            f"<b>{LATITUDE}:</b> %{{lat:.2f}}<br><b>{LONGITUDE}:</b> %{{lon:.2f}}<br>%{{text}}<extra></extra>"
        ),
    )
)

fig.update_layout(
    autosize=False,
    title={
        "text": "scatter-map-geographic · python · plotly · anyplot.ai",
        "font": {"size": 18, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    geo={
        "projection_type": "natural earth",
        "showland": True,
        "landcolor": LAND_COLOR,
        "showocean": True,
        "oceancolor": OCEAN_COLOR,
        "showcoastlines": True,
        "coastlinecolor": COAST_COLOR,
        "coastlinewidth": 0.6,
        "showcountries": True,
        "countrycolor": COUNTRY_COLOR,
        "countrywidth": 0.3,
        "showlakes": True,
        "lakecolor": OCEAN_COLOR,
        "showframe": False,
        "bgcolor": PAGE_BG,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin={"l": 20, "r": 135, "t": 60, "b": 20},
    font={"color": INK},
)

# Size legend: the marker diameter encodes the monthly reading count
fig.add_annotation(
    x=1.0,
    y=0.2,
    xref="paper",
    yref="paper",
    text=f"<b>Point size</b><br>{READINGS}<br>{readings.min():.0f} to {readings.max():.0f}",
    showarrow=False,
    font={"size": 10, "color": INK},
    align="left",
    xanchor="left",
    bgcolor=ELEVATED_BG,
    bordercolor=INK_SOFT,
    borderwidth=1,
    borderpad=4,
)

# Save as PNG and HTML
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
