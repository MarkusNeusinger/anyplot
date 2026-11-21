""" anyplot.ai
bar-3d-categorical: 3D Bar Chart for Categorical Comparison
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 79/100 | Updated: 2026-11-21
"""

import os
import sys


# Prevent this file (bokeh.py) from shadowing the installed bokeh package
_this_dir = os.path.dirname(os.path.abspath(__file__))
if _this_dir in sys.path:
    sys.path.remove(_this_dir)

import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Label
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
PRODUCT = "Product category"  # role: x_category
QUARTER = "Quarter"  # role: y_category
SALES = "Sales (k units)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("sales.csv")
df = pd.DataFrame(
    {
        PRODUCT: np.repeat(["Electronics", "Apparel", "Food & Bev", "Books", "Sports"], 4),
        QUARTER: ["Q1", "Q2", "Q3", "Q4"] * 5,
        SALES: [118, 92, 105, 134, 72, 88, 78, 65, 60, 68, 74, 58, 42, 38, 44, 52, 85, 76, 92, 80],
    }
)

# Plot: reads only df and the constants above
table = df.pivot_table(index=PRODUCT, columns=QUARTER, values=SALES, sort=False).astype(float)
products = list(table.index)
quarters = list(table.columns)
n_prod, n_qtr = len(products), len(quarters)
v_max = np.nanmax(table.to_numpy())

H_SCALE = 2.5  # height of the tallest bar in projected coordinate units
DX = 0.45  # oblique x-offset per depth unit
DY = 0.52  # oblique y-offset per depth unit
bar_w = 0.72
gap = (1.0 - bar_w) / 2.0


def project(x, y, z):
    return x + y * DX, z + y * DY


def hex_darken(hex_color, f=0.60):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"#{int(r * f):02x}{int(g * f):02x}{int(b * f):02x}"


def hex_lighten(hex_color, f=1.35):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"#{min(255, int(r * f)):02x}{min(255, int(g * f)):02x}{min(255, int(b * f)):02x}"


# Base-plane grid lines as thin quads
grid_thick = 0.012
grid_xs, grid_ys = [], []
for j in range(n_qtr + 1):
    quad = [project(0, j, 0), project(n_prod, j, 0), project(n_prod, j + grid_thick, 0), project(0, j + grid_thick, 0)]
    grid_xs.append([c[0] for c in quad])
    grid_ys.append([c[1] for c in quad])
for i in range(n_prod + 1):
    quad = [project(i, 0, 0), project(i, n_qtr, 0), project(i + grid_thick, n_qtr, 0), project(i + grid_thick, 0, 0)]
    grid_xs.append([c[0] for c in quad])
    grid_ys.append([c[1] for c in quad])

# Bar patches: painter's algorithm, back (large j) to front (small j)
bar_xs, bar_ys, bar_cs = [], [], []
value_labels = []


def add_patch(corners, color):
    bar_xs.append([project(*c)[0] for c in corners])
    bar_ys.append([project(*c)[1] for c in corners])
    bar_cs.append(color)


for j in range(n_qtr - 1, -1, -1):
    color = IMPRINT_PALETTE[j]
    for i in range(n_prod):
        v = table.iloc[i, j]
        if np.isnan(v):
            continue
        h = v / v_max * H_SCALE
        x0, x1 = i + gap, i + gap + bar_w
        y0, y1 = j + gap, j + gap + bar_w
        add_patch([(x1, y0, 0), (x1, y1, 0), (x1, y1, h), (x1, y0, h)], hex_darken(color))  # side
        add_patch([(x0, y0, 0), (x1, y0, 0), (x1, y0, h), (x0, y0, h)], color)  # front
        add_patch([(x0, y0, h), (x1, y0, h), (x1, y1, h), (x0, y1, h)], hex_lighten(color))  # top
        lx, ly = project(i + gap + bar_w / 2, j + gap + bar_w / 2, h)
        value_labels.append((lx, ly, f"{v:g}"))

# Value-axis ticks at a round step
raw_step = v_max / 4
mag = 10 ** np.floor(np.log10(raw_step))
step = min((1, 2, 5, 10), key=lambda m: abs(m * mag - raw_step)) * mag
ticks = np.arange(step, v_max, step)

# Figure ranges derived from the projected scene
x_left = -1.9
x_right = n_prod + n_qtr * DX + 1.1
y_bottom = -1.0
y_top = H_SCALE + n_qtr * DY + 0.45

p = figure(
    width=3200,
    height=1800,
    title="Retail Sales by Product & Quarter  ·  bar-3d-categorical · python · bokeh · anyplot.ai",
    x_range=(x_left, x_right),
    y_range=(y_bottom, y_top),
    toolbar_location=None,
    min_border_left=20,
    min_border_right=20,
    min_border_top=20,
    min_border_bottom=20,
)

# Base-plane grid behind the bars
p.patches(grid_xs, grid_ys, color=INK, alpha=0.15 if THEME == "light" else 0.18, line_color=None)

# Bars
src_bars = ColumnDataSource({"xs": bar_xs, "ys": bar_ys, "cs": bar_cs})
p.patches("xs", "ys", source=src_bars, color="cs", line_color=PAGE_BG, line_width=1.5, alpha=0.95)

# Value labels on top of each bar
for lx, ly, text in value_labels:
    p.add_layout(
        Label(
            x=lx,
            y=ly + 0.06,
            text=text,
            text_align="center",
            text_baseline="bottom",
            text_color=INK,
            text_font_size="24pt",
            text_font_style="bold",
            background_fill_color=PAGE_BG,
            background_fill_alpha=0.75,
        )
    )

# Value axis line, ticks and labels
ax_x0, ax_y0 = project(0, 0, 0)
ax_x1, ax_y1 = project(0, 0, H_SCALE)
p.line([ax_x0, ax_x1], [ax_y0, ax_y1], line_color=INK_SOFT, line_width=3)
for v_tick in ticks:
    tx, ty = project(0, 0, v_tick / v_max * H_SCALE)
    p.line([tx - 0.12, tx], [ty, ty], line_color=INK_SOFT, line_width=3)
    p.add_layout(
        Label(
            x=tx - 0.18,
            y=ty,
            text=f"{v_tick:g}",
            text_align="right",
            text_baseline="middle",
            text_color=INK_SOFT,
            text_font_size="30pt",
        )
    )

# Value axis title, rotated
p.add_layout(
    Label(
        x=x_left + 0.25,
        y=project(0, 0, H_SCALE / 2)[1],
        text=SALES,
        angle=np.pi / 2,
        text_align="center",
        text_baseline="middle",
        text_color=INK,
        text_font_size="36pt",
    )
)

# Product labels along the front edge
for i, prod in enumerate(products):
    px, py = project(i + 0.5, 0, 0)
    p.add_layout(
        Label(
            x=px,
            y=py - 0.2,
            text=prod,
            text_align="center",
            text_baseline="top",
            text_color=INK_SOFT,
            text_font_size="30pt",
        )
    )
px, py = project(n_prod / 2, 0, 0)
p.add_layout(
    Label(
        x=px, y=py - 0.62, text=PRODUCT, text_align="center", text_baseline="top", text_color=INK, text_font_size="36pt"
    )
)

# Quarter labels along the depth axis, colored per series
for j, qtr in enumerate(quarters):
    px, py = project(n_prod + 0.25, j + 0.5, 0)
    p.add_layout(
        Label(
            x=px,
            y=py,
            text=str(qtr),
            text_align="left",
            text_baseline="middle",
            text_color=IMPRINT_PALETTE[j],
            text_font_size="34pt",
            text_font_style="bold",
        )
    )
px, py = project(n_prod + 0.25, n_qtr + 0.15, 0)
p.add_layout(
    Label(x=px, y=py, text=QUARTER, text_align="left", text_baseline="bottom", text_color=INK, text_font_size="36pt")
)

# Theme chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.title.text_color = INK
p.title.text_font_size = f"{round(50 * 67 / len(p.title.text))}pt"
p.title.text_font_style = "normal"
p.title.align = "center"

p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

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
