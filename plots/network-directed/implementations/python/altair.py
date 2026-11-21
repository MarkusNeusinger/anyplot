""" anyplot.ai
network-directed: Directed Network Graph
Library: altair 6.3.0 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-21
"""

import os
import sys
from pathlib import Path


# Avoid name collision with this script's own name (altair.py)
sys.path = [p for p in sys.path if p != str(Path(__file__).parent)]

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per module type in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
VIEW_W, VIEW_H = 620, 320  # inner view in px; the layout is computed in these units
NODE_R = 11  # node radius in view px
ARROW_SIDE = 11  # arrowhead width and height in view px
BEND = 0.12  # sideways bend of the two edges of a mutual pair, as a share of their length

# Columns: set these to your table's column names
SOURCE = "Source module"  # role: edges
TARGET = "Target module"  # role: extra
NODE = "Module"  # role: nodes
GROUP = "Module type"  # role: extra

# Data: replace with your own edge list (for example pd.read_csv("edges.csv")) and a node table
# with one row per module and its group; arrows point from SOURCE to TARGET.
edge_pairs = [
    ("App", "API"),
    ("App", "Auth"),
    ("App", "Router"),
    ("API", "Database"),
    ("API", "Cache"),
    ("API", "Models"),
    ("Auth", "Database"),
    ("Auth", "Cache"),
    ("Auth", "Logger"),
    ("Database", "Config"),
    ("Database", "Logger"),
    ("Cache", "Config"),
    ("Cache", "Logger"),
    ("Router", "Middleware"),
    ("Router", "API"),
    ("Middleware", "Auth"),
    ("Middleware", "Logger"),
    ("Models", "Schemas"),
    ("Models", "Utils"),
    ("Schemas", "Utils"),
    ("Logger", "Config"),
    ("Utils", "Config"),
    ("API", "Auth"),
    ("Cache", "Database"),
]
nodes = pd.DataFrame(
    {
        NODE: ["App", "API", "Auth", "Database", "Cache", "Logger"]
        + ["Config", "Utils", "Models", "Schemas", "Router", "Middleware"],
        GROUP: ["Entry", "Core", "Core", "Core", "Service", "Utility"]
        + ["Utility", "Utility", "Data", "Data", "Core", "Core"],
    }
)
df = pd.DataFrame(edge_pairs, columns=[SOURCE, TARGET])

# Plot: reads only df, nodes and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
module_types = list(dict.fromkeys(nodes[GROUP]))
pairs = list(zip(df[SOURCE], df[TARGET], strict=True))

# Hierarchical layout: column = longest dependency path from a module nobody imports
depth = dict.fromkeys(nodes[NODE], 0)
for _ in range(len(nodes)):
    for src, dst in pairs:
        depth[dst] = max(depth[dst], min(depth[src] + 1, len(nodes) - 1))
columns = {d: [n for n in nodes[NODE] if depth[n] == d] for d in sorted(set(depth.values()))}

# Order each column by the mean row of its neighbours to reduce crossings
rank = {n: i for members in columns.values() for i, n in enumerate(members)}
for _ in range(4):
    for members in columns.values():
        members.sort(key=lambda n: np.mean([rank[b if a == n else a] for a, b in pairs if n in (a, b)]))
        rank.update({n: i / max(len(members) - 1, 1) * 10 for i, n in enumerate(members)})

margin_x, margin_y = 55, 34
pos = {}
for d, members in columns.items():
    for i, n in enumerate(members):
        x = margin_x + d / max(len(columns) - 1, 1) * (VIEW_W - 2 * margin_x)
        y = margin_y + (i + 0.5) / len(members) * (VIEW_H - 2 * margin_y)
        pos[n] = np.array([x, VIEW_H - y])

# Edges as short polylines; the arrowhead tip sits on the target node's border
mutual = {(a, b) for a, b in pairs if (b, a) in pairs}
edge_rows, arrow_rows = [], []
for k, (src, dst) in enumerate(pairs):
    p, q = pos[src], pos[dst]
    chord = q - p
    normal = np.array([-chord[1], chord[0]]) / np.linalg.norm(chord)
    bend = BEND * np.linalg.norm(chord) * (1 if (src, dst) in mutual else 0)
    ctrl = (p + q) / 2 + normal * bend
    t = np.linspace(0, 1, 24)[:, None]
    curve = (1 - t) ** 2 * p + 2 * (1 - t) * t * ctrl + t**2 * q
    to_target = np.linalg.norm(curve - q, axis=1)
    to_source = np.linalg.norm(curve - p, axis=1)
    tip_i = np.where(to_target >= NODE_R)[0].max()
    keep = (to_source >= NODE_R) & (np.arange(len(curve)) <= tip_i)
    path = curve[keep]
    heading = curve[tip_i] - curve[max(tip_i - 1, 0)]
    heading = heading / np.linalg.norm(heading)
    centre = curve[tip_i] - heading * ARROW_SIDE / 2
    edge_rows += [{"edge": k, "step": i, "x": x, "y": y} for i, (x, y) in enumerate(path[path[:, 0] >= 0])]
    arrow_rows.append({"x": centre[0], "y": centre[1], "angle": np.degrees(np.arctan2(heading[0], heading[1]))})
edge_df, arrow_df = pd.DataFrame(edge_rows), pd.DataFrame(arrow_rows)

node_df = nodes.assign(x=[pos[n][0] for n in nodes[NODE]], y=[pos[n][1] for n in nodes[NODE]])

x_scale = alt.Scale(domain=[0, VIEW_W], nice=False)
y_scale = alt.Scale(domain=[0, VIEW_H], nice=False)
pos_x = alt.X("x:Q", scale=x_scale, axis=None)
pos_y = alt.Y("y:Q", scale=y_scale, axis=None)
color_scale = alt.Scale(domain=module_types, range=IMPRINT_PALETTE)

edges = (
    alt.Chart(edge_df)
    .mark_line(strokeWidth=1.2, opacity=0.7, color=INK_SOFT)
    .encode(x=pos_x, y=pos_y, detail="edge:N", order="step:Q")
)
arrows = (
    alt.Chart(arrow_df)
    .mark_point(shape="triangle-up", size=ARROW_SIDE**2, filled=True, color=INK_SOFT, opacity=0.9)
    .encode(x=pos_x, y=pos_y, angle=alt.Angle("angle:Q", scale=None))
)
circles = (
    alt.Chart(node_df)
    .mark_circle(size=np.pi * NODE_R**2, stroke=PAGE_BG, strokeWidth=1.5, opacity=1)
    .encode(
        x=pos_x,
        y=pos_y,
        color=alt.Color(
            GROUP.translate(ESCAPE),
            type="nominal",
            scale=color_scale,
            legend=alt.Legend(title=GROUP, titleFontSize=12, labelFontSize=11, symbolSize=180, orient="right"),
        ),
        tooltip=[
            alt.Tooltip(NODE.translate(ESCAPE), type="nominal", title=NODE),
            alt.Tooltip(GROUP.translate(ESCAPE), type="nominal", title=GROUP),
        ],
    )
)
label_style = {"fontSize": 11, "fontWeight": "bold", "dy": -(NODE_R + 8)}
label_text = alt.Text(NODE.translate(ESCAPE), type="nominal")
# A page-coloured copy underneath keeps edges out of the label text
label_halo = (
    alt.Chart(node_df)
    .mark_text(fill=PAGE_BG, stroke=PAGE_BG, strokeWidth=4, **label_style)
    .encode(x=pos_x, y=pos_y, text=label_text)
)
labels = alt.Chart(node_df).mark_text(fill=INK, **label_style).encode(x=pos_x, y=pos_y, text=label_text)

title = "network-directed · python · altair · anyplot.ai"
chart = (
    (edges + arrows + circles + label_halo + labels)
    .properties(
        width=VIEW_W, height=VIEW_H, background=PAGE_BG, title=alt.Title(title, fontSize=16, anchor="middle", color=INK)
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK, padding=8)
)

# Output: PAD (never crop) the saved PNG to the 3200 x 1800 target
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    raise SystemExit(f"vl-convert produced {img.width}x{img.height}, exceeds {TARGET_W}x{TARGET_H}")
canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
