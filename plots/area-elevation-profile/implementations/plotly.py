""" pyplots.ai
area-elevation-profile: Terrain Elevation Profile Along Transect
Library: plotly 6.6.0 | Python 3.14.3
Quality: 94/100 | Created: 2026-03-15
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

# Compute slope for color-mapped line
slope = np.gradient(elevation, distance)
abs_slope = np.abs(slope)

landmarks = [
    {"name": "Grindelwald", "distance": 0.0, "elevation": 1034},
    {"name": "Bachalpsee", "distance": 18.0, "elevation": 2265},
    {"name": "Faulhorn", "distance": 35.0, "elevation": 2681},
    {"name": "Schynige Platte", "distance": 58.0, "elevation": 2076},
    {"name": "Männlichen", "distance": 82.0, "elevation": 1100},
    {"name": "Kleine Scheidegg", "distance": 100.0, "elevation": 2061},
    {"name": "Wengen", "distance": 120.0, "elevation": 1274},
]

# Vertical exaggeration: ratio of horizontal to vertical scale on screen
# Plot area ~1480x760px for 1600x900 canvas; x=127km, y=3.2km
plot_h_px, plot_w_px = 760, 1480
x_range_m = 127 * 1000  # meters
y_range_m = 3200  # meters
vert_exag_display = round((x_range_m / plot_w_px) / (y_range_m / plot_h_px), 0)

# Plot
fig = go.Figure()

# Area fill with gradient using fillgradient (Plotly-distinctive feature)
fig.add_trace(
    go.Scatter(
        x=distance,
        y=elevation,
        fill="tozeroy",
        fillgradient={
            "type": "vertical",
            "colorscale": [
                [0.0, "rgba(34, 85, 130, 0.08)"],
                [0.4, "rgba(48, 105, 152, 0.20)"],
                [0.7, "rgba(48, 105, 152, 0.35)"],
                [1.0, "rgba(48, 105, 152, 0.50)"],
            ],
        },
        line={"color": "#306998", "width": 3},
        mode="lines",
        name="Elevation",
        hovertemplate="Distance: %{x:.1f} km<br>Elevation: %{y:.0f} m<extra></extra>",
    )
)

# Slope-colored segments as overlay for visual storytelling
# Colorblind-safe palette: blue (gentle), orange (moderate), dark purple (steep)
slope_palette = {"gentle": "#306998", "moderate": "#d4820a", "steep": "#7b2d8e"}

slope_labels = []
for s in abs_slope:
    if s < 15:
        slope_labels.append("gentle")
    elif s < 35:
        slope_labels.append("moderate")
    else:
        slope_labels.append("steep")

# Group consecutive segments with same slope category to reduce trace count
i = 0
while i < len(distance) - 1:
    label = slope_labels[i]
    j = i + 1
    while j < len(distance) - 1 and slope_labels[j] == label:
        j += 1
    fig.add_trace(
        go.Scatter(
            x=distance[i : j + 1],
            y=elevation[i : j + 1],
            mode="lines",
            line={"color": slope_palette[label], "width": 3.5},
            showlegend=False,
            hoverinfo="skip",
        )
    )
    i = j

# Landmark markers
fig.add_trace(
    go.Scatter(
        x=[lm["distance"] for lm in landmarks],
        y=[lm["elevation"] for lm in landmarks],
        mode="markers",
        marker={"size": 16, "color": "#306998", "line": {"color": "white", "width": 2.5}, "symbol": "circle"},
        name="Landmarks",
        hovertemplate="%{text}<br>Distance: %{x:.1f} km<br>Elevation: %{y:.0f} m<extra></extra>",
        text=[lm["name"] for lm in landmarks],
    )
)

# Annotations with elevation values
annotations = []
offsets_y = [50, 50, 50, 50, -50, 50, 50]
anchors_y = ["bottom", "bottom", "bottom", "bottom", "top", "bottom", "bottom"]
arrow_ay = [-40, -40, -40, -40, 40, -40, -40]
# Horizontal shifts to avoid edge crowding for Grindelwald (first) and Wengen (last)
anchors_x = ["left", "center", "center", "center", "center", "center", "right"]

for i, lm in enumerate(landmarks):
    # Vertical reference line
    fig.add_shape(
        type="line",
        x0=lm["distance"],
        x1=lm["distance"],
        y0=0,
        y1=lm["elevation"],
        line={"color": "rgba(48, 105, 152, 0.25)", "width": 1.5, "dash": "dot"},
    )
    # Annotation with name AND elevation
    annotations.append(
        {
            "x": lm["distance"],
            "y": lm["elevation"] + offsets_y[i],
            "text": f"<b>{lm['name']}</b><br>{lm['elevation']:,} m",
            "showarrow": True,
            "arrowhead": 0,
            "arrowwidth": 1.5,
            "arrowcolor": "rgba(48, 105, 152, 0.4)",
            "ax": 0,
            "ay": arrow_ay[i],
            "font": {"size": 16, "color": "#2a2a2a"},
            "align": "center",
            "xanchor": anchors_x[i],
            "yanchor": anchors_y[i],
        }
    )

# Vertical exaggeration note (fix SC-02)
annotations.append(
    {
        "x": 1.0,
        "y": 0.0,
        "xref": "paper",
        "yref": "paper",
        "text": f"Vertical exaggeration: ~{int(vert_exag_display)}x",
        "showarrow": False,
        "font": {"size": 14, "color": "#888888"},
        "xanchor": "right",
        "yanchor": "bottom",
    }
)

# Slope legend annotation
annotations.append(
    {
        "x": 0.0,
        "y": 0.0,
        "xref": "paper",
        "yref": "paper",
        "text": (
            '<span style="color:#306998">\u2588</span> Gentle  '
            '<span style="color:#d4820a">\u2588</span> Moderate  '
            '<span style="color:#7b2d8e">\u2588</span> Steep'
        ),
        "showarrow": False,
        "font": {"size": 14, "color": "#666666"},
        "xanchor": "left",
        "yanchor": "bottom",
    }
)

# Style
fig.update_layout(
    title={
        "text": "Bernese Oberland Traverse · area-elevation-profile · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#2a2a2a"},
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
        "range": [0, 3200],
        "gridcolor": "rgba(0, 0, 0, 0.06)",
        "gridwidth": 1,
        "zeroline": False,
    },
    template="plotly_white",
    showlegend=False,
    annotations=annotations,
    margin={"l": 80, "r": 40, "t": 80, "b": 70},
    plot_bgcolor="white",
    paper_bgcolor="white",
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
