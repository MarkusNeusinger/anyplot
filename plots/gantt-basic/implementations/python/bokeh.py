"""anyplot.ai
gantt-basic: Basic Gantt Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
"""

import os
import time
from pathlib import Path

import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TASK = "Task"  # role: task
START = "Start"  # role: start
END = "End"  # role: end
CATEGORY = "Phase"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("schedule.csv")
df = pd.DataFrame(
    {
        TASK: [
            "Requirements Analysis",
            "System Design",
            "Database Schema",
            "Backend API",
            "Frontend UI",
            "Integration",
            "Unit Testing",
            "System Testing",
            "User Acceptance",
            "Documentation",
            "Deployment",
            "Training",
        ],
        START: pd.to_datetime(
            [
                "2025-01-06",
                "2025-01-13",
                "2025-01-27",
                "2025-02-03",
                "2025-02-10",
                "2025-03-03",
                "2025-02-17",
                "2025-03-17",
                "2025-03-24",
                "2025-03-10",
                "2025-04-01",
                "2025-04-07",
            ]
        ),
        END: pd.to_datetime(
            [
                "2025-01-17",
                "2025-01-31",
                "2025-02-07",
                "2025-02-28",
                "2025-03-14",
                "2025-03-21",
                "2025-03-14",
                "2025-03-28",
                "2025-04-04",
                "2025-04-04",
                "2025-04-11",
                "2025-04-18",
            ]
        ),
        CATEGORY: [
            "Planning",
            "Planning",
            "Development",
            "Development",
            "Development",
            "Development",
            "Testing",
            "Testing",
            "Testing",
            "Deployment",
            "Deployment",
            "Deployment",
        ],
    }
)

# Plot: reads only df and the constants above
ROW = "row"
df = df.sort_values([START, CATEGORY]).reset_index(drop=True)
df[ROW] = len(df) - 1 - df.index  # first task on top
categories = list(df[CATEGORY].unique())
span = df[END].max() - df[START].min()

title = "gantt-basic · python · bokeh · anyplot.ai"
p = figure(
    width=3200,
    height=1800,
    title=title,
    x_axis_type="datetime",
    x_axis_label="Timeline",
    x_range=Range1d(df[START].min() - span * 0.24, df[END].max() + span * 0.03),
    y_range=Range1d(-0.6, len(df) - 0.4),
    tools="",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=60,
    min_border_top=110,
    min_border_right=60,
)

# One bar per task, one renderer per category so the legend names each color
for i, cat in enumerate(categories):
    rows = ColumnDataSource(df[df[CATEGORY] == cat])
    p.hbar(
        y=ROW,
        left=START,
        right=END,
        height=0.62,
        source=rows,
        fill_color=IMPRINT_PALETTE[i],
        line_color=PAGE_BG,
        line_width=2,
        legend_label=str(cat),
    )

# Task names at the left of each row
p.text(
    x=df[START].min() - span * 0.015,
    y=df[ROW],
    text=df[TASK],
    text_font_size="32pt",
    text_align="right",
    text_baseline="middle",
    text_color=INK,
)

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.xaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None
p.xaxis.formatter.days = "%b %d"
p.xaxis.formatter.months = "%b %d"
p.yaxis.visible = False
p.xgrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.15
p.ygrid.grid_line_color = None
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.legend.title = CATEGORY
p.legend.title_text_font_size = "30pt"
p.legend.title_text_color = INK
p.legend.label_text_font_size = "30pt"
p.legend.label_text_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.95
p.legend.border_line_color = INK_SOFT
p.legend.location = "top_right"
p.legend.glyph_height = 40
p.legend.glyph_width = 50
p.legend.spacing = 14
p.legend.padding = 20
p.legend.margin = 30

# Save HTML and screenshot it with headless Chrome
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
