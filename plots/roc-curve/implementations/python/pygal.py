"""anyplot.ai
roc-curve: ROC Curve with AUC
Library: pygal 3.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-09
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style
from sklearn.metrics import auc, roc_curve


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Columns: set these to your table's column names
MODEL = "Model"  # role: extra
FPR = "False Positive Rate"  # role: fpr
TPR = "True Positive Rate"  # role: tpr
AUC = "AUC"  # role: auc

# Data: replace this block with your own table, for example df = pd.read_csv("roc_points.csv")
np.random.seed(42)
n_per_class = 100
beta_params = {
    "Excellent": ((1.5, 6), (6, 1.5)),
    "Moderate": ((2.0, 3.0), (3.0, 2.0)),
    "Poor": ((2.5, 2.5), (2.8, 2.2)),
}
frames = []
for name, (neg, pos) in beta_params.items():
    scores = np.concatenate([np.random.beta(*neg, n_per_class), np.random.beta(*pos, n_per_class)])
    labels = [0] * n_per_class + [1] * n_per_class
    fpr, tpr, _ = roc_curve(labels, scores)
    frames.append(pd.DataFrame({MODEL: name, FPR: fpr, TPR: tpr, AUC: auc(fpr, tpr)}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
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
    stroke_width=2.5,
)

# Square canvas: both axes span 0-1, so the diagonal runs corner to corner at 45 degrees
chart = pygal.XY(
    width=2400,
    height=2400,
    style=custom_style,
    title="roc-curve · python · pygal · anyplot.ai",
    x_title=FPR,
    y_title=TPR,
    show_dots=False,
    stroke_style={"width": 7},
    range=(0, 1),
    xrange=(0, 1),
    show_x_guides=True,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    legend_box_size=40,
    truncate_legend=-1,
    margin=40,
    fill=False,
    interpolate=None,
)

for name, group in df.groupby(MODEL, sort=False):
    chart.add(f"{name} ({AUC} = {group[AUC].iloc[0]:.2f})", list(zip(group[FPR], group[TPR], strict=True)))

# Random classifier reference: dashed diagonal from corner to corner
chart.add("Random (AUC = 0.50)", [(0, 0), (1, 1)], stroke_dasharray="18,12", stroke_style={"width": 5})

# Save
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
