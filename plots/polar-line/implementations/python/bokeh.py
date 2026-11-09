"""anyplot.ai
polar-line: Polar Line Plot
Library: bokeh 3.10.1 | Python 3.14.9
Quality: pending | Updated: 2026-11-09
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
CYCLE = 24  # hours in one turn of the circle
SPOKES = 12  # radial grid lines, one every CYCLE / SPOKES hours
RADIUS_LABEL = "Wind speed (m/s)"  # what the radius measures, shared by every series

# Columns: set these to your table's column names
HOUR = "Hour of day"  # role: theta
DAYS = ["Day 1", "Day 2"]  # role: radius

# Data: replace this block with your own table, for example df = pd.read_csv("wind.csv")
np.random.seed(42)
hours = np.arange(24)
angle = hours * (2 * np.pi / 24)
base_pattern = 5 + 3 * np.sin(angle - np.pi / 2) + 2 * np.cos(2 * angle)
day1 = np.maximum(base_pattern + np.random.normal(0, 0.5, len(hours)), 0.5)
day2 = np.maximum(base_pattern * 0.8 + np.random.normal(0, 0.4, len(hours)), 0.5)
df = pd.DataFrame({HOUR: hours, DAYS[0]: day1, DAYS[1]: day2})

# Plot: reads only df and the constants above
title = "polar-line · python · bokeh · anyplot.ai"
title_size = f"{max(34, round(50 * (67 / len(title) if len(title) > 67 else 1.0)))}pt"

# Radial scale from the data: a 1-2-5 step giving at most six rings
r_peak = float(df[DAYS].max().max())
raw_step = r_peak / 6
magnitude = 10 ** np.floor(np.log10(raw_step))
step = next(m * magnitude for m in (1, 2, 5, 10) if m * magnitude >= raw_step)
rings = np.arange(step, r_peak + step * 0.999, step)
r_outer = rings[-1]
extent = r_outer * 1.22

p = figure(
    width=2400,
    height=2400,
    title=title,
    x_range=Range1d(-extent, extent),
    y_range=Range1d(-extent, extent),
    match_aspect=True,
    x_axis_type=None,
    y_axis_type=None,
    toolbar_location=None,
    min_border_top=110,
    min_border_bottom=50,
    min_border_left=50,
    min_border_right=50,
)

# Grid: concentric rings and radial spokes, clockwise from the top like a clock
circle = np.linspace(0, 2 * np.pi, 361)
for r in rings:
    p.line(r * np.sin(circle), r * np.cos(circle), line_color=INK, line_alpha=0.15, line_width=2)
spoke_angles = np.arange(SPOKES) * (2 * np.pi / SPOKES)
p.multi_line(
    xs=[[0, r_outer * np.sin(a)] for a in spoke_angles],
    ys=[[0, r_outer * np.cos(a)] for a in spoke_angles],
    line_color=INK,
    line_alpha=0.15,
    line_width=2,
)

# Angle labels just outside the outer ring
label_r = r_outer * 1.09
p.text(
    x=label_r * np.sin(spoke_angles),
    y=label_r * np.cos(spoke_angles),
    text=[f"{h:g}h" for h in np.arange(SPOKES) * CYCLE / SPOKES],
    text_align="center",
    text_baseline="middle",
    text_font_size="34pt",
    text_color=INK_SOFT,
)

# Radius labels along the spoke between 0h and the first spoke clockwise
label_angle = np.pi / SPOKES
p.text(
    x=rings * np.sin(label_angle),
    y=rings * np.cos(label_angle),
    text=[f"{r:g}" for r in rings],
    text_align="left",
    text_baseline="bottom",
    text_font_size="28pt",
    text_color=INK_SOFT,
    x_offset=8,
)
p.text(
    x=[0],
    y=[-extent * 0.97],
    text=[f"Radius: {RADIUS_LABEL}"],
    text_align="center",
    text_baseline="bottom",
    text_font_size="34pt",
    text_color=INK,
)

# Series: one closed loop per radius column in theta order, markers on the data points
rows = df.sort_values(HOUR)
theta = rows[HOUR].to_numpy(dtype=float) * (2 * np.pi / CYCLE)
for i, series in enumerate(DAYS):
    radius = rows[series].to_numpy(dtype=float)
    points = ColumnDataSource(
        {"x": radius * np.sin(theta), "y": radius * np.cos(theta), "hour": rows[HOUR], "speed": radius}
    )
    loop_theta = np.append(theta, theta[0])
    loop_radius = np.append(radius, radius[0])
    color = IMPRINT_PALETTE[i]
    p.line(
        loop_radius * np.sin(loop_theta),
        loop_radius * np.cos(loop_theta),
        line_color=color,
        line_width=5,
        line_alpha=0.95,
        legend_label=str(series),
    )
    markers = p.scatter(
        "x", "y", source=points, size=16, color=color, line_color=PAGE_BG, line_width=2, legend_label=str(series)
    )
    p.add_tools(
        HoverTool(
            renderers=[markers],
            tooltips=[("Series", str(series)), (HOUR, "@hour{0.[0]}"), (RADIUS_LABEL, "@speed{0.0}")],
        )
    )

# Style
p.title.text_font_size = title_size
p.title.align = "center"
p.title.text_color = INK
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.legend.location = "top_right"
p.legend.label_text_font_size = "34pt"
p.legend.label_text_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.9
p.legend.border_line_color = INK_SOFT
p.legend.glyph_width = 60
p.legend.glyph_height = 40
p.legend.padding = 20
p.legend.spacing = 12

# Save: interactive HTML, then a headless Chrome screenshot of it
output_file(f"plot-{THEME}.html", title=title)
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
# Paint the page itself in PAGE_BG so no white shows through the seam around the plot frame
driver.execute_script(
    "document.documentElement.style.background = arguments[0];"
    "document.body.style.background = arguments[0];"
    "document.body.style.margin = '0';",
    PAGE_BG,
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
