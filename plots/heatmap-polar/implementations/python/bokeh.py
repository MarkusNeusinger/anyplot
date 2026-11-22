"""anyplot.ai
heatmap-polar: Polar Heatmap for Cyclic Two-Dimensional Data
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-11-22
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColorBar, ColumnDataSource, Label, LinearColorMapper
from bokeh.plotting import figure
from bokeh.transform import transform as bk_transform
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
CELL_TEXT = "#1A1A17"  # sits on the green low-value cells, identical in both themes

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]


def lerp_hex(c0, c1, t):
    a = [int(c0[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b, strict=True))


# Imprint sequential ramp (single-sign data): green to blue
IMPRINT_SEQ256 = [lerp_hex("#009E73", "#4467A3", t / 255.0) for t in range(256)]

# Columns: set these to your table's column names
HOUR = "Hour of day"  # role: angular
DAY = "Day of week"  # role: radial
VISITS = "Hourly visits"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("traffic.csv")
np.random.seed(42)
day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
rows = []
for d, day in enumerate(day_names):
    for h in range(24):
        if d < 5:
            base = 100 + 820 * np.exp(-0.5 * ((h - 9) / 1.5) ** 2) + 640 * np.exp(-0.5 * ((h - 20) / 2.0) ** 2)
        else:
            base = 80 + 510 * np.exp(-0.5 * ((h - 14) / 3.0) ** 2)
        rows.append((h, day, max(20.0, base + np.random.normal(0, 25))))
df = pd.DataFrame(rows, columns=[HOUR, DAY, VISITS])

# Plot
days = list(df[DAY].unique())
hours = sorted(df[HOUR].unique())
n_days, n_hours = len(days), len(hours)
hour_idx = df[HOUR].map({h: i for i, h in enumerate(hours)})
day_idx = df[DAY].map({d: i for i, d in enumerate(days)})

min_r = 0.28
max_r = 1.05
ring_width = (max_r - min_r) / n_days
gap = 0.004
quarter_turn = np.pi / 2  # midnight at the top, hours run clockwise

source = ColumnDataSource(
    {
        "inner_radius": min_r + day_idx * ring_width + gap,
        "outer_radius": min_r + (day_idx + 1) * ring_width - gap,
        "start_angle": quarter_turn - 2 * np.pi * hour_idx / n_hours,
        "end_angle": quarter_turn - 2 * np.pi * (hour_idx + 1) / n_hours,
        VISITS: df[VISITS],
    }
)

color_mapper = LinearColorMapper(palette=IMPRINT_SEQ256, low=df[VISITS].min(), high=df[VISITS].max())

W, H = 2400, 2400
lim = max_r * 1.4
p = figure(
    width=W,
    height=H,
    x_range=(-lim, lim),
    y_range=(-lim, lim),
    match_aspect=True,
    title="Website Traffic · heatmap-polar · python · bokeh · anyplot.ai",
    toolbar_location=None,
    min_border_left=40,
    min_border_right=40,
    min_border_top=70,
    min_border_bottom=40,
)

p.annular_wedge(
    x=0,
    y=0,
    inner_radius="inner_radius",
    outer_radius="outer_radius",
    start_angle="start_angle",
    end_angle="end_angle",
    direction="clock",
    fill_color=bk_transform(VISITS, color_mapper),
    line_color=PAGE_BG,
    line_width=0.6,
    source=source,
)

# Subordinate spokes every 3 hours, neutral so they show on both themes
label_step = max(1, n_hours // 8)
for i in range(0, n_hours, label_step):
    angle = quarter_turn - 2 * np.pi * i / n_hours
    p.segment(
        x0=[min_r * np.cos(angle)],
        y0=[min_r * np.sin(angle)],
        x1=[max_r * np.cos(angle)],
        y1=[max_r * np.sin(angle)],
        line_color=INK_SOFT,
        line_width=1.5,
        line_alpha=0.45,
    )

# Hour labels outside the ring
for i in range(0, n_hours, label_step):
    angle = quarter_turn - 2 * np.pi * i / n_hours
    hour = hours[i]
    p.add_layout(
        Label(
            x=1.2 * np.cos(angle),
            y=1.2 * np.sin(angle),
            text=f"{hour % 12 or 12}{'am' if hour < 12 else 'pm'}",
            text_align="center",
            text_baseline="middle",
            text_font_size="34pt",
            text_color=INK_SOFT,
        )
    )

# Ring labels at the centre of the first (midnight) cell of each ring
cell_angle = quarter_turn - np.pi / n_hours
for d, day in enumerate(days):
    mid_r = min_r + (d + 0.5) * ring_width
    p.add_layout(
        Label(
            x=mid_r * np.cos(cell_angle),
            y=mid_r * np.sin(cell_angle),
            text=str(day),
            text_align="center",
            text_baseline="middle",
            text_font_size="26pt",
            text_font_style="bold",
            text_color=CELL_TEXT,
        )
    )

color_bar = ColorBar(
    color_mapper=color_mapper,
    width=50,
    padding=20,
    location=(0, 0),
    title=VISITS,
    title_text_font_size="34pt",
    title_text_color=INK,
    major_label_text_font_size="30pt",
    major_label_text_color=INK_SOFT,
    background_fill_color=PAGE_BG,
    bar_line_color=None,
)
p.add_layout(color_bar, "right")

# Chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.title.text_font_size = "44pt"
p.title.text_color = INK
p.title.text_font_style = "bold"
p.title.align = "center"
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None

# Save HTML + PNG
output_file(f"plot-{THEME}.html")
save(p)

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
