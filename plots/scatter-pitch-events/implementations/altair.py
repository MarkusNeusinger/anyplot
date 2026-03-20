""" pyplots.ai
scatter-pitch-events: Soccer Pitch Event Map
Library: altair 6.0.0 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-20
"""

import altair as alt
import numpy as np
import pandas as pd


# Data
np.random.seed(42)
n_events = 120
event_types = np.random.choice(["Pass", "Shot", "Tackle", "Interception"], size=n_events, p=[0.50, 0.15, 0.20, 0.15])

x = np.zeros(n_events)
y = np.zeros(n_events)
end_x = np.zeros(n_events)
end_y = np.zeros(n_events)

for i, etype in enumerate(event_types):
    if etype == "Pass":
        x[i] = np.random.uniform(10, 95)
        y[i] = np.random.uniform(5, 63)
        end_x[i] = np.clip(x[i] + np.random.uniform(-15, 25), 0, 105)
        end_y[i] = np.clip(y[i] + np.random.uniform(-12, 12), 0, 68)
    elif etype == "Shot":
        x[i] = np.random.uniform(60, 98)
        y[i] = np.random.uniform(15, 53)
        end_x[i] = 105
        end_y[i] = 34 + np.random.uniform(-4, 4)
    elif etype == "Tackle":
        x[i] = np.random.uniform(15, 80)
        y[i] = np.random.uniform(5, 63)
    elif etype == "Interception":
        x[i] = np.random.uniform(20, 75)
        y[i] = np.random.uniform(5, 63)

outcomes = np.where(np.random.random(n_events) < 0.65, "Successful", "Unsuccessful")

df = pd.DataFrame({"x": x, "y": y, "end_x": end_x, "end_y": end_y, "event_type": event_types, "outcome": outcomes})

# Bolder colorblind-safe palette: vivid blue, warm orange, strong teal, rich purple
color_domain = ["Pass", "Shot", "Tackle", "Interception"]
color_range = ["#2171b5", "#e6550d", "#1b9e77", "#7b3294"]

# Marker sizes: shots larger to create visual hierarchy (danger zone focal point)
df["marker_size"] = np.where(df["event_type"] == "Shot", 280, 160)

# Compute arrowhead positions (small triangle at 85% along each direction line)
arrows_df = df[df["event_type"].isin(["Pass", "Shot"])].copy()
arrow_frac = 0.85
arrows_df["arrow_x"] = arrows_df["x"] + arrow_frac * (arrows_df["end_x"] - arrows_df["x"])
arrows_df["arrow_y"] = arrows_df["y"] + arrow_frac * (arrows_df["end_y"] - arrows_df["y"])
dx = arrows_df["end_x"] - arrows_df["x"]
dy = arrows_df["end_y"] - arrows_df["y"]
arrows_df["angle"] = np.degrees(np.arctan2(dy, dx))

# Pitch zone shading — highlight attacking third as "danger zone" for storytelling
zones_data = pd.DataFrame(
    {
        "x": [0, 35, 70],
        "y": [0, 0, 0],
        "x2": [35, 70, 105],
        "y2": [68, 68, 68],
        "zone": ["Defensive Third", "Middle Third", "Attacking Third"],
        "fill": ["#1a472a", "#1f5432", "#2d6a3f"],
    }
)

# Pitch markings - line segments
lines_data = pd.DataFrame(
    {
        "x": [0, 0, 105, 0, 52.5, 0, 16.5, 16.5, 0, 5.5, 5.5, 105, 88.5, 88.5, 105, 99.5, 99.5],
        "y": [0, 0, 0, 68, 0, 13.84, 13.84, 54.16, 24.84, 24.84, 43.16, 13.84, 13.84, 54.16, 24.84, 24.84, 43.16],
        "x2": [105, 0, 105, 105, 52.5, 16.5, 16.5, 0, 5.5, 5.5, 0, 88.5, 88.5, 105, 99.5, 99.5, 105],
        "y2": [0, 68, 68, 68, 68, 13.84, 54.16, 54.16, 24.84, 43.16, 43.16, 13.84, 54.16, 54.16, 24.84, 43.16, 43.16],
    }
)

# Center circle points
theta = np.linspace(0, 2 * np.pi, 60)
center_circle = pd.DataFrame({"x": 52.5 + 9.15 * np.cos(theta), "y": 34 + 9.15 * np.sin(theta), "order": range(60)})

# Left penalty arc (outside penalty area, center at 11, 34)
arc_theta = np.linspace(-0.65, 0.65, 30)
left_arc = pd.DataFrame({"x": 11 + 9.15 * np.cos(arc_theta), "y": 34 + 9.15 * np.sin(arc_theta), "order": range(30)})

# Right penalty arc (outside penalty area, center at 94, 34)
right_arc = pd.DataFrame(
    {"x": 94 + 9.15 * np.cos(np.pi - arc_theta), "y": 34 + 9.15 * np.sin(np.pi - arc_theta), "order": range(30)}
)

# Corner arcs
corner_arcs = []
for cx, cy, t_start, t_end in [
    (0, 0, 0, np.pi / 2),
    (0, 68, -np.pi / 2, 0),
    (105, 0, np.pi / 2, np.pi),
    (105, 68, np.pi, 3 * np.pi / 2),
]:
    t = np.linspace(t_start, t_end, 15)
    corner_arcs.append(pd.DataFrame({"x": cx + 1 * np.cos(t), "y": cy + 1 * np.sin(t), "order": range(15)}))

# Spots
spots = pd.DataFrame({"x": [52.5, 11, 94], "y": [34, 34, 34]})

# Pitch zone backgrounds — gradient from dark to lighter green toward attacking third
zone_layers = []
for _, row in zones_data.iterrows():
    zone_layers.append(
        alt.Chart(pd.DataFrame({"x": [row["x"]], "y": [row["y"]], "x2": [row["x2"]], "y2": [row["y2"]]}))
        .mark_rect(color=row["fill"], opacity=0.18)
        .encode(x="x:Q", y="y:Q", x2="x2:Q", y2="y2:Q")
    )

# Pitch lines — white lines on dark pitch for crisp contrast
pitch_lines = (
    alt.Chart(lines_data)
    .mark_rule(color="rgba(255,255,255,0.75)", strokeWidth=1.8)
    .encode(x="x:Q", y="y:Q", x2="x2:Q", y2="y2:Q")
)

# Shared axis config — tighter domain for better canvas utilization
x_axis = alt.X(
    "x:Q",
    scale=alt.Scale(domain=[-2, 107]),
    axis=alt.Axis(title=None, labels=False, ticks=False, grid=False, domain=False),
)
y_axis = alt.Y(
    "y:Q",
    scale=alt.Scale(domain=[-2, 70]),
    axis=alt.Axis(title=None, labels=False, ticks=False, grid=False, domain=False),
)

# Center circle layer
circle_layer = (
    alt.Chart(center_circle)
    .mark_line(color="rgba(255,255,255,0.75)", strokeWidth=1.8, filled=False)
    .encode(x=x_axis, y=y_axis, order="order:O")
)

# Penalty arc layers
left_arc_layer = (
    alt.Chart(left_arc)
    .mark_line(color="rgba(255,255,255,0.75)", strokeWidth=1.8)
    .encode(x=x_axis, y=y_axis, order="order:O")
)
right_arc_layer = (
    alt.Chart(right_arc)
    .mark_line(color="rgba(255,255,255,0.75)", strokeWidth=1.8)
    .encode(x=x_axis, y=y_axis, order="order:O")
)

# Corner arc layers
corner_layers = [
    alt.Chart(ca).mark_line(color="rgba(255,255,255,0.75)", strokeWidth=1.8).encode(x=x_axis, y=y_axis, order="order:O")
    for ca in corner_arcs
]

# Spots — white to match pitch lines
spot_layer = alt.Chart(spots).mark_point(color="rgba(255,255,255,0.8)", size=45, filled=True).encode(x=x_axis, y=y_axis)

# Direction lines for passes and shots
arrow_lines = (
    alt.Chart(arrows_df)
    .mark_rule(strokeWidth=1.3)
    .encode(
        x="x:Q",
        y="y:Q",
        x2="end_x:Q",
        y2="end_y:Q",
        color=alt.Color("event_type:N", scale=alt.Scale(domain=color_domain, range=color_range), legend=None),
        opacity=alt.Opacity(
            "outcome:N", scale=alt.Scale(domain=["Successful", "Unsuccessful"], range=[0.55, 0.25]), legend=None
        ),
    )
)

# Arrowheads as rotated triangles at the end of direction lines
arrowheads = (
    alt.Chart(arrows_df)
    .mark_point(shape="triangle-right", filled=True, size=90, stroke=None)
    .encode(
        x=alt.X("arrow_x:Q", scale=alt.Scale(domain=[-2, 107]), axis=None),
        y=alt.Y("arrow_y:Q", scale=alt.Scale(domain=[-2, 70]), axis=None),
        color=alt.Color("event_type:N", scale=alt.Scale(domain=color_domain, range=color_range), legend=None),
        angle=alt.Angle("angle:Q", scale=alt.Scale(domain=[-180, 180], range=[-180, 180])),
        opacity=alt.Opacity(
            "outcome:N", scale=alt.Scale(domain=["Successful", "Unsuccessful"], range=[0.75, 0.35]), legend=None
        ),
    )
)

# Event markers — size encoding creates visual hierarchy (shots stand out in the danger zone)
event_points = (
    alt.Chart(df)
    .mark_point(filled=True, stroke="#ffffff", strokeWidth=1.0)
    .encode(
        x=x_axis,
        y=y_axis,
        color=alt.Color(
            "event_type:N",
            scale=alt.Scale(domain=color_domain, range=color_range),
            legend=alt.Legend(
                title="Event Type",
                titleFontSize=18,
                titleFontWeight="bold",
                labelFontSize=16,
                symbolSize=220,
                orient="right",
                titleColor="#222222",
                labelColor="#333333",
            ),
        ),
        shape=alt.Shape(
            "event_type:N",
            scale=alt.Scale(
                domain=["Pass", "Shot", "Tackle", "Interception"],
                range=["circle", "triangle-right", "triangle-up", "diamond"],
            ),
            legend=None,
        ),
        size=alt.Size("marker_size:Q", scale=alt.Scale(domain=[160, 280], range=[160, 280]), legend=None),
        opacity=alt.Opacity(
            "outcome:N",
            scale=alt.Scale(domain=["Successful", "Unsuccessful"], range=[0.92, 0.42]),
            legend=alt.Legend(
                title="Outcome",
                titleFontSize=18,
                titleFontWeight="bold",
                labelFontSize=16,
                symbolSize=220,
                orient="right",
                titleColor="#222222",
                labelColor="#333333",
            ),
        ),
        tooltip=[
            alt.Tooltip("event_type:N", title="Event"),
            alt.Tooltip("outcome:N", title="Outcome"),
            alt.Tooltip("x:Q", title="X (m)", format=".1f"),
            alt.Tooltip("y:Q", title="Y (m)", format=".1f"),
        ],
    )
)

# Compose all layers
chart = (
    alt.layer(
        *zone_layers,
        pitch_lines,
        circle_layer,
        left_arc_layer,
        right_arc_layer,
        *corner_layers,
        spot_layer,
        arrow_lines,
        arrowheads,
        event_points,
    )
    .properties(
        width=1600,
        height=round(1600 * 68 / 105),
        title=alt.Title(
            "scatter-pitch-events · altair · pyplots.ai",
            fontSize=28,
            fontWeight="bold",
            color="#1a1a1a",
            subtitle="Match events: passes, shots, tackles, and interceptions — shots highlighted in the attacking third",
            subtitleFontSize=17,
            subtitleColor="#555555",
            subtitlePadding=8,
        ),
    )
    .configure_view(strokeWidth=0)
    .configure_legend(fillColor="#f8f9fa", strokeColor="#d0d0d0", padding=12, cornerRadius=6, titlePadding=6)
    .resolve_scale(
        color="independent", opacity="independent", shape="independent", angle="independent", size="independent"
    )
    .interactive()
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
