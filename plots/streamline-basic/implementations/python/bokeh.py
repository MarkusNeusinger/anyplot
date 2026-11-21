"""anyplot.ai
streamline-basic: Basic Streamline Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 95/100 | Updated: 2026-05-14
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColorBar, ColumnDataSource, HoverTool, LinearColorMapper
from bokeh.plotting import figure
from scipy.interpolate import RegularGridInterpolator
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]


def lerp_hex(c0, c1, t):
    """Linear blend between two hex colors."""
    a = [int(c0[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i : i + 2], 16) for i in (1, 3, 5)]
    r, g, bl = (round(p + (q - p) * t) for p, q in zip(a, b, strict=True))
    return f"#{r:02X}{g:02X}{bl:02X}"


# Imprint sequential ramp (single polarity) for the speed encoding
IMPRINT_SEQ256 = [lerp_hex("#009E73", "#4467A3", t / 255.0) for t in range(256)]

# Columns: set these to your table's column names
X = "X position (m)"  # role: x
Y = "Y position (m)"  # role: y
U = "Horizontal velocity (m/s)"  # role: u
V = "Vertical velocity (m/s)"  # role: v

# Data: replace this block with your own table, for example df = pd.read_csv("field.csv")
grid = np.linspace(-3, 3, 40)
gx, gy = np.meshgrid(grid, grid)
df = pd.DataFrame({X: gx.ravel(), Y: gy.ravel(), U: -gy.ravel(), V: gx.ravel()})  # vortex: u = -y, v = x

# Plot: reads only df and the constants above
field = df.dropna(subset=[X, Y])  # a row without a position cannot sit on the grid
u_table = field.pivot_table(index=Y, columns=X, values=U, dropna=False)
v_table = field.pivot_table(index=Y, columns=X, values=V, dropna=False).reindex_like(u_table)
xs_grid = u_table.columns.to_numpy(dtype=float)
ys_grid = u_table.index.to_numpy(dtype=float)
u_grid = u_table.to_numpy()
v_grid = v_table.to_numpy()
speed_grid = np.hypot(u_grid, v_grid)
SPEED = "Flow speed (m/s)"

u_interp = RegularGridInterpolator((ys_grid, xs_grid), u_grid, bounds_error=False, fill_value=np.nan)
v_interp = RegularGridInterpolator((ys_grid, xs_grid), v_grid, bounds_error=False, fill_value=np.nan)
speed_interp = RegularGridInterpolator((ys_grid, xs_grid), speed_grid, bounds_error=False, fill_value=np.nan)

x_lo, x_hi = xs_grid.min(), xs_grid.max()
y_lo, y_hi = ys_grid.min(), ys_grid.max()
span = min(x_hi - x_lo, y_hi - y_lo)
step = span / 120  # integration step
min_gap = span / 18  # a seed closer than this to an existing line would only retrace it


def direction(px, py):
    """Unit flow direction at a point, or None where the field is undefined or at rest."""
    u = u_interp([[py, px]])[0]
    v = v_interp([[py, px]])[0]
    norm = np.hypot(u, v)
    if np.isnan(norm) or norm < 1e-9:
        return None
    return np.array([u, v]) / norm


def trace(px, py, sign):
    """RK4 integration along (sign=1) or against (sign=-1) the flow until the edge of the domain."""
    pts = [(px, py)]
    for _ in range(int(2.2 * np.pi * max(x_hi, y_hi) / step)):
        k1 = direction(px, py)
        if k1 is None:
            break
        k2 = direction(px + sign * step / 2 * k1[0], py + sign * step / 2 * k1[1])
        k3 = direction(px + sign * step / 2 * k2[0], py + sign * step / 2 * k2[1]) if k2 is not None else None
        k4 = direction(px + sign * step * k3[0], py + sign * step * k3[1]) if k3 is not None else None
        if k4 is None:
            break
        px += sign * step / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
        py += sign * step / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
        if not (x_lo <= px <= x_hi and y_lo <= py <= y_hi):
            break
        pts.append((px, py))
        # closed orbit: back near the start after a full turn
        if len(pts) > 20 and np.hypot(px - pts[0][0], py - pts[0][1]) < step:
            break
    return pts


# Seeds on a coarse grid spanning the whole domain; skip seeds already covered by a traced line
seed_x = np.linspace(x_lo * 0.85, x_hi * 0.85, 9)
seed_y = np.linspace(y_lo * 0.85, y_hi * 0.85, 9)
lines = []
covered = np.empty((0, 2))
for sy in seed_y:
    for sx in seed_x:
        if len(covered) and np.min(np.hypot(covered[:, 0] - sx, covered[:, 1] - sy)) < min_gap:
            continue
        backward = trace(sx, sy, -1)
        forward = trace(sx, sy, 1)
        path = np.array(backward[::-1] + forward[1:])
        if len(path) < 10:
            continue
        speeds = speed_interp(path[:, ::-1])
        lines.append({"xs": path[:, 0], "ys": path[:, 1], "speed": float(np.nanmean(speeds))})
        covered = np.vstack([covered, path])

# Color: mean line speed through the Imprint sequential ramp
mapper = LinearColorMapper(palette=IMPRINT_SEQ256, low=0, high=float(np.nanmax(speed_grid)))
line_speeds = np.array([ln["speed"] for ln in lines])
colors = [IMPRINT_SEQ256[int(np.clip(s / mapper.high * 255, 0, 255))] for s in line_speeds]

# Direction arrow at the middle of each line, pointing with the flow
arrow_len = span / 38
tips_x, tips_y, w1_x, w1_y, w2_x, w2_y = [], [], [], [], [], []
for ln in lines:
    mid = len(ln["xs"]) // 2
    d = np.array([ln["xs"][mid + 1] - ln["xs"][mid - 1], ln["ys"][mid + 1] - ln["ys"][mid - 1]])
    d /= np.hypot(*d)
    tip = np.array([ln["xs"][mid], ln["ys"][mid]]) + d * arrow_len / 2
    normal = np.array([-d[1], d[0]])
    base = tip - d * arrow_len
    tips_x.append([tip[0], (base + normal * arrow_len * 0.45)[0], (base - normal * arrow_len * 0.45)[0]])
    tips_y.append([tip[1], (base + normal * arrow_len * 0.45)[1], (base - normal * arrow_len * 0.45)[1]])

# Figure: square canvas, equal data scales so circular flow stays circular
p = figure(
    width=2400,
    height=2400,
    title="streamline-basic · python · bokeh · anyplot.ai",
    x_axis_label=X,
    y_axis_label=Y,
    x_range=(x_lo - span * 0.03, x_hi + span * 0.03),
    y_range=(y_lo - span * 0.03, y_hi + span * 0.03),
    match_aspect=True,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=60,
)

# Style
p.title.text_font_size = "44pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "38pt"
p.yaxis.axis_label_text_font_size = "38pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "30pt"
p.yaxis.major_label_text_font_size = "30pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10
p.outline_line_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG

line_source = ColumnDataSource(
    {
        "xs": [ln["xs"] for ln in lines],
        "ys": [ln["ys"] for ln in lines],
        "color": colors,
        SPEED: [round(s, 3) for s in line_speeds],
    }
)
lines_glyph = p.multi_line("xs", "ys", source=line_source, line_color="color", line_width=7, line_alpha=0.95)
arrow_source = ColumnDataSource({"xs": tips_x, "ys": tips_y, "color": colors})
p.patches("xs", "ys", source=arrow_source, fill_color="color", line_color="color", line_width=1)

p.add_tools(HoverTool(renderers=[lines_glyph], tooltips=[(SPEED, f"@{{{SPEED}}}")]))

colorbar = ColorBar(
    color_mapper=mapper,
    title=SPEED,
    title_text_font_size="30pt",
    title_text_color=INK,
    major_label_text_font_size="28pt",
    major_label_text_color=INK_SOFT,
    background_fill_color=PAGE_BG,
    major_tick_line_color=INK_SOFT,
    bar_line_color=INK_SOFT,
    width=50,
    padding=20,
    title_standoff=20,
)
p.add_layout(colorbar, "right")

# Save HTML + PNG via headless Chrome
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
