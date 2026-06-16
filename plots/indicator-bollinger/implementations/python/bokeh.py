""" anyplot.ai
indicator-bollinger: Bollinger Bands Indicator Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-17
"""

import os
import sys
import time
from pathlib import Path


# Prevent this script from shadowing the bokeh package
sys.path = [p for p in sys.path if "implementations" not in p]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from bokeh.io import output_file, save  # noqa: E402
from bokeh.models import Band, ColumnDataSource, HoverTool, Legend  # noqa: E402
from bokeh.plotting import figure  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (positions 1-3)
BRAND = "#009E73"  # Position 1 - first series (price)
ACCENT_BLUE = "#4467A3"  # Position 3 - SMA and bands
ACCENT_ORANGE = "#C475FD"  # Position 2 - optional

# Data - Generate synthetic stock price data
np.random.seed(42)
n_days = 120

# Generate realistic price movement using random walk with drift
dates = pd.date_range("2024-01-01", periods=n_days, freq="B")  # Business days
returns = np.random.normal(0.0005, 0.015, n_days)  # Daily returns with slight upward drift
price = 100 * np.cumprod(1 + returns)

# Calculate Bollinger Bands (20-period SMA, 2 standard deviations)
window = 20
sma = pd.Series(price).rolling(window=window).mean().values
std = pd.Series(price).rolling(window=window).std().values
upper_band = sma + 2 * std
lower_band = sma - 2 * std

# Create DataFrame for cleaner handling
df = pd.DataFrame({"date": dates, "close": price, "sma": sma, "upper_band": upper_band, "lower_band": lower_band})

# Drop NaN values from the start (due to rolling window)
df = df.dropna().reset_index(drop=True)

# Create ColumnDataSource
source = ColumnDataSource(df)

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="indicator-bollinger · bokeh · anyplot.ai",
    x_axis_label="Date",
    y_axis_label="Price ($)",
    x_axis_type="datetime",
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

# Add the band fill between upper and lower bands
band = Band(
    base="date",
    lower="lower_band",
    upper="upper_band",
    source=source,
    fill_alpha=0.15,
    fill_color=ACCENT_BLUE,
    line_color=ACCENT_BLUE,
    line_alpha=0.4,
)
p.add_layout(band)

# Plot the bands and price lines with legend
# Upper band
upper_line = p.line(
    "date", "upper_band", source=source, line_color=ACCENT_BLUE, line_width=2, line_dash="solid", alpha=0.6
)

# Lower band
lower_line = p.line(
    "date", "lower_band", source=source, line_color=ACCENT_BLUE, line_width=2, line_dash="solid", alpha=0.6
)

# Middle band (SMA) - dashed line
sma_line = p.line("date", "sma", source=source, line_color=ACCENT_BLUE, line_width=3, line_dash="dashed", alpha=0.9)

# Price line - most prominent (first series in Okabe-Ito)
price_line = p.line("date", "close", source=source, line_color=BRAND, line_width=5, alpha=1.0)

# Add hover tool for interactivity
hover = HoverTool(
    tooltips=[
        ("Date", "@date{%F}"),
        ("Close", "$@close{0.2f}"),
        ("SMA (20)", "$@sma{0.2f}"),
        ("Upper Band", "$@upper_band{0.2f}"),
        ("Lower Band", "$@lower_band{0.2f}"),
    ],
    formatters={"@date": "datetime"},
    mode="vline",
    renderers=[price_line],
)
p.add_tools(hover)

# Create legend
legend = Legend(
    items=[("Close Price", [price_line]), ("SMA (20)", [sma_line]), ("Upper/Lower Band (±2σ)", [upper_line])],
    location="top_left",
)

p.add_layout(legend, "right")

# Style the plot - text sizing for 4800×2700 px
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Legend styling
p.legend.label_text_font_size = "16pt"
p.legend.glyph_width = 40
p.legend.glyph_height = 25
p.legend.spacing = 12
p.legend.padding = 15

# Grid styling - subtle
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK

# Theme-adaptive chrome
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

if p.legend:
    p.legend.background_fill_color = ELEVATED_BG
    p.legend.border_line_color = INK_SOFT
    p.legend.label_text_color = INK_SOFT

# Save interactive HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome (Selenium 4 / Selenium Manager)
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
time.sleep(3)  # let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
