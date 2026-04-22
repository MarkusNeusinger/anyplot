""" pyplots.ai
map-drilldown-geographic: Drillable Geographic Map
Library: plotly 6.5.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import numpy as np
import plotly.graph_objects as go


np.random.seed(42)

# Hierarchical geographic data - US states with cities
# Structure: state -> cities with sales values
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

# Calculate state totals (aggregated from cities)
states = list(us_states_data.keys())
state_abbrevs = [us_states_data[s]["abbrev"] for s in states]
state_values = [sum(us_states_data[s]["city_values"]) for s in states]

# City coordinates (approximate) for scatter overlay
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

# Create state-level choropleth (initial view)
fig = go.Figure()

# Add choropleth for US states
fig.add_trace(
    go.Choropleth(
        locations=state_abbrevs,
        z=state_values,
        locationmode="USA-states",
        colorscale=[
            [0, "#FFD43B"],  # Python Yellow (low)
            [0.5, "#4B8BBE"],  # Python Blue (mid)
            [1, "#306998"],  # Dark Python Blue (high)
        ],
        colorbar=dict(
            title=dict(text="Sales ($K)", font=dict(size=20)), tickfont=dict(size=16), len=0.6, thickness=25, x=1.02
        ),
        marker=dict(line=dict(color="white", width=2)),
        hovertemplate="<b>%{text}</b><br>Total Sales: $%{z:,.0f}K<extra></extra>",
        text=states,
        name="States",
    )
)

# Add city markers as a second layer
all_city_lons = []
all_city_lats = []
all_city_names = []
all_city_values = []
all_city_states = []

for state, data in us_states_data.items():
    for city, value in zip(data["cities"], data["city_values"]):
        if city in city_coords:
            lon, lat = city_coords[city]
            all_city_lons.append(lon)
            all_city_lats.append(lat)
            all_city_names.append(city)
            all_city_values.append(value)
            all_city_states.append(state)

# Add city scatter layer (visible when zoomed in)
fig.add_trace(
    go.Scattergeo(
        lon=all_city_lons,
        lat=all_city_lats,
        mode="markers+text",
        marker=dict(
            size=[v / 30 for v in all_city_values],
            color=all_city_values,
            colorscale=[[0, "#FFD43B"], [0.5, "#4B8BBE"], [1, "#306998"]],
            line=dict(color="white", width=1.5),
            sizemin=8,
        ),
        text=all_city_names,
        textposition="top center",
        textfont=dict(size=12, color="#333333"),
        hovertemplate="<b>%{text}</b><br>%{customdata}<br>Sales: $%{marker.color:,.0f}K<extra></extra>",
        customdata=all_city_states,
        name="Cities",
        visible=False,  # Hidden initially, shown when drilled down
    )
)

# Create dropdown buttons for drill-down navigation
buttons = [
    dict(
        label="🌎 All States (Click to drill down)",
        method="update",
        args=[
            {"visible": [True, False]},
            {
                "geo": {
                    "scope": "usa",
                    "showlakes": True,
                    "lakecolor": "rgb(220, 235, 250)",
                    "landcolor": "rgb(245, 245, 245)",
                    "showland": True,
                    "showcountries": False,
                    "bgcolor": "rgba(0,0,0,0)",
                },
                "title.text": "map-drilldown-geographic · plotly · pyplots.ai<br><sub>📍 United States Sales by State | Click dropdown to explore cities</sub>",
            },
        ],
    ),
    dict(
        label="🏙️ All Cities (Detailed view)",
        method="update",
        args=[
            {"visible": [True, True]},
            {
                "geo": {
                    "scope": "usa",
                    "showlakes": True,
                    "lakecolor": "rgb(220, 235, 250)",
                    "landcolor": "rgb(245, 245, 245)",
                    "showland": True,
                    "showcountries": False,
                    "bgcolor": "rgba(0,0,0,0)",
                },
                "title.text": "map-drilldown-geographic · plotly · pyplots.ai<br><sub>📍 United States > All Cities | Sales Distribution</sub>",
            },
        ],
    ),
]

# Add state-specific drill-down buttons
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
        dict(
            label=f"📍 {state} (${state_total}K)",
            method="update",
            args=[
                {"visible": [True, True]},
                {
                    "geo": {
                        "scope": "usa",
                        "center": {"lon": center["lon"], "lat": center["lat"]},
                        "projection": {"scale": center["zoom"]},
                        "showlakes": True,
                        "lakecolor": "rgb(220, 235, 250)",
                        "landcolor": "rgb(245, 245, 245)",
                        "showland": True,
                        "showcountries": False,
                        "bgcolor": "rgba(0,0,0,0)",
                    },
                    "title.text": f"map-drilldown-geographic · plotly · pyplots.ai<br><sub>📍 United States > {state} | City-level Sales</sub>",
                },
            ],
        )
    )

# Update layout
fig.update_layout(
    title=dict(
        text="map-drilldown-geographic · plotly · pyplots.ai<br><sub>📍 United States Sales by State | Click dropdown to explore cities</sub>",
        font=dict(size=28, color="#333333"),
        x=0.5,
        xanchor="center",
    ),
    geo=dict(
        scope="usa",
        showlakes=True,
        lakecolor="rgb(220, 235, 250)",
        landcolor="rgb(245, 245, 245)",
        showland=True,
        bgcolor="rgba(0,0,0,0)",
    ),
    updatemenus=[
        dict(
            type="dropdown",
            direction="down",
            active=0,
            x=0.02,
            y=0.98,
            xanchor="left",
            yanchor="top",
            buttons=buttons,
            font=dict(size=14),
            bgcolor="white",
            bordercolor="#306998",
            borderwidth=2,
            showactive=True,
        )
    ],
    paper_bgcolor="white",
    margin=dict(l=20, r=20, t=100, b=20),
    annotations=[
        dict(
            text="<b>Navigation:</b> Use dropdown menu to drill down into states and cities",
            x=0.5,
            y=-0.02,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=14, color="#666666"),
            align="center",
        )
    ],
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
