"""anyplot.ai
roc-curve: ROC Curve with AUC
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per model in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
MODEL = "Model"  # role: extra
FPR = "False Positive Rate"  # role: fpr
TPR = "True Positive Rate"  # role: tpr
AUC = "AUC"  # role: auc

# Data: replace this block with your own table, for example df = pd.read_csv("roc.csv")
# One row per threshold point; curve TPR = FPR^k, a smaller k bows further to the top-left
t = np.linspace(0, 1, 200)
shapes = {"Model A": 0.15, "Model B": 0.35, "Model C": 0.6}
df = pd.concat(
    [
        pd.DataFrame({MODEL: name, FPR: t, TPR: np.power(t, k), AUC: np.trapezoid(np.power(t, k), t)})
        for name, k in shapes.items()
    ],
    ignore_index=True,
)

# Plot: reads only df and the constants above
models = list(df[MODEL].unique())
auc = df.groupby(MODEL, sort=False)[AUC].first()

p = figure(
    width=2400,
    height=2400,
    title="roc-curve · python · bokeh · anyplot.ai",
    x_axis_label=FPR,
    y_axis_label=TPR,
    x_range=Range1d(-0.02, 1.02),
    y_range=Range1d(-0.02, 1.02),
    toolbar_location=None,
    min_border_left=250,
    min_border_right=60,
    min_border_top=120,
    min_border_bottom=190,
)

# Random classifier reference: the diagonal of the fixed 0-1 domain
p.line(
    x=[0, 1],
    y=[0, 1],
    line_width=4,
    line_dash="dashed",
    line_color=INK_SOFT,
    alpha=0.7,
    legend_label="Random classifier (AUC = 0.50)",
)

for i, model in enumerate(models):
    source = ColumnDataSource(df[df[MODEL] == model])
    p.line(
        x=FPR,
        y=TPR,
        source=source,
        line_width=7,
        line_color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
        legend_label=f"{model} (AUC = {auc[model]:.2f})",
    )

p.add_tools(
    HoverTool(tooltips=[(MODEL, f"@{{{MODEL}}}"), ("FPR", f"@{{{FPR}}}{{0.00}}"), ("TPR", f"@{{{TPR}}}{{0.00}}")])
)

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.title.align = "center"
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

p.legend.location = "bottom_right"
p.legend.label_text_font_size = "30pt"
p.legend.label_text_color = INK_SOFT
p.legend.glyph_width = 70
p.legend.glyph_height = 30
p.legend.spacing = 14
p.legend.padding = 24
p.legend.margin = 40
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.9
p.legend.border_line_color = INK_SOFT
p.legend.border_line_width = 2

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT
p.outline_line_width = 2

for axis in (p.xaxis, p.yaxis):
    axis.axis_line_color = INK_SOFT
    axis.major_tick_line_color = INK_SOFT
    axis.minor_tick_line_color = None
    axis.major_tick_line_width = 2
    axis.axis_line_width = 2

# Save as HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
W, H = 2400, 2400
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
