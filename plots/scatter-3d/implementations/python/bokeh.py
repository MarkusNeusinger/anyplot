""" anyplot.ai
scatter-3d: 3D Scatter Plot
Library: bokeh 3.10.1 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-09
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
X = "Bill Length (mm)"  # role: x
Y = "Flipper Length (mm)"  # role: y
Z = "Body Mass (kg)"  # role: z

# Data: replace this block with your own table, for example df = pd.read_csv("penguins.csv")
# Field measurements of three penguin species, 50 birds each
np.random.seed(42)
species = {  # mean and spread of (bill, flipper, mass) per species
    "Adelie": ((38.8, 190.0, 3.70), (2.4, 6.5, 0.42)),
    "Chinstrap": ((48.8, 195.8, 3.73), (3.0, 7.0, 0.38)),
    "Gentoo": ((47.5, 217.2, 5.08), (2.8, 6.2, 0.45)),
}
df = pd.DataFrame(
    np.vstack([np.random.normal(mean, sd, size=(50, 3)) for mean, sd in species.values()]), columns=[X, Y, Z]
)

# Plot: reads only df and the constants above
# Orthographic view as one matrix: rotate about z by the azimuth, tilt by the elevation
PROJ = np.array(
    [
        [np.cos(AZIMUTH), -np.sin(AZIMUTH), 0.0],
        [np.sin(AZIMUTH) * np.sin(ELEVATION), np.cos(AZIMUTH) * np.sin(ELEVATION), np.cos(ELEVATION)],
    ]
)
DEPTH = np.array([np.sin(AZIMUTH) * np.cos(ELEVATION), np.cos(AZIMUTH) * np.cos(ELEVATION), -np.sin(ELEVATION)])
half = np.array([BOX_HALF["x"], BOX_HALF["y"], BOX_HALF["z"]])
bx, by, bz = half

# Normalize each column into the box, then project the markers
values = df[[X, Y, Z]].to_numpy(dtype=float)
lo, hi = np.nanmin(values, axis=0), np.nanmax(values, axis=0)
span = np.where(hi > lo, hi - lo, 1.0)
normed = (2 * (values - lo) / span - 1) * half
screen_xy = normed @ PROJ.T
depth = normed @ DEPTH

# Projected marks, sorted back to front; far points are drawn smaller
nearness = 1 - (depth - np.nanmin(depth)) / ((np.nanmax(depth) - np.nanmin(depth)) or 1.0)
marks = df.assign(px=screen_xy[:, 0], py=screen_xy[:, 1], size=24 + nearness * 24)
source = ColumnDataSource(marks.iloc[np.argsort(-depth, kind="stable")])

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
# Every line is a segment between two 3D corners, projected in one matrix product
ticks = {axis: np.linspace(-BOX_HALF[axis], BOX_HALF[axis], N_TICKS) for axis in BOX_HALF}
pane_segments = np.array(
    [s for t in ticks["x"] for s in (((t, -by, -bz), (t, by, -bz)), ((t, by, -bz), (t, by, bz)))]
    + [s for t in ticks["y"] for s in (((-bx, t, -bz), (bx, t, -bz)), ((bx, t, -bz), (bx, t, bz)))]
    + [s for t in ticks["z"] for s in (((bx, -by, t), (bx, by, t)), ((-bx, by, t), (bx, by, t)))]
)
pane_xy = pane_segments @ PROJ.T
p.multi_line(xs=pane_xy[..., 0].tolist(), ys=pane_xy[..., 1].tolist(), line_color=INK, line_alpha=0.12, line_width=2)

# Box edges: faint solid edges, plus one dashed hidden edge so the cube reads as a volume
edge_segments = np.array(
    [
        ((bx, by, -bz), (bx, by, bz)),
        ((-bx, by, bz), (bx, by, bz)),
        ((bx, -by, bz), (bx, by, bz)),
        ((bx, -by, -bz), (bx, -by, bz)),
        ((-bx, -by, bz), (-bx, by, bz)),
        ((-bx, -by, bz), (bx, -by, bz)),
        ((-bx, -by, -bz), (-bx, -by, bz)),
    ]
)
edge_xy = edge_segments @ PROJ.T
edge_style = {"line_color": INK_SOFT, "line_alpha": 0.45, "line_width": 3}
p.multi_line(xs=edge_xy[:-1, :, 0].tolist(), ys=edge_xy[:-1, :, 1].tolist(), **edge_style)
p.line(edge_xy[-1, :, 0], edge_xy[-1, :, 1], line_dash=[10, 8], **edge_style)

# Points: color carries the z value, translucency lets interior points show through
color_mapper = LinearColorMapper(palette=IMPRINT_SEQ256, low=lo[2], high=hi[2])
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
axis_specs = (
    (0, X, (-bx, -by, -bz), (bx, -by, -bz), (0.04, -0.06), "left", "top"),
    (1, Y, (-bx, -by, -bz), (-bx, by, -bz), (-0.04, -0.06), "right", "top"),
    (2, Z, (-bx, by, -bz), (-bx, by, bz), (-0.07, 0.0), "right", "middle"),
)
for i, col, corner_lo, corner_hi, tick_offset, align, baseline in axis_specs:
    tick_xy = (np.array(corner_lo) + np.outer(np.linspace(0, 1, N_TICKS), np.subtract(corner_hi, corner_lo))) @ PROJ.T
    start, end = tick_xy[0], tick_xy[-1]
    p.line([start[0], end[0]], [start[1], end[1]], line_color=INK_SOFT, line_width=5)

    direction = (end - start) / np.linalg.norm(end - start)
    perp = np.array([-direction[1], direction[0]])
    base = end - direction * 0.12
    arrow = [end, base + perp * 0.035, base - perp * 0.035]
    p.patch(x=[a[0] for a in arrow], y=[a[1] for a in arrow], fill_color=INK_SOFT, line_color=INK_SOFT)

    for tick, value in zip(tick_xy, np.linspace(lo[i], hi[i], N_TICKS), strict=True):
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
    mid = (start + end) / 2
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
