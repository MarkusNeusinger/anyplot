""" anyplot.ai
map-tile-background: Map with Tile Background
Library: plotly 6.7.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-27
"""

import os
import sys


# Remove this script's directory from sys.path so "plotly.py" doesn't shadow
# the installed plotly package when Python prepends the script dir.
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _script_dir]

import numpy as np
import plotly.graph_objects as go


THEME = os.getenv("ANYPLOT_THEME", "light")

# Theme-adaptive chrome
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Anyplot sequential colorscale: brand green → blue (single-polarity continuous)
imprint_seq = [[0.0, "#009E73"], [1.0, "#4467A3"]]

# Theme-adaptive map tile style
map_style = "open-street-map" if THEME == "light" else "carto-darkmatter"

# Data — European City Landmarks with annual visitor counts
np.random.seed(42)

names = [
    "Eiffel Tower",
    "Colosseum",
    "Sagrada Familia",
    "Big Ben",
    "Brandenburg Gate",
    "Anne Frank House",
    "Acropolis",
    "Charles Bridge",
    "St. Stephen's Basilica",
    "Royal Palace",
    "Manneken Pis",
    "Tivoli Gardens",
    "Schönbrunn Palace",
    "Old Town Square",
    "Rialto Bridge",
]
lats = [
    48.8584,
    41.8902,
    41.4036,
    51.5007,
    52.5163,
    52.3752,
    37.9715,
    50.0865,
    47.5008,
    59.3268,
    50.8450,
    55.6736,
    48.1845,
    50.0870,
    45.4380,
]
lons = [
    2.2945,
    12.4922,
    2.1744,
    -0.1246,
    13.3777,
    4.8840,
    23.7267,
    14.4114,
    19.0538,
    18.0717,
    4.3499,
    12.5681,
    16.3119,
    14.4208,
    12.3358,
]
visitors = np.array(
    [
        7_000_000,
        7_400_000,
        4_500_000,
        2_000_000,
        3_000_000,
        1_300_000,
        3_000_000,
        5_000_000,
        1_000_000,
        1_500_000,
        500_000,
        4_000_000,
        4_000_000,
        6_000_000,
        5_000_000,
    ]
)

# Scale visitor counts to marker diameters (15–50 px range)
sizes = 15 + (visitors - visitors.min()) / (visitors.max() - visitors.min()) * 35

fig = go.Figure()

fig.add_trace(
    go.Scattermap(
        lat=lats,
        lon=lons,
        mode="markers+text",
        marker={
            "size": sizes,
            "color": visitors,
            "colorscale": imprint_seq,
            "colorbar": {
                "title": {"text": "Annual Visitors", "font": {"size": 12, "color": INK}},
                "tickfont": {"size": 10, "color": INK_SOFT},
                "bgcolor": ELEVATED_BG,
                "bordercolor": INK_SOFT,
                "borderwidth": 1,
                "thickness": 18,
                "len": 0.65,
                "tickformat": ",.0f",
            },
            "opacity": 0.85,
        },
        text=names,
        textposition="top center",
        textfont={"size": 14, "color": INK},
        hovertemplate=(
            "<b>%{text}</b><br>Lat: %{lat:.4f}°<br>Lon: %{lon:.4f}°<br>Visitors: %{marker.color:,.0f}<extra></extra>"
        ),
    )
)

fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    font={"color": INK},
    title={
        "text": (
            "European Landmarks by Visitor Count<br>"
            "<span style='font-size:12px'>"
            "map-tile-background · python · plotly · anyplot.ai"
            "</span>"
        ),
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    map={"style": map_style, "center": {"lat": 48.5, "lon": 10.0}, "zoom": 3.5},
    margin={"l": 20, "r": 20, "t": 80, "b": 20},
    showlegend=False,
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
