"""anyplot.ai
dashboard-synchronized-crosshair: Synchronized Multi-Chart Dashboard
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-05-23
"""

import base64
import os
import sys
import time
from pathlib import Path


# Prevent this file (bokeh.py) from shadowing the installed bokeh package.
# Python inserts the script's directory as sys.path[0]; remove it so that
# 'import bokeh' resolves to the package, not this script.
_here = str(Path(__file__).resolve().parent)
sys.path = [p for p in sys.path if Path(p).resolve() != Path(_here)]

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, CrosshairTool, HoverTool
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# anyplot palette — assigned across the three metric series
C_PRICE = "#009E73"  # green  (position 1)
C_VOLUME = "#9418DB"  # purple (position 2)
C_RSI = "#16B8F3"  # sky blue (position 4)
C_OVERBOUGHT = "#B71D27"  # red — semantic: danger / sell zone

# Data — stock data over 200 trading days
np.random.seed(42)
n_points = 200
dates = pd.date_range("2024-01-01", periods=n_points, freq="B")

price_changes = np.random.randn(n_points) * 2 + 0.05
price = 100 + np.cumsum(price_changes)

volume = np.abs(price_changes) * 1e6 + np.random.uniform(1e6, 3e6, n_points)

rsi = 50 + np.cumsum(np.random.randn(n_points) * 3)
rsi = np.clip(rsi, 20, 80)

source = ColumnDataSource(
    data={"date": dates, "price": price, "volume": volume / 1e6, "rsi": rsi, "date_str": dates.strftime("%Y-%m-%d")}
)

# Canvas: landscape 3200 × 1800 — three charts, heights sum to 1800
W, H = 3200, 1800

crosshair_opts = {"dimensions": "height", "line_color": INK_SOFT, "line_alpha": 0.85, "line_width": 2}
common_opts = {"width": W, "toolbar_location": None, "x_axis_type": "datetime", "min_border_left": 180, "min_border_right": 60}

# Chart 1: Price
p1 = figure(
    **common_opts,
    height=600,
    title="dashboard-synchronized-crosshair · python · bokeh · anyplot.ai",
    y_axis_label="Price ($)",
    min_border_top=110,
    min_border_bottom=20,
)
p1.line("date", "price", source=source, line_width=3, color=C_PRICE, legend_label="Price ($)")
p1.add_tools(CrosshairTool(**crosshair_opts))
p1.add_tools(HoverTool(tooltips=[("Date", "@date_str"), ("Price", "$@price{0.00}")], mode="vline"))

# Chart 2: Volume
p2 = figure(
    **common_opts, height=540, y_axis_label="Volume (M)", x_range=p1.x_range, min_border_top=30, min_border_bottom=20
)
p2.vbar(
    "date",
    top="volume",
    source=source,
    width=60 * 60 * 1000 * 18,
    color=C_VOLUME,
    alpha=0.75,
    legend_label="Volume (M)",
)
p2.add_tools(CrosshairTool(**crosshair_opts))
p2.add_tools(HoverTool(tooltips=[("Date", "@date_str"), ("Volume", "@volume{0.00}M")], mode="vline"))

# Chart 3: RSI with overbought / oversold reference lines
p3 = figure(
    **common_opts,
    height=660,
    y_axis_label="RSI",
    x_axis_label="Date",
    x_range=p1.x_range,
    min_border_top=30,
    min_border_bottom=160,
)
p3.line("date", "rsi", source=source, line_width=3, color=C_RSI, legend_label="RSI")
p3.line(
    dates,
    [70] * n_points,
    line_dash="dashed",
    line_width=2,
    color=C_OVERBOUGHT,
    alpha=0.85,
    legend_label="Overbought (70)",
)
p3.line(
    dates, [30] * n_points, line_dash="dashed", line_width=2, color=C_PRICE, alpha=0.6, legend_label="Oversold (30)"
)
p3.add_tools(CrosshairTool(**crosshair_opts))
p3.add_tools(HoverTool(tooltips=[("Date", "@date_str"), ("RSI", "@rsi{0.0}")], mode="vline"))

# Style all charts — theme-adaptive chrome
for p in [p1, p2, p3]:
    p.title.text_font_size = "50pt"
    p.xaxis.axis_label_text_font_size = "42pt"
    p.yaxis.axis_label_text_font_size = "42pt"
    p.xaxis.major_label_text_font_size = "34pt"
    p.yaxis.major_label_text_font_size = "34pt"
    p.legend.label_text_font_size = "28pt"
    p.legend.location = "top_left"
    p.legend.background_fill_color = ELEVATED_BG
    p.legend.border_line_color = INK_SOFT
    p.legend.label_text_color = INK_SOFT
    p.legend.padding = 12
    p.legend.spacing = 6

    p.background_fill_color = PAGE_BG
    p.border_fill_color = PAGE_BG
    p.outline_line_color = INK_SOFT

    p.title.text_color = INK
    p.xaxis.axis_label_text_color = INK
    p.yaxis.axis_label_text_color = INK
    p.xaxis.major_label_text_color = INK_SOFT
    p.yaxis.major_label_text_color = INK_SOFT
    p.xaxis.axis_line_color = INK_SOFT
    p.yaxis.axis_line_color = INK_SOFT
    p.xaxis.major_tick_line_color = INK_SOFT
    p.yaxis.major_tick_line_color = INK_SOFT

    p.xgrid.grid_line_color = INK
    p.ygrid.grid_line_color = INK
    p.xgrid.grid_line_alpha = 0.10
    p.ygrid.grid_line_alpha = 0.10

# Hide x-axis on upper charts for cleaner stacked look
p1.xaxis.visible = False
p2.xaxis.visible = False

# Stacked layout — heights sum to 1800 exactly
layout = column(p1, p2, p3, spacing=0, sizing_mode="fixed")

# Save interactive HTML
output_file(f"plot-{THEME}.html")
save(layout)

# Screenshot with headless Chrome — use CDP Page.captureScreenshot with
# captureBeyondViewport so the canvas dimensions are exact regardless of
# the browser's implicit window-chrome offset (~139 px on headless Chrome).
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H + 200}",
    "--hide-scrollbars",
    "--force-device-scale-factor=1",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
result = driver.execute_cdp_cmd(
    "Page.captureScreenshot",
    {
        "format": "png",
        "clip": {"x": 0.0, "y": 0.0, "width": float(W), "height": float(H), "scale": 1.0},
        "captureBeyondViewport": True,
    },
)
with open(f"plot-{THEME}.png", "wb") as fh:
    fh.write(base64.b64decode(result["data"]))
driver.quit()
