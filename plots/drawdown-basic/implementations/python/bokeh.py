"""anyplot.ai
drawdown-basic: Drawdown Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-23
"""

import base64
import os
import sys
import time
from pathlib import Path


# Remove the script's own directory from sys.path so "bokeh" resolves to the
# installed package, not this file.
_this_dir = str(Path(__file__).parent.resolve())
sys.path = [p for p in sys.path if os.path.abspath(p) != _this_dir and p != ""]

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Span
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette with semantic override: loss/drawdown → red
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
DRAWDOWN_COLOR = IMPRINT_PALETTE[4]  # Imprint red (pos 5) — semantic: financial loss
MAX_DD_COLOR = IMPRINT_PALETTE[2]  # Imprint blue (pos 3) — contrasting accent
RECOVERY_COLOR = IMPRINT_PALETTE[0]  # Imprint green (pos 1) — recovery / new highs

# Columns: set these to your table's column names
DATE = "Date"  # role: date
PRICE = "Portfolio value (USD)"  # role: price
DRAWDOWN = "Drawdown (%)"  # axis title of the derived drawdown column

# Data: replace this block with your own table, for example df = pd.read_csv("portfolio.csv")
np.random.seed(42)
rng = np.random
n_days = 750
returns = rng.normal(0.0003, 0.015, n_days)
returns[200:250] = rng.normal(-0.005, 0.025, 50)
returns[450:520] = rng.normal(-0.008, 0.030, 70)
returns[600:630] = rng.normal(-0.004, 0.020, 30)
df = pd.DataFrame(
    {DATE: pd.date_range("2022-01-01", periods=n_days, freq="B"), PRICE: 100 * np.exp(np.cumsum(returns))}
)

# Plot: reads only df and the constants above
df = df.dropna(subset=[PRICE]).reset_index(drop=True)
df[DRAWDOWN] = (df[PRICE] / df[PRICE].cummax() - 1) * 100
dates = df[DATE]
drawdown = df[DRAWDOWN]

# Maximum drawdown: trough, the last peak before it, and the return to a new high
trough = int(drawdown.idxmin())
max_dd_value = drawdown[trough]
max_dd_date = dates[trough]
at_peak = drawdown <= -0.1
peak_before = np.flatnonzero(~at_peak.to_numpy()[: trough + 1])
start = int(peak_before[-1]) if len(peak_before) else 0
max_dd_duration = (max_dd_date - dates[start]).days
back_at_peak = np.flatnonzero(~at_peak.to_numpy()[trough:])
recovery_str = (
    f"{(dates[trough + int(back_at_peak[0])] - max_dd_date).days} days" if len(back_at_peak) else "not yet reached"
)

# Recovery points: the curve returns from a drawdown to zero (a new high)
returned = (drawdown.shift(1) < -0.5) & (drawdown >= -0.05)
recovery = df[returned]

source = ColumnDataSource(df.assign(zero=0.0))

W, H = 3200, 1800
p = figure(
    width=W,
    height=H,
    title="drawdown-basic · python · bokeh · anyplot.ai",
    x_axis_label=DATE,
    y_axis_label=DRAWDOWN,
    x_axis_type="datetime",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# HoverTool for the HTML artifact
hover = HoverTool(
    tooltips=[(DATE, f"@{{{DATE}}}{{%F}}"), (DRAWDOWN, f"@{{{DRAWDOWN}}}{{0.2f}}%")],
    formatters={f"@{{{DATE}}}": "datetime"},
)
p.add_tools(hover)

# Filled drawdown area: stronger alpha on the dark page so the fill still registers
fill_alpha = 0.35 if THEME == "light" else 0.55
p.varea(x=DATE, y1="zero", y2=DRAWDOWN, source=source, fill_color=DRAWDOWN_COLOR, fill_alpha=fill_alpha)

# Drawdown line
p.line(x=DATE, y=DRAWDOWN, source=source, line_color=DRAWDOWN_COLOR, line_width=3, legend_label="Drawdown")

# Zero baseline
p.add_layout(Span(location=0, dimension="width", line_color=INK_SOFT, line_width=2))

# Maximum drawdown marker and label
p.scatter(
    x=[max_dd_date],
    y=[max_dd_value],
    size=20,
    color=MAX_DD_COLOR,
    marker="circle",
    legend_label=f"Max DD: {max_dd_value:.1f}%",
)
p.add_layout(
    Label(
        x=max_dd_date,
        y=max_dd_value,
        text=f"  {max_dd_value:.1f}%",
        text_font_size="30pt",
        text_color=MAX_DD_COLOR,
        x_offset=12,
        y_offset=-5,
    )
)

# Recovery (new high) markers on the zero line
if len(recovery):
    p.scatter(
        x=recovery[DATE],
        y=np.zeros(len(recovery)),
        size=24,
        color=RECOVERY_COLOR,
        marker="triangle",
        legend_label="New High",
    )

# Statistics block in a callout box, placed in screen fractions
p.add_layout(
    Label(
        x=0.60 * W,
        y=0.62 * H,
        x_units="screen",
        y_units="screen",
        text=f"Max DD: {max_dd_value:.1f}%\nDuration: {max_dd_duration} days\nRecovery: {recovery_str}",
        text_font_size="28pt",
        text_color=INK,
        text_align="left",
        background_fill_color=ELEVATED_BG,
        background_fill_alpha=0.95,
        border_line_color=INK_SOFT,
        border_line_width=2,
        padding=14,
    )
)

# Font sizes
p.title.text_font_size = "50pt"
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"

# Legend
p.legend.location = "bottom_left"
p.legend.label_text_font_size = "34pt"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT
p.legend.glyph_height = 40
p.legend.glyph_width = 40
p.legend.label_standoff = 16
p.legend.spacing = 12
p.legend.padding = 20

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = "rgba(0,0,0,0)"
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

# Save HTML artifact
output_file(f"plot-{THEME}.html", title="Drawdown Chart")
save(p)

# Screenshot with headless Chrome via CDP clip for exact pixel dimensions
# (export_png uses snap chromedriver which is broken; save_screenshot clips at viewport)
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H + 200}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
screenshot = driver.execute_cdp_cmd(
    "Page.captureScreenshot",
    {"format": "png", "captureBeyondViewport": True, "clip": {"x": 0, "y": 0, "width": W, "height": H, "scale": 1}},
)
driver.quit()
img_bytes = base64.b64decode(screenshot["data"])
with open(f"plot-{THEME}.png", "wb") as f:
    f.write(img_bytes)
