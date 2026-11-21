"""anyplot.ai
parallel-categories-basic: Basic Parallel Categories Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 96/100 | Updated: 2026-05-13
"""

import os
import sys


# Remove script directory from sys.path to avoid importing local altair.py
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir in sys.path:
    sys.path.remove(script_dir)

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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names, left to right
DIMENSIONS = ["Channel", "Category", "Outcome"]  # role: dimension_

# Data: replace this block with your own table, for example df = pd.read_csv("journeys.csv")
np.random.seed(42)
n_customers = 200
df = pd.DataFrame(
    {
        DIMENSIONS[0]: np.random.choice(["Direct", "Search", "Social", "Email"], n_customers, p=[0.3, 0.35, 0.2, 0.15]),
        DIMENSIONS[1]: np.random.choice(
            ["Electronics", "Clothing", "Home", "Sports"], n_customers, p=[0.25, 0.35, 0.25, 0.15]
        ),
        DIMENSIONS[2]: np.random.choice(["Purchase", "Abandon", "Browse"], n_customers, p=[0.4, 0.35, 0.25]),
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
COLOR_DIM = DIMENSIONS[0]  # ribbons take the color of the first dimension on every axis
AXIS_GAP = 1.6  # distance between neighboring axes, in x units
SEG_W = 0.5  # width of a category segment, in x units
total = len(df)
gap = 0.04 * total  # blank space between segments, in observation units

# Layout order: the largest category first on every axis
order = {d: df[d].value_counts().index.tolist() for d in DIMENSIONS}
rank = {d: {c: i for i, c in enumerate(order[d])} for d in DIMENSIONS}
tallest = total + gap * (max(len(v) for v in order.values()) - 1)

# Segment extents: length is the category's count, each axis centered vertically
segments = {}
for d in DIMENSIONS:
    y = (tallest - (total + gap * (len(order[d]) - 1))) / 2
    for cat in order[d]:
        n = int((df[d] == cat).sum())
        segments[(d, cat)] = (y, y + n, n)
        y += n + gap

# Ribbons between neighboring axes, stacked inside segments in the order that limits crossings
ribbon_rows = []
for i in range(len(DIMENSIONS) - 1):
    a, b = DIMENSIONS[i], DIMENSIONS[i + 1]
    cols = list(dict.fromkeys([COLOR_DIM, a, b]))
    flows = df.groupby(cols, sort=False).size().reset_index(name="n")
    left, right = {}, {}
    cursor_l = {c: segments[(a, c)][0] for c in order[a]}
    cursor_r = {c: segments[(b, c)][0] for c in order[b]}
    for _, f in flows.sort_values(
        by=list(dict.fromkeys([a, b, COLOR_DIM])), key=lambda s: s.map(rank[s.name])
    ).iterrows():
        key = (f[COLOR_DIM], f[a], f[b])
        left[key] = cursor_l[f[a]]
        cursor_l[f[a]] += f["n"]
    by_right = flows.sort_values(by=list(dict.fromkeys([b, a, COLOR_DIM])), key=lambda s: s.map(rank[s.name]))
    for _, f in by_right.iterrows():
        right[(f[COLOR_DIM], f[a], f[b])] = cursor_r[f[b]]
        cursor_r[f[b]] += f["n"]
    t = np.linspace(0, 1, 30)
    smooth = 3 * t**2 - 2 * t**3
    x_start = i * AXIS_GAP + SEG_W
    x_end = (i + 1) * AXIS_GAP
    for rid, (_, f) in enumerate(flows.iterrows()):
        key = (f[COLOR_DIM], f[a], f[b])
        top = left[key] + (right[key] - left[key]) * smooth
        for xv, yv in zip(x_start + (x_end - x_start) * t, top, strict=True):
            ribbon_rows.append({"flow": f"{i}-{rid}", COLOR_DIM: f[COLOR_DIM], "x": xv, "y": yv, "y2": yv + f["n"]})
ribbons_df = pd.DataFrame(ribbon_rows)

# Segment boxes and their labels
boxes_df = pd.DataFrame(
    [
        {
            "label": cat,
            "count": str(n),
            "x": k * AXIS_GAP,
            "x2": k * AXIS_GAP + SEG_W,
            "xmid": k * AXIS_GAP + SEG_W / 2,
            "y": y0,
            "y2": y1,
            "ymid": (y0 + y1) / 2,
            "fill": IMPRINT_PALETTE[rank[COLOR_DIM][cat] % len(IMPRINT_PALETTE)] if d == COLOR_DIM else ELEVATED_BG,
            "ink": "#1A1A17" if d == COLOR_DIM else INK,
            "ink_soft": "#1A1A17" if d == COLOR_DIM else INK_SOFT,
        }
        for k, d in enumerate(DIMENSIONS)
        for cat in order[d]
        for y0, y1, n in [segments[(d, cat)]]
    ]
)
headers_df = pd.DataFrame(
    {"x": [k * AXIS_GAP + SEG_W / 2 for k in range(len(DIMENSIONS))], "y": -gap, "header": DIMENSIONS}
)

x_scale = alt.Scale(domain=[-0.05, (len(DIMENSIONS) - 1) * AXIS_GAP + SEG_W + 0.05], nice=False)
y_scale = alt.Scale(domain=[-gap * 1.8, tallest + gap * 0.3], reverse=True, nice=False)

ribbons = (
    alt.Chart(ribbons_df)
    .mark_area(opacity=0.6)
    .encode(
        x=alt.X("x:Q", axis=None, scale=x_scale),
        y=alt.Y("y:Q", axis=None, scale=y_scale),
        y2="y2:Q",
        detail="flow:N",
        color=alt.Color(
            COLOR_DIM.translate(ESCAPE),
            type="nominal",
            title=COLOR_DIM,
            sort=None,
            scale=alt.Scale(domain=order[COLOR_DIM], range=IMPRINT_PALETTE),
            legend=alt.Legend(
                orient="right",
                columns=int(np.ceil(len(order[COLOR_DIM]) / 8)),
                titleLimit=110,
                labelLimit=110,
                titleFontSize=11,
                labelFontSize=10,
                symbolSize=160,
                titleColor=INK,
                labelColor=INK_SOFT,
                fillColor=ELEVATED_BG,
                strokeColor=INK_SOFT,
                padding=6,
            ),
        ),
    )
)

boxes = (
    alt.Chart(boxes_df)
    .mark_rect(stroke=INK_SOFT, strokeWidth=0.8)
    .encode(
        x=alt.X("x:Q", axis=None, scale=x_scale),
        x2="x2:Q",
        y=alt.Y("y:Q", axis=None, scale=y_scale),
        y2="y2:Q",
        color=alt.Color("fill:N", scale=None),
    )
)

labels = (
    alt.Chart(boxes_df)
    .mark_text(fontSize=10, fontWeight="bold", baseline="middle", dy=-5)
    .encode(
        x=alt.X("xmid:Q", scale=x_scale),
        y=alt.Y("ymid:Q", scale=y_scale),
        text="label:N",
        color=alt.Color("ink:N", scale=None),
    )
)

counts = (
    alt.Chart(boxes_df)
    .mark_text(fontSize=9, baseline="middle", dy=7)
    .encode(
        x=alt.X("xmid:Q", scale=x_scale),
        y=alt.Y("ymid:Q", scale=y_scale),
        text="count:N",
        color=alt.Color("ink_soft:N", scale=None),
    )
)

headers = (
    alt.Chart(headers_df)
    .mark_text(fontSize=12, fontWeight="bold", baseline="middle")
    .encode(x=alt.X("x:Q", scale=x_scale), y=alt.Y("y:Q", scale=y_scale), text="header:N", color=alt.value(INK))
)

chart = (
    alt.layer(ribbons, boxes, labels, counts, headers)
    .properties(
        width=540,
        height=320,
        background=PAGE_BG,
        title=alt.Title(
            "parallel-categories-basic · python · altair · anyplot.ai",
            fontSize=16,
            anchor="middle",
            color=INK,
            offset=10,
        ),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
)

# Save, then pad to the canonical canvas
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair produced {w}x{h}, exceeds target {TW}x{TH}; shrink width/height")
if (w, h) != (TW, TH):
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
    canvas.save(f"plot-{THEME}.png")
