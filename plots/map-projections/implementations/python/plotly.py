""" pyplots.ai
map-projections: World Map with Different Projections
Library: plotly 6.5.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-20
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Define projections to showcase
projections = [
    {"name": "Mercator", "type": "mercator"},
    {"name": "Robinson", "type": "robinson"},
    {"name": "Mollweide", "type": "mollweide"},
    {"name": "Orthographic", "type": "orthographic"},
    {"name": "Equal Earth", "type": "equal earth"},
    {"name": "Natural Earth", "type": "natural earth"},
]

# Create subplot figure with 2 rows, 3 columns
fig = make_subplots(
    rows=2,
    cols=3,
    subplot_titles=[p["name"] for p in projections],
    specs=[[{"type": "geo"}, {"type": "geo"}, {"type": "geo"}], [{"type": "geo"}, {"type": "geo"}, {"type": "geo"}]],
    horizontal_spacing=0.02,
    vertical_spacing=0.08,
)

# Add each projection as a separate geo subplot
for idx, proj in enumerate(projections):
    row = idx // 3 + 1
    col = idx % 3 + 1
    geo_key = f"geo{idx + 1}" if idx > 0 else "geo"

    # Add an empty scattergeo trace to create the map
    fig.add_trace(go.Scattergeo(lon=[], lat=[], mode="markers", showlegend=False, geo=geo_key), row=row, col=col)

    # Configure the geo layout for this subplot
    fig.update_geos(
        selector={"geo": geo_key} if idx > 0 else None,
        projection_type=proj["type"],
        showland=True,
        landcolor="#306998",
        showocean=True,
        oceancolor="#E8F4F8",
        showcoastlines=True,
        coastlinecolor="#1A3D5C",
        coastlinewidth=1.5,
        showcountries=True,
        countrycolor="#1A3D5C",
        countrywidth=0.8,
        showlakes=True,
        lakecolor="#E8F4F8",
        showframe=True,
        framecolor="#333333",
        framewidth=1,
        lataxis={"showgrid": True, "gridcolor": "#FFD43B", "gridwidth": 1, "dtick": 30},
        lonaxis={"showgrid": True, "gridcolor": "#FFD43B", "gridwidth": 1, "dtick": 30},
        bgcolor="rgba(0,0,0,0)",
    )

# Update each geo individually
for idx, proj in enumerate(projections):
    geo_key = f"geo{idx + 1}" if idx > 0 else "geo"
    update_dict = {
        geo_key: {
            "projection_type": proj["type"],
            "showland": True,
            "landcolor": "#306998",
            "showocean": True,
            "oceancolor": "#E8F4F8",
            "showcoastlines": True,
            "coastlinecolor": "#1A3D5C",
            "coastlinewidth": 1.5,
            "showcountries": True,
            "countrycolor": "#1A3D5C",
            "countrywidth": 0.8,
            "showlakes": True,
            "lakecolor": "#E8F4F8",
            "showframe": True,
            "framecolor": "#333333",
            "framewidth": 1,
            "lataxis": {"showgrid": True, "gridcolor": "#FFD43B", "gridwidth": 1, "dtick": 30},
            "lonaxis": {"showgrid": True, "gridcolor": "#FFD43B", "gridwidth": 1, "dtick": 30},
            "bgcolor": "rgba(0,0,0,0)",
        }
    }
    fig.update_layout(**update_dict)

# Update overall layout
fig.update_layout(
    title={
        "text": "map-projections · plotly · pyplots.ai",
        "font": {"size": 32, "color": "#333333"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.98,
    },
    showlegend=False,
    paper_bgcolor="white",
    plot_bgcolor="white",
    margin={"l": 20, "r": 20, "t": 100, "b": 40},
)

# Update subplot titles font size
fig.update_annotations(font={"size": 22, "color": "#333333"})

# Save as PNG
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs="cdn")
