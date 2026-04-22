""" pyplots.ai
cartogram-area-distortion: Cartogram with Area Distortion by Data Value
Library: plotly 6.6.0 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-13
"""

import numpy as np
import plotly.graph_objects as go


# Data - US states sized by population (2023 estimates, in millions)
states = [
    "CA",
    "TX",
    "FL",
    "NY",
    "PA",
    "IL",
    "OH",
    "GA",
    "NC",
    "MI",
    "NJ",
    "VA",
    "WA",
    "AZ",
    "MA",
    "TN",
    "IN",
    "MO",
    "MD",
    "WI",
    "CO",
    "MN",
    "SC",
    "AL",
    "LA",
    "KY",
    "OR",
    "OK",
    "CT",
    "UT",
    "IA",
    "NV",
    "AR",
    "MS",
    "KS",
    "NM",
    "NE",
    "ID",
    "WV",
    "HI",
    "NH",
    "ME",
    "MT",
    "RI",
    "DE",
    "SD",
    "ND",
    "AK",
    "VT",
    "WY",
]

population = np.array(
    [
        39.03,
        30.03,
        22.24,
        19.57,
        12.97,
        12.55,
        11.78,
        10.91,
        10.70,
        10.04,
        9.29,
        8.64,
        7.81,
        7.36,
        7.00,
        7.05,
        6.83,
        6.18,
        6.18,
        5.89,
        5.84,
        5.71,
        5.28,
        5.07,
        4.59,
        4.53,
        4.24,
        4.00,
        3.62,
        3.42,
        3.20,
        3.18,
        3.05,
        2.94,
        2.94,
        2.11,
        1.97,
        1.94,
        1.77,
        1.44,
        1.40,
        1.39,
        1.12,
        1.10,
        1.02,
        0.91,
        0.78,
        0.74,
        0.65,
        0.58,
    ]
)

# State area in sq miles (for density calculation)
area_sq_miles = np.array(
    [
        163696,
        268596,
        65758,
        54555,
        46054,
        57914,
        44826,
        59425,
        53819,
        96714,
        8723,
        42775,
        71298,
        113990,
        10554,
        42144,
        36420,
        69707,
        12406,
        65496,
        104094,
        86936,
        32020,
        52420,
        52378,
        40408,
        98379,
        69899,
        5543,
        84897,
        56273,
        110572,
        53179,
        48432,
        82278,
        121590,
        77348,
        83569,
        24230,
        10932,
        9349,
        35380,
        147040,
        1545,
        2489,
        77116,
        70698,
        665384,
        9616,
        97813,
    ]
)

# Approximate centroids (latitude, longitude) for each state
lats = np.array(
    [
        36.78,
        31.97,
        27.66,
        42.93,
        41.20,
        40.63,
        40.42,
        32.68,
        35.63,
        44.31,
        40.06,
        37.43,
        47.75,
        34.05,
        42.41,
        35.52,
        40.27,
        38.57,
        39.05,
        43.78,
        39.55,
        46.73,
        33.84,
        32.32,
        31.17,
        37.84,
        43.80,
        35.47,
        41.60,
        39.32,
        41.88,
        38.80,
        35.20,
        32.35,
        39.01,
        34.52,
        41.49,
        44.07,
        38.60,
        19.90,
        43.19,
        45.25,
        46.88,
        41.58,
        38.91,
        43.97,
        47.55,
        63.59,
        44.56,
        43.08,
    ]
)

lons = np.array(
    [
        -119.42,
        -99.90,
        -81.52,
        -75.58,
        -77.19,
        -89.40,
        -82.91,
        -83.54,
        -79.81,
        -84.71,
        -74.41,
        -78.66,
        -120.74,
        -111.09,
        -71.38,
        -86.15,
        -86.13,
        -91.83,
        -76.64,
        -89.62,
        -105.78,
        -94.69,
        -81.16,
        -86.90,
        -91.87,
        -84.27,
        -120.55,
        -97.09,
        -72.76,
        -111.09,
        -93.10,
        -116.42,
        -92.37,
        -89.40,
        -98.48,
        -105.87,
        -99.90,
        -114.74,
        -80.62,
        -155.58,
        -71.57,
        -69.45,
        -110.36,
        -71.48,
        -75.53,
        -99.44,
        -101.00,
        -154.49,
        -72.58,
        -107.29,
    ]
)

density = population * 1e6 / area_sq_miles

# Offset NE states more aggressively to eliminate crowding
ne_offsets = {
    "NJ": (0.3, 2.5),
    "CT": (-0.3, 3.2),
    "MA": (1.2, 2.8),
    "RI": (-1.2, 3.8),
    "NH": (1.8, 1.8),
    "VT": (2.2, 0.0),
    "DE": (-1.2, 2.8),
    "MD": (-1.8, 1.5),
    "ME": (1.5, 2.2),
}

for i, s in enumerate(states):
    if s in ne_offsets:
        dlat, dlon = ne_offsets[s]
        lats[i] += dlat
        lons[i] += dlon

# Scale bubble sizes: area proportional to population
# Enforce minimum size so small states remain visible
max_marker_size = 65
raw_sizes = np.sqrt(population / population.max()) * max_marker_size
sizes = np.clip(raw_sizes, 10, max_marker_size)

# Color values on log scale
log_density = np.log10(density)

# Show labels on states with population >= 2M for better coverage
label_threshold = 2.0
label_texts = [s if p >= label_threshold else "" for s, p in zip(states, population, strict=False)]

# Custom colorscale: deep navy → teal → golden yellow (publication quality)
custom_colorscale = [
    [0.0, "#0d0887"],
    [0.15, "#3a049a"],
    [0.3, "#6a00a8"],
    [0.45, "#900da4"],
    [0.55, "#b73779"],
    [0.65, "#d8576b"],
    [0.75, "#ed7953"],
    [0.85, "#f89540"],
    [0.95, "#fdca26"],
    [1.0, "#f0f921"],
]

# Create figure
fig = go.Figure()

# Background: faint state boundaries for geographic reference
fig.add_trace(
    go.Choropleth(
        locationmode="USA-states",
        locations=states,
        z=[0] * len(states),
        colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
        showscale=False,
        marker={"line": {"color": "rgba(180,190,200,0.5)", "width": 0.6}},
        hoverinfo="skip",
    )
)

# Bubble cartogram layer
fig.add_trace(
    go.Scattergeo(
        locationmode="USA-states",
        lon=lons,
        lat=lats,
        text=[
            f"<b>{s}</b><br>Population: {p:.1f}M<br>Density: {d:,.0f} per sq mi<br>Area: {a:,} sq mi"
            for s, p, d, a in zip(states, population, density, area_sq_miles, strict=False)
        ],
        hoverinfo="text",
        marker={
            "size": sizes,
            "color": log_density,
            "colorscale": custom_colorscale,
            "cmin": np.log10(5),
            "cmax": np.log10(6000),
            "colorbar": {
                "title": {
                    "text": "Population Density<br>(per sq mi)",
                    "font": {"size": 18, "family": "Arial", "color": "#333"},
                },
                "tickfont": {"size": 15, "color": "#555"},
                "tickvals": np.log10([10, 50, 100, 500, 1000, 5000]).tolist(),
                "ticktext": ["10", "50", "100", "500", "1k", "5k"],
                "len": 0.55,
                "thickness": 22,
                "x": 0.94,
                "outlinewidth": 0,
                "bgcolor": "rgba(255,255,255,0.8)",
            },
            "line": {"width": 1.8, "color": "rgba(255,255,255,0.9)"},
            "opacity": 0.92,
            "sizemode": "diameter",
        },
    )
)

# State abbreviation labels
fig.add_trace(
    go.Scattergeo(
        locationmode="USA-states",
        lon=lons,
        lat=lats,
        text=label_texts,
        mode="text",
        textfont={
            "size": [max(9, min(14, int(s / 5))) if t else 1 for s, t in zip(sizes, label_texts, strict=False)],
            "color": "white",
            "family": "Arial Black",
        },
        hoverinfo="skip",
        showlegend=False,
    )
)

# Layout with refined styling
fig.update_layout(
    title={
        "text": (
            "<b style='color:#1a1a2e'>U.S. States Sized by Population</b>"
            "<br><span style='font-size:16px;color:#888;font-weight:normal'>"
            "cartogram-area-distortion · plotly · pyplots.ai</span>"
        ),
        "font": {"size": 30, "family": "Arial"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.96,
    },
    geo={
        "scope": "usa",
        "showframe": False,
        "showcoastlines": True,
        "coastlinecolor": "rgba(180,190,200,0.4)",
        "coastlinewidth": 0.5,
        "showland": True,
        "landcolor": "#fafbfc",
        "showlakes": True,
        "lakecolor": "#f0f4f8",
        "bgcolor": "white",
        "projection_type": "albers usa",
    },
    template="plotly_white",
    paper_bgcolor="white",
    plot_bgcolor="white",
    margin={"l": 20, "r": 100, "t": 90, "b": 60},
    showlegend=False,
    annotations=[
        # Footer with encoding explanation
        {
            "text": ("<b>Area</b> proportional to population  ·  <b>Color</b> proportional to density"),
            "xref": "paper",
            "yref": "paper",
            "x": 0.5,
            "y": -0.04,
            "showarrow": False,
            "font": {"size": 16, "color": "#666", "family": "Arial"},
        },
        # Highlight annotation for storytelling
        {
            "text": ("California (39M) has 6× more people than<br>median state, yet New Jersey is 4× denser"),
            "xref": "paper",
            "yref": "paper",
            "x": 0.02,
            "y": 0.15,
            "showarrow": False,
            "font": {"size": 13, "color": "#777", "family": "Arial"},
            "align": "left",
            "bgcolor": "rgba(255,255,255,0.85)",
            "borderpad": 6,
        },
    ],
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
