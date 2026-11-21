"""anyplot.ai
alluvial-basic: Basic Alluvial Diagram
Library: altair 6.3.0 | Python 3.14.10
Quality: 78/100 | Updated: 2026-11-20
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

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TIME_POINT = "Election year"  # role: time_point
CATEGORY = "Party"  # role: category
NEXT_CATEGORY = "Party at next election"  # role: extra
NEXT_TIME_POINT = "Next election year"  # role: extra
FLOW = "Voters (thousands)"  # role: flow

# Data: replace this block with your own edge list, for example df = pd.read_csv("flows.csv")
# One row per band: the party at one election, the party at the next, and the voters who made that move.
df = pd.DataFrame(
    [
        ("2012", "2016", "Conservative", "Conservative", 280),
        ("2012", "2016", "Conservative", "Independent", 20),
        ("2012", "2016", "Liberal", "Liberal", 250),
        ("2012", "2016", "Liberal", "Progressive", 30),
        ("2012", "2016", "Liberal", "Independent", 15),
        ("2012", "2016", "Progressive", "Progressive", 120),
        ("2012", "2016", "Progressive", "Liberal", 25),
        ("2012", "2016", "Independent", "Independent", 80),
        ("2012", "2016", "Independent", "Conservative", 30),
        ("2012", "2016", "Independent", "Liberal", 20),
        ("2016", "2020", "Conservative", "Conservative", 260),
        ("2016", "2020", "Conservative", "Independent", 50),
        ("2016", "2020", "Liberal", "Liberal", 250),
        ("2016", "2020", "Liberal", "Progressive", 45),
        ("2016", "2020", "Progressive", "Progressive", 120),
        ("2016", "2020", "Progressive", "Liberal", 30),
        ("2016", "2020", "Independent", "Independent", 80),
        ("2016", "2020", "Independent", "Conservative", 25),
        ("2016", "2020", "Independent", "Progressive", 10),
        ("2020", "2024", "Conservative", "Conservative", 250),
        ("2020", "2024", "Conservative", "Independent", 35),
        ("2020", "2024", "Liberal", "Liberal", 240),
        ("2020", "2024", "Liberal", "Progressive", 40),
        ("2020", "2024", "Progressive", "Progressive", 135),
        ("2020", "2024", "Progressive", "Liberal", 40),
        ("2020", "2024", "Independent", "Independent", 100),
        ("2020", "2024", "Independent", "Conservative", 20),
        ("2020", "2024", "Independent", "Liberal", 10),
    ],
    columns=[TIME_POINT, NEXT_TIME_POINT, CATEGORY, NEXT_CATEGORY, FLOW],
)

# Plot: reads only df and the constants above
TITLE = "alluvial-basic · python · altair · anyplot.ai"

# Canvas: inner view in px; saved at scale_factor 4 and padded to 3200 x 1800
WIDTH, HEIGHT = 620, 340
NODE_WIDTH, NODE_GAP = 76, 7
TOP, BOTTOM, SIDE = 46, 14, 40
CURVE_POINTS = 30

time_points = list(dict.fromkeys([*df[TIME_POINT], *df[NEXT_TIME_POINT]]))
categories = list(dict.fromkeys([*df[CATEGORY], *df[NEXT_CATEGORY]]))
time_idx = {tp: i for i, tp in enumerate(time_points)}
n_cols = len(time_points)
col_x = [SIDE + i * (WIDTH - 2 * SIDE) / (n_cols - 1) for i in range(n_cols)]

# Block size per column: outgoing flow in the first column, incoming flow after that
edges = df.assign(src_t=df[TIME_POINT].map(time_idx))
edges["tgt_t"] = df[NEXT_TIME_POINT].map(time_idx)
outflow = edges.groupby(["src_t", CATEGORY], sort=False)[FLOW].sum()
inflow = edges.groupby(["tgt_t", NEXT_CATEGORY], sort=False)[FLOW].sum()
inflow.index.names = outflow.index.names
totals = pd.concat([outflow, inflow], axis=1).max(axis=1).to_dict()

# Stack the blocks of each column, with a gap between them
usable = (HEIGHT - TOP - BOTTOM) - NODE_GAP * (len(categories) - 1)
blocks = {}
for t in range(n_cols):
    col_total = sum(v for (tt, _), v in totals.items() if tt == t)
    y = TOP
    for cat in categories:
        size = totals.get((t, cat), 0) / col_total * usable if col_total else 0
        if size > 0:
            blocks[(t, cat)] = {"y": y, "h": size, "total": totals[(t, cat)]}
            y += size + NODE_GAP

nodes = pd.DataFrame(
    [
        {
            "party": cat,
            "year": time_points[t],
            "x": col_x[t] - NODE_WIDTH / 2,
            "x2": col_x[t] + NODE_WIDTH / 2,
            "y": b["y"],
            "y2": b["y"] + b["h"],
            "label_x": col_x[t],
            "label_y": b["y"] + b["h"] / 2,
            "total": b["total"],
        }
        for (t, cat), b in blocks.items()
    ]
)

# Bands: smoothstep ribbons from the right edge of one block to the left edge of the next
out_y = {k: b["y"] for k, b in blocks.items()}
in_y = {k: b["y"] for k, b in blocks.items()}
points = []
for i, row in enumerate(edges.itertuples(index=False)):
    src, tgt = (row.src_t, row[2]), (row.tgt_t, row[3])
    flow = row[4]
    h_src = flow / totals[src] * blocks[src]["h"]
    h_tgt = flow / totals[tgt] * blocks[tgt]["h"]
    s0, t0 = out_y[src], in_y[tgt]
    out_y[src] += h_src
    in_y[tgt] += h_tgt
    x0, x1 = col_x[src[0]] + NODE_WIDTH / 2, col_x[tgt[0]] - NODE_WIDTH / 2
    steps = [k / (CURVE_POINTS - 1) for k in range(CURVE_POINTS)]
    top_edge = [(x0 + u * (x1 - x0), s0 + u * u * (3 - 2 * u) * (t0 - s0)) for u in steps]
    bottom_edge = [(x0 + u * (x1 - x0), s0 + h_src + u * u * (3 - 2 * u) * (t0 + h_tgt - s0 - h_src)) for u in steps]
    for order, (x, y) in enumerate(top_edge + bottom_edge[::-1]):
        points.append({"band": i, "party": row[2], "x": x, "y": y, "order": order, "voters": flow})
bands = pd.DataFrame(points)

headers = pd.DataFrame({"x": col_x, "y": TOP - 12, "year": time_points})

x_scale = alt.Scale(domain=[0, WIDTH], nice=False)
y_scale = alt.Scale(domain=[HEIGHT, 0], nice=False)

LEGEND = alt.Legend(titleFontSize=11, labelFontSize=10, orient="right", symbolType="square", symbolSize=140)

band_layer = (
    alt.Chart(bands)
    .mark_line(filled=True, opacity=0.5, strokeWidth=0)
    .encode(
        x=alt.X("x:Q", scale=x_scale, axis=None),
        y=alt.Y("y:Q", scale=y_scale, axis=None),
        color=alt.Color(
            "party:N",
            title=CATEGORY,
            sort=None,
            scale=alt.Scale(domain=categories, range=IMPRINT_PALETTE),
            legend=LEGEND,
        ),
        detail="band:N",
        order="order:Q",
    )
)

node_layer = (
    alt.Chart(nodes)
    .mark_rect(stroke=INK_SOFT, strokeWidth=0.8)
    .encode(
        x=alt.X("x:Q", scale=x_scale),
        x2="x2:Q",
        y=alt.Y("y:Q", scale=y_scale),
        y2="y2:Q",
        color=alt.Color(
            "party:N",
            title=CATEGORY,
            sort=None,
            scale=alt.Scale(domain=categories, range=IMPRINT_PALETTE),
            legend=LEGEND,
        ),
        tooltip=[
            alt.Tooltip("party:N", title=CATEGORY),
            alt.Tooltip("year:N", title=TIME_POINT),
            alt.Tooltip("total:Q", title=FLOW),
        ],
    )
)

label_layer = (
    alt.Chart(nodes)
    .mark_text(fontSize=10, fontWeight="bold", color=INK, baseline="middle", align="center")
    .encode(x=alt.X("label_x:Q", scale=x_scale), y=alt.Y("label_y:Q", scale=y_scale), text="party:N")
)

header_layer = (
    alt.Chart(headers)
    .mark_text(fontSize=13, fontWeight="bold", color=INK, baseline="bottom")
    .encode(x=alt.X("x:Q", scale=x_scale), y=alt.Y("y:Q", scale=y_scale), text="year:N")
)

# Style
chart = (
    alt.layer(band_layer, node_layer, label_layer, header_layer)
    .properties(
        width=WIDTH,
        height=HEIGHT,
        background=PAGE_BG,
        title=alt.Title(TITLE, fontSize=16, anchor="middle", color=INK, offset=8),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_legend(
        padding=8, cornerRadius=4, fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK
    )
    .interactive()
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) the saved PNG to the canonical landscape canvas
TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
img.thumbnail((TARGET_W, TARGET_H))  # only shrinks, when other data makes the legend or view larger
canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
