"""anyplot.ai
map-route-path: Route Path Map
Library: plotly | Python
"""

import os
import sys


# Remove this script's directory from sys.path so 'plotly' resolves to the
# installed package, not this file (which shares the name).
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _here]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import plotly.graph_objects as go  # noqa: E402


THEME = os.getenv("ANYPLOT_THEME", "light")

PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito: position 1 = start, position 2 = end, position 3 = waypoints
START_COLOR = "#009E73"
END_COLOR = "#D55E00"
WAYPOINT_COLOR = "#0072B2"

# Data: Appalachian Trail section through Great Smoky Mountains, Tennessee
np.random.seed(42)

start_lat, start_lon = 35.6127, -83.4254  # Newfound Gap, TN
n_points = 300

t = np.linspace(0, 1, n_points)

# Trail winds northeast with characteristic Smoky Mountain undulations
lat_drift = 0.15 * t + 0.018 * np.sin(12 * np.pi * t) + 0.009 * np.sin(5 * np.pi * t)
lon_drift = 0.20 * t + 0.022 * np.sin(8 * np.pi * t) + 0.012 * np.cos(4 * np.pi * t)

lat = start_lat + lat_drift + np.cumsum(np.random.randn(n_points) * 0.0007)
lon = start_lon + lon_drift + np.cumsum(np.random.randn(n_points) * 0.0007)

timestamps = pd.date_range("2024-09-14 07:30", periods=n_points, freq="72s")

df = pd.DataFrame({"lat": lat, "lon": lon, "sequence": range(n_points), "timestamp": timestamps})

fig = go.Figure()

# Viridis colormap key stops for continuous path gradient
_VIRIDIS = [
    (0.00, (68, 1, 84)),
    (0.25, (59, 82, 139)),
    (0.50, (33, 145, 140)),
    (0.75, (94, 201, 98)),
    (1.00, (253, 231, 37)),
]


def viridis_color(t):
    for i in range(len(_VIRIDIS) - 1):
        t0, c0 = _VIRIDIS[i]
        t1, c1 = _VIRIDIS[i + 1]
        if t <= t1:
            f = (t - t0) / (t1 - t0)
            r = int(c0[0] + f * (c1[0] - c0[0]))
            g = int(c0[1] + f * (c1[1] - c0[1]))
            b = int(c0[2] + f * (c1[2] - c0[2]))
            return f"rgb({r},{g},{b})"
    return f"rgb{_VIRIDIS[-1][1]}"


# Route path with viridis gradient to show time progression (continuous data)
for i in range(len(df) - 1):
    progress = i / (len(df) - 1)
    color = viridis_color(progress)
    fig.add_trace(
        go.Scattermap(
            lat=[df["lat"].iloc[i], df["lat"].iloc[i + 1]],
            lon=[df["lon"].iloc[i], df["lon"].iloc[i + 1]],
            mode="lines",
            line={"width": 3, "color": color},
            hoverinfo="skip",
            showlegend=False,
        )
    )

# Start marker — Okabe-Ito position 1 (bluish green)
fig.add_trace(
    go.Scattermap(
        lat=[df["lat"].iloc[0]],
        lon=[df["lon"].iloc[0]],
        mode="markers+text",
        marker={"size": 18, "color": START_COLOR},
        text=["Start"],
        textposition="top center",
        textfont={"size": 13, "color": START_COLOR},
        name="Start (Newfound Gap)",
        hovertemplate="<b>Start — Newfound Gap</b><br>Lat: %{lat:.4f}<br>Lon: %{lon:.4f}<br>Time: 07:30<extra></extra>",
    )
)

# End marker — Okabe-Ito position 2 (vermillion)
fig.add_trace(
    go.Scattermap(
        lat=[df["lat"].iloc[-1]],
        lon=[df["lon"].iloc[-1]],
        mode="markers+text",
        marker={"size": 18, "color": END_COLOR},
        text=["End"],
        textposition="top center",
        textfont={"size": 13, "color": END_COLOR},
        name="End (Mt. Kephart area)",
        hovertemplate="<b>End — Mt. Kephart area</b><br>Lat: %{lat:.4f}<br>Lon: %{lon:.4f}<br>Time: 13:30<extra></extra>",
    )
)

# Waypoints at regular intervals — Okabe-Ito position 3 (blue)
interval = 75
waypoints = df.iloc[interval::interval]
wp_labels = [
    f"{int(row.timestamp.strftime('%H')) % 12 or 12}:{row.timestamp.strftime('%M')}" for _, row in waypoints.iterrows()
]
fig.add_trace(
    go.Scattermap(
        lat=waypoints["lat"],
        lon=waypoints["lon"],
        mode="markers",
        marker={"size": 10, "color": WAYPOINT_COLOR, "opacity": 0.9},
        name="Checkpoints",
        hovertemplate="<b>Checkpoint at %{text}</b><br>Lat: %{lat:.4f}<br>Lon: %{lon:.4f}<extra></extra>",
        text=wp_labels,
    )
)

center_lat = df["lat"].mean()
center_lon = df["lon"].mean()

fig.update_layout(
    autosize=False,
    title={
        "text": "map-route-path · python · plotly · anyplot.ai", "font": {"size": 16, "color": INK}, "x": 0.5, "xanchor": "center"
    },
    map={"style": "open-street-map", "center": {"lat": center_lat, "lon": center_lon}, "zoom": 10},
    paper_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 20, "r": 20, "t": 60, "b": 20},
    legend={
        "x": 0.01,
        "y": 0.99,
        "xanchor": "left",
        "yanchor": "top",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "font": {"size": 12, "color": INK_SOFT},
    },
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn", full_html=True)
