""" pyplots.ai
stereonet-equal-area: Structural Geology Stereonet (Equal-Area Projection)
Library: altair 6.0.0 | Python 3.14.3
Quality: 81/100 | Created: 2026-03-15
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Field measurements of geological structures
np.random.seed(42)

bedding_strike = np.random.normal(45, 12, 25)
bedding_dip = np.random.normal(35, 8, 25)

fault_strike = np.random.normal(310, 15, 18)
fault_dip = np.random.normal(70, 10, 18)

joint_strike = np.random.normal(90, 10, 22)
joint_dip = np.random.normal(80, 7, 22)

strikes = np.concatenate([bedding_strike, fault_strike, joint_strike]) % 360
dips = np.clip(np.concatenate([bedding_dip, fault_dip, joint_dip]), 0, 90)
feature_types = ["Bedding"] * len(bedding_strike) + ["Fault"] * len(fault_strike) + ["Joint"] * len(joint_strike)

# Equal-area (Schmidt) projection: poles to planes
pole_trend = np.radians((strikes + 90) % 360)
pole_r = np.sqrt(2) * np.sin(np.radians(dips) / 2)
pole_x = pole_r * np.sin(pole_trend)
pole_y = pole_r * np.cos(pole_trend)

df_poles = pd.DataFrame(
    {"x": pole_x, "y": pole_y, "feature_type": feature_types, "strike": np.round(strikes, 1), "dip": np.round(dips, 1)}
)

# Great circles for each measurement
gc_rows = []
for i in range(len(strikes)):
    s_rad = np.radians(strikes[i])
    d_rad = np.radians(dips[i])
    dd_rad = s_rad + np.pi / 2
    v1 = np.array([np.sin(s_rad), np.cos(s_rad), 0.0])
    v2 = np.array([np.cos(d_rad) * np.sin(dd_rad), np.cos(d_rad) * np.cos(dd_rad), -np.sin(d_rad)])
    for j, rake in enumerate(np.linspace(0, np.pi, 61)):
        line = np.cos(rake) * v1 + np.sin(rake) * v2
        if line[2] > 0:
            line = -line
        plunge = np.arcsin(-line[2])
        trend = np.arctan2(line[0], line[1])
        r = np.sqrt(2) * np.sin((np.pi / 2 - plunge) / 2)
        gc_rows.append(
            {"x": r * np.sin(trend), "y": r * np.cos(trend), "feature_type": feature_types[i], "gc_id": i, "order": j}
        )
df_gc = pd.DataFrame(gc_rows)

# Primitive circle
r_prim = np.sqrt(2) * np.sin(np.pi / 4)
theta_circ = np.linspace(0, 2 * np.pi, 361)
df_circle = pd.DataFrame({"x": r_prim * np.sin(theta_circ), "y": r_prim * np.cos(theta_circ), "order": range(361)})

# Tick marks every 10 degrees
tick_rows = []
for deg in range(0, 360, 10):
    rad = np.radians(deg)
    tick_len = 0.06 if deg % 30 == 0 else 0.04
    tick_rows.append({"x": r_prim * np.sin(rad), "y": r_prim * np.cos(rad), "tid": deg, "order": 0})
    tick_rows.append(
        {"x": (r_prim - tick_len) * np.sin(rad), "y": (r_prim - tick_len) * np.cos(rad), "tid": deg, "order": 1}
    )
df_ticks = pd.DataFrame(tick_rows)

# Cardinal labels
lbl_r = r_prim + 0.09
df_dirs = pd.DataFrame(
    {"x": [0, lbl_r, 0, -lbl_r], "y": [lbl_r + 0.03, 0, -lbl_r - 0.03, 0], "label": ["N", "E", "S", "W"]}
)

# Grid circles at 30 and 60 degree dip
grid_rows = []
for dip_g in [30, 60]:
    r_g = np.sqrt(2) * np.sin(np.radians(dip_g) / 2)
    for j, t in enumerate(np.linspace(0, 2 * np.pi, 181)):
        grid_rows.append({"x": r_g * np.sin(t), "y": r_g * np.cos(t), "level": dip_g, "order": j})
df_grid = pd.DataFrame(grid_rows)

# Grid cross lines
df_cross = pd.DataFrame(
    {
        "x": [0, 0, -r_prim, r_prim],
        "y": [-r_prim, r_prim, 0, 0],
        "line_id": ["NS", "NS", "EW", "EW"],
        "order": [0, 1, 0, 1],
    }
)

# Density contours using Gaussian KDE - extract iso-lines via marching squares
n_grid = 100
gx = np.linspace(-r_prim, r_prim, n_grid)
gy = np.linspace(-r_prim, r_prim, n_grid)
gxx, gyy = np.meshgrid(gx, gy)
bw = 0.10
density = np.zeros_like(gxx)
for px, py in zip(pole_x, pole_y, strict=True):
    density += np.exp(-((gxx - px) ** 2 + (gyy - py) ** 2) / (2 * bw**2))
density /= len(pole_x) * 2 * np.pi * bw**2
circ_mask = gxx**2 + gyy**2 <= r_prim**2
density[~circ_mask] = 0.0

# Extract contour lines using simple marching squares
contour_levels = np.linspace(np.nanmax(density) * 0.15, np.nanmax(density) * 0.85, 5)
contour_rows = []
for lev_idx, level in enumerate(contour_levels):
    for ri in range(n_grid - 1):
        for ci in range(n_grid - 1):
            corners = [density[ri, ci], density[ri, ci + 1], density[ri + 1, ci + 1], density[ri + 1, ci]]
            above = [c >= level for c in corners]
            n_above = sum(above)
            if n_above == 0 or n_above == 4:
                continue
            edges = []
            edge_pairs = [
                (0, 1, ri, ci, ri, ci + 1),
                (1, 2, ri, ci + 1, ri + 1, ci + 1),
                (2, 3, ri + 1, ci + 1, ri + 1, ci),
                (3, 0, ri + 1, ci, ri, ci),
            ]
            for c1, c2, r1, col1, r2, col2 in edge_pairs:
                if above[c1] != above[c2]:
                    t = (level - corners[c1]) / (corners[c2] - corners[c1]) if corners[c2] != corners[c1] else 0.5
                    ex = gxx[r1, col1] + t * (gxx[r2, col2] - gxx[r1, col1])
                    ey = gyy[r1, col1] + t * (gyy[r2, col2] - gyy[r1, col1])
                    edges.append((ex, ey))
            if len(edges) >= 2:
                seg_id = f"c{lev_idx}_{ri}_{ci}"
                contour_rows.append(
                    {"x": edges[0][0], "y": edges[0][1], "seg_id": seg_id, "level": float(lev_idx), "order": 0}
                )
                contour_rows.append(
                    {"x": edges[1][0], "y": edges[1][1], "seg_id": seg_id, "level": float(lev_idx), "order": 1}
                )

df_contours = (
    pd.DataFrame(contour_rows) if contour_rows else pd.DataFrame(columns=["x", "y", "seg_id", "level", "order"])
)

# Mean orientation for each feature type (for annotations)
mean_rows = []
for ft in ["Bedding", "Fault", "Joint"]:
    mask = np.array(feature_types) == ft
    mx = np.mean(pole_x[mask])
    my = np.mean(pole_y[mask])
    ms = np.mean(strikes[mask])
    md = np.mean(dips[mask])
    mean_rows.append({"x": mx, "y": my, "feature_type": ft, "label": f"μ {ms:.0f}°/{md:.0f}°"})
df_means = pd.DataFrame(mean_rows)

# Plot
color_map = {"Bedding": "#306998", "Fault": "#C1432E", "Joint": "#2A9D8F"}
color_scale = alt.Scale(domain=list(color_map.keys()), range=list(color_map.values()))
x_enc = alt.X("x:Q", axis=None, scale=alt.Scale(domain=[-1.25, 1.25]))
y_enc = alt.Y("y:Q", axis=None, scale=alt.Scale(domain=[-1.25, 1.25]))

# Interactive selection for highlighting by feature type
selection = alt.selection_point(fields=["feature_type"], bind="legend")

# Density contour lines (smooth, not blocky)
contour_layer = (
    (
        alt.Chart(df_contours)
        .mark_line(strokeWidth=1.0)
        .encode(
            x=x_enc,
            y=y_enc,
            detail="seg_id:N",
            order="order:O",
            color=alt.Color("level:Q", scale=alt.Scale(scheme="greys", domain=[0, len(contour_levels)]), legend=None),
            opacity=alt.value(0.35),
        )
    )
    if len(df_contours) > 0
    else alt.Chart(pd.DataFrame({"x": [0], "y": [0]})).mark_point(size=0).encode(x="x:Q", y="y:Q")
)

grid_circles = (
    alt.Chart(df_grid)
    .mark_line(strokeWidth=0.8, color="#cccccc", opacity=0.5)
    .encode(x=x_enc, y=y_enc, detail="level:N", order="order:O")
)

cross_lines = (
    alt.Chart(df_cross)
    .mark_line(strokeWidth=0.8, color="#cccccc", opacity=0.5)
    .encode(x=x_enc, y=y_enc, detail="line_id:N", order="order:O")
)

great_circles = (
    alt.Chart(df_gc)
    .mark_line(strokeWidth=1.0)
    .encode(
        x=x_enc,
        y=y_enc,
        detail="gc_id:N",
        order="order:O",
        color=alt.Color("feature_type:N", scale=color_scale, legend=None),
        opacity=alt.condition(selection, alt.value(0.35), alt.value(0.05)),
    )
    .add_params(selection)
)

prim_circle = alt.Chart(df_circle).mark_line(strokeWidth=2.5, color="#333333").encode(x=x_enc, y=y_enc, order="order:O")

tick_marks = (
    alt.Chart(df_ticks)
    .mark_line(strokeWidth=1.5, color="#333333")
    .encode(x=x_enc, y=y_enc, detail="tid:N", order="order:O")
)

dir_labels = (
    alt.Chart(df_dirs)
    .mark_text(fontSize=24, fontWeight="bold", color="#333333")
    .encode(x=x_enc, y=y_enc, text="label:N")
)

poles_layer = (
    alt.Chart(df_poles)
    .mark_point(filled=True, size=180, stroke="white", strokeWidth=1.2)
    .encode(
        x=x_enc,
        y=y_enc,
        color=alt.Color(
            "feature_type:N",
            scale=color_scale,
            title="Feature Type",
            legend=alt.Legend(
                titleFontSize=20,
                labelFontSize=18,
                symbolSize=300,
                orient="top-right",
                titleColor="#333333",
                labelColor="#333333",
            ),
        ),
        opacity=alt.condition(selection, alt.value(0.9), alt.value(0.15)),
        tooltip=[
            alt.Tooltip("feature_type:N", title="Type"),
            alt.Tooltip("strike:Q", title="Strike (°)"),
            alt.Tooltip("dip:Q", title="Dip (°)"),
        ],
    )
    .add_params(selection)
)

# Mean orientation markers with labels
mean_markers = (
    alt.Chart(df_means)
    .mark_point(shape="cross", size=400, strokeWidth=3)
    .encode(
        x=x_enc,
        y=y_enc,
        color=alt.Color("feature_type:N", scale=color_scale, legend=None),
        opacity=alt.condition(selection, alt.value(1.0), alt.value(0.15)),
    )
    .add_params(selection)
)

mean_labels = (
    alt.Chart(df_means)
    .mark_text(fontSize=16, fontWeight="bold", dy=-18, color="#333333")
    .encode(x=x_enc, y=y_enc, text="label:N", opacity=alt.condition(selection, alt.value(0.9), alt.value(0.1)))
    .add_params(selection)
)

chart = (
    alt.layer(
        contour_layer,
        grid_circles,
        cross_lines,
        great_circles,
        prim_circle,
        tick_marks,
        dir_labels,
        poles_layer,
        mean_markers,
        mean_labels,
    )
    .properties(
        width=1200,
        height=1200,
        title=alt.Title(
            text="stereonet-equal-area · altair · pyplots.ai",
            subtitle="Lower-Hemisphere Equal-Area (Schmidt) Projection",
            fontSize=28,
            subtitleFontSize=20,
            subtitleColor="#666666",
        ),
    )
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
