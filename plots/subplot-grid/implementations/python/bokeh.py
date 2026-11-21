"""anyplot.ai
subplot-grid: Subplot Grid Layout
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-13
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.layouts import column, gridplot
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (first series is always #009E73)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
HIGH_RETURN = 8  # annual return (%) above which an asset counts as a strong performer
LOW_RETURN = 5  # annual return (%) below which an asset counts as a weak performer
HIST_BINS = 25

# Columns: set these to your table's column names
DAY = "Trading Day"  # role: x
PRICE = "Price ($)"  # role: y
VOLUME = "Volume (Millions)"  # role: extra
RISK = "Risk (Volatility %)"  # role: extra
ASSET_RETURN = "Annual Return (%)"  # role: extra
DAILY_RETURN = "Daily Return (%)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("dashboard.csv")
# Financial dashboard: each panel's columns fill the first rows; shorter columns stay NaN below.
rng = np.random.default_rng(42)
n_days, n_assets, n_returns = 60, 40, 200

returns = rng.normal(0.001, 0.02, n_days)
price = 100 * np.cumprod(1 + returns)
volume = rng.uniform(0.8, 1.2, n_days) * 1_000_000 * (1 + np.abs(returns) * 10)

asset_returns = rng.normal(8, 4, n_assets)
asset_risk = np.abs(asset_returns) * 0.3 + rng.uniform(2, 8, n_assets)

daily_returns = rng.normal(0.1, 2.5, n_returns)


def padded(values):
    out = np.full(n_returns, np.nan)
    out[: len(values)] = values
    return out


df = pd.DataFrame(
    {
        DAY: padded(np.arange(n_days)),
        PRICE: padded(price),
        VOLUME: padded(volume / 1_000_000),
        RISK: padded(asset_risk),
        ASSET_RETURN: padded(asset_returns),
        DAILY_RETURN: daily_returns,
    }
)

# Plot: reads only df and the constants above
PANEL_W, PANEL_H, TITLE_H = 1600, 840, 120


def make_panel(title, x_label, y_label):
    p = figure(
        width=PANEL_W,
        height=PANEL_H,
        title=title,
        x_axis_label=x_label,
        y_axis_label=y_label,
        tools="",
        toolbar_location=None,
        min_border_left=150,
        min_border_bottom=130,
        min_border_top=60,
        min_border_right=40,
    )
    p.background_fill_color = PAGE_BG
    p.border_fill_color = PAGE_BG
    p.outline_line_color = INK_SOFT
    p.title.text_font_size = "28pt"
    p.title.text_color = INK
    p.xaxis.axis_label_text_font_size = "22pt"
    p.yaxis.axis_label_text_font_size = "22pt"
    p.xaxis.axis_label_text_color = INK
    p.yaxis.axis_label_text_color = INK
    p.xaxis.major_label_text_font_size = "18pt"
    p.yaxis.major_label_text_font_size = "18pt"
    p.xaxis.major_label_text_color = INK_SOFT
    p.yaxis.major_label_text_color = INK_SOFT
    p.axis.axis_line_color = INK_SOFT
    p.axis.major_tick_line_color = INK_SOFT
    p.grid.grid_line_color = INK
    p.grid.grid_line_alpha = 0.10
    return p


# Panel 1: price line (top-left)
series = df[[DAY, PRICE]].dropna()
p1 = make_panel("Stock Price Over Time", DAY, PRICE)
src_price = ColumnDataSource(series)
p1.line(DAY, PRICE, source=src_price, line_width=4, color=IMPRINT_PALETTE[0], alpha=0.9)
p1.scatter(DAY, PRICE, source=src_price, size=12, color=IMPRINT_PALETTE[0], alpha=0.6)

# Panel 2: volume bars (top-right)
p2 = make_panel("Daily Trading Volume", DAY, VOLUME)
p2.vbar(
    x=DAY,
    top=VOLUME,
    source=ColumnDataSource(df[[DAY, VOLUME]].dropna()),
    width=0.7,
    color=IMPRINT_PALETTE[1],
    alpha=0.8,
)

# Panel 3: risk vs return scatter (bottom-left), colored by performance
assets = df[[RISK, ASSET_RETURN]].dropna().copy()
assets["tier"] = np.where(
    assets[ASSET_RETURN] > HIGH_RETURN,
    IMPRINT_PALETTE[0],
    np.where(assets[ASSET_RETURN] < LOW_RETURN, IMPRINT_PALETTE[2], IMPRINT_PALETTE[1]),
)
p3 = make_panel("Risk vs Return Analysis", RISK, ASSET_RETURN)
p3.scatter(RISK, ASSET_RETURN, source=ColumnDataSource(assets), size=18, color="tier", alpha=0.7)

# Panel 4: distribution histogram (bottom-right)
counts, edges = np.histogram(df[DAILY_RETURN].dropna(), bins=HIST_BINS)
p4 = make_panel("Daily Returns Distribution", DAILY_RETURN, "Frequency")
p4.quad(
    top=counts,
    bottom=0,
    left=edges[:-1],
    right=edges[1:],
    fill_color=IMPRINT_PALETTE[2],
    line_color=PAGE_BG,
    alpha=0.8,
    line_width=2,
)

# Layout: figure title above a 2x2 grid, 3200 x 1800 in total
heading = figure(
    width=2 * PANEL_W,
    height=TITLE_H,
    title="subplot-grid · python · bokeh · anyplot.ai",
    tools="",
    toolbar_location=None,
    min_border=0,
)
heading.title.align = "center"
heading.title.text_font_size = "36pt"
heading.title.text_color = INK
heading.background_fill_color = PAGE_BG
heading.border_fill_color = PAGE_BG
heading.outline_line_color = None
heading.axis.visible = False
heading.grid.visible = False
grid = gridplot([[p1, p2], [p3, p4]], merge_tools=False, toolbar_location=None)
layout = column(heading, grid, background=PAGE_BG)

# Write the interactive HTML (also a required catalog artifact)
output_file(f"plot-{THEME}.html")
save(layout)

# Screenshot it with headless Chrome — Selenium 4 / Selenium Manager
# auto-resolves a working driver for the system Chrome.
W, H = 2 * PANEL_W, TITLE_H + 2 * PANEL_H
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
# Pin the viewport exactly: headless Chrome reserves a phantom title-bar height
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
