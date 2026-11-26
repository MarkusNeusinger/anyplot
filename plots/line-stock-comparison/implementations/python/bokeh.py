"""anyplot.ai
line-stock-comparison: Stock Price Comparison Chart
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 88/100 | Updated: 2026-11-26
"""

import base64
import os
import sys
import time
from pathlib import Path


# Remove the current directory from sys.path to avoid circular imports with bokeh.py
sys.path = [p for p in sys.path if p not in ("", ".", os.getcwd(), os.path.dirname(__file__))]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from bokeh.io import output_file, save  # noqa: E402
from bokeh.models import ColumnDataSource, HoverTool, Label, Legend, Range1d, Span  # noqa: E402
from bokeh.plotting import figure  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per stock in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BASE = 100  # every series is rebased to this value on the first date

# Columns: set these to your table's column names
DATE = "Date"  # role: date
SYMBOL = "Symbol"  # role: symbol
PRICE = "Adjusted close (USD)"  # role: price

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
# Synthetic daily prices via geometric Brownian motion, one row per symbol and trading day
dates = pd.date_range("2024-01-02", periods=252, freq="B")
params = {
    "AAPL": {"drift": 0.0006, "volatility": 0.018, "seed": 42, "start": 185.0},
    "GOOGL": {"drift": 0.0005, "volatility": 0.020, "seed": 43, "start": 140.0},
    "MSFT": {"drift": 0.0002, "volatility": 0.016, "seed": 44, "start": 370.0},
    "SPY": {"drift": 0.0003, "volatility": 0.009, "seed": 45, "start": 470.0},
}
frames = []
for symbol, cfg in params.items():
    rng = np.random.RandomState(cfg["seed"])
    returns = rng.normal(cfg["drift"], cfg["volatility"], len(dates))
    prices = cfg["start"] * np.exp(np.cumsum(returns))
    prices = prices / prices[0] * cfg["start"]
    frames.append(pd.DataFrame({DATE: dates, SYMBOL: symbol, PRICE: prices}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
df = df.sort_values([SYMBOL, DATE], kind="stable")
df["rebased"] = df[PRICE].astype(float) / df.groupby(SYMBOL, sort=False)[PRICE].transform("first").astype(float) * BASE
symbols = list(df[SYMBOL].unique())
all_dates = np.sort(df[DATE].unique())
final = df.groupby(SYMBOL, sort=False)["rebased"].last()
best, worst = final.idxmax(), final.idxmin()

# Extend the x-axis to the right to make room for the end-of-series labels
DAY_MS = 24 * 60 * 60 * 1000
first_ms = pd.Timestamp(all_dates[0]).timestamp() * 1000
last_ms = pd.Timestamp(all_dates[-1]).timestamp() * 1000
span_ms = last_ms - first_ms
x_range = Range1d(start=first_ms - 0.02 * span_ms, end=last_ms + 0.24 * span_ms)

# Figure: 3200x1800 with the toolbar disabled for correct PNG dimensions
p = figure(
    width=3200,
    height=1800,
    title="line-stock-comparison · python · bokeh · anyplot.ai",
    x_axis_label=DATE,
    y_axis_label=f"Rebased price (start = {BASE})",
    x_axis_type="datetime",
    x_range=x_range,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=80,
)

# Font sizes: bokeh CSS pt sizing (~1.333 source-px per pt)
p.title.text_font_size = "50pt"
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"

# Reference line at the base (starting point indicator)
p.add_layout(Span(location=BASE, dimension="width", line_color=INK_SOFT, line_dash="dashed", line_width=3))

# End-of-series label positions: spread the labels apart where final values are close
y_span = df["rebased"].max() - df["rebased"].min()
min_gap = 0.07 * y_span
label_ys: dict[str, float] = {}
prev_y = -np.inf
for sym in final.sort_values().index:
    prev_y = max(final[sym], prev_y + min_gap)
    label_ys[sym] = prev_y

# One line per stock, thicker for the best and worst performers
legend_items = []
for i, symbol in enumerate(symbols):
    rows = ColumnDataSource(df[df[SYMBOL] == symbol])
    width = 7 if symbol in (best, worst) else 4
    line = p.line(
        x=DATE,
        y="rebased",
        source=rows,
        line_width=width,
        line_color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
        alpha=0.9,
    )
    legend_items.append((symbol, [line]))
    p.add_layout(
        Label(
            x=last_ms + 8 * DAY_MS,
            y=label_ys[symbol],
            text=f"{symbol} {final[symbol]:.0f}",
            text_color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
            text_font_size="28pt",
            text_font_style="bold",
            text_baseline="middle",
            text_align="left",
        )
    )

# Hover tool: active in the HTML artifact
hover = HoverTool(
    tooltips=[(SYMBOL, f"@{{{SYMBOL}}}"), (DATE, f"@{{{DATE}}}{{%F}}"), ("Rebased", "@rebased{0.1f}")],
    formatters={f"@{{{DATE}}}": "datetime"},
    mode="vline",
)
p.add_tools(hover)

# Legend above the plot, so it never covers data
legend = Legend(
    items=legend_items,
    orientation="horizontal",
    label_text_font_size="34pt",
    label_text_color=INK_SOFT,
    glyph_width=60,
    glyph_height=40,
    label_standoff=16,
    spacing=40,
    padding=20,
    background_fill_color=ELEVATED_BG,
    border_line_color=None,
    click_policy="hide",
)
p.add_layout(legend, "above")

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None  # L-shaped frame via axis lines only

p.title.text_color = INK
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Y-axis grid only (appropriate for line charts)
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10
p.xgrid.grid_line_color = None

# Save interactive HTML artifact
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome, pinned to exactly W x H px via CDP
W, H = 3200, 1800
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
driver.set_window_size(W, H + 200)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_script(
    "document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG
)
time.sleep(3)
screenshot = driver.execute_cdp_cmd(
    "Page.captureScreenshot",
    {"format": "png", "clip": {"x": 0, "y": 0, "width": W, "height": H, "scale": 1}, "captureBeyondViewport": True},
)
with open(f"plot-{THEME}.png", "wb") as f:
    f.write(base64.b64decode(screenshot["data"]))
driver.quit()
