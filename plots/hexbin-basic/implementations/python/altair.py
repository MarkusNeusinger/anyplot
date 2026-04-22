""" pyplots.ai
hexbin-basic: Basic Hexbin Plot
Library: altair 6.0.0 | Python 3.14.3
Quality: 92/100 | Updated: 2026-02-21
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - GPS coordinates showing traffic density in Seattle
np.random.seed(42)

n_points = 5000

# Downtown core - highest density (tight cluster for strong density peak)
downtown_lon = np.random.randn(n_points // 2) * 0.006 + (-122.335)
downtown_lat = np.random.randn(n_points // 2) * 0.005 + 47.608

# Shopping district - secondary hotspot
shopping_lon = np.random.randn(n_points // 3) * 0.005 + (-122.315)
shopping_lat = np.random.randn(n_points // 3) * 0.004 + 47.622

# Industrial zone - sparse traffic
industrial_lon = np.random.randn(n_points // 6) * 0.004 + (-122.355)
industrial_lat = np.random.randn(n_points // 6) * 0.003 + 47.635

longitude = np.concatenate([downtown_lon, shopping_lon, industrial_lon])
latitude = np.concatenate([downtown_lat, shopping_lat, industrial_lat])

# Hexagonal binning - compute hex grid positions and counts
hex_radius = 0.002
dx = hex_radius * np.sqrt(3)
dy = hex_radius * 1.5

row_idx = np.round(latitude / dy).astype(int)
shift = (row_idx % 2) * 0.5
col_adj = np.round((longitude / dx) - shift).astype(int)

hex_cx = (col_adj + shift) * dx
hex_cy = row_idx * dy

hexbins = pd.DataFrame({"lon": hex_cx, "lat": hex_cy}).groupby(["lon", "lat"]).size().reset_index(name="count")

# Compute pixel size for hexagons to tile cleanly
chart_width, chart_height = 1600, 900
lon_range = hexbins["lon"].max() - hexbins["lon"].min()
lat_range = hexbins["lat"].max() - hexbins["lat"].min()
hex_px_w = dx * (chart_width / lon_range) if lon_range > 0 else 1
hex_px_h = 2 * hex_radius * (chart_height / lat_range) if lat_range > 0 else 1
hex_area = hex_px_w * hex_px_h

# Custom hexagon SVG path (pointy-top)
hex_path = "M0,-1L0.866,-0.5L0.866,0.5L0,1L-0.866,0.5L-0.866,-0.5Z"

# Interactive hover selection — distinctive Altair/Vega-Lite feature
hover = alt.selection_point(on="pointerover", nearest=True, empty=False)

# Hexbin layer with hover-responsive encoding and computed density level
hexbin_layer = (
    alt.Chart(hexbins)
    .transform_calculate(density="datum.count > 60 ? 'High' : datum.count > 25 ? 'Medium' : 'Low'")
    .mark_point(shape=hex_path, filled=True, stroke="white")
    .encode(
        x=alt.X(
            "lon:Q",
            title="Longitude (\u00b0W)",
            scale=alt.Scale(zero=False),
            axis=alt.Axis(
                labelFontSize=18,
                titleFontSize=22,
                format=".2f",
                values=[-122.36, -122.34, -122.32, -122.30],
                grid=True,
                gridOpacity=0.08,
                gridColor="#ccc",
            ),
        ),
        y=alt.Y(
            "lat:Q",
            title="Latitude (\u00b0N)",
            scale=alt.Scale(zero=False),
            axis=alt.Axis(
                labelFontSize=18,
                titleFontSize=22,
                format=".2f",
                values=[47.59, 47.60, 47.61, 47.62, 47.63, 47.64],
                grid=True,
                gridOpacity=0.08,
                gridColor="#ccc",
            ),
        ),
        color=alt.Color(
            "count:Q",
            scale=alt.Scale(scheme="viridis", type="symlog"),
            legend=alt.Legend(
                title="Vehicle Count",
                titleFontSize=20,
                labelFontSize=16,
                gradientLength=350,
                gradientThickness=25,
                orient="right",
                offset=20,
                titlePadding=10,
            ),
        ),
        size=alt.value(hex_area),
        strokeWidth=alt.condition(hover, alt.value(2.5), alt.value(0.4)),
        tooltip=[
            alt.Tooltip("lon:Q", title="Longitude", format=".4f"),
            alt.Tooltip("lat:Q", title="Latitude", format=".4f"),
            alt.Tooltip("count:Q", title="Vehicles"),
            alt.Tooltip("density:N", title="Density Level"),
        ],
    )
    .add_params(hover)
)

# Cluster annotation labels for data storytelling
annotations = pd.DataFrame(
    {
        "lon": [-122.335, -122.303, -122.360],
        "lat": [47.587, 47.633, 47.648],
        "label": ["Downtown Core", "Shopping District", "Industrial Zone"],
    }
)

text_bg = (
    alt.Chart(annotations)
    .mark_text(fontSize=16, fontWeight="bold", color="#f9f9fb", strokeWidth=4, stroke="#f9f9fb")
    .encode(x="lon:Q", y="lat:Q", text="label:N")
)

text_fg = (
    alt.Chart(annotations)
    .mark_text(fontSize=16, fontWeight="bold", color="#2a2a2a")
    .encode(x="lon:Q", y="lat:Q", text="label:N")
)

# Compose layers with title, subtitle, and refined styling
chart = (
    alt.layer(hexbin_layer, text_bg, text_fg)
    .properties(
        width=chart_width,
        height=chart_height,
        title=alt.Title(
            "hexbin-basic \u00b7 altair \u00b7 pyplots.ai",
            fontSize=28,
            anchor="middle",
            color="#222",
            subtitle="Seattle metropolitan traffic density \u2014 5,000 GPS vehicle observations",
            subtitleFontSize=18,
            subtitleColor="#666",
            subtitlePadding=8,
        ),
        padding={"left": 20, "right": 20, "top": 10, "bottom": 10},
    )
    .configure_view(strokeWidth=0, fill="#f9f9fb")
    .configure_axis(domainColor="#aaa", tickColor="#aaa", labelColor="#555", titleColor="#333")
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
