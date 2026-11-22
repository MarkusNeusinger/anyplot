"""anyplot.ai
indicator-macd: MACD Technical Indicator Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-16
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Legend, Span
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
HIST_POSITIVE = IMPRINT_PALETTE[0]  # green: histogram above zero
HIST_NEGATIVE = IMPRINT_PALETTE[4]  # red: histogram below zero
MACD_COLOR = IMPRINT_PALETTE[2]  # blue
SIGNAL_COLOR = IMPRINT_PALETTE[3]  # ochre

# Constants: the standard MACD parameters
FAST_SPAN = 12
SLOW_SPAN = 26
SIGNAL_SPAN = 9

# Columns: set these to your table's column names
DATE = "Date"  # role: date
MACD = "MACD"  # role: macd
SIGNAL = "Signal"  # role: signal
HISTOGRAM = "Histogram"  # role: histogram

# Data: replace this block with your own table, for example df = pd.read_csv("macd.csv", parse_dates=["Date"])
np.random.seed(42)
n_days = 150
returns = np.random.normal(0.001, 0.02, n_days)
close = pd.Series(100 * np.cumprod(1 + returns))
macd = close.ewm(span=FAST_SPAN, adjust=False).mean() - close.ewm(span=SLOW_SPAN, adjust=False).mean()
signal = macd.ewm(span=SIGNAL_SPAN, adjust=False).mean()
df = pd.DataFrame(
    {DATE: pd.date_range("2025-06-01", periods=n_days, freq="D"), MACD: macd, SIGNAL: signal, HISTOGRAM: macd - signal}
)
df = df.iloc[SLOW_SPAN + SIGNAL_SPAN :].reset_index(
    drop=True
)  # drop the warm-up, where the averages are not yet filled

# Plot
df["_pos"] = df[HISTOGRAM].where(df[HISTOGRAM] >= 0, 0)
df["_neg"] = df[HISTOGRAM].where(df[HISTOGRAM] < 0, 0)
source = ColumnDataSource(df)
bar_width = 0.8 * df[DATE].diff().median() / pd.Timedelta(milliseconds=1)  # 80% of the date spacing, in ms

p = figure(
    width=3200,
    height=1800,
    x_axis_type="datetime",
    title="indicator-macd · python · bokeh · anyplot.ai",
    x_axis_label=DATE,
    y_axis_label=f"MACD value (EMA {FAST_SPAN}/{SLOW_SPAN}/{SIGNAL_SPAN})",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

hist_pos = p.vbar(
    x=DATE, top="_pos", width=bar_width, source=source, fill_color=HIST_POSITIVE, line_color=HIST_POSITIVE, alpha=0.8
)
hist_neg = p.vbar(
    x=DATE, top="_neg", width=bar_width, source=source, fill_color=HIST_NEGATIVE, line_color=HIST_NEGATIVE, alpha=0.8
)
macd_line = p.line(x=DATE, y=MACD, source=source, line_color=MACD_COLOR, line_width=6)
signal_line = p.line(x=DATE, y=SIGNAL, source=source, line_color=SIGNAL_COLOR, line_width=6)

p.add_layout(Span(location=0, dimension="width", line_color=INK_SOFT, line_dash="dashed", line_width=3, line_alpha=0.7))

legend = Legend(
    items=[
        (f"MACD line (EMA {FAST_SPAN} − EMA {SLOW_SPAN})", [macd_line]),
        (f"Signal line (EMA {SIGNAL_SPAN} of MACD)", [signal_line]),
        ("Histogram above zero", [hist_pos]),
        ("Histogram below zero", [hist_neg]),
    ],
    location="top_left",
    label_text_font_size="30pt",
    label_text_color=INK_SOFT,
    spacing=10,
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.9,
    border_line_color=INK_SOFT,
)
p.add_layout(legend)

p.add_tools(
    HoverTool(
        tooltips=[
            (DATE, f"@{{{DATE}}}{{%F}}"),
            (MACD, f"@{{{MACD}}}{{0.000}}"),
            (SIGNAL, f"@{{{SIGNAL}}}{{0.000}}"),
            (HISTOGRAM, f"@{{{HISTOGRAM}}}{{0.000}}"),
        ],
        formatters={f"@{{{DATE}}}": "datetime"},
    )
)

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
for axis in (p.xaxis, p.yaxis):
    axis.axis_label_text_font_size = "42pt"
    axis.major_label_text_font_size = "34pt"
    axis.axis_label_text_color = INK
    axis.major_label_text_color = INK_SOFT
    axis.axis_line_color = INK_SOFT
    axis.major_tick_line_color = INK_SOFT
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Save HTML and PNG
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
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)  # let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
