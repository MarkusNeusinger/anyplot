"""anyplot.ai
network-hierarchical: Hierarchical Network Graph with Tree Layout
Library: altair 6.1.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-17
"""

import os

import altair as alt
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per level in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
NODE_ID = "Node ID"  # role: nodes
LABEL = "Label"  # role: extra
PARENT = "Parent ID"  # role: edges
LEVEL = "Level"  # role: level
TIER = "Role"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("org.csv")
# Organizational chart: 25 employees across 4 management levels (root has no parent)
rows = [
    (0, "CEO", None, 0, "Executive"),
    (1, "VP Eng", 0, 1, "VP"),
    (2, "VP Sales", 0, 1, "VP"),
    (3, "VP Mkt", 0, 1, "VP"),
    (4, "VP Ops", 0, 1, "VP"),
    (5, "Frontend", 1, 2, "Director"),
    (6, "Backend", 1, 2, "Director"),
    (7, "East", 2, 2, "Director"),
    (8, "West", 2, 2, "Director"),
    (9, "Digital", 3, 2, "Director"),
    (10, "Brand", 3, 2, "Director"),
    (11, "Logistics", 4, 2, "Director"),
    (12, "Facilities", 4, 2, "Director"),
    (13, "UI", 5, 3, "Manager"),
    (14, "UX", 5, 3, "Manager"),
    (15, "API", 6, 3, "Manager"),
    (16, "NE", 7, 3, "Manager"),
    (17, "SE", 7, 3, "Manager"),
    (18, "NW", 8, 3, "Manager"),
    (19, "Social", 9, 3, "Manager"),
    (20, "Content", 9, 3, "Manager"),
    (21, "PR", 10, 3, "Manager"),
    (22, "Design", 10, 3, "Manager"),
    (23, "Supply", 11, 3, "Manager"),
    (24, "Office", 12, 3, "Manager"),
]
df = pd.DataFrame(rows, columns=[NODE_ID, LABEL, PARENT, LEVEL, TIER])
df[PARENT] = df[PARENT].astype("Int64")

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})

# Tree layout: leaves get one slot each, a parent sits above the middle of its subtree
children = {node: df.loc[df[PARENT] == node, NODE_ID].tolist() for node in df[NODE_ID]}
by_level = df.sort_values(LEVEL, kind="stable")
slots = {}
for node in by_level[NODE_ID][::-1]:
    slots[node] = max(1, sum(slots[c] for c in children[node]))

start = {}
cursor = 0
for node in df.loc[df[PARENT].isna(), NODE_ID]:
    start[node] = cursor
    cursor += slots[node]
for node in by_level[NODE_ID]:
    cursor = start[node]
    for child in children[node]:
        start[child] = cursor
        cursor += slots[child]

nodes = df.copy()
nodes["pos_x"] = nodes[NODE_ID].map(lambda n: start[n] + slots[n] / 2)
nodes["pos_y"] = -nodes[LEVEL]
position = nodes.set_index(NODE_ID)[["pos_x", "pos_y"]]

# Edges: two points per parent-child pair, grouped by the child id
links = df.dropna(subset=[PARENT])
edges = pd.concat(
    [
        position.loc[links[PARENT].astype(int)].reset_index(drop=True).assign(edge=links[NODE_ID].to_numpy()),
        position.loc[links[NODE_ID]].reset_index(drop=True).assign(edge=links[NODE_ID].to_numpy()),
    ]
)

x_enc = alt.X("pos_x:Q", axis=None, scale=alt.Scale(domain=[-0.5, cursor + 0.5], nice=False))
y_enc = alt.Y("pos_y:Q", axis=None, scale=alt.Scale(domain=[-df[LEVEL].max() - 0.45, 0.55], nice=False))

edge_layer = (
    alt.Chart(edges).mark_line(strokeWidth=1.2, opacity=0.5, color=INK_SOFT).encode(x=x_enc, y=y_enc, detail="edge:N")
)

node_layer = (
    alt.Chart(nodes)
    .mark_circle(size=330, stroke=INK, strokeWidth=1.2, opacity=1)
    .encode(
        x=x_enc,
        y=y_enc,
        color=alt.Color(
            TIER.translate(ESCAPE),
            type="nominal",
            title=TIER,
            sort=None,
            scale=alt.Scale(range=IMPRINT_PALETTE),
            legend=alt.Legend(symbolSize=200, labelFontSize=11, titleFontSize=12),
        ),
        tooltip=[alt.Tooltip(LABEL.translate(ESCAPE), title=LABEL), alt.Tooltip(TIER.translate(ESCAPE), title=TIER)],
    )
)

label_layer = (
    alt.Chart(nodes)
    .mark_text(dy=-17, fontSize=9.5, fontWeight="bold", color=INK)
    .encode(x=x_enc, y=y_enc, text=alt.Text(LABEL.translate(ESCAPE), type="nominal"))
)

chart = (
    alt.layer(edge_layer, node_layer, label_layer)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title(
            "network-hierarchical · python · altair · anyplot.ai",
            fontSize=16,
            color=INK,
            anchor="middle",
            subtitle=f"Organizational chart: {len(df)} employees across {df[LEVEL].nunique()} management levels",
            subtitleFontSize=11,
            subtitleColor=INK_SOFT,
        ),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK, padding=8)
)

# Save as PNG and HTML
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the canonical landscape canvas
TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    raise SystemExit(f"altair produced {img.width}x{img.height}, exceeds {TARGET_W}x{TARGET_H}; shrink width/height")
if img.size != (TARGET_W, TARGET_H):
    canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
    canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
    canvas.save(f"plot-{THEME}.png")
