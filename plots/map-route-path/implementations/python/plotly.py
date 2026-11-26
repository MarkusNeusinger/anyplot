"""anyplot.ai
map-route-path: Route Path Map
Library: plotly 6.7.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-21
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

# Imprint palette: position 1 = start, position 2 = end, position 3 = checkpoints
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential ramp for marks (colored points on the page), low -> high
SEQ_MARKS = (
    [[0.0, "#009E73"], [0.338, "#4467A3"], [1.0, "#002850"]]
    if THEME == "light"
    else [[0.0, "#007755"], [0.32, "#009E73"], [1.0, "#CDD9FF"]]
)

# Columns: set these to your table's column names
LAT = "Latitude"  # role: lat
LON = "Longitude"  # role: lon
SEQUENCE = "Sequence"  # role: sequence
TIMESTAMP = "Time"  # role: timestamp

# Data: Appalachian Trail section through Great Smoky Mountains, Tennessee.
# Replace this block with your own table, for example df = pd.read_csv("track.csv")
np.random.seed(42)
n_points = 300
t = np.linspace(0, 1, n_points)

# Trail winds northeast with gentle undulations and small GPS noise
lat_drift = 0.15 * t + 0.005 * np.sin(3 * np.pi * t) + 0.003 * np.sin(4 * np.pi * t)
lon_drift = 0.20 * t + 0.006 * np.sin(3 * np.pi * t) + 0.004 * np.cos(4 * np.pi * t)
lat = 35.6127 + lat_drift + np.cumsum(np.random.randn(n_points) * 0.0002)
lon = -83.4254 + lon_drift + np.cumsum(np.random.randn(n_points) * 0.0002)

df = pd.DataFrame(
    {
        LAT: lat,
        LON: lon,
        SEQUENCE: range(n_points),
        TIMESTAMP: pd.date_range("2024-09-14 07:30", periods=n_points, freq="72s"),
    }
)

# Plot: reads only df and the constants above
START_COLOR, END_COLOR, WAYPOINT_COLOR = IMPRINT_PALETTE[0], IMPRINT_PALETTE[1], IMPRINT_PALETTE[2]
timestamps = df[TIMESTAMP]
last = len(df) - 1
t_values = df[SEQUENCE].to_numpy(dtype=float)
tick_idx = np.linspace(0, last, 5).round().astype(int)
start_label = timestamps.iloc[0].strftime("%H:%M")
end_label = timestamps.iloc[-1].strftime("%H:%M")

fig = go.Figure()

# Thin route line for path connectivity
fig.add_trace(
    go.Scattermap(
        lat=df[LAT],
        lon=df[LON],
        mode="lines",
        line={"width": 3, "color": INK_SOFT},
        opacity=0.65,
        hoverinfo="skip",
        showlegend=False,
    )
)

# Single marker trace with Imprint marks ramp for time progression; colorbar provides the time scale
hover_times = [ts.strftime("%H:%M") for ts in timestamps]
fig.add_trace(
    go.Scattermap(
        lat=df[LAT],
        lon=df[LON],
        mode="markers",
        marker={
            "size": 8,
            "color": t_values,
            "colorscale": SEQ_MARKS,
            "showscale": True,
            "colorbar": {
                "title": {"text": "Time", "font": {"size": 13, "color": INK}},
                "tickvals": tick_idx,
                "ticktext": [timestamps.iloc[i].strftime("%H:%M") for i in tick_idx],
                "tickfont": {"size": 12, "color": INK_SOFT},
                "bgcolor": ELEVATED_BG,
                "bordercolor": INK_SOFT,
                "borderwidth": 1,
                "len": 0.5,
                "thickness": 15,
            },
        },
        hovertemplate="<b>%{text}</b><br>Lat: %{lat:.4f}<br>Lon: %{lon:.4f}<extra></extra>",
        text=hover_times,
        showlegend=False,
    )
)

# Start marker — Imprint position 1
fig.add_trace(
    go.Scattermap(
        lat=[df[LAT].iloc[0]],
        lon=[df[LON].iloc[0]],
        mode="markers+text",
        marker={"size": 18, "color": START_COLOR},
        text=["Start"],
        textposition="bottom center",
        textfont={"size": 14, "color": INK},
        name="Start (Newfound Gap)",
        hovertemplate="<b>Start — Newfound Gap</b><br>Lat: %{lat:.4f}<br>Lon: %{lon:.4f}<br>Time: "
        + start_label
        + "<extra></extra>",
    )
)

# End marker — Imprint position 2
fig.add_trace(
    go.Scattermap(
        lat=[df[LAT].iloc[-1]],
        lon=[df[LON].iloc[-1]],
        mode="markers+text",
        marker={"size": 18, "color": END_COLOR},
        text=["End"],
        textposition="top center",
        textfont={"size": 14, "color": INK},
        name="End (Mt. Kephart area)",
        hovertemplate="<b>End — Mt. Kephart area</b><br>Lat: %{lat:.4f}<br>Lon: %{lon:.4f}<br>Time: "
        + end_label
        + "<extra></extra>",
    )
)

# Waypoints at regular intervals — Imprint position 3
interval = len(df) // 4
waypoints = df.iloc[interval::interval]
wp_labels = [
    f"{int(row[TIMESTAMP].strftime('%H')) % 12 or 12}:{row[TIMESTAMP].strftime('%M')}"
    for _, row in waypoints.iterrows()
]
fig.add_trace(
    go.Scattermap(
        lat=waypoints[LAT],
        lon=waypoints[LON],
        mode="markers",
        marker={"size": 12, "color": WAYPOINT_COLOR, "opacity": 0.9},
        name="Checkpoints",
        hovertemplate="<b>Checkpoint at %{text}</b><br>Lat: %{lat:.4f}<br>Lon: %{lon:.4f}<extra></extra>",
        text=wp_labels,
    )
)

center_lat = df[LAT].mean()
center_lon = df[LON].mean()

# Use dark tiles for dark theme to maintain visual coherence with dark chrome
map_style = "carto-darkmatter" if THEME == "dark" else "open-street-map"

fig.update_layout(
    autosize=False,
    title={
        "text": "map-route-path · python · plotly · anyplot.ai",
        "font": {"size": 18, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    map={"style": map_style, "center": {"lat": center_lat, "lon": center_lon}, "zoom": 10},
    paper_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 20, "r": 90, "t": 60, "b": 20},
    legend={
        "x": 0.01,
        "y": 0.99,
        "xanchor": "left",
        "yanchor": "top",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "font": {"size": 13, "color": INK_SOFT},
    },
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn", full_html=True)
