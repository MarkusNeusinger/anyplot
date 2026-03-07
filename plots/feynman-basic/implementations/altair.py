"""pyplots.ai
feynman-basic: Feynman Diagram for Particle Interactions
Library: altair | Python 3.13
Quality: pending | Created: 2026-03-07
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Electron-positron annihilation: e- + e+ -> gamma -> e- + e+
# Vertices
vertices = {"v1": (1.5, 3.0), "v2": (5.5, 3.0)}

# Propagators with particle info
propagators = [
    {"from": "v1", "to": "v2", "type": "photon", "label": "\u03b3"},
    {"from": "start_e-", "to": "v1", "type": "fermion", "label": "e\u207b"},
    {"from": "start_e+", "to": "v1", "type": "fermion", "label": "e\u207a"},
    {"from": "v2", "to": "end_e-", "type": "fermion", "label": "e\u207b"},
    {"from": "v2", "to": "end_e+", "type": "fermion", "label": "e\u207a"},
]

external_positions = {"start_e-": (0.0, 5.0), "start_e+": (0.0, 1.0), "end_e-": (7.0, 5.0), "end_e+": (7.0, 1.0)}

all_positions = {**vertices, **external_positions}

# Build line segments for fermion lines (straight lines)
fermion_lines = []
for p in propagators:
    if p["type"] != "fermion":
        continue
    x0, y0 = all_positions[p["from"]]
    x1, y1 = all_positions[p["to"]]
    fermion_lines.append({"x": x0, "y": y0, "x2": x1, "y2": y1, "label": p["label"], "group": p["label"] + p["from"]})

fermion_df = pd.DataFrame(fermion_lines)

# Build wavy line for photon (sinusoidal path between vertices)
photon_points = []
x0, y0 = all_positions["v1"]
x1, y1 = all_positions["v2"]
n_points = 200
t = np.linspace(0, 1, n_points)
wave_freq = 8
wave_amp = 0.25
dx = x1 - x0
dy = y1 - y0
length = np.sqrt(dx**2 + dy**2)
nx, ny = -dy / length, dx / length

for i in range(n_points):
    offset = wave_amp * np.sin(2 * np.pi * wave_freq * t[i])
    px = x0 + t[i] * dx + offset * nx
    py = y0 + t[i] * dy + offset * ny
    photon_points.append({"x": px, "y": py, "order": i})

photon_df = pd.DataFrame(photon_points)

# Build arrow indicators for fermion lines (triangle at midpoint)
arrows = []
for p in propagators:
    if p["type"] != "fermion":
        continue
    x0, y0 = all_positions[p["from"]]
    x1, y1 = all_positions[p["to"]]
    mx = (x0 + x1) / 2
    my = (y0 + y1) / 2
    angle_deg = np.degrees(np.arctan2(y1 - y0, x1 - x0))
    arrows.append({"x": mx, "y": my, "angle": angle_deg, "label": p["label"]})

arrows_df = pd.DataFrame(arrows)

# Build vertex points
vertex_df = pd.DataFrame([{"x": pos[0], "y": pos[1], "name": name} for name, pos in vertices.items()])

# Build labels for propagators
label_data = []
for p in propagators:
    x0, y0 = all_positions[p["from"]]
    x1, y1 = all_positions[p["to"]]
    mx = (x0 + x1) / 2
    my = (y0 + y1) / 2
    dx = x1 - x0
    dy = y1 - y0
    length = np.sqrt(dx**2 + dy**2)
    nx, ny = -dy / length, dx / length
    offset = 0.35
    if p["type"] == "photon":
        offset = 0.5
    label_data.append({"x": mx + offset * nx, "y": my + offset * ny, "label": p["label"]})

label_df = pd.DataFrame(label_data)

# Build time axis arrow
time_arrow_df = pd.DataFrame([{"x": 0.5, "y": -0.3, "x2": 6.5, "y2": -0.3}])

time_label_df = pd.DataFrame([{"x": 3.5, "y": -0.7, "label": "time"}])

# Plot - Fermion lines
fermion_layer = (
    alt.Chart(fermion_df)
    .mark_rule(strokeWidth=3, color="#306998")
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[-0.5, 7.5]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[-1.5, 6.0]), axis=None),
        x2="x2:Q",
        y2="y2:Q",
    )
)

# Photon wavy line
photon_layer = (
    alt.Chart(photon_df)
    .mark_line(strokeWidth=3, color="#D4A017", interpolate="monotone")
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None), order="order:O")
)

# Arrow triangles at midpoints of fermion lines
arrow_layer = (
    alt.Chart(arrows_df)
    .mark_point(shape="triangle", size=400, filled=True, color="#306998")
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None), angle=alt.Angle("angle:Q"))
)

# Vertex dots
vertex_layer = (
    alt.Chart(vertex_df)
    .mark_circle(size=300, color="#1a1a1a", stroke="white", strokeWidth=2)
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None))
)

# Particle labels
label_layer = (
    alt.Chart(label_df)
    .mark_text(fontSize=24, fontWeight="bold", color="#1a1a1a", font="serif", fontStyle="italic")
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None), text="label:N")
)

# Time axis
time_line_layer = (
    alt.Chart(time_arrow_df)
    .mark_rule(strokeWidth=2, color="#888888", strokeDash=[6, 4])
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None), x2="x2:Q", y2="y2:Q")
)

time_arrow_head = (
    alt.Chart(pd.DataFrame([{"x": 6.5, "y": -0.3, "angle": 90}]))
    .mark_point(shape="triangle", size=250, filled=True, color="#888888")
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None), angle=alt.Angle("angle:Q"))
)

time_label_layer = (
    alt.Chart(time_label_df)
    .mark_text(fontSize=20, color="#888888", fontStyle="italic")
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None), text="label:N")
)

# Combine all layers
chart = (
    alt.layer(
        fermion_layer,
        photon_layer,
        arrow_layer,
        vertex_layer,
        label_layer,
        time_line_layer,
        time_arrow_head,
        time_label_layer,
    )
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "feynman-basic \u00b7 altair \u00b7 pyplots.ai",
            fontSize=28,
            fontWeight="normal",
            anchor="middle",
            offset=20,
        ),
    )
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
