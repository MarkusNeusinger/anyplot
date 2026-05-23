"""anyplot.ai
map-drilldown-geographic: Drillable Geographic Map
Library: plotly | Python 3.13
Quality: pending | Updated: 2026-05-23
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

ANYPLOT_SEQ = [[0.0, "#009E73"], [1.0, "#003D94"]]

# Geo background colors per theme
LAND_COLOR = "rgb(228, 224, 210)" if THEME == "light" else "rgb(40, 38, 33)"
LAKE_COLOR = "rgb(197, 220, 245)" if THEME == "light" else "rgb(20, 40, 65)"
OCEAN_COLOR = "rgb(210, 228, 248)" if THEME == "light" else "rgb(15, 30, 55)"
BORDER_COLOR = "rgb(180, 175, 160)" if THEME == "light" else "rgb(70, 68, 60)"

# Data — US states with cities, sales values ($K)
np.random.seed(42)

us_states_data = {
    "California": {
        "abbrev": "CA",
        "cities": ["Los Angeles", "San Francisco", "San Diego", "San Jose", "Sacramento"],
        "city_values": [850, 720, 480, 520, 280],
    },
    "Texas": {
        "abbrev": "TX",
        "cities": ["Houston", "Dallas", "Austin", "San Antonio", "Fort Worth"],
        "city_values": [780, 690, 580, 420, 320],
    },
    "Florida": {
        "abbrev": "FL",
        "cities": ["Miami", "Orlando", "Tampa", "Jacksonville", "Fort Lauderdale"],
        "city_values": [620, 510, 450, 380, 290],
    },
    "New York": {
        "abbrev": "NY",
        "cities": ["New York City", "Buffalo", "Rochester", "Albany", "Syracuse"],
        "city_values": [950, 280, 250, 220, 180],
    },
    "Illinois": {
        "abbrev": "IL",
        "cities": ["Chicago", "Aurora", "Naperville", "Rockford", "Joliet"],
        "city_values": [720, 180, 165, 145, 130],
    },
    "Pennsylvania": {
        "abbrev": "PA",
        "cities": ["Philadelphia", "Pittsburgh", "Allentown", "Erie", "Reading"],
        "city_values": [580, 420, 180, 150, 140],
    },
    "Ohio": {
        "abbrev": "OH",
        "cities": ["Columbus", "Cleveland", "Cincinnati", "Toledo", "Akron"],
        "city_values": [450, 380, 360, 220, 190],
    },
    "Georgia": {
        "abbrev": "GA",
        "cities": ["Atlanta", "Augusta", "Savannah", "Columbus", "Athens"],
        "city_values": [680, 220, 200, 180, 150],
    },
    "North Carolina": {
        "abbrev": "NC",
        "cities": ["Charlotte", "Raleigh", "Greensboro", "Durham", "Wilmington"],
        "city_values": [520, 450, 280, 260, 180],
    },
    "Michigan": {
        "abbrev": "MI",
        "cities": ["Detroit", "Grand Rapids", "Ann Arbor", "Lansing", "Flint"],
        "city_values": [480, 280, 250, 180, 150],
    },
}

states = list(us_states_data.keys())
state_abbrevs = [us_states_data[s]["abbrev"] for s in states]
state_values = [sum(us_states_data[s]["city_values"]) for s in states]

# City coordinates (approximate lat/lon)
city_coords = {
    "Los Angeles": (-118.24, 34.05),
    "San Francisco": (-122.42, 37.77),
    "San Diego": (-117.16, 32.72),
    "San Jose": (-121.89, 37.34),
    "Sacramento": (-121.49, 38.58),
    "Houston": (-95.37, 29.76),
    "Dallas": (-96.80, 32.78),
    "Austin": (-97.74, 30.27),
    "San Antonio": (-98.49, 29.42),
    "Fort Worth": (-97.33, 32.75),
    "Miami": (-80.19, 25.76),
    "Orlando": (-81.38, 28.54),
    "Tampa": (-82.46, 27.95),
    "Jacksonville": (-81.66, 30.33),
    "Fort Lauderdale": (-80.14, 26.12),
    "New York City": (-74.01, 40.71),
    "Buffalo": (-78.88, 42.89),
    "Rochester": (-77.61, 43.16),
    "Albany": (-73.76, 42.65),
    "Syracuse": (-76.15, 43.05),
    "Chicago": (-87.63, 41.88),
    "Aurora": (-88.32, 41.76),
    "Naperville": (-88.15, 41.79),
    "Rockford": (-89.09, 42.27),
    "Joliet": (-88.08, 41.53),
    "Philadelphia": (-75.16, 39.95),
    "Pittsburgh": (-79.99, 40.44),
    "Allentown": (-75.49, 40.60),
    "Erie": (-80.09, 42.13),
    "Reading": (-75.93, 40.34),
    "Columbus": (-82.99, 39.96),
    "Cleveland": (-81.69, 41.50),
    "Cincinnati": (-84.51, 39.10),
    "Toledo": (-83.54, 41.65),
    "Akron": (-81.52, 41.08),
    "Atlanta": (-84.39, 33.75),
    "Augusta": (-82.01, 33.47),
    "Savannah": (-81.10, 32.08),
    "Athens": (-83.38, 33.96),
    "Charlotte": (-80.84, 35.23),
    "Raleigh": (-78.64, 35.79),
    "Greensboro": (-79.79, 36.07),
    "Durham": (-78.90, 35.99),
    "Wilmington": (-77.95, 34.23),
    "Detroit": (-83.05, 42.33),
    "Grand Rapids": (-85.67, 42.96),
    "Ann Arbor": (-83.74, 42.28),
    "Lansing": (-84.55, 42.73),
    "Flint": (-83.69, 43.01),
}

# Flatten city data for scattergeo layer
all_city_lons, all_city_lats = [], []
all_city_names, all_city_values, all_city_states = [], [], []

for state, data in us_states_data.items():
    for city, value in zip(data["cities"], data["city_values"], strict=False):
        if city in city_coords:
            lon, lat = city_coords[city]
            all_city_lons.append(lon)
            all_city_lats.append(lat)
            all_city_names.append(city)
            all_city_values.append(value)
            all_city_states.append(state)

# Plot — state choropleth (top level) + city scatter (drill-down layer)
fig = go.Figure()

fig.add_trace(
    go.Choropleth(
        locations=state_abbrevs,
        z=state_values,
        locationmode="USA-states",
        colorscale=ANYPLOT_SEQ,
        colorbar={
            "title": {"text": "Sales ($K)", "font": {"size": 12, "color": INK}},
            "tickfont": {"size": 10, "color": INK_SOFT},
            "len": 0.6,
            "thickness": 18,
            "x": 1.01,
            "bgcolor": ELEVATED_BG,
            "bordercolor": INK_SOFT,
            "borderwidth": 1,
        },
        marker={"line": {"color": BORDER_COLOR, "width": 1.5}},
        hovertemplate="<b>%{text}</b><br>Total Sales: $%{z:,.0f}K<extra></extra>",
        text=states,
        name="States",
    )
)

fig.add_trace(
    go.Scattergeo(
        lon=all_city_lons,
        lat=all_city_lats,
        mode="markers+text",
        marker={
            "size": [max(v / 40, 8) for v in all_city_values],
            "color": all_city_values,
            "colorscale": ANYPLOT_SEQ,
            "line": {"color": PAGE_BG, "width": 1.5},
            "sizemin": 8,
            "showscale": False,
        },
        text=all_city_names,
        textposition="top center",
        textfont={"size": 10, "color": INK},
        hovertemplate=("<b>%{text}</b><br>%{customdata}<br>Sales: $%{marker.color:,.0f}K<extra></extra>"),
        customdata=all_city_states,
        name="Cities",
        visible=False,
    )
)

# Dropdown buttons for hierarchical navigation
geo_base = {
    "scope": "usa",
    "showlakes": True,
    "lakecolor": LAKE_COLOR,
    "landcolor": LAND_COLOR,
    "showland": True,
    "showcountries": False,
    "showcoastlines": True,
    "coastlinecolor": BORDER_COLOR,
    "bgcolor": PAGE_BG,
}

title_base = "map-drilldown-geographic · python · plotly · anyplot.ai"

buttons = [
    {
        "label": "All States",
        "method": "update",
        "args": [
            {"visible": [True, False]},
            {
                "geo": {**geo_base},
                "title.text": f"{title_base}<br><sub>US Sales by State — use dropdown to drill into cities</sub>",
            },
        ],
    },
    {
        "label": "All Cities",
        "method": "update",
        "args": [
            {"visible": [True, True]},
            {"geo": {**geo_base}, "title.text": f"{title_base}<br><sub>US Sales — All Cities Overlay</sub>"},
        ],
    },
]

state_centers = {
    "California": {"lon": -119.5, "lat": 37.0, "zoom": 4.5},
    "Texas": {"lon": -99.0, "lat": 31.5, "zoom": 4.5},
    "Florida": {"lon": -82.5, "lat": 28.0, "zoom": 5.0},
    "New York": {"lon": -75.5, "lat": 43.0, "zoom": 5.0},
    "Illinois": {"lon": -89.0, "lat": 40.0, "zoom": 5.5},
    "Pennsylvania": {"lon": -77.5, "lat": 41.0, "zoom": 5.5},
    "Ohio": {"lon": -82.5, "lat": 40.5, "zoom": 5.5},
    "Georgia": {"lon": -83.5, "lat": 32.5, "zoom": 5.5},
    "North Carolina": {"lon": -79.5, "lat": 35.5, "zoom": 5.5},
    "Michigan": {"lon": -85.0, "lat": 44.0, "zoom": 5.0},
}

for state in states:
    center = state_centers[state]
    state_total = sum(us_states_data[state]["city_values"])
    buttons.append(
        {
            "label": f"{state} (${state_total}K)",
            "method": "update",
            "args": [
                {"visible": [True, True]},
                {
                    "geo": {
                        **geo_base,
                        "center": {"lon": center["lon"], "lat": center["lat"]},
                        "projection": {"scale": center["zoom"]},
                    },
                    "title.text": f"{title_base}<br><sub>United States > {state} | City-Level Sales</sub>",
                },
            ],
        }
    )

# Style
fig.update_layout(
    autosize=False,
    title={
        "text": f"{title_base}<br><sub>US Sales by State — use dropdown to drill into cities</sub>",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    geo=dict(**geo_base),
    updatemenus=[
        {
            "type": "dropdown",
            "direction": "down",
            "active": 0,
            "x": 0.01,
            "y": 0.99,
            "xanchor": "left",
            "yanchor": "top",
            "buttons": buttons,
            "font": {"size": 12, "color": INK},
            "bgcolor": ELEVATED_BG,
            "bordercolor": INK_SOFT,
            "borderwidth": 1,
            "showactive": True,
        }
    ],
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={"bgcolor": ELEVATED_BG, "bordercolor": INK_SOFT, "borderwidth": 1, "font": {"color": INK_SOFT}},
    margin={"l": 40, "r": 60, "t": 80, "b": 40},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
