"""anyplot.ai
line-confidence: Line Plot with Confidence Interval
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-09
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Legend
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: single series, line and band share position 1
BRAND = "#009E73"

# Columns: set these to your table's column names
TIME = "Time (units)"  # role: x
PREDICTION = "Predicted Value"  # role: y
LOWER = "Lower bound (95% CI)"  # role: y_lower
UPPER = "Upper bound (95% CI)"  # role: y_upper

# Data: replace this block with your own table, for example df = pd.read_csv("forecast.csv")
np.random.seed(42)
time_points = np.linspace(0, 10, 50)
y_true = 2 + 0.5 * time_points + 0.1 * time_points**2
prediction = y_true + np.random.normal(0, 0.5, len(time_points))
uncertainty = 0.8 + 0.15 * time_points  # interval widens over the prediction horizon
df = pd.DataFrame(
    {
        TIME: time_points,
        PREDICTION: prediction,
        LOWER: prediction - 1.96 * uncertainty,
        UPPER: prediction + 1.96 * uncertainty,
    }
)

# Plot: reads only df and the constants above
df = df.sort_values(TIME)
source = ColumnDataSource(df)

p = figure(
    width=3200,
    height=1800,
    title="line-confidence · python · bokeh · anyplot.ai",
    x_axis_label=TIME,
    y_axis_label=PREDICTION,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=60,
)

# Band first so the line draws on top of it
band = p.varea(x=TIME, y1=LOWER, y2=UPPER, source=source, fill_color=BRAND, fill_alpha=0.3)
line = p.line(x=TIME, y=PREDICTION, source=source, line_color=BRAND, line_width=5)

p.add_tools(
    HoverTool(
        renderers=[line],
        tooltips=[
            (TIME, f"@{{{TIME}}}{{0.00}}"),
            (PREDICTION, f"@{{{PREDICTION}}}{{0.00}}"),
            ("95% CI", f"@{{{LOWER}}}{{0.00}} – @{{{UPPER}}}{{0.00}}"),
        ],
    )
)

legend = Legend(items=[("Prediction", [line]), ("95% confidence interval", [band])], location="top_left")
legend.label_text_font_size = "34pt"
legend.glyph_height = 40
legend.glyph_width = 60
legend.spacing = 16
legend.padding = 28
legend.margin = 30
legend.background_fill_color = ELEVATED_BG
legend.background_fill_alpha = 0.9
legend.border_line_color = INK_SOFT
legend.label_text_color = INK_SOFT
p.add_layout(legend)

# Style
p.title.text_font_size = "50pt"
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"

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
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.15
p.ygrid.grid_line_alpha = 0.15

# Save: interactive HTML, then a PNG screenshot through headless Chrome
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
time.sleep(3)  # let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
