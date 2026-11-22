""" anyplot.ai
parliament-basic: Parliament Seat Chart
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-22
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per party in data order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
PARTY = "Party"  # role: party
SEATS = "Seats"  # role: seats
COLOR = "Color"  # role: color

# Data: replace this block with your own table, for example df = pd.read_csv("chamber.csv")
df = pd.DataFrame(
    {
        PARTY: ["Harbor Union", "Ember League", "Quarry Alliance", "Meadow Circle", "Cinder Forum", "Willow Bloc"],
        SEATS: [42, 52, 85, 58, 67, 96],
        COLOR: ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"],  # Imprint positions 1-6
    }
)

# Plot: reads only df and the constants above
counts = df[SEATS].round().astype(int).to_numpy()
total = int(counts.sum())
majority = total // 2 + 1

# Concentric arcs: the seats per arc grow with its radius (largest-remainder rounding)
n_rows = 10
radii = 0.4 + 0.095 * np.arange(n_rows)
share = total * radii / radii.sum()
per_row = np.floor(share).astype(int)
order = np.argsort(share - per_row)[::-1]
per_row[order[: total - per_row.sum()]] += 1

# Every seat gets a position; sweeping the half circle from left to right makes each party one block
angle = np.concatenate([np.linspace(np.pi, 0, k) for k in per_row])
radius = np.repeat(radii, per_row)
sweep = np.lexsort((radius, -angle))
x = (radius * np.cos(angle))[sweep]
y = (radius * np.sin(angle))[sweep]
seats = ColumnDataSource({"x": x, "y": y, "color": np.repeat(df[COLOR].to_numpy(), counts)})

# Square data units: pixels per unit follows from the plot area and the vertical range
W, H = 3200, 1800
border = 40
y_lo, y_hi = -0.9, radii.max() + 0.15
units_px = (H - 110 - border) / (y_hi - y_lo)
half_width = (W - 2 * border) / units_px / 2

p = figure(
    width=W,
    height=H,
    title="parliament-basic · python · bokeh · anyplot.ai",
    tools="",
    toolbar_location=None,
    x_range=(-half_width, half_width),
    y_range=(y_lo, y_hi),
    min_border_top=110,
    min_border_bottom=border,
    min_border_left=border,
    min_border_right=border,
)
p.scatter(x="x", y="y", source=seats, color="color", size=36, line_color=PAGE_BG, line_width=2)

# Legend below the chamber: one colored seat per party with its name and seat count
slot = 0.72
for i, (party, count, color) in enumerate(zip(df[PARTY], counts, df[COLOR], strict=True)):
    lx = (i - (len(df) - 1) / 2) * slot
    p.scatter(x=[lx], y=[-0.5], color=color, size=36, line_color=PAGE_BG, line_width=2)
    p.text(
        x=[lx],
        y=[-0.58],
        text=[f"{party}\n{count} seats"],
        text_align="center",
        text_baseline="top",
        text_font_size="24pt",
        text_color=INK_SOFT,
    )

p.text(
    x=[0],
    y=[-0.12],
    text=[f"Majority threshold: {majority} of {total} seats"],
    text_align="center",
    text_font_size="26pt",
    text_font_style="bold",
    text_color=INK,
)

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.title.align = "center"
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_alpha = 0
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome via Selenium
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
try:
    driver.set_window_size(W, H)
    driver.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
    )
    driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
    time.sleep(3)  # let bokeh's JS render the canvas
    driver.save_screenshot(f"plot-{THEME}.png")
finally:
    driver.quit()
