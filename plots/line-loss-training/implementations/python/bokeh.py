"""anyplot.ai
line-loss-training: Training Loss Curve
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 95/100 | Updated: 2026-11-21
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
EPOCH = "Epoch"  # role: epoch
TRAIN_LOSS = "Training Loss"  # role: train_loss
VAL_LOSS = "Validation Loss"  # role: val_loss

# Data: replace this block with your own table, for example df = pd.read_csv("history.csv")
np.random.seed(42)
n_epochs = 150
epochs = np.arange(1, n_epochs + 1)
train_loss = 2.5 * np.exp(-0.015 * (epochs - 1)) + 0.15 + np.random.normal(0, 0.02, n_epochs)
val_loss = 2.5 * np.exp(-0.012 * (epochs - 1)) + 0.2 + np.random.normal(0, 0.035, n_epochs)
val_loss[80:] += np.linspace(0, 0.08, n_epochs - 80)  # overfitting drift in late epochs
df = pd.DataFrame({EPOCH: epochs, TRAIN_LOSS: np.maximum(train_loss, 0.15), VAL_LOSS: np.maximum(val_loss, 0.18)})

# Plot: reads only df and the constants above
best = df.loc[df[VAL_LOSS].idxmin()]
best_epoch = int(best[EPOCH])
best_loss = float(best[VAL_LOSS])
last_epoch = df[EPOCH].max()
loss_top = df[[TRAIN_LOSS, VAL_LOSS]].to_numpy().max()
source = ColumnDataSource(df)

title = "line-loss-training · python · bokeh · anyplot.ai"
p = figure(
    width=3200,
    height=1800,
    title=title,
    x_axis_label=EPOCH,
    y_axis_label="Loss (Cross-Entropy)",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
    x_range=Range1d(df[EPOCH].min(), last_epoch),
    y_range=Range1d(0, loss_top * 1.08),
)

for i, column in enumerate([TRAIN_LOSS, VAL_LOSS]):
    color = IMPRINT_PALETTE[i]
    p.line(
        x=EPOCH,
        y=column,
        source=source,
        line_width=5,
        color=color,
        legend_label=column,
        muted_color=color,
        muted_alpha=0.15,
    )
    p.scatter(x=EPOCH, y=column, source=source, size=9, color=color, alpha=0.6)

# Optimal stopping epoch: marker at the lowest point of the validation curve
p.scatter(
    x=[best_epoch],
    y=[best_loss],
    size=30,
    color=IMPRINT_PALETTE[1],
    line_color=INK,
    line_width=4,
    legend_label=f"Optimal epoch: {best_epoch}",
)
p.add_layout(
    Label(
        x=best_epoch,
        y=best_loss,
        x_offset=-40,
        y_offset=-35,
        text=f"Epoch {best_epoch}, loss {best_loss:.3f}",
        text_color=INK,
        text_font_size="30pt",
        text_baseline="middle",
        text_align="right",
    )
)

p.add_tools(HoverTool(tooltips=[(EPOCH, f"@{{{EPOCH}}}"), ("Loss", "$y{0.000}")], mode="vline"))

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

p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10
p.xgrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.05

p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT
p.legend.label_text_font_size = "34pt"
p.legend.location = "top_right"
p.legend.click_policy = "mute"

# Save HTML, then screenshot it with headless Chrome
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
