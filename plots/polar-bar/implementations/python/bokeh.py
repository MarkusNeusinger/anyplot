"""anyplot.ai
polar-bar: Polar Bar Chart (Wind Rose)
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-13
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Label, Title
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per direction in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DIRECTION = "Direction"  # role: direction
FREQUENCY = "Frequency (%)"  # role: frequency

# Data: replace this block with your own table, for example df = pd.read_csv("wind.csv")
# Simulated wind pattern: prevailing winds from SW and W
df = pd.DataFrame({DIRECTION: ["N", "NE", "E", "SE", "S", "SW", "W", "NW"], FREQUENCY: [12, 8, 10, 6, 9, 18, 22, 14]})

# Plot: reads only df and the constants above
n_dirs = len(df)
max_freq = df[FREQUENCY].max()
BAR_SCALE = 0.75  # longest bar reaches this share of the unit plot radius

# Compass angles: 0° = North, clockwise. Bokeh measures counterclockwise from East.
compass = np.linspace(0, 2 * np.pi, n_dirs, endpoint=False)
centers = np.pi / 2 - compass
half_width = np.pi / n_dirs

source = ColumnDataSource(
    data={
        "x": [0] * n_dirs,
        "y": [0] * n_dirs,
        "radius": (df[FREQUENCY] / max_freq * BAR_SCALE).tolist(),
        "start_angle": (centers - half_width).tolist(),
        "end_angle": (centers + half_width).tolist(),
        "color": [IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i in range(n_dirs)],
        DIRECTION: df[DIRECTION].tolist(),
        FREQUENCY: df[FREQUENCY].tolist(),
    }
)

# Square canvas for a polar plot
SIZE = 2400
p = figure(
    width=SIZE,
    height=SIZE,
    x_range=(-1.05, 1.05),
    y_range=(-1.05, 1.05),
    tools="",
    toolbar_location=None,
    min_border_top=110,
    min_border_bottom=40,
    min_border_left=40,
    min_border_right=40,
)

# Theme-adaptive styling
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title = Title(text="polar-bar · python · bokeh · anyplot.ai", text_font_size="40pt", text_color=INK, align="center")

# Remove axes and grid for polar appearance
p.axis.visible = False
p.grid.visible = False

# Concentric reference circles at thirds of the longest bar, plus the outer rim
circle_radii = [BAR_SCALE * f for f in (1 / 3, 2 / 3, 1)]
for r in circle_radii:
    p.circle(x=0, y=0, radius=r, fill_color=None, line_color=INK_SOFT, line_width=2, line_dash="dashed", line_alpha=0.3)
p.circle(x=0, y=0, radius=0.85, fill_color=None, line_color=INK_SOFT, line_width=2, line_alpha=0.5)

# Radial guide lines for each direction
for angle in centers:
    p.line([0, np.cos(angle) * 0.85], [0, np.sin(angle) * 0.85], line_color=INK_SOFT, line_width=1.5, line_alpha=0.3)

# Polar bars
p.wedge(
    x="x",
    y="y",
    radius="radius",
    start_angle="start_angle",
    end_angle="end_angle",
    fill_color="color",
    fill_alpha=0.85,
    line_color=INK_SOFT,
    line_width=3,
    source=source,
)

# Direction labels at the rim
LABEL_RADIUS = 0.93
for angle, direction in zip(centers, df[DIRECTION], strict=True):
    p.add_layout(
        Label(
            x=np.cos(angle) * LABEL_RADIUS,
            y=np.sin(angle) * LABEL_RADIUS,
            text=str(direction),
            text_font_size="30pt",
            text_color=INK,
            text_align="center",
            text_baseline="middle",
        )
    )

# Frequency scale labels at the reference circles
for r in circle_radii:
    p.add_layout(
        Label(
            x=0.03,
            y=r + 0.015,
            text=f"{r / BAR_SCALE * max_freq:.0f}",
            text_font_size="22pt",
            text_color=INK_SOFT,
            text_align="left",
            text_baseline="bottom",
        )
    )
p.add_layout(
    Label(
        x=0.03,
        y=BAR_SCALE + 0.055,
        text=FREQUENCY,
        text_font_size="22pt",
        text_color=INK_SOFT,
        text_align="left",
        text_baseline="bottom",
    )
)

# Save as HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={SIZE},{SIZE}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.set_window_size(SIZE, SIZE)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": SIZE, "height": SIZE, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)  # let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
