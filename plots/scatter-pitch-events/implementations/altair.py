"""pyplots.ai
scatter-pitch-events: Soccer Pitch Event Map
Library: altair | Python 3.13
Quality: pending | Created: 2026-03-20
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

# Pitch background
pitch_bg = (
    alt.Chart(pd.DataFrame({"x": [0], "y": [0], "x2": [105], "y2": [68]}))
    .mark_rect(color="#3a7d44", opacity=0.18)
    .encode(x="x:Q", y="y:Q", x2="x2:Q", y2="y2:Q")
)

# Pitch lines
pitch_lines = (
    alt.Chart(lines_data).mark_rule(color="#555555", strokeWidth=1.5).encode(x="x:Q", y="y:Q", x2="x2:Q", y2="y2:Q")
)

# Shared axis config
x_axis = alt.X(
    "x:Q",
    scale=alt.Scale(domain=[-3, 108]),
    axis=alt.Axis(title=None, labels=False, ticks=False, grid=False, domain=False),
)
y_axis = alt.Y(
    "y:Q",
    scale=alt.Scale(domain=[-3, 71]),
    axis=alt.Axis(title=None, labels=False, ticks=False, grid=False, domain=False),
)

# Center circle layer
circle_layer = (
    alt.Chart(center_circle)
    .mark_line(color="#555555", strokeWidth=1.5, filled=False)
    .encode(x=x_axis, y=y_axis, order="order:O")
)

# Penalty arc layers
left_arc_layer = (
    alt.Chart(left_arc).mark_line(color="#555555", strokeWidth=1.5).encode(x=x_axis, y=y_axis, order="order:O")
)
right_arc_layer = (
    alt.Chart(right_arc).mark_line(color="#555555", strokeWidth=1.5).encode(x=x_axis, y=y_axis, order="order:O")
)

# Corner arc layers
corner_layers = [
    alt.Chart(ca).mark_line(color="#555555", strokeWidth=1.5).encode(x=x_axis, y=y_axis, order="order:O")
    for ca in corner_arcs
]

# Spots
spot_layer = alt.Chart(spots).mark_point(color="#555555", size=40, filled=True).encode(x=x_axis, y=y_axis)

# Direction lines for passes and shots
arrows_df = df[df["event_type"].isin(["Pass", "Shot"])].copy()
arrow_lines = (
    alt.Chart(arrows_df)
    .mark_rule(strokeWidth=1.2)
    .encode(
        x="x:Q",
        y="y:Q",
        x2="end_x:Q",
        y2="end_y:Q",
        color=alt.Color(
            "event_type:N",
            scale=alt.Scale(
                domain=["Pass", "Shot", "Tackle", "Interception"], range=["#306998", "#e74c3c", "#2ecc71", "#9b59b6"]
            ),
            legend=None,
        ),
        opacity=alt.Opacity(
            "outcome:N", scale=alt.Scale(domain=["Successful", "Unsuccessful"], range=[0.5, 0.2]), legend=None
        ),
    )
)

# Event markers

event_points = (
    alt.Chart(df)
    .mark_point(filled=True, size=180, stroke="#ffffff", strokeWidth=0.8)
    .encode(
        x=x_axis,
        y=y_axis,
        color=alt.Color(
            "event_type:N",
            scale=alt.Scale(
                domain=["Pass", "Shot", "Tackle", "Interception"], range=["#306998", "#e74c3c", "#2ecc71", "#9b59b6"]
            ),
            legend=alt.Legend(title="Event Type", titleFontSize=18, labelFontSize=16, symbolSize=200),
        ),
        shape=alt.Shape(
            "event_type:N",
            scale=alt.Scale(
                domain=["Pass", "Shot", "Tackle", "Interception"],
                range=["circle", "triangle-right", "triangle-up", "diamond"],
            ),
            legend=None,
        ),
        opacity=alt.Opacity(
            "outcome:N",
            scale=alt.Scale(domain=["Successful", "Unsuccessful"], range=[0.9, 0.3]),
            legend=alt.Legend(title="Outcome", titleFontSize=18, labelFontSize=16, symbolSize=200),
        ),
        tooltip=[
            alt.Tooltip("event_type:N", title="Event"),
            alt.Tooltip("outcome:N", title="Outcome"),
            alt.Tooltip("x:Q", title="X Position", format=".1f"),
            alt.Tooltip("y:Q", title="Y Position", format=".1f"),
        ],
    )
)

# Compose all layers
chart = (
    alt.layer(
        pitch_bg,
        pitch_lines,
        circle_layer,
        left_arc_layer,
        right_arc_layer,
        *corner_layers,
        spot_layer,
        arrow_lines,
        event_points,
    )
    .properties(
        width=1500,
        height=round(1500 * 68 / 105),
        title=alt.Title(
            "scatter-pitch-events · altair · pyplots.ai",
            fontSize=28,
            color="#222222",
            subtitle="Match events: passes, shots, tackles, and interceptions across the pitch",
            subtitleFontSize=16,
            subtitleColor="#777777",
            subtitlePadding=6,
        ),
    )
    .configure_view(strokeWidth=0)
    .configure_legend(fillColor="white", strokeColor="#cccccc", padding=10, cornerRadius=4)
    .resolve_scale(color="independent", opacity="independent", shape="independent")
    .interactive()
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
