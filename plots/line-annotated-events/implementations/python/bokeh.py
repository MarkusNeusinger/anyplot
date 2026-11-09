"""anyplot.ai
line-annotated-events: Annotated Line Plot with Event Markers
Library: bokeh 3.10.1 | Python 3.14.10
Quality: 88/100 | Updated: 2026-11-09
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Range1d, Span
from bokeh.plotting import figure
from bokeh.resources import CDN
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 for the data line, position 2 for the event markers
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
VALUE = "Active Users (thousands)"  # role: value
EVENT_DATE = "Event date"  # role: event_date
EVENT_LABEL = "Event"  # role: event_label

# Data: replace this block with your own table, for example df = pd.read_csv("active_users.csv")
np.random.seed(42)
dates = pd.date_range("2024-01-01", periods=365, freq="D")
base_trend = np.linspace(100, 180, 365)
seasonal = 15 * np.sin(np.arange(365) * 2 * np.pi / 365)
noise = np.cumsum(np.random.randn(365) * 0.8)
series = pd.DataFrame({DATE: dates, VALUE: base_trend + seasonal + noise})
events = pd.DataFrame(
    {
        EVENT_DATE: pd.to_datetime(["2024-02-15", "2024-05-01", "2024-07-20", "2024-09-10", "2024-11-25"]),
        EVENT_LABEL: ["Pricing Change", "Feature Update", "Server Upgrade", "API v2 Release", "Mobile App Launch"],
    }
)
df = pd.concat([series, events], ignore_index=True)

# Plot: reads only df and the constants above
line_rows = df[df[DATE].notna()].sort_values(DATE)
event_rows = df[df[EVENT_DATE].notna()].sort_values(EVENT_DATE)
x_num = line_rows[DATE].astype("int64").to_numpy()
y_vals = line_rows[VALUE].astype(float).to_numpy()
valid = ~np.isnan(y_vals)
event_values = np.interp(event_rows[EVENT_DATE].astype("int64").to_numpy(), x_num[valid], y_vals[valid])

y_min, y_max = np.nanmin(y_vals), np.nanmax(y_vals)
y_span = y_max - y_min
label_tiers = [y_max + 0.10 * y_span, y_max + 0.24 * y_span]  # two alternating heights above the data
x_start, x_end = line_rows[DATE].min(), line_rows[DATE].max()

title = "line-annotated-events · python · bokeh · anyplot.ai"
p = figure(
    width=3200,
    height=1800,
    title=title,
    x_axis_type="datetime",
    x_axis_label=DATE,
    y_axis_label=VALUE,
    y_range=Range1d(y_min - 0.06 * y_span, y_max + 0.36 * y_span),
    x_range=Range1d(x_start, x_end),
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=60,
)

line_source = ColumnDataSource(line_rows[[DATE, VALUE]])
data_line = p.line(x=DATE, y=VALUE, source=line_source, line_width=5, color=IMPRINT_PALETTE[0])
p.add_tools(
    HoverTool(
        renderers=[data_line],
        tooltips=[(DATE, f"@{{{DATE}}}{{%F}}"), (VALUE, f"@{{{VALUE}}}{{0.0}}")],
        formatters={f"@{{{DATE}}}": "datetime"},
        mode="vline",
    )
)

# Events: dashed vertical span, a dot where it meets the line, and a label in an alternating tier
event_color = IMPRINT_PALETTE[1]
for i, (event_date, label) in enumerate(zip(event_rows[EVENT_DATE], event_rows[EVENT_LABEL], strict=True)):
    p.add_layout(
        Span(location=event_date, dimension="height", line_color=event_color, line_width=4, line_dash="dashed")
    )
    near_right = (event_date - x_start) > 0.8 * (x_end - x_start)
    p.add_layout(
        Label(
            x=event_date,
            y=label_tiers[i % len(label_tiers)],
            text=str(label),
            text_font_size="30pt",
            text_font_style="bold",
            text_color=INK,
            text_align="right" if near_right else "left",
            text_baseline="middle",
            x_offset=-16 if near_right else 16,
            background_fill_color=PAGE_BG,
            background_fill_alpha=0.85,
        )
    )
p.scatter(x=event_rows[EVENT_DATE], y=event_values, size=26, color=event_color, line_color=PAGE_BG, line_width=4)

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.12

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

# Save
output_file(f"plot-{THEME}.html")
save(p, resources=CDN, title=title)

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
