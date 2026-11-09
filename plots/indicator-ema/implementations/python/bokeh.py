"""anyplot.ai
indicator-ema: Exponential Moving Average (EMA) Indicator Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 74/100 | Updated: 2026-05-19
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Legend
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SHORT_SPAN = 12  # short-period EMA
LONG_SPAN = 26  # long-period EMA

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Price (USD)"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 120
dates = pd.date_range("2025-01-01", periods=n_days, freq="B")  # Business days
returns = np.random.normal(0.0008, 0.018, n_days)  # Daily returns
price = 150 * np.cumprod(1 + returns)
price[40:80] = price[40:80] * np.linspace(1, 1.15, 40)  # Uptrend
price[80:100] = price[80:100] * np.linspace(1, 0.92, 20)  # Downtrend
df = pd.DataFrame({DATE: dates, CLOSE: price})

# Plot: reads only df and the constants above
ema_short_label = f"EMA {SHORT_SPAN}"
ema_long_label = f"EMA {LONG_SPAN}"
plot_df = df[[DATE, CLOSE]].copy()
plot_df[ema_short_label] = plot_df[CLOSE].ewm(span=SHORT_SPAN, adjust=False).mean()
plot_df[ema_long_label] = plot_df[CLOSE].ewm(span=LONG_SPAN, adjust=False).mean()
source = ColumnDataSource(plot_df)

# Crossovers: the exact intersection of the two EMA segments between consecutive dates
diff = (plot_df[ema_short_label] - plot_df[ema_long_label]).to_numpy()
crossed = np.where(np.sign(diff[1:]) * np.sign(diff[:-1]) < 0)[0]
frac = diff[crossed] / (diff[crossed] - diff[crossed + 1])
t0 = plot_df[DATE].iloc[crossed].to_numpy()
t1 = plot_df[DATE].iloc[crossed + 1].to_numpy()
y0 = plot_df[ema_short_label].iloc[crossed].to_numpy()
y1 = plot_df[ema_short_label].iloc[crossed + 1].to_numpy()
crossover_source = ColumnDataSource(data={DATE: t0 + (t1 - t0) * frac, CLOSE: y0 + (y1 - y0) * frac})

title = "indicator-ema · python · bokeh · anyplot.ai"
title_size = max(34, round(50 * min(1.0, 67 / len(title))))

p = figure(
    width=3200,
    height=1800,
    title=title,
    x_axis_label=DATE,
    y_axis_label=CLOSE,
    x_axis_type="datetime",
    tools="pan,wheel_zoom,box_zoom,reset,save",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Price is the dominant series; the EMAs are thinner overlays on the same axis
price_line = p.line(DATE, CLOSE, source=source, line_width=6, line_color=IMPRINT_PALETTE[0])
ema_short_line = p.line(DATE, ema_short_label, source=source, line_width=3.5, line_color=IMPRINT_PALETTE[2])
ema_long_line = p.line(DATE, ema_long_label, source=source, line_width=3.5, line_color=IMPRINT_PALETTE[3])
crossover_marks = p.scatter(
    DATE, CLOSE, source=crossover_source, size=22, marker="circle", fill_color=PAGE_BG, line_color=INK, line_width=3.5
)

legend = Legend(
    items=[
        ("Close price", [price_line]),
        (ema_short_label, [ema_short_line]),
        (ema_long_label, [ema_long_line]),
        ("EMA crossover", [crossover_marks]),
    ]
)
p.add_layout(legend, "right")

# Style
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.title.text_font_size = f"{title_size}pt"
p.title.text_font_style = "normal"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_font_style = "normal"
p.yaxis.axis_label_text_font_style = "normal"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.yaxis.formatter.use_scientific = False

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.15
p.ygrid.grid_line_alpha = 0.15

p.legend.label_text_font_size = "34pt"
p.legend.label_text_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.glyph_width = 60
p.legend.glyph_height = 40
p.legend.spacing = 18
p.legend.padding = 24
p.legend.margin = 30

# Save
output_file(f"plot-{THEME}.html", title=title)
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
