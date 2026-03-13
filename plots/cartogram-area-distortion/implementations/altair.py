""" pyplots.ai
cartogram-area-distortion: Cartogram with Area Distortion by Data Value
Library: altair 6.0.0 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-13
"""

import altair as alt
import pandas as pd


# Data - US states with population (2023 estimates, millions) and centroids
states = pd.DataFrame(
    [
        {"state": "AL", "name": "Alabama", "pop": 5.1, "lat": 32.8, "lon": -86.8, "region": "South"},
        {"state": "AK", "name": "Alaska", "pop": 0.7, "lat": 64.2, "lon": -153.5, "region": "West"},
        {"state": "AZ", "name": "Arizona", "pop": 7.4, "lat": 34.3, "lon": -111.7, "region": "West"},
        {"state": "AR", "name": "Arkansas", "pop": 3.0, "lat": 34.9, "lon": -92.4, "region": "South"},
        {"state": "CA", "name": "California", "pop": 38.9, "lat": 37.2, "lon": -119.5, "region": "West"},
        {"state": "CO", "name": "Colorado", "pop": 5.9, "lat": 39.0, "lon": -105.5, "region": "West"},
        {"state": "CT", "name": "Connecticut", "pop": 3.6, "lat": 41.6, "lon": -72.7, "region": "Northeast"},
        {"state": "DE", "name": "Delaware", "pop": 1.0, "lat": 38.2, "lon": -74.8, "region": "South"},
        {"state": "FL", "name": "Florida", "pop": 22.6, "lat": 28.6, "lon": -82.5, "region": "South"},
        {"state": "GA", "name": "Georgia", "pop": 11.0, "lat": 33.0, "lon": -83.5, "region": "South"},
        {"state": "HI", "name": "Hawaii", "pop": 1.4, "lat": 20.5, "lon": -157.5, "region": "West"},
        {"state": "ID", "name": "Idaho", "pop": 2.0, "lat": 44.4, "lon": -114.6, "region": "West"},
        {"state": "IL", "name": "Illinois", "pop": 12.5, "lat": 40.0, "lon": -89.2, "region": "Midwest"},
        {"state": "IN", "name": "Indiana", "pop": 6.9, "lat": 39.9, "lon": -86.3, "region": "Midwest"},
        {"state": "IA", "name": "Iowa", "pop": 3.2, "lat": 42.0, "lon": -93.5, "region": "Midwest"},
        {"state": "KS", "name": "Kansas", "pop": 2.9, "lat": 38.5, "lon": -98.4, "region": "Midwest"},
        {"state": "KY", "name": "Kentucky", "pop": 4.5, "lat": 37.8, "lon": -85.3, "region": "South"},
        {"state": "LA", "name": "Louisiana", "pop": 4.6, "lat": 31.0, "lon": -91.8, "region": "South"},
        {"state": "ME", "name": "Maine", "pop": 1.4, "lat": 45.4, "lon": -69.2, "region": "Northeast"},
        {"state": "MD", "name": "Maryland", "pop": 6.2, "lat": 38.5, "lon": -76.0, "region": "South"},
        {"state": "MA", "name": "Massachusetts", "pop": 7.0, "lat": 42.6, "lon": -71.2, "region": "Northeast"},
        {"state": "MI", "name": "Michigan", "pop": 10.0, "lat": 43.4, "lon": -84.7, "region": "Midwest"},
        {"state": "MN", "name": "Minnesota", "pop": 5.7, "lat": 46.3, "lon": -94.3, "region": "Midwest"},
        {"state": "MS", "name": "Mississippi", "pop": 2.9, "lat": 32.7, "lon": -89.7, "region": "South"},
        {"state": "MO", "name": "Missouri", "pop": 6.2, "lat": 38.4, "lon": -92.5, "region": "Midwest"},
        {"state": "MT", "name": "Montana", "pop": 1.1, "lat": 47.0, "lon": -109.6, "region": "West"},
        {"state": "NE", "name": "Nebraska", "pop": 2.0, "lat": 41.5, "lon": -99.8, "region": "Midwest"},
        {"state": "NV", "name": "Nevada", "pop": 3.2, "lat": 39.3, "lon": -116.6, "region": "West"},
        {"state": "NH", "name": "New Hampshire", "pop": 1.4, "lat": 44.2, "lon": -71.6, "region": "Northeast"},
        {"state": "NJ", "name": "New Jersey", "pop": 9.3, "lat": 40.3, "lon": -73.8, "region": "Northeast"},
        {"state": "NM", "name": "New Mexico", "pop": 2.1, "lat": 34.5, "lon": -106.0, "region": "West"},
        {"state": "NY", "name": "New York", "pop": 19.6, "lat": 43.2, "lon": -75.5, "region": "Northeast"},
        {"state": "NC", "name": "N. Carolina", "pop": 10.7, "lat": 35.6, "lon": -79.4, "region": "South"},
        {"state": "ND", "name": "N. Dakota", "pop": 0.8, "lat": 47.4, "lon": -100.4, "region": "Midwest"},
        {"state": "OH", "name": "Ohio", "pop": 11.8, "lat": 40.4, "lon": -82.8, "region": "Midwest"},
        {"state": "OK", "name": "Oklahoma", "pop": 4.0, "lat": 35.6, "lon": -97.4, "region": "South"},
        {"state": "OR", "name": "Oregon", "pop": 4.2, "lat": 44.0, "lon": -120.5, "region": "West"},
        {"state": "PA", "name": "Pennsylvania", "pop": 13.0, "lat": 41.2, "lon": -77.8, "region": "Northeast"},
        {"state": "RI", "name": "Rhode Island", "pop": 1.1, "lat": 41.4, "lon": -70.4, "region": "Northeast"},
        {"state": "SC", "name": "S. Carolina", "pop": 5.4, "lat": 34.0, "lon": -81.0, "region": "South"},
        {"state": "SD", "name": "S. Dakota", "pop": 0.9, "lat": 44.4, "lon": -100.2, "region": "Midwest"},
        {"state": "TN", "name": "Tennessee", "pop": 7.1, "lat": 35.8, "lon": -86.3, "region": "South"},
        {"state": "TX", "name": "Texas", "pop": 30.5, "lat": 31.5, "lon": -99.4, "region": "South"},
        {"state": "UT", "name": "Utah", "pop": 3.4, "lat": 39.3, "lon": -111.7, "region": "West"},
        {"state": "VT", "name": "Vermont", "pop": 0.6, "lat": 44.1, "lon": -72.6, "region": "Northeast"},
        {"state": "VA", "name": "Virginia", "pop": 8.6, "lat": 37.5, "lon": -78.9, "region": "South"},
        {"state": "WA", "name": "Washington", "pop": 7.8, "lat": 47.4, "lon": -120.5, "region": "West"},
        {"state": "WV", "name": "W. Virginia", "pop": 1.8, "lat": 38.6, "lon": -80.6, "region": "South"},
        {"state": "WI", "name": "Wisconsin", "pop": 5.9, "lat": 44.6, "lon": -89.8, "region": "Midwest"},
        {"state": "WY", "name": "Wyoming", "pop": 0.6, "lat": 43.0, "lon": -107.5, "region": "West"},
    ]
)

# Compute rank for storytelling emphasis
states = states.sort_values("pop", ascending=False).reset_index(drop=True)
states["rank"] = states.index + 1
states["pop_label"] = states["pop"].apply(lambda x: f"{x:.1f}M")

# Reference map background (faint outlines for geographic context)
us_topo_url = "https://cdn.jsdelivr.net/npm/vega-datasets@2/data/us-10m.json"
us_states = alt.topo_feature(us_topo_url, "states")

# Region color palette (colorblind-safe, refined hues)
region_order = ["Northeast", "Midwest", "South", "West"]
region_colors = ["#306998", "#D4A934", "#C75B28", "#3A8A5C"]

# Background reference map - very subtle for context
background = (
    alt.Chart(us_states)
    .mark_geoshape(fill="#F5F5F2", stroke="#D8D8D5", strokeWidth=0.5)
    .project(type="albersUsa")
    .properties(width=1600, height=900)
)

# Top 5 states highlighted with stronger stroke
top5 = states.head(5)
other = states.iloc[5:]

# Dorling cartogram - main circles
circles_main = (
    alt.Chart(other)
    .mark_circle(opacity=0.82, stroke="#FFFFFF", strokeWidth=1.5)
    .encode(
        longitude="lon:Q",
        latitude="lat:Q",
        size=alt.Size(
            "pop:Q",
            scale=alt.Scale(domain=[0.5, 40], range=[200, 6000]),
            legend=alt.Legend(
                title="Population (millions)",
                titleFontSize=18,
                titleFont="Helvetica Neue, Arial",
                labelFontSize=16,
                labelFont="Helvetica Neue, Arial",
                symbolFillColor="#306998",
                symbolStrokeColor="#FFFFFF",
                orient="bottom-right",
                offset=20,
                titleLimit=280,
                values=[1, 5, 10, 20],
            ),
        ),
        color=alt.Color(
            "region:N",
            scale=alt.Scale(domain=region_order, range=region_colors),
            legend=alt.Legend(
                title="Region",
                titleFontSize=18,
                titleFont="Helvetica Neue, Arial",
                labelFontSize=16,
                labelFont="Helvetica Neue, Arial",
                symbolSize=500,
                symbolStrokeWidth=0,
                orient="bottom-left",
                offset=20,
            ),
        ),
        tooltip=[
            alt.Tooltip("name:N", title="State"),
            alt.Tooltip("pop:Q", title="Population (M)", format=".1f"),
            alt.Tooltip("region:N", title="Region"),
        ],
    )
    .project(type="albersUsa")
)

# Top 5 states with emphasized strokes
circles_top5 = (
    alt.Chart(top5)
    .mark_circle(opacity=0.9, stroke="#333333", strokeWidth=2.5)
    .encode(
        longitude="lon:Q",
        latitude="lat:Q",
        size=alt.Size("pop:Q", scale=alt.Scale(domain=[0.5, 40], range=[200, 6000]), legend=None),
        color=alt.Color("region:N", scale=alt.Scale(domain=region_order, range=region_colors), legend=None),
        tooltip=[
            alt.Tooltip("name:N", title="State"),
            alt.Tooltip("pop:Q", title="Population (M)", format=".1f"),
            alt.Tooltip("region:N", title="Region"),
        ],
    )
    .project(type="albersUsa")
)

# State abbreviation labels - larger font, only for states >= 4M
labeled_states = states[states["pop"] >= 4.0].copy()
labels = (
    alt.Chart(labeled_states)
    .mark_text(fontSize=17, fontWeight="bold", color="#FFFFFF", font="Helvetica Neue, Arial")
    .encode(longitude="lon:Q", latitude="lat:Q", text="state:N")
    .project(type="albersUsa")
)

# Population values under labels for top 5 states
pop_labels = (
    alt.Chart(top5)
    .mark_text(fontSize=13, color="#FFFFFF", font="Helvetica Neue, Arial", dy=16, fontStyle="italic")
    .encode(longitude="lon:Q", latitude="lat:Q", text="pop_label:N")
    .project(type="albersUsa")
)

# Annotation text - key insight about population concentration
annotation_data = pd.DataFrame([{"text": "Top 5 states hold 37% of the US population", "lat": 26.0, "lon": -105.0}])
annotation = (
    alt.Chart(annotation_data)
    .mark_text(fontSize=16, font="Helvetica Neue, Arial", fontStyle="italic", color="#555555", align="left")
    .encode(longitude="lon:Q", latitude="lat:Q", text="text:N")
    .project(type="albersUsa")
)

# Combine all layers
chart = (
    (background + circles_main + circles_top5 + labels + pop_labels + annotation)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            text="US States by Population · cartogram-area-distortion · altair · pyplots.ai",
            subtitle="Circle area proportional to state population — darker outlines mark the five most populous states",
            fontSize=28,
            subtitleFontSize=17,
            subtitleColor="#777777",
            anchor="middle",
            font="Helvetica Neue, Arial",
            subtitleFont="Helvetica Neue, Arial",
        ),
    )
    .configure_view(strokeWidth=0)
    .configure(background="#FAFAF8")
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
