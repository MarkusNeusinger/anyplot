"""anyplot.ai
calibration-curve: Calibration Curve
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label
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
N_BINS = 10  # equal-width probability bins, as the spec asks

# Columns: set these to your table's column names
Y_TRUE = "Actual outcome (0/1)"  # role: y_true
Y_PROB = ["Predicted probability"]  # role: y_prob

# Data: replace this block with your own table, for example df = pd.read_csv("predictions.csv")
np.random.seed(42)
n_samples = 5000
raw_prob = np.random.uniform(0, 1, n_samples)
true_prob = np.clip(1 / (1 + np.exp(-1.3 * np.log(raw_prob / (1 - raw_prob + 1e-10)))), 0.01, 0.99)
df = pd.DataFrame({Y_PROB[0]: raw_prob, Y_TRUE: (np.random.uniform(0, 1, n_samples) < true_prob).astype(int)})

# Plot: reads only df and the constants above
y_prob = df[Y_PROB[0]].to_numpy()
y_true = df[Y_TRUE].to_numpy()

# Bin by equal-width probability intervals; the last bin includes 1.0
bin_ids = np.clip(np.digitize(y_prob, np.linspace(0, 1, N_BINS + 1)[1:-1]), 0, N_BINS - 1)
rows = []
for b in range(N_BINS):
    in_bin = bin_ids == b
    if in_bin.any():
        rows.append((y_prob[in_bin].mean(), y_true[in_bin].mean(), int(in_bin.sum())))
bins = pd.DataFrame(rows, columns=["x", "y", "count"])

brier_score = np.mean((y_prob - y_true) ** 2)
ece = np.sum(bins["count"] / bins["count"].sum() * (bins["y"] - bins["x"]).abs())

W, H = 3200, 1800
p = figure(
    width=W,
    height=H,
    title="calibration-curve · python · bokeh · anyplot.ai",
    x_axis_label="Mean Predicted Probability",
    y_axis_label="Fraction of Positives",
    x_range=(-0.02, 1.02),
    y_range=(-0.02, 1.02),
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Diagonal reference line (perfect calibration)
p.line([0, 1], [0, 1], line_color=INK_SOFT, line_dash="dashed", line_width=4, legend_label="Perfect Calibration")

source = ColumnDataSource(bins)
p.add_tools(HoverTool(tooltips=[("Predicted", "@x{0.00}"), ("Observed", "@y{0.00}"), ("Count", "@count")]))

p.line("x", "y", source=source, line_color=IMPRINT_PALETTE[0], line_width=6, legend_label="Classifier")
p.scatter("x", "y", source=source, size=28, color=IMPRINT_PALETTE[0], fill_alpha=0.9, line_color=PAGE_BG, line_width=2)

# Metrics annotation
p.add_layout(
    Label(
        x=0.04,
        y=0.86,
        text=f"Classifier\nBrier Score: {brier_score:.3f}\nECE: {ece:.3f}",
        text_font_size="30pt",
        text_color=INK,
        background_fill_color=ELEVATED_BG,
        background_fill_alpha=0.95,
        border_line_color=INK_SOFT,
        border_line_width=1,
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
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.legend.label_text_font_size = "34pt"
p.legend.label_text_color = INK_SOFT
p.legend.location = "bottom_right"
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.95
p.legend.border_line_color = INK_SOFT
p.legend.padding = 20
p.legend.spacing = 12
p.legend.glyph_height = 40
p.legend.glyph_width = 60

# Save HTML, then screenshot with headless Chrome
output_file(f"plot-{THEME}.html")
save(p)

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
