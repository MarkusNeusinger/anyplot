"""anyplot.ai
learning-curve-basic: Model Learning Curve
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-10
"""

import os
import sys
import time
from pathlib import Path


# Remove the script directory from sys.path to avoid importing bokeh.py as bokeh
script_dir = Path(__file__).parent
if str(script_dir) in sys.path:
    sys.path.remove(str(script_dir))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from bokeh.io import output_file, save  # noqa: E402
from bokeh.models import Band, ColumnDataSource  # noqa: E402
from bokeh.plotting import figure  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TRAIN_SIZE = "Training set size (samples)"  # role: train_sizes
TRAIN_SCORE = "Training accuracy"  # role: train_scores
VALIDATION_SCORE = "Validation accuracy"  # role: validation_scores
FOLD = "Fold"  # role: extra
SCORE_AXIS = "Accuracy"  # y axis title shared by both curves

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
# One row per training size and cross-validation fold (simulated 5-fold CV of a classifier)
rng = np.random.default_rng(42)
sizes = np.array([50, 100, 200, 300, 400, 500, 600, 700, 800, 900])
fold_offsets = np.array([-1.5, -0.5, 0.0, 0.5, 1.5])  # mean 0, std 1: folds spread around each mean

# Training accuracy stays high and dips slightly; validation accuracy climbs with more data
train_mean = 0.99 - 0.02 * np.log(sizes / sizes[0]) / np.log(sizes[-1] / sizes[0])
train_std = 0.01 + 0.01 * (1 - sizes / sizes[-1])
val_mean = 0.65 + 0.25 * (1 - np.exp(-sizes / 300))
val_std = 0.08 * np.exp(-sizes / 400) + 0.01

rows = []
for i, size in enumerate(sizes):
    train_scores = train_mean[i] + train_std[i] * rng.permutation(fold_offsets)
    val_scores = val_mean[i] + val_std[i] * rng.permutation(fold_offsets)
    rows += [(size, fold + 1, t, v) for fold, (t, v) in enumerate(zip(train_scores, val_scores, strict=True))]
df = pd.DataFrame(rows, columns=[TRAIN_SIZE, FOLD, TRAIN_SCORE, VALIDATION_SCORE])

# Plot: reads only df and the constants above
curves = {}
for score, label in ((TRAIN_SCORE, "Training score"), (VALIDATION_SCORE, "Validation score")):
    by_size = df.groupby(TRAIN_SIZE)[score]
    stats = pd.DataFrame({"mean": by_size.mean(), "std": by_size.std(ddof=0)}).reset_index()
    stats["lower"] = stats["mean"] - stats["std"]
    stats["upper"] = stats["mean"] + stats["std"]
    curves[label] = stats

y_low = min(s["lower"].min() for s in curves.values())
y_high = max(s["upper"].max() for s in curves.values())
y_pad = (y_high - y_low) * 0.06

p = figure(
    width=3200,
    height=1800,
    title="learning-curve-basic · python · bokeh · anyplot.ai",
    x_axis_label=TRAIN_SIZE,
    y_axis_label=SCORE_AXIS,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=60,
)
p.y_range.start = y_low - y_pad
p.y_range.end = y_high + y_pad

for i, (label, stats) in enumerate(curves.items()):
    color = IMPRINT_PALETTE[i]
    source = ColumnDataSource(stats)
    p.add_layout(Band(base=TRAIN_SIZE, lower="lower", upper="upper", source=source, fill_color=color, fill_alpha=0.22))
    p.line(x=TRAIN_SIZE, y="mean", source=source, line_color=color, line_width=5, legend_label=label)
    p.scatter(x=TRAIN_SIZE, y="mean", source=source, color=color, size=16, legend_label=label)

# Style
p.title.text_font_size = "50pt"
p.title.text_font_style = "bold"
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

p.legend.location = "bottom_right"
p.legend.label_text_font_size = "34pt"
p.legend.label_text_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.95
p.legend.border_line_color = INK_SOFT
p.legend.border_line_width = 2
p.legend.padding = 20
p.legend.spacing = 14
p.legend.glyph_width = 50
p.legend.glyph_height = 40

p.grid.grid_line_color = INK
p.grid.grid_line_alpha = 0.10
p.grid.grid_line_dash = "dashed"

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Save HTML, then screenshot it with headless Chrome for the PNG
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
