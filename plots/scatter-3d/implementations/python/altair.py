"""anyplot.ai
scatter-3d: 3D Scatter Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-08
"""

import os
from itertools import product

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

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
ELEVATION = 25  # viewing angle above the floor, degrees
AZIMUTH = 35  # viewing angle around the vertical axis, degrees
GRID_STEPS = 4  # floor grid divisions per axis

# Columns: set these to your table's column names
X = "Length (cm)"  # role: x
Y = "Width (cm)"  # role: y
Z = "Height (cm)"  # role: z
CLUSTER = "Cluster"  # role: color

# Data: replace this block with your own table, for example df = pd.read_csv("points.csv")
np.random.seed(42)
centers = [(2.5, 2.5, 2.5), (-2.5, -1.5, 1.0), (0.5, 0.0, -2.5)]
clusters = []
for i, (cx, cy, cz) in enumerate(centers):
    n_cluster = 50
    clusters.append(
        pd.DataFrame(
            {
                X: np.random.randn(n_cluster) * 0.8 + cx,
                Y: np.random.randn(n_cluster) * 0.8 + cy,
                Z: np.random.randn(n_cluster) * 0.8 + cz,
                CLUSTER: f"Cluster {i + 1}",
            }
        )
    )
df = pd.concat(clusters, ignore_index=True)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
axes_cols = [X, Y, Z]
lo = df[axes_cols].min()
hi = df[axes_cols].max()
elev, azim = np.radians(ELEVATION), np.radians(AZIMUTH)


def project(x, y, z):
    """Map unit-box coordinates to screen (u, v) and a depth where larger means farther."""
    x, y, z = x - 0.5, y - 0.5, z - 0.5
    u = x * np.cos(azim) - y * np.sin(azim)
    w = x * np.sin(azim) + y * np.cos(azim)
    return u, z * np.cos(elev) + w * np.sin(elev), w * np.cos(elev) - z * np.sin(elev)


unit = (df[axes_cols] - lo) / (hi - lo)
pts = df.copy()
pts["u"], pts["v"], pts["depth"] = project(unit[X], unit[Y], unit[Z])
span = pts["depth"].max() - pts["depth"].min()
pts["near"] = 0.55 + 0.45 * (pts["depth"].max() - pts["depth"]) / span  # near points more opaque

# Bounding box: 12 edges between corners that differ in exactly one axis
corners = list(product([0, 1], repeat=3))
edges = [(a, b) for a in corners for b in corners if a < b and sum(p != q for p, q in zip(a, b, strict=True)) == 1]
box = pd.DataFrame([(*project(*a)[:2], *project(*b)[:2]) for a, b in edges], columns=["u1", "v1", "u2", "v2"])
# Floor grid at the bottom of the box
ticks = np.linspace(0, 1, GRID_STEPS + 1)
floor = pd.DataFrame(
    [(*project(t, 0, 0)[:2], *project(t, 1, 0)[:2]) for t in ticks]
    + [(*project(0, t, 0)[:2], *project(1, t, 0)[:2]) for t in ticks],
    columns=["u1", "v1", "u2", "v2"],
)

# Axis titles and end values sit on the edges nearest the viewer
floor_corners = [(a, b) for a, b in product([0, 1], repeat=2)]
nx, ny = min(floor_corners, key=lambda c: project(c[0], c[1], 0)[2])
lx = min(floor_corners, key=lambda c: project(c[0], c[1], 0)[0])
labels = []
for name, col, a, b, away in [
    (X, X, (0, ny, 0), (1, ny, 0), (0, 1 if ny == 0 else -1)),
    (Y, Y, (nx, 0, 0), (nx, 1, 0), (1 if nx == 1 else -1, 0)),
    (Z, Z, (*lx, 0), (*lx, 1), (-1, 0)),
]:
    (ua, va, _), (ub, vb, _) = project(*a), project(*b)
    sx, sy = away
    labels.append((name, (ua + ub) / 2, (va + vb) / 2, sx * 62, -sy * 42, 12, "title"))
    for pos, t, value in [(a, ua, lo[col]), (b, ub, hi[col])]:
        vv = va if pos is a else vb
        labels.append((f"{value:.1f}", t, vv, sx * 18 if sx else 0, -sy * 14 if sy else 0, 9, "tick"))
labels = pd.DataFrame(labels, columns=["text", "u", "v", "dx", "dy", "size", "kind"])
# Several edges meet at a corner: keep one end value per corner
is_tick = labels["kind"] == "tick"
labels = labels[~(is_tick & labels.duplicated(["u", "v"], keep="last"))]
pad = 0.12
u_all = np.concatenate([box["u1"], box["u2"]])
v_all = np.concatenate([box["v1"], box["v2"]])
u_dom = [u_all.min() - pad, u_all.max() + 0.45]
v_dom = [v_all.min() - pad, v_all.max() + pad]
scale_u = alt.Scale(domain=u_dom, nice=False)
scale_v = alt.Scale(domain=v_dom, nice=False)

rule_kw = {"u1": "u1", "v1": "v1", "u2": "u2", "v2": "v2"}


def rules(data, opacity, width, dash=None):
    return (
        alt.Chart(data)
        .mark_rule(color=INK_SOFT, opacity=opacity, strokeWidth=width, strokeDash=dash or [1, 0])
        .encode(
            x=alt.X("u1:Q", scale=scale_u, axis=None), y=alt.Y("v1:Q", scale=scale_v, axis=None), x2="u2:Q", y2="v2:Q"
        )
    )


scatter = (
    alt.Chart(pts)
    .mark_circle(size=110, strokeWidth=0.8, stroke=PAGE_BG)
    .encode(
        x=alt.X("u:Q", scale=scale_u, axis=None),
        y=alt.Y("v:Q", scale=scale_v, axis=None),
        color=alt.Color(
            CLUSTER.translate(ESCAPE),
            type="nominal",
            title=CLUSTER,
            sort=None,
            scale=alt.Scale(range=IMPRINT_PALETTE),
            legend=alt.Legend(titleFontSize=12, labelFontSize=11, orient="top-right", symbolSize=140, offset=4),
        ),
        opacity=alt.Opacity("near:Q", legend=None, scale=None),
        order=alt.Order("depth:Q", sort="descending"),
        tooltip=[alt.Tooltip(c.translate(ESCAPE), title=c, format=".2f") for c in axes_cols]
        + [alt.Tooltip(CLUSTER.translate(ESCAPE), title=CLUSTER)],
    )
)

text_layers = [
    alt.Chart(labels[labels["kind"] == kind])
    .mark_text(color=color, fontSize=size, fontWeight=weight)
    .encode(
        x=alt.X("u:Q", scale=scale_u, axis=None),
        y=alt.Y("v:Q", scale=scale_v, axis=None),
        text="text:N",
        xOffset=alt.XOffset("dx:Q", scale=None),
        yOffset=alt.YOffset("dy:Q", scale=None),
    )
    for kind, color, size, weight in [("title", INK, 12, "bold"), ("tick", INK_SOFT, 9, "normal")]
]

chart = (
    alt.layer(rules(floor, 0.22, 0.8), rules(box, 0.6, 1.1), *text_layers, scatter)
    .properties(
        width=560,
        height=320,
        background=PAGE_BG,
        title=alt.Title(text="scatter-3d · python · altair · anyplot.ai", fontSize=16, color=INK),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK, padding=6)
    .interactive()
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad up to the canonical canvas
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair vl-convert produced {w}x{h}, exceeds target {TW}x{TH}")
if (w, h) != (TW, TH):
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
    canvas.save(f"plot-{THEME}.png")
