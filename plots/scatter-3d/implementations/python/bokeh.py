""" anyplot.ai
scatter-3d: 3D Scatter Plot
Library: bokeh 3.10.1 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-09
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColorBar, ColumnDataSource, HoverTool, Label, LinearColorMapper
from bokeh.plotting import figure
from bokeh.resources import CDN
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (read from environment, default light)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"


# Imprint sequential colormap: 256 stops from position 1 (#009E73) to #4467A3
def _lerp_hex(c0, c1, t):
    r0, g0, b0 = (int(c0[i : i + 2], 16) for i in (1, 3, 5))
    r1, g1, b1 = (int(c1[i : i + 2], 16) for i in (1, 3, 5))
    r, g, b = (int(round(a + (b - a) * t)) for a, b in ((r0, r1), (g0, g1), (b0, b1)))
    return f"#{r:02X}{g:02X}{b:02X}"


IMPRINT_SEQ256 = [_lerp_hex("#009E73", "#4467A3", t / 255.0) for t in range(256)]

# Constants: view angles and the box shape of the projection
ELEVATION = np.radians(25)
AZIMUTH = np.radians(45)
BOX_HALF = {"x": 1.0, "y": 1.0, "z": 0.8}  # half-extent of each normalized axis
N_TICKS = 5

# Columns: set these to your table's column names
X = "X-Axis (units)"  # role: x
Y = "Y-Axis (units)"  # role: y
Z = "Z-Axis (units)"  # role: z

# Data: replace this block with your own table, for example df = pd.read_csv("points.csv")
np.random.seed(42)
n_per_cluster = 50
x1 = np.random.randn(n_per_cluster) * 0.8 + 2
y1 = np.random.randn(n_per_cluster) * 0.8 + 2
z1 = np.random.randn(n_per_cluster) * 0.8 + 2
x2 = np.random.randn(n_per_cluster) * 0.7 - 2
y2 = np.random.randn(n_per_cluster) * 0.7 - 1
z2 = np.random.randn(n_per_cluster) * 0.7 + 3
x3 = np.random.randn(n_per_cluster) * 0.9
y3 = np.random.randn(n_per_cluster) * 0.9 - 2
z3 = np.random.randn(n_per_cluster) * 0.9 - 1
df = pd.DataFrame({X: np.concatenate([x1, x2, x3]), Y: np.concatenate([y1, y2, y3]), Z: np.concatenate([z1, z2, z3])})

# Plot: reads only df and the constants above
lims = {axis: (df[col].min(), df[col].max()) for axis, col in (("x", X), ("y", Y), ("z", Z))}


def normalize(values, axis):
    lo, hi = lims[axis]
    span = (hi - lo) or 1.0
    return (2 * (np.asarray(values, dtype=float) - lo) / span - 1) * BOX_HALF[axis]


def project(xn, yn, zn):
    """Orthographic view: rotate about z by the azimuth, tilt by the elevation."""
    x_rot = xn * np.cos(AZIMUTH) - yn * np.sin(AZIMUTH)
    y_rot = xn * np.sin(AZIMUTH) + yn * np.cos(AZIMUTH)
    screen_y = y_rot * np.sin(ELEVATION) + zn * np.cos(ELEVATION)
    depth = y_rot * np.cos(ELEVATION) - zn * np.sin(ELEVATION)
    return x_rot, screen_y, depth


bx, by, bz = BOX_HALF["x"], BOX_HALF["y"], BOX_HALF["z"]


def screen(xn, yn, zn):
    sx, sy, _ = project(np.asarray(xn, dtype=float), np.asarray(yn, dtype=float), np.asarray(zn, dtype=float))
    return list(sx), list(sy)


# Projected marks, sorted back to front; far points are drawn smaller
px, py, depth = project(normalize(df[X], "x"), normalize(df[Y], "y"), normalize(df[Z], "z"))
nearness = 1 - (depth - np.nanmin(depth)) / ((np.nanmax(depth) - np.nanmin(depth)) or 1.0)
marks = df.assign(px=px, py=py, size=24 + nearness * 24).iloc[np.argsort(-depth, kind="stable")]
source = ColumnDataSource(marks)

title = "scatter-3d · python · bokeh · anyplot.ai"
p = figure(
    width=2400,
    height=2400,
    title=title,
    toolbar_location=None,
    tools="pan,wheel_zoom,box_zoom,reset,save",
    match_aspect=True,
    min_border_top=110,
    min_border_left=60,
    min_border_bottom=60,
    min_border_right=60,
)

# Pane grids on the floor and the two back walls (the walls at max x and max y face the viewer)
ticks = {axis: np.linspace(-BOX_HALF[axis], BOX_HALF[axis], N_TICKS) for axis in BOX_HALF}
pane_style = {"line_color": INK, "line_alpha": 0.12, "line_width": 2}
for t in ticks["x"]:
    p.line(*screen([t, t], [-by, by], [-bz, -bz]), **pane_style)  # floor
    p.line(*screen([t, t], [by, by], [-bz, bz]), **pane_style)  # back wall y = max
for t in ticks["y"]:
    p.line(*screen([-bx, bx], [t, t], [-bz, -bz]), **pane_style)  # floor
    p.line(*screen([bx, bx], [t, t], [-bz, bz]), **pane_style)  # back wall x = max
for t in ticks["z"]:
    p.line(*screen([bx, bx], [-by, by], [t, t]), **pane_style)
    p.line(*screen([-bx, bx], [by, by], [t, t]), **pane_style)

# Box edges: back edges faint, front top edges dashed so the cube reads as a volume
edge_style = {"line_color": INK_SOFT, "line_alpha": 0.45, "line_width": 3}
for xs, ys, zs in (
    ([bx, bx], [by, by], [-bz, bz]),
    ([-bx, bx], [by, by], [bz, bz]),
    ([bx, bx], [-by, by], [bz, bz]),
    ([bx, bx], [-by, -by], [-bz, bz]),
    ([-bx, -bx], [-by, by], [bz, bz]),
    ([-bx, bx], [-by, -by], [bz, bz]),
):
    p.line(*screen(xs, ys, zs), **edge_style)
p.line(*screen([-bx, -bx], [-by, -by], [-bz, bz]), line_dash=[10, 8], **edge_style)
p.line(*screen([bx, bx], [by, by], [-bz, -bz]), **edge_style)

# Points: color carries the z value, translucency lets interior points show through
color_mapper = LinearColorMapper(palette=IMPRINT_SEQ256, low=lims["z"][0], high=lims["z"][1])
points = p.scatter(
    x="px",
    y="py",
    size="size",
    source=source,
    fill_color={"field": Z, "transform": color_mapper},
    fill_alpha=0.8,
    line_color=PAGE_BG,
    line_width=1.5,
)
p.add_tools(HoverTool(renderers=[points], tooltips=[(c, f"@{{{c}}}{{0.00}}") for c in (X, Y, Z)]))


# Axes along three outer edges, each with an arrow, value ticks and its label
def point(xn, yn, zn):
    sx, sy, _ = project(xn, yn, zn)
    return np.array([sx, sy])


axis_specs = (
    ("x", X, lambda s: point(s, -by, -bz), (0.04, -0.06), "left", "top"),
    ("y", Y, lambda s: point(-bx, s, -bz), (-0.04, -0.06), "right", "top"),
    ("z", Z, lambda s: point(-bx, by, s), (-0.07, 0.0), "right", "middle"),
)
for axis, col, at, tick_offset, align, baseline in axis_specs:
    half = BOX_HALF[axis]
    start, end = at(-half), at(half)
    p.line([start[0], end[0]], [start[1], end[1]], line_color=INK_SOFT, line_width=5)

    direction = (end - start) / np.linalg.norm(end - start)
    perp = np.array([-direction[1], direction[0]])
    base = end - direction * 0.12
    arrow = [end, base + perp * 0.035, base - perp * 0.035]
    p.patch(x=[a[0] for a in arrow], y=[a[1] for a in arrow], fill_color=INK_SOFT, line_color=INK_SOFT)

    lo, hi = lims[axis]
    for t, value in zip(ticks[axis], np.linspace(lo, hi, N_TICKS), strict=True):
        tick = at(t)
        p.add_layout(
            Label(
                x=tick[0] + tick_offset[0],
                y=tick[1] + tick_offset[1],
                text=f"{value:.1f}",
                text_font_size="28pt",
                text_color=INK_SOFT,
                text_align=align,
                text_baseline=baseline,
            )
        )

    # Axis title outside the box, parallel to its edge and kept upright
    mid = at(0.0)
    outward = mid / (np.linalg.norm(mid) or 1.0)
    angle = np.arctan2(direction[1], direction[0])
    if angle > np.pi / 2 + 1e-6:
        angle -= np.pi
    p.add_layout(
        Label(
            x=mid[0] + outward[0] * 0.3,
            y=mid[1] + outward[1] * 0.3,
            text=col,
            text_font_size="40pt",
            text_font_style="bold",
            text_color=INK,
            text_align="center",
            text_baseline="middle",
            angle=float(angle),
        )
    )

# Color bar labeled with the variable it encodes
color_bar = ColorBar(
    color_mapper=color_mapper,
    width=50,
    title=Z,
    title_text_font_size="34pt",
    title_text_color=INK,
    title_text_font_style="normal",
    major_label_text_font_size="28pt",
    major_label_text_color=INK_SOFT,
    major_tick_line_color=INK_SOFT,
    bar_line_color=None,
    background_fill_color=PAGE_BG,
    title_standoff=24,
    margin=40,
    padding=20,
)
p.add_layout(color_bar, "right")

# Style: the 3D frame replaces the 2D axes and grid
p.title.text_font_size = "50pt"
p.title.text_font_style = "bold"
p.title.text_color = INK
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.x_range.range_padding = 0.2
p.y_range.range_padding = 0.12

# Save HTML output
output_file(f"plot-{THEME}.html")
save(p, resources=CDN, title=title)

# Screenshot with headless Chrome for the PNG
W, H = 2400, 2400
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
time.sleep(3)  # let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
