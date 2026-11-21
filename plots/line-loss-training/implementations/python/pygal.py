""" anyplot.ai
line-loss-training: Training Loss Curve
Library: pygal 3.1.3 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
EPOCH = "Epoch"  # role: epoch
TRAIN_LOSS = "Training Loss"  # role: train_loss
VAL_LOSS = "Validation Loss"  # role: val_loss
LOSS_FUNCTION = "Cross-Entropy Loss"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("history.csv")
np.random.seed(42)
epochs = np.arange(1, 51)
# Training loss: steady decay with a little noise
train_loss = 2.5 * np.exp(-0.08 * epochs) + 0.1 + np.random.normal(0, 0.02, len(epochs))
# Validation loss: decays, then rises again (overfitting after epoch ~25)
val_loss = 2.3 * np.exp(-0.07 * epochs) + 0.15 + 0.003 * np.maximum(0, epochs - 25) ** 1.5
val_loss += np.random.normal(0, 0.03, len(epochs))
df = pd.DataFrame({EPOCH: epochs, TRAIN_LOSS: train_loss, VAL_LOSS: val_loss})

# Plot
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=5,
)

chart = pygal.Line(
    width=3200,
    height=1800,
    style=custom_style,
    title="line-loss-training · python · pygal · anyplot.ai",
    x_title=EPOCH,
    y_title=LOSS_FUNCTION,
    show_x_guides=True,
    show_y_guides=True,
    dots_size=7,
    legend_at_bottom=False,
    legend_box_size=36,
    x_label_rotation=0,
    truncate_label=-1,
    show_dots=True,
)

# Label every 5th epoch so the axis stays readable
chart.x_labels = [str(e) if e % 5 == 0 else "" for e in df[EPOCH]]

chart.add(TRAIN_LOSS, df[TRAIN_LOSS].tolist())
chart.add(VAL_LOSS, df[VAL_LOSS].tolist())

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
