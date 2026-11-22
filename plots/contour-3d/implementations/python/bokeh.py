""" anyplot.ai
contour-3d: 3D Contour Plot
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-22
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import Arrow, ColorBar, FixedTicker, LinearColorMapper, PrintfTickFormatter, VeeHead
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (single-polarity ramp below uses positions 1 and 3)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]


def lerp_hex(c0, c1, t):
    a = [int(c0[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(p + (q - p) * t):02X}" for p, q in zip(a, b, strict=True))


IMPRINT_SEQ = [lerp_hex(IMPRINT_PALETTE[0], IMPRINT_PALETTE[2], t / 255) for t in range(256)]

# Constants
N_LEVELS = 10  # regular contour levels between the lowest and highest height
VIEW_ELEVATION = 28  # degrees above the base plane
VIEW_AZIMUTH = 45  # degrees of rotation about the vertical axis
Z_SPAN = 0.55  # drawn height of the surface as a share of the x-y extent
LIFT = 0.35  # gap between base plane and surface foot, as a share of the drawn height

# Columns: set these to your table's column names
X = "x"  # role: x
Y = "y"  # role: y
AMPLITUDE = "Amplitude (a.u.)"  # role: z

# Data: replace this block with your own table, for example df = pd.read_csv("field.csv")
grid = np.linspace(-3, 3, 40)
gx, gy = np.meshgrid(grid, grid)
gz = np.exp(-(gx**2 + gy**2) / 1.5) + 0.6 * np.exp(-((gx - 1.5) ** 2 + (gy + 1.2) ** 2) / 0.8)
df = pd.DataFrame({X: gx.ravel(), Y: gy.ravel(), AMPLITUDE: gz.ravel()})

# Plot: reads only df and the constants above
field = df.pivot(index=Y, columns=X, values=AMPLITUDE)
xs, ys, zgrid = field.columns.to_numpy(), field.index.to_numpy(), field.to_numpy()
z_min, z_max = np.nanmin(zgrid), np.nanmax(zgrid)
x_lo, x_hi, y_lo, y_hi = xs.min(), xs.max(), ys.min(), ys.max()
z_scale = Z_SPAN * max(x_hi - x_lo, y_hi - y_lo) / (z_max - z_min)
lift = LIFT * (z_max - z_min) * z_scale

cos_a, sin_a = np.cos(np.radians(VIEW_AZIMUTH)), np.sin(np.radians(VIEW_AZIMUTH))
cos_e, sin_e = np.cos(np.radians(VIEW_ELEVATION)), np.sin(np.radians(VIEW_ELEVATION))


def project(px, py, height):
    """Orthographic oblique view: screen x, screen y and depth (larger = farther from the viewer)."""
    px, py, height = np.broadcast_arrays(np.asarray(px, float), np.asarray(py, float), np.asarray(height, float))
    rot_x = px * cos_a - py * sin_a
    rot_y = px * sin_a + py * cos_a
    return rot_x, rot_y * sin_e + height * cos_e, rot_y * cos_e - height * sin_e


def ramp_color(value):
    idx = np.clip(((value - z_min) / (z_max - z_min) * 255).astype(int), 0, 255)
    return [IMPRINT_SEQ[i] for i in np.atleast_1d(idx)]


levels = np.linspace(z_min, z_max, N_LEVELS + 2)[1:-1]


def level_segments(level):
    """Marching squares: the contour at `level` as an (n, 2, 2) array of segment end points in data units."""
    segments = []
    for i in range(len(ys) - 1):
        for j in range(len(xs) - 1):
            # Cell corners counter-clockwise, then the crossing of each edge that straddles the level
            pts = [(xs[j], ys[i], zgrid[i, j]), (xs[j + 1], ys[i], zgrid[i, j + 1])]
            pts += [(xs[j + 1], ys[i + 1], zgrid[i + 1, j + 1]), (xs[j], ys[i + 1], zgrid[i + 1, j])]
            cross = []
            for (x0, y0, z0), (x1, y1, z1) in zip(pts, pts[1:] + pts[:1], strict=True):
                if (z0 - level) * (z1 - level) < 0:
                    t = (level - z0) / (z1 - z0)
                    cross.append((x0 + t * (x1 - x0), y0 + t * (y1 - y0)))
            for k in range(0, len(cross) - 1, 2):
                segments.append((cross[k], cross[k + 1]))
    return np.array(segments).reshape(-1, 2, 2)


# Surface quads: screen polygon, depth and color per grid cell
gxx, gyy = np.meshgrid(xs, ys)
sx, sy, sd = project(gxx, gyy, (zgrid - z_min) * z_scale + lift)
corners = [(slice(None, -1), slice(None, -1)), (slice(1, None), slice(None, -1)), (slice(1, None), slice(1, None))]
corners.append((slice(None, -1), slice(1, None)))
quad_x = np.stack([sx[c] for c in corners], axis=-1).reshape(-1, 4)
quad_y = np.stack([sy[c] for c in corners], axis=-1).reshape(-1, 4)
quad_depth = np.mean([sd[c] for c in corners], axis=0).ravel()
quad_color = ramp_color(np.mean([zgrid[c] for c in corners], axis=0).ravel())

# Contour segments lifted to their level height, nudged toward the viewer so they sit on the surface
seg_x, seg_y, seg_depth = [], [], []
base_lines = []
for level in levels:
    seg = level_segments(level)
    lx, ly, ld = project(seg[..., 0], seg[..., 1], (level - z_min) * z_scale + lift)
    seg_x += lx.tolist()
    seg_y += ly.tolist()
    seg_depth += list(ld.mean(axis=1) - 0.04)
    bx, by, _ = project(seg[..., 0], seg[..., 1], 0)
    base_lines.append((bx.tolist(), by.tolist(), ramp_color(np.array([level]))[0]))
seg_depth = np.array(seg_depth)

# Figure
p = figure(
    width=3200,
    height=1800,
    title="contour-3d · python · bokeh · anyplot.ai",
    toolbar_location=None,
    match_aspect=True,
    min_border_left=60,
    min_border_right=60,
    min_border_top=110,
    min_border_bottom=60,
)
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.outline_line_alpha = 0
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False

# Base-plane contours first: flat, dashed, colored by their level
for bx, by, color in base_lines:
    p.multi_line(bx, by, line_color=color, line_width=5, line_alpha=0.85)

# Surface and surface contours interleaved by depth slice, far to near, so nearer relief hides what is behind it
n_slices = 90
d_all = np.concatenate([quad_depth, seg_depth])
edges = np.linspace(d_all.min(), d_all.max(), n_slices + 1)
quad_bin = np.minimum(np.searchsorted(edges, quad_depth, side="right") - 1, n_slices - 1)
seg_bin = np.minimum(np.searchsorted(edges, seg_depth, side="right") - 1, n_slices - 1)
for b in range(n_slices - 1, -1, -1):
    q = np.where(quad_bin == b)[0]
    q = q[np.argsort(-quad_depth[q])]
    if len(q):
        p.patches(
            xs=quad_x[q].tolist(),
            ys=quad_y[q].tolist(),
            fill_color=[quad_color[i] for i in q],
            line_color=[quad_color[i] for i in q],
            line_width=1.5,
        )
    s = np.where(seg_bin == b)[0]
    if len(s):
        p.multi_line(
            xs=[seg_x[i] for i in s], ys=[seg_y[i] for i in s], line_color=INK, line_width=3.5, line_alpha=0.85
        )

# 3D axes drawn along the base-plane edges, with a vertical axis rising from the left corner
pad = 0.12 * max(x_hi - x_lo, y_hi - y_lo)
ax_x0, ax_x1, ax_y0, ax_y1 = x_lo - pad, x_hi + pad, y_lo - pad, y_hi + pad
z_top = (z_max - z_min) * z_scale * 1.25 + lift
origin = project(ax_x0, ax_y0, 0)
x_end = project(ax_x1, ax_y0, 0)
y_end = project(ax_x0, ax_y1, 0)
z_base = project(ax_x0, ax_y1, 0)
z_end = project(ax_x0, ax_y1, z_top)

for back in (project([ax_x1, ax_x1], [ax_y0, ax_y1], 0), project([ax_x0, ax_x1], [ax_y1, ax_y1], 0)):
    p.line(back[0], back[1], line_color=INK_SOFT, line_width=3, line_alpha=0.45)

axes = [(origin, x_end), (origin, y_end), (z_base, z_end)]
for start, end in axes:
    p.add_layout(
        Arrow(
            end=VeeHead(size=38, fill_color=INK_SOFT, line_color=INK_SOFT),
            x_start=float(start[0]),
            y_start=float(start[1]),
            x_end=float(end[0]),
            y_end=float(end[1]),
            line_color=INK_SOFT,
            line_width=7,
        )
    )

label_pad = 0.45
# Invisible anchor points so the automatic range also covers the axes and their labels
extent = [origin, x_end, y_end, z_end, project(ax_x1, ax_y1, 0)]
p.scatter(
    x=[float(e[0]) for e in extent] + [float(x_end[0]) + 2 * label_pad, float(z_end[0]) - 2 * label_pad],
    y=[float(e[1]) for e in extent] + [float(z_end[1]) + 2 * label_pad] * 2,
    alpha=0,
)
p.text(
    x=[float(x_end[0]) + label_pad, float(y_end[0]) - label_pad, float(z_end[0]) + label_pad * 0.2],
    y=[float(x_end[1]) - label_pad * 0.2, float(y_end[1]) + label_pad * 0.2, float(z_end[1]) + label_pad * 0.9],
    text=[X, Y, AMPLITUDE.split(" (")[0]],
    text_color=INK,
    text_font_size="40pt",
    text_font_style="italic",
    text_align="center",
    text_baseline="middle",
)

# Color bar covering the contour range, ticked at the contour levels
color_mapper = LinearColorMapper(palette=IMPRINT_SEQ, low=z_min, high=z_max)
color_bar = ColorBar(
    color_mapper=color_mapper,
    ticker=FixedTicker(ticks=[float(v) for v in levels]),
    formatter=PrintfTickFormatter(format="%.2f"),
    title=AMPLITUDE,
    title_text_font_size="40pt",
    title_text_color=INK,
    title_text_font_style="normal",
    title_standoff=30,
    major_label_text_font_size="34pt",
    major_label_text_color=INK_SOFT,
    major_tick_line_color=INK_SOFT,
    major_tick_line_width=3,
    bar_line_color=None,
    background_fill_color=PAGE_BG,
    width=70,
    padding=30,
    margin=40,
)
p.add_layout(color_bar, "right")

# Output
output_file(f"plot-{THEME}.html")
save(p)

W, H = 3200, 1800
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
