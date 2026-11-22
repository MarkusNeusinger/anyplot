"""anyplot.ai
bubble-map-geographic: Bubble Map with Sized Geographic Markers
Library: plotly 6.7.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-11-22
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

LAND_COLOR = "#E8E4D8" if THEME == "light" else "#2E2E28"
OCEAN_COLOR = "#D0E4F0" if THEME == "light" else "#1A2535"
COAST_COLOR = "#B0A890" if THEME == "light" else "#4A4A40"
COUNTRY_COLOR = "#C8C4B4" if THEME == "light" else "#3A3A34"

# Imprint palette: one color per region in order of first appearance
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns
CITY = "City"  # role: label
LATITUDE = "Latitude"  # role: latitude
LONGITUDE = "Longitude"  # role: longitude
POPULATION = "Population (millions)"  # role: value
REGION = "Region"  # role: category

# Data: major world cities with population (in millions); replace with your own table
cities = [
    {CITY: "Tokyo", LATITUDE: 35.6762, LONGITUDE: 139.6503, POPULATION: 37.4, REGION: "Asia"},
    {CITY: "Delhi", LATITUDE: 28.7041, LONGITUDE: 77.1025, POPULATION: 31.2, REGION: "Asia"},
    {CITY: "Shanghai", LATITUDE: 31.2304, LONGITUDE: 121.4737, POPULATION: 27.8, REGION: "Asia"},
    {CITY: "São Paulo", LATITUDE: -23.5505, LONGITUDE: -46.6333, POPULATION: 22.4, REGION: "South America"},
    {CITY: "Mexico City", LATITUDE: 19.4326, LONGITUDE: -99.1332, POPULATION: 21.9, REGION: "North America"},
    {CITY: "Cairo", LATITUDE: 30.0444, LONGITUDE: 31.2357, POPULATION: 21.3, REGION: "Africa"},
    {CITY: "Mumbai", LATITUDE: 19.0760, LONGITUDE: 72.8777, POPULATION: 20.7, REGION: "Asia"},
    {CITY: "Beijing", LATITUDE: 39.9042, LONGITUDE: 116.4074, POPULATION: 20.5, REGION: "Asia"},
    {CITY: "Dhaka", LATITUDE: 23.8103, LONGITUDE: 90.4125, POPULATION: 22.5, REGION: "Asia"},
    {CITY: "Osaka", LATITUDE: 34.6937, LONGITUDE: 135.5023, POPULATION: 19.2, REGION: "Asia"},
    {CITY: "New York", LATITUDE: 40.7128, LONGITUDE: -74.0060, POPULATION: 18.8, REGION: "North America"},
    {CITY: "Karachi", LATITUDE: 24.8607, LONGITUDE: 67.0011, POPULATION: 16.5, REGION: "Asia"},
    {CITY: "Buenos Aires", LATITUDE: -34.6037, LONGITUDE: -58.3816, POPULATION: 15.2, REGION: "South America"},
    {CITY: "Istanbul", LATITUDE: 41.0082, LONGITUDE: 28.9784, POPULATION: 15.4, REGION: "Europe"},
    {CITY: "Lagos", LATITUDE: 6.5244, LONGITUDE: 3.3792, POPULATION: 14.9, REGION: "Africa"},
    {CITY: "Manila", LATITUDE: 14.5995, LONGITUDE: 120.9842, POPULATION: 14.4, REGION: "Asia"},
    {CITY: "Rio de Janeiro", LATITUDE: -22.9068, LONGITUDE: -43.1729, POPULATION: 13.5, REGION: "South America"},
    {CITY: "Los Angeles", LATITUDE: 34.0522, LONGITUDE: -118.2437, POPULATION: 12.5, REGION: "North America"},
    {CITY: "Moscow", LATITUDE: 55.7558, LONGITUDE: 37.6173, POPULATION: 12.5, REGION: "Europe"},
    {CITY: "Paris", LATITUDE: 48.8566, LONGITUDE: 2.3522, POPULATION: 11.1, REGION: "Europe"},
    {CITY: "London", LATITUDE: 51.5074, LONGITUDE: -0.1278, POPULATION: 9.5, REGION: "Europe"},
    {CITY: "Lima", LATITUDE: -12.0464, LONGITUDE: -77.0428, POPULATION: 10.9, REGION: "South America"},
    {CITY: "Bangkok", LATITUDE: 13.7563, LONGITUDE: 100.5018, POPULATION: 10.7, REGION: "Asia"},
    {CITY: "Jakarta", LATITUDE: -6.2088, LONGITUDE: 106.8456, POPULATION: 10.6, REGION: "Asia"},
    {CITY: "Seoul", LATITUDE: 37.5665, LONGITUDE: 126.9780, POPULATION: 9.9, REGION: "Asia"},
    {CITY: "Sydney", LATITUDE: -33.8688, LONGITUDE: 151.2093, POPULATION: 5.4, REGION: "Oceania"},
    {CITY: "Melbourne", LATITUDE: -37.8136, LONGITUDE: 144.9631, POPULATION: 5.0, REGION: "Oceania"},
    {CITY: "Toronto", LATITUDE: 43.6532, LONGITUDE: -79.3832, POPULATION: 6.3, REGION: "North America"},
    {CITY: "Chicago", LATITUDE: 41.8781, LONGITUDE: -87.6298, POPULATION: 8.9, REGION: "North America"},
    {CITY: "Singapore", LATITUDE: 1.3521, LONGITUDE: 103.8198, POPULATION: 5.9, REGION: "Asia"},
]

df = pd.DataFrame(cities)

# Plot
FIG_W, FIG_H = 800, 450
# Bubble sizing: diameter grows with the square root of the value, so area is proportional to it
min_size, max_size = 8, 36
pop_min, pop_max = df[POPULATION].min(), df[POPULATION].max()


def bubble_size(pop):
    return min_size + (max_size - min_size) * np.sqrt((pop - pop_min) / (pop_max - pop_min))


df["marker_size"] = bubble_size(df[POPULATION])

fig = go.Figure()

for i, (region, rdf) in enumerate(df.groupby(REGION, sort=False)):
    fig.add_trace(
        go.Scattergeo(
            lon=rdf[LONGITUDE],
            lat=rdf[LATITUDE],
            text=[f"{c}<br>Population: {p:.1f}M" for c, p in zip(rdf[CITY], rdf[POPULATION], strict=True)],
            marker={
                "size": rdf["marker_size"],
                "color": IMPRINT_PALETTE[i],
                "opacity": 0.65,
                "line": {"width": 0.75, "color": PAGE_BG},
                "sizemode": "diameter",
            },
            name=str(region),
            hovertemplate="%{text}<extra></extra>",
        )
    )

# Style
fig.update_layout(
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    title={
        "text": "World City Populations · bubble-map-geographic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    geo={
        "showland": True,
        "landcolor": LAND_COLOR,
        "showlakes": False,
        "showocean": True,
        "oceancolor": OCEAN_COLOR,
        "showcoastlines": True,
        "coastlinecolor": COAST_COLOR,
        "coastlinewidth": 0.5,
        "showframe": True,
        "framecolor": INK_SOFT,
        "framewidth": 0.5,
        "showcountries": True,
        "countrycolor": COUNTRY_COLOR,
        "countrywidth": 0.25,
        "projection_type": "natural earth",
        "lataxis": {"range": [-60, 75]},
        "lonaxis": {"range": [-140, 180]},
        "bgcolor": PAGE_BG,
    },
    legend={
        "title": {"text": REGION, "font": {"size": 11, "color": INK}},
        "font": {"size": 10, "color": INK_SOFT},
        "itemsizing": "constant",
        "x": 0.02,
        "y": 0.40,
        "xanchor": "left",
        "yanchor": "bottom",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 0.5,
    },
    autosize=False,
    width=FIG_W,
    height=FIG_H,
    margin={"l": 10, "r": 10, "t": 40, "b": 10},
)

# Visual size legend: circle shapes in paper coordinates
ref_pops = [35, 20, 5]  # drawn top to bottom
ref_sizes_px = [bubble_size(p) for p in ref_pops]

fig.add_shape(
    type="rect",
    xref="paper",
    yref="paper",
    x0=0.005,
    y0=0.005,
    x1=0.195,
    y1=0.290,
    fillcolor=ELEVATED_BG,
    line={"color": INK_SOFT, "width": 0.5},
    opacity=0.92,
)

fig.add_annotation(
    text="<b>Population scale</b>",
    xref="paper",
    yref="paper",
    x=0.100,
    y=0.282,
    showarrow=False,
    font={"size": 9, "color": INK},
    align="center",
    xanchor="center",
    yanchor="top",
)

cx = 0.062
y_centers = [0.205, 0.115, 0.045]
labels = [f"{p}M" for p in ref_pops]

for size_px, y_c, label in zip(ref_sizes_px, y_centers, labels, strict=False):
    rx = (size_px / 2) / FIG_W
    ry = (size_px / 2) / FIG_H
    fig.add_shape(
        type="circle",
        xref="paper",
        yref="paper",
        x0=cx - rx,
        y0=y_c - ry,
        x1=cx + rx,
        y1=y_c + ry,
        fillcolor=INK_SOFT,
        line={"color": PAGE_BG, "width": 0.5},
        opacity=0.55,
    )
    fig.add_annotation(
        text=label,
        xref="paper",
        yref="paper",
        x=cx + rx + 0.012,
        y=y_c,
        showarrow=False,
        font={"size": 9, "color": INK_SOFT},
        align="left",
        xanchor="left",
        yanchor="middle",
    )

# Save
fig.write_image(f"plot-{THEME}.png", width=FIG_W, height=FIG_H, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
