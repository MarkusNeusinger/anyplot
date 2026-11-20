"""anyplot.ai
polar-scatter: Polar Scatter Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Legend, LegendItem
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
RINGS = 8  # target number of radial gridlines
COMPASS = {0: "E", 45: "NE", 90: "N", 135: "NW", 180: "W", 225: "SW", 270: "S", 315: "SE"}

# Columns: set these to your table's column names
DIRECTION = "Wind direction (°)"  # role: theta
SPEED = "Wind speed (m/s)"  # role: radius
PERIOD = "Time of day"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("wind.csv")
np.random.seed(42)
morning_angles = np.random.normal(45, 30, 50) % 360
morning_speeds = np.random.gamma(3, 3, 50) + 5
afternoon_angles = np.random.normal(225, 35, 45) % 360
afternoon_speeds = np.random.gamma(2.5, 4, 45) + 3
evening_angles = np.random.uniform(0, 360, 25)
evening_speeds = np.random.gamma(2, 2, 25) + 2
df = pd.DataFrame(
    {
        DIRECTION: np.concatenate([morning_angles, afternoon_angles, evening_angles]),
        SPEED: np.concatenate([morning_speeds, afternoon_speeds, evening_speeds]),
        PERIOD: ["Morning"] * 50 + ["Afternoon"] * 45 + ["Evening"] * 25,
    }
)

# Plot: reads only df and the constants above
# Polar to Cartesian (bokeh has no native polar axes)
theta = np.radians(df[DIRECTION])
df["x"] = df[SPEED] * np.cos(theta)
df["y"] = df[SPEED] * np.sin(theta)

raw_step = df[SPEED].max() / RINGS
magnitude = 10 ** np.floor(np.log10(raw_step))
step = next(m * magnitude for m in (1, 2, 5, 10) if m * magnitude >= raw_step)
rim = np.ceil(df[SPEED].max() / step) * step
label_r = rim * 1.1
span = rim * 1.28

W = H = 2400
p = figure(
    width=W,
    height=H,
    title="polar-scatter · python · bokeh · anyplot.ai",
    x_range=(-span, span),
    y_range=(-span, span),
    match_aspect=True,
    tools="",
    toolbar_location=None,
    min_border_left=40,
    min_border_right=40,
    min_border_bottom=40,
    min_border_top=110,
)

# Radial gridlines (circles) with radius labels along the sparse SE spoke
ring = np.linspace(0, 2 * np.pi, 200)
for r in np.arange(step, rim + step / 2, step):
    p.line(r * np.cos(ring), r * np.sin(ring), line_color=INK_SOFT, line_width=2, line_alpha=0.2)
    p.text(
        [r * np.cos(-np.pi / 4) + rim * 0.01],
        [r * np.sin(-np.pi / 4) - rim * 0.01],
        text=[f"{r:g}"],
        text_font_size="24pt",
        text_color=INK_SOFT,
        text_baseline="top",
    )

# Angular spokes every 30°
for angle in range(0, 360, 30):
    rad = np.radians(angle)
    p.line([0, rim * np.cos(rad)], [0, rim * np.sin(rad)], line_color=INK_SOFT, line_width=2, line_alpha=0.2)

# Compass labels
for angle, name in COMPASS.items():
    rad = np.radians(angle)
    cardinal = angle % 90 == 0
    p.text(
        [label_r * np.cos(rad)],
        [label_r * np.sin(rad)],
        text=[name],
        text_font_size="32pt" if cardinal else "26pt",
        text_font_style="bold" if cardinal else "normal",
        text_color=INK if cardinal else INK_SOFT,
        text_align="center",
        text_baseline="middle",
    )

# Radius axis title
p.text(
    [0],
    [-span * 0.97],
    text=[SPEED],
    text_font_size="28pt",
    text_color=INK_SOFT,
    text_align="center",
    text_baseline="bottom",
)

# One scatter renderer per time of day, in palette order
legend_items = []
renderers = []
for i, period in enumerate(df[PERIOD].unique()):
    source = ColumnDataSource(df[df[PERIOD] == period])
    r = p.scatter(
        "x", "y", source=source, size=30, color=IMPRINT_PALETTE[i], alpha=0.7, line_color=PAGE_BG, line_width=2
    )
    renderers.append(r)
    legend_items.append(LegendItem(label=str(period), renderers=[r]))

p.add_tools(
    HoverTool(
        renderers=renderers,
        tooltips=[(DIRECTION, f"@{{{DIRECTION}}}{{0.0}}"), (SPEED, f"@{{{SPEED}}}{{0.0}}"), (PERIOD, f"@{{{PERIOD}}}")],
    )
)

legend = Legend(
    items=legend_items,
    title=PERIOD,
    location="top_left",
    label_text_font_size="26pt",
    label_text_color=INK_SOFT,
    title_text_font_size="26pt",
    title_text_color=INK,
    spacing=12,
    glyph_height=30,
    glyph_width=30,
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.9,
    border_line_color=INK_SOFT,
    padding=18,
    margin=30,
    border_line_width=2,
)
p.add_layout(legend, "center")

# Style
p.title.text_font_size = "44pt"
p.title.text_color = INK
p.title.align = "center"
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False

# Save HTML and screenshot with headless Chrome
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
