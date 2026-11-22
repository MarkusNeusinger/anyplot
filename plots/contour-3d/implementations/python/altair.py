""" anyplot.ai
contour-3d: 3D Contour Plot
Library: altair 6.3.0 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-22
"""

import os
import sys

import numpy as np
import pandas as pd
from PIL import Image


# Avoid name collision with the script filename
_sys_path = sys.path[:]
sys.path = [p for p in sys.path if not p.startswith(os.path.dirname(__file__))]
import altair as alt  # noqa: E402


sys.path = _sys_path

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: single-polarity sequential ramp for height
IMPRINT_SEQ = ["#009E73", "#4467A3"]

# Constants
AZIMUTH = np.radians(28)  # view rotation around the vertical axis
ELEVATION = np.radians(32)  # camera height above the base plane
BOX_HEIGHT = 0.9  # height of the drawing box relative to its footprint
N_LEVELS = 8  # number of level curves
VIEW_W, VIEW_H = 520, 300  # inner view in px; vl-convert adds title and legend around it

# Columns: set these to your table's column names
X_COORD = "X coordinate"  # role: x
Y_COORD = "Y coordinate"  # role: y
HEIGHT = "Elevation (m)"  # role: z

# Data: replace this block with your own table, for example df = pd.read_csv("surface.csv")
grid = np.linspace(-6, 6, 50)
gx, gy = np.meshgrid(grid, grid)
gz = (
    100 * np.exp(-(gx**2 + gy**2) / 10)
    + 60 * np.exp(-((gx - 3.5) ** 2 + (gy - 3.5) ** 2) / 8)
    + 40 * np.exp(-((gx + 3) ** 2 + (gy + 2.5) ** 2) / 12)
)
df = pd.DataFrame({X_COORD: gx.ravel(), Y_COORD: gy.ravel(), HEIGHT: gz.ravel()})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
surface = df.pivot_table(index=Y_COORD, columns=X_COORD, values=HEIGHT)
xs, ys, zs = surface.columns.to_numpy(), surface.index.to_numpy(), surface.to_numpy()
x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
z0, z1 = np.nanmin(zs), np.nanmax(zs)
step = float(np.round((z1 - z0) / (N_LEVELS + 1), -1)) or (z1 - z0) / (N_LEVELS + 1)
levels = np.arange(np.ceil(z0 / step) * step + step, z1, step)


def project(x, y, z):
    """Oblique projection of data coordinates onto the screen plane."""
    xn = 2 * (np.asarray(x) - x0) / (x1 - x0) - 1
    yn = 2 * (np.asarray(y) - y0) / (y1 - y0) - 1
    zn = (np.asarray(z) - z0) / (z1 - z0) * BOX_HEIGHT
    depth = xn * np.sin(AZIMUTH) + yn * np.cos(AZIMUTH)
    return xn * np.cos(AZIMUTH) - yn * np.sin(AZIMUTH), depth * np.sin(ELEVATION) + zn * np.cos(ELEVATION) * 2


# Surface wireframe: every fifth grid line, drawn flat in a soft tone
rows = []
for k in range(0, len(ys), 5):
    u, v = project(xs, np.full_like(xs, ys[k]), zs[k, :])
    rows += [
        {"u": a, "v": b, "path": f"wx{k}", "seq": i, "kind": "surface"}
        for i, (a, b) in enumerate(zip(u, v, strict=True))
    ]
for k in range(0, len(xs), 5):
    u, v = project(np.full_like(ys, xs[k]), ys, zs[:, k])
    rows += [
        {"u": a, "v": b, "path": f"wy{k}", "seq": i, "kind": "surface"}
        for i, (a, b) in enumerate(zip(u, v, strict=True))
    ]

# Level curves, lifted to their height and repeated on the base plane
# Marching squares: edges 0..3 are bottom, right, top, left of a cell; each case joins two crossings
CASES = {1: [(3, 0)], 2: [(0, 1)], 3: [(3, 1)], 4: [(1, 2)], 5: [(0, 1), (2, 3)], 6: [(0, 2)], 7: [(3, 2)]}
CASES |= {8: [(2, 3)], 9: [(0, 2)], 10: [(3, 0), (1, 2)], 11: [(1, 2)], 12: [(1, 3)], 13: [(0, 1)], 14: [(3, 0)]}
EDGES = [((0, 0), (0, 1)), ((0, 1), (1, 1)), ((1, 1), (1, 0)), ((1, 0), (0, 0))]  # (row, col) offsets of corners
for level in levels:
    above = zs >= level
    code = above[:-1, :-1] * 1 + above[:-1, 1:] * 2 + above[1:, 1:] * 4 + above[1:, :-1] * 8
    for r, c in zip(*np.nonzero((code > 0) & (code < 15)), strict=True):
        for s, (e0, e1) in enumerate(CASES[code[r, c]]):
            pts = []
            for e in (e0, e1):
                (ra, ca), (rb, cb) = EDGES[e]
                za, zb = zs[r + ra, c + ca], zs[r + rb, c + cb]
                t = (level - za) / (zb - za)
                pts.append((xs[c + ca] + t * (xs[c + cb] - xs[c + ca]), ys[r + ra] + t * (ys[r + rb] - ys[r + ra])))
            for kind, z_line in (("lifted", level), ("base", z0)):
                u, v = project([p[0] for p in pts], [p[1] for p in pts], np.full(2, z_line))
                for i in range(2):
                    rows.append(
                        {
                            "u": u[i],
                            "v": v[i],
                            "path": f"{kind}{level}-{r}-{c}-{s}",
                            "seq": i,
                            "kind": kind,
                            HEIGHT: level,
                        }
                    )
paths = pd.DataFrame(rows)

# Axes drawn as a box: base-plane frame, the x and y edges at the front, a z axis on the left
corners = np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]])
cu, cv = project(corners[:, 0], corners[:, 1], np.full(4, z0))
frame = pd.DataFrame(
    [
        {"u": cu[(i + s) % 4], "v": cv[(i + s) % 4], "path": f"f{i}", "seq": s, "kind": "frame"}
        for i in range(4)
        for s in (0, 1)
    ]
)
front = int(np.argmin(cv))
left = int(np.argmin(cu))
nice = lambda lo, hi: np.round(np.linspace(lo, hi, 5)[1:-1], 0)  # noqa: E731

labels = []
# x axis runs along the front edge that starts at the front corner and varies x
x_edge_y = corners[front, 1]
y_edge_x = corners[front, 0]
for t in nice(x0, x1):
    u, v = project(t, x_edge_y + (-0.7 if x_edge_y == y0 else 0.7), z0)
    labels.append({"u": float(u), "v": float(v), "text": f"{t:g}", "kind": "tick"})
for t in nice(y0, y1):
    u, v = project(y_edge_x + (-0.7 if y_edge_x == x0 else 0.7), t, z0)
    labels.append({"u": float(u), "v": float(v), "text": f"{t:g}", "kind": "tick"})
mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2
u, v = project(mid_x, x_edge_y + (-4.8 if x_edge_y == y0 else 4.8), z0)
labels.append({"u": float(u), "v": float(v), "text": X_COORD, "kind": "title"})
u, v = project(y_edge_x + (-4.8 if y_edge_x == x0 else 4.8), mid_y, z0)
labels.append({"u": float(u), "v": float(v), "text": Y_COORD, "kind": "title"})

# z axis: a vertical rule at the leftmost corner with ticks at the contour levels
zx, zy = corners[left]
zu, zv = project(np.full(2, zx), np.full(2, zy), np.array([z0, z1]))
z_axis = pd.DataFrame({"u": zu, "v": zv, "path": "z", "seq": [0, 1], "kind": "frame"})
for t in np.arange(np.ceil(z0 / step) * step, z1, step * 2):
    u, v = project(zx, zy, t)
    labels.append({"u": float(u) - 0.16, "v": float(v), "text": f"{t:g}", "kind": "ztick"})
u, v = project(zx, zy, z1)
labels.append({"u": float(u) - 0.16, "v": float(v) + 0.25, "text": HEIGHT, "kind": "title"})
labels = pd.DataFrame(labels)

# Screen domains share one scale so the oblique box keeps its proportions
allu = np.concatenate([paths["u"], frame["u"], labels["u"]])
allv = np.concatenate([paths["v"], frame["v"], labels["v"]])
cx, cy = (allu.min() + allu.max()) / 2, (allv.min() + allv.max()) / 2
half_w = max((allu.max() - allu.min()) / 2, (allv.max() - allv.min()) / 2 * VIEW_W / VIEW_H) * 1.04
half_h = half_w * VIEW_H / VIEW_W
u_scale = alt.Scale(domain=[cx - half_w, cx + half_w], nice=False)
v_scale = alt.Scale(domain=[cy - half_h, cy + half_h], nice=False)

HEIGHT_FIELD = HEIGHT.translate(ESCAPE)
line_enc = {
    "x": alt.X("u:Q", scale=u_scale, axis=None),
    "y": alt.Y("v:Q", scale=v_scale, axis=None),
    "detail": alt.Detail("path:N"),
    "order": alt.Order("seq:Q"),
}
height_scale = alt.Scale(range=IMPRINT_SEQ, domain=[float(levels.min()), float(levels.max())])

height_legend = alt.Legend(
    gradientLength=240,
    gradientThickness=22,
    values=[float(v) for v in levels[::2]],
    format=".0f",
    labelColor=INK_SOFT,
    labelFontSize=16,
    titleColor=INK,
    titleFontSize=18,
    titlePadding=10,
)

wire = (
    alt.Chart(paths[paths["kind"] == "surface"])
    .mark_line(color=INK_SOFT, strokeWidth=1.1, opacity=0.35)
    .encode(**line_enc)
)
base = (
    alt.Chart(paths[paths["kind"] == "base"])
    .mark_line(strokeWidth=2.2, strokeCap="round")
    .encode(
        **line_enc,
        color=alt.Color(HEIGHT_FIELD, type="quantitative", title=HEIGHT, scale=height_scale, legend=height_legend),
    )
)
lifted = (
    alt.Chart(paths[paths["kind"] == "lifted"])
    .mark_line(strokeWidth=5.5, strokeCap="round")
    .encode(
        **line_enc,
        color=alt.Color(HEIGHT_FIELD, type="quantitative", title=HEIGHT, scale=height_scale, legend=height_legend),
    )
)
frame_layer = (
    alt.Chart(pd.concat([frame, z_axis]))
    .mark_line(color=INK_SOFT, strokeWidth=2.2)
    .encode(x=line_enc["x"], y=line_enc["y"], detail=line_enc["detail"], order=line_enc["order"])
)
text_enc = {"x": alt.X("u:Q", scale=u_scale, axis=None), "y": alt.Y("v:Q", scale=v_scale, axis=None), "text": "text:N"}
ticks = (
    alt.Chart(labels[labels["kind"].isin(["tick", "ztick"])]).mark_text(color=INK_SOFT, fontSize=17).encode(**text_enc)
)
titles = (
    alt.Chart(labels[labels["kind"] == "title"]).mark_text(color=INK, fontSize=21, fontWeight="bold").encode(**text_enc)
)

chart = (
    alt.layer(wire, base, frame_layer, lifted, ticks, titles)
    .properties(
        width=VIEW_W,
        height=VIEW_H,
        background=PAGE_BG,
        title=alt.Title(
            "contour-3d · python · altair · anyplot.ai", fontSize=24, color=INK, anchor="middle", offset=12
        ),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, padding=12, cornerRadius=4)
)

# Save: PNG padded (never cropped) to the canvas, plus the interactive HTML
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TW or img.height > TH:
    raise SystemExit(f"altair produced {img.width}x{img.height}, exceeds {TW}x{TH}; shrink width/height")
canvas = Image.new("RGB", (TW, TH), PAGE_BG)
canvas.paste(img, ((TW - img.width) // 2, (TH - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
