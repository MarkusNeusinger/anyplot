"""anyplot.ai
line-loss-training: Training Loss Curve
Library: bokeh | Python 3.13
Quality: pending | Created: 2025-05-14
"""

import os
import sys
import time
from pathlib import Path


# Prevent script name from shadowing bokeh module
script_dir = str(Path(__file__).parent)
if script_dir in sys.path:
    sys.path.remove(script_dir)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from bokeh.io import output_file, save  # noqa: E402
from bokeh.models import ColumnDataSource, HoverTool  # noqa: E402
from bokeh.plotting import figure  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
TRAIN_COLOR = "#009E73"  # bluish green - first series (brand)
VAL_COLOR = "#D55E00"  # vermillion - second series

# Generate realistic neural network training data
np.random.seed(42)
n_epochs = 150

# Training loss: smooth exponential decay with noise
epochs = np.arange(1, n_epochs + 1)
train_loss_base = 2.5 * np.exp(-0.015 * (epochs - 1)) + 0.15
train_loss = train_loss_base + np.random.normal(0, 0.02, n_epochs)
train_loss = np.maximum(train_loss, 0.15)  # ensure positive

# Validation loss: slightly noisier, higher baseline, potential overfitting
val_loss_base = 2.5 * np.exp(-0.012 * (epochs - 1)) + 0.2
val_loss = val_loss_base + np.random.normal(0, 0.035, n_epochs)
# Add slight overfitting effect in later epochs
val_loss[80:] += np.linspace(0, 0.08, n_epochs - 80)
val_loss = np.maximum(val_loss, 0.18)

# Find minimum validation loss epoch (for annotation)
min_val_idx = np.argmin(val_loss)
min_val_epoch = epochs[min_val_idx]
min_val_loss = val_loss[min_val_idx]

# Create DataFrame
df = pd.DataFrame({"epoch": epochs, "train_loss": train_loss, "val_loss": val_loss})

# Create Bokeh figure
p = figure(
    width=4800,
    height=2700,
    title="Training and Validation Loss Over Epochs",
    x_axis_label="Epoch",
    y_axis_label="Loss (Cross-Entropy)",
    toolbar_location="right",
)

# Set up data sources
train_source = ColumnDataSource(df[["epoch", "train_loss"]])
val_source = ColumnDataSource(df[["epoch", "val_loss"]])

# Plot lines
train_line = p.line(
    x="epoch",
    y="train_loss",
    source=train_source,
    line_width=4,
    color=TRAIN_COLOR,
    legend_label="Training Loss",
    muted_color=TRAIN_COLOR,
    muted_alpha=0.15,
)

val_line = p.line(
    x="epoch",
    y="val_loss",
    source=val_source,
    line_width=4,
    color=VAL_COLOR,
    legend_label="Validation Loss",
    muted_color=VAL_COLOR,
    muted_alpha=0.15,
)

# Add subtle circle markers at data points
p.scatter(x="epoch", y="train_loss", source=train_source, size=5, color=TRAIN_COLOR, alpha=0.6)

p.scatter(x="epoch", y="val_loss", source=val_source, size=5, color=VAL_COLOR, alpha=0.6)

# Mark the epoch with minimum validation loss
p.scatter(
    x=[min_val_epoch],
    y=[min_val_loss],
    size=12,
    color=VAL_COLOR,
    line_color=INK,
    line_width=2,
    alpha=0.8,
    legend_label=f"Optimal epoch: {min_val_epoch}",
)

# Add hover tool
hover = HoverTool(tooltips=[("Epoch", "@epoch"), ("Loss", "@y{0.0000}")])
p.add_tools(hover)

# Apply text sizing
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Apply theme-adaptive chrome colors
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

# Y-axis grid (for line charts per style guide)
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10
p.xgrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.05

# Configure legend
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT
p.legend.location = "top_right"
p.legend.click_policy = "mute"
p.legend.label_text_font_size = "16pt"

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome using Selenium
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
