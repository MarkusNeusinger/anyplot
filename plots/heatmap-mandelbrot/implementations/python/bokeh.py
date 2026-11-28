"""anyplot.ai
heatmap-mandelbrot: Mandelbrot Set Fractal Visualization
Library: bokeh 3.9.0 | Python 3.13.13
"""

import os
import sys


# Prevent self-import: this file is named bokeh.py, so Python's path search would
# find it before the installed bokeh package. Remove the script's own directory
# from sys.path so imports resolve to the installed package.
_own_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _own_dir]

import time
from itertools import pairwise
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import BasicTicker, ColorBar, LinearColorMapper, NumeralTickFormatter
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (all eight positions; this plot colors by a continuous ramp instead)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# imprint_seq, fields stops (colored cells fill the plot), low -> high
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.369, "#009E73"), (0.803, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#404C02"), (0.487, "#009E73"), (1.0, "#CDD9FF")]
)


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


# LinearColorMapper takes evenly spaced colors, so sample the stops at 256 even steps
ANYPLOT_SEQ256 = [ramp_color(SEQ_FIELDS, k / 255) for k in range(256)]

# Data: replace this block with your own parameters (generated shape: no table)
# Complex-plane window; y is padded so one unit is the same number of pixels on both
# axes of the 2400x2400 canvas (inner area ~2000px wide x ~2130px tall after the borders)
x_min, x_max = -2.5, 1.0
y_min, y_max = -1.865, 1.865
max_iter = 200
grid_w = 1400
grid_h = round(grid_w * (y_max - y_min) / (x_max - x_min))  # square pixels in the complex plane

real = np.linspace(x_min, x_max, grid_w)
imag = np.linspace(y_min, y_max, grid_h)
real_grid, imag_grid = np.meshgrid(real, imag)
c = real_grid + 1j * imag_grid

z = np.zeros_like(c, dtype=complex)
iteration_count = np.full(c.shape, np.nan)
escaped = np.zeros(c.shape, dtype=bool)

for i in range(max_iter):
    active = ~escaped
    z[active] = z[active] ** 2 + c[active]
    newly_escaped = active & (np.abs(z) > 2.0)
    # Smooth coloring: normalized iteration count eliminates discrete banding
    iteration_count[newly_escaped] = i + 1 - np.log2(np.log2(np.abs(z[newly_escaped])))
    escaped |= newly_escaped

# Plot: reads only the parameters and arrays above
# Clip low to the 5th percentile so the ramp spreads over the visible gradient;
# interior (never escaping, NaN) is drawn black by nan_color
low_val = float(np.nanpercentile(iteration_count, 5))
high_val = float(np.nanmax(iteration_count))

title = "heatmap-mandelbrot · python · bokeh · anyplot.ai"

# Square 2400x2400 canvas
W, H = 2400, 2400
p = figure(
    width=W,
    height=H,
    x_range=(x_min, x_max),
    y_range=(y_min, y_max),
    title=title,
    x_axis_label="Re(c)",
    y_axis_label="Im(c)",
    toolbar_location=None,
    tools="",
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=220,
)

# LinearColorMapper with 5th-percentile low clips the flat fast-escape floor,
# spreading the gradient evenly across the visible range; interior (NaN) → black
mapper = LinearColorMapper(palette=ANYPLOT_SEQ256, low=low_val, high=high_val, nan_color="#000000")

p.image(image=[iteration_count], x=x_min, y=y_min, dw=x_max - x_min, dh=y_max - y_min, color_mapper=mapper)

# Color bar
color_bar = ColorBar(
    color_mapper=mapper,
    ticker=BasicTicker(desired_num_ticks=8),
    formatter=NumeralTickFormatter(format="0"),
    label_standoff=20,
    width=55,
    title="Escape Iterations",
    title_text_font_size="34pt",
    title_text_color=INK,
    major_label_text_font_size="34pt",
    major_label_text_color=INK_SOFT,
    title_standoff=24,
    border_line_color=None,
    padding=16,
    background_fill_color=ELEVATED_BG,
)
p.add_layout(color_bar, "right")

# Style — canonical bokeh font sizes for 2400x2400 canvas
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
p.outline_line_color = INK_SOFT
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG

# Save HTML artifact (interactive catalog output)
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot via headless Chrome
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
# Pin the viewport exactly (headless Chrome reserves a phantom title bar) and paint the
# page in the theme color so no light edge shows through the canvas anti-aliasing
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.execute_script(
    "document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
