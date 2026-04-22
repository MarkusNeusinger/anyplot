""" pyplots.ai
map-animated-temporal: Animated Map over Time
Library: plotly 6.5.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
import plotly.express as px


# Data: Simulated earthquake aftershock sequence spreading from epicenter
np.random.seed(42)

# Generate 15 time steps (days) of aftershock data
n_days = 15
points_per_day = 30

# Epicenter location (off coast of Japan)
epicenter_lat, epicenter_lon = 38.3, 142.4

data = []
for day in range(n_days):
    n_points = points_per_day + np.random.randint(-10, 15)

    # Aftershocks spread outward over time with decreasing intensity
    spread = 0.5 + day * 0.3  # Increasing spread radius
    intensity_decay = 1.0 - day * 0.05  # Decreasing magnitude

    for _ in range(n_points):
        # Random angle and distance from epicenter
        angle = np.random.uniform(0, 2 * np.pi)
        distance = np.abs(np.random.normal(0, spread))

        lat = epicenter_lat + distance * np.cos(angle)
        lon = epicenter_lon + distance * np.sin(angle)

        # Magnitude decreases over time with random variation
        magnitude = max(2.0, np.random.exponential(2.5) * intensity_decay)

        data.append(
            {
                "lat": lat,
                "lon": lon,
                "day": f"Day {day + 1:02d}",
                "magnitude": magnitude,
                "depth_km": np.random.uniform(5, 50),
            }
        )

df = pd.DataFrame(data)

# Create animated scatter geo map
fig = px.scatter_geo(
    df,
    lat="lat",
    lon="lon",
    size="magnitude",
    color="magnitude",
    animation_frame="day",
    hover_data={"lat": ":.2f", "lon": ":.2f", "magnitude": ":.1f", "depth_km": ":.1f"},
    color_continuous_scale="YlOrRd",
    size_max=25,
    opacity=0.7,
)

# Update layout for large canvas and styling
fig.update_layout(
    title={
        "text": "Earthquake Aftershock Sequence · map-animated-temporal · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#333333"},
        "x": 0.5,
        "xanchor": "center",
    },
    geo={
        "scope": "asia",
        "center": {"lat": epicenter_lat, "lon": epicenter_lon},
        "projection_scale": 4,
        "showland": True,
        "landcolor": "#f0f0f0",
        "showocean": True,
        "oceancolor": "#d4e6f1",
        "showcountries": True,
        "countrycolor": "#888888",
        "countrywidth": 1,
        "showcoastlines": True,
        "coastlinecolor": "#555555",
        "coastlinewidth": 1.5,
        "showlakes": True,
        "lakecolor": "#d4e6f1",
    },
    coloraxis_colorbar={
        "title": {"text": "Magnitude", "font": {"size": 18}}, "tickfont": {"size": 14}, "len": 0.6, "thickness": 20
    },
    margin={"l": 20, "r": 20, "t": 80, "b": 20},
    paper_bgcolor="white",
    updatemenus=[
        {
            "type": "buttons",
            "showactive": True,
            "y": 0.02,
            "x": 0.1,
            "xanchor": "left",
            "buttons": [
                {
                    "label": "▶ Play",
                    "method": "animate",
                    "args": [
                        None,
                        {
                            "frame": {"duration": 800, "redraw": True},
                            "fromcurrent": True,
                            "transition": {"duration": 300, "easing": "cubic-in-out"},
                        },
                    ],
                },
                {
                    "label": "⏸ Pause",
                    "method": "animate",
                    "args": [
                        [None],
                        {"frame": {"duration": 0, "redraw": False}, "mode": "immediate", "transition": {"duration": 0}},
                    ],
                },
            ],
            "font": {"size": 14},
            "bgcolor": "#ffffff",
            "bordercolor": "#cccccc",
        }
    ],
    sliders=[
        {
            "active": 0,
            "yanchor": "top",
            "xanchor": "left",
            "currentvalue": {"font": {"size": 16}, "prefix": "Time: ", "visible": True, "xanchor": "center"},
            "transition": {"duration": 300, "easing": "cubic-in-out"},
            "pad": {"b": 10, "t": 50},
            "len": 0.8,
            "x": 0.1,
            "y": 0,
            "steps": [
                {
                    "args": [
                        [f"Day {i + 1:02d}"],
                        {"frame": {"duration": 300, "redraw": True}, "mode": "immediate", "transition": {"duration": 300}},
                    ],
                    "label": f"Day {i + 1}",
                    "method": "animate",
                }
                for i in range(n_days)
            ],
        }
    ],
)

# Update marker styling
fig.update_traces(marker={"line": {"width": 1, "color": "#333333"}})

# Save static PNG (first frame)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML with animation
fig.write_html("plot.html", include_plotlyjs="cdn", full_html=True)
