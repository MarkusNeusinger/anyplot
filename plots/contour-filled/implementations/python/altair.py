"""anyplot.ai
contour-filled: Filled Contour Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-11
"""

import os

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

# Imprint palette (positions 1 to 8); the single-signed field uses the imprint_seq ramp below
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
IMPRINT_SEQ = [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]]  # imprint_seq: brand green to blue

# Constants
N_LEVELS = 12  # number of evenly stepped bands
N_FINE = 480  # resolution the bands are resolved at, so band boundaries read as smooth curves

# Columns: set these to your table's column names
X = "X coordinate"  # role: x
Y = "Y coordinate"  # role: y
Z = "Intensity"  # role: z

# Data: replace this block with your own table, for example df = pd.read_csv("field.csv")
# Two Gaussian peaks, a dip and a faint ripple, sampled on a 90 x 90 grid
grid = np.linspace(-3, 3, 90)
gx, gy = np.meshgrid(grid, grid)
field = (
    1.5 * np.exp(-((gx - 1) ** 2 + (gy - 1) ** 2) / 0.8)
    + 1.2 * np.exp(-((gx + 1) ** 2 + (gy + 0.5) ** 2) / 1.0)
    - 0.6 * np.exp(-(gx**2 + (gy - 1.5) ** 2) / 0.6)
    + 0.2 * np.sin(gx * 2) * np.cos(gy * 2)
)
df = pd.DataFrame({X: gx.ravel(), Y: gy.ravel(), Z: field.ravel()})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
alt.data_transformers.disable_max_rows()

surface = df.pivot_table(index=Y, columns=X, values=Z, sort=True, dropna=False)
xs, ys = surface.columns.to_numpy(float), surface.index.to_numpy(float)
values = surface.to_numpy(float)

# Resample bilinearly to a fine grid, then cut it into evenly stepped level bands
fx, fy = np.linspace(xs.min(), xs.max(), N_FINE), np.linspace(ys.min(), ys.max(), N_FINE)
rows = np.array([np.interp(fx, xs, r) for r in values])
fine = np.array([np.interp(fy, ys, c) for c in rows.T]).T
levels = np.linspace(np.nanmin(values), np.nanmax(values), N_LEVELS + 1)
centers = (levels[:-1] + levels[1:]) / 2
band = np.where(np.isnan(fine), -1, np.clip(np.digitize(fine, levels) - 1, 0, N_LEVELS - 1))

# Merge neighbouring cells of one band along each row into a single rectangle
dx, dy = fx[1] - fx[0], fy[1] - fy[0]
runs = []
for r, line in enumerate(band):
    starts = np.flatnonzero(np.r_[True, line[1:] != line[:-1]])
    stops = np.r_[starts[1:], len(line)]
    for a, b in zip(starts, stops, strict=True):
        if line[a] >= 0:
            runs.append((fx[a] - dx / 2, fx[b - 1] + dx / 2, fy[r] - dy / 2, fy[r] + dy / 2, centers[line[a]]))
rects = pd.DataFrame(runs, columns=["x0", "x1", "y0", "y1", Z])
rects[["x0", "x1"]] = rects[["x0", "x1"]].clip(xs.min(), xs.max())
rects[["y0", "y1"]] = rects[["y0", "y1"]].clip(ys.min(), ys.max())

# Contour lines: fine-grid cells where the band changes toward the right or upper neighbour
edge = np.zeros_like(band, dtype=bool)
edge[:, :-1] |= band[:, :-1] != band[:, 1:]
edge[:-1, :] |= band[:-1, :] != band[1:, :]
edge &= band >= 0
iy, ix = np.nonzero(edge)
lines = pd.DataFrame({"x": fx[ix], "y": fy[iy]})

x_scale = alt.Scale(domain=[float(xs.min()), float(xs.max())], nice=False)
y_scale = alt.Scale(domain=[float(ys.min()), float(ys.max())], nice=False)
color_scale = alt.Scale(domain=[float(centers[0]), float(centers[-1])], range=IMPRINT_SEQ, interpolate="lab")
color = alt.Color(
    Z.translate(ESCAPE),
    type="quantitative",
    title=Z,
    scale=color_scale,
    legend=alt.Legend(
        type="symbol",
        values=[float(c) for c in centers],
        format=".2f",
        symbolType="square",
        symbolSize=260,
        titleFontSize=13,
        labelFontSize=11,
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        padding=8,
    ),
)

bands = (
    alt.Chart(rects)
    .mark_rect(strokeWidth=0.6)
    .encode(
        x=alt.X("x0:Q", title=X, scale=x_scale, axis=alt.Axis(tickCount=7)),
        x2="x1:Q",
        y=alt.Y("y0:Q", title=Y, scale=y_scale, axis=alt.Axis(tickCount=7)),
        y2="y1:Q",
        color=color,
        stroke=alt.Stroke(Z.translate(ESCAPE), type="quantitative", scale=color_scale, legend=None),
    )
)
contour_lines = (
    alt.Chart(lines)
    .mark_circle(size=1.6, opacity=0.35, color=INK)
    .encode(x=alt.X("x:Q", scale=x_scale), y=alt.Y("y:Q", scale=y_scale))
)

title = "contour-filled · python · altair · anyplot.ai"
chart = (
    alt.layer(bands, contour_lines)
    .properties(width=380, height=400, background=PAGE_BG, title=alt.Title(title, fontSize=16, anchor="middle"))
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=11,
        titleFontSize=13,
    )
    .configure_title(color=INK)
    .configure_legend(labelColor=INK_SOFT, titleColor=INK)
)

# Output: pad (never crop) to the 2400 x 2400 square target
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
TARGET = 2400
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET or img.height > TARGET:
    raise SystemExit(f"altair rendered {img.width}x{img.height}, larger than {TARGET}x{TARGET}; shrink the view")
canvas = Image.new("RGB", (TARGET, TARGET), PAGE_BG)
canvas.paste(img, ((TARGET - img.width) // 2, (TARGET - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
