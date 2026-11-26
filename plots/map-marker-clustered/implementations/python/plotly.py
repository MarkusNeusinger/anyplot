"""anyplot.ai
map-marker-clustered: Clustered Marker Map
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-23
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

# Imprint palette — canonical order for categorical series
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns
LAT = "lat"  # role: latitude
LON = "lon"  # role: longitude
LABEL = "label"  # role: hover label
CATEGORY = "category"  # role: color group

# Data - Retail store locations across North America
np.random.seed(42)

cities = {
    "New York": (40.7128, -74.0060, 80),
    "Los Angeles": (34.0522, -118.2437, 60),
    "Chicago": (41.8781, -87.6298, 50),
    "Houston": (29.7604, -95.3698, 40),
    "Phoenix": (33.4484, -112.0740, 35),
    "Seattle": (47.6062, -122.3321, 30),
    "Denver": (39.7392, -104.9903, 25),
    "Miami": (25.7617, -80.1918, 45),
    "Atlanta": (33.7490, -84.3880, 35),
    "Boston": (42.3601, -71.0589, 40),
}

categories = ["Electronics", "Grocery", "Clothing", "Hardware"]

lats, lons, labels, cats = [], [], [], []
store_id = 1

for city, (lat, lon, count) in cities.items():
    for _ in range(count):
        lats.append(lat + np.random.normal(0, 0.15))
        lons.append(lon + np.random.normal(0, 0.15))
        cats.append(np.random.choice(categories))
        labels.append(f"Store #{store_id} - {city}")
        store_id += 1

df = pd.DataFrame({LAT: lats, LON: lons, LABEL: labels, CATEGORY: cats})

city_counts = {city: count for city, (_, _, count) in cities.items()}
densest_city = max(city_counts, key=city_counts.get)

# Plot
map_style = "carto-positron" if THEME == "light" else "carto-darkmatter"

fig = go.Figure()

# Clustering runs per trace, so each category forms its own cluster at a city. Giving every
# category a different cluster size stacks them as concentric rings (first category outermost),
# so all category colors stay visible; ring size grows with the number of grouped stores.
for category, rows in df.groupby(CATEGORY, sort=False):
    color = IMPRINT_PALETTE[categories.index(category)]
    ring = 22 + 8 * (len(categories) - 1 - categories.index(category))
    fig.add_trace(
        go.Scattermap(
            lat=rows[LAT],
            lon=rows[LON],
            mode="markers",
            marker={"size": 14, "color": color, "opacity": 0.85},
            text=rows[LABEL],
            hovertemplate=(
                "<b>%{text}</b><br>"
                + f"Category: {category}<br>"
                + "Lat: %{lat:.4f}<br>Lon: %{lon:.4f}"
                + "<extra></extra>"
            ),
            name=str(category),
            cluster={"enabled": True, "maxzoom": 10, "step": 1, "size": ring, "color": color, "opacity": 0.8},
        )
    )

fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    title={
        "text": "Retail Store Locations · map-marker-clustered · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    map={"style": map_style, "center": {"lat": 39.0, "lon": -100.0}, "zoom": 3.5},
    legend={
        "title": {"text": f"Store Category  (n={len(df)})", "font": {"size": 12, "color": INK}},
        "font": {"size": 10, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "x": 0.01,
        "y": 0.99,
        "xanchor": "left",
        "yanchor": "top",
    },
    margin={"l": 80, "r": 60, "t": 80, "b": 60},
)

# Data-context annotation, kept above the basemap attribution row
fig.add_annotation(
    x=0.97,
    y=0.07,
    xref="paper",
    yref="paper",
    text=(
        f"<b>{len(df)} retail locations</b> across {len(cities)} US cities<br>"
        f"Densest cluster: <b>{densest_city}</b> ({city_counts[densest_city]} stores)"
        "  ·  zoom in to expand clusters"
    ),
    showarrow=False,
    font={"size": 10, "color": INK_SOFT},
    bgcolor=ELEVATED_BG,
    bordercolor=INK_SOFT,
    borderwidth=1,
    borderpad=6,
    align="right",
    xanchor="right",
    yanchor="bottom",
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
