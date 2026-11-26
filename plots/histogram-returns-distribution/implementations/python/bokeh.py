""" anyplot.ai
histogram-returns-distribution: Returns Distribution Histogram
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-26
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import BoxAnnotation, ColumnDataSource, HoverTool, Label
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_BINS = 30  # equal-width bins, within the 20-50 the spec suggests
TAIL_SIGMAS = 2  # tail regions start this many standard deviations from the mean

# Columns: set these to your table's column names
DATE = "Date"  # role: date
RETURNS = "Daily Returns (%)"  # role: returns

# Derived columns of the binned table and the fitted curve (built below the Data block)
BIN_LEFT = "bin_left"  # role: extra
BIN_RIGHT = "bin_right"  # role: extra
BIN_BOTTOM = "bin_bottom"  # role: extra
DENSITY = "Density"  # role: extra
BIN_COLOR = "bin_color"  # role: extra
CURVE_X = "curve_x"  # role: extra
CURVE_Y = "curve_y"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("returns.csv")
np.random.seed(42)
n_days = 252
df = pd.DataFrame(
    {
        DATE: pd.bdate_range("2024-01-01", periods=n_days),
        RETURNS: np.random.normal(loc=0.0005, scale=0.015, size=n_days) * 100,
    }
)

# Plot: reads only df and the constants above
returns = df[RETURNS].dropna()
n = len(returns)
mean_return = returns.mean()
std_return = returns.std(ddof=0)
skewness = (((returns - mean_return) / std_return) ** 3).sum() / n
kurtosis = (((returns - mean_return) / std_return) ** 4).sum() / n - 3

hist, edges = np.histogram(returns, bins=N_BINS, density=True)

x_norm = np.linspace(returns.min() - std_return, returns.max() + std_return, 200)
y_norm = (1 / (std_return * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_norm - mean_return) / std_return) ** 2)

lower_tail = mean_return - TAIL_SIGMAS * std_return
upper_tail = mean_return + TAIL_SIGMAS * std_return

is_tail = (edges[:-1] < lower_tail) | (edges[1:] > upper_tail)
bins = pd.DataFrame(
    {
        DENSITY: hist,
        BIN_LEFT: edges[:-1],
        BIN_RIGHT: edges[1:],
        BIN_BOTTOM: 0.0,
        BIN_COLOR: np.where(is_tail, IMPRINT_PALETTE[1], IMPRINT_PALETTE[0]),
    }
)
hist_source = ColumnDataSource(bins)
norm_source = ColumnDataSource(pd.DataFrame({CURVE_X: x_norm, CURVE_Y: y_norm}))

p = figure(
    width=3200,
    height=1800,
    title="histogram-returns-distribution · python · bokeh · anyplot.ai",
    x_axis_label=RETURNS,
    y_axis_label=DENSITY,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

p.add_layout(BoxAnnotation(right=lower_tail, fill_alpha=0.10, fill_color=IMPRINT_PALETTE[1]))
p.add_layout(BoxAnnotation(left=upper_tail, fill_alpha=0.10, fill_color=IMPRINT_PALETTE[1]))

bars = p.quad(
    top=DENSITY,
    bottom=BIN_BOTTOM,
    left=BIN_LEFT,
    right=BIN_RIGHT,
    fill_color=BIN_COLOR,
    line_color=PAGE_BG,
    fill_alpha=0.80,
    line_width=1,
    source=hist_source,
)

hover = HoverTool(
    renderers=[bars],
    tooltips=[
        ("Range", f"@{{{BIN_LEFT}}}{{0.00}}% – @{{{BIN_RIGHT}}}{{0.00}}%"),
        (DENSITY, f"@{{{DENSITY}}}{{0.0000}}"),
    ],
    formatters={f"@{{{BIN_LEFT}}}": "numeral", f"@{{{BIN_RIGHT}}}": "numeral", f"@{{{DENSITY}}}": "numeral"},
)
p.add_tools(hover)

p.line(
    x=CURVE_X,
    y=CURVE_Y,
    source=norm_source,
    line_color=IMPRINT_PALETTE[2],
    line_width=5,
    legend_label="Normal Distribution",
)

stats_text = f"Mean: {mean_return:.3f}%\nStd Dev: {std_return:.3f}%\nSkewness: {skewness:.3f}\nKurtosis: {kurtosis:.3f}"
stats_label = Label(
    x=210,
    y=1180,
    x_units="screen",
    y_units="screen",
    text=stats_text,
    text_font_size="30pt",
    text_color=INK,
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.90,
    border_line_color=INK_SOFT,
    border_line_width=2,
)
p.add_layout(stats_label)

# Style
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

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

p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10

p.legend.location = "top_right"
p.legend.label_text_font_size = "34pt"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT

# Save
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
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
