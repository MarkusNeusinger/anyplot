"""anyplot.ai
heatmap-basic: Basic Heatmap
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-28
"""

import math
import os
import time
from itertools import pairwise
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import BasicTicker, ColumnDataSource, HoverTool, LabelSet
from bokeh.plotting import figure
from bokeh.transform import linear_cmap
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

# Imprint diverging ramp for fields (colored cells that fill the plot): red -> page color -> blue
DIV_FIELDS = [(0.0, "#AE3030"), (0.5, PAGE_BG), (1.0, "#4467A3")]


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    if not math.isfinite(t):
        return "none"  # a missing value draws nothing, never the low end
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


IMPRINT_DIV256 = [ramp_color(DIV_FIELDS, k / 255) for k in range(256)]

# Columns: set these to your table's column names
MONTH = "Month (2024)"  # role: x
CITY = "City"  # role: y
ANOMALY = "Anomaly (°C)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("anomalies.csv")
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
cities = ["Oslo", "Berlin", "Madrid", "Cairo", "Mumbai", "Tokyo", "Sydney"]
seasonal = np.sin(np.linspace(-np.pi / 2, 3 * np.pi / 2, len(months)))
offsets = {
    "Oslo": seasonal * 1.5 - 0.3,
    "Berlin": seasonal * 1.5 - 0.3,
    "Madrid": seasonal * 1.2 + 0.4,
    "Cairo": seasonal * 1.2 + 0.4,
    "Mumbai": np.full(len(months), 0.8),
    "Tokyo": seasonal * 0.7,
    "Sydney": -seasonal * 0.9,
}
noise = np.random.randn(len(cities), len(months)) * 0.6
anomalies = np.round(noise + np.array([offsets[city] for city in cities]), 1)
df = pd.DataFrame({MONTH: months * len(cities), CITY: np.repeat(cities, len(months)), ANOMALY: anomalies.ravel()})

# Plot: reads only df and the constants above
limit = df[ANOMALY].abs().max()
df["label"] = df[ANOMALY].map(lambda v: f"{v:+.1f}")


def luminance(hex_color):
    """Approximate relative luminance (0 to 1) of a #RRGGBB color."""
    if not hex_color.startswith("#"):
        return 1.0  # an undrawn cell has the page behind it
    r, g, b = (int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


# Label ink follows the fill it sits on: light ink on dark fills, dark ink on light fills
fills = [ramp_color(DIV_FIELDS, (v + limit) / (2 * limit)) for v in df[ANOMALY]]
df["text_color"] = ["#F0EFE8" if luminance(f) < 0.5 else "#1A1A17" for f in fills]
source = ColumnDataSource(df)
cmap = linear_cmap(ANOMALY, IMPRINT_DIV256, low=-limit, high=limit)

p = figure(
    width=2400,
    height=2400,
    x_range=list(df[MONTH].dropna().unique()),
    y_range=list(reversed(df[CITY].dropna().unique())),
    title="heatmap-basic · python · bokeh · anyplot.ai",
    x_axis_label=MONTH,
    y_axis_label=CITY,
    toolbar_location=None,
    tools="",
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=300,
)

r = p.rect(x=MONTH, y=CITY, width=1, height=1, source=source, fill_color=cmap, line_color=PAGE_BG, line_width=2)

p.add_layout(
    LabelSet(
        x=MONTH,
        y=CITY,
        text="label",
        text_color="text_color",
        source=source,
        text_align="center",
        text_baseline="middle",
        text_font_size="28pt",
    )
)

color_bar = r.construct_color_bar(
    width=50,
    ticker=BasicTicker(desired_num_ticks=10),
    label_standoff=16,
    major_label_text_font_size="34pt",
    major_label_text_color=INK_SOFT,
    border_line_color=None,
    padding=20,
    title=ANOMALY,
    title_text_font_size="34pt",
    title_text_color=INK,
    title_standoff=20,
    background_fill_color=PAGE_BG,
)
p.add_layout(color_bar, "right")

p.add_tools(
    HoverTool(
        tooltips=[(CITY, f"@{{{CITY}}}"), (MONTH, f"@{{{MONTH}}}"), (ANOMALY, f"@{{{ANOMALY}}}{{+0.0}}")], renderers=[r]
    )
)

# Style
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.title.text_font_size = "50pt"
p.title.text_color = INK

p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK

p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

p.xaxis.axis_line_color = None
p.yaxis.axis_line_color = None
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None

# Save interactive HTML, then screenshot it with headless Chrome
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
driver.execute_script(
    "document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
