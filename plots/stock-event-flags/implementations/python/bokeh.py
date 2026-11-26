""" anyplot.ai
stock-event-flags: Stock Chart with Event Flags
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-26
"""

import base64
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Legend, LegendItem
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, position 1 is the price line
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

# Constants
EVENT_MARKERS = {"earnings": "triangle", "dividend": "circle", "split": "square", "news": "diamond"}
EVENT_COLORS = {"earnings": 1, "dividend": 2, "split": 3, "news": 4}  # Imprint positions 2-5
MARKER_CYCLE = ["triangle", "circle", "square", "diamond", "hex", "inverted_triangle"]
MAJOR_EVENT_TYPES = {"earnings", "split"}  # drawn larger and higher than the minor ones

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Price (USD)"  # role: close
EVENT_DATE = "Event date"  # role: event_date
EVENT_TYPE = "Event type"  # role: event_type
EVENT_LABEL = "Event"  # role: event_label

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv", parse_dates=[DATE])
# Event rows carry an event type and label; all other trading days leave both empty.
np.random.seed(42)
n_days = 180
dates = pd.bdate_range(start=pd.Timestamp("2024-01-02"), periods=n_days)
daily_returns = np.random.normal(0.0005, 0.018, n_days)
close_prices = 150.0 * np.cumprod(1 + daily_returns)
event_rows = {
    25: ("earnings", "Q4 Earnings"),
    50: ("dividend", "Dividend $0.50"),
    75: ("news", "Product Launch"),
    95: ("earnings", "Q1 Earnings"),
    110: ("split", "2:1 Split"),
    140: ("dividend", "Dividend $0.55"),
    160: ("news", "Partnership"),
}
df = pd.DataFrame(
    {
        DATE: dates,
        CLOSE: close_prices,
        EVENT_DATE: [dates[i] if i in event_rows else pd.NaT for i in range(n_days)],
        EVENT_TYPE: [event_rows.get(i, (None, None))[0] for i in range(n_days)],
        EVENT_LABEL: [event_rows.get(i, (None, None))[1] for i in range(n_days)],
    }
)

# Plot
events = df.dropna(subset=[EVENT_DATE, EVENT_TYPE, EVENT_LABEL]).reset_index(drop=True)
event_types = list(dict.fromkeys(events[EVENT_TYPE]))
price_range = df[CLOSE].max() - df[CLOSE].min()

p = figure(
    width=3200,
    height=1800,
    x_axis_type="datetime",
    title="stock-event-flags · python · bokeh · anyplot.ai",
    x_axis_label=DATE,
    y_axis_label=CLOSE,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None  # L-shaped frame: only left/bottom axis lines visible

p.title.text_color = INK
p.title.text_font_size = "50pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xgrid.grid_line_color = None  # horizontal price guides only
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.15

# Price line
source = ColumnDataSource(df)
price_line = p.line(x=DATE, y=CLOSE, source=source, line_width=4, line_color=BRAND, alpha=0.9)

# Event flags: vertical connector + marker + label per event
legend_renderers = {}
all_event_renderers = []

for i, event in events.iterrows():
    event_date = event[EVENT_DATE]
    event_type = event[EVENT_TYPE]
    type_index = event_types.index(event_type)
    color = IMPRINT_PALETTE[EVENT_COLORS.get(event_type, 5 + type_index) % len(IMPRINT_PALETTE)]
    marker = EVENT_MARKERS.get(event_type, MARKER_CYCLE[type_index % len(MARKER_CYCLE)])
    is_major = event_type in MAJOR_EVENT_TYPES

    event_price = event[CLOSE]
    offset_dir = 1 if i % 2 == 0 else -1
    flag_y = event_price + offset_dir * price_range * (0.20 if is_major else 0.13)

    p.segment(
        x0=[event_date],
        y0=[event_price],
        x1=[event_date],
        y1=[flag_y],
        line_color=color,
        line_dash="dashed",
        line_width=3,
        alpha=0.7,
    )

    flag_source = ColumnDataSource(
        data={
            "x": [event_date],
            "y": [flag_y],
            EVENT_TYPE: [str(event_type).capitalize()],
            EVENT_LABEL: [event[EVENT_LABEL]],
            CLOSE: [event_price],
        }
    )
    renderer = p.scatter(
        x="x",
        y="y",
        source=flag_source,
        size=28 if is_major else 22,
        color=color,
        alpha=0.9,
        line_color=PAGE_BG,
        line_width=2,
        marker=marker,
    )
    all_event_renderers.append(renderer)
    legend_renderers.setdefault(event_type, renderer)

    p.add_layout(
        Label(
            x=event_date,
            y=flag_y,
            text=event[EVENT_LABEL],
            text_font_size="26pt",
            text_color=color,
            x_offset=22,
            y_offset=8 if offset_dir > 0 else -40,
            text_font_style="bold",
        )
    )

# HoverTool on event markers: full event details in the HTML artifact
hover = HoverTool(
    renderers=all_event_renderers,
    tooltips=[
        ("Type", f"@{{{EVENT_TYPE}}}"),
        (EVENT_LABEL, f"@{{{EVENT_LABEL}}}"),
        ("Price", f"@{{{CLOSE}}}{{$0.00}}"),
    ],
)
p.add_tools(hover)

# Legend
legend_items = [LegendItem(label="Close Price", renderers=[price_line])]
for event_type, renderer in legend_renderers.items():
    legend_items.append(LegendItem(label=str(event_type).capitalize(), renderers=[renderer]))

legend = Legend(
    items=legend_items,
    location="bottom_left",
    label_text_font_size="34pt",
    label_text_color=INK_SOFT,
    background_fill_color=ELEVATED_BG,
    border_line_color=INK_SOFT,
    glyph_width=64,
    glyph_height=48,
)
p.add_layout(legend)

# Save HTML artifact
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome (Selenium 4 / Selenium Manager)
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
# Force exact viewport via CDP to override any OS/browser chrome overhead
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
# Paint the page in the theme color so the anti-aliased canvas edge shows no white line
driver.execute_script(
    "document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG
)
time.sleep(3)
screenshot_b64 = driver.execute_cdp_cmd(
    "Page.captureScreenshot", {"format": "png", "fromSurface": True, "captureBeyondViewport": False}
)["data"]
with open(f"plot-{THEME}.png", "wb") as f:
    f.write(base64.b64decode(screenshot_b64))
driver.quit()
