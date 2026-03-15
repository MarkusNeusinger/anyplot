""" pyplots.ai
area-elevation-profile: Terrain Elevation Profile Along Transect
Library: plotly 6.6.0 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-15
"""

import numpy as np
import plotly.graph_objects as go


# Data
np.random.seed(42)

distance = np.linspace(0, 120, 300)

keypoints_dist = [0, 10, 18, 28, 35, 45, 58, 68, 82, 92, 100, 110, 120]
keypoints_elev = [1034, 1200, 2265, 1800, 2681, 1900, 2076, 1400, 1100, 1600, 2061, 1500, 1274]
elevation = np.interp(distance, keypoints_dist, keypoints_elev)
noise = np.random.normal(0, 12, len(distance))
elevation = elevation + noise

landmarks = [
    {"name": "Grindelwald\n1,034 m", "distance": 0.0, "elevation": 1034},
    {"name": "Bachalpsee\n2,265 m", "distance": 18.0, "elevation": 2265},
    {"name": "Faulhorn\n2,681 m", "distance": 35.0, "elevation": 2681},
    {"name": "Schynige Platte\n2,076 m", "distance": 58.0, "elevation": 2076},
    {"name": "Männlichen\n1,100 m", "distance": 82.0, "elevation": 1100},
    {"name": "Kleine Scheidegg\n2,061 m", "distance": 100.0, "elevation": 2061},
    {"name": "Wengen\n1,274 m", "distance": 120.0, "elevation": 1274},
]

# Plot
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=distance,
        y=elevation,
        fill="tozeroy",
        fillcolor="rgba(48, 105, 152, 0.25)",
        line={"color": "#306998", "width": 3},
        mode="lines",
        name="Elevation",
        hovertemplate="Distance: %{x:.1f} km<br>Elevation: %{y:.0f} m<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=[lm["distance"] for lm in landmarks],
        y=[lm["elevation"] for lm in landmarks],
        mode="markers",
        marker={"size": 14, "color": "#306998", "line": {"color": "white", "width": 2}, "symbol": "circle"},
        name="Landmarks",
        hovertemplate="%{text}<br>Distance: %{x:.1f} km<br>Elevation: %{y:.0f} m<extra></extra>",
        text=[lm["name"].split("\n")[0] for lm in landmarks],
    )
)

annotations = []
for lm in landmarks:
    fig.add_shape(
        type="line",
        x0=lm["distance"],
        x1=lm["distance"],
        y0=0,
        y1=lm["elevation"],
        line={"color": "rgba(48, 105, 152, 0.3)", "width": 1.5, "dash": "dot"},
    )
    annotations.append(
        {
            "x": lm["distance"],
            "y": lm["elevation"] + 60,
            "text": f"<b>{lm['name'].split(chr(10))[0]}</b>",
            "showarrow": True,
            "arrowhead": 0,
            "arrowwidth": 1.5,
            "arrowcolor": "rgba(48, 105, 152, 0.5)",
            "ax": 0,
            "ay": -35,
            "font": {"size": 14, "color": "#333333"},
            "align": "center",
            "yanchor": "bottom",
        }
    )

# Style
fig.update_layout(
    title={
        "text": "Bernese Oberland Traverse · area-elevation-profile · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#333333"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Distance (km)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "range": [-2, 125],
        "showgrid": False,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "Elevation (m)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "range": [0, 3100],
        "gridcolor": "rgba(0, 0, 0, 0.08)",
        "gridwidth": 1,
        "zeroline": False,
    },
    template="plotly_white",
    showlegend=False,
    annotations=annotations,
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
    plot_bgcolor="white",
    paper_bgcolor="white",
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
