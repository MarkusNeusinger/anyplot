""" anyplot.ai
renko-basic: Basic Renko Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-17
"""

import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd


# Remove current directory from path to avoid name conflict with bokeh.py
sys.path = [p for p in sys.path if p != "." and not p.endswith(os.path.dirname(__file__))]

from bokeh.io import output_file, save  # noqa: E402
from bokeh.models import ColumnDataSource, HoverTool  # noqa: E402
from bokeh.plotting import figure  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BULLISH_COLOR = "#009E73"  # Okabe-Ito position 1 — always first series (green)
BEARISH_COLOR = "#AE3030"  # imprint red — down bricks

# Generate synthetic stock price data
np.random.seed(42)
n_days = 200
dates = pd.date_range("2024-01-01", periods=n_days, freq="D")
returns = np.random.randn(n_days) * 0.02
price = 100 * np.cumprod(1 + returns)

# Build Renko bricks
brick_size = 2.0
bricks = []
current_price = price[0]
brick_start = current_price - (current_price % brick_size)
direction = None
brick_index = 0

for close in price:
    while True:
        if direction is None:
            if close >= brick_start + brick_size:
                bricks.append(
                    {
                        "index": brick_index,
                        "bottom": brick_start,
                        "top": brick_start + brick_size,
                        "direction": "up",
                        "price_range": f"${brick_start:.2f} - ${brick_start + brick_size:.2f}",
                    }
                )
                brick_start += brick_size
                direction = "up"
                brick_index += 1
            elif close <= brick_start - brick_size:
                bricks.append(
                    {
                        "index": brick_index,
                        "bottom": brick_start - brick_size,
                        "top": brick_start,
                        "direction": "down",
                        "price_range": f"${brick_start - brick_size:.2f} - ${brick_start:.2f}",
                    }
                )
                brick_start -= brick_size
                direction = "down"
                brick_index += 1
            else:
                break
        elif direction == "up":
            if close >= brick_start + brick_size:
                bricks.append(
                    {
                        "index": brick_index,
                        "bottom": brick_start,
                        "top": brick_start + brick_size,
                        "direction": "up",
                        "price_range": f"${brick_start:.2f} - ${brick_start + brick_size:.2f}",
                    }
                )
                brick_start += brick_size
                brick_index += 1
            elif close <= brick_start - 2 * brick_size:
                bricks.append(
                    {
                        "index": brick_index,
                        "bottom": brick_start - brick_size,
                        "top": brick_start,
                        "direction": "down",
                        "price_range": f"${brick_start - brick_size:.2f} - ${brick_start:.2f}",
                    }
                )
                brick_start -= brick_size
                direction = "down"
                brick_index += 1
            else:
                break
        else:
            if close <= brick_start - brick_size:
                bricks.append(
                    {
                        "index": brick_index,
                        "bottom": brick_start - brick_size,
                        "top": brick_start,
                        "direction": "down",
                        "price_range": f"${brick_start - brick_size:.2f} - ${brick_start:.2f}",
                    }
                )
                brick_start -= brick_size
                brick_index += 1
            elif close >= brick_start + 2 * brick_size:
                bricks.append(
                    {
                        "index": brick_index,
                        "bottom": brick_start,
                        "top": brick_start + brick_size,
                        "direction": "up",
                        "price_range": f"${brick_start:.2f} - ${brick_start + brick_size:.2f}",
                    }
                )
                brick_start += brick_size
                direction = "up"
                brick_index += 1
            else:
                break

# Prepare data for plotting
brick_df = pd.DataFrame(bricks)
bullish = brick_df[brick_df["direction"] == "up"]
bearish = brick_df[brick_df["direction"] == "down"]

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="renko-basic · bokeh · anyplot.ai",
    x_axis_label="Brick Number",
    y_axis_label="Price ($)",
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

# Text styling for large canvas
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Theme-adaptive chrome
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

# Grid styling
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# Brick width
brick_width = 0.85

# Draw bullish bricks
if len(bullish) > 0:
    bullish_source = ColumnDataSource(
        data={
            "x": bullish["index"].values,
            "bottom": bullish["bottom"].values,
            "top": bullish["top"].values,
            "price_range": bullish["price_range"].values,
        }
    )
    bullish_bars = p.vbar(
        x="x",
        width=brick_width,
        bottom="bottom",
        top="top",
        source=bullish_source,
        color=BULLISH_COLOR,
        line_color=BULLISH_COLOR,
        line_width=1,
        legend_label="Bullish",
    )
    hover_bullish = HoverTool(
        renderers=[bullish_bars], tooltips=[("Brick", "@x"), ("Price Range", "@price_range"), ("Direction", "Up")]
    )
    p.add_tools(hover_bullish)

# Draw bearish bricks
if len(bearish) > 0:
    bearish_source = ColumnDataSource(
        data={
            "x": bearish["index"].values,
            "bottom": bearish["bottom"].values,
            "top": bearish["top"].values,
            "price_range": bearish["price_range"].values,
        }
    )
    bearish_bars = p.vbar(
        x="x",
        width=brick_width,
        bottom="bottom",
        top="top",
        source=bearish_source,
        color=BEARISH_COLOR,
        line_color=BEARISH_COLOR,
        line_width=1,
        legend_label="Bearish",
    )
    hover_bearish = HoverTool(
        renderers=[bearish_bars], tooltips=[("Brick", "@x"), ("Price Range", "@price_range"), ("Direction", "Down")]
    )
    p.add_tools(hover_bearish)

# Legend styling
if p.legend:
    p.legend.location = "top_left"
    p.legend.label_text_font_size = "18pt"
    p.legend.background_fill_color = ELEVATED_BG
    p.legend.border_line_color = INK_SOFT
    p.legend.label_text_color = INK_SOFT
    p.legend.glyph_height = 35
    p.legend.glyph_width = 35

# Save HTML output
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
W, H = 4800, 2700
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
