"""anyplot.ai
bar-error: Bar Chart with Error Bars
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-10
"""

import os
import time
from pathlib import Path

import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Label, TeeHead, Whisker
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
CATEGORY = "Product Category"  # role: category
REVENUE = "Quarterly Revenue ($ millions)"  # role: value
SD = "Standard deviation ($ millions)"  # role: error

# Data: replace this block with your own table, for example df = pd.read_csv("revenue.csv")
df = pd.DataFrame(
    {
        CATEGORY: ["Electronics", "Clothing", "Home & Garden", "Sports", "Books"],
        REVENUE: [85.2, 62.8, 48.5, 71.3, 35.7],
        SD: [8.5, 5.2, 6.8, 9.1, 4.2],
    }
)

# Plot: reads only df and the constants above
UPPER, LOWER = "upper", "lower"
df = df.sort_values(REVENUE, ascending=False).reset_index(drop=True)
df[UPPER] = df[REVENUE] + df[SD]
df[LOWER] = df[REVENUE] - df[SD]
source = ColumnDataSource(df)

p = figure(
    x_range=list(df[CATEGORY]),
    width=3200,
    height=1800,
    title="bar-error · python · bokeh · anyplot.ai",
    x_axis_label=CATEGORY,
    y_axis_label=REVENUE,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

p.vbar(
    x=CATEGORY,
    top=REVENUE,
    width=0.6,
    source=source,
    fill_color=IMPRINT_PALETTE[0],
    line_color=IMPRINT_PALETTE[0],
    line_width=3,
    fill_alpha=0.85,
)

whisker = Whisker(
    source=source,
    base=CATEGORY,
    upper=UPPER,
    lower=LOWER,
    line_color=INK,
    line_width=5,
    level="overlay",
    upper_head=TeeHead(size=36, line_color=INK, line_width=5),
    lower_head=TeeHead(size=36, line_color=INK, line_width=5),
)
p.add_layout(whisker)

# Annotation naming what the error bars show
p.add_layout(
    Label(
        x=2930,
        y=1470,
        x_units="screen",
        y_units="screen",
        text_align="right",
        text="Error bars: ±1 standard deviation",
        text_font_size="28pt",
        text_color=INK_SOFT,
        text_font_style="italic",
    )
)

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2

p.xgrid.visible = False
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.15
p.ygrid.grid_line_width = 1

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.y_range.start = 0
p.y_range.end = df[UPPER].max() * 1.12

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
