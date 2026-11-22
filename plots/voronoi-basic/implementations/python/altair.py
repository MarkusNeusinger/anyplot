"""anyplot.ai
voronoi-basic: Voronoi Diagram for Spatial Partitioning
Library: altair 6.1.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-17
"""

import os
import sys


# Remove current directory from path to avoid shadowing altair library
_current_dir = os.path.dirname(os.path.abspath(__file__))
_sys_path_backup = sys.path.copy()
sys.path = [p for p in sys.path if os.path.abspath(p) != _current_dir]

try:
    import altair as alt
finally:
    sys.path = _sys_path_backup

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402
from scipy.spatial import Voronoi  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BOX_PAD = 0.08  # margin around the seeds, as a share of their span, that makes the clipping box

# Columns: set these to your table's column names
X = "X coordinate"  # role: x
Y = "Y coordinate"  # role: y
STATION = "Weather station"  # role: label

# Data: replace this block with your own table, for example df = pd.read_csv("seeds.csv")
np.random.seed(42)
n_points = 15
df = pd.DataFrame(
    {
        X: np.random.uniform(5, 95, n_points),
        Y: np.random.uniform(5, 95, n_points),
        STATION: [f"Station {i + 1}" for i in range(n_points)],
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
df = df.dropna(subset=[X, Y]).reset_index(drop=True)
points = df[[X, Y]].to_numpy()
low, high = points.min(axis=0), points.max(axis=0)
box_min, box_max = low - BOX_PAD * (high - low), high + BOX_PAD * (high - low)
n = len(points)

# Mirror every seed across the four box edges: the cells of the real seeds are then
# bounded exactly by the box, corners included, and need no clipping afterwards.
mirrors = np.vstack(
    [
        np.column_stack([2 * box_min[0] - points[:, 0], points[:, 1]]),
        np.column_stack([2 * box_max[0] - points[:, 0], points[:, 1]]),
        np.column_stack([points[:, 0], 2 * box_min[1] - points[:, 1]]),
        np.column_stack([points[:, 0], 2 * box_max[1] - points[:, 1]]),
    ]
)
vor = Voronoi(np.vstack([points, mirrors]))

# Neighbouring cells get different Imprint colors (greedy coloring over shared edges)
neighbours = [set() for _ in range(n)]
for a, b in vor.ridge_points:
    if a < n and b < n:
        neighbours[a].add(b)
        neighbours[b].add(a)
cell_color = []
for i in range(n):
    used = {cell_color[j] for j in neighbours[i] if j < i}
    cell_color.append(next(c for c in range(len(IMPRINT_PALETTE)) if c not in used))

rows = []
for i in range(n):
    verts = vor.vertices[vor.regions[vor.point_region[i]]]
    center = verts.mean(axis=0)
    ring = verts[np.argsort(np.arctan2(verts[:, 1] - center[1], verts[:, 0] - center[0]))]
    for k, (vx, vy) in enumerate(ring):
        rows.append({"vx": vx, "vy": vy, "order": k, "cell": df[STATION][i], "fill": IMPRINT_PALETTE[cell_color[i]]})
cells = pd.DataFrame(rows)

x_scale = alt.Scale(domain=[box_min[0], box_max[0]], nice=False)
y_scale = alt.Scale(domain=[box_min[1], box_max[1]], nice=False)
cell_layer = (
    alt.Chart(cells)
    .mark_line(filled=True, interpolate="linear-closed", opacity=0.55, stroke=INK_SOFT, strokeWidth=2)
    .encode(
        x=alt.X("vx:Q", scale=x_scale, title=X),
        y=alt.Y("vy:Q", scale=y_scale, title=Y),
        color=alt.Color("fill:N", scale=None, legend=None),
        detail="cell:N",
        order="order:O",
    )
)
seed_layer = (
    alt.Chart(df)
    .mark_circle(size=130, color=INK, opacity=1, stroke=PAGE_BG, strokeWidth=2.5)
    .encode(
        x=alt.X(X.translate(ESCAPE), type="quantitative", title=X),
        y=alt.Y(Y.translate(ESCAPE), type="quantitative", title=Y),
        tooltip=[
            alt.Tooltip(STATION.translate(ESCAPE), type="nominal", title=STATION),
            alt.Tooltip(X.translate(ESCAPE), type="quantitative", title=X, format=".1f"),
            alt.Tooltip(Y.translate(ESCAPE), type="quantitative", title=Y, format=".1f"),
        ],
    )
)
# Each label is centered above its seed, or below it when the nearest other seed is higher,
# so labels of close seeds go to opposite sides instead of colliding
dist = np.linalg.norm(points[:, None] - points[None, :], axis=2)
np.fill_diagonal(dist, np.inf)
neighbour_above = points[dist.argmin(axis=1), 1] > points[:, 1]
label_df = df.assign(side=np.where(neighbour_above, "below", "above"))


def label_layer(side, dy):
    return (
        alt.Chart(label_df[label_df["side"] == side])
        .mark_text(dy=dy, fontSize=11, fontWeight="bold", color=INK)
        .encode(
            x=alt.X(X.translate(ESCAPE), type="quantitative"),
            y=alt.Y(Y.translate(ESCAPE), type="quantitative"),
            text=alt.Text(STATION.translate(ESCAPE), type="nominal"),
        )
    )


chart = (
    (cell_layer + seed_layer + label_layer("above", -14) + label_layer("below", 16))
    .properties(
        width=440,
        height=440,
        background=PAGE_BG,
        title=alt.Title("voronoi-basic · python · altair · anyplot.ai", fontSize=20, anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        grid=False,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=12,
        titleFontSize=14,
    )
    .configure_title(color=INK)
)

# Save output, padded (never cropped) to the canonical square canvas
TARGET = (2400, 2400)
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET[0] or img.height > TARGET[1]:
    raise SystemExit(f"altair rendered {img.size}, larger than {TARGET}; shrink width/height")
canvas = Image.new("RGB", TARGET, PAGE_BG)
canvas.paste(img, ((TARGET[0] - img.width) // 2, (TARGET[1] - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
