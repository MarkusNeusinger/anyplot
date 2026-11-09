""" anyplot.ai
windbarb-basic: Wind Barb Plot for Meteorological Data
Library: bokeh 3.10.1 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-09
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Title
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: single series, first position
BRAND = "#009E73"

# Constants: standard wind barb notation (knots)
CALM_KT = 2.5
HALF_KT = 5
FULL_KT = 10
PENNANT_KT = 50

# Columns: set these to your table's column names
X_POS = "Longitude (°)"  # role: x
Y_POS = "Latitude (°N)"  # role: y
U_WIND = "U Wind (kt)"  # role: u
V_WIND = "V Wind (kt)"  # role: v

# Data: replace this block with your own table, for example df = pd.read_csv("winds.csv")
# Surface stations over the US Plains around a deep low, steered by a weak westerly flow
np.random.seed(42)
lon, lat = np.meshgrid(np.arange(-103.0, -88.0, 2.0), np.arange(31.0, 44.0, 2.0))
lon_c, lat_c = -97.0, 38.39  # low-pressure center, placed so the station just north of it is calm
v_max, r_max, westerly = 50.0, 3.0, 10.0  # peak rotation (kt), its radius (°), steering flow (kt)
dx, dy = lon - lon_c, lat - lat_c
r = np.hypot(dx, dy)
v_rot = np.where(r < r_max, v_max * r / r_max, v_max * r_max / np.maximum(r, 1e-9))
# Counterclockwise rotation (Northern Hemisphere cyclone) with a 10° inflow toward the center
inflow = np.deg2rad(10)
ex, ey = dx / np.maximum(r, 1e-9), dy / np.maximum(r, 1e-9)
u = v_rot * (-np.cos(inflow) * ey - np.sin(inflow) * ex) + westerly + np.random.normal(0, 0.8, r.shape)
v = v_rot * (np.cos(inflow) * ex - np.sin(inflow) * ey) + np.random.normal(0, 0.8, r.shape)
df = pd.DataFrame({X_POS: lon.ravel(), Y_POS: lat.ravel(), U_WIND: u.ravel(), V_WIND: v.ravel()})

# Plot: reads only df and the constants above
obs = df.dropna(subset=[X_POS, Y_POS, U_WIND, V_WIND])
pts = obs[[X_POS, Y_POS]].to_numpy(dtype=float)
speed = np.hypot(obs[U_WIND].to_numpy(dtype=float), obs[V_WIND].to_numpy(dtype=float))

# Staff length follows the station spacing so neighboring barbs stay apart
dist = np.hypot(pts[:, None, 0] - pts[None, :, 0], pts[:, None, 1] - pts[None, :, 1])
dist[dist == 0] = np.inf
nearest = dist.min(axis=1) if len(pts) > 1 else np.array([np.inf])
nearest = nearest[np.isfinite(nearest)]
spacing = np.median(nearest) if len(nearest) else max(np.ptp(pts, axis=0).max(), 1.0)
staff_len = 0.45 * spacing
feather_len = 0.42 * staff_len
feather_gap = 0.14 * staff_len
pennant_base = 0.18 * staff_len

line_xs, line_ys, pennant_xs, pennant_ys, calm_x, calm_y = [], [], [], [], [], []
for (x0, y0), u0, v0, spd in zip(pts, obs[U_WIND], obs[V_WIND], speed, strict=True):
    if spd < CALM_KT:
        calm_x.append(x0)
        calm_y.append(y0)
        continue

    # Staff points toward the direction the wind blows FROM
    angle = np.arctan2(-v0, -u0)
    along = np.array([np.cos(angle), np.sin(angle)])
    # Northern Hemisphere: feathers on the left, looking downwind
    side = np.array([np.cos(angle - np.pi / 2), np.sin(angle - np.pi / 2)])
    tip = np.array([x0, y0]) + staff_len * along
    line_xs.append([x0, tip[0]])
    line_ys.append([y0, tip[1]])

    rounded = HALF_KT * int(spd / HALF_KT + 0.5)
    pennants, rest = divmod(rounded, PENNANT_KT)
    fulls, rest = divmod(rest, FULL_KT)
    halves = int(rest >= HALF_KT)

    pos = 0.0
    for _ in range(int(pennants)):
        base = tip - pos * along
        back = tip - (pos + pennant_base) * along
        flag = base + feather_len * side
        pennant_xs.append([base[0], flag[0], back[0]])
        pennant_ys.append([base[1], flag[1], back[1]])
        pos += pennant_base + 0.5 * feather_gap
    for _ in range(int(fulls)):
        base = tip - pos * along
        end = base + feather_len * side
        line_xs.append([base[0], end[0]])
        line_ys.append([base[1], end[1]])
        pos += feather_gap
    if halves:
        # A lone half barb sits one step in from the tip, as in the standard notation
        pos = max(pos, feather_gap)
        base = tip - pos * along
        end = base + 0.5 * feather_len * side
        line_xs.append([base[0], end[0]])
        line_ys.append([base[1], end[1]])

p = figure(
    width=2400,
    height=2400,
    title="windbarb-basic · python · bokeh · anyplot.ai",
    x_axis_label=X_POS,
    y_axis_label=Y_POS,
    match_aspect=True,
    toolbar_location=None,
    min_border_bottom=200,
    min_border_left=180,
    min_border_top=110,
    min_border_right=60,
)
# Fit the auto ranges tightly to the barb extent; match_aspect still keeps the angles true
p.x_range.range_padding = 0.03
p.y_range.range_padding = 0.03

p.multi_line(xs="xs", ys="ys", source=ColumnDataSource({"xs": line_xs, "ys": line_ys}), line_width=5, line_color=BRAND)
p.patches(
    xs="xs",
    ys="ys",
    source=ColumnDataSource({"xs": pennant_xs, "ys": pennant_ys}),
    fill_color=BRAND,
    line_color=BRAND,
    line_width=3,
    line_join="miter",
)
p.scatter(
    x="x",
    y="y",
    source=ColumnDataSource({"x": calm_x, "y": calm_y}),
    size=34,
    fill_color=None,
    line_color=BRAND,
    line_width=5,
)

# Key that decodes the notation
p.add_layout(
    Title(
        text=f"Half barb = {HALF_KT} kt  ·  Full barb = {FULL_KT} kt  ·  Pennant = {PENNANT_KT} kt  ·  "
        f"Open circle = calm (< {CALM_KT:g} kt)",
        text_font_size="30pt",
        text_font_style="normal",
        text_color=INK_SOFT,
        align="center",
    ),
    "below",
)

# Style
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title.text_font_size = "50pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.15
p.ygrid.grid_line_alpha = 0.15
p.grid.grid_line_dash = [6, 4]

# Save
output_file(f"plot-{THEME}.html")
save(p)

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
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
