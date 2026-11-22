"""anyplot.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: bokeh 3.10.2 | Python 3.13
Quality: pending | Updated: 2026-11-22
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Legend, Range1d, Span
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

# Columns: set these to your table's column names
DATE = "Date"  # role: date
ACTUAL = "Actual"  # role: actual
FORECAST = "Forecast"  # role: forecast
LOWER_80 = "Lower 80%"  # role: lower_80
UPPER_80 = "Upper 80%"  # role: upper_80
LOWER_95 = "Lower 95%"  # role: lower_95
UPPER_95 = "Upper 95%"  # role: upper_95
SALES_LABEL = "Sales (thousands)"

# Data: replace this block with your own table, for example df = pd.read_csv("forecast.csv")
# Monthly product sales: 36 months of history, then a 12-month forecast that starts at the last observation
rng = np.random.default_rng(42)
n_hist, n_fc = 36, 12
dates = pd.date_range("2022-01-01", periods=n_hist + n_fc, freq="MS")
actual = np.linspace(80, 120, n_hist) + 15 * np.sin(np.linspace(0, 6 * np.pi, n_hist)) + rng.normal(0, 5, n_hist)
trend_fc = np.linspace(120, 135, n_fc)
seasonal_fc = 15 * np.sin(np.linspace(6 * np.pi, 8 * np.pi, n_fc))
forecast = np.concatenate([[actual[-1]], trend_fc + seasonal_fc])
half_80 = np.concatenate([[0], np.linspace(5, 15, n_fc)])
half_95 = np.concatenate([[0], np.linspace(8, 25, n_fc)])
df = pd.DataFrame(
    {
        DATE: dates[n_hist - 1 :],
        FORECAST: forecast,
        LOWER_80: forecast - half_80,
        UPPER_80: forecast + half_80,
        LOWER_95: forecast - half_95,
        UPPER_95: forecast + half_95,
    }
)
df = pd.concat([pd.DataFrame({DATE: dates[:n_hist], ACTUAL: actual}), df], ignore_index=True)

# Plot: reads only df and the constants above
history = df[df[ACTUAL].notna()]
future = df[df[FORECAST].notna()]
split_ms = history[DATE].max().timestamp() * 1000
band_top = df[[ACTUAL, UPPER_95]].max().max()
band_bottom = df[[ACTUAL, LOWER_95]].min().min()
pad = (band_top - band_bottom) * 0.08
x_end = df[DATE].max() + pd.DateOffset(months=2)

p = figure(
    width=3200,
    height=1800,
    title="timeseries-forecast-uncertainty · python · bokeh · anyplot.ai",
    x_axis_label=DATE,
    y_axis_label=SALES_LABEL,
    x_axis_type="datetime",
    x_range=Range1d(df[DATE].min().timestamp() * 1000, x_end.timestamp() * 1000),
    y_range=Range1d(band_bottom - pad, band_top + 2.5 * pad),
    toolbar_location=None,
    min_border_bottom=180,
    min_border_left=200,
    min_border_top=120,
    min_border_right=60,
)

# Style
p.title.text_font_size = "56pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_font_style = "normal"
p.yaxis.axis_label_text_font_style = "normal"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "36pt"
p.yaxis.major_label_text_font_size = "36pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK_SOFT
p.ygrid.grid_line_alpha = 0.10
p.ygrid.grid_line_width = 1

# Nested confidence bands: wider 95% band first, narrower 80% band on top
future_src = ColumnDataSource(future)
band_95 = p.varea(x=DATE, y1=LOWER_95, y2=UPPER_95, source=future_src, fill_color=IMPRINT_PALETTE[1], fill_alpha=0.18)
band_80 = p.varea(x=DATE, y1=LOWER_80, y2=UPPER_80, source=future_src, fill_color=IMPRINT_PALETTE[1], fill_alpha=0.38)

# Historical line (solid) and forecast line (dashed)
hist_line = p.line(x=DATE, y=ACTUAL, source=ColumnDataSource(history), line_color=IMPRINT_PALETTE[0], line_width=4)
forecast_line = p.line(
    x=DATE, y=FORECAST, source=future_src, line_color=IMPRINT_PALETTE[1], line_width=5, line_dash="dashed"
)

# Forecast start marker and label
p.add_layout(Span(location=split_ms, dimension="height", line_color=INK_SOFT, line_width=2, line_dash="dashed"))
p.add_layout(
    Label(
        x=split_ms, y=band_top + 1.2 * pad, text="Forecast ▶", text_color=INK_SOFT, text_font_size="32pt", x_offset=20
    )
)

# Hover tooltips
p.add_tools(
    HoverTool(
        renderers=[hist_line],
        tooltips=[(DATE, f"@{{{DATE}}}{{%b %Y}}"), (ACTUAL, f"@{{{ACTUAL}}}{{0.0}}k")],
        formatters={f"@{{{DATE}}}": "datetime"},
        mode="vline",
    )
)
p.add_tools(
    HoverTool(
        renderers=[forecast_line],
        tooltips=[
            (DATE, f"@{{{DATE}}}{{%b %Y}}"),
            (FORECAST, f"@{{{FORECAST}}}{{0.0}}k"),
            ("80% CI", f"[@{{{LOWER_80}}}{{0.0}}, @{{{UPPER_80}}}{{0.0}}]k"),
            ("95% CI", f"[@{{{LOWER_95}}}{{0.0}}, @{{{UPPER_95}}}{{0.0}}]k"),
        ],
        formatters={f"@{{{DATE}}}": "datetime"},
        mode="vline",
    )
)

# Legend
legend = Legend(
    items=[
        ("Historical Data", [hist_line]),
        (FORECAST, [forecast_line]),
        ("80% Confidence Interval", [band_80]),
        ("95% Confidence Interval", [band_95]),
    ],
    location="top_left",
    label_text_font_size="36pt",
    label_text_color=INK_SOFT,
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.95,
    border_line_color=INK_SOFT,
    border_line_width=2,
    padding=30,
    spacing=16,
    glyph_width=60,
    glyph_height=40,
)
p.add_layout(legend)

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
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
