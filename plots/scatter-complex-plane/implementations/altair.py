""" pyplots.ai
scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
Library: altair 6.0.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-04
"""

import altair as alt
import numpy as np
import pandas as pd


# Data
np.random.seed(42)

# 3rd roots of unity
n_roots = 3
roots_of_unity = [np.exp(2j * np.pi * k / n_roots) for k in range(n_roots)]

# Arbitrary complex numbers across all quadrants
arbitrary_points = [2.5 + 1.5j, -1.8 + 2.2j, 1.0 - 2.0j, -0.5 - 1.5j, 2.0 + 0.5j]

# Complex rotation: z * e^(iπ/4)
z_original = 1.5 + 0.8j
z_rotated = z_original * np.exp(1j * np.pi / 4)

# Build all points with a compact helper expression
all_points = []
point_sets = [
    (roots_of_unity, [f"ω{k}" for k in range(n_roots)], "Roots of Unity"),
    (arbitrary_points, [f"z{chr(0x2081 + k)}" for k in range(5)], "Arbitrary"),
    ([z_original, z_rotated], ["z", "z·e^(iπ/4)"], "Transformation"),
]
for points, labels, cat in point_sets:
    for lbl, z in zip(labels, points, strict=True):
        r, i = round(z.real, 2), round(z.imag, 2)
        sign = "+" if i >= 0 else ""
        all_points.append(
            {"real": z.real, "imaginary": z.imag, "label": lbl, "rect_form": f"{r}{sign}{i}i", "category": cat}
        )

df = pd.DataFrame(all_points)
df["annotation"] = df["label"] + " = " + df["rect_form"]

# Label offsets: push labels away from origin based on quadrant, with special
# handling for nearby points (z at 1.5+0.8i and z₅ at 2.0+0.5i in Q1)
offsets = {"dx": [], "dy": [], "align": []}
for _, row in df.iterrows():
    rx, iy = row["real"], row["imaginary"]
    # Default quadrant-based offsets
    dx = 0.15 if rx >= 0 else -0.15
    dy = 0.22 if iy >= 0 else -0.22
    align = "left" if rx >= 0 else "right"
    # Push z₅ label down-right to avoid z label
    if row["label"] == "z\u2085":
        dy = -0.18
    # Push z·e^(iπ/4) label further up
    if row["label"] == "z·e^(iπ/4)":
        dy = 0.28
        dx = 0.20
    offsets["dx"].append(rx + dx)
    offsets["dy"].append(iy + dy)
    offsets["align"].append(align)

df["label_x"] = offsets["dx"]
df["label_y"] = offsets["dy"]
df["label_align"] = offsets["align"]

# Unit circle (parametric)
theta = np.linspace(0, 2 * np.pi, 200)
circle_df = pd.DataFrame({"x": np.cos(theta), "y": np.sin(theta), "order": range(len(theta))})

# Vector segments (origin → point)
arrow_rows = []
for _, row in df.iterrows():
    arrow_rows.append({"x": 0, "y": 0, "group": row["label"], "order": 0, "category": row["category"]})
    arrow_rows.append(
        {"x": row["real"], "y": row["imaginary"], "group": row["label"], "order": 1, "category": row["category"]}
    )
arrow_df = pd.DataFrame(arrow_rows)

# Arrowhead positions (slightly offset back along vector)
head_offset = 0.08
arrowhead_rows = []
for _, row in df.iterrows():
    rx, iy = row["real"], row["imaginary"]
    mag = np.sqrt(rx**2 + iy**2)
    scale = head_offset / mag if mag > 0 else 0
    hx, hy = rx - scale * rx, iy - scale * iy
    vega_angle = 90 - np.degrees(np.arctan2(iy, rx))
    arrowhead_rows.append({"x": hx, "y": hy, "angle": vega_angle, "category": row["category"]})
arrowhead_df = pd.DataFrame(arrowhead_rows)

# Rotation arc (curved arrow from z to z·e^(iπ/4)) for visual storytelling
arc_start = np.arctan2(z_original.imag, z_original.real)
arc_end = arc_start + np.pi / 4
arc_theta = np.linspace(arc_start, arc_end, 40)
arc_r = abs(z_original) * 0.55  # arc at 55% of vector length
arc_df = pd.DataFrame({"x": arc_r * np.cos(arc_theta), "y": arc_r * np.sin(arc_theta), "order": range(40)})

# Axis range (tighter to maximize canvas utilization)
axis_limit = 2.65

# Axis lines through origin
axis_line_data = pd.DataFrame(
    {
        "x": [-axis_limit, axis_limit, 0, 0],
        "y": [0, 0, -axis_limit, axis_limit],
        "axis": ["real", "real", "imag", "imag"],
        "order": [0, 1, 0, 1],
    }
)

# Color palette
cat_domain = ["Roots of Unity", "Arbitrary", "Transformation"]
cat_colors = ["#306998", "#E8822A", "#6A5ACD"]
color_scale = alt.Scale(domain=cat_domain, range=cat_colors)

# Selection for interactive highlight (distinctive Altair feature)
highlight = alt.selection_point(fields=["category"], bind="legend")
opacity_cond = alt.condition(highlight, alt.value(1.0), alt.value(0.25))

# --- Layers ---

# Axis lines
axes = (
    alt.Chart(axis_line_data)
    .mark_line(color="#999999", strokeWidth=1.5, opacity=0.5)
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None), detail="axis:N", order="order:O")
)

# Dashed unit circle
unit_circle = (
    alt.Chart(circle_df)
    .mark_line(color="#AAAAAA", strokeWidth=2, strokeDash=[8, 6], opacity=0.5)
    .encode(x="x:Q", y="y:Q", order="order:O")
)

# Rotation arc (storytelling element)
rotation_arc = (
    alt.Chart(arc_df)
    .mark_line(color="#6A5ACD", strokeWidth=2.5, strokeDash=[5, 3], opacity=0.6)
    .encode(x="x:Q", y="y:Q", order="order:O")
)

# Arc label "π/4"
arc_mid_angle = arc_start + np.pi / 8
arc_label_df = pd.DataFrame(
    {"x": [arc_r * np.cos(arc_mid_angle) - 0.15], "y": [arc_r * np.sin(arc_mid_angle) + 0.15], "text": ["π/4"]}
)
arc_label = (
    alt.Chart(arc_label_df)
    .mark_text(fontSize=16, fontStyle="italic", fontWeight="bold", color="#6A5ACD", opacity=0.8)
    .encode(x="x:Q", y="y:Q", text="text:N")
)

# Vector lines from origin
vectors = (
    alt.Chart(arrow_df)
    .mark_line(strokeWidth=2)
    .encode(
        x="x:Q",
        y="y:Q",
        detail="group:N",
        order="order:O",
        color=alt.Color("category:N", scale=color_scale, legend=None),
        opacity=opacity_cond,
    )
    .add_params(highlight)
)

# Arrowheads (rotated triangles)
arrowheads = (
    alt.Chart(arrowhead_df)
    .mark_point(shape="triangle-up", filled=True, size=250)
    .encode(
        x="x:Q",
        y="y:Q",
        angle=alt.Angle("angle:Q"),
        color=alt.Color("category:N", scale=color_scale, legend=None),
        opacity=opacity_cond,
    )
    .add_params(highlight)
)

# Scatter points with legend-bound selection
points = (
    alt.Chart(df)
    .mark_point(filled=True, size=220, stroke="white", strokeWidth=2)
    .encode(
        x=alt.X(
            "real:Q",
            title="Real Axis",
            scale=alt.Scale(domain=[-axis_limit, axis_limit]),
            axis=alt.Axis(
                tickCount=11,
                labelFontSize=16,
                titleFontSize=20,
                gridDash=[3, 3],
                gridOpacity=0.12,
                titleColor="#333333",
                labelColor="#555555",
            ),
        ),
        y=alt.Y(
            "imaginary:Q",
            title="Imaginary Axis",
            scale=alt.Scale(domain=[-axis_limit, axis_limit]),
            axis=alt.Axis(
                tickCount=11,
                labelFontSize=16,
                titleFontSize=20,
                gridDash=[3, 3],
                gridOpacity=0.12,
                titleColor="#333333",
                labelColor="#555555",
            ),
        ),
        color=alt.Color(
            "category:N",
            scale=color_scale,
            legend=alt.Legend(
                title="Category",
                titleFontSize=18,
                labelFontSize=16,
                symbolType="circle",
                symbolSize=200,
                symbolStrokeWidth=0,
                orient="top-right",
                titleColor="#333333",
                labelColor="#444444",
            ),
        ),
        opacity=opacity_cond,
        tooltip=[
            alt.Tooltip("label:N", title="Label"),
            alt.Tooltip("rect_form:N", title="Value"),
            alt.Tooltip("category:N", title="Category"),
        ],
    )
    .add_params(highlight)
)

# Annotations at computed label positions
annotations = (
    alt.Chart(df)
    .mark_text(fontSize=16, fontWeight="bold", color="#333333")
    .encode(x="label_x:Q", y="label_y:Q", text="annotation:N", opacity=opacity_cond)
    .add_params(highlight)
)

# Axis endpoint labels (Re, Im)
axis_labels_df = pd.DataFrame({"x": [axis_limit - 0.15, 0.22], "y": [-0.22, axis_limit - 0.1], "text": ["Re", "Im"]})
axis_labels = (
    alt.Chart(axis_labels_df)
    .mark_text(fontSize=18, fontStyle="italic", fontWeight="bold", color="#666666")
    .encode(x="x:Q", y="y:Q", text="text:N")
)

# Compose all layers
chart = (
    alt.layer(axes, unit_circle, rotation_arc, arc_label, vectors, arrowheads, points, annotations, axis_labels)
    .properties(
        width=1200,
        height=1200,
        title=alt.Title(
            "scatter-complex-plane · altair · pyplots.ai",
            fontSize=28,
            anchor="middle",
            color="#222222",
            subtitle="Roots of unity, arbitrary points & rotation (z → z·e^(iπ/4)) in the complex plane",
            subtitleFontSize=17,
            subtitleColor="#666666",
        ),
    )
    .resolve_scale(color="independent")
    .configure_axis(titlePadding=14)
    .configure_view(strokeWidth=0)
    .interactive()
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
