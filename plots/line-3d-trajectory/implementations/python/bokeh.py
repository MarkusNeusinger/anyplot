"""anyplot.ai
line-3d-trajectory: 3D Line Plot for Trajectory Visualization
Library: bokeh 3.10.1 | Python 3.14.10
Quality: 78/100 | Updated: 2026-11-09
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColorBar, ColumnDataSource, HoverTool, Label, LabelSet, LinearColorMapper, Range1d
from bokeh.plotting import figure
from bokeh.resources import CDN
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (read from environment)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
ANYPLOT_AMBER = "#DDCC77"


# imprint_seq: 256-stop sequential ramp, brand green -> blue
def _lerp_hex(c0, c1, t):
    r0, g0, b0 = (int(c0[i : i + 2], 16) for i in (1, 3, 5))
    r1, g1, b1 = (int(c1[i : i + 2], 16) for i in (1, 3, 5))
    r, g, b = (int(round(a + (b - a) * t)) for a, b in ((r0, r1), (g0, g1), (b0, b1)))
    return f"#{r:02X}{g:02X}{b:02X}"


IMPRINT_SEQ256 = [_lerp_hex("#009E73", "#4467A3", t / 255.0) for t in range(256)]

# Columns: set these to your table's column names
X = "X (state)"  # role: x
Y = "Y (state)"  # role: y
Z = "Z (state)"  # role: z
TIME = "Time (s)"  # role: color

# Data: replace this block with your own table, for example df = pd.read_csv("trajectory.csv")
# Lorenz attractor (sigma=10, rho=28, beta=8/3), inline Euler integration
sigma, rho, beta = 10.0, 28.0, 8.0 / 3.0
n_points = 2000
dt = 0.005
xs, ys, zs = np.zeros(n_points), np.zeros(n_points), np.zeros(n_points)
xs[0], ys[0], zs[0] = 0.1, 0.0, 0.0
for i in range(n_points - 1):
    xs[i + 1] = xs[i] + sigma * (ys[i] - xs[i]) * dt
    ys[i + 1] = ys[i] + (xs[i] * (rho - zs[i]) - ys[i]) * dt
    zs[i + 1] = zs[i] + (xs[i] * ys[i] - beta * zs[i]) * dt
df = pd.DataFrame({TIME: np.linspace(0, n_points * dt, n_points), X: xs, Y: ys, Z: zs})

# Plot: reads only df and the constants above
# Standardize each coordinate so all three axes share one scale in the projection
coords = df[[X, Y, Z]].astype(float)
mean, std = coords.mean(), coords.std().fillna(0).replace(0, 1)
norm = ((coords - mean) / std * 2).to_numpy()

# Oblique projection (elevation=20°, azimuth=55°) as a 3x2 matrix: standardized xyz -> screen xy
elev_rad, azim_rad = np.radians(20), np.radians(55)
proj = np.array(
    [
        [np.cos(azim_rad), np.sin(azim_rad) * np.sin(elev_rad)],
        [-np.sin(azim_rad), np.cos(azim_rad) * np.sin(elev_rad)],
        [0.0, np.cos(elev_rad)],
    ]
)
x_proj, y_proj = (norm @ proj).T
times = df[TIME].astype(float).to_numpy()

# Line as consecutive segments, each colored by the time at its start
segments = ColumnDataSource(
    data={"x0": x_proj[:-1], "y0": y_proj[:-1], "x1": x_proj[1:], "y1": y_proj[1:], "t": times[:-1]}
)
color_mapper = LinearColorMapper(palette=IMPRINT_SEQ256, low=np.nanmin(times), high=np.nanmax(times))

# Points for hover, showing the original values
hover_step = max(1, len(df) // 150)
hover_rows = df.iloc[::hover_step]
hover_source = ColumnDataSource(
    data={
        "px": x_proj[::hover_step],
        "py": y_proj[::hover_step],
        "t": hover_rows[TIME].to_numpy(),
        "x": hover_rows[X].to_numpy(),
        "y": hover_rows[Y].to_numpy(),
        "z": hover_rows[Z].to_numpy(),
    }
)

title = "Lorenz Attractor · line-3d-trajectory · python · bokeh · anyplot.ai"
title_pt = round(50 * (67 / len(title) if len(title) > 67 else 1.0))

p = figure(
    width=3200,
    height=1800,
    title=title,
    toolbar_location=None,
    tools="pan,wheel_zoom,box_zoom,reset,save",
    min_border_top=110,
    min_border_bottom=60,
    min_border_left=60,
    min_border_right=60,
)

p.segment(
    x0="x0",
    y0="y0",
    x1="x1",
    y1="y1",
    source=segments,
    line_color={"field": "t", "transform": color_mapper},
    line_width=4,
    line_alpha=0.85,
    line_cap="round",
)

scatter = p.scatter(
    x="px",
    y="py",
    source=hover_source,
    size=18,
    fill_color=INK_SOFT,
    line_color=None,
    alpha=0.0,
    hover_fill_color=ANYPLOT_AMBER,
    hover_alpha=0.95,
)
p.add_tools(
    HoverTool(
        renderers=[scatter],
        tooltips=[(TIME, "@t{0.2f}"), (X, "@x{0.2f}"), (Y, "@y{0.2f}"), (Z, "@z{0.2f}")],
        mode="mouse",
    )
)

# 3D axes along edges of the data's bounding box, with value ticks: X and Y along the front floor
# edges from the min corner, Z up the outer vertical edge at the far end of X, clear of the path
lo, hi = np.nanmin(norm, axis=0), np.nanmax(norm, axis=0)
hi = np.where(hi > lo, hi, lo + 1.0)  # a constant column still gets a visible axis
z_start = lo.copy()
z_start[0] = hi[0]
axis_starts = (lo, lo, z_start)
center = ((lo + hi) / 2) @ proj
span = np.linalg.norm(hi - lo)
tick_len = 0.012 * span
ticks = {"x0": [], "y0": [], "x1": [], "y1": [], "lx": [], "ly": [], "text": []}
extent_x, extent_y = [], []
for k, name in enumerate((X, Y, Z)):
    start_3d = axis_starts[k]
    corner = start_3d @ proj
    end_3d = start_3d.copy()
    end_3d[k] = hi[k]
    end = end_3d @ proj
    direction = (end - corner) / np.linalg.norm(end - corner)
    perp = np.array([-direction[1], direction[0]])
    # Ticks and labels point away from the data, onto empty canvas
    if np.dot(perp, (corner + end) / 2 - center) < 0:
        perp = -perp
    p.line(x=[corner[0], end[0]], y=[corner[1], end[1]], line_color=INK_SOFT, line_width=4)

    # "Nice" tick values in the original units of this column
    v_lo, v_hi = coords[name].min(), coords[name].max()
    raw_step = (v_hi - v_lo) / 4 or max(abs(v_hi), 1.0)
    magnitude = 10 ** np.floor(np.log10(raw_step))
    step = magnitude * next(m for m in (1, 2, 2.5, 5, 10) if m * magnitude >= raw_step)
    for value in np.arange(np.ceil(v_lo / step) * step, v_hi + step * 1e-9, step):
        point_3d = start_3d.copy()
        point_3d[k] = (value - mean[name]) / std[name] * 2
        pos = point_3d @ proj
        ticks["x0"].append(pos[0])
        ticks["y0"].append(pos[1])
        ticks["x1"].append(pos[0] + tick_len * perp[0])
        ticks["y1"].append(pos[1] + tick_len * perp[1])
        ticks["lx"].append(pos[0] + 3.2 * tick_len * perp[0])
        ticks["ly"].append(pos[1] + 3.2 * tick_len * perp[1])
        ticks["text"].append(f"{value:g}")
    # Axis title at the middle of the axis, outside its tick labels; Z reads upright along its axis
    label_pos = (corner + end) / 2 + 7.5 * tick_len * perp
    p.add_layout(
        Label(
            x=label_pos[0],
            y=label_pos[1],
            text=name,
            text_font_size="40pt",
            text_color=INK,
            text_font_style="bold",
            text_align="center",
            text_baseline="middle",
            angle=np.pi / 2 if k == 2 else 0.0,
        )
    )
    extent_x += [corner[0], end[0], label_pos[0]]
    extent_y += [corner[1], end[1], label_pos[1]]

tick_source = ColumnDataSource(data=ticks)
p.segment(x0="x0", y0="y0", x1="x1", y1="y1", source=tick_source, line_color=INK_SOFT, line_width=3)
p.add_layout(
    LabelSet(
        x="lx",
        y="ly",
        text="text",
        source=tick_source,
        text_font_size="30pt",
        text_color=INK_SOFT,
        text_align="center",
        text_baseline="middle",
    )
)

# Ranges from the projected data, axes and their labels, with padding
all_x = np.concatenate([x_proj, extent_x, ticks["lx"]])
all_y = np.concatenate([y_proj, extent_y, ticks["ly"]])
x_min, x_max = np.nanmin(all_x), np.nanmax(all_x)
y_min, y_max = np.nanmin(all_y), np.nanmax(all_y)
x_pad = (x_max - x_min) * 0.12
y_pad = (y_max - y_min) * 0.12
p.x_range = Range1d(x_min - x_pad, x_max + x_pad)
p.y_range = Range1d(y_min - y_pad, y_max + y_pad)

# Hide the 2D axes; the drawn 3D axes replace them
p.xaxis.visible = False
p.yaxis.visible = False

# Color bar for time progression
color_bar = ColorBar(
    color_mapper=color_mapper,
    width=60,
    location=(0, 0),
    title=TIME,
    title_text_font_size="42pt",
    title_text_color=INK,
    major_label_text_font_size="34pt",
    major_label_text_color=INK_SOFT,
    major_tick_line_color=INK_SOFT,
    bar_line_color=None,
    background_fill_color=PAGE_BG,
    title_standoff=24,
    margin=40,
    padding=24,
)
p.add_layout(color_bar, "right")

# Style
p.title.text_font_size = f"{title_pt}pt"
p.title.text_font_style = "bold"
p.title.text_color = INK

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10
p.xgrid.grid_line_dash = [6, 4]
p.ygrid.grid_line_dash = [6, 4]

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Save HTML for the interactive version
output_file(f"plot-{THEME}.html")
save(p, resources=CDN, title="line-3d-trajectory · python · bokeh · anyplot.ai")

# Screenshot with headless Chrome via Selenium
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
