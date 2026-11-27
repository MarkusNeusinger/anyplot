"""anyplot.ai
bump-basic: Basic Bump Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-29
"""

import sys


# Remove the script's own directory so 'bokeh' resolves to the installed package,
# not this script file (bokeh.py would shadow the bokeh package otherwise).
if sys.path and sys.path[0]:
    sys.path = sys.path[1:]

import os
import time
from pathlib import Path

import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, FactorRange, FixedTicker, Label
from bokeh.plotting import figure
from bokeh.resources import INLINE
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — 8 hues, theme-independent
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Column constants
CONSTRUCTOR = "Constructor"  # role: entity
RACE = "Race"  # role: period
POSITION = "Championship Position"  # role: rank

# Data: replace this block with your own table, for example df = pd.read_csv("standings.csv")
# Formula 1 constructor standings over a 6-race stretch
standings = {
    "Red Bull Racing": [3, 2, 1, 1, 2, 1],
    "McLaren": [1, 1, 2, 3, 3, 4],
    "Ferrari": [5, 4, 4, 2, 1, 2],
    "Mercedes": [2, 3, 3, 4, 4, 3],
    "Aston Martin": [4, 5, 5, 5, 5, 5],
}
df = pd.DataFrame(
    [
        {CONSTRUCTOR: team, RACE: f"Race {i + 1}", POSITION: rank}
        for team, ranks in standings.items()
        for i, rank in enumerate(ranks)
    ]
)

# Plot
title_str = "F1 Constructor Standings · bump-basic · python · bokeh · anyplot.ai"
ratio = 67 / len(title_str) if len(title_str) > 67 else 1.0
title_fontsize = f"{max(34, round(50 * ratio))}pt"

races = list(df[RACE].unique())
ranks_used = sorted(df[POSITION].dropna().unique())

# 3200×1800 landscape; toolbar_location=None keeps the PNG at its exact height
p = figure(
    width=3200,
    height=1800,
    title=title_str,
    x_range=FactorRange(*races, range_padding=0.9, range_padding_units="absolute"),
    y_range=(max(ranks_used) + 0.8, min(ranks_used) - 0.6),  # inverted: rank 1 on top
    x_axis_label="Constructor Standings by Race",
    y_axis_label=POSITION,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=60,
)

for i, team in enumerate(df[CONSTRUCTOR].unique()):
    rows = df[df[CONSTRUCTOR] == team]
    source = ColumnDataSource(rows)
    color = IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)]
    p.line(x=RACE, y=POSITION, source=source, line_width=7, line_color=color)
    p.scatter(x=RACE, y=POSITION, source=source, size=30, color=color)
    p.add_layout(
        Label(
            x=len(races) - 0.5,  # categorical factors are centred at index + 0.5
            y=rows[POSITION].iloc[-1],
            text=team,
            text_font_size="28pt",
            text_color=color,
            text_font_style="bold",
            x_offset=36,
            y_offset=-12,
        )
    )

# Font sizes
p.title.text_font_size = title_fontsize
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"

# Theme-adaptive chrome
p.title.text_color = INK
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

# No spines or ticks; only a faint dashed guide per rank
for axis in (p.xaxis, p.yaxis):
    axis.axis_line_color = None
    axis.major_tick_line_color = None
    axis.minor_tick_line_color = None
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.15
p.ygrid.grid_line_dash = [6, 4]

# Whole-number ranks only, written as ordinals (1st, 2nd, 3rd, 4th ...)
p.yaxis.ticker = FixedTicker(ticks=ranks_used)
p.yaxis.major_label_overrides = {
    int(r): f"{int(r)}{'th' if 11 <= r % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(int(r % 10), 'th')}"
    for r in ranks_used
}

# Save interactive HTML with inline resources so headless Chrome renders offline
output_file(f"plot-{THEME}.html")
save(p, resources=INLINE)

# Screenshot via headless Chrome; CDP pins the viewport exactly to the canvas
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
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_script(
    "document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

# Pin the saved PNG to the exact target size
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.size != (W, H):
    canvas = Image.new("RGB", (W, H), PAGE_BG)
    canvas.paste(img, ((W - img.size[0]) // 2, (H - img.size[1]) // 2))
    canvas.save(f"plot-{THEME}.png")
