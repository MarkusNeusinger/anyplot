"""anyplot.ai
hive-basic: Basic Hive Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-07
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per axis group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
MIN_RADIUS = 0.25  # nearest a node sits to the center
MAX_RADIUS = 0.85  # farthest a node sits from the center
AXIS_START_ANGLE = 30  # degrees of the first axis; the others follow at equal spacing

# Columns: set these to your table's column names
MODULE = "Module"  # role: nodes
MODULE_TYPE = "Module type"  # role: axis_attribute
IMPORTANCE = "Importance (share of dependents)"  # role: extra
SOURCE = "Source"  # role: edges
TARGET = "Target"  # role: extra

# Data: replace this block with your own tables, for example df = pd.read_csv("edges.csv")
nodes = pd.DataFrame(
    {
        MODULE: ["Main", "Database", "Config", "Logger", "Cache"]
        + ["HTTP", "FileIO", "String", "DateTime"]
        + ["REST API", "WebUI", "CLI"],
        MODULE_TYPE: ["Core"] * 5 + ["Utility"] * 4 + ["Interface"] * 3,
        IMPORTANCE: [1.0, 0.80, 0.60, 0.40, 0.20] + [1.0, 0.75, 0.50, 0.25] + [1.0, 0.66, 0.33],
    }
)
df = pd.DataFrame(
    {
        SOURCE: ["Main", "Main", "Config", "Config", "Logger", "Logger", "Cache", "Database"]
        + ["Main", "Main", "Config", "Database", "Logger"]
        + ["HTTP", "HTTP", "String", "FileIO", "DateTime"],
        TARGET: ["String", "FileIO", "FileIO", "String", "DateTime", "FileIO", "DateTime", "String"]
        + ["REST API", "CLI", "REST API", "REST API", "WebUI"]
        + ["REST API", "WebUI", "CLI", "CLI", "WebUI"],
    }
)

# Plot: reads only the tables and the constants above
groups = list(nodes[MODULE_TYPE].unique())
angle = {g: np.radians(AXIS_START_ANGLE + 360 / len(groups) * i) for i, g in enumerate(groups)}
color_scale = alt.Scale(domain=groups, range=IMPRINT_PALETTE)

# Node positions: direction from the axis group, distance from the importance
radius = MIN_RADIUS + (MAX_RADIUS - MIN_RADIUS) * nodes[IMPORTANCE] / nodes[IMPORTANCE].max()
theta = nodes[MODULE_TYPE].map(angle)
nodes["x"] = radius * np.cos(theta)
nodes["y"] = radius * np.sin(theta)
position = nodes.set_index(MODULE)[["x", "y"]]

# Labels sit beside their node: right on the right half, left on the left half, alternating in between
cos_t = np.cos(theta)
rank = nodes.groupby(MODULE_TYPE, sort=False).cumcount()
nodes["side"] = np.where(cos_t > 0.1, "right", np.where(cos_t < -0.1, "left", np.where(rank % 2 == 0, "right", "left")))

# Edges as quadratic Bezier curves whose control point is pulled toward the center
t = np.linspace(0, 1, 30)
curve_rows = []
for i, (src, dst) in enumerate(zip(df[SOURCE], df[TARGET], strict=True)):
    p0 = position.loc[src].to_numpy()
    p2 = position.loc[dst].to_numpy()
    p1 = 0.2 * (p0 + p2)
    pts = ((1 - t) ** 2)[:, None] * p0 + (2 * (1 - t) * t)[:, None] * p1 + (t**2)[:, None] * p2
    curve_rows.append(pd.DataFrame({"x": pts[:, 0], "y": pts[:, 1], "step": t, "edge": i, "link": f"{src} → {dst}"}))
curves = pd.concat(curve_rows, ignore_index=True)

# Axis lines and their labels
axes = pd.DataFrame(
    {
        "group": groups,
        "x2": [0.95 * np.cos(angle[g]) for g in groups],
        "y2": [0.95 * np.sin(angle[g]) for g in groups],
        "lx": [1.14 * np.cos(angle[g]) for g in groups],
        "ly": [1.14 * np.sin(angle[g]) for g in groups],
    }
)
axes["x"] = 0.0
axes["y"] = 0.0

view = alt.Scale(domain=[-1.12, 1.12])
xy = {"x": alt.X("x:Q", scale=view, axis=None), "y": alt.Y("y:Q", scale=view, axis=None)}
group_color = alt.Color("group:N", scale=color_scale, legend=None)

edge_layer = (
    alt.Chart(curves)
    .mark_line(strokeWidth=1.2, opacity=0.3, color=INK_SOFT)
    .encode(**xy, order="step:Q", detail="edge:N", tooltip=["link:N"])
)
axis_layer = (
    alt.Chart(axes).mark_rule(strokeWidth=2.5, opacity=0.75).encode(**xy, x2="x2:Q", y2="y2:Q", color=group_color)
)
node_layer = (
    alt.Chart(nodes.rename(columns={MODULE_TYPE: "group"}))
    .mark_circle(size=150, opacity=0.95, stroke=PAGE_BG, strokeWidth=1.5)
    .encode(
        **xy,
        color=group_color,
        tooltip=[
            alt.Tooltip(f"{MODULE}:N", title=MODULE),
            alt.Tooltip("group:N", title=MODULE_TYPE),
            alt.Tooltip(f"{IMPORTANCE}:Q", title=IMPORTANCE),
        ],
    )
)
label_layers = [
    alt.Chart(nodes[nodes["side"] == side])
    .mark_text(
        fontSize=11,
        fontWeight="bold",
        align="left" if side == "right" else "right",
        dx=11 if side == "right" else -11,
        color=INK,
    )
    .encode(**xy, text=f"{MODULE}:N")
    for side in ("right", "left")
]
axis_label_layer = (
    alt.Chart(axes)
    .mark_text(fontSize=15, fontWeight="bold")
    .encode(
        x=alt.X("lx:Q", scale=view, axis=None),
        y=alt.Y("ly:Q", scale=view, axis=None),
        text="group:N",
        color=group_color,
    )
)

chart = (
    alt.layer(edge_layer, axis_layer, node_layer, *label_layers, axis_label_layer)
    .properties(
        width=460,
        height=460,
        background=PAGE_BG,
        title=alt.Title(
            text="hive-basic · python · altair · anyplot.ai",
            subtitle=f"Distance from the center = {IMPORTANCE.lower()}",
            fontSize=16,
            subtitleFontSize=11,
            anchor="middle",
            color=INK,
            subtitleColor=INK_SOFT,
        ),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
)

# Save: pad (never crop) to the 2400 x 2400 square canvas
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
TARGET_SIZE = (2400, 2400)
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_SIZE[0] or img.height > TARGET_SIZE[1]:
    raise SystemExit(f"altair produced {img.width}x{img.height}, exceeds target {TARGET_SIZE}; shrink width/height")
canvas = Image.new("RGB", TARGET_SIZE, PAGE_BG)
canvas.paste(img, ((TARGET_SIZE[0] - img.width) // 2, (TARGET_SIZE[1] - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
