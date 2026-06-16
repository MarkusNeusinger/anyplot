""" anyplot.ai
line-loss-training: Training Loss Curve
Library: pygal 3.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-14
"""

import os
import sys

import numpy as np


# Remove local directory from sys.path to avoid shadowing the pygal package
_local_dir = os.path.abspath(os.path.dirname(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _local_dir]

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


THEME = os.getenv("ANYPLOT_THEME", "light")

# Theme tokens (from default-style-guide.md)
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette (first series = brand green #009E73)
IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Data: Simulated training loss curves showing typical overfitting behavior
np.random.seed(42)
epochs = np.arange(1, 51)

# Training loss: Steadily decreasing with some noise
train_loss = 2.5 * np.exp(-0.08 * epochs) + 0.1 + np.random.normal(0, 0.02, len(epochs))

# Validation loss: Decreases then increases (overfitting after epoch ~25)
val_loss = 2.3 * np.exp(-0.07 * epochs) + 0.15 + 0.003 * np.maximum(0, epochs - 25) ** 1.5
val_loss += np.random.normal(0, 0.03, len(epochs))

# Find minimum validation loss epoch for annotation
min_val_epoch = int(epochs[np.argmin(val_loss)])
min_val_loss = float(np.min(val_loss))

# Custom theme-adaptive style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
)

# Create line chart
chart = pygal.Line(
    width=4800,
    height=2700,
    style=custom_style,
    title="line-loss-training · pygal · anyplot.ai",
    x_title="Epoch",
    y_title="Cross-Entropy Loss",
    show_x_guides=True,
    show_y_guides=True,
    dots_size=6,
    stroke_style={"width": 3},
    legend_at_bottom=False,
    legend_box_size=24,
    margin=80,
    x_label_rotation=0,
    truncate_label=-1,
    show_dots=True,
)

# Set x-axis labels (show every 5th epoch for readability)
chart.x_labels = [str(e) if e % 5 == 0 else "" for e in epochs]

# Add training and validation loss data
chart.add("Training Loss", list(train_loss))
chart.add("Validation Loss", list(val_loss))

# Save as PNG and HTML with theme suffix
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
