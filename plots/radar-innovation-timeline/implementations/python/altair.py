""" pyplots.ai
radar-innovation-timeline: Innovation Radar with Time-Horizon Rings
Library: altair 6.0.0 | Python 3.14.3
Quality: 86/100 | Created: 2026-02-18
"""

from collections import defaultdict

import altair as alt
import numpy as np
import pandas as pd


np.random.seed(42)

# --- Configuration ---
rings = ["Adopt", "Trial", "Assess", "Hold"]
sectors = ["AI & ML", "Cloud & Infra", "Data Engineering", "Security"]
n_sectors = len(sectors)

# 270-degree arc layout
start_angle = -np.pi / 4
total_arc = 1.5 * np.pi
sector_arc = total_arc / n_sectors
sector_bounds = {s: (start_angle + i * sector_arc, start_angle + (i + 1) * sector_arc) for i, s in enumerate(sectors)}

# Ring bands — wider Adopt ring to reduce crowding at inner radius
ring_inner = {"Adopt": 0.5, "Trial": 1.45, "Assess": 2.4, "Hold": 3.35}
ring_outer = {"Adopt": 1.3, "Trial": 2.25, "Assess": 3.2, "Hold": 4.1}
ring_boundary_radii = [1.375, 2.325, 3.275, 4.175]

sector_colors = {"AI & ML": "#306998", "Cloud & Infra": "#E07A2F", "Data Engineering": "#2CA02C", "Security": "#9467BD"}
ring_tints = {"Adopt": "#306998", "Trial": "#4A8FBF", "Assess": "#7BB5D6", "Hold": "#B0D4E8"}
ring_opacities = {"Adopt": 0.18, "Trial": 0.11, "Assess": 0.05, "Hold": 0.02}
ring_shapes = {"Adopt": "circle", "Trial": "diamond", "Assess": "triangle-up", "Hold": "square"}

# --- Data: 25 technology items ---
items = [
    {"name": "LLM Agents", "ring": "Adopt", "sector": "AI & ML"},
    {"name": "RAG Pipelines", "ring": "Adopt", "sector": "AI & ML"},
    {"name": "Vision Models", "ring": "Trial", "sector": "AI & ML"},
    {"name": "AI Code Review", "ring": "Trial", "sector": "AI & ML"},
    {"name": "Neuro-symb. AI", "ring": "Assess", "sector": "AI & ML"},
    {"name": "Auto. ML Ops", "ring": "Assess", "sector": "AI & ML"},
    {"name": "AGI Frameworks", "ring": "Hold", "sector": "AI & ML"},
    {"name": "Edge Computing", "ring": "Adopt", "sector": "Cloud & Infra"},
    {"name": "Platform Eng.", "ring": "Adopt", "sector": "Cloud & Infra"},
    {"name": "WASM Backends", "ring": "Trial", "sector": "Cloud & Infra"},
    {"name": "FinOps Tools", "ring": "Trial", "sector": "Cloud & Infra"},
    {"name": "Serverless GPUs", "ring": "Assess", "sector": "Cloud & Infra"},
    {"name": "Quantum Cloud", "ring": "Hold", "sector": "Cloud & Infra"},
    {"name": "Data Contracts", "ring": "Adopt", "sector": "Data Engineering"},
    {"name": "Lakehouse Arch.", "ring": "Trial", "sector": "Data Engineering"},
    {"name": "Streaming SQL", "ring": "Trial", "sector": "Data Engineering"},
    {"name": "Data Mesh", "ring": "Assess", "sector": "Data Engineering"},
    {"name": "Graph Analytics", "ring": "Assess", "sector": "Data Engineering"},
    {"name": "Quantum DB", "ring": "Hold", "sector": "Data Engineering"},
    {"name": "Zero Trust", "ring": "Adopt", "sector": "Security"},
    {"name": "SBOM Tooling", "ring": "Adopt", "sector": "Security"},
    {"name": "AI Threat Det.", "ring": "Trial", "sector": "Security"},
    {"name": "Passkeys", "ring": "Trial", "sector": "Security"},
    {"name": "Confid. Compute", "ring": "Assess", "sector": "Security"},
    {"name": "Post-Q. Crypto", "ring": "Assess", "sector": "Security"},
    {"name": "Homomorphic Enc.", "ring": "Hold", "sector": "Security"},
]

# --- Position items with alternating label offsets to prevent overlap ---
groups = defaultdict(list)
for item in items:
    groups[(item["sector"], item["ring"])].append(item)

records = []
for (sector, ring), group_items in groups.items():
    a_min, a_max = sector_bounds[sector]
    padding = 0.12 * sector_arc
    n = len(group_items)
    r_in, r_out = ring_inner[ring], ring_outer[ring]
    r_mid = (r_in + r_out) / 2
    ring_idx = rings.index(ring)
    # Stagger angular positions by ring to separate cross-ring labels
    ring_jitter = 0.16 * sector_arc * ((-1) ** ring_idx)
    for idx, it in enumerate(group_items):
        angle = a_min + padding + (idx + 0.5) / n * (a_max - a_min - 2 * padding) + ring_jitter
        r_offset = 0.30 * ((-1) ** idx) if n > 1 else 0
        radius = r_mid + r_offset
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        # Push label outward from center along radial direction
        outward_r = 0.42 + 0.16 * (idx % 2)  # alternate offset for separation
        label_x = x + outward_r * np.cos(angle)
        label_y = y + outward_r * np.sin(angle)
        # Align text outward: left-align on right side, right-align on left side
        text_align = "left" if x > 0 else "right" if x < -0.5 else "center"
        records.append(
            {
                "name": it["name"],
                "ring": ring,
                "sector": sector,
                "x": x,
                "y": y,
                "label_x": label_x,
                "label_y": label_y,
                "text_align": text_align,
            }
        )

df = pd.DataFrame(records)

# --- Geometry: ring fills, arcs, spokes ---
fill_pts = 80
ring_fill_rows = []
for rn in rings:
    r_in, r_out = ring_inner[rn], ring_outer[rn]
    thetas = np.linspace(start_angle, start_angle + total_arc, fill_pts)
    for i, t in enumerate(thetas):
        ring_fill_rows.append({"x": r_in * np.cos(t), "y": r_in * np.sin(t), "ring": rn, "order": i})
    for i, t in enumerate(thetas[::-1]):
        ring_fill_rows.append({"x": r_out * np.cos(t), "y": r_out * np.sin(t), "ring": rn, "order": fill_pts + i})
    ring_fill_rows.append(
        {"x": r_in * np.cos(thetas[0]), "y": r_in * np.sin(thetas[0]), "ring": rn, "order": 2 * fill_pts}
    )
df_fills = pd.DataFrame(ring_fill_rows)

arc_pts = 100
arc_rows = []
for rb in ring_boundary_radii:
    for i, t in enumerate(np.linspace(start_angle, start_angle + total_arc, arc_pts)):
        arc_rows.append({"x": rb * np.cos(t), "y": rb * np.sin(t), "rb": rb, "order": i})
df_arcs = pd.DataFrame(arc_rows)

spoke_rows = []
for i in range(n_sectors + 1):
    a = start_angle + i * sector_arc
    spoke_rows.append({"x": 0, "y": 0, "sid": i, "order": 0})
    spoke_rows.append({"x": 4.3 * np.cos(a), "y": 4.3 * np.sin(a), "sid": i, "order": 1})
df_spokes = pd.DataFrame(spoke_rows)

# Sector headers beyond outer ring
sec_r = 4.85
df_sec = pd.DataFrame(
    [
        {
            "x": sec_r * np.cos(start_angle + (i + 0.5) * sector_arc),
            "y": sec_r * np.sin(start_angle + (i + 0.5) * sector_arc),
            "sector": s,
        }
        for i, s in enumerate(sectors)
    ]
)

# Ring labels in the gap area (below center, aligned with ring radii)
gap_angle = 3 * np.pi / 2  # Bottom center of the gap
df_rlabels = pd.DataFrame(
    [
        {
            "x": (ring_inner[rn] + ring_outer[rn]) / 2 * np.cos(gap_angle) + 0.15,
            "y": (ring_inner[rn] + ring_outer[rn]) / 2 * np.sin(gap_angle),
            "ring": rn,
        }
        for rn in rings
    ]
)

# --- Altair chart assembly ---
chart_size = 1200
dom = [-5.7, 5.7]
x_enc = alt.X("x:Q", scale=alt.Scale(domain=dom), axis=None)
y_enc = alt.Y("y:Q", scale=alt.Scale(domain=dom), axis=None)
color_scale = alt.Scale(domain=list(sector_colors), range=list(sector_colors.values()))
shape_scale = alt.Scale(domain=rings, range=[ring_shapes[r] for r in rings])

# Hover selection — Altair interactive highlight
hover = alt.selection_point(on="pointerover", fields=["name"], nearest=True, empty=False)

# Ring fill bands
fill_layers = [
    alt.Chart(df_fills[df_fills["ring"] == rn])
    .mark_line(strokeWidth=0, filled=True, fill=ring_tints[rn], fillOpacity=ring_opacities[rn])
    .encode(x=x_enc, y=y_enc, order="order:Q")
    for rn in rings
]

# Ring boundary arcs
arcs = (
    alt.Chart(df_arcs)
    .mark_line(strokeWidth=1.2, stroke="#aaaaaa", opacity=0.4)
    .encode(x=x_enc, y=y_enc, detail="rb:N", order="order:Q")
)

# Sector spokes
spokes = (
    alt.Chart(df_spokes)
    .mark_line(strokeWidth=1.2, stroke="#999999", opacity=0.4)
    .encode(x=x_enc, y=y_enc, detail="sid:N", order="order:Q")
)

# Data points with hover-driven size highlight
points = (
    alt.Chart(df)
    .mark_point(filled=True, strokeWidth=1.5, stroke="white", opacity=0.92)
    .encode(
        x=x_enc,
        y=y_enc,
        color=alt.Color(
            "sector:N",
            scale=color_scale,
            legend=alt.Legend(
                title="Sector",
                titleFontSize=18,
                labelFontSize=16,
                orient="none",
                legendX=300,
                legendY=1050,
                symbolSize=280,
                symbolStrokeWidth=0,
                direction="horizontal",
            ),
        ),
        shape=alt.Shape(
            "ring:N",
            scale=shape_scale,
            legend=alt.Legend(
                title="Ring",
                titleFontSize=18,
                labelFontSize=16,
                orient="none",
                legendX=300,
                legendY=1105,
                symbolSize=280,
                symbolStrokeWidth=0,
                direction="horizontal",
            ),
        ),
        size=alt.condition(hover, alt.value(500), alt.value(300)),
        tooltip=["name:N", "sector:N", "ring:N"],
    )
    .add_params(hover)
)

# Item labels at offset positions, aligned outward from center
# Split by text alignment to avoid overlap
labels_left = (
    alt.Chart(df[df["text_align"] == "left"])
    .mark_text(fontSize=20, color="#222222", fontWeight="normal", align="left")
    .encode(
        x=alt.X("label_x:Q", scale=alt.Scale(domain=dom), axis=None),
        y=alt.Y("label_y:Q", scale=alt.Scale(domain=dom), axis=None),
        text="name:N",
        opacity=alt.condition(hover, alt.value(1.0), alt.value(0.85)),
    )
)
labels_right = (
    alt.Chart(df[df["text_align"] == "right"])
    .mark_text(fontSize=20, color="#222222", fontWeight="normal", align="right")
    .encode(
        x=alt.X("label_x:Q", scale=alt.Scale(domain=dom), axis=None),
        y=alt.Y("label_y:Q", scale=alt.Scale(domain=dom), axis=None),
        text="name:N",
        opacity=alt.condition(hover, alt.value(1.0), alt.value(0.85)),
    )
)
labels_center = (
    alt.Chart(df[df["text_align"] == "center"])
    .mark_text(fontSize=20, color="#222222", fontWeight="normal", align="center")
    .encode(
        x=alt.X("label_x:Q", scale=alt.Scale(domain=dom), axis=None),
        y=alt.Y("label_y:Q", scale=alt.Scale(domain=dom), axis=None),
        text="name:N",
        opacity=alt.condition(hover, alt.value(1.0), alt.value(0.85)),
    )
)

# Sector headers
sec_headers = (
    alt.Chart(df_sec)
    .mark_text(fontSize=24, fontWeight="bold", color="#333333")
    .encode(x=x_enc, y=y_enc, text="sector:N")
)

# Ring labels inside bands
rlabels = (
    alt.Chart(df_rlabels)
    .mark_text(fontSize=20, fontWeight="bold", color="#555555", align="left", baseline="middle")
    .encode(x=x_enc, y=y_enc, text="ring:N")
)

# Leader lines connecting markers to labels
leaders = (
    alt.Chart(df)
    .mark_rule(strokeWidth=0.7, opacity=0.25, color="#888888")
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=dom), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=dom), axis=None),
        x2="label_x:Q",
        y2="label_y:Q",
    )
)

# Combine all layers
chart = (
    alt.layer(
        *fill_layers, arcs, spokes, leaders, points, labels_left, labels_right, labels_center, sec_headers, rlabels
    )
    .properties(
        width=chart_size,
        height=chart_size,
        title=alt.Title("radar-innovation-timeline · altair · pyplots.ai", fontSize=28, anchor="middle", offset=20),
    )
    .configure_view(strokeWidth=0)
    .configure_legend(padding=12, cornerRadius=4, fillColor="#fafafa", strokeColor="#dddddd")
)

chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
