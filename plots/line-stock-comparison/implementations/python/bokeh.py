"""anyplot.ai
line-stock-comparison: Stock Price Comparison Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-23
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
from bokeh.models import HoverTool, Label, Legend, Range1d, Span  # noqa: E402
from bokeh.plotting import figure  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

ANYPLOT_PALETTE = ["#009E73", "#9418DB", "#B71D27", "#16B8F3"]

# Data — synthetic stock price paths via geometric Brownian motion
n_days = 252
dates = pd.date_range("2024-01-02", periods=n_days, freq="B")

# Per-stock seeds ensure reproducibility without cross-stock correlation artifacts
stocks = {
    "AAPL": {"drift": 0.0008, "volatility": 0.018, "seed": 42},
    "GOOGL": {"drift": 0.0006, "volatility": 0.020, "seed": 43},
    "MSFT": {"drift": 0.0007, "volatility": 0.016, "seed": 44},
    "SPY": {"drift": 0.0003, "volatility": 0.009, "seed": 45},
}

price_data = {"date": dates}
for symbol, params in stocks.items():
    rng = np.random.RandomState(params["seed"])
    returns = rng.normal(params["drift"], params["volatility"], n_days)
    prices = 100 * np.exp(np.cumsum(returns))
    prices = prices / prices[0] * 100  # Rebase to exactly 100 at start
    price_data[symbol] = prices

df = pd.DataFrame(price_data)

# Determine visual hierarchy by final performance
final_vals = {symbol: df[symbol].iloc[-1] for symbol in stocks}
ranked = sorted(final_vals, key=lambda s: final_vals[s])
best, worst = ranked[-1], ranked[0]

# Extend x-axis range to accommodate end-of-series labels
DAY_MS = 24 * 60 * 60 * 1000
start_ms = int((dates[0] - pd.Timedelta(days=5)).timestamp() * 1000)
end_ms = int((dates[-1] + pd.Timedelta(days=55)).timestamp() * 1000)

# Figure — 3200×1800 with toolbar disabled for correct PNG dimensions
p = figure(
    width=3200,
    height=1800,
    title="line-stock-comparison · python · bokeh · anyplot.ai",
    x_axis_label="Date",
    y_axis_label="Rebased Price (Start = 100)",
    x_axis_type="datetime",
    x_range=Range1d(start=start_ms, end=end_ms),
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=80,
)

# Font sizes — bokeh CSS pt sizing (~1.333 source-px per pt)
p.title.text_font_size = "50pt"
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"

# Reference line at 100 (starting point indicator)
hline = Span(location=100, dimension="width", line_color=INK_SOFT, line_dash="dashed", line_width=3)
p.add_layout(hline)

# Plot each stock series with performance-based line widths for visual hierarchy
legend_items = []
label_ms_offset = 7 * DAY_MS  # position label ~7 trading days past the last date
for i, symbol in enumerate(stocks):
    lw = 7 if symbol in (best, worst) else 4  # emphasize top and bottom performers
    line = p.line(x=df["date"], y=df[symbol], line_width=lw, line_color=ANYPLOT_PALETTE[i], alpha=0.9)
    legend_items.append((symbol, [line]))

    # End-of-series label showing symbol and final value
    final_date_ms = int(df["date"].iloc[-1].timestamp() * 1000)
    final_val = final_vals[symbol]
    p.add_layout(
        Label(
            x=final_date_ms + label_ms_offset,
            y=final_val,
            text=f"{symbol} {final_val:.0f}",
            text_color=ANYPLOT_PALETTE[i],
            text_font_size="26pt",
            text_baseline="middle",
            text_align="left",
        )
    )

# Hover tool — active in HTML artifact
hover = HoverTool(tooltips=[("Date", "@x{%F}"), ("Value", "@y{0.2f}")], formatters={"@x": "datetime"}, mode="vline")
p.add_tools(hover)

# Legend
legend = Legend(
    items=legend_items,
    location="top_left",
    label_text_font_size="34pt",
    label_text_color=INK_SOFT,
    glyph_width=60,
    glyph_height=30,
    spacing=15,
    padding=20,
    background_fill_color=ELEVATED_BG,
    border_line_color=INK_SOFT,
    click_policy="hide",
)
p.add_layout(legend)

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None  # Remove box; L-shaped frame via axis lines only

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

# Screenshot with headless Chrome — use CDP clip to capture exactly W×H px
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
time.sleep(3)
screenshot = driver.execute_cdp_cmd(
    "Page.captureScreenshot",
    {"format": "png", "clip": {"x": 0, "y": 0, "width": W, "height": H, "scale": 1}, "captureBeyondViewport": True},
)
with open(f"plot-{THEME}.png", "wb") as f:
    f.write(base64.b64decode(screenshot["data"]))
driver.quit()
