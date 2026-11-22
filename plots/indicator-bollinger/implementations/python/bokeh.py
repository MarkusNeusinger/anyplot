"""anyplot.ai
indicator-bollinger: Bollinger Bands Indicator Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-17
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import Band, ColumnDataSource, HoverTool, Legend
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
WINDOW = 20  # SMA period
NUM_STD = 2  # standard deviation multiple

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Close price ($)"  # role: close
SMA = "SMA (20)"  # role: sma
UPPER = "Upper band"  # role: upper_band
LOWER = "Lower band"  # role: lower_band

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 120
dates = pd.date_range("2024-01-01", periods=n_days, freq="B")
returns = np.random.normal(0.0005, 0.015, n_days)
close = pd.Series(100 * np.cumprod(1 + returns))
rolling = close.rolling(window=WINDOW)
df = pd.DataFrame(
    {
        DATE: dates,
        CLOSE: close,
        SMA: rolling.mean(),
        UPPER: rolling.mean() + NUM_STD * rolling.std(),
        LOWER: rolling.mean() - NUM_STD * rolling.std(),
    }
).dropna()

# Plot: reads only df and the constants above
source = ColumnDataSource(df)
band_color = IMPRINT_PALETTE[2]

p = figure(
    width=3200,
    height=1800,
    title="indicator-bollinger · python · bokeh · anyplot.ai",
    x_axis_label=DATE,
    y_axis_label=CLOSE,
    x_axis_type="datetime",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

p.add_layout(
    Band(
        base=DATE,
        lower=LOWER,
        upper=UPPER,
        source=source,
        fill_alpha=0.15,
        fill_color=band_color,
        line_color=band_color,
        line_alpha=0.4,
    )
)

upper_line = p.line(x=DATE, y=UPPER, source=source, line_color=band_color, line_width=3, alpha=0.6)
p.line(x=DATE, y=LOWER, source=source, line_color=band_color, line_width=3, alpha=0.6)
sma_line = p.line(x=DATE, y=SMA, source=source, line_color=band_color, line_width=4, line_dash="dashed", alpha=0.95)
price_line = p.line(x=DATE, y=CLOSE, source=source, line_color=IMPRINT_PALETTE[0], line_width=5)

p.add_tools(
    HoverTool(
        tooltips=[
            (DATE, f"@{{{DATE}}}{{%F}}"),
            (CLOSE, f"$@{{{CLOSE}}}{{0.2f}}"),
            (SMA, f"$@{{{SMA}}}{{0.2f}}"),
            (UPPER, f"$@{{{UPPER}}}{{0.2f}}"),
            (LOWER, f"$@{{{LOWER}}}{{0.2f}}"),
        ],
        formatters={f"@{{{DATE}}}": "datetime"},
        mode="vline",
        renderers=[price_line],
    )
)

legend = Legend(
    items=[
        ("Close price", [price_line]),
        (f"SMA ({WINDOW})", [sma_line]),
        (f"Upper / lower band (±{NUM_STD}σ)", [upper_line]),
    ],
    location="top_left",
)
p.add_layout(legend, "right")

# Style
p.title.text_font_size = "50pt"
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.legend.label_text_font_size = "30pt"
p.legend.glyph_width = 70
p.legend.glyph_height = 40
p.legend.spacing = 16
p.legend.padding = 20

p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK

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
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT

# Save interactive HTML, then screenshot it with headless Chrome
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
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
