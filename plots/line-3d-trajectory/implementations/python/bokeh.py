"""anyplot.ai
line-3d-trajectory: 3D Line Plot for Trajectory Visualization
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-16
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColorBar, ColumnDataSource, HoverTool, Label, LinearColorMapper, Range1d
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
n_points = 1500
dt = 0.01
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
norm = (coords - coords.mean()) / coords.std() * 2
nx, ny, nz = norm[X].to_numpy(), norm[Y].to_numpy(), norm[Z].to_numpy()

# Oblique projection (elevation=20°, azimuth=55°)
elev_rad = np.radians(20)
azim_rad = np.radians(55)


def project(px, py, pz):
    x_rot = px * np.cos(azim_rad) - py * np.sin(azim_rad)
    y_rot = px * np.sin(azim_rad) + py * np.cos(azim_rad)
    return x_rot, y_rot * np.sin(elev_rad) + pz * np.cos(elev_rad)


x_proj, y_proj = project(nx, ny, nz)
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
    alpha=0.12,
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

# 3D axes drawn from the projected origin of the standardized space
axis_length = 2.5
arrow_size = 0.18
origin = np.array(project(0.0, 0.0, 0.0))
axis_ends = {
    X: np.array(project(axis_length, 0.0, 0.0)),
    Y: np.array(project(0.0, axis_length, 0.0)),
    Z: np.array(project(0.0, 0.0, axis_length)),
}
label_offsets = {X: (0.15, -0.2), Y: (-0.75, -0.4), Z: (0.15, 0.1)}
for name, end in axis_ends.items():
    p.line(x=[origin[0], end[0]], y=[origin[1], end[1]], line_color=INK_SOFT, line_width=4)
    direction = (end - origin) / np.linalg.norm(end - origin)
    perp = np.array([-direction[1], direction[0]])
    base = end - arrow_size * direction
    p.patch(
        x=[end[0], base[0] + arrow_size * 0.5 * perp[0], base[0] - arrow_size * 0.5 * perp[0]],
        y=[end[1], base[1] + arrow_size * 0.5 * perp[1], base[1] - arrow_size * 0.5 * perp[1]],
        fill_color=INK_SOFT,
        line_color=INK_SOFT,
    )
    dx, dy = label_offsets[name]
    p.add_layout(
        Label(x=end[0] + dx, y=end[1] + dy, text=name, text_font_size="42pt", text_color=INK, text_font_style="bold")
    )

# Ranges from the projected data and axes, with padding
all_x = np.concatenate([x_proj, [origin[0]], [e[0] for e in axis_ends.values()]])
all_y = np.concatenate([y_proj, [origin[1]], [e[1] for e in axis_ends.values()]])
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
