"""anyplot.ai
lift-curve: Model Lift Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-11-20
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Range1d, Span
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

# Columns: set these to your table's column names
Y_TRUE = "Responded (0/1)"  # role: y_true
Y_SCORE = "Model score"  # role: y_score

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
# Simulated customer response data for a marketing campaign
rng = np.random.RandomState(42)
n_samples = 1000
responded = rng.binomial(1, 0.15, n_samples)  # 15% baseline response rate
noise = rng.normal(0, 0.3, n_samples)
# Scores correlate with the true outcome but imperfectly
score = np.clip(0.3 + 0.5 * responded + noise, 0, 1)
df = pd.DataFrame({Y_TRUE: responded, Y_SCORE: score})

# Plot: reads only df and the constants above
ranked = df.sort_values(Y_SCORE, ascending=False, kind="stable")
n_total = len(ranked)
baseline_rate = ranked[Y_TRUE].mean()
percentile = np.arange(1, 101)
n_selected = np.maximum(n_total * percentile // 100, 1)
hits = ranked[Y_TRUE].to_numpy().cumsum()[n_selected - 1]
lift = (hits / n_selected) / baseline_rate

curve = pd.DataFrame({"percentile": percentile, "lift": lift, "n_selected": n_selected})
deciles = curve[curve["percentile"] % 10 == 0]

source = ColumnDataSource(curve)
decile_source = ColumnDataSource(deciles)

p = figure(
    width=3200,
    height=1800,
    title="lift-curve · python · bokeh · anyplot.ai",
    x_axis_label="Population targeted (%)",
    y_axis_label="Cumulative lift (model / random)",
    x_range=Range1d(0, 100 * 1.05),
    y_range=Range1d(0, curve["lift"].max() * 1.15),
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=60,
)

# Hover tool (active in the interactive HTML)
p.add_tools(
    HoverTool(
        tooltips=[("Population %", "@percentile%"), ("Lift ratio", "@lift{0.00}"), ("Customers", "@n_selected{,}")]
    )
)

# Horizontal reference line at a lift of 1 (random selection)
p.add_layout(Span(location=1, dimension="width", line_color=INK_SOFT, line_width=5, line_dash="dashed"))

# Lift curve
p.line(x="percentile", y="lift", source=source, line_width=8, line_color=IMPRINT_PALETTE[0], legend_label="Model lift")

# Decile markers sit on the curve at their percentiles
p.scatter(
    x="percentile",
    y="lift",
    source=decile_source,
    size=30,
    fill_color=IMPRINT_PALETTE[1],
    line_color=IMPRINT_PALETTE[0],
    line_width=4,
    legend_label="Deciles",
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
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.15
p.ygrid.grid_line_alpha = 0.15

p.legend.location = "top_right"
p.legend.label_text_font_size = "34pt"
p.legend.label_text_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.glyph_height = 40
p.legend.glyph_width = 40

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

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
