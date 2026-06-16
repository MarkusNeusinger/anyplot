""" anyplot.ai
area-cumulative-flow: Cumulative Flow Diagram for Workflow Analytics
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 87/100 | Created: 2026-05-07
"""

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
from bokeh.models import ColumnDataSource, DatetimeTickFormatter, Legend, LegendItem
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette — first series always #009E73
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data — 90-day Kanban board for a software delivery team
np.random.seed(42)
days = 90
dates = pd.date_range("2024-01-15", periods=days, freq="D")

# Items enter the backlog at a Poisson rate (~3/day) starting from 15 committed items
daily_intake = np.random.poisson(3, days)
backlog_cum = np.maximum.accumulate(np.cumsum(daily_intake) + 15)

# Each downstream stage lags the upstream by a delay and has a throughput rate
analysis_cum = np.zeros(days, dtype=int)
analysis_cum[5:] = (backlog_cum[:-5] * 0.88).astype(int)
analysis_cum = np.maximum.accumulate(analysis_cum)

dev_cum = np.zeros(days, dtype=int)
dev_cum[7:] = (analysis_cum[:-7] * 0.92).astype(int)
dev_cum = np.maximum.accumulate(dev_cum)

testing_cum = np.zeros(days, dtype=int)
testing_cum[5:] = (dev_cum[:-5] * 0.95).astype(int)
testing_cum = np.maximum.accumulate(testing_cum)

done_cum = np.zeros(days, dtype=int)
done_cum[4:] = (testing_cum[:-4] * 0.97).astype(int)
done_cum = np.maximum.accumulate(done_cum)

# Band heights = WIP in each stage (differences between consecutive cumulative boundaries)
source = ColumnDataSource(
    data={
        "date": dates,
        "done": done_cum.astype(float),
        "testing": np.maximum(0, testing_cum - done_cum).astype(float),
        "development": np.maximum(0, dev_cum - testing_cum).astype(float),
        "analysis": np.maximum(0, analysis_cum - dev_cum).astype(float),
        "backlog": np.maximum(0, backlog_cum - analysis_cum).astype(float),
    }
)

stages = ["done", "testing", "development", "analysis", "backlog"]
labels = ["Done", "Testing", "Development", "Analysis", "Backlog"]

# Plot
p = figure(
    width=4800,
    height=2700,
    x_axis_type="datetime",
    title="area-cumulative-flow · bokeh · anyplot.ai",
    tools="",
    toolbar_location=None,
)

# Stacked areas — each color corresponds to the matching stacker
renderers = p.varea_stack(stackers=stages, x="date", color=IMPRINT, alpha=0.82, source=source)

# Subtle boundary lines at each stage transition
cum_vals = np.zeros(days)
for stage in stages:
    cum_vals = cum_vals + source.data[stage]
    p.line(x=dates, y=cum_vals, line_width=1.5, line_color=INK_SOFT, line_alpha=0.40)

# Legend — top to bottom: Backlog → Done (matches visual band order)
legend_items = [LegendItem(label=labels[i], renderers=[renderers[i]]) for i in range(len(stages) - 1, -1, -1)]
legend = Legend(
    items=legend_items,
    location="top_left",
    background_fill_color=ELEVATED_BG,
    border_line_color=INK_SOFT,
    label_text_color=INK_SOFT,
    label_text_font_size="18pt",
    padding=20,
    spacing=10,
)
p.add_layout(legend)

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title.text_color = INK
p.title.text_font_size = "28pt"
p.title.text_font_style = "normal"

p.xaxis.axis_label = "Date"
p.yaxis.axis_label = "Cumulative Items"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

p.xaxis.formatter = DatetimeTickFormatter(days="%b %d", months="%b %Y")

# Save HTML then screenshot with headless Chrome
output_file(f"plot-{THEME}.html")
save(p)

W, H = 4800, 2700
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
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
