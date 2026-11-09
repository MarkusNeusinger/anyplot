"""anyplot.ai
indicator-rsi: RSI Technical Indicator Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-16
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import BoxAnnotation, ColumnDataSource, Legend, LegendItem, Range1d, Span
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: position 1 for the RSI line, matte red for overbought, blue for oversold
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
RSI_COLOR = IMPRINT_PALETTE[0]
OVERBOUGHT_COLOR = IMPRINT_PALETTE[4]
OVERSOLD_COLOR = IMPRINT_PALETTE[2]

# Constants
LOOKBACK = 14  # standard RSI lookback period
OVERBOUGHT = 70
OVERSOLD = 30
CENTERLINE = 50
RSI_MIN, RSI_MAX = 0, 100

# Columns: set these to your table's column names
DATE = "Date"  # role: date
RSI = "RSI (14-period)"  # role: rsi

# Data: replace this block with your own table, for example df = pd.read_csv("rsi.csv", parse_dates=["Date"])
np.random.seed(42)
n_days = 120
dates = pd.date_range(start="2024-01-01", periods=n_days, freq="B")
returns = np.random.normal(0.0005, 0.02, n_days)
returns[30:40] = np.random.normal(0.02, 0.01, 10)  # strong uptrend pushes RSI high
returns[60:75] = np.random.normal(-0.015, 0.01, 15)  # downtrend pushes RSI low
returns[95:105] = np.random.normal(0.018, 0.01, 10)  # another uptrend
price = 100 * np.exp(np.cumsum(returns))

# Wilder-smoothed RSI over the lookback period
delta = np.diff(price)
gains = np.where(delta > 0, delta, 0)
losses = np.where(delta < 0, -delta, 0)
avg_gain = np.zeros(len(price))
avg_loss = np.zeros(len(price))
avg_gain[LOOKBACK] = np.mean(gains[:LOOKBACK])
avg_loss[LOOKBACK] = np.mean(losses[:LOOKBACK])
for i in range(LOOKBACK + 1, len(price)):
    avg_gain[i] = (avg_gain[i - 1] * (LOOKBACK - 1) + gains[i - 1]) / LOOKBACK
    avg_loss[i] = (avg_loss[i - 1] * (LOOKBACK - 1) + losses[i - 1]) / LOOKBACK
rs = np.divide(avg_gain, avg_loss, out=np.zeros_like(avg_gain), where=avg_loss != 0)
rsi = 100 - (100 / (1 + rs))
df = pd.DataFrame({DATE: dates[LOOKBACK:], RSI: rsi[LOOKBACK:]})

# Plot: reads only df and the constants above
source = ColumnDataSource(df)
overbought_rows = ColumnDataSource(df[df[RSI] >= OVERBOUGHT])
oversold_rows = ColumnDataSource(df[df[RSI] <= OVERSOLD])

p = figure(
    width=3200,
    height=1800,
    title="indicator-rsi · python · bokeh · anyplot.ai",
    x_axis_label=DATE,
    y_axis_label=RSI,
    x_axis_type="datetime",
    y_range=Range1d(RSI_MIN, RSI_MAX),
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=80,
)

# Shaded zones and reference levels, kept light so the RSI line leads
p.add_layout(
    BoxAnnotation(
        bottom=OVERBOUGHT, top=RSI_MAX, fill_color=OVERBOUGHT_COLOR, fill_alpha=0.10, line_alpha=0, level="underlay"
    )
)
p.add_layout(
    BoxAnnotation(
        bottom=RSI_MIN, top=OVERSOLD, fill_color=OVERSOLD_COLOR, fill_alpha=0.10, line_alpha=0, level="underlay"
    )
)
p.add_layout(
    Span(location=OVERBOUGHT, dimension="width", line_color=OVERBOUGHT_COLOR, line_width=3, line_dash="dashed")
)
p.add_layout(Span(location=OVERSOLD, dimension="width", line_color=OVERSOLD_COLOR, line_width=3, line_dash="dashed"))
p.add_layout(Span(location=CENTERLINE, dimension="width", line_color=INK_MUTED, line_width=2, line_dash="dotted"))

# RSI line with markers on the readings beyond each threshold
rsi_line = p.line(x=DATE, y=RSI, source=source, line_width=5, line_color=RSI_COLOR)
high_marks = p.scatter(
    x=DATE, y=RSI, source=overbought_rows, size=20, color=OVERBOUGHT_COLOR, line_color=PAGE_BG, line_width=2
)
low_marks = p.scatter(
    x=DATE, y=RSI, source=oversold_rows, size=20, color=OVERSOLD_COLOR, line_color=PAGE_BG, line_width=2
)

legend = Legend(
    items=[
        LegendItem(label=f"RSI ({LOOKBACK}-period lookback)", renderers=[rsi_line]),
        LegendItem(label=f"Overbought (≥ {OVERBOUGHT})", renderers=[high_marks]),
        LegendItem(label=f"Oversold (≤ {OVERSOLD})", renderers=[low_marks]),
    ],
    orientation="horizontal",
    location="top_right",
    label_text_font_size="34pt",
    label_text_color=INK_SOFT,
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.9,
    border_line_color=INK_SOFT,
    glyph_width=60,
    glyph_height=40,
    spacing=40,
    padding=20,
)
p.add_layout(legend, "above")

# Style
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
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.yaxis.ticker = [RSI_MIN, OVERSOLD, CENTERLINE, OVERBOUGHT, RSI_MAX]

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.12

# Save
output_file(f"plot-{THEME}.html", title="indicator-rsi · python · bokeh · anyplot.ai")
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
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
