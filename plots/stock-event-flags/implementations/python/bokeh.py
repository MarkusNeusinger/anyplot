"""anyplot.ai
stock-event-flags: Stock Chart with Event Flags
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-27
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

ANYPLOT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = ANYPLOT_PALETTE[0]  # price line uses position 1

# Data — 180 trading days of synthetic stock prices via geometric Brownian motion
np.random.seed(42)
n_days = 180
dates = pd.bdate_range(start=pd.Timestamp("2024-01-02"), periods=n_days)

initial_price = 150.0
daily_returns = np.random.normal(0.0005, 0.018, n_days)
close_prices = initial_price * np.cumprod(1 + daily_returns)

df = pd.DataFrame({"date": dates, "close": close_prices})

events = [
    {"date": dates[25], "type": "earnings", "label": "Q4 Earnings"},
    {"date": dates[50], "type": "dividend", "label": "Dividend $0.50"},
    {"date": dates[75], "type": "news", "label": "Product Launch"},
    {"date": dates[95], "type": "earnings", "label": "Q1 Earnings"},
    {"date": dates[110], "type": "split", "label": "2:1 Split"},
    {"date": dates[140], "type": "dividend", "label": "Dividend $0.55"},
    {"date": dates[160], "type": "news", "label": "Partnership"},
]
events_df = pd.DataFrame(events)

# Event styling — positions 2–5 (position 1 is the price line)
event_colors = {
    "earnings": ANYPLOT_PALETTE[1],  # lavender
    "dividend": ANYPLOT_PALETTE[2],  # blue
    "split": ANYPLOT_PALETTE[3],  # ochre
    "news": ANYPLOT_PALETTE[4],  # matte red
}
event_markers = {"earnings": "triangle", "dividend": "circle", "split": "square", "news": "diamond"}

# Plot
title_str = "stock-event-flags · python · bokeh · anyplot.ai"

p = figure(
    width=3200,
    height=1800,
    x_axis_type="datetime",
    title=title_str,
    x_axis_label="Date",
    y_axis_label="Price (USD)",
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
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.15
p.ygrid.grid_line_alpha = 0.15

# Price line
source = ColumnDataSource(df)
price_line = p.line(x="date", y="close", source=source, line_width=4, line_color=BRAND, alpha=0.9)

# Event flags — vertical connector lines + markers + labels
legend_renderers = {}
all_event_renderers = []
price_range = close_prices.max() - close_prices.min()

# Major events (earnings, split) get slightly larger offsets for visual hierarchy
major_events = {"earnings", "split"}

for i, event in events_df.iterrows():
    event_date = event["date"]
    event_type = event["type"]
    event_label = event["label"]
    color = event_colors[event_type]
    marker = event_markers[event_type]

    idx = df[df["date"] == event_date].index[0]
    event_price = df.loc[idx, "close"]

    offset_dir = 1 if i % 2 == 0 else -1
    # Major events flagged higher to create visual hierarchy
    offset_factor = 0.20 if event_type in major_events else 0.13
    flag_y = event_price + offset_dir * price_range * offset_factor

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
            "event_type": [event_type.capitalize()],
            "event_label": [event_label],
            "price": [f"${event_price:.2f}"],
        }
    )
    marker_size = 28 if event_type in major_events else 22
    renderer = p.scatter(
        x="x",
        y="y",
        source=flag_source,
        size=marker_size,
        color=color,
        alpha=0.9,
        line_color=PAGE_BG,
        line_width=2,
        marker=marker,
    )

    all_event_renderers.append(renderer)

    if event_type not in legend_renderers:
        legend_renderers[event_type] = renderer

    label = Label(
        x=event_date,
        y=flag_y,
        text=event_label,
        text_font_size="26pt",
        text_color=color,
        x_offset=22,
        y_offset=8 if offset_dir > 0 else -40,
        text_font_style="bold",
    )
    p.add_layout(label)

# HoverTool on event markers — reveals full event details in the HTML artifact
hover = HoverTool(
    renderers=all_event_renderers, tooltips=[("Type", "@event_type"), ("Event", "@event_label"), ("Price", "@price")]
)
p.add_tools(hover)

# Legend
legend_items = [LegendItem(label="Close Price", renderers=[price_line])]
for event_type, renderer in legend_renderers.items():
    legend_items.append(LegendItem(label=event_type.capitalize(), renderers=[renderer]))

legend = Legend(
    items=legend_items,
    location="top_left",
    label_text_font_size="34pt",
    label_text_color=INK_SOFT,
    background_fill_color=ELEVATED_BG,
    border_line_color=INK_SOFT,
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
time.sleep(3)
screenshot_b64 = driver.execute_cdp_cmd(
    "Page.captureScreenshot", {"format": "png", "fromSurface": True, "captureBeyondViewport": False}
)["data"]
with open(f"plot-{THEME}.png", "wb") as f:
    f.write(base64.b64decode(screenshot_b64))
driver.quit()
