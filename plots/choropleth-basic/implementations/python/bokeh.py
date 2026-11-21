"""anyplot.ai
choropleth-basic: Choropleth Map with Regional Coloring
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 73/100 | Updated: 2026-05-15
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColorBar, ColumnDataSource, LabelSet, LogColorMapper
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
NO_DATA = "#B9B8B0" if THEME == "light" else "#6E6D66"

# Imprint palette: first position is the brand green
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]


def _lerp_hex(c0, c1, t):
    r0, g0, b0 = (int(c0[i : i + 2], 16) for i in (1, 3, 5))
    r1, g1, b1 = (int(c1[i : i + 2], 16) for i in (1, 3, 5))
    r, g, b = (round(a + (b - a) * t) for a, b in ((r0, r1), (g0, g1), (b0, b1)))
    return f"#{r:02X}{g:02X}{b:02X}"


# imprint_seq: single-polarity ramp from brand green to blue
IMPRINT_SEQ = [_lerp_hex("#009E73", "#4467A3", t / 255.0) for t in range(256)]

# Columns: set these to your table's column names
STATE = "State"  # role: region_id
TILE_COL = "Tile column"  # role: extra
TILE_ROW = "Tile row"  # role: extra
DENSITY = "Population density (people per sq mile)"  # role: value

# Data: US states as a tile grid (column, row) with population density; replace with your own table
# DC is left without a value on purpose to show the no-data style.
df = pd.DataFrame(
    [
        ("AK", 0, 5, 1), ("HI", 0, 1, 226), ("WA", 1, 5, 117), ("OR", 1, 4, 44),
        ("CA", 0, 3, 253), ("NV", 1, 3, 28), ("ID", 2, 5, 23), ("MT", 3, 5, 8),
        ("WY", 3, 4, 6), ("UT", 2, 3, 40), ("AZ", 2, 2, 64), ("CO", 3, 3, 57),
        ("NM", 3, 2, 17), ("ND", 4, 5, 11), ("SD", 4, 4, 12), ("NE", 4, 3, 25),
        ("KS", 4, 2, 36), ("OK", 4, 1, 58), ("TX", 3, 1, 112), ("MN", 5, 5, 71),
        ("IA", 5, 4, 57), ("MO", 5, 3, 89), ("AR", 5, 2, 58), ("LA", 5, 1, 107),
        ("WI", 6, 5, 108), ("IL", 6, 4, 227), ("IN", 7, 4, 189), ("MI", 7, 5, 177),
        ("OH", 8, 4, 289), ("KY", 7, 3, 114), ("TN", 6, 3, 167), ("MS", 6, 2, 63),
        ("AL", 7, 2, 99), ("GA", 8, 2, 185), ("FL", 8, 1, 411), ("SC", 9, 2, 173),
        ("NC", 9, 3, 218), ("VA", 9, 4, 218), ("WV", 8, 3, 74), ("PA", 10, 4, 286),
        ("NY", 10, 5, 408), ("VT", 11, 5, 68), ("NH", 11, 4, 154), ("ME", 12, 5, 44),
        ("MA", 11, 3, 901), ("RI", 12, 3, 1061), ("CT", 11, 2, 733), ("NJ", 10, 3, 1263),
        ("DE", 10, 2, 508), ("MD", 9, 1, 636), ("DC", 10, 1, None),
    ],
    columns=[STATE, TILE_COL, TILE_ROW, DENSITY],
)  # fmt: skip
df[DENSITY] = df[DENSITY].astype(float)

# Plot: reads only df and the constants above
PITCH = 1.1  # tile spacing; tiles are 1.0 wide so a thin gap shows between neighbours
values = df[DENSITY]
low, high = values.min(), values.max()
color_mapper = LogColorMapper(palette=IMPRINT_SEQ, low=low, high=high, nan_color=NO_DATA)

# Fill color per tile, taken from the same log mapping the color bar uses
norm = (np.log10(values) - np.log10(low)) / (np.log10(high) - np.log10(low))
index = (norm * (len(IMPRINT_SEQ) - 1)).round()
fills = [NO_DATA if np.isnan(i) else IMPRINT_SEQ[int(i)] for i in index]
# Label ink: light text on dark fills, dark text on light fills (relative luminance)
label_ink = []
for fill in fills:
    r, g, b = (int(fill[k : k + 2], 16) / 255 for k in (1, 3, 5))
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    label_ink.append("#1A1A17" if luminance > 0.35 else "#FAF8F1")

source = ColumnDataSource(
    {
        "x": df[TILE_COL] * PITCH,
        "y": df[TILE_ROW] * PITCH,
        "fill": fills,
        "ink": label_ink,
        "label": df[STATE],
        "value": values,
    }
)

title = "choropleth-basic · python · bokeh · anyplot.ai"
p = figure(
    width=3200,
    height=1800,
    title=title,
    x_axis_location=None,
    y_axis_location=None,
    tools="",
    toolbar_location=None,
    x_range=(df[TILE_COL].min() * PITCH - 0.7, df[TILE_COL].max() * PITCH + 0.7),
    y_range=(df[TILE_ROW].min() * PITCH - 0.7, df[TILE_ROW].max() * PITCH + 0.7),
    min_border_top=110,
    min_border_bottom=60,
    min_border_left=60,
    min_border_right=60,
    background_fill_color=PAGE_BG,
    border_fill_color=PAGE_BG,
)
p.outline_line_color = None
p.outline_line_alpha = 0
p.grid.grid_line_color = None

p.rect(x="x", y="y", width=1.0, height=1.0, source=source, fill_color="fill", line_color=PAGE_BG, line_width=2)
p.add_layout(
    LabelSet(
        x="x",
        y="y",
        text="label",
        text_color="ink",
        source=source,
        text_align="center",
        text_baseline="middle",
        text_font_size="30pt",
        text_font_style="bold",
    )
)

p.title.text_font_size = "50pt"
p.title.text_color = INK
p.title.align = "center"

color_bar = ColorBar(
    color_mapper=color_mapper,
    width=60,
    height=1100,
    location="center",
    title=DENSITY,
    title_text_font_size="30pt",
    title_text_color=INK,
    major_label_text_font_size="28pt",
    major_label_text_color=INK_SOFT,
    title_standoff=24,
    padding=20,
    margin=30,
    background_fill_color=PAGE_BG,
    bar_line_color=INK_SOFT,
    major_tick_line_color=INK_SOFT,
)
p.add_layout(color_bar, "right")

# Save: interactive HTML, then a headless Chrome screenshot at the exact canvas size
W, H = 3200, 1800
html_path = Path(f"plot-{THEME}.html")
output_file(str(html_path))
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
driver.get(f"file://{html_path.resolve()}")
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
