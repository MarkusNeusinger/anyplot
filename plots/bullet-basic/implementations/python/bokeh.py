""" anyplot.ai
bullet-basic: Basic Bullet Chart
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-27
"""

import os
import sys
import time
from pathlib import Path


# Prevent this script (named bokeh.py) from shadowing the installed bokeh package
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if p != "" and os.path.abspath(p) != _this_dir]

import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
# Grayscale qualitative bands, poor to good, in a steady light-to-dark progression per theme
BAND_COLORS = ["#8A8A8A", "#B8B8B8", "#DEDEDE"] if THEME == "light" else ["#484848", "#666666", "#858585"]

# Columns: set these to your table's column names
METRIC = "Metric"  # role: label
ACTUAL = "Actual"  # role: actual
TARGET = "Target"  # role: target
# One column per band, each holding that band's upper threshold
POOR = "Poor"  # role: ranges
SATISFACTORY = "Satisfactory"  # role: extra
GOOD = "Good"  # role: extra
BANDS = [POOR, SATISFACTORY, GOOD]

# Data: replace this block with your own table, for example df = pd.read_csv("kpis.csv")
# (one row per metric)
df = pd.DataFrame(
    {
        METRIC: ["Revenue ($K)", "Profit ($K)", "Orders", "Customers", "Satisfaction (/5)"],
        ACTUAL: [275, 85, 320, 1450, 4.2],
        TARGET: [250, 100, 350, 1200, 4.5],
        POOR: [150, 50, 200, 800, 3.0],
        SATISFACTORY: [225, 75, 300, 1100, 4.0],
        GOOD: [300, 100, 400, 1500, 5.0],
    }
)

# Plot: reads only df and the constants above
# Every metric is scaled to percent of its own top band so that all bullets share one axis
n = len(df)
top = df[BANDS].max(axis=1)
actual_pct = df[ACTUAL] / top * 100
target_pct = df[TARGET] / top * 100
y_pos = [n - 1 - i for i in range(n)]
bar_height = 0.75

source = ColumnDataSource(
    {
        "y": y_pos,
        "x": actual_pct / 2,
        "width": actual_pct,
        "height": [bar_height * 0.38] * n,
        "metric": df[METRIC],
        "actual": df[ACTUAL].map(lambda v: f"{v:g}"),
        "target": df[TARGET].map(lambda v: f"{v:g}"),
        "pct": actual_pct.map(lambda v: f"{v:.0f}%"),
    }
)

p = figure(
    width=3200,
    height=1800,
    x_range=Range1d(-26, 118),
    y_range=Range1d(-0.6, n - 0.3),
    title="bullet-basic · python · bokeh · anyplot.ai",
    x_axis_label="% of Maximum Range",
    toolbar_location=None,
    min_border_bottom=60,
    min_border_left=180,
    min_border_top=110,
    min_border_right=80,
)

# Chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.title.text_font_size = "50pt"
p.title.text_color = INK
p.title.align = "center"

p.xaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None
p.xaxis.ticker = [0, 20, 40, 60, 80, 100]

p.yaxis.visible = False
p.ygrid.grid_line_color = None
p.xgrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.15

# Qualitative bands: widest first so the narrower ones stay visible on top
bands = df[BANDS].div(top, axis=0) * 100
for j, band in reversed(list(enumerate(BANDS))):
    p.rect(
        x=bands[band] / 2,
        y=y_pos,
        width=bands[band],
        height=bar_height,
        color=BAND_COLORS[j],
        line_color=None,
        legend_label=band,
    )

# Measure bar, one color throughout
actual_renderer = p.rect(
    x="x", y="y", width="width", height="height", color=IMPRINT_PALETTE[0], line_color=None, source=source
)

# Target marker: thin line perpendicular to the bar
p.rect(x=target_pct, y=y_pos, width=0.7, height=bar_height * 0.6, color=INK, line_color=None, legend_label=TARGET)

p.add_tools(
    HoverTool(
        renderers=[actual_renderer],
        tooltips=[(METRIC, "@metric"), (ACTUAL, "@actual"), (TARGET, "@target"), ("% of maximum range", "@pct")],
    )
)

# Metric labels beside the bullets and the actual value in a column past the bands,
# clear of every target marker
for y, metric, value in zip(y_pos, df[METRIC], source.data["actual"], strict=True):
    p.add_layout(
        Label(
            x=-2,
            y=y,
            text=str(metric),
            text_font_size="30pt",
            text_color=INK,
            text_align="right",
            text_baseline="middle",
        )
    )
    p.add_layout(
        Label(
            x=102,
            y=y,
            text=value,
            text_font_size="30pt",
            text_color=INK,
            text_font_style="bold",
            text_align="left",
            text_baseline="middle",
            background_fill_color=PAGE_BG,
            background_fill_alpha=0.88,
            padding=4,
        )
    )

# Legend below the chart: the three bands and the target marker
legend = p.legend[0]
legend.items = [*reversed(legend.items[:-1]), legend.items[-1]]  # Poor, Satisfactory, Good, Target
legend.orientation = "horizontal"
legend.location = "center"
legend.label_text_font_size = "30pt"
legend.label_text_color = INK_SOFT
legend.glyph_height = 40
legend.glyph_width = 40
legend.label_standoff = 16
legend.spacing = 40
legend.padding = 20
legend.background_fill_color = PAGE_BG
legend.border_line_color = None
p.add_layout(legend, "below")

# Save: interactive HTML, then a headless-Chrome screenshot at the exact canvas size
output_file(f"plot-{THEME}.html")
save(p)

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
