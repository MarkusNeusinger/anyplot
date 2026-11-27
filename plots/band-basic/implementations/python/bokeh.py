"""anyplot.ai
band-basic: Basic Band Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-29
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (Imprint palette — see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
HOUR = "Hour of Day"  # role: x
IRRADIANCE = "Solar Irradiance (W/m²)"  # role: y_center
LOWER = "Lower 95% bound (W/m²)"  # role: y_lower
UPPER = "Upper 95% bound (W/m²)"  # role: y_upper

# Data: replace this block with your own table, for example df = pd.read_csv("forecast.csv")
np.random.seed(42)
hours = np.linspace(6, 20, 120)  # 6 AM to 8 PM
irradiance = 850 * np.exp(-0.5 * ((hours - 13.0) / 2.8) ** 2) + 50

# Uncertainty tight at midday (clear sky), widens in afternoon (convective clouds)
uncertainty = 15 + 8 * np.abs(hours - 13.0) + 45 * np.clip((hours - 15) / 2, 0, 1) ** 1.5
df = pd.DataFrame(
    {
        HOUR: hours,
        IRRADIANCE: irradiance,
        LOWER: np.maximum(irradiance - 1.96 * uncertainty, 0),
        UPPER: irradiance + 1.96 * uncertainty,
    }
)

# Plot: reads only df and the constants above
source = ColumnDataSource(df)
title = "Solar Irradiance Forecast · band-basic · python · bokeh · anyplot.ai"

p = figure(
    width=3200,
    height=1800,
    title=title,
    x_axis_label=HOUR,
    y_axis_label=IRRADIANCE,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Confidence interval band — first series → Imprint position 1
# Higher alpha in dark theme: alpha=0.25 on #1A1A17 composites to near-invisible forest-green
band_alpha = 0.38 if THEME == "dark" else 0.25
p.varea(
    x=HOUR,
    y1=LOWER,
    y2=UPPER,
    source=source,
    fill_color=IMPRINT_PALETTE[0],
    fill_alpha=band_alpha,
    legend_label="95% Confidence Interval",
)

# Forecast mean line — second series → Imprint position 2
p.line(x=HOUR, y=IRRADIANCE, source=source, line_color=IMPRINT_PALETTE[1], line_width=6, legend_label="Forecast Mean")

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.title.text_font_size = "50pt"
p.title.text_font_style = "normal"
p.title.text_color = INK

p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.axis_label_text_font_style = "normal"
p.yaxis.axis_label_text_font_style = "normal"

p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.axis_line_width = 1
p.yaxis.axis_line_width = 1

p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Y-grid only (style guide: y-axis grid for line charts)
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.15

# Legend
p.legend.label_text_font_size = "34pt"
p.legend.label_text_color = INK_SOFT
p.legend.location = "top_right"
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.85
p.legend.border_line_color = INK_SOFT
p.legend.glyph_width = 60
p.legend.glyph_height = 40
p.legend.padding = 20
p.legend.spacing = 12

# Save HTML artifact
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Selenium — export_png not used (snap driver incompatible)
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
# CDP override pins the viewport to exactly W×H at DPR=1, avoiding
# headless-Chrome viewport-vs-window-size discrepancies
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
# Paint the page in the theme color so the anti-aliased canvas edge shows no white line
driver.execute_script(
    "document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
