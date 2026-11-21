"""anyplot.ai
venn-basic: Venn Diagram
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
"""

import math
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

# Imprint palette: all eight positions, one per set in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SET_COLUMNS = ["Machine Learning", "Statistics", "Data Engineering"]  # role: set_labels
COUNT = "Elements"  # role: intersections

# Data: replace this block with your own table, for example df = pd.read_csv("regions.csv")
# One row per region, one True/False column per set, and the exclusive element count of the region.
# The example follows set sizes 100, 80, 60 with overlaps AB=30, AC=20, BC=25 and ABC=10 (all inclusive).
df = pd.DataFrame(
    {
        SET_COLUMNS[0]: [True, False, False, True, True, False, True],
        SET_COLUMNS[1]: [False, True, False, True, False, True, True],
        SET_COLUMNS[2]: [False, False, True, False, True, True, True],
        COUNT: [60, 35, 25, 20, 10, 15, 10],
    }
)

# Plot: reads only df and the constants above
VIEW_W, VIEW_H = 760, 400
membership = df[SET_COLUMNS].fillna(False).to_numpy(dtype=bool)
counts = df[COUNT].to_numpy(dtype=float)

# Inclusive set sizes and pairwise overlaps, summed from the exclusive region counts
sizes = np.array([counts[membership[:, i]].sum() for i in range(len(SET_COLUMNS))])
radii_unit = np.sqrt(sizes / sizes.max())


def lens_area(r1, r2, d):
    """Area of the intersection of two circles whose centers are d apart."""
    if d >= r1 + r2:
        return 0.0
    if d <= abs(r1 - r2):
        return math.pi * min(r1, r2) ** 2
    a1 = r1**2 * math.acos((d**2 + r1**2 - r2**2) / (2 * d * r1))
    a2 = r2**2 * math.acos((d**2 + r2**2 - r1**2) / (2 * d * r2))
    kite = 0.5 * math.sqrt((-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2))
    return a1 + a2 - kite


def center_distance(r1, r2, overlap_share):
    """Distance at which the lens covers overlap_share of the largest circle's area (bisection)."""
    target = overlap_share * math.pi
    lo, hi = abs(r1 - r2), r1 + r2
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if lens_area(r1, r2, mid) > target else (lo, mid)
    return (lo + hi) / 2


def pair_overlap(i, j):
    return counts[membership[:, i] & membership[:, j]].sum() / sizes.max()


# Place the circles: first at the origin, second to its right, third from the triangle of distances
d01 = center_distance(radii_unit[0], radii_unit[1], pair_overlap(0, 1))
d02 = center_distance(radii_unit[0], radii_unit[2], pair_overlap(0, 2))
d12 = center_distance(radii_unit[1], radii_unit[2], pair_overlap(1, 2))
x2 = (d01**2 + d02**2 - d12**2) / (2 * d01)
centers = np.array([[0.0, 0.0], [d01, 0.0], [x2, math.sqrt(max(d02**2 - x2**2, 0.0))]])

# Scale the layout to the view and center its bounding box on the origin
lo_xy = (centers - radii_unit[:, None]).min(axis=0)
hi_xy = (centers + radii_unit[:, None]).max(axis=0)
scale = min(500 / (hi_xy[0] - lo_xy[0]), 290 / (hi_xy[1] - lo_xy[1]))
centers = (centers - (lo_xy + hi_xy) / 2) * scale
radii = radii_unit * scale

# Each region's label sits at the point deepest inside it (farthest from every circle outline)
gx, gy = np.meshgrid(np.arange(-VIEW_W / 2, VIEW_W / 2, 1.0), np.arange(-VIEW_H / 2, VIEW_H / 2, 1.0))
dist = np.stack([np.hypot(gx - cx, gy - cy) for cx, cy in centers])
inside = dist < radii[:, None, None]
depth = np.abs(dist - radii[:, None, None]).min(axis=0)
region_rows = []
for row, count in zip(membership, counts, strict=True):
    mask = (inside == row[:, None, None]).all(axis=0)
    if mask.any():
        k = np.argmax(np.where(mask, depth, -1.0))
        region_rows.append({"x": gx.ravel()[k], "y": gy.ravel()[k], "text": f"{count:g}"})
regions = pd.DataFrame(region_rows)

# Set names sit outside their circle, pushed away from the middle of the layout
LABEL_SIZE = 14
outward = centers - centers.mean(axis=0)
outward /= np.linalg.norm(outward, axis=1, keepdims=True)
half_w = 0.3 * LABEL_SIZE * np.array([len(name) for name in SET_COLUMNS])
reach = radii + 8 + np.abs(outward[:, 0]) * half_w + np.abs(outward[:, 1]) * LABEL_SIZE * 0.6
label_xy = centers + outward * reach[:, None]

sets = pd.DataFrame(
    {
        "x": centers[:, 0],
        "y": centers[:, 1],
        "set": SET_COLUMNS,
        "area": math.pi * radii**2,
        "label_x": label_xy[:, 0],
        "label_y": label_xy[:, 1],
    }
)

x_scale = alt.Scale(domain=[-VIEW_W / 2, VIEW_W / 2])
y_scale = alt.Scale(domain=[-VIEW_H / 2, VIEW_H / 2])
set_colors = alt.Scale(domain=SET_COLUMNS, range=IMPRINT_PALETTE)

# One translucent filled circle per set with a solid outline; area follows the set size
circles = (
    alt.Chart(sets)
    .mark_circle(fillOpacity=0.3, strokeOpacity=1, strokeWidth=2.5)
    .encode(
        x=alt.X("x:Q", scale=x_scale, axis=None),
        y=alt.Y("y:Q", scale=y_scale, axis=None),
        size=alt.Size("area:Q", scale=None, legend=None),
        fill=alt.Fill("set:N", scale=set_colors, legend=None),
        stroke=alt.Stroke("set:N", scale=set_colors, legend=None),
    )
)

region_counts = (
    alt.Chart(regions)
    .mark_text(fontSize=15, fontWeight="bold", color=INK)
    .encode(x=alt.X("x:Q", scale=x_scale, axis=None), y=alt.Y("y:Q", scale=y_scale, axis=None), text="text:N")
)

set_names = (
    alt.Chart(sets)
    .mark_text(fontSize=LABEL_SIZE, fontWeight="bold", color=INK_SOFT)
    .encode(
        x=alt.X("label_x:Q", scale=x_scale, axis=None), y=alt.Y("label_y:Q", scale=y_scale, axis=None), text="set:N"
    )
)

# Style
chart = (
    alt.layer(circles, region_counts, set_names)
    .properties(
        width=VIEW_W,
        height=VIEW_H,
        background=PAGE_BG,
        padding={"left": 0, "right": 0, "top": 0, "bottom": 0},
        title=alt.Title("venn-basic · python · altair · anyplot.ai", fontSize=16, anchor="middle", color=INK),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
)

# Save outputs, padding (never cropping) the PNG up to the 3200 x 1800 canvas
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    raise SystemExit(f"vl-convert produced {img.width}x{img.height}, exceeds {TARGET_W}x{TARGET_H}")
if img.size != (TARGET_W, TARGET_H):
    canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
    canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
    canvas.save(f"plot-{THEME}.png")
