""" pyplots.ai
map-route-path: Route Path Map
Library: plotly 6.5.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-19
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data: Simulated hiking trail in the Swiss Alps region
np.random.seed(42)

# Starting point near Zermatt, Switzerland
start_lat, start_lon = 46.01, 7.75
n_points = 150

# Generate a realistic hiking path with gradual progression
t = np.linspace(0, 1, n_points)

# Create a winding path heading generally northeast
lat_drift = 0.08 * t + 0.015 * np.sin(8 * np.pi * t)
lon_drift = 0.12 * t + 0.02 * np.sin(6 * np.pi * t)

# Add small random variations for realism
lat = start_lat + lat_drift + np.cumsum(np.random.randn(n_points) * 0.001)
lon = start_lon + lon_drift + np.cumsum(np.random.randn(n_points) * 0.001)

# Time stamps over a 4-hour hike
timestamps = pd.date_range("2024-07-15 08:00", periods=n_points, freq="96s")

# Create DataFrame
df = pd.DataFrame({"lat": lat, "lon": lon, "sequence": range(n_points), "timestamp": timestamps})

# Create the map figure
fig = go.Figure()

# Add the route path as a line with color gradient segments
for i in range(len(df) - 1):
    progress = i / (len(df) - 1)
    # Color gradient from blue (start) to red (end)
    r = int(48 + (220 - 48) * progress)
    g = int(105 - 80 * progress)
    b = int(152 - 100 * progress)
    color = f"rgb({r},{g},{b})"

    fig.add_trace(
        go.Scattermap(
            lat=[df["lat"].iloc[i], df["lat"].iloc[i + 1]],
            lon=[df["lon"].iloc[i], df["lon"].iloc[i + 1]],
            mode="lines",
            line=dict(width=4, color=color),
            hoverinfo="skip",
            showlegend=False,
        )
    )

# Add start marker (green)
fig.add_trace(
    go.Scattermap(
        lat=[df["lat"].iloc[0]],
        lon=[df["lon"].iloc[0]],
        mode="markers+text",
        marker=dict(size=20, color="#2ECC71"),
        text=["Start"],
        textposition="top center",
        textfont=dict(size=16, color="#2ECC71"),
        name="Start",
        hovertemplate="<b>Start</b><br>Lat: %{lat:.4f}<br>Lon: %{lon:.4f}<br>Time: 08:00<extra></extra>",
    )
)

# Add end marker (red)
fig.add_trace(
    go.Scattermap(
        lat=[df["lat"].iloc[-1]],
        lon=[df["lon"].iloc[-1]],
        mode="markers+text",
        marker=dict(size=20, color="#E74C3C"),
        text=["End"],
        textposition="top center",
        textfont=dict(size=16, color="#E74C3C"),
        name="End",
        hovertemplate="<b>End</b><br>Lat: %{lat:.4f}<br>Lon: %{lon:.4f}<br>Time: 12:00<extra></extra>",
    )
)

# Add waypoint markers at intervals
interval = 30
waypoints = df.iloc[interval::interval]
fig.add_trace(
    go.Scattermap(
        lat=waypoints["lat"],
        lon=waypoints["lon"],
        mode="markers",
        marker=dict(size=10, color="#FFD43B", opacity=0.9),
        name="Waypoints",
        hovertemplate="<b>Waypoint %{text}</b><br>Lat: %{lat:.4f}<br>Lon: %{lon:.4f}<extra></extra>",
        text=[str(i) for i in waypoints["sequence"]],
    )
)

# Calculate center and zoom
center_lat = df["lat"].mean()
center_lon = df["lon"].mean()

# Update layout with map settings
fig.update_layout(
    title=dict(
        text="Alpine Hiking Trail · map-route-path · plotly · pyplots.ai",
        font=dict(size=28, color="#333333"),
        x=0.5,
        xanchor="center",
    ),
    map=dict(style="open-street-map", center=dict(lat=center_lat, lon=center_lon), zoom=10.5),
    margin=dict(l=20, r=20, t=80, b=20),
    legend=dict(
        x=0.01,
        y=0.99,
        xanchor="left",
        yanchor="top",
        bgcolor="rgba(255, 255, 255, 0.9)",
        bordercolor="#CCCCCC",
        borderwidth=1,
        font=dict(size=16),
    ),
    template="plotly_white",
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
