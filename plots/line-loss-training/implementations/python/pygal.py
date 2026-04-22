""" pyplots.ai
line-loss-training: Training Loss Curve
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
import pygal
from pygal.style import Style


# Data: Simulated training loss curves showing typical overfitting behavior
np.random.seed(42)
epochs = np.arange(1, 51)

# Training loss: Steadily decreasing with some noise
train_loss = 2.5 * np.exp(-0.08 * epochs) + 0.1 + np.random.normal(0, 0.02, len(epochs))

# Validation loss: Decreases then increases (overfitting after epoch ~30)
val_loss = 2.3 * np.exp(-0.07 * epochs) + 0.15 + 0.003 * np.maximum(0, epochs - 25) ** 1.5
val_loss += np.random.normal(0, 0.03, len(epochs))

# Find minimum validation loss epoch for annotation
min_val_epoch = int(epochs[np.argmin(val_loss)])
min_val_loss = float(np.min(val_loss))

# Custom style for large canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B"),  # Python Blue, Python Yellow
    title_font_size=48,
    label_font_size=36,
    major_label_font_size=32,
    legend_font_size=32,
    value_font_size=28,
    stroke_width=4,
    opacity=0.9,
    opacity_hover=1.0,
)

# Create line chart
chart = pygal.Line(
    width=4800,
    height=2700,
    style=custom_style,
    title="line-loss-training · pygal · pyplots.ai",
    x_title="Epoch",
    y_title="Cross-Entropy Loss",
    show_x_guides=False,
    show_y_guides=True,
    dots_size=6,
    stroke_style={"width": 4},
    legend_at_bottom=False,
    legend_box_size=24,
    margin=50,
    x_label_rotation=0,
    truncate_label=-1,
    show_dots=True,
)

# Set x-axis labels (show every 5th epoch for readability)
chart.x_labels = [str(e) if e % 5 == 0 else "" for e in epochs]

# Add training and validation loss data
chart.add("Training Loss", list(train_loss))
chart.add("Validation Loss", list(val_loss))

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
