""" pyplots.ai
feynman-basic: Feynman Diagram for Particle Interactions
Library: altair 6.0.0 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-07
"""

import altair as alt
import numpy as np
import pandas as pd


# Higgs boson production via gluon fusion: g + g → [t loop] → H → γ + γ
# Shows all 4 particle types: fermion (straight), photon (wavy), gluon (curly), boson (dashed)

# Vertex positions — spread to maximize canvas utilization
v1 = (2.5, 5.5)  # upper-left triangle vertex (g-t-t)
v2 = (2.5, 1.5)  # lower-left triangle vertex (g-t-t)
v3 = (5.2, 3.5)  # right triangle vertex (t-t-H)
v4 = (7.5, 3.5)  # Higgs decay vertex (H-γ-γ)

# Shared scales — tighter domain to fill more canvas
x_scale = alt.Scale(domain=[-0.3, 9.8])
y_scale = alt.Scale(domain=[-0.3, 7.2])

color_scale = alt.Scale(
    domain=["fermion", "photon", "gluon", "boson"], range=["#306998", "#D4A017", "#C0392B", "#8E44AD"]
)

# Interactive selection bound to legend
highlight = alt.selection_point(fields=["particle_type"], bind="legend")
opacity_cond = alt.condition(highlight, alt.value(1.0), alt.value(0.25))

# --- Straight lines: fermion edges + Higgs boson ---
fermion_edges = [(v1, v2, "t1"), (v2, v3, "t2"), (v3, v1, "t3")]
straight_df = pd.DataFrame(
    [
        {"x": f[0], "y": f[1], "x2": t[0], "y2": t[1], "particle_type": "fermion", "label": "t", "line_id": pid}
        for f, t, pid in fermion_edges
    ]
    + [{"x": v3[0], "y": v3[1], "x2": v4[0], "y2": v4[1], "particle_type": "boson", "label": "H", "line_id": "H"}]
)

# Fermion direction arrows at edge midpoints
arrows_df = pd.DataFrame(
    [
        {
            "x": (f[0] + t[0]) / 2,
            "y": (f[1] + t[1]) / 2,
            "angle": np.degrees(np.arctan2(t[1] - f[1], t[0] - f[0])),
            "particle_type": "fermion",
            "label": "t",
        }
        for f, t, _ in fermion_edges
    ]
)

# --- Wavy paths (photon) — vectorized sinusoidal offset ---
n_wavy = 200
wavy_paths = []
for x0, y0, x1, y1, lid in [(*v4, 9.2, 5.8, "γ1"), (*v4, 9.2, 1.2, "γ2")]:
    t = np.linspace(0, 1, n_wavy)
    dx, dy = x1 - x0, y1 - y0
    length = np.hypot(dx, dy)
    nx, ny = -dy / length, dx / length
    offset = 0.22 * np.sin(2 * np.pi * 8 * t)
    wavy_paths.append(
        pd.DataFrame(
            {
                "x": x0 + t * dx + offset * nx,
                "y": y0 + t * dy + offset * ny,
                "order": np.arange(n_wavy),
                "particle_type": "photon",
                "label": "γ",
                "line_id": lid,
            }
        )
    )

# --- Curly paths (gluon) — vectorized looped offset ---
n_curly, n_loops, loop_r = 400, 7, 0.18
curly_paths = []
for x0, y0, x1, y1, lid in [(0.3, 5.5, *v1, "g1"), (0.3, 1.5, *v2, "g2")]:
    dx, dy = x1 - x0, y1 - y0
    length = np.hypot(dx, dy)
    tx, ty = dx / length, dy / length
    nx, ny = -ty, tx
    theta = np.linspace(0, n_loops * 2 * np.pi, n_curly)
    base = np.linspace(0, length, n_curly)
    curly_paths.append(
        pd.DataFrame(
            {
                "x": x0 + (base + loop_r * np.sin(theta)) * tx + loop_r * np.cos(theta) * nx,
                "y": y0 + (base + loop_r * np.sin(theta)) * ty + loop_r * np.cos(theta) * ny,
                "order": np.arange(n_curly),
                "particle_type": "gluon",
                "label": "g",
                "line_id": lid,
            }
        )
    )

path_df = pd.concat(wavy_paths + curly_paths, ignore_index=True)

# --- Labels colored by particle type ---
label_df = pd.DataFrame(
    [
        {"x": 3.1, "y": 3.5, "label": "t", "particle_type": "fermion"},
        {"x": (v3[0] + v4[0]) / 2, "y": v3[1] + 0.5, "label": "H", "particle_type": "boson"},
        {"x": 1.0, "y": 6.2, "label": "g", "particle_type": "gluon"},
        {"x": 1.0, "y": 0.8, "label": "g", "particle_type": "gluon"},
        {"x": 8.8, "y": 6.2, "label": "γ", "particle_type": "photon"},
        {"x": 8.8, "y": 0.8, "label": "γ", "particle_type": "photon"},
    ]
)

# --- Vertex dots ---
vertex_df = pd.DataFrame(
    [
        {"x": v1[0], "y": v1[1], "vertex": "g-t-t"},
        {"x": v2[0], "y": v2[1], "vertex": "g-t-t"},
        {"x": v3[0], "y": v3[1], "vertex": "t-t-H"},
        {"x": v4[0], "y": v4[1], "vertex": "H-γ-γ"},
    ]
)

# --- Process annotation and time axis ---
process_df = pd.DataFrame([{"x": 5.0, "y": 6.8, "text": "g + g  →  H  →  γ + γ"}])
time_line_df = pd.DataFrame([{"x": 1.5, "y": 0.2, "x2": 8.5, "y2": 0.2}])
time_arrow_df = pd.DataFrame([{"x": 8.5, "y": 0.2, "angle": 90}])
time_label_df = pd.DataFrame([{"x": 5.0, "y": -0.1, "label": "time"}])

# --- Subtle background panel for the interaction region ---
bg_df = pd.DataFrame([{"x": 0.0, "y": 0.5, "x2": 9.6, "y2": 6.5}])
bg_layer = (
    alt.Chart(bg_df)
    .mark_rect(color="#f7f9fc", cornerRadius=18, stroke="#e0e4ea", strokeWidth=1)
    .encode(x=alt.X("x:Q", scale=x_scale, axis=None), y=alt.Y("y:Q", scale=y_scale, axis=None), x2="x2:Q", y2="y2:Q")
)

# --- Chart layers ---
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

path_layer = (
    alt.Chart(path_df)
    .mark_line(strokeWidth=2.8)
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

arrow_layer = (
    alt.Chart(arrows_df)
    .mark_point(shape="triangle", size=400, filled=True)
    .encode(
        x=alt.X("x:Q", scale=x_scale, axis=None),
        y=alt.Y("y:Q", scale=y_scale, axis=None),
        angle=alt.Angle("angle:Q"),
        color=alt.Color("particle_type:N", scale=color_scale, legend=None),
        opacity=opacity_cond,
    )
    .add_params(highlight)
)

vertex_shadow = (
    alt.Chart(vertex_df)
    .mark_circle(size=700, color="#00000015")
    .encode(x=alt.X("x:Q", scale=x_scale, axis=None), y=alt.Y("y:Q", scale=y_scale, axis=None))
)

vertex_layer = (
    alt.Chart(vertex_df)
    .mark_circle(size=500, color="#1a1a1a", stroke="white", strokeWidth=2.5)
    .encode(
        x=alt.X("x:Q", scale=x_scale, axis=None),
        y=alt.Y("y:Q", scale=y_scale, axis=None),
        tooltip=[alt.Tooltip("vertex:N", title="Interaction")],
    )
)

label_layer = (
    alt.Chart(label_df)
    .transform_calculate(description="datum.label + ' (' + datum.particle_type + ')'")
    .mark_text(fontSize=26, fontWeight="bold", font="serif", fontStyle="italic")
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

process_layer = (
    alt.Chart(process_df)
    .mark_text(fontSize=22, font="serif", fontStyle="italic", color="#444444")
    .encode(x=alt.X("x:Q", scale=x_scale, axis=None), y=alt.Y("y:Q", scale=y_scale, axis=None), text="text:N")
)

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
        bg_layer,
        straight_layer,
        path_layer,
        arrow_layer,
        vertex_shadow,
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
