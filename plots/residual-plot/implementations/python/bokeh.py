"""anyplot.ai
residual-plot: Residual Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 98/100 | Updated: 2026-05-10
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import Band, ColumnDataSource, Label, Range1d, Span
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
OUTLIER_SD = 2  # residuals beyond this many standard deviations count as outliers

# Columns: set these to your table's column names
Y_TRUE = "Observed price ($1000s)"  # role: y_true
Y_PRED = "Fitted values (predicted price in $1000s)"  # role: y_pred

# Data: replace this block with your own table, for example df = pd.read_csv("predictions.csv")
rng = np.random.default_rng(42)
n_points = 150
fitted = np.linspace(150, 450, n_points) + rng.normal(0, 20, n_points)
noise = rng.normal(0, 25, n_points)
noise[[10, 45, 89, 120, 140]] = [62, -68, 58, -65, 70]  # a few clear outliers
df = pd.DataFrame({Y_TRUE: fitted + noise, Y_PRED: fitted})

# Plot: reads only df and the constants above
residuals = df[Y_TRUE] - df[Y_PRED]
limit = OUTLIER_SD * residuals.std(ddof=0)
is_outlier = residuals.abs() > limit
RESIDUAL = "Residuals (observed − predicted)"
plot_df = pd.DataFrame({Y_PRED: df[Y_PRED], RESIDUAL: residuals})

x_min, x_max = plot_df[Y_PRED].min(), plot_df[Y_PRED].max()
x_pad = (x_max - x_min) * 0.04
y_pad = (residuals.max() - residuals.min()) * 0.08

p = figure(
    width=3200,
    height=1800,
    title="residual-plot · python · bokeh · anyplot.ai",
    x_axis_label=Y_PRED,
    y_axis_label=RESIDUAL,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
    x_range=Range1d(x_min - x_pad, x_max + x_pad),
    y_range=Range1d(residuals.min() - y_pad, residuals.max() + y_pad),
)

# ±2 SD band, computed from the plotted residuals
band_source = ColumnDataSource(
    {"x": [x_min - x_pad, x_max + x_pad], "lower": [-limit, -limit], "upper": [limit, limit]}
)
p.add_layout(
    Band(base="x", lower="lower", upper="upper", source=band_source, fill_alpha=0.15, fill_color=INK_SOFT, line_width=0)
)
p.add_layout(Span(location=limit, dimension="width", line_color=INK_SOFT, line_width=2, line_dash="dashed"))
p.add_layout(Span(location=-limit, dimension="width", line_color=INK_SOFT, line_width=2, line_dash="dashed"))
# Zero reference line
p.add_layout(Span(location=0, dimension="width", line_color=IMPRINT_PALETTE[0], line_width=4))

p.scatter(
    x=Y_PRED,
    y=RESIDUAL,
    source=ColumnDataSource(plot_df[~is_outlier]),
    size=18,
    color=IMPRINT_PALETTE[0],
    alpha=0.7,
    legend_label="Residuals",
)
p.scatter(
    x=Y_PRED,
    y=RESIDUAL,
    source=ColumnDataSource(plot_df[is_outlier]),
    size=22,
    color=IMPRINT_PALETTE[1],
    alpha=0.9,
    line_color=IMPRINT_PALETTE[0],
    line_width=2,
    legend_label=f"Outliers (>{OUTLIER_SD} SD)",
)

for sign in (1, -1):
    p.add_layout(
        Label(
            x=x_min,
            y=sign * limit,
            y_offset=8,
            text=f"{'+' if sign > 0 else '−'}{OUTLIER_SD} SD",
            text_font_size="24pt",
            text_color=INK_SOFT,
            text_font_style="italic",
        )
    )

# Style
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
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

p.legend.location = "top_right"
p.legend.label_text_font_size = "34pt"
p.legend.label_text_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.padding = 15
p.legend.spacing = 10

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Save HTML, then screenshot with headless Chrome
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
