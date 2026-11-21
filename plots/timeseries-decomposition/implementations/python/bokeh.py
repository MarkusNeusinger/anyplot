"""anyplot.ai
timeseries-decomposition: Time Series Decomposition Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-14
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, DataRange1d, Label, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from statsmodels.tsa.seasonal import seasonal_decompose


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per component in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
PERIOD = 12  # observations per seasonal cycle (monthly data, annual cycle)

# Columns: set these to your table's column names
DATE = "Date"  # role: date
VALUE = "Passengers (thousands)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("passengers.csv", parse_dates=["Date"])
np.random.seed(42)
n_months = 120  # 10 years of monthly observations
months = np.arange(n_months)
df = pd.DataFrame(
    {
        DATE: pd.date_range(start="2018-01-01", periods=n_months, freq="MS"),
        VALUE: np.linspace(100, 250, n_months)
        + 30 * np.sin(2 * np.pi * months / 12)
        + np.random.normal(0, 10, n_months),
    }
)

# Plot: reads only df and the constants above
series = df.set_index(DATE)[VALUE].interpolate(limit_direction="both")  # the decomposition needs gap-free input
decomposition = seasonal_decompose(series, model="additive", period=min(PERIOD, len(series) // 2))
panels = [
    ("Original", df[VALUE].to_numpy()),
    ("Trend", decomposition.trend.to_numpy()),
    ("Seasonal", decomposition.seasonal.to_numpy()),
    ("Residual", decomposition.resid.to_numpy()),
]

W, H = 3200, 1800
heights = [480, 410, 410, H - 480 - 410 - 410]
shared_range = DataRange1d()  # one time axis for all panels
figures = []
for i, ((name, values), height) in enumerate(zip(panels, heights, strict=True)):
    first, last = i == 0, i == len(panels) - 1
    p = figure(
        width=W,
        height=height,
        x_axis_type="datetime",
        toolbar_location=None,
        title="timeseries-decomposition · python · bokeh · anyplot.ai" if first else None,
        min_border_left=170,
        min_border_right=60,
        min_border_top=120 if first else 20,
        min_border_bottom=130 if last else 10,
        x_range=shared_range,
    )
    low, high = np.nanmin(values), np.nanmax(values)
    p.y_range = Range1d(low - 0.06 * (high - low), high + 0.28 * (high - low))  # headroom for the component name

    p.background_fill_color = PAGE_BG
    p.border_fill_color = PAGE_BG
    p.outline_line_color = INK_SOFT

    if first:
        p.title.text_color = INK
        p.title.text_font_size = "44pt"
        p.title.text_font_style = "bold"

    p.yaxis.axis_label = VALUE
    p.yaxis.axis_label_text_color = INK
    p.yaxis.axis_label_text_font_size = "20pt"
    p.yaxis.axis_label_text_font_style = "normal"
    p.yaxis.major_label_text_color = INK_SOFT
    p.yaxis.major_label_text_font_size = "22pt"
    p.xaxis.major_label_text_color = INK_SOFT
    p.xaxis.major_label_text_font_size = "24pt"
    p.xaxis.visible = last
    p.xaxis.axis_label = DATE
    p.xaxis.axis_label_text_color = INK
    p.xaxis.axis_label_text_font_size = "26pt"
    p.xaxis.axis_label_text_font_style = "normal"
    for axis in (p.xaxis, p.yaxis):
        axis.axis_line_color = INK_SOFT
        axis.major_tick_line_color = INK_SOFT
        axis.minor_tick_line_color = None

    p.xgrid.grid_line_color = INK
    p.xgrid.grid_line_alpha = 0.08
    p.ygrid.grid_line_color = INK
    p.ygrid.grid_line_alpha = 0.12

    source = ColumnDataSource({DATE: df[DATE], name: values})
    p.line(DATE, name, source=source, line_width=4, color=IMPRINT_PALETTE[i])

    # Component name, pinned to the top-left corner of the panel
    p.add_layout(
        Label(
            x=24,
            y=height - p.min_border_top - 54,
            x_units="screen",
            y_units="screen",
            text=name,
            text_color=INK,
            text_font_size="30pt",
            text_font_style="bold",
        )
    )
    figures.append(p)

layout = column(*figures, spacing=0)

# Save interactive HTML
output_file(f"plot-{THEME}.html")
save(layout)

# Screenshot with headless Chrome using Selenium
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
time.sleep(3)  # Let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
