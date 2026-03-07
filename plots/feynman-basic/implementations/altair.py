"""pyplots.ai
feynman-basic: Feynman Diagram for Particle Interactions
Library: altair 6.0.0 | Python 3.14.3
"""

import altair as alt
import numpy as np
import pandas as pd


# Higgs boson production via gluon fusion: g + g → [t loop] → H → γ + γ
# Shows all 4 particle types: fermion (straight), photon (wavy), gluon (curly), boson (dashed)

# Vertex positions
v1 = (2.0, 4.5)  # upper-left triangle vertex (g-t-t)
v2 = (2.0, 1.7)  # lower-left triangle vertex (g-t-t)
v3 = (4.5, 3.1)  # right triangle vertex (t-t-H)
v4 = (6.8, 3.1)  # Higgs decay vertex (H-γ-γ)

# Shared scales
x_scale = alt.Scale(domain=[-0.8, 9.2])
y_scale = alt.Scale(domain=[-0.2, 5.6])

# Color scale mapping particle type to color
color_scale = alt.Scale(
    domain=["fermion", "photon", "gluon", "boson"], range=["#306998", "#D4A017", "#C0392B", "#27AE60"]
)

# Interactive selection bound to legend (works in HTML export)
highlight = alt.selection_point(fields=["particle_type"], bind="legend")
opacity_cond = alt.condition(highlight, alt.value(1.0), alt.value(0.25))

# --- Straight lines: fermion (solid) and boson (dashed) ---
straight_records = []
arrow_records = []

# Top quark loop (v1→v2→v3→v1)
for from_pos, to_pos, pid in [(v1, v2, "t1"), (v2, v3, "t2"), (v3, v1, "t3")]:
    x0, y0, x1, y1 = *from_pos, *to_pos
    straight_records.append(
        {"x": x0, "y": y0, "x2": x1, "y2": y1, "particle_type": "fermion", "label": "t", "line_id": pid}
    )
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    angle = np.degrees(np.arctan2(y1 - y0, x1 - x0))
    arrow_records.append({"x": mx, "y": my, "angle": angle, "particle_type": "fermion", "label": "t"})

# Higgs boson: v3 → v4 (dashed)
straight_records.append(
    {"x": v3[0], "y": v3[1], "x2": v4[0], "y2": v4[1], "particle_type": "boson", "label": "H", "line_id": "H"}
)

straight_df = pd.DataFrame(straight_records)
arrows_df = pd.DataFrame(arrow_records)

# --- Wavy paths (photon) and curly paths (gluon) ---
path_records = []


def add_wavy_path(x0, y0, x1, y1, label, line_id, freq=8, amp=0.2, n_pts=200):
    t = np.linspace(0, 1, n_pts)
    dx, dy = x1 - x0, y1 - y0
    length = np.hypot(dx, dy)
    nx, ny = -dy / length, dx / length
    offset = amp * np.sin(2 * np.pi * freq * t)
    for i in range(n_pts):
        path_records.append(
            {
                "x": x0 + t[i] * dx + offset[i] * nx,
                "y": y0 + t[i] * dy + offset[i] * ny,
                "order": i,
                "particle_type": "photon",
                "label": label,
                "line_id": line_id,
            }
        )


def add_curly_path(x0, y0, x1, y1, label, line_id, n_loops=7, loop_r=0.15, n_pts=400):
    dx, dy = x1 - x0, y1 - y0
    length = np.hypot(dx, dy)
    tx, ty = dx / length, dy / length
    nx, ny = -ty, tx
    theta = np.linspace(0, n_loops * 2 * np.pi, n_pts)
    base = np.linspace(0, length, n_pts)
    advance = base + loop_r * np.sin(theta)
    perp = loop_r * np.cos(theta)
    for i in range(n_pts):
        path_records.append(
            {
                "x": x0 + advance[i] * tx + perp[i] * nx,
                "y": y0 + advance[i] * ty + perp[i] * ny,
                "order": i,
                "particle_type": "gluon",
                "label": label,
                "line_id": line_id,
            }
        )


# Gluon inputs
add_curly_path(0.0, 4.5, *v1, "g", "g1")
add_curly_path(0.0, 1.7, *v2, "g", "g2")
# Photon outputs
add_wavy_path(*v4, 8.5, 4.7, "γ", "γ1")
add_wavy_path(*v4, 8.5, 1.5, "γ", "γ2")

path_df = pd.DataFrame(path_records)

# --- Labels with computed tooltip via transform_calculate ---
label_records = [
    {"x": 2.55, "y": 3.1, "label": "t", "particle_type": "fermion"},  # triangle centroid
    {"x": (v3[0] + v4[0]) / 2, "y": v3[1] + 0.4, "label": "H", "particle_type": "boson"},
    {"x": 0.8, "y": 5.0, "label": "g", "particle_type": "gluon"},
    {"x": 0.8, "y": 1.2, "label": "g", "particle_type": "gluon"},
    {"x": 7.9, "y": 5.0, "label": "γ", "particle_type": "photon"},
    {"x": 7.9, "y": 1.2, "label": "γ", "particle_type": "photon"},
]
label_df = pd.DataFrame(label_records)

# --- Vertex dots ---
vertex_df = pd.DataFrame(
    [
        {"x": v1[0], "y": v1[1], "vertex": "g-t-t"},
        {"x": v2[0], "y": v2[1], "vertex": "g-t-t"},
        {"x": v3[0], "y": v3[1], "vertex": "t-t-H"},
        {"x": v4[0], "y": v4[1], "vertex": "H-γ-γ"},
    ]
)

# --- Process annotation ---
process_df = pd.DataFrame([{"x": 4.25, "y": 5.3, "text": "g + g  →  H  →  γ + γ"}])

# --- Time axis ---
time_line_df = pd.DataFrame([{"x": 1.0, "y": 0.3, "x2": 7.8, "y2": 0.3}])
time_arrow_df = pd.DataFrame([{"x": 7.8, "y": 0.3, "angle": 90}])
time_label_df = pd.DataFrame([{"x": 4.4, "y": -0.02, "label": "time"}])

# --- Chart layers ---
# Straight lines with data-driven color and strokeDash encoding
straight_layer = (
    alt.Chart(straight_df)
    .mark_rule(strokeWidth=3)
    .encode(
        x=alt.X("x:Q", scale=x_scale, axis=None),
        y=alt.Y("y:Q", scale=y_scale, axis=None),
        x2="x2:Q",
        y2="y2:Q",
        color=alt.Color(
            "particle_type:N",
            scale=color_scale,
            legend=alt.Legend(
                title="Particle Type", titleFontSize=18, labelFontSize=16, symbolSize=200, orient="right", offset=10
            ),
        ),
        strokeDash=alt.StrokeDash(
            "particle_type:N", scale=alt.Scale(domain=["fermion", "boson"], range=[[1, 0], [10, 6]]), legend=None
        ),
        opacity=opacity_cond,
        tooltip=[alt.Tooltip("label:N", title="Particle"), alt.Tooltip("particle_type:N", title="Type")],
    )
    .add_params(highlight)
)

# Wavy/curly paths with data-driven color and detail separation
path_layer = (
    alt.Chart(path_df)
    .mark_line(strokeWidth=2.5)
    .encode(
        x=alt.X("x:Q", scale=x_scale, axis=None),
        y=alt.Y("y:Q", scale=y_scale, axis=None),
        color=alt.Color("particle_type:N", scale=color_scale, legend=None),
        detail="line_id:N",
        order="order:Q",
        opacity=opacity_cond,
        tooltip=[alt.Tooltip("label:N", title="Particle"), alt.Tooltip("particle_type:N", title="Type")],
    )
    .add_params(highlight)
)

# Fermion direction arrows
arrow_layer = (
    alt.Chart(arrows_df)
    .mark_point(shape="triangle", size=350, filled=True)
    .encode(
        x=alt.X("x:Q", scale=x_scale, axis=None),
        y=alt.Y("y:Q", scale=y_scale, axis=None),
        angle=alt.Angle("angle:Q"),
        color=alt.Color("particle_type:N", scale=color_scale, legend=None),
        opacity=opacity_cond,
    )
    .add_params(highlight)
)

# Vertex dots with interaction tooltips
vertex_layer = (
    alt.Chart(vertex_df)
    .mark_circle(size=400, color="#1a1a1a", stroke="white", strokeWidth=2)
    .encode(
        x=alt.X("x:Q", scale=x_scale, axis=None),
        y=alt.Y("y:Q", scale=y_scale, axis=None),
        tooltip=[alt.Tooltip("vertex:N", title="Interaction")],
    )
)

# Particle labels colored by type with computed tooltip
label_layer = (
    alt.Chart(label_df)
    .transform_calculate(description="datum.label + ' (' + datum.particle_type + ')'")
    .mark_text(fontSize=24, fontWeight="bold", font="serif", fontStyle="italic")
    .encode(
        x=alt.X("x:Q", scale=x_scale, axis=None),
        y=alt.Y("y:Q", scale=y_scale, axis=None),
        text="label:N",
        color=alt.Color("particle_type:N", scale=color_scale, legend=None),
        opacity=opacity_cond,
        tooltip=[alt.Tooltip("description:N", title="Particle")],
    )
    .add_params(highlight)
)

# Process annotation
process_layer = (
    alt.Chart(process_df)
    .mark_text(fontSize=20, font="serif", fontStyle="italic", color="#555555")
    .encode(x=alt.X("x:Q", scale=x_scale, axis=None), y=alt.Y("y:Q", scale=y_scale, axis=None), text="text:N")
)

# Time axis
time_line_layer = (
    alt.Chart(time_line_df)
    .mark_rule(strokeWidth=1.5, color="#999999", strokeDash=[6, 4])
    .encode(x=alt.X("x:Q", scale=x_scale, axis=None), y=alt.Y("y:Q", scale=y_scale, axis=None), x2="x2:Q", y2="y2:Q")
)

time_arrow_layer = (
    alt.Chart(time_arrow_df)
    .mark_point(shape="triangle", size=200, filled=True, color="#999999")
    .encode(
        x=alt.X("x:Q", scale=x_scale, axis=None), y=alt.Y("y:Q", scale=y_scale, axis=None), angle=alt.Angle("angle:Q")
    )
)

time_label_layer = (
    alt.Chart(time_label_df)
    .mark_text(fontSize=18, color="#999999", fontStyle="italic")
    .encode(x=alt.X("x:Q", scale=x_scale, axis=None), y=alt.Y("y:Q", scale=y_scale, axis=None), text="label:N")
)

# Combine all layers
chart = (
    alt.layer(
        straight_layer,
        path_layer,
        arrow_layer,
        vertex_layer,
        label_layer,
        process_layer,
        time_line_layer,
        time_arrow_layer,
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
