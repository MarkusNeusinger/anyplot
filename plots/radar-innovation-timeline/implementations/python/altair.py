""" anyplot.ai
radar-innovation-timeline: Innovation Radar with Time-Horizon Rings
Library: altair 6.3.0 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-27
"""

import os
import sys


# Prevent this file from shadowing the altair package when run from its own directory
_self_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _self_dir]

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per sector in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
RING_ORDER = ["Adopt", "Trial", "Assess", "Hold"]  # nearest time horizon first
RING_SHAPES = ["circle", "diamond", "triangle-up", "square"]  # redundant ring encoding
ARC_SPAN = 1.5 * np.pi  # 270-degree layout, the open quarter at the bottom holds the ring labels

# Columns: set these to your table's column names
NAME = "Technology"  # role: name
RING = "Ring"  # role: ring
SECTOR = "Sector"  # role: sector

# Data: replace this block with your own table, for example df = pd.read_csv("radar.csv")
df = pd.DataFrame(
    [
        ("LLM Agents", "Adopt", "AI & ML"),
        ("RAG Pipelines", "Adopt", "AI & ML"),
        ("Vision Models", "Trial", "AI & ML"),
        ("AI Code Review", "Trial", "AI & ML"),
        ("Neuro-symb. AI", "Assess", "AI & ML"),
        ("Auto. ML Ops", "Assess", "AI & ML"),
        ("AGI Frameworks", "Hold", "AI & ML"),
        ("Edge Computing", "Adopt", "Cloud & Infra"),
        ("Platform Eng.", "Adopt", "Cloud & Infra"),
        ("WASM Backends", "Trial", "Cloud & Infra"),
        ("FinOps Tools", "Trial", "Cloud & Infra"),
        ("Serverless GPUs", "Assess", "Cloud & Infra"),
        ("Quantum Cloud", "Hold", "Cloud & Infra"),
        ("Data Contracts", "Adopt", "Data Engineering"),
        ("Lakehouse Arch.", "Trial", "Data Engineering"),
        ("Streaming SQL", "Trial", "Data Engineering"),
        ("Data Mesh", "Assess", "Data Engineering"),
        ("Graph Analytics", "Assess", "Data Engineering"),
        ("Quantum DB", "Hold", "Data Engineering"),
        ("Zero Trust", "Adopt", "Security"),
        ("SBOM Tooling", "Adopt", "Security"),
        ("AI Threat Det.", "Trial", "Security"),
        ("Passkeys", "Trial", "Security"),
        ("Confid. Compute", "Assess", "Security"),
        ("Post-Q. Crypto", "Assess", "Security"),
        ("Homomorphic Enc.", "Hold", "Security"),
    ],
    columns=[NAME, RING, SECTOR],
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
rings = list(dict.fromkeys(RING_ORDER + df[RING].dropna().tolist()))
sectors = list(dict.fromkeys(df[SECTOR].dropna().tolist()))
n_rings, n_sectors = len(rings), len(sectors)
sector_colors = {s: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, s in enumerate(sectors)}
ring_shapes = {r: RING_SHAPES[i % len(RING_SHAPES)] for i, r in enumerate(rings)}

# Geometry: one band per ring, outward from the hub
start_angle = -np.pi / 4
sector_arc = ARC_SPAN / n_sectors
ring_inner = np.array([0.5 + 0.95 * i for i in range(n_rings)])
ring_outer = ring_inner + 0.8
ring_boundaries = ring_outer + 0.075
r_max = ring_boundaries[-1]
x_lim = r_max + 2.0
x_dom = [-x_lim, x_lim]
y_dom = [-1.25 * r_max, r_max + 1.1]  # the quarter below the hub only holds the ring names

# Positions: items are spread inside the cell of their own sector and ring
pts = df.dropna(subset=[NAME, RING, SECTOR]).reset_index(drop=True)
cell = pts.groupby([SECTOR, RING], sort=False)
n_cell = cell[NAME].transform("size").to_numpy()
idx = cell.cumcount().to_numpy()
si = pts[SECTOR].map({s: i for i, s in enumerate(sectors)}).to_numpy()
ri = pts[RING].map({r: i for i, r in enumerate(rings)}).to_numpy()
padding = 0.12 * sector_arc
ring_jitter = 0.08 * sector_arc * (-1.0) ** ri  # neighbouring rings sit at different angles
angle = (
    start_angle
    + si * sector_arc
    + padding
    + (idx + 0.5) / n_cell * (sector_arc - 2 * padding)
    + np.where(n_cell > 1, ring_jitter, 0.4 * ring_jitter)
)
radius = (ring_inner[ri] + ring_outer[ri]) / 2 + np.where(n_cell > 1, 0.27 * (-1.0) ** idx, 0.0)
label_side = np.where(np.cos(angle) >= 0, 1.0, -1.0)
pts["x"] = radius * np.cos(angle)
pts["y"] = radius * np.sin(angle)

# Sector headers sit outside the outer ring at the middle of their sector
sec_mid = start_angle + (np.arange(n_sectors) + 0.5) * sector_arc
head_x = (r_max + 1.0) * np.cos(sec_mid)
head_y = (r_max + 1.0) * np.sin(sec_mid)

# Labels only: push overlapping text apart vertically (headers stay put), the markers stay at their cells
n_pts = len(pts)
text_x = np.concatenate([pts["x"].to_numpy() + label_side * 0.32, head_x])
text_y = np.concatenate([pts["y"].to_numpy(), head_y])
text_w = np.concatenate([0.125 * pts[NAME].str.len().to_numpy(), 0.16 * np.array([len(s) for s in sectors])])
text_lo = np.concatenate(
    [np.where(label_side > 0, text_x[:n_pts], text_x[:n_pts] - text_w[:n_pts]), head_x - text_w[n_pts:] / 2]
)
text_hi = text_lo + text_w
movable = np.arange(len(text_x)) < n_pts
min_gap = 0.32
for _ in range(60):
    for i in range(len(text_x)):
        for j in range(i + 1, len(text_x)):
            gap = abs(text_y[i] - text_y[j])
            if text_lo[i] < text_hi[j] and text_lo[j] < text_hi[i] and gap < min_gap and (movable[i] or movable[j]):
                push = min_gap - gap + 0.01
                up, down = (i, j) if text_y[i] >= text_y[j] else (j, i)
                if movable[up] and movable[down]:
                    text_y[up] += push / 2
                    text_y[down] -= push / 2
                elif movable[up]:
                    text_y[up] += push
                else:
                    text_y[down] -= push
pts["label_x"] = text_x[:n_pts]
pts["label_y"] = text_y[:n_pts]
pts["side"] = np.where(label_side > 0, "right", "left")

# Ring fills, boundary arcs and sector spokes
n_arc = 100
arc_t = np.linspace(start_angle, start_angle + ARC_SPAN, n_arc)
fill_rows = []
for i, rn in enumerate(rings):
    outline = np.concatenate([ring_inner[i] * np.exp(1j * arc_t), ring_outer[i] * np.exp(1j * arc_t[::-1])])
    for order, z in enumerate(np.append(outline, outline[0])):
        fill_rows.append({"x": z.real, "y": z.imag, "ring": rn, "order": order})
df_fills = pd.DataFrame(fill_rows)

arc_rows = [
    {"x": rb * np.cos(t), "y": rb * np.sin(t), "rb": rb, "order": order}
    for rb in ring_boundaries
    for order, t in enumerate(arc_t)
]
df_arcs = pd.DataFrame(arc_rows)

spoke_rows = []
for i in range(n_sectors + 1):
    a = start_angle + i * sector_arc
    spoke_rows.append({"x": 0.0, "y": 0.0, "sid": i, "order": 0})
    spoke_rows.append({"x": (r_max + 0.1) * np.cos(a), "y": (r_max + 0.1) * np.sin(a), "sid": i, "order": 1})
df_spokes = pd.DataFrame(spoke_rows)

# Sector headers along the outer edge, ring names in the open quarter
df_sec = pd.DataFrame({"x": head_x, "y": head_y, "sector": sectors})
ring_mid = (ring_inner + ring_outer) / 2
df_rlabels = pd.DataFrame({"x": 0.22, "y": -ring_mid, "ring": rings})

# Chart layers
x_enc = alt.X("x:Q", scale=alt.Scale(domain=x_dom), axis=None)
y_enc = alt.Y("y:Q", scale=alt.Scale(domain=y_dom), axis=None)
color_scale = alt.Scale(domain=sectors, range=[sector_colors[s] for s in sectors])
shape_scale = alt.Scale(domain=rings, range=[ring_shapes[r] for r in rings])
hover = alt.selection_point(on="pointerover", fields=[NAME], nearest=True, empty=False)

fill_layers = [
    alt.Chart(df_fills[df_fills["ring"] == rn])
    .mark_line(
        strokeWidth=0, filled=True, fill=IMPRINT_PALETTE[(0, 2, 1, 3, 4, 5, 6, 7)[i % 8]], fillOpacity=0.12 * 0.6**i
    )
    .encode(x=x_enc, y=y_enc, order="order:Q")
    for i, rn in enumerate(rings)
]

arcs = (
    alt.Chart(df_arcs)
    .mark_line(strokeWidth=1.2, stroke=INK_SOFT, opacity=0.35)
    .encode(x=x_enc, y=y_enc, detail="rb:N", order="order:Q")
)

spokes = (
    alt.Chart(df_spokes)
    .mark_line(strokeWidth=1.2, stroke=INK_MUTED, opacity=0.35)
    .encode(x=x_enc, y=y_enc, detail="sid:N", order="order:Q")
)

leaders = (
    alt.Chart(pts)
    .mark_rule(strokeWidth=0.7, opacity=0.35)
    .encode(x=x_enc, y=y_enc, x2="label_x:Q", y2="label_y:Q", color=alt.value(INK_MUTED))
)

points = (
    alt.Chart(pts)
    .mark_point(filled=True, strokeWidth=1.2, stroke=PAGE_BG, opacity=0.95)
    .encode(
        x=x_enc,
        y=y_enc,
        color=alt.Color(SECTOR.translate(ESCAPE), type="nominal", title=SECTOR, scale=color_scale),
        shape=alt.Shape(RING.translate(ESCAPE), type="nominal", title=RING, scale=shape_scale),
        size=alt.condition(hover, alt.value(380), alt.value(230)),
        tooltip=[
            alt.Tooltip(NAME.translate(ESCAPE), title=NAME),
            alt.Tooltip(SECTOR.translate(ESCAPE), title=SECTOR),
            alt.Tooltip(RING.translate(ESCAPE), title=RING),
        ],
    )
    .add_params(hover)
)

label_layers = [
    alt.Chart(pts[pts["side"] == side])
    .mark_text(fontSize=11, align="left" if side == "right" else "right", baseline="middle")
    .encode(
        x=alt.X("label_x:Q", scale=alt.Scale(domain=x_dom), axis=None),
        y=alt.Y("label_y:Q", scale=alt.Scale(domain=y_dom), axis=None),
        text=alt.Text(NAME.translate(ESCAPE), type="nominal"),
        color=alt.value(INK_SOFT),
        opacity=alt.condition(hover, alt.value(1.0), alt.value(0.9)),
    )
    for side in ("left", "right")
]

sec_header_layers = [
    alt.Chart(df_sec[df_sec["sector"] == s])
    .mark_text(fontSize=13, fontWeight="bold", color=sector_colors[s])
    .encode(x=x_enc, y=y_enc, text="sector:N")
    for s in sectors
]

rlabels = (
    alt.Chart(df_rlabels)
    .mark_text(fontSize=11, fontWeight="bold", align="left", baseline="middle")
    .encode(x=x_enc, y=y_enc, text="ring:N", color=alt.value(INK_MUTED))
)

chart = (
    alt.layer(*fill_layers, arcs, spokes, leaders, points, *label_layers, *sec_header_layers, rlabels)
    .properties(
        width=600,
        height=600,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding=10,
        background=PAGE_BG,
        title=alt.Title(
            "radar-innovation-timeline · python · altair · anyplot.ai",
            fontSize=16,
            anchor="middle",
            offset=8,
            color=INK,
        ),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_legend(
        padding=6,
        cornerRadius=4,
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=11,
        titleFontSize=12,
        orient="bottom",
        direction="horizontal",
        symbolSize=180,
        symbolStrokeWidth=0,
    )
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Fit to the exact 2400x2400 canvas: scale an overshoot down, centre a shortfall on the page color
TW, TH = 2400, 2400
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (TW, TH):
    _scale = min(1.0, TW / _img.width, TH / _img.height)
    _img = _img.resize((round(_img.width * _scale), round(_img.height * _scale)), Image.LANCZOS)
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _img.width) // 2, (TH - _img.height) // 2))
    _canvas.save(f"plot-{THEME}.png")
