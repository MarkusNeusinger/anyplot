""" anyplot.ai
area-stacked-confidence: Stacked Area Chart with Confidence Bands
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-18
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import Band, ColumnDataSource, HoverTool, Legend
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette - first series is always #009E73
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2"]

# Data - Quarterly energy consumption by source with uncertainty
np.random.seed(42)
quarters = pd.date_range("2020-01-01", periods=24, freq="QE")
n = len(quarters)

# Generate energy consumption data (GWh) with uncertainty
# Solar - growing trend with increasing uncertainty
solar_base = 50 + np.linspace(0, 80, n) + np.random.normal(0, 5, n)
solar_lower = solar_base - (5 + np.linspace(0, 15, n))
solar_upper = solar_base + (5 + np.linspace(0, 15, n))

# Wind - seasonal variation with moderate uncertainty
wind_base = 80 + 20 * np.sin(np.linspace(0, 6 * np.pi, n)) + np.random.normal(0, 3, n)
wind_lower = wind_base - 10
wind_upper = wind_base + 10

# Hydro - stable with low uncertainty
hydro_base = 60 + np.random.normal(0, 2, n)
hydro_lower = hydro_base - 5
hydro_upper = hydro_base + 5

# Stack the values for cumulative display
# First series (Solar) starts at 0
stack1_base = solar_base
stack1_lower = solar_lower
stack1_upper = solar_upper

# Second series (Wind) stacks on top of Solar
stack2_base = stack1_base + wind_base
stack2_lower = stack1_base + wind_lower
stack2_upper = stack1_base + wind_upper

# Third series (Hydro) stacks on top of Wind
stack3_base = stack2_base + hydro_base
stack3_lower = stack2_base + hydro_lower
stack3_upper = stack2_base + hydro_upper

# Create figure with larger dimensions
p = figure(
    width=4800,
    height=2700,
    title="area-stacked-confidence · Python · bokeh · anyplot.ai",
    x_axis_label="Quarter",
    y_axis_label="Energy Consumption (GWh)",
    x_axis_type="datetime",
)

# Create data sources for each stacked area with bands
source_solar = ColumnDataSource(
    data={"x": quarters, "y": stack1_base, "y_lower": stack1_lower, "y_upper": stack1_upper, "base": np.zeros(n)}
)

source_wind = ColumnDataSource(
    data={"x": quarters, "y": stack2_base, "y_lower": stack2_lower, "y_upper": stack2_upper, "base": stack1_base}
)

source_hydro = ColumnDataSource(
    data={"x": quarters, "y": stack3_base, "y_lower": stack3_lower, "y_upper": stack3_upper, "base": stack2_base}
)

# Plot confidence bands (back to front for proper layering)
solar_band = Band(
    base="x",
    lower="y_lower",
    upper="y_upper",
    source=source_solar,
    fill_alpha=0.2,
    fill_color=OKABE_ITO[0],
    line_color=OKABE_ITO[0],
    line_alpha=0.3,
)
p.add_layout(solar_band)

wind_band = Band(
    base="x",
    lower="y_lower",
    upper="y_upper",
    source=source_wind,
    fill_alpha=0.2,
    fill_color=OKABE_ITO[1],
    line_color=OKABE_ITO[1],
    line_alpha=0.3,
)
p.add_layout(wind_band)

hydro_band = Band(
    base="x",
    lower="y_lower",
    upper="y_upper",
    source=source_hydro,
    fill_alpha=0.2,
    fill_color=OKABE_ITO[2],
    line_color=OKABE_ITO[2],
    line_alpha=0.3,
)
p.add_layout(hydro_band)

# Plot stacked areas using varea
r_solar = p.varea(x="x", y1="base", y2="y", source=source_solar, fill_color=OKABE_ITO[0], fill_alpha=0.7)
r_wind = p.varea(x="x", y1="base", y2="y", source=source_wind, fill_color=OKABE_ITO[1], fill_alpha=0.7)
r_hydro = p.varea(x="x", y1="base", y2="y", source=source_hydro, fill_color=OKABE_ITO[2], fill_alpha=0.7)

# Add center lines for each series for better visibility
p.line(x="x", y="y", source=source_solar, line_color=OKABE_ITO[0], line_width=3, line_alpha=0.8)
p.line(x="x", y="y", source=source_wind, line_color=OKABE_ITO[1], line_width=3, line_alpha=0.8)
p.line(x="x", y="y", source=source_hydro, line_color=OKABE_ITO[2], line_width=3, line_alpha=0.8)

# Create legend outside plot area (bottom right)
legend = Legend(
    items=[
        ("Solar (± uncertainty)", [r_solar]),
        ("Wind (± uncertainty)", [r_wind]),
        ("Hydro (± uncertainty)", [r_hydro]),
    ],
    location="bottom_right",
)
legend.click_policy = "hide"
p.add_layout(legend)

# Add hover tool for interactivity
hover = HoverTool(tooltips=[("Date", "@x{%F}"), ("Value", "@y{0,0.0}")], formatters={"@x": "datetime"})
p.add_tools(hover)

# Theme-adaptive styling
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title.text_color = INK
p.title.text_font_size = "28pt"

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

p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT
p.legend.label_text_font_size = "16pt"

# Set y-axis to start at 0
p.y_range.start = 0

# Add padding
p.min_border_left = 100
p.min_border_right = 100
p.min_border_top = 50
p.min_border_bottom = 100

# Save output
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
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
