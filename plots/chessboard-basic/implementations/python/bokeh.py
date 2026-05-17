""" anyplot.ai
chessboard-basic: Chess Board Grid Visualization
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-17
"""

import os
import time
from pathlib import Path

from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Chess board colors (light and dark squares)
LIGHT_SQUARE = "#F0D9B5"
DARK_SQUARE = "#B58863"

# Data - 8x8 chess board squares
columns = list("abcdefgh")
rows = list("12345678")

x_coords = []
y_coords = []
colors = []

for row_idx, _row in enumerate(rows):
    for col_idx, _col in enumerate(columns):
        x_coords.append(col_idx + 0.5)
        y_coords.append(row_idx + 0.5)
        if (row_idx + col_idx) % 2 == 0:
            colors.append(DARK_SQUARE)
        else:
            colors.append(LIGHT_SQUARE)

source = ColumnDataSource(data={"x": x_coords, "y": y_coords, "color": colors})

# Plot
p = figure(
    width=3600,
    height=3600,
    title="chessboard-basic · bokeh · anyplot.ai",
    x_range=(-0.1, 8.1),
    y_range=(-0.1, 8.1),
    tools="",
    toolbar_location=None,
)

p.rect(x="x", y="y", width=1, height=1, source=source, color="color", line_color=INK_SOFT, line_width=2)

# Style
p.title.text_font_size = "32pt"
p.title.text_color = INK
p.title.align = "center"

p.xaxis.ticker = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5]
p.xaxis.major_label_overrides = {0.5: "a", 1.5: "b", 2.5: "c", 3.5: "d", 4.5: "e", 5.5: "f", 6.5: "g", 7.5: "h"}
p.xaxis.major_label_text_font_size = "24pt"
p.xaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_label = "Column"
p.xaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.xaxis.axis_line_color = INK_SOFT

p.yaxis.ticker = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5]
p.yaxis.major_label_overrides = {0.5: "1", 1.5: "2", 2.5: "3", 3.5: "4", 4.5: "5", 5.5: "6", 6.5: "7", 7.5: "8"}
p.yaxis.major_label_text_font_size = "24pt"
p.yaxis.major_label_text_color = INK_SOFT
p.yaxis.axis_label = "Row"
p.yaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_color = INK
p.yaxis.axis_line_color = INK_SOFT

p.xgrid.visible = False
p.ygrid.visible = False

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT
p.outline_line_width = 3

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
W, H = 3600, 3600
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
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
